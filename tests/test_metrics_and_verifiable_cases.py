"""Testes de validação dos cenários verificáveis manualmente e das métricas."""

from pathlib import Path

from simulator.core.engine import SimulationEngine
from simulator.entities.process import Process
from simulator.loader.workload_loader import WorkloadLoader
from simulator.metrics.collector import MetricsCollector
from simulator.scheduler.fcfs import FCFSPolicy
from simulator.scheduler.scheduler import Scheduler


def test_verifiable_fcfs_case_from_prompt() -> None:
    """Verifica com exatidão o caso verificável obrigatório do enunciado:

    - P1: chegada 0, CPU 3.
    - P2: chegada 1, CPU 2.
    - P3: chegada 2, CPU 1.

    Resultado esperado:
    - P1 executa de 0 a 3.
    - P2 executa de 3 a 5.
    - P3 executa de 5 a 6.
    - Esperas e respostas: 0, 2 e 3.
    - Retornos: 3, 4 e 4.
    - Utilização útil: 100%.
    - Throughput: 3/6 = 0,5 processo por unidade de tempo.
    """
    workload_path = Path(__file__).resolve().parent.parent / "workloads" / "verificacao_fcfs.json"
    processes = WorkloadLoader.load_from_file(workload_path)

    scheduler = Scheduler(policy=FCFSPolicy(), context_switch_cost=0)
    engine = SimulationEngine(scheduler=scheduler)
    engine.load_workload(processes)

    sys_m, proc_m = engine.run()

    # 1. P1 executa de 0 a 3, P2 de 3 a 5, P3 de 5 a 6
    p1_t = proc_m[0].threads_metrics[0]
    p2_t = proc_m[1].threads_metrics[0]
    p3_t = proc_m[2].threads_metrics[0]

    assert p1_t.first_execution_time == 0
    assert p1_t.completion_time == 3

    assert p2_t.first_execution_time == 3
    assert p2_t.completion_time == 5

    assert p3_t.first_execution_time == 5
    assert p3_t.completion_time == 6

    # 2. Esperas: 0, 2 e 3
    assert p1_t.waiting_time == 0
    assert p2_t.waiting_time == 2
    assert p3_t.waiting_time == 3

    # 3. Respostas: 0, 2 e 3
    assert p1_t.response_time == 0
    assert p2_t.response_time == 2
    assert p3_t.response_time == 3

    # 4. Retornos por processo: 3, 4 e 4
    assert proc_m[0].turnaround_time == 3
    assert proc_m[1].turnaround_time == 4
    assert proc_m[2].turnaround_time == 4

    # 5. Utilização útil: 100%
    assert sys_m.useful_cpu_time == 6
    assert sys_m.total_simulation_time == 6
    assert sys_m.useful_cpu_utilization == 100.0

    # 6. Throughput: 3/6 = 0.5 processo por unidade de tempo
    assert sys_m.throughput == 0.5


def test_verifiable_io_scenario() -> None:
    """Verifica cenário de E/S com conferência analítica."""
    workload_path = Path(__file__).resolve().parent.parent / "workloads" / "verificacao_io.json"
    processes = WorkloadLoader.load_from_file(workload_path)

    scheduler = Scheduler(policy=FCFSPolicy(), context_switch_cost=0)
    engine = SimulationEngine(scheduler=scheduler)
    engine.load_workload(processes)

    sys_m, proc_m = engine.run()

    # P1 (PID 1): chegada 0, CPU 2, IO 3, CPU 2 -> Término = 7, Retorno = 7, Espera = 0
    # P2 (PID 2): chegada 1, CPU 3 -> Início = 2, Término = 5, Retorno = 4, Espera = 1
    p1 = proc_m[0]
    p2 = proc_m[1]

    assert p1.completion_time == 7
    assert p1.turnaround_time == 7
    assert p1.threads_metrics[0].waiting_time == 0
    assert p1.threads_metrics[0].response_time == 0

    assert p2.completion_time == 5
    assert p2.turnaround_time == 4
    assert p2.threads_metrics[0].waiting_time == 1
    assert p2.threads_metrics[0].response_time == 1

    assert sys_m.total_simulation_time == 7
    assert sys_m.useful_cpu_time == 7
    assert sys_m.idle_time == 0
    assert sys_m.useful_cpu_utilization == 100.0


def test_zero_horizon_handling() -> None:
    """Garante que cenários vazios ou de tempo zero não causem divisão por zero."""
    collector = MetricsCollector()
    sys_m, proc_m = collector.compute(
        processes=[],
        total_simulation_time=0,
        context_switches_count=0,
        total_context_switch_time=0,
    )

    assert sys_m.total_simulation_time == 0
    assert sys_m.useful_cpu_utilization == 0.0
    assert sys_m.overhead_percentage == 0.0
    assert sys_m.throughput == 0.0

    report = collector.format_report(sys_m, proc_m)
    assert "0 ticks" in report
