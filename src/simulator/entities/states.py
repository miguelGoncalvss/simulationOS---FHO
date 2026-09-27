"""Definição de estados e regras de transição para processos e threads."""

from enum import Enum, auto
from typing import Final


class ProcessState(Enum):
    """Estados possíveis de um processo no ciclo de vida simulado."""
    NEW = "NOVO"
    READY = "PRONTO"
    RUNNING = "EXECUTANDO"
    BLOCKED = "BLOQUEADO"
    TERMINATED = "FINALIZADO"


class ThreadState(Enum):
    """Estados possíveis de uma thread no ciclo de vida simulado."""
    NEW = "NOVO"
    READY = "PRONTO"
    RUNNING = "EXECUTANDO"
    BLOCKED = "BLOQUEADO"
    TERMINATED = "FINALIZADO"


class InvalidStateTransitionError(Exception):
    """Exceção levantada quando uma transição de estado ilegal é tentada."""

    def __init__(
        self,
        entity_name: str,
        entity_id: str,
        source_state: str,
        target_state: str,
        cause: str,
    ) -> None:
        super().__init__(
            f"Transição de estado inválida para {entity_name} [{entity_id}]: "
            f"{source_state} -> {target_state} (Causa: {cause})"
        )
        self.entity_name = entity_name
        self.entity_id = entity_id
        self.source_state = source_state
        self.target_state = target_state
        self.cause = cause


# Grafo de transições válidas para uma thread simulada
VALID_THREAD_TRANSITIONS: Final[dict[ThreadState, set[ThreadState]]] = {
    ThreadState.NEW: {ThreadState.READY},
    ThreadState.READY: {ThreadState.RUNNING},
    ThreadState.RUNNING: {ThreadState.BLOCKED, ThreadState.READY, ThreadState.TERMINATED},
    ThreadState.BLOCKED: {ThreadState.READY},
    ThreadState.TERMINATED: set(),
}


def validate_thread_transition(
    thread_id: str,
    current_state: ThreadState,
    target_state: ThreadState,
    cause: str,
) -> None:
    """Valida se uma transição de estado da thread é permitida pelo modelo.

    Raises:
        InvalidStateTransitionError: Se a transição for proibida.
    """
    allowed_targets = VALID_THREAD_TRANSITIONS.get(current_state, set())
    if target_state not in allowed_targets:
        raise InvalidStateTransitionError(
            entity_name="Thread",
            entity_id=thread_id,
            source_state=current_state.value,
            target_state=target_state.value,
            cause=cause,
        )
