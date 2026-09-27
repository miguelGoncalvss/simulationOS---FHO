"""Motor de simulação orientada a eventos discretos (SimulationEngine)."""

from typing import Optional

from simulator.core.clock import Clock
from simulator.core.event import Event, EventType
from simulator.core.event_queue import EventQueue
from simulator.entities.operation import OperationType
from simulator.entities.process import Process
from simulator.entities.states import ProcessState, ThreadState
from simulator.entities.thread import SimulatedThread
from simulator.io.io_manager import SimplifiedIOManager
from simulator.metrics.collector import (
    MetricsCollector,
    ProcessMetrics,
    SystemMetrics,
)
from simulator.metrics.logger import EventLogger
from simulator.scheduler.scheduler import Scheduler


class SimulationEngine:
    """Coordenador central da simulação a eventos discretos.

    Avança o tempo lógico através da fila de eventos, orquestra admissões,
    despachos, conclusões de surto de CPU, bloqueios e conclusões de E/S.
    """

    def __init__(
        self,
        scheduler: Scheduler,
        io_manager: Optional[SimplifiedIOManager] = None,
        clock: Optional[Clock] = None,
        event_queue: Optional[EventQueue] = None,
        logger: Optional[EventLogger] = None,
    ) -> None:
        self.clock: Clock = clock or Clock()
        self.event_queue: EventQueue = event_queue or EventQueue()
        self.scheduler: Scheduler = scheduler
        self.io_manager: SimplifiedIOManager = io_manager or SimplifiedIOManager()
        self.logger: EventLogger = logger or EventLogger()
        self.metrics_collector: MetricsCollector = MetricsCollector()

        self.processes: list[Process] = []
        self._process_map: dict[int, Process] = {}
        self._schedule_pending: bool = False
        self._is_initialized: bool = False

    def _get_process(self, pid: int) -> Process:
        return self._process_map[pid]

    def load_workload(self, processes: list[Process]) -> None:
        """Carrega a lista de processos a serem executados na simulação."""
        self.processes = list(processes)
        self._process_map = {p.pid: p for p in self.processes}

        # Agenda a chegada de cada processo no relógio lógico
        for proc in self.processes:
            self.event_queue.schedule(
                time=proc.creation_time,
                event_type=EventType.PROCESS_ARRIVAL,
                pid=proc.pid,
                description=f"Chegada do processo P{proc.pid} ao sistema",
                payload={"process": proc},
            )

        config_summary = (
            f"Política de Escalonamento: {self.scheduler.policy_name}\n"
            f"Custo de Troca de Contexto: {self.scheduler.context_switch_cost} ticks\n"
            f"Quantidade de Processos: {len(self.processes)}\n"
            f"Total de Threads: {sum(len(p.threads) for p in self.processes)}"
        )
        self.logger.set_config(config_summary)
        self._is_initialized = True

    def _request_schedule(self) -> None:
        """Solicita uma avaliação de escalonamento para o instante atual, se a CPU estiver livre."""
        if self.scheduler.is_cpu_idle() and not self._schedule_pending:
            self._schedule_pending = True
            self.event_queue.schedule(
                time=self.clock.time,
                event_type=EventType.SCHEDULE_DECISION,
                description="Avaliação de despacho da fila de prontos",
            )

    def _handle_process_arrival(self, event: Event) -> None:
        """Processa a chegada e admissão de um processo e de suas threads."""
        proc: Process = event.payload["process"]
        self.logger.log(
            clock=self.clock.time,
            event_type="CHEGADA_PROCESSO",
            pid=proc.pid,
            description=f"Processo P{proc.pid} admitido no sistema.",
        )

        for thread in proc.threads:
            self.scheduler.add_ready_thread(
                thread=thread,
                current_time=self.clock.time,
                cause="Admissão de thread na fila de prontos",
            )
            self.logger.log(
                clock=self.clock.time,
                event_type="ADMISSAO_THREAD",
                pid=proc.pid,
                tid=thread.tid,
                description=f"Thread {thread.id_str} admitida na fila de prontos ({self.scheduler.policy_name}).",
            )

        proc.update_derived_state(self.clock.time, cause="Admissão de threads")
        self._request_schedule()

    def _handle_schedule_decision(self, event: Event) -> None:
        """Executa a decisão da política de escalonamento se a CPU estiver ociosa."""
        self._schedule_pending = False

        if not self.scheduler.is_cpu_idle():
            return

        next_thread = self.scheduler.select_next_thread()
        if next_thread is None:
            return

        # Notifica a thread de que seu tempo de espera na fila de prontos encerrou
        if next_thread.tcb.last_ready_entry_time is not None:
            next_thread.tcb.total_ready_wait_time += (
                self.clock.time - next_thread.tcb.last_ready_entry_time
            )
            next_thread.tcb.last_ready_entry_time = None

        if self.scheduler.context_switch_cost > 0:
            self.scheduler.start_context_switch(next_thread)
            self.logger.log(
                clock=self.clock.time,
                event_type="INICIO_TROCA_CONTEXTO",
                pid=next_thread.process_id,
                tid=next_thread.tid,
                description=(
                    f"Iniciada troca de contexto para {next_thread.id_str} "
                    f"(sobrecarga: {self.scheduler.context_switch_cost} ticks)."
                ),
            )
            self.event_queue.schedule(
                time=self.clock.time + self.scheduler.context_switch_cost,
                event_type=EventType.CONTEXT_SWITCH_END,
                pid=next_thread.process_id,
                tid=next_thread.tid,
                description=f"Conclusão da troca de contexto para {next_thread.id_str}",
                payload={"thread": next_thread},
            )
        else:
            # Custo zero: despacho imediato
            self.scheduler.dispatch_immediately(
                thread=next_thread,
                current_time=self.clock.time,
                cause="Despacho da fila de prontos (troca de contexto custo 0)",
            )
            self.logger.log(
                clock=self.clock.time,
                event_type="DESPACHO",
                pid=next_thread.process_id,
                tid=next_thread.tid,
                description=f"Thread {next_thread.id_str} despachada para a CPU.",
            )
            proc = self._get_process(next_thread.process_id)
            proc.update_derived_state(self.clock.time, cause="Thread despachada para a CPU")

            op = next_thread.get_current_operation()
            assert op is not None and op.op_type == OperationType.CPU
            next_thread.tcb.total_cpu_time += op.duration
            self.event_queue.schedule(
                time=self.clock.time + op.duration,
                event_type=EventType.CPU_BURST_END,
                pid=next_thread.process_id,
                tid=next_thread.tid,
                description=f"Fim de surto de CPU para {next_thread.id_str}",
                payload={"thread": next_thread, "burst_duration": op.duration},
            )

    def _handle_context_switch_end(self, event: Event) -> None:
        """Processa a conclusão da troca de contexto e inicia o surto de CPU útil."""
        thread: SimulatedThread = event.payload["thread"]
        self.logger.log(
            clock=self.clock.time,
            event_type="FIM_TROCA_CONTEXTO",
            pid=thread.process_id,
            tid=thread.tid,
            description=f"Troca de contexto concluída para {thread.id_str}.",
        )

        self.scheduler.finish_context_switch(
            thread=thread,
            current_time=self.clock.time,
            cause="Conclusão da troca de contexto",
        )
        self.logger.log(
            clock=self.clock.time,
            event_type="DESPACHO",
            pid=thread.process_id,
            tid=thread.tid,
            description=f"Thread {thread.id_str} despachada para a CPU.",
        )
        proc = self._get_process(thread.process_id)
        proc.update_derived_state(self.clock.time, cause="Thread despachada para a CPU")

        op = thread.get_current_operation()
        assert op is not None and op.op_type == OperationType.CPU
        thread.tcb.total_cpu_time += op.duration
        self.event_queue.schedule(
            time=self.clock.time + op.duration,
            event_type=EventType.CPU_BURST_END,
            pid=thread.process_id,
            tid=thread.tid,
            description=f"Fim de surto de CPU para {thread.id_str}",
            payload={"thread": thread, "burst_duration": op.duration},
        )

    def _handle_cpu_burst_end(self, event: Event) -> None:
        """Processa o término de um surto de CPU (bloqueio por E/S ou término)."""
        thread: SimulatedThread = event.payload["thread"]
        burst_duration: int = event.payload["burst_duration"]
        self.logger.log(
            clock=self.clock.time,
            event_type="FIM_SURTO_CPU",
            pid=thread.process_id,
            tid=thread.tid,
            description=f"Thread {thread.id_str} concluiu surto de CPU de {burst_duration} ticks.",
        )

        # Avança a operação que acabou de ser concluída
        thread.advance_operation()
        self.scheduler.release_cpu()
        proc = self._get_process(thread.process_id)

        if thread.has_more_operations():
            # A próxima operação é uma operação de E/S
            next_op = thread.get_current_operation()
            assert next_op is not None and next_op.op_type == OperationType.IO
            self.logger.log(
                clock=self.clock.time,
                event_type="BLOQUEIO_ES",
                pid=thread.process_id,
                tid=thread.tid,
                description=f"Thread {thread.id_str} bloqueada aguardando E/S ({next_op.duration} ticks).",
            )
            completion_time = self.io_manager.start_io(
                thread=thread,
                duration=next_op.duration,
                current_time=self.clock.time,
            )
            proc.update_derived_state(self.clock.time, cause="Thread bloqueada em E/S")
            self.event_queue.schedule(
                time=completion_time,
                event_type=EventType.IO_COMPLETION,
                pid=thread.process_id,
                tid=thread.tid,
                description=f"Conclusão de operação de E/S para {thread.id_str}",
                payload={"thread": thread},
            )
        else:
            # Todas as operações da thread foram concluídas
            thread.transition_to(
                ThreadState.TERMINATED,
                self.clock.time,
                cause="Todas as operações concluídas com sucesso",
            )
            self.logger.log(
                clock=self.clock.time,
                event_type="FINALIZACAO_THREAD",
                pid=thread.process_id,
                tid=thread.tid,
                description=f"Thread {thread.id_str} finalizada com sucesso.",
            )
            proc.update_derived_state(self.clock.time, cause="Finalização de thread")
            if proc.is_terminated():
                self.logger.log(
                    clock=self.clock.time,
                    event_type="FINALIZACAO_PROCESSO",
                    pid=proc.pid,
                    description=f"Processo P{proc.pid} finalizado (todas as threads concluídas).",
                )

        # CPU foi liberada; solicita novo escalonamento
        self._request_schedule()

    def _handle_io_completion(self, event: Event) -> None:
        """Processa a interrupção simulada de conclusão de E/S."""
        thread: SimulatedThread = event.payload["thread"]
        self.logger.log(
            clock=self.clock.time,
            event_type="INTERRUPCAO_ES",
            pid=thread.process_id,
            tid=thread.tid,
            description=f"Interrupção de hardware: E/S concluída para {thread.id_str}.",
        )

        self.io_manager.complete_io(thread, self.clock.time)
        self.scheduler.add_ready_thread(
            thread=thread,
            current_time=self.clock.time,
            cause="Retorno de bloqueio de E/S",
        )
        self.logger.log(
            clock=self.clock.time,
            event_type="RETORNO_FILA_PRONTOS",
            pid=thread.process_id,
            tid=thread.tid,
            description=f"Thread {thread.id_str} retornou ao final da fila de prontos.",
        )
        proc = self._get_process(thread.process_id)
        proc.update_derived_state(self.clock.time, cause="Retorno de thread de E/S")

        self._request_schedule()

    def run(self) -> tuple[SystemMetrics, list[ProcessMetrics]]:
        """Executa a simulação completa até o esgotamento dos eventos.

        Returns:
            Tupla contendo as métricas globais do sistema e as métricas por processo.
        """
        if not self._is_initialized:
            raise RuntimeError("Carga de trabalho não carregada no motor de simulação.")

        while not self.event_queue.is_empty():
            event = self.event_queue.pop_next()
            self.clock.advance_to(event.time)

            if event.event_type == EventType.PROCESS_ARRIVAL:
                self._handle_process_arrival(event)
            elif event.event_type == EventType.SCHEDULE_DECISION:
                self._handle_schedule_decision(event)
            elif event.event_type == EventType.CONTEXT_SWITCH_END:
                self._handle_context_switch_end(event)
            elif event.event_type == EventType.CPU_BURST_END:
                self._handle_cpu_burst_end(event)
            elif event.event_type == EventType.IO_COMPLETION:
                self._handle_io_completion(event)

        # Simulação concluída
        system_metrics, process_metrics = self.metrics_collector.compute(
            processes=self.processes,
            total_simulation_time=self.clock.time,
            context_switches_count=self.scheduler.context_switches_count,
            total_context_switch_time=self.scheduler.total_context_switch_time,
        )

        return system_metrics, process_metrics
