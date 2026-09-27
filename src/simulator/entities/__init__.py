"""Entidades fundamentais da simulação de SO."""

from simulator.entities.operation import Operation, OperationType
from simulator.entities.pcb import PCB
from simulator.entities.process import Process
from simulator.entities.states import (
    InvalidStateTransitionError,
    ProcessState,
    ThreadState,
    validate_thread_transition,
)
from simulator.entities.tcb import TCB
from simulator.entities.thread import SimulatedThread

__all__ = [
    "Operation",
    "OperationType",
    "ProcessState",
    "ThreadState",
    "InvalidStateTransitionError",
    "validate_thread_transition",
    "TCB",
    "SimulatedThread",
    "PCB",
    "Process",
]
