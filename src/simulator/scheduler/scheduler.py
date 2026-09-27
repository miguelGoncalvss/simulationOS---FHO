"""Mecanismo de escalonamento e coordenação da CPU."""

from typing import Optional

from simulator.entities.states import ThreadState
from simulator.entities.thread import SimulatedThread
from simulator.scheduler.cpu import CPUState, SimulatedCPU
from simulator.scheduler.policy import SchedulingPolicy


class Scheduler:
    """Mecanismo de escalonamento.

    Gerencia a CPU uniprocessadora, a fila de prontos através de uma política
    configurável (SchedulingPolicy) e contabiliza as trocas de contexto.
    """

    def __init__(
        self,
        policy: SchedulingPolicy,
        context_switch_cost: int = 0,
    ) -> None:
        if context_switch_cost < 0:
            raise ValueError(
                f"Custo de troca de contexto não pode ser negativo: {context_switch_cost}"
            )
        self.policy: SchedulingPolicy = policy
        self.context_switch_cost: int = context_switch_cost
        self.cpu: SimulatedCPU = SimulatedCPU()

        # Métricas de sobrecarga
        self.context_switches_count: int = 0
        self.total_context_switch_time: int = 0

    @property
    def policy_name(self) -> str:
        return self.policy.name

    def add_ready_thread(self, thread: SimulatedThread, current_time: int, cause: str) -> None:
        """Move uma thread para o estado PRONTO e insere na fila da política."""
        thread.transition_to(ThreadState.READY, current_time, cause)
        self.policy.add_thread(thread)

    def is_cpu_idle(self) -> bool:
        """Informa se a CPU está livre para receber uma nova tarefa."""
        return self.cpu.is_idle()

    def is_cpu_switching(self) -> bool:
        """Informa se a CPU está atualmente realizando troca de contexto."""
        return self.cpu.is_switching()

    def is_cpu_busy(self) -> bool:
        """Informa se a CPU está atualmente executando instruções úteis."""
        return self.cpu.is_busy()

    def get_current_thread(self) -> Optional[SimulatedThread]:
        """Retorna a thread atualmente na CPU."""
        return self.cpu.current_thread

    def select_next_thread(self) -> Optional[SimulatedThread]:
        """Consulta a política para selecionar a próxima thread a executar."""
        return self.policy.select_next_thread()

    def start_context_switch(self, thread: SimulatedThread) -> None:
        """Inicia a troca de contexto na CPU para a thread selecionada."""
        self.context_switches_count += 1
        self.total_context_switch_time += self.context_switch_cost
        self.cpu.start_context_switch(thread)

    def finish_context_switch(self, thread: SimulatedThread, current_time: int, cause: str) -> None:
        """Conclui a troca de contexto e coloca a thread em execução útil na CPU."""
        thread.transition_to(ThreadState.RUNNING, current_time, cause)
        self.cpu.start_execution(thread)

    def dispatch_immediately(self, thread: SimulatedThread, current_time: int, cause: str) -> None:
        """Despacha a thread imediatamente quando o custo de troca de contexto é zero."""
        self.context_switches_count += 1
        thread.transition_to(ThreadState.RUNNING, current_time, cause)
        self.cpu.start_execution(thread)

    def release_cpu(self) -> Optional[SimulatedThread]:
        """Libera a CPU, tornando-a ociosa."""
        return self.cpu.release()

    def has_ready_threads(self) -> bool:
        """Verifica se há threads aguardando na fila de prontos."""
        return not self.policy.is_empty()

    def __repr__(self) -> str:
        return (
            f"Scheduler(policy={self.policy_name}, switch_cost={self.context_switch_cost}, "
            f"switches={self.context_switches_count}, cpu={self.cpu})"
        )
