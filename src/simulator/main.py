"""Interface de Linha de Comando (CLI) para o Simulador de SO."""

import argparse
import sys
from pathlib import Path
from typing import NoReturn

from simulator.core.engine import SimulationEngine
from simulator.io.io_manager import SimplifiedIOManager
from simulator.loader.workload_loader import (
    WorkloadLoader,
    WorkloadValidationError,
)
from simulator.metrics.logger import EventLogger
from simulator.scheduler.fcfs import FCFSPolicy
from simulator.scheduler.scheduler import Scheduler


def parse_arguments(args: list[str]) -> argparse.Namespace:
    """Configura e processa os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        prog="simulador-so",
        description="Simulador Didático de Sistemas Operacionais (Entrega 1 - FCFS)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "-w", "--workload",
        required=True,
        help="Caminho do arquivo JSON contendo a carga de trabalho.",
    )
    parser.add_argument(
        "-p", "--policy",
        default="FCFS",
        help="Política de escalonamento. Nesta versão, apenas 'FCFS' é suportada.",
    )
    parser.add_argument(
        "-c", "--context-switch",
        type=int,
        default=0,
        help="Custo em unidades de tempo da troca de contexto (inteiro >= 0).",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Caminho opcional do arquivo para salvar os logs e relatório de métricas.",
    )
    parser.add_argument(
        "-q", "--quantum",
        type=int,
        default=None,
        help="Tamanho do quantum de tempo (reservado para Round Robin na entrega final).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suprime a impressão do histórico detalhado de eventos no terminal.",
    )

    return parser.parse_args(args)


def validate_cli_options(args: argparse.Namespace) -> None:
    """Valida argumentos fornecidos pelo usuário, rejeitando parâmetros não suportados."""
    # Validação de quantum não suportado na entrega 1
    if args.quantum is not None:
        sys.stderr.write(
            "Erro: O parâmetro '--quantum' é exclusivo da política Round Robin, "
            "que será implementada na etapa final do projeto.\n"
        )
        sys.exit(2)

    # Validação da política
    policy_upper = args.policy.strip().upper()
    if policy_upper != "FCFS":
        supported = ["FCFS"]
        planned = ["RR", "ROUND_ROBIN", "PRIORITY", "PRIORIDADES"]
        if policy_upper in planned:
            sys.stderr.write(
                f"Erro: A política '{args.policy}' está planejada para a etapa final do projeto. "
                f"Nesta primeira entrega, apenas 'FCFS' está funcional e homologada.\n"
            )
        else:
            sys.stderr.write(
                f"Erro: Política '{args.policy}' desconhecida. "
                f"Políticas válidas nesta versão: {supported}.\n"
            )
        sys.exit(2)

    # Validação do custo de troca de contexto
    if args.context_switch < 0:
        sys.stderr.write(
            f"Erro: O custo de troca de contexto deve ser um inteiro não negativo (>= 0). "
            f"Valor informado: {args.context_switch}\n"
        )
        sys.exit(2)


def main(argv: list[str] | None = None) -> int:
    """Ponto de entrada principal da aplicação."""
    args = parse_arguments(argv if argv is not None else sys.argv[1:])
    validate_cli_options(args)

    workload_path = Path(args.workload)

    # 1. Carregamento da carga de trabalho
    try:
        processes = WorkloadLoader.load_from_file(workload_path)
    except WorkloadValidationError as e:
        sys.stderr.write(f"Erro de validação na carga de trabalho: {e}\n")
        return 1
    except Exception as e:
        sys.stderr.write(f"Erro inesperado ao processar carga: {e}\n")
        return 1

    # 2. Configuração do escalonador e motor
    policy = FCFSPolicy()
    scheduler = Scheduler(policy=policy, context_switch_cost=args.context_switch)
    io_manager = SimplifiedIOManager()
    logger = EventLogger()

    engine = SimulationEngine(
        scheduler=scheduler,
        io_manager=io_manager,
        logger=logger,
    )
    engine.load_workload(processes)

    # 3. Execução da simulação
    system_metrics, process_metrics = engine.run()

    # 4. Geração do relatório
    metrics_report = engine.metrics_collector.format_report(system_metrics, process_metrics)
    full_log_text = logger.get_text()

    if not args.quiet:
        print(full_log_text)
        print()

    print(metrics_report)

    # 5. Gravação em arquivo se solicitado
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        content_to_save = f"{full_log_text}\n\n{metrics_report}\n"
        out_path.write_text(content_to_save, encoding="utf-8")
        print(f"\n[Info] Resultados salvos com sucesso em: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
