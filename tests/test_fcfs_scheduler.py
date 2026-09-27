"""Testes unitários para a política de escalonamento FCFS."""

from simulator.entities.operation import Operation, OperationType
from simulator.entities.states import ThreadState
from simulator.entities.thread import SimulatedThread
from simulator.scheduler.fcfs import FCFSPolicy
from simulator.scheduler.scheduler import Scheduler


def make_thread(pid: int, tid: int, arrival: int = 0) -> SimulatedThread:
    return SimulatedThread(
        tid=tid,
        process_id=pid,
        priority=1,
        arrival_time=arrival,
        operations=[Operation(OperationType.CPU, 5)],
    )


def test_fcfs_fifo_ordering() -> None:
    """Verifica que a política FCFS segue estritamente a ordem de inserção (FIFO)."""
    policy = FCFSPolicy()
    assert policy.is_empty()

    t1 = make_thread(pid=1, tid=1)
    t2 = make_thread(pid=2, tid=1)
    t3 = make_thread(pid=3, tid=1)

    policy.add_thread(t1)
    policy.add_thread(t2)
    policy.add_thread(t3)

    assert not policy.is_empty()
    assert policy.peek_next_thread() == t1

    assert policy.select_next_thread() == t1
    assert policy.select_next_thread() == t2
    assert policy.select_next_thread() == t3
    assert policy.select_next_thread() is None
    assert policy.is_empty()


def test_fcfs_thread_returning_from_io_goes_to_tail() -> None:
    """Verifica que uma thread que retorna de E/S entra no final da fila de prontos."""
    policy = FCFSPolicy()
    scheduler = Scheduler(policy=policy, context_switch_cost=0)

    t1 = make_thread(pid=1, tid=1)
    t2 = make_thread(pid=2, tid=1)
    t3 = make_thread(pid=3, tid=1)

    # t1 e t2 estão prontas
    scheduler.add_ready_thread(t1, current_time=0, cause="Chegada")
    scheduler.add_ready_thread(t2, current_time=0, cause="Chegada")

    # t1 é despachada
    selected = scheduler.select_next_thread()
    assert selected == t1
    t1.transition_to(ThreadState.RUNNING, current_time=0, cause="Despacho")

    # Enquanto t1 executa, t3 chega
    scheduler.add_ready_thread(t3, current_time=2, cause="Chegada")

    # t1 termina surto, vai para E/S e depois retorna para PRONTO
    t1.transition_to(ThreadState.BLOCKED, current_time=3, cause="Início de E/S")
    scheduler.add_ready_thread(t1, current_time=5, cause="Retorno de E/S")

    # A fila de prontos deve ter primeiro t2, depois t3, e por fim t1
    ready_ids = [t.id_str for t in scheduler.policy.get_ready_threads()]
    assert ready_ids == ["P2-T1", "P3-T1", "P1-T1"]


def test_fcfs_remove_thread() -> None:
    """Verifica remoção explícita de thread da fila de prontos."""
    policy = FCFSPolicy()
    t1 = make_thread(1, 1)
    t2 = make_thread(2, 1)

    policy.add_thread(t1)
    policy.add_thread(t2)

    assert policy.remove_thread(t1) is True
    assert policy.remove_thread(t1) is False
    assert policy.select_next_thread() == t2
