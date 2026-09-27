"""Testes unitários para validação e carregamento de arquivos de carga."""

import json
import pytest

from simulator.loader.workload_loader import (
    WorkloadLoader,
    WorkloadValidationError,
)


def test_valid_workload_loading(tmp_path) -> None:
    """Verifica carregamento com sucesso de um arquivo JSON válido."""
    content = {
        "processes": [
            {
                "pid": 1,
                "arrival_time": 0,
                "priority": 1,
                "threads": [
                    {
                        "tid": 1,
                        "operations": [
                            {"type": "CPU", "duration": 4},
                            {"type": "IO", "duration": 2},
                            {"type": "CPU", "duration": 3},
                        ],
                    }
                ],
            }
        ]
    }
    file = tmp_path / "valid.json"
    file.write_text(json.dumps(content), encoding="utf-8")

    processes = WorkloadLoader.load_from_file(file)
    assert len(processes) == 1
    assert processes[0].pid == 1
    assert len(processes[0].threads) == 1
    assert len(processes[0].threads[0].operations) == 3


def test_workload_file_not_found() -> None:
    """Arquivo inexistente deve lançar WorkloadValidationError."""
    with pytest.raises(WorkloadValidationError, match="não encontrado"):
        WorkloadLoader.load_from_file("caminho_inexistente_123.json")


def test_workload_rejects_missing_processes() -> None:
    """JSON sem o campo processes deve ser rejeitado."""
    with pytest.raises(WorkloadValidationError, match="processes"):
        WorkloadLoader.load_from_dict({"outra_chave": []})


def test_workload_rejects_duplicate_pid() -> None:
    """PIDs duplicados devem ser rejeitados."""
    data = {
        "processes": [
            {"pid": 1, "arrival_time": 0, "threads": [{"tid": 1, "operations": [{"type": "CPU", "duration": 1}]}]},
            {"pid": 1, "arrival_time": 2, "threads": [{"tid": 1, "operations": [{"type": "CPU", "duration": 1}]}]},
        ]
    }
    with pytest.raises(WorkloadValidationError, match="PID duplicado"):
        WorkloadLoader.load_from_dict(data)


def test_workload_rejects_negative_arrival() -> None:
    """arrival_time negativo deve ser rejeitado."""
    data = {
        "processes": [
            {"pid": 1, "arrival_time": -5, "threads": [{"tid": 1, "operations": [{"type": "CPU", "duration": 1}]}]}
        ]
    }
    with pytest.raises(WorkloadValidationError, match="arrival_time"):
        WorkloadLoader.load_from_dict(data)


def test_workload_rejects_duplicate_tid_in_process() -> None:
    """TIDs duplicados no mesmo processo devem ser rejeitados."""
    data = {
        "processes": [
            {
                "pid": 1,
                "arrival_time": 0,
                "threads": [
                    {"tid": 1, "operations": [{"type": "CPU", "duration": 2}]},
                    {"tid": 1, "operations": [{"type": "CPU", "duration": 3}]},
                ],
            }
        ]
    }
    with pytest.raises(WorkloadValidationError, match="TID duplicado"):
        WorkloadLoader.load_from_dict(data)


def test_workload_rejects_non_alternating_operations() -> None:
    """Operações consecutivas do mesmo tipo devem ser rejeitadas."""
    # Dois CPUs seguidos
    data = {
        "processes": [
            {
                "pid": 1,
                "arrival_time": 0,
                "threads": [
                    {
                        "tid": 1,
                        "operations": [
                            {"type": "CPU", "duration": 2},
                            {"type": "CPU", "duration": 3},
                        ],
                    }
                ],
            }
        ]
    }
    with pytest.raises(WorkloadValidationError, match="operações consecutivas do mesmo tipo"):
        WorkloadLoader.load_from_dict(data)


def test_workload_rejects_starting_or_ending_with_io() -> None:
    """Thread não pode começar nem terminar com IO."""
    # Começa com IO
    data1 = {
        "processes": [
            {
                "pid": 1,
                "arrival_time": 0,
                "threads": [
                    {"tid": 1, "operations": [{"type": "IO", "duration": 2}, {"type": "CPU", "duration": 3}]}
                ],
            }
        ]
    }
    with pytest.raises(WorkloadValidationError, match="deve iniciar com surto de CPU"):
        WorkloadLoader.load_from_dict(data1)

    # Termina com IO
    data2 = {
        "processes": [
            {
                "pid": 1,
                "arrival_time": 0,
                "threads": [
                    {"tid": 1, "operations": [{"type": "CPU", "duration": 3}, {"type": "IO", "duration": 2}]}
                ],
            }
        ]
    }
    with pytest.raises(WorkloadValidationError, match="deve terminar com surto de CPU"):
        WorkloadLoader.load_from_dict(data2)


def test_workload_rejects_invalid_duration() -> None:
    """Duração zero ou negativa deve ser rejeitada."""
    data = {
        "processes": [
            {
                "pid": 1,
                "arrival_time": 0,
                "threads": [
                    {"tid": 1, "operations": [{"type": "CPU", "duration": 0}]}
                ],
            }
        ]
    }
    with pytest.raises(WorkloadValidationError, match="deve ser inteiro > 0"):
        WorkloadLoader.load_from_dict(data)
