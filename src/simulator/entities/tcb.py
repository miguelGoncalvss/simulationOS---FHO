"""Thread Control Block (TCB) para a thread simulada."""

from dataclasses import dataclass, field
from typing import Optional

from simulator.entities.operation import Operation
from simulator.entities.states import ThreadState


@dataclass
class TCB:
    """Bloco de Controle de Thread (TCB).

    Armazena todo o estado e metadados necessários para o controle,
    escalonamento e preservação de contexto da thread simulada.
    """

    tid: int
    process_id: int
    priority: int
    arrival_time: int
    operations: list[Operation] = field(default_factory=list)

    # Estado de execução
    state: ThreadState = ThreadState.NEW
    current_op_index: int = 0

    # Contexto simulado (registradores e pilha lógica)
    # PC: contador de programa lógico que aponta para o índice da operação atual.
    # R0, R1: registradores de uso geral simulados guardando valores de trabalho.
    # SP: registrador apontador de pilha lógica.
    registers: dict[str, int] = field(
        default_factory=lambda: {"PC": 0, "R0": 0, "R1": 0, "SP": 1024}
    )
    # Pilha lógica: representa os quadros de ativação da thread (escopo local).
    stack: list[str] = field(default_factory=lambda: ["main()"])

    # Métricas e temporização
    admission_time: Optional[int] = None
    first_execution_time: Optional[int] = None
    completion_time: Optional[int] = None
    total_cpu_time: int = 0
    total_io_time: int = 0
    total_ready_wait_time: int = 0
    last_ready_entry_time: Optional[int] = None

    # Histórico de transições: tuplas de (instante, novo_estado, causa)
    state_history: list[tuple[int, ThreadState, str]] = field(default_factory=list)

    @property
    def id_str(self) -> str:
        """Identificador textual canônico da thread (P{pid}-T{tid})."""
        return f"P{self.process_id}-T{self.tid}"

    def record_transition(self, current_time: int, new_state: ThreadState, cause: str) -> None:
        """Registra a transição de estado no histórico do TCB."""
        self.state = new_state
        self.state_history.append((current_time, new_state, cause))

    def __repr__(self) -> str:
        return (
            f"TCB({self.id_str}, state={self.state.value}, op_idx={self.current_op_index}/"
            f"{len(self.operations)}, wait={self.total_ready_wait_time}, cpu={self.total_cpu_time})"
        )
