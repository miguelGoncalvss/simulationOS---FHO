"""Relógio lógico da simulação.

Mantém o tempo lógico discreto em unidades abstratas inteiras, garantindo
monotonicidade temporal (o relógio nunca retrocede).
"""

from typing import Final


class Clock:
    """Relógio lógico para simulação orientada a eventos discretos."""

    def __init__(self, initial_time: int = 0) -> None:
        if initial_time < 0:
            raise ValueError(f"Tempo inicial não pode ser negativo: {initial_time}")
        self._current_time: int = initial_time

    @property
    def time(self) -> int:
        """Retorna o tempo lógico atual em unidades abstratas inteiras."""
        return self._current_time

    def advance_to(self, new_time: int) -> int:
        """Avança o relógio lógico para o novo tempo especificado.

        Args:
            new_time: Próximo instante de tempo.

        Returns:
            O novo tempo lógico após o avanço.

        Raises:
            ValueError: Se new_time for menor que o tempo atual (tentativa de retrocesso).
        """
        if new_time < self._current_time:
            raise ValueError(
                f"Tentativa de retrocesso temporal: relógio atual={self._current_time}, "
                f"novo tempo={new_time}"
            )
        self._current_time = new_time
        return self._current_time

    def reset(self, initial_time: int = 0) -> None:
        """Reinicia o relógio para o tempo inicial especificado."""
        if initial_time < 0:
            raise ValueError(f"Tempo inicial não pode ser negativo: {initial_time}")
        self._current_time = initial_time

    def __repr__(self) -> str:
        return f"Clock(time={self._current_time})"
