"""Definição de operações executadas por uma thread (surto de CPU e E/S)."""

from dataclasses import dataclass
from enum import Enum


class OperationType(Enum):
    """Tipo de operação de uma thread simulada."""
    CPU = "CPU"
    IO = "IO"


@dataclass(frozen=True)
class Operation:
    """Representa um surto de CPU ou uma operação de E/S."""
    op_type: OperationType
    duration: int

    def __post_init__(self) -> None:
        if self.duration <= 0:
            raise ValueError(f"Duração da operação deve ser estritamente positiva (> 0): {self.duration}")

    def __repr__(self) -> str:
        return f"{self.op_type.value}({self.duration})"
