"""Núcleo da simulação: relógio lógico, fila de eventos e motor central."""

from simulator.core.clock import Clock
from simulator.core.engine import SimulationEngine
from simulator.core.event import Event, EventType
from simulator.core.event_queue import EventQueue

__all__ = ["Clock", "Event", "EventType", "EventQueue", "SimulationEngine"]
