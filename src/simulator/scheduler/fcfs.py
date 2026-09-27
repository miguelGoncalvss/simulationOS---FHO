"""Política de escalonamento FCFS (First-Come, First-Served)."""

from collections import deque
from typing import Optional

from simulator.entities.thread import SimulatedThread
from simulator.scheduler.policy import SchedulingPolicy


class FCFSPolicy(SchedulingPolicy):
    """Política FCFS (First-Come, First-Served) não preemptiva.

    As threads são atendidas rigorosamente na ordem de inserção na fila de prontos.
    Uma thread que retorna de E/S é posicionada no final da fila.
    Empates de inserção simultânea são ordenados por (tempo de chegada, PID, TID).
    """

    def __init__(self) -> None:
        self._ready_queue: deque[SimulatedThread] = deque()

    @property
    def name(self) -> str:
        return "FCFS"

    def add_thread(self, thread: SimulatedThread) -> None:
        """Adiciona a thread ao final da fila de prontos (FIFO)."""
        self._ready_queue.append(thread)

    def select_next_thread(self) -> Optional[SimulatedThread]:
        """Seleciona e remove a primeira thread da fila de prontos."""
        if not self._ready_queue:
            return None
        return self._ready_queue.popleft()

    def peek_next_thread(self) -> Optional[SimulatedThread]:
        """Inspeciona a primeira thread da fila sem removê-la."""
        if not self._ready_queue:
            return None
        return self._ready_queue[0]

    def remove_thread(self, thread: SimulatedThread) -> bool:
        """Remove a thread da fila, caso presente."""
        try:
            self._ready_queue.remove(thread)
            return True
        except ValueError:
            return False

    def is_empty(self) -> bool:
        return len(self._ready_queue) == 0

    def get_ready_threads(self) -> list[SimulatedThread]:
        return list(self._ready_queue)

    def __repr__(self) -> str:
        threads_repr = [t.id_str for t in self._ready_queue]
        return f"FCFSPolicy(ready={threads_repr})"
