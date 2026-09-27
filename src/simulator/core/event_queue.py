"""Fila de prioridade de eventos discretos da simulação."""

import heapq
from typing import Optional

from simulator.core.event import Event, EventType


class EventQueue:
    """Fila de eventos discretos baseada em min-heap determinístico."""

    def __init__(self) -> None:
        self._heap: list[Event] = []
        self._seq_counter: int = 0

    def schedule(
        self,
        time: int,
        event_type: EventType,
        pid: Optional[int] = None,
        tid: Optional[int] = None,
        description: str = "",
        payload: Optional[dict] = None,
    ) -> Event:
        """Cria e insere um novo evento na fila de eventos.

        Args:
            time: Instante lógico de ocorrência do evento.
            event_type: Tipo do evento (determina prioridade intrínseca).
            pid: Identificador opcional do processo envolvido.
            tid: Identificador opcional da thread envolvida.
            description: Descrição textual do evento.
            payload: Metadados adicionais associados ao evento.

        Returns:
            O evento agendado.
        """
        self._seq_counter += 1
        event = Event(
            time=time,
            priority=int(event_type.value),
            seq=self._seq_counter,
            event_type=event_type,
            pid=pid,
            tid=tid,
            description=description,
            payload=payload or {},
        )
        heapq.heappush(self._heap, event)
        return event

    def pop_next(self) -> Event:
        """Remove e retorna o próximo evento com menor timestamp e prioridade.

        Raises:
            IndexError: Se a fila estiver vazia.
        """
        if not self._heap:
            raise IndexError("Tentativa de retirar evento de uma fila vazia.")
        return heapq.heappop(self._heap)

    def peek_next(self) -> Optional[Event]:
        """Retorna o próximo evento sem removê-lo, ou None se estiver vazia."""
        return self._heap[0] if self._heap else None

    def is_empty(self) -> bool:
        """Verifica se a fila de eventos não contém eventos pendentes."""
        return len(self._heap) == 0

    def __len__(self) -> int:
        return len(self._heap)

    def clear(self) -> None:
        """Esvazia a fila de eventos e reinicia o contador de sequência."""
        self._heap.clear()
        self._seq_counter = 0

    def __repr__(self) -> str:
        return f"EventQueue(size={len(self._heap)}, next={self.peek_next()})"
