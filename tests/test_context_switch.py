"""Testes unitários e de integração para a sobrecarga de troca de contexto."""

from simulator.core.engine import SimulationEngine
from simulator.entities.operation import Operation, OperationType
from simulator.entities.process import Process
from simulator.entities.thread import SimulatedThread
from simulator.io.io_manager import SimplifiedIOManager
from simulator.scheduler.fcfs import FCFSPolicy
from simulator.scheduler.scheduler import Scheduler


def build_two_proc_system(arrival1: int = 0, burst1: int = 3, arrival2: int = 0, burst2: int = 3) -> list[Process]:
    p1 = Process(pid=1, priority=1, arrival_time=arrival1)
    p1.add_thread(SimulatedThread(1, 1, 1, arrival1, [Operation(OperationType.CPU, burst1)]))

    p2 = Process(pid=2, priority=1, arrival_time=arrival2)
    p2.add_thread(SimulatedThread(1, 2, 1, arrival2, [Operation(OperationType.CPU, burst2)]))

    return [p1, p2]


def test_context_switch_cost_zero() -> None:
    """Verifica comportamento com custo zero de troca de contexto."""
    procs = build_two_proc_system(arrival1=0, burst1=4, arrival2=0, burst2=4)
    scheduler = Scheduler(policy=FCFSPolicy(), context_switch_cost=0)
    engine = SimulationEngine(scheduler=scheduler)
    engine.load_workload(procs)

    system_metrics, process_metrics = engine.run()

    # P1 executa [0..4], P2 executa [4..8]
    assert system_metrics.total_simulation_time == 8
    assert system_metrics.useful_cpu_time == 8
    assert system_metrics.context_switch_time == 0
    assert system_metrics.context_switches_count == 2
    assert system_metrics.useful_cpu_utilization == 100.0
    assert system_metrics.overhead_percentage == 0.0

    # Resposta de P1 é 0, de P2 é 4
    assert process_metrics[0].threads_metrics[0].response_time == 0
    assert process_metrics[1].threads_metrics[0].response_time == 4


def test_context_switch_cost_positive() -> None:
    """Verifica sobrecarga temporal acumulada com custo de troca de contexto positivo."""
    procs = build_two_proc_system(arrival1=0, burst1=4, arrival2=0, burst2=4)
    # Custo de 2 ticks por troca de contexto
    scheduler = Scheduler(policy=FCFSPolicy(), context_switch_cost=2)
    engine = SimulationEngine(scheduler=scheduler)
    engine.load_workload(procs)

    system_metrics, process_metrics = engine.run()

    # Cronograma esperado:
    # t=0: Chegam P1 e P2. Inicia troca de contexto para P1 (0..2).
    # t=2: P1 inicia execução útil (2..6).
    # t=6: P1 termina. Inicia troca de contexto para P2 (6..8).
    # t=8: P2 inicia execução útil (8..12).
    # t=12: P2 termina.
    assert system_metrics.total_simulation_time == 12
    assert system_metrics.useful_cpu_time == 8
    assert system_metrics.context_switch_time == 4  # 2 trocas * 2 ticks
    assert system_metrics.context_switches_count == 2
    assert system_metrics.idle_time == 0
    assert system_metrics.useful_cpu_utilization == round((8 / 12) * 100.0, 2)
    assert system_metrics.overhead_percentage == round((4 / 12) * 100.0, 2)

    # Tempos de resposta com a sobrecarga de 2 ticks:
    # P1 começou no tick 2 -> resposta = 2 - 0 = 2 (exatamente o custo da troca inicial!)
    # P2 começou no tick 8 -> resposta = 8 - 0 = 8
    assert process_metrics[0].threads_metrics[0].response_time == 2
    assert process_metrics[1].threads_metrics[0].response_time == 8

    # Tempos de espera:
    # P1 esperou 0 na fila antes da seleção
    # P2 esperou 6 na fila até ser selecionado
    assert process_metrics[0].threads_metrics[0].waiting_time == 0
    assert process_metrics[1].threads_metrics[0].waiting_time == 6
