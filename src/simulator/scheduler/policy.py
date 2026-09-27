"""Interface abstrata para políticas de escalonamento da CPU."""

from abc import ABC, abstractmethod
from typing import Optional

from simulator.entities.thread import SimulatedThread


class SchedulingPolicy(ABC):
    """Interface abstrata que define o contrato de uma política de escalonamento.
    
    Separa a política (ordem de seleção das tarefas) do mecanismo de despacho
    e controle de troca de contexto implementado pelo Scheduler.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome identificador da política."""
        pass

    @abstractmethod
    def add_thread(self, thread: SimulatedThread) -> None:
        """Insere uma thread tornada elegível na fila de prontos da política."""
        pass

    @abstractmethod
    def select_next_thread(self) -> Optional[SimulatedThread]:
        """Seleciona e remove a próxima thread a ser despachada para a CPU."""
        pass

    @abstractmethod
    def peek_next_thread(self) -> Optional[SimulatedThread]:
        """Inspeciona a próxima thread sem removê-la da fila de prontos."""
        pass

    @abstractmethod
    def remove_thread(self, thread: SimulatedThread) -> bool:
        """Remove explicitamente uma thread da fila de prontos, se presente."""
        pass

    @abstractmethod
    def is_empty(self) -> bool:
        """Indica se não há threads na fila de prontos."""
        pass

    @abstractmethod
    def get_ready_threads(self) -> list[SimulatedThread]:
        """Retorna uma cópia da lista de threads atualmente na fila de prontos."""
        pass
