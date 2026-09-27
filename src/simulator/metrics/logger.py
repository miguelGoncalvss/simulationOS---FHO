"""Registro determinístico de eventos da simulação."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class LogEntry:
    """Entrada estruturada no log de eventos."""
    clock: int
    event_type: str
    pid: Optional[int]
    tid: Optional[int]
    description: str

    def to_line(self) -> str:
        """Formata a linha de log determinística sem timestamps reais."""
        pid_str = f"{self.pid}" if self.pid is not None else "-"
        tid_str = f"{self.tid}" if self.tid is not None else "-"
        entity_str = f"P{pid_str}-T{tid_str}" if (self.pid is not None or self.tid is not None) else "SYSTEM"
        return f"[Clock: {self.clock:>4}] [{self.event_type:<20}] [{entity_str:<10}] {self.description}"


class EventLogger:
    """Logger de eventos da simulação com saída determinística e estruturada."""

    def __init__(self, config_summary: Optional[str] = None) -> None:
        self.config_summary: str = config_summary or ""
        self.entries: list[LogEntry] = []

    def log(
        self,
        clock: int,
        event_type: str,
        pid: Optional[int] = None,
        tid: Optional[int] = None,
        description: str = "",
    ) -> LogEntry:
        """Registra uma nova ocorrência no log."""
        entry = LogEntry(
            clock=clock,
            event_type=event_type,
            pid=pid,
            tid=tid,
            description=description,
        )
        self.entries.append(entry)
        return entry

    def set_config(self, summary: str) -> None:
        """Define o resumo de configuração da simulação."""
        self.config_summary = summary

    def get_text(self) -> str:
        """Gera o texto completo do log com cabeçalho de configuração."""
        lines = [
            "=" * 78,
            "SIMULADOR DIDÁTICO DE SISTEMAS OPERACIONAIS - REGISTRO DE EVENTOS",
            "=" * 78,
        ]
        if self.config_summary:
            lines.append("CONFIGURAÇÃO DA EXECUÇÃO:")
            for conf_line in self.config_summary.strip().splitlines():
                lines.append(f"  {conf_line}")
            lines.append("-" * 78)
        lines.append("HISTÓRICO DE EVENTOS:")
        for entry in self.entries:
            lines.append(entry.to_line())
        lines.append("=" * 78)
        return "\n".join(lines)

    def write_to_file(self, filepath: str | Path) -> None:
        """Grava o log em arquivo textual."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.get_text(), encoding="utf-8")
