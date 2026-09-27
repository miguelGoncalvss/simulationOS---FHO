"""Testes de determinismo das simulações e validação da CLI."""

from pathlib import Path
import pytest

from simulator.core.engine import SimulationEngine
from simulator.loader.workload_loader import WorkloadLoader
from simulator.main import main, parse_arguments, validate_cli_options
from simulator.metrics.logger import EventLogger
from simulator.scheduler.fcfs import FCFSPolicy
from simulator.scheduler.scheduler import Scheduler


def test_determinism_identical_runs() -> None:
    """Verifica que duas execuções independentes da mesma carga geram resultados idênticos."""
    workload_path = Path(__file__).resolve().parent.parent / "workloads" / "mixed.json"

    # Execução 1
    procs1 = WorkloadLoader.load_from_file(workload_path)
    logger1 = EventLogger()
    engine1 = SimulationEngine(
        scheduler=Scheduler(FCFSPolicy(), context_switch_cost=1),
        logger=logger1,
    )
    engine1.load_workload(procs1)
    sys_m1, proc_m1 = engine1.run()
    log1 = [entry.to_line() for entry in logger1.entries]

    # Execução 2
    procs2 = WorkloadLoader.load_from_file(workload_path)
    logger2 = EventLogger()
    engine2 = SimulationEngine(
        scheduler=Scheduler(FCFSPolicy(), context_switch_cost=1),
        logger=logger2,
    )
    engine2.load_workload(procs2)
    sys_m2, proc_m2 = engine2.run()
    log2 = [entry.to_line() for entry in logger2.entries]

    # Logs devem ser idênticos linha por linha
    assert log1 == log2

    # Métricas globais devem ser exatamente iguais
    assert sys_m1.total_simulation_time == sys_m2.total_simulation_time
    assert sys_m1.useful_cpu_time == sys_m2.useful_cpu_time
    assert sys_m1.context_switch_time == sys_m2.context_switch_time
    assert sys_m1.idle_time == sys_m2.idle_time
    assert sys_m1.useful_cpu_utilization == sys_m2.useful_cpu_utilization
    assert sys_m1.throughput == sys_m2.throughput

    # Métricas por processo devem ser exatamente iguais
    for p1, p2 in zip(proc_m1, proc_m2):
        assert p1.pid == p2.pid
        assert p1.completion_time == p2.completion_time
        assert p1.turnaround_time == p2.turnaround_time


def test_cli_rejects_unsupported_policies() -> None:
    """CLI deve rejeitar com mensagem clara políticas não implementadas nesta entrega."""
    # Round Robin
    args_rr = parse_arguments(["-w", "workloads/cpu_bound.json", "--policy", "RR"])
    with pytest.raises(SystemExit) as exc_info:
        validate_cli_options(args_rr)
    assert exc_info.value.code == 2

    # Prioridades
    args_prio = parse_arguments(["-w", "workloads/cpu_bound.json", "--policy", "PRIORITY"])
    with pytest.raises(SystemExit) as exc_info:
        validate_cli_options(args_prio)
    assert exc_info.value.code == 2


def test_cli_rejects_quantum_in_first_delivery() -> None:
    """CLI deve rejeitar parâmetro --quantum na primeira entrega."""
    args = parse_arguments(["-w", "workloads/cpu_bound.json", "--quantum", "4"])
    with pytest.raises(SystemExit) as exc_info:
        validate_cli_options(args)
    assert exc_info.value.code == 2


def test_cli_rejects_negative_context_switch() -> None:
    """CLI deve rejeitar custo de troca de contexto negativo."""
    args = parse_arguments(["-w", "workloads/cpu_bound.json", "-c", "-1"])
    with pytest.raises(SystemExit) as exc_info:
        validate_cli_options(args)
    assert exc_info.value.code == 2
