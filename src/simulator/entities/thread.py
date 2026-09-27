"""Representação da thread simulada (unidade escalonável)."""

from typing import Optional

from simulator.entities.operation import Operation, OperationType
from simulator.entities.states import ThreadState, validate_thread_transition
from simulator.entities.tcb import TCB


class SimulatedThread:
    """Thread simulada. Representa a unidade básica escalonada pela CPU."""

    def __init__(
        self,
        tid: int,
        process_id: int,
        priority: int,
        arrival_time: int,
        operations: list[Operation],
    ) -> None:
        self.tcb = TCB(
            tid=tid,
            process_id=process_id,
            priority=priority,
            arrival_time=arrival_time,
            operations=operations,
        )

    @property
    def tid(self) -> int:
        return self.tcb.tid

    @property
    def process_id(self) -> int:
        return self.tcb.process_id

    @property
    def id_str(self) -> str:
        return self.tcb.id_str

    @property
    def priority(self) -> int:
        return self.tcb.priority

    @property
    def arrival_time(self) -> int:
        return self.tcb.arrival_time

    @property
    def state(self) -> ThreadState:
        return self.tcb.state

    @property
    def operations(self) -> list[Operation]:
        return self.tcb.operations

    @property
    def current_op_index(self) -> int:
        return self.tcb.current_op_index

    def transition_to(
        self,
        target_state: ThreadState,
        current_time: int,
        cause: str,
    ) -> None:
        """Executa a transição de estado da thread com validação e coleta de métricas.

        Args:
            target_state: Novo estado desejado.
            current_time: Instante do relógio lógico no momento da transição.
            cause: Descrição da causa que provocou a mudança de estado.

        Raises:
            InvalidStateTransitionError: Se a transição for proibida.
        """
        old_state = self.tcb.state
        validate_thread_transition(self.id_str, old_state, target_state, cause)

        # Se estava em PRONTO e saindo para outro estado, acumula tempo de espera na fila
        if old_state == ThreadState.READY and self.tcb.last_ready_entry_time is not None:
            wait_delta = current_time - self.tcb.last_ready_entry_time
            self.tcb.total_ready_wait_time += wait_delta

        # Se entrando em PRONTO, marca o início da espera atual
        if target_state == ThreadState.READY:
            self.tcb.last_ready_entry_time = current_time
            if self.tcb.admission_time is None:
                self.tcb.admission_time = current_time

        # Se entrando em EXECUTANDO pela primeira vez, registra instante de primeira resposta
        if target_state == ThreadState.RUNNING and self.tcb.first_execution_time is None:
            self.tcb.first_execution_time = current_time

        # Se finalizando, registra instante de término
        if target_state == ThreadState.TERMINATED:
            self.tcb.completion_time = current_time

        self.tcb.record_transition(current_time, target_state, cause)

    def get_current_operation(self) -> Optional[Operation]:
        """Retorna a operação atual da thread, ou None se todas já foram concluídas."""
        if self.tcb.current_op_index < len(self.tcb.operations):
            return self.tcb.operations[self.tcb.current_op_index]
        return None

    def advance_operation(self) -> Optional[Operation]:
        """Avança o contador de programa simulado para a próxima operação."""
        self.tcb.current_op_index += 1
        self.tcb.registers["PC"] = self.tcb.current_op_index
        # Simula atualização de registrador de trabalho
        self.tcb.registers["R0"] = (self.tcb.registers["R0"] + 1) % 65536
        return self.get_current_operation()

    def has_more_operations(self) -> bool:
        """Indica se a thread ainda possui operações a executar."""
        return self.tcb.current_op_index < len(self.tcb.operations)

    def is_terminated(self) -> bool:
        """Verifica se a thread atingiu o estado FINALIZADO."""
        return self.tcb.state == ThreadState.TERMINATED

    @property
    def turnaround_time(self) -> Optional[int]:
        """Tempo de retorno: término menos chegada."""
        if self.tcb.completion_time is None:
            return None
        return self.tcb.completion_time - self.tcb.arrival_time

    @property
    def waiting_time(self) -> int:
        """Tempo de espera acumulado na fila de prontos."""
        return self.tcb.total_ready_wait_time

    @property
    def response_time(self) -> Optional[int]:
        """Tempo de resposta: primeira execução útil menos chegada."""
        if self.tcb.first_execution_time is None:
            return None
        return self.tcb.first_execution_time - self.tcb.arrival_time

    def __repr__(self) -> str:
        return f"SimulatedThread({self.tcb})"
