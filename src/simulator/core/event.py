"""Definição de eventos e tipos de eventos para a simulação discreta."""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Optional


class EventType(IntEnum):
    """Tipos de eventos com prioridades intrínsecas para desempate no mesmo instante.
    
    A prioridade é definida de forma que eventos que liberam recursos ou preparam
    entidades para a fila de prontos ocorram antes de decisões de escalonamento:
    1. IO_COMPLETION: desbloqueia thread e a coloca em PRONTO antes do escalonador agir.
    2. PROCESS_ARRIVAL: admite novo processo e suas threads na fila de prontos.
    3. CONTEXT_SWITCH_END: finaliza a sobrecarga de troca de contexto e inicia execução útil.
    4. CPU_BURST_END: encerra surto de CPU atual, liberando a CPU (para E/S ou término).
    5. SCHEDULE_DECISION: avalia a fila de prontos e despacha a próxima thread se CPU livre.
    """
    IO_COMPLETION = 1
    PROCESS_ARRIVAL = 2
    CONTEXT_SWITCH_END = 3
    CPU_BURST_END = 4
    SCHEDULE_DECISION = 5


@dataclass(order=True)
class Event:
    """Representa um evento discreto agendado no tempo lógico."""

    # Campos usados na comparação e ordenação da fila de prioridade
    time: int
    priority: int
    seq: int = field(default=0)

    # Campos informativos (não comparados na tupla de ordenação)
    event_type: EventType = field(compare=False, default=EventType.SCHEDULE_DECISION)
    pid: Optional[int] = field(compare=False, default=None)
    tid: Optional[int] = field(compare=False, default=None)
    description: str = field(compare=False, default="")
    payload: dict[str, Any] = field(compare=False, default_factory=dict)

    def __post_init__(self) -> None:
        if self.priority is None:
            self.priority = int(self.event_type.value)

    def __repr__(self) -> str:
        return (
            f"Event(t={self.time}, type={self.event_type.name}, prio={self.priority}, "
            f"seq={self.seq}, pid={self.pid}, tid={self.tid}, desc='{self.description}')"
        )
