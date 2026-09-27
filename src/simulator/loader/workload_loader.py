"""Carregador e validador de cargas de trabalho em formato JSON."""

import json
from pathlib import Path
from typing import Any

from simulator.entities.operation import Operation, OperationType
from simulator.entities.process import Process
from simulator.entities.thread import SimulatedThread


class WorkloadValidationError(Exception):
    """Exceção levantada quando a carga de trabalho apresenta formato inválido."""
    pass


class WorkloadLoader:
    """Lê, valida e converte especificações JSON em objetos de Processo e Thread."""

    @classmethod
    def load_from_file(cls, filepath: str | Path) -> list[Process]:
        """Carrega e valida a carga de trabalho a partir de um arquivo JSON.

        Args:
            filepath: Caminho do arquivo JSON da carga.

        Returns:
            Lista de instâncias de Process devidamente configuradas.

        Raises:
            WorkloadValidationError: Se o arquivo não existir, não for JSON válido
                                     ou violar as regras de integridade do modelo.
        """
        path = Path(filepath)
        if not path.exists():
            raise WorkloadValidationError(f"Arquivo de carga não encontrado: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise WorkloadValidationError(f"Erro de sintaxe JSON no arquivo {path}: {e}")
        except Exception as e:
            raise WorkloadValidationError(f"Erro ao ler arquivo de carga {path}: {e}")

        return cls.load_from_dict(data)

    @classmethod
    def load_from_dict(cls, data: dict[str, Any]) -> list[Process]:
        """Valida e converte uma estrutura de dados de dicionário em processos.

        Raises:
            WorkloadValidationError: Se houver violação estrutural ou semântica.
        """
        if not isinstance(data, dict):
            raise WorkloadValidationError("A raiz da carga de trabalho deve ser um objeto JSON (dict).")

        if "processes" not in data:
            raise WorkloadValidationError("Campo obrigatório 'processes' ausente na raiz do JSON.")

        processes_data = data["processes"]
        if not isinstance(processes_data, list) or len(processes_data) == 0:
            raise WorkloadValidationError("O campo 'processes' deve ser uma lista não vazia de processos.")

        loaded_processes: list[Process] = []
        seen_pids: set[int] = set()

        for proc_idx, proc_entry in enumerate(processes_data):
            if not isinstance(proc_entry, dict):
                raise WorkloadValidationError(
                    f"Processo no índice {proc_idx} deve ser um objeto JSON."
                )

            # Validação do PID
            if "pid" not in proc_entry:
                raise WorkloadValidationError(
                    f"Processo no índice {proc_idx} não informa o campo obrigatório 'pid'."
                )
            pid = proc_entry["pid"]
            if not isinstance(pid, int) or pid < 0:
                raise WorkloadValidationError(
                    f"PID do processo deve ser um inteiro não negativo (obtido: {pid})."
                )
            if pid in seen_pids:
                raise WorkloadValidationError(f"PID duplicado detectado: PID {pid} já existe.")
            seen_pids.add(pid)

            # Validação do instante de chegada
            if "arrival_time" not in proc_entry:
                raise WorkloadValidationError(
                    f"Processo PID {pid} não informa o campo obrigatório 'arrival_time'."
                )
            arrival_time = proc_entry["arrival_time"]
            if not isinstance(arrival_time, int) or arrival_time < 0:
                raise WorkloadValidationError(
                    f"arrival_time do processo PID {pid} deve ser um inteiro >= 0 (obtido: {arrival_time})."
                )

            # Prioridade
            priority = proc_entry.get("priority", 1)
            if not isinstance(priority, int):
                raise WorkloadValidationError(
                    f"priority do processo PID {pid} deve ser um inteiro (obtido: {priority})."
                )

            # Validação de threads
            if "threads" not in proc_entry:
                raise WorkloadValidationError(
                    f"Processo PID {pid} não informa o campo obrigatório 'threads'."
                )
            threads_data = proc_entry["threads"]
            if not isinstance(threads_data, list) or len(threads_data) == 0:
                raise WorkloadValidationError(
                    f"Processo PID {pid} deve possuir uma lista não vazia de threads."
                )

            process = Process(pid=pid, priority=priority, arrival_time=arrival_time)
            seen_tids: set[int] = set()

            for t_idx, thread_entry in enumerate(threads_data):
                if not isinstance(thread_entry, dict):
                    raise WorkloadValidationError(
                        f"Thread no índice {t_idx} do processo PID {pid} deve ser um objeto JSON."
                    )

                if "tid" not in thread_entry:
                    raise WorkloadValidationError(
                        f"Thread no índice {t_idx} do processo PID {pid} não informa o 'tid'."
                    )
                tid = thread_entry["tid"]
                if not isinstance(tid, int) or tid < 0:
                    raise WorkloadValidationError(
                        f"TID da thread no processo PID {pid} deve ser inteiro >= 0 (obtido: {tid})."
                    )
                if tid in seen_tids:
                    raise WorkloadValidationError(
                        f"TID duplicado no processo PID {pid}: TID {tid} já existe."
                    )
                seen_tids.add(tid)

                # Prioridade da thread (herda do processo se não fornecida)
                t_priority = thread_entry.get("priority", priority)
                if not isinstance(t_priority, int):
                    raise WorkloadValidationError(
                        f"priority da thread P{pid}-T{tid} deve ser um inteiro (obtido: {t_priority})."
                    )

                # Operações
                if "operations" not in thread_entry:
                    raise WorkloadValidationError(
                        f"Thread P{pid}-T{tid} não informa o campo 'operations'."
                    )
                ops_data = thread_entry["operations"]
                if not isinstance(ops_data, list) or len(ops_data) == 0:
                    raise WorkloadValidationError(
                        f"Thread P{pid}-T{tid} deve possuir uma lista não vazia de operações."
                    )

                operations: list[Operation] = []
                for op_idx, op_entry in enumerate(ops_data):
                    if not isinstance(op_entry, dict):
                        raise WorkloadValidationError(
                            f"Operação {op_idx} da thread P{pid}-T{tid} deve ser um objeto JSON."
                        )
                    if "type" not in op_entry or "duration" not in op_entry:
                        raise WorkloadValidationError(
                            f"Operação {op_idx} da thread P{pid}-T{tid} requer campos 'type' e 'duration'."
                        )
                    op_type_raw = str(op_entry["type"]).strip().upper()
                    if op_type_raw not in ("CPU", "IO"):
                        raise WorkloadValidationError(
                            f"Tipo de operação inválido em P{pid}-T{tid} op {op_idx}: '{op_entry['type']}'. "
                            "Deve ser 'CPU' ou 'IO'."
                        )
                    duration = op_entry["duration"]
                    if not isinstance(duration, int) or duration <= 0:
                        raise WorkloadValidationError(
                            f"Duração da operação em P{pid}-T{tid} op {op_idx} deve ser inteiro > 0 (obtido: {duration})."
                        )

                    op_type = OperationType.CPU if op_type_raw == "CPU" else OperationType.IO
                    operations.append(Operation(op_type=op_type, duration=duration))

                # Valida alternância: deve iniciar com CPU, terminar com CPU e alternar
                if operations[0].op_type != OperationType.CPU:
                    raise WorkloadValidationError(
                        f"Thread P{pid}-T{tid} deve iniciar com surto de CPU (obtido: {operations[0].op_type.value})."
                    )
                if operations[-1].op_type != OperationType.CPU:
                    raise WorkloadValidationError(
                        f"Thread P{pid}-T{tid} deve terminar com surto de CPU (obtido: {operations[-1].op_type.value})."
                    )
                for i in range(len(operations) - 1):
                    if operations[i].op_type == operations[i + 1].op_type:
                        raise WorkloadValidationError(
                            f"Thread P{pid}-T{tid} possui operações consecutivas do mesmo tipo ({operations[i].op_type.value}) "
                            f"nos índices {i} e {i+1}. A sequência deve alternar entre CPU e IO."
                        )

                thread = SimulatedThread(
                    tid=tid,
                    process_id=pid,
                    priority=t_priority,
                    arrival_time=arrival_time,
                    operations=operations,
                )
                process.add_thread(thread)

            loaded_processes.append(process)

        # Ordena processos por tempo de chegada e PID
        loaded_processes.sort(key=lambda p: (p.creation_time, p.pid))
        return loaded_processes
