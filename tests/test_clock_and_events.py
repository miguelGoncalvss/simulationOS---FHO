"""Testes unitários para o relógio lógico e fila de eventos discretos."""

import pytest

from simulator.core.clock import Clock
from simulator.core.event import Event, EventType
from simulator.core.event_queue import EventQueue


def test_clock_monotonicity() -> None:
    """Verifica se o relógio avança corretamente e impede retrocesso temporal."""
    clock = Clock(initial_time=0)
    assert clock.time == 0

    assert clock.advance_to(5) == 5
    assert clock.time == 5

    assert clock.advance_to(5) == 5  # Avanço para o mesmo instante é permitido

    assert clock.advance_to(10) == 10
    assert clock.time == 10

    # Tentativa de retrocesso temporal deve lançar ValueError
    with pytest.raises(ValueError, match="Tentativa de retrocesso temporal"):
        clock.advance_to(8)

    # Tempo não pode ser negativo
    with pytest.raises(ValueError, match="não pode ser negativo"):
        Clock(initial_time=-1)


def test_event_queue_ordering() -> None:
    """Verifica ordenação por tempo lógico."""
    eq = EventQueue()
    assert eq.is_empty()

    eq.schedule(time=10, event_type=EventType.PROCESS_ARRIVAL, pid=1)
    eq.schedule(time=2, event_type=EventType.PROCESS_ARRIVAL, pid=2)
    eq.schedule(time=5, event_type=EventType.PROCESS_ARRIVAL, pid=3)

    assert len(eq) == 3
    assert not eq.is_empty()

    ev1 = eq.pop_next()
    assert ev1.time == 2
    assert ev1.pid == 2

    ev2 = eq.pop_next()
    assert ev2.time == 5
    assert ev2.pid == 3

    ev3 = eq.pop_next()
    assert ev3.time == 10
    assert ev3.pid == 1

    assert eq.is_empty()
    with pytest.raises(IndexError):
        eq.pop_next()


def test_event_queue_deterministic_tie_breaking() -> None:
    """Verifica resolução determinística de empates de eventos no mesmo instante."""
    eq = EventQueue()

    # Inserção no mesmo instante t=5 em ordem arbitrária
    eq.schedule(time=5, event_type=EventType.SCHEDULE_DECISION, description="Escalonamento")
    eq.schedule(time=5, event_type=EventType.CPU_BURST_END, description="Fim CPU")
    eq.schedule(time=5, event_type=EventType.IO_COMPLETION, description="Conclusão E/S")
    eq.schedule(time=5, event_type=EventType.PROCESS_ARRIVAL, description="Chegada")
    eq.schedule(time=5, event_type=EventType.CONTEXT_SWITCH_END, description="Fim troca")

    # A ordem esperada de prioridade intrínseca:
    # 1. IO_COMPLETION
    # 2. PROCESS_ARRIVAL
    # 3. CONTEXT_SWITCH_END
    # 4. CPU_BURST_END
    # 5. SCHEDULE_DECISION
    popped = [eq.pop_next().event_type for _ in range(5)]
    expected = [
        EventType.IO_COMPLETION,
        EventType.PROCESS_ARRIVAL,
        EventType.CONTEXT_SWITCH_END,
        EventType.CPU_BURST_END,
        EventType.SCHEDULE_DECISION,
    ]
    assert popped == expected


def test_event_queue_fifo_for_exact_ties() -> None:
    """Verifica que eventos com mesmo instante e mesmo tipo respeitam FIFO por seq counter."""
    eq = EventQueue()
    eq.schedule(time=4, event_type=EventType.PROCESS_ARRIVAL, pid=1, description="Primeiro P1")
    eq.schedule(time=4, event_type=EventType.PROCESS_ARRIVAL, pid=2, description="Segundo P2")
    eq.schedule(time=4, event_type=EventType.PROCESS_ARRIVAL, pid=3, description="Terceiro P3")

    pids = [eq.pop_next().pid for _ in range(3)]
    assert pids == [1, 2, 3]
