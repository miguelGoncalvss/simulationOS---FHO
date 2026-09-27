"""Coleta, cálculo e formatação de métricas de desempenho da simulação."""

from dataclasses import dataclass
from typing import Any, Optional

from simulator.entities.process import Process
from simulator.entities.thread import SimulatedThread


@dataclass
class ThreadMetrics:
    """Métricas individuais de uma thread simulada."""
    pid: int
    tid: int
    id_str: str
    arrival_time: int
    first_execution_time: Optional[int]
    completion_time: Optional[int]
    turnaround_time: Optional[int]
    waiting_time: int
    response_time: Optional[int]
    total_cpu_time: int
    total_io_time: int


@dataclass
class ProcessMetrics:
    """Métricas agregadas de um processo simulado."""
    pid: int
    creation_time: int
    completion_time: Optional[int]
    turnaround_time: Optional[int]
    threads_count: int
    threads_metrics: list[ThreadMetrics]


@dataclass
class SystemMetrics:
    """Métricas globais do sistema operacional simulado."""
    total_simulation_time: int
    useful_cpu_time: int
    context_switch_time: int
    idle_time: int
    useful_cpu_utilization: float
    overhead_percentage: float
    throughput: float
    context_switches_count: int
    completed_processes_count: int
    total_processes_count: int


class MetricsCollector:
    """Calculador e formatador de métricas da simulação."""

    def __init__(self) -> None:
        pass

    def compute(
        self,
        processes: list[Process],
        total_simulation_time: int,
        context_switches_count: int,
        total_context_switch_time: int,
    ) -> tuple[SystemMetrics, list[ProcessMetrics]]:
        """Calcula todas as métricas a partir dos processos e parâmetros da simulação.

        Trata explicitamente casos de horizonte zero (divisão por zero).
        """
        process_metrics_list: list[ProcessMetrics] = []
        total_useful_cpu = 0

        for proc in processes:
            t_metrics_list: list[ThreadMetrics] = []
            for t in proc.threads:
                tcb = t.tcb
                turnaround = (
                    tcb.completion_time - tcb.arrival_time
                    if tcb.completion_time is not None
                    else None
                )
                response = (
                    tcb.first_execution_time - tcb.arrival_time
                    if tcb.first_execution_time is not None
                    else None
                )
                total_useful_cpu += tcb.total_cpu_time

                t_metrics = ThreadMetrics(
                    pid=proc.pid,
                    tid=t.tid,
                    id_str=t.id_str,
                    arrival_time=tcb.arrival_time,
                    first_execution_time=tcb.first_execution_time,
                    completion_time=tcb.completion_time,
                    turnaround_time=turnaround,
                    waiting_time=tcb.total_ready_wait_time,
                    response_time=response,
                    total_cpu_time=tcb.total_cpu_time,
                    total_io_time=tcb.total_io_time,
                )
                t_metrics_list.append(t_metrics)

            proc_turnaround = (
                proc.completion_time - proc.creation_time
                if proc.completion_time is not None
                else None
            )

            p_metrics = ProcessMetrics(
                pid=proc.pid,
                creation_time=proc.creation_time,
                completion_time=proc.completion_time,
                turnaround_time=proc_turnaround,
                threads_count=len(proc.threads),
                threads_metrics=t_metrics_list,
            )
            process_metrics_list.append(p_metrics)

        # Cálculo do tempo ocioso e proporções
        completed_procs = sum(1 for p in processes if p.is_terminated())
        useful_cpu = total_useful_cpu
        cs_time = total_context_switch_time
        sim_time = max(0, total_simulation_time)
        idle_time = max(0, sim_time - useful_cpu - cs_time)

        if sim_time > 0:
            useful_util = (useful_cpu / sim_time) * 100.0
            overhead_pct = (cs_time / sim_time) * 100.0
            throughput = completed_procs / sim_time
        else:
            useful_util = 0.0
            overhead_pct = 0.0
            throughput = 0.0

        system_metrics = SystemMetrics(
            total_simulation_time=sim_time,
            useful_cpu_time=useful_cpu,
            context_switch_time=cs_time,
            idle_time=idle_time,
            useful_cpu_utilization=round(useful_util, 2),
            overhead_percentage=round(overhead_pct, 2),
            throughput=round(throughput, 4),
            context_switches_count=context_switches_count,
            completed_processes_count=completed_procs,
            total_processes_count=len(processes),
        )

        return system_metrics, process_metrics_list

    def format_report(
        self,
        system_metrics: SystemMetrics,
        process_metrics: list[ProcessMetrics],
    ) -> str:
        """Formata relatório textual completo com tabelas alinhadas."""
        lines = [
            "=" * 78,
            "RELATÓRIO DE MÉTRICAS E DESEMPENHO DA SIMULAÇÃO",
            "=" * 78,
            "1. MÉTRICAS GLOBAIS DO SISTEMA:",
            f"  Tempo total simulado (horizonte):    {system_metrics.total_simulation_time:>8} ticks",
            f"  Tempo útil de CPU:                   {system_metrics.useful_cpu_time:>8} ticks",
            f"  Sobrecarga de troca de contexto:     {system_metrics.context_switch_time:>8} ticks",
            f"  Tempo de CPU ociosa:                 {system_metrics.idle_time:>8} ticks",
            f"  Utilização útil da CPU:              {system_metrics.useful_cpu_utilization:>7.2f}%",
            f"  Sobrecarga de trocas de contexto:    {system_metrics.overhead_percentage:>7.2f}%",
            f"  Quantidade de trocas de contexto:    {system_metrics.context_switches_count:>8}",
            f"  Throughput de processos:             {system_metrics.throughput:>8.4f} proc/tick",
            f"  Processos finalizados:               {system_metrics.completed_processes_count:>4} / {system_metrics.total_processes_count}",
            "-" * 78,
            "2. MÉTRICAS POR THREAD (UNIDADE ESCALONÁVEL):",
            f"  {'Thread':<10} | {'Chegada':>7} | {'Início':>7} | {'Fim':>7} | {'Retorno':>7} | {'Espera':>7} | {'Resposta':>8} | {'CPU':>5} | {'E/S':>5}",
            "  " + "-" * 74,
        ]

        for p in process_metrics:
            for t in p.threads_metrics:
                start_str = str(t.first_execution_time) if t.first_execution_time is not None else "-"
                end_str = str(t.completion_time) if t.completion_time is not None else "-"
                ret_str = str(t.turnaround_time) if t.turnaround_time is not None else "-"
                resp_str = str(t.response_time) if t.response_time is not None else "-"
                lines.append(
                    f"  {t.id_str:<10} | {t.arrival_time:>7} | {start_str:>7} | {end_str:>7} | "
                    f"{ret_str:>7} | {t.waiting_time:>7} | {resp_str:>8} | {t.total_cpu_time:>5} | {t.total_io_time:>5}"
                )

        lines.extend([
            "-" * 78,
            "3. MÉTRICAS POR PROCESSO:",
            f"  {'PID':<6} | {'Criação':>7} | {'Término':>7} | {'Retorno':>7} | {'Threads':>7}",
            "  " + "-" * 45,
        ])

        for p in process_metrics:
            end_str = str(p.completion_time) if p.completion_time is not None else "-"
            ret_str = str(p.turnaround_time) if p.turnaround_time is not None else "-"
            lines.append(
                f"  {p.pid:<6} | {p.creation_time:>7} | {end_str:>7} | {ret_str:>7} | {p.threads_count:>7}"
            )

        lines.append("=" * 78)
        return "\n".join(lines)
