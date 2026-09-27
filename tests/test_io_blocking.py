"""Testes de integração para operações de E/S bloqueante e concorrência."""

from simulator.core.engine import SimulationEngine
from simulator.entities.operation import Operation, OperationType
from simulator.entities.process import Process
from simulator.entities.states import ThreadState
from simulator.entities.thread import SimulatedThread
from simulator.scheduler.fcfs import FCFSPolicy
from simulator.scheduler.scheduler import Scheduler


def test_single_thread_io_blocking_and_unblocking() -> None:
    """Verifica que a thread bloqueia em E/S e retoma após conclusão."""
    p = Process(pid=1, priority=1, arrival_time=0)
    t = SimulatedThread(
        tid=1,
        process_id=1,
        priority=1,
        arrival_time=0,
        operations=[
            Operation(OperationType.CPU, 3),
            Operation(OperationType.IO, 4),
            Operation(OperationType.CPU, 2),
        ],
    )
    p.add_thread(t)

    engine = SimulationEngine(scheduler=Scheduler(FCFSPolicy(), context_switch_cost=0))
    engine.load_workload([p])

    sys_m, proc_m = engine.run()

    # t=0..3: CPU (3)
    # t=3..7: E/S (4) - CPU ociosa!
    # t=7..9: CPU (2)
    assert sys_m.total_simulation_time == 9
    assert sys_m.useful_cpu_time == 5
    assert sys_m.idle_time == 4  # Ficou ociosa durante a E/S
    assert proc_m[0].threads_metrics[0].total_io_time == 4
    assert proc_m[0].threads_metrics[0].total_cpu_time == 5
    assert proc_m[0].turnaround_time == 9


def test_concurrent_execution_while_one_thread_is_blocked() -> None:
    """Verifica que outra thread executa enquanto a primeira está bloqueada em E/S."""
    # P1 faz CPU (2), E/S (5), CPU (2)
    p1 = Process(pid=1, priority=1, arrival_time=0)
    t1 = SimulatedThread(
        tid=1, process_id=1, priority=1, arrival_time=0,
        operations=[
            Operation(OperationType.CPU, 2),
            Operation(OperationType.IO, 5),
            Operation(OperationType.CPU, 2),
        ],
    )
    p1.add_thread(t1)

    # P2 faz CPU (4)
    p2 = Process(pid=2, priority=1, arrival_time=1)
    t2 = SimulatedThread(
        tid=1, process_id=2, priority=1, arrival_time=1,
        operations=[Operation(OperationType.CPU, 4)],
    )
    p2.add_thread(t2)

    engine = SimulationEngine(scheduler=Scheduler(FCFSPolicy(), context_switch_cost=0))
    engine.load_workload([p1, p2])

    sys_m, proc_m = engine.run()

    # Cronograma:
    # t=0..2: P1 executa
    # t=2: P1 bloqueia em E/S (conclusão em t=2+5=7). P2 é despachada!
    # t=2..6: P2 executa CPU (4). Termina em t=6.
    # t=6..7: CPU ociosa (1 tick) esperando E/S de P1 terminar em t=7.
    # t=7: P1 conclui E/S, volta à fila de prontos e é despachada.
    # t=7..9: P1 executa 2º surto de CPU (2). Termina em t=9.
    assert sys_m.total_simulation_time == 9
    assert sys_m.useful_cpu_time == 8  # P1 (2 + 2) + P2 (4) = 8
    assert sys_m.idle_time == 1        # ociosa apenas em [6..7]
    assert sys_m.useful_cpu_utilization == round((8 / 9) * 100.0, 2)

    # P2 executou em [2..6], terminando em 6
    assert proc_m[1].completion_time == 6


def test_multithread_same_process_interleaving() -> None:
    """Verifica que outra thread do MESMO processo executa enquanto a irmã está bloqueada."""
    p = Process(pid=1, priority=1, arrival_time=0)
    t1 = SimulatedThread(
        tid=1, process_id=1, priority=1, arrival_time=0,
        operations=[
            Operation(OperationType.CPU, 2),
            Operation(OperationType.IO, 4),
            Operation(OperationType.CPU, 2),
        ],
    )
    t2 = SimulatedThread(
        tid=2, process_id=1, priority=1, arrival_time=0,
        operations=[
            Operation(OperationType.CPU, 3),
        ],
    )
    p.add_thread(t1)
    p.add_thread(t2)

    engine = SimulationEngine(scheduler=Scheduler(FCFSPolicy(), context_switch_cost=0))
    engine.load_workload([p])

    sys_m, proc_m = engine.run()

    # Cronograma:
    # t=0..2: T1 executa CPU (2).
    # t=2: T1 bloqueia em E/S (conclusão em t=6). T2 despachada!
    # t=2..5: T2 executa CPU (3). Termina em t=5.
    # t=5..6: CPU ociosa (1 tick).
    # t=6..8: T1 conclui E/S e executa CPU (2). Termina em t=8.
    assert sys_m.total_simulation_time == 8
    assert sys_m.useful_cpu_time == 7  # 2 + 3 + 2 = 7
    assert sys_m.idle_time == 1
    assert p.is_terminated()
    assert p.completion_time == 8
