#!/usr/bin/env python3
"""Ponto de entrada raiz para execução do simulador."""

import sys
from pathlib import Path

# Adiciona o diretório 'src' ao sys.path para importação do pacote simulator
SRC_DIR = Path(__file__).resolve().parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from simulator.main import main

if __name__ == "__main__":
    sys.exit(main())
