"""Representação de um processo simulado e seu relacionamento com threads."""

from typing import Optional

from simulator.entities.pcb import PCB
from simulator.entities.states import ProcessState, ThreadState
from simulator.entities.thread import SimulatedThread


class Process:
    """Processo simulado, contendo seu PCB e um conjunto de threads."""

    def __init__(self, pid: int, priority: int, arrival_time: int) -> None:
        self.pcb = PCB(pid=pid, priority=priority, creation_time=arrival_time)
        self._threads: list[SimulatedThread] = []

    @property
    def pid(self) -> int:
        return self.pcb.pid

    @property
    def priority(self) -> int:
        return self.pcb.priority

    @property
    def creation_time(self) -> int:
        return self.pcb.creation_time

    @property
    def completion_time(self) -> Optional[int]:
        return self.pcb.completion_time

    @property
    def state(self) -> ProcessState:
        return self.pcb.state

    @property
    def threads(self) -> list[SimulatedThread]:
        return list(self._threads)

    def add_thread(self, thread: SimulatedThread) -> None:
        """Adiciona uma thread ao processo."""
        if thread.process_id != self.pid:
            raise ValueError(
                f"Thread {thread.id_str} tem process_id diferente do processo {self.pid}"
            )
        self._threads.append(thread)

    def update_derived_state(self, current_time: int, cause: str) -> ProcessState:
        """Deriva o estado do processo a partir dos estados de suas threads.

        Regras de derivação:
        1. Se todas as threads estão FINALIZADAS, o processo está FINALIZADO.
        2. Se ao menos uma thread está EXECUTANDO, o processo está EXECUTANDO.
        3. Se ao menos uma thread está PRONTA (e nenhuma EXECUTANDO), o processo está PRONTO.
        4. Se todas as threads ativas estão BLOQUEADAS, o processo está BLOQUEADO.
        5. Se todas as threads estão NOVAS, o processo está NOVO.

        Returns:
            O estado derivado atualizado do processo.
        """
        if not self._threads:
            return self.pcb.state

        thread_states = [t.state for t in self._threads]

        if all(s == ThreadState.TERMINATED for s in thread_states):
            new_state = ProcessState.TERMINATED
            if self.pcb.completion_time is None:
                self.pcb.completion_time = max(
                    (t.tcb.completion_time or current_time) for t in self._threads
                )
        elif any(s == ThreadState.RUNNING for s in thread_states):
            new_state = ProcessState.RUNNING
        elif any(s == ThreadState.READY for s in thread_states):
            new_state = ProcessState.READY
        elif all(s == ThreadState.BLOCKED for s in thread_states if s != ThreadState.TERMINATED):
            new_state = ProcessState.BLOCKED
        elif all(s == ThreadState.NEW for s in thread_states):
            new_state = ProcessState.NEW
        else:
            new_state = ProcessState.READY

        if new_state != self.pcb.state:
            self.pcb.record_transition(current_time, new_state, cause)

        return self.pcb.state

    def is_terminated(self) -> bool:
        """Indica se o processo foi completamente finalizado."""
        return self.pcb.state == ProcessState.TERMINATED

    @property
    def turnaround_time(self) -> Optional[int]:
        """Tempo de retorno do processo: término da última thread menos criação."""
        if self.pcb.completion_time is None:
            return None
        return self.pcb.completion_time - self.pcb.creation_time

    def __repr__(self) -> str:
        return f"Process({self.pcb}, threads_count={len(self._threads)})"
