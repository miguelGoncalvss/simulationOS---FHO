"""Módulo de escalonamento do simulador."""

from simulator.scheduler.cpu import CPUState, SimulatedCPU
from simulator.scheduler.fcfs import FCFSPolicy
from simulator.scheduler.policy import SchedulingPolicy
from simulator.scheduler.scheduler import Scheduler

__all__ = [
    "CPUState",
    "SimulatedCPU",
    "SchedulingPolicy",
    "FCFSPolicy",
    "Scheduler",
]
