# Simulador Didático de Sistemas Operacionais

**Disciplina de Sistemas Operacionais**  
**Prof. Maurício Acconcia Dias**

---

## Integrantes do Projeto

* **Miguel Pereira Gonçalves** — RA: 115333
* **Rafael Silva Cruz** — RA: 114833
* **Renato Martins** — RA: 115944

---

## 1. Visão Geral e Escopo da Primeira Entrega

Este projeto consiste em um **simulador didático de sistemas operacionais** orientado a objetos e controlado por **eventos discretos** no tempo lógico. O software reproduz em ambiente controlado a dinâmica de ciclo de vida de processos e threads, políticas de escalonamento da CPU, custos de troca de contexto e operações básicas de entrada e saída bloqueante.

### Escopo Entregue na Etapa Intermediária:
- **Núcleo de Eventos Discretos:** Relógio lógico inteiro estritamente monotônico e fila de prioridades (`EventQueue` com `heapq`).
- **Abstração de Processos e Threads:** Modelagem formal de `Process`, `PCB`, `SimulatedThread` e `TCB`, com registradores simulados, pilha lógica e espaço reservado para descritores futuros.
- **Ciclo de Vida e Estados:** Transições formais e validadas entre `NOVO`, `PRONTO`, `EXECUTANDO`, `BLOQUEADO` e `FINALIZADO`, com derivação determinística do estado do processo a partir de suas threads.
- **Escalonamento da CPU:** Separação estrita entre mecanismo (`Scheduler`) e política (`SchedulingPolicy`), com a política **FCFS (First-Come, First-Served)** totalmente funcional e não preemptiva.
- **Sobrecarga de Troca de Contexto:** Custo configurável em unidades inteiras de tempo, cobrado a cada despacho para a CPU, com distinção clara entre tempo útil, tempo ocioso e sobrecarga.
- **Modelo de E/S Simplificado:** Operações de E/S bloqueantes por evento com duração definida, liberando a CPU para outras threads (inclusive do mesmo processo) e gerando interrupção simulada ao concluir.
- **Cargas de Trabalho Externas:** Carga em formato JSON com validação semântica rigorosa (rejeição de IDs duplicados, durações inválidas ou sequências incorretas).
- **Métricas e Logs Determinísticos:** Registro detalhado de eventos e relatório completo de tempos de retorno, espera, resposta, utilização da CPU, throughput e sobrecargas.
- **Testes Automatizados:** Bateria de testes unitários e de integração com `pytest` (100% de aprovação).


## 2. Requisitos de Ambiente

- **Python:** Versão 3.11 ou superior (desenvolvido e homologado em Python 3.13).
- **Dependências de Execução:** Apenas a biblioteca padrão do Python (`json`, `heapq`, `dataclasses`, `enum`, `pathlib`, `argparse`, `typing`).
- **Dependências de Teste:** `pytest>=8.0.0` para execução da suíte de testes automatizados.

---

## 3. Instalação e Preparação

Clone ou descompacte o repositório no seu ambiente de preferência:

```powershell
# A partir da raiz do repositório
python -m pip install -r requirements.txt
```

---

## 4. Como Executar o Simulador

O simulador é executado via linha de comando através do script principal `simulador.py` na raiz do projeto:

```powershell
python simulador.py --workload <caminho_do_arquivo.json> [opcoes]
```

### Parâmetros da CLI:

| Parâmetro | Nome Longo | Padrão | Descrição |
| :--- | :--- | :---: | :--- |
| `-w` | `--workload` | *Obrigatório* | Caminho do arquivo JSON contendo a carga de trabalho. |
| `-p` | `--policy` | `FCFS` | Política de escalonamento. Nesta versão, apenas `FCFS` é aceita. |
| `-c` | `--context-switch` | `0` | Custo em ticks da troca de contexto (inteiro $\ge 0$). |
| `-o` | `--output` | `None` | Caminho de arquivo opcional para salvar o log de eventos e métricas. |
| `-q` | `--quantum` | `None` | Tamanho do quantum (rejeitado nesta etapa; reservado para Round Robin). |
| `--quiet` | `--quiet` | `False` | Suprime a exibição do histórico de eventos, imprimindo só as métricas. |
---

## 5. Formato das Cargas de Trabalho (JSON)

As tarefas simuladas são descritas em arquivos JSON textuais e externos ao código-fonte.

### Esquema:
- `processes`: Lista não vazia de processos.
  - `pid`: Identificador único do processo (inteiro $\ge 0$).
  - `arrival_time`: Instante de criação/chegada no relógio lógico (inteiro $\ge 0$).
  - `priority`: Nível de prioridade lógica do processo (inteiro).
  - `threads`: Lista não vazia de threads pertencentes ao processo.
    - `tid`: Identificador da thread (inteiro $\ge 0$, único dentro do processo).
    - `operations`: Sequência alternada de surtos de CPU e E/S.
      - Deve **obrigatoriamente iniciar com CPU** e **terminar com CPU**.
      - Deve alternar estritamente entre `CPU` e `IO` (ex: `CPU -> IO -> CPU`).
      - Toda duração deve ser um inteiro estritamente positivo ($> 0$).

### Exemplo Completo:

```json
{
  "processes": [
    {
      "pid": 1,
      "arrival_time": 0,
      "priority": 1,
      "threads": [
        {
          "tid": 1,
          "operations": [
            { "type": "CPU", "duration": 3 },
            { "type": "IO", "duration": 2 },
            { "type": "CPU", "duration": 2 }
          ]
        }
      ]
    },
    {
      "pid": 2,
      "arrival_time": 2,
      "priority": 1,
      "threads": [
        {
          "tid": 1,
          "operations": [
            { "type": "CPU", "duration": 4 }
          ]
        }
      ]
    }
  ]
}
```

---

## 6. Cargas de Exemplo Fornecidas

O repositório disponibiliza cargas pré-configuradas no diretório `workloads/`:

1. **`workloads/verificacao_fcfs.json`**: Cenário de verificação analítica do enunciado da disciplina (3 processos de surto único, custo de troca 0).
2. **`workloads/verificacao_io.json`**: Cenário de verificação com sobreposição de E/S e CPU entre 2 processos.
3. **`workloads/cpu_bound.json`**: Carga com surtos longos de CPU e sem solicitações de E/S.
4. **`workloads/io_bound.json`**: Carga com surtos curtos de CPU e operações longas de E/S.
5. **`workloads/mixed.json`**: Carga com processos mono-thread e processo **multi-thread** (Processo 1 com 2 threads concorrentes), combinando CPU e E/S.

### Comandos de Demonstração:

```powershell
# 1. Caso verificável FCFS básico
python simulador.py -w workloads/verificacao_fcfs.json

# 2. Caso verificável com custo de troca de contexto = 1
python simulador.py -w workloads/verificacao_fcfs.json -c 1

# 3. Caso verificável com operações de E/S
python simulador.py -w workloads/verificacao_io.json

# 4. Carga mista com processo multi-thread e gravação em arquivo
python simulador.py -w workloads/mixed.json -c 2 -o outputs/resultado_misto.txt
```

---

## 7. Resultados do Caso de Verificação Obrigatório

O enunciado especifica o seguinte caso com custo zero de troca de contexto:
- **P1:** chegada 0, CPU 3.
- **P2:** chegada 1, CPU 2.
- **P3:** chegada 2, CPU 1.

### Execução no Simulador:

```powershell
python simulador.py -w workloads/verificacao_fcfs.json
```

### Tabela de Comparação de Resultados:

| Métrica / Entidade | Esperado pelo Enunciado | Obtido pelo Simulador | Status |
| :--- | :---: | :---: | :---: |
| Execução de P1 | Ticks $0 \rightarrow 3$ | Ticks $0 \rightarrow 3$ | **Exato** |
| Execução de P2 | Ticks $3 \rightarrow 5$ | Ticks $3 \rightarrow 5$ | **Exato** |
| Execução de P3 | Ticks $5 \rightarrow 6$ | Ticks $5 \rightarrow 6$ | **Exato** |
| Tempo de Espera (P1, P2, P3) | 0, 2, 3 | 0, 2, 3 | **Exato** |
| Tempo de Resposta (P1, P2, P3) | 0, 2, 3 | 0, 2, 3 | **Exato** |
| Tempo de Retorno (P1, P2, P3) | 3, 4, 4 | 3, 4, 4 | **Exato** |
| Utilização Útil da CPU | 100.0% | 100.0% | **Exato** |
| Throughput do Sistema | 0.5 proc/tick ($3/6$) | 0.5000 proc/tick | **Exato** |

---

## 8. Execução dos Testes Automatizados

A suíte de testes automatizados cobre todas as regras centrais do modelo:

```powershell
python -m pytest
```

### Resumo dos Módulos de Teste:

- `test_clock_and_events.py`: Monotonicidade do clock, ordenação da `EventQueue` e desempates determinísticos de eventos simultâneos.
- `test_states_and_transitions.py`: Transições válidas de threads, rejeição de transições ilegais (`InvalidStateTransitionError`) e derivação do estado do processo a partir de suas threads.
- `test_fcfs_scheduler.py`: Garantia da ordem FIFO no FCFS, inserção de threads que retornam de E/S no final da fila de prontos.
- `test_context_switch.py`: Contabilização de sobrecarga temporal, impacto no tempo de resposta e despacho com custo zero e positivo.
- `test_io_blocking.py`: Bloqueio imediato da CPU em operações de E/S, interrupção simulada no tempo exato, execução de outra thread enquanto uma está bloqueada (mesmo processo e processos distintos).
- `test_metrics_and_verifiable_cases.py`: Conferência analítica dos cenários do enunciado e tratamento de divisão por zero.
- `test_workload_loader.py`: Validação de arquivos JSON inválidos (PIDs duplicados, durações $\le 0$, erros estruturais).
- `test_determinism.py`: Reprodutibilidade idêntica entre múltiplas execuções e validações da interface de linha de comando.

---

## 9. Estrutura do Repositório

```
Simulacao/
├── .gitignore                    # Regras de exclusão do Git
├── pyproject.toml                # Metadados e configuração do pytest
├── requirements.txt              # Dependências do projeto
├── README.md                     # Documentação principal e instruções de execução
├── simulador.py                  # Ponto de entrada executável na raiz
├── docs/
│   ├── arquitetura.md            # Descrição arquitetural, estados e decisões
│   ├── diagrama_classes.md       # Diagrama de classes Mermaid (implementado e futuro)
│   └── relatorio_progresso.md    # Relatório de progresso e plano para etapa final
├── workloads/
│   ├── cpu_bound.json            # Carga limitada por CPU
│   ├── io_bound.json             # Carga limitada por E/S
│   ├── mixed.json                # Carga mista com processo multi-thread
│   ├── verificacao_fcfs.json     # Caso de teste obrigatório do enunciado
│   └── verificacao_io.json       # Cenário analítico de E/S concorrente
├── src/
│   └── simulator/
│       ├── __init__.py
│       ├── main.py               # Interface CLI e parsing de argumentos
│       ├── core/
│       │   ├── clock.py          # Relógio lógico monotônico
│       │   ├── event.py          # Estrutura e tipos de eventos discretos
│       │   ├── event_queue.py    # Min-heap de eventos determinístico
│       │   └── engine.py         # Motor de simulação central (SimulationEngine)
│       ├── entities/
│       │   ├── operation.py      # Operações de CPU e E/S
│       │   ├── states.py         # Estados e validação de transições
│       │   ├── tcb.py            # Bloco de Controle de Thread
│       │   ├── thread.py         # Thread simulada (unidade escalonável)
│       │   ├── pcb.py            # Bloco de Controle de Processo
│       │   └── process.py        # Processo simulado
│       ├── scheduler/
│       │   ├── cpu.py            # CPU simulada uniprocessadora
│       │   ├── policy.py         # Interface abstrata SchedulingPolicy
│       │   ├── fcfs.py           # Política First-Come, First-Served
│       │   └── scheduler.py      # Mecanismo de escalonamento e contexto
│       ├── io/
│       │   └── io_manager.py     # Gerenciamento de E/S bloqueante simplificada
│       ├── loader/
│       │   └── workload_loader.py# Leitura e validação rigorosa de cargas JSON
│       └── metrics/
│           ├── logger.py         # Logger determinístico de eventos
│           └── collector.py      # Cálculo e formatação de métricas
└── tests/                        # 31 testes unitários e de integração
    ├── test_clock_and_events.py
    ├── test_context_switch.py
    ├── test_determinism.py
    ├── test_fcfs_scheduler.py
    ├── test_io_blocking.py
    ├── test_metrics_and_verifiable_cases.py
    ├── test_states_and_transitions.py
    └── test_workload_loader.py
```
