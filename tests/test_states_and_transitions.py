"""Testes unitários para ciclo de vida, estados e validação de transições."""

import pytest

from simulator.entities.operation import Operation, OperationType
from simulator.entities.process import Process
from simulator.entities.states import (
    InvalidStateTransitionError,
    ProcessState,
    ThreadState,
)
from simulator.entities.thread import SimulatedThread


def create_dummy_thread(pid: int = 1, tid: int = 1) -> SimulatedThread:
    return SimulatedThread(
        tid=tid,
        process_id=pid,
        priority=1,
        arrival_time=0,
        operations=[
            Operation(op_type=OperationType.CPU, duration=3),
            Operation(op_type=OperationType.IO, duration=2),
            Operation(op_type=OperationType.CPU, duration=1),
        ],
    )


def test_valid_thread_transitions() -> None:
    """Verifica sequência completa de transições válidas no ciclo de vida."""
    t = create_dummy_thread()
    assert t.state == ThreadState.NEW

    # NEW -> READY
    t.transition_to(ThreadState.READY, current_time=0, cause="Admissão")
    assert t.state == ThreadState.READY

    # READY -> RUNNING
    t.transition_to(ThreadState.RUNNING, current_time=2, cause="Despacho")
    assert t.state == ThreadState.RUNNING
    assert t.response_time == 2
    assert t.waiting_time == 2

    # RUNNING -> BLOCKED
    t.transition_to(ThreadState.BLOCKED, current_time=5, cause="Início E/S")
    assert t.state == ThreadState.BLOCKED

    # BLOCKED -> READY
    t.transition_to(ThreadState.READY, current_time=7, cause="Conclusão E/S")
    assert t.state == ThreadState.READY

    # READY -> RUNNING
    t.transition_to(ThreadState.RUNNING, current_time=9, cause="Segundo despacho")
    assert t.state == ThreadState.RUNNING
    # Espera total deve ser 2 (primeira) + (9 - 7) = 4
    assert t.waiting_time == 4

    # RUNNING -> TERMINATED
    t.transition_to(ThreadState.TERMINATED, current_time=10, cause="Fim de operações")
    assert t.state == ThreadState.TERMINATED
    assert t.turnaround_time == 10

    # Histórico de transições deve conter todas as 6 transições
    assert len(t.tcb.state_history) == 6


def test_invalid_thread_transitions_raise_error() -> None:
    """Garante que transições ilegais sejam barradas com exceção explicativa."""
    t = create_dummy_thread()

    # Tentativa de passar de NOVO diretamente para EXECUTANDO
    with pytest.raises(InvalidStateTransitionError) as exc_info:
        t.transition_to(ThreadState.RUNNING, current_time=0, cause="Pular pronto")
    assert exc_info.value.source_state == ThreadState.NEW.value
    assert exc_info.value.target_state == ThreadState.RUNNING.value

    # NEW -> READY
    t.transition_to(ThreadState.READY, current_time=0, cause="Admissão")

    # Tentativa de passar de PRONTO diretamente para BLOQUEADO
    with pytest.raises(InvalidStateTransitionError):
        t.transition_to(ThreadState.BLOCKED, current_time=1, cause="Bloqueio sem CPU")

    # Tentativa de passar de PRONTO diretamente para FINALIZADO
    with pytest.raises(InvalidStateTransitionError):
        t.transition_to(ThreadState.TERMINATED, current_time=1, cause="Morte súbita")

    # READY -> RUNNING
    t.transition_to(ThreadState.RUNNING, current_time=2, cause="Despacho")
    # RUNNING -> TERMINATED
    t.transition_to(ThreadState.TERMINATED, current_time=3, cause="Fim")

    # Tentativa de ressuscitar thread FINALIZADA
    with pytest.raises(InvalidStateTransitionError):
        t.transition_to(ThreadState.READY, current_time=4, cause="Ressurreição")


def test_process_derived_state_and_multi_thread_completion() -> None:
    """Verifica que o estado do processo reflete suas threads e só termina com todas."""
    p = Process(pid=1, priority=1, arrival_time=0)
    t1 = create_dummy_thread(pid=1, tid=1)
    t2 = create_dummy_thread(pid=1, tid=2)
    p.add_thread(t1)
    p.add_thread(t2)

    assert p.state == ProcessState.NEW

    # Ambas vão para PRONTO
    t1.transition_to(ThreadState.READY, 0, "Admitida")
    t2.transition_to(ThreadState.READY, 0, "Admitida")
    p.update_derived_state(0, "Threads prontas")
    assert p.state == ProcessState.READY

    # T1 executa
    t1.transition_to(ThreadState.RUNNING, 1, "Despachada")
    p.update_derived_state(1, "T1 executando")
    assert p.state == ProcessState.RUNNING

    # T1 bloqueia em E/S
    t1.transition_to(ThreadState.BLOCKED, 3, "T1 E/S")
    p.update_derived_state(3, "T1 bloqueada, T2 pronta")
    assert p.state == ProcessState.READY  # T2 ainda está PRONTA!

    # T2 executa
    t2.transition_to(ThreadState.RUNNING, 3, "T2 despachada")
    p.update_derived_state(3, "T2 executando")
    assert p.state == ProcessState.RUNNING

    # T2 também bloqueia
    t2.transition_to(ThreadState.BLOCKED, 5, "T2 E/S")
    p.update_derived_state(5, "Ambas bloqueadas")
    assert p.state == ProcessState.BLOCKED

    # T1 conclui e finaliza
    t1.transition_to(ThreadState.READY, 6, "T1 volta de E/S")
    t1.transition_to(ThreadState.RUNNING, 6, "T1 executa")
    t1.transition_to(ThreadState.TERMINATED, 8, "T1 finalizada")
    p.update_derived_state(8, "T1 finalizou, T2 ainda viva")
    assert not p.is_terminated()
    assert p.state == ProcessState.BLOCKED  # T2 ainda está BLOQUEADA!

    # T2 conclui e finaliza
    t2.transition_to(ThreadState.READY, 9, "T2 volta")
    t2.transition_to(ThreadState.RUNNING, 9, "T2 executa")
    t2.transition_to(ThreadState.TERMINATED, 12, "T2 finalizada")
    p.update_derived_state(12, "T2 finalizou")

    # Agora sim, o processo deve estar finalizado
    assert p.is_terminated()
    assert p.state == ProcessState.TERMINATED
    assert p.turnaround_time == 12  # Terminou no tick 12
