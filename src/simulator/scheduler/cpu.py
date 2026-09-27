"""Representação da CPU simulada (uniprocessador)."""

from enum import Enum
from typing import Optional

from simulator.entities.thread import SimulatedThread


class CPUState(Enum):
    """Estados operacionais da CPU simulada."""
    IDLE = "OCIOSA"
    CONTEXT_SWITCHING = "TROCA_DE_CONTEXTO"
    BUSY = "EXECUTANDO"


class SimulatedCPU:
    """CPU uniprocessadora do simulador."""

    def __init__(self) -> None:
        self.state: CPUState = CPUState.IDLE
        self.current_thread: Optional[SimulatedThread] = None

    def is_idle(self) -> bool:
        return self.state == CPUState.IDLE

    def is_switching(self) -> bool:
        return self.state == CPUState.CONTEXT_SWITCHING

    def is_busy(self) -> bool:
        return self.state == CPUState.BUSY

    def start_context_switch(self, thread: SimulatedThread) -> None:
        """Inicia uma troca de contexto na CPU para preparar a execução da thread."""
        self.state = CPUState.CONTEXT_SWITCHING
        self.current_thread = thread

    def start_execution(self, thread: SimulatedThread) -> None:
        """Aloca a CPU para execução útil da thread."""
        self.state = CPUState.BUSY
        self.current_thread = thread

    def release(self) -> Optional[SimulatedThread]:
        """Libera a CPU, retornando a thread que a estava ocupando."""
        thread = self.current_thread
        self.state = CPUState.IDLE
        self.current_thread = None
        return thread

    def __repr__(self) -> str:
        curr = self.current_thread.id_str if self.current_thread else "None"
        return f"SimulatedCPU(state={self.state.value}, current_thread={curr})"
