"""Process Control Block (PCB) para o processo simulado."""

from dataclasses import dataclass, field
from typing import Any, Optional

from simulator.entities.states import ProcessState


@dataclass
class PCB:
    """Bloco de Controle de Processo (PCB).

    Contém os metadados de gerenciamento do processo no sistema operacional simulado.
    """

    pid: int
    priority: int
    creation_time: int

    # Estado derivado do ciclo de vida das threads
    state: ProcessState = ProcessState.NEW
    completion_time: Optional[int] = None

    # Contexto e estruturas de controle lógicas
    # PC: contador lógico geral do processo
    program_counter: int = 0
    # Registradores simulados do processo
    registers: dict[str, int] = field(
        default_factory=lambda: {"R0": 0, "R1": 0}
    )

    # Pontos de extensão reservados para a Etapa Final (Entrega 2):
    # address_space: armazenará a tabela de páginas e alocação de molduras.
    # open_files_table: armazenará os descritores de arquivos abertos locais ao processo.
    address_space: Optional[Any] = None
    open_files_table: list[Any] = field(default_factory=list)

    # Histórico de transições do processo: (instante, novo_estado, causa)
    state_history: list[tuple[int, ProcessState, str]] = field(default_factory=list)

    def record_transition(self, current_time: int, new_state: ProcessState, cause: str) -> None:
        """Registra uma mudança de estado no histórico do processo."""
        self.state = new_state
        self.state_history.append((current_time, new_state, cause))

    def __repr__(self) -> str:
        return (
            f"PCB(PID={self.pid}, state={self.state.value}, prio={self.priority}, "
            f"created={self.creation_time}, completed={self.completion_time})"
        )
