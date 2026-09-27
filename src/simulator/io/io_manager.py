"""Gerenciamento simplificado de operações de E/S bloqueante.

Nesta primeira entrega, implementa-se o modelo de E/S por evento com duração
definida na carga. A thread bloqueia, libera a CPU e retorna à fila de prontos
após a conclusão (interrupção simulada).

Pontos de extensão para a Entrega Final:
- Dispositivos de bloco e caractere independentes com filas próprias.
- Escalonamento de disco (SSTF/SCAN).
- Operações de E/S não bloqueantes.
"""

from typing import Optional

from simulator.entities.states import ThreadState
from simulator.entities.thread import SimulatedThread


class SimplifiedIOManager:
    """Gerenciador de E/S simplificado para a primeira entrega."""

    def __init__(self) -> None:
        # Mapeia tid_str -> SimulatedThread para rastreamento de threads bloqueadas em E/S
        self._blocked_threads: dict[str, SimulatedThread] = {}

    def start_io(
        self,
        thread: SimulatedThread,
        duration: int,
        current_time: int,
        cause: str = "Início de operação de E/S bloqueante",
    ) -> int:
        """Inicia a operação de E/S para a thread, transicionando-a para BLOQUEADO.

        Args:
            thread: Thread solicitante da E/S.
            duration: Duração da operação de E/S.
            current_time: Instante do relógio lógico atual.
            cause: Descrição da causa do bloqueio.

        Returns:
            O instante de tempo lógico previsto para a conclusão da E/S.
        """
        thread.transition_to(ThreadState.BLOCKED, current_time, cause)
        thread.tcb.total_io_time += duration
        self._blocked_threads[thread.id_str] = thread
        return current_time + duration

    def complete_io(
        self,
        thread: SimulatedThread,
        current_time: int,
        cause: str = "Conclusão de operação de E/S (interrupção simulada)",
    ) -> SimulatedThread:
        """Processa a interrupção de conclusão de E/S, liberando a thread.

        A thread avança sua operação (passando para o próximo surto de CPU)
        e é removida do conjunto de bloqueadas.
        """
        if thread.id_str in self._blocked_threads:
            del self._blocked_threads[thread.id_str]

        # Avança a operação atual concluída (de E/S para a próxima operação)
        thread.advance_operation()
        return thread

    def get_blocked_count(self) -> int:
        """Retorna a quantidade de threads atualmente bloqueadas em E/S."""
        return len(self._blocked_threads)

    def is_blocked(self, thread: SimulatedThread) -> bool:
        """Verifica se uma determinada thread está atualmente aguardando E/S."""
        return thread.id_str in self._blocked_threads

    def __repr__(self) -> str:
        return f"SimplifiedIOManager(blocked_threads={list(self._blocked_threads.keys())})"
