# Relatório de Progresso - Primeira Entrega (Intermediária)

**Disciplina de Sistemas Operacionais**  
**Prof. Maurício Acconcia Dias**

---

## 1. Identificação do Projeto e Equipe

* **Projeto:** Simulador Didático de Sistemas Operacionais Orientado a Objetos e a Eventos Discretos
* **Etapa:** Primeira Entrega (Entrega Intermediária)
* **Integrantes:**
  * **Miguel Pereira Gonçalves** — RA: 115333
  * **Rafael Silva Cruz** — RA: 114833
  * **Renato Martins** — RA: 115944

---

## 2. Objetivo e Escopo Desta Etapa

O objetivo desta primeira entrega é estabelecer a espinha dorsal computacional do simulador, implementando:
1. O núcleo da simulação a eventos discretos (relógio lógico e fila de prioridade determinística).
2. O ciclo de vida e estruturas de dados de processos e threads (`Process`, `PCB`, `SimulatedThread`, `TCB`), com validação formal de estados.
3. O mecanismo de escalonamento com suporte à política **FCFS (First-Come, First-Served)** não preemptiva e contabilização de sobrecarga de troca de contexto.
4. O modelo simplificado de operações de E/S bloqueante por evento com liberação de CPU e interrupções simuladas.
5. A leitura e validação semântica de cargas de trabalho externas em JSON.
6. A coleta e apresentação de métricas completas de tempo (retorno, espera, resposta), utilização de recursos e throughput.
7. A validação empírica através de suíte de testes automatizados com `pytest` e casos verificáveis analiticamente.

---

## 3. Funcionalidades Concluídas e Evidências

Todas as funcionalidades obrigatórias desta entrega foram implementadas e verificadas. A tabela abaixo sintetiza as evidências concretas:

| Funcionalidade | Descrição Técnica | Evidência em Código / Teste |
| :--- | :--- | :--- |
| **Relógio Lógico Monotônico** | Avança estritamente no tempo; impede retrocessos; opera em ticks inteiros abstratos. | `src/simulator/core/clock.py`<br>`tests/test_clock_and_events.py::test_clock_monotonicity` |
| **Fila de Eventos Determinística** | Baseada em min-heap (`heapq`), com ordenação por `(tempo, prioridade_tipo, seq)`. | `src/simulator/core/event_queue.py`<br>`tests/test_clock_and_events.py::test_event_queue_deterministic_tie_breaking` |
| **Abstração Processo e PCB** | Encapsula PID, prioridade, tempo de criação, registradores simulados, referências futuras para memória e arquivos. | `src/simulator/entities/process.py`<br>`src/simulator/entities/pcb.py` |
| **Abstração Thread e TCB** | Unidade escalonável; mantém TID, registradores lógicos (`PC`, `R0`, `R1`, `SP`), pilha lógica (`stack`) e métricas. | `src/simulator/entities/thread.py`<br>`src/simulator/entities/tcb.py` |
| **Ciclo de Vida e Transições** | Estados `NOVO`, `PRONTO`, `EXECUTANDO`, `BLOQUEADO`, `FINALIZADO`. Rejeição com erro explicativo de transições ilegais. | `src/simulator/entities/states.py`<br>`tests/test_states_and_transitions.py` |
| **Estado Derivado do Processo** | Processo só finaliza quando todas as threads terminam; reflete execução/bloqueio das threads. | `src/simulator/entities/process.py`<br>`tests/test_states_and_transitions.py::test_process_derived_state_and_multi_thread_completion` |
| **Escalonamento FCFS** | Política não preemptiva; seleção estritamente FIFO; thread retornando de E/S vai para o fim da fila. | `src/simulator/scheduler/fcfs.py`<br>`tests/test_fcfs_scheduler.py` |
| **Mecanismo de Despacho & Contexto** | Separação entre mecanismo (`Scheduler`) e política (`SchedulingPolicy`); custo configurável de troca de contexto. | `src/simulator/scheduler/scheduler.py`<br>`tests/test_context_switch.py` |
| **E/S Bloqueante Simplificada** | Libera CPU imediatamente; agenda término em $T + \text{duração}$; interrupção simulada devolve thread a `PRONTO`. | `src/simulator/io/io_manager.py`<br>`tests/test_io_blocking.py` |
| **Concorrência entre Threads** | Execução de outra thread enquanto uma está bloqueada em E/S (mesmo processo e processos distintos). | `tests/test_io_blocking.py::test_concurrent_execution_while_one_thread_is_blocked`<br>`tests/test_io_blocking.py::test_multithread_same_process_interleaving` |
| **Carregador de Cargas (JSON)** | Validação rigorosa: rejeição de PIDs duplicados, durações $\le 0$, chegadas negativas, alternância incorreta CPU/IO. | `src/simulator/loader/workload_loader.py`<br>`tests/test_workload_loader.py` |
| **Métricas e Logs** | Cálculo de retorno, espera, resposta, utilização útil da CPU, sobrecarga, throughput e formatação tabular. | `src/simulator/metrics/collector.py`<br>`src/simulator/metrics/logger.py` |
| **Caso Verificável Obrigatório** | Execução e conferência exata do caso do enunciado (P1: 0..3, P2: 3..5, P3: 5..6, throughput 0.5). | `workloads/verificacao_fcfs.json`<br>`tests/test_metrics_and_verifiable_cases.py::test_verifiable_fcfs_case_from_prompt` |

---

## 4. Limitações Conhecidas Desta Etapa

1. **Escalonamento Monopolítico:** Apenas a política FCFS está implementada e disponível para execução nesta entrega. Políticas Round Robin e Prioridades estão estruturadas na interface `SchedulingPolicy`, mas ainda não possuem classes concretas.
2. **Modelo de E/S Simplificado:** A E/S atual é modelada como um evento abstrato com duração fixa definida na carga. Não há ainda controladores de dispositivo de bloco (disco) ou caractere (teclado), filas de requisições por dispositivo nem operações assíncronas (não bloqueantes).
3. **Memória Abstrata:** O modelo atual assume que todos os processos e threads residem inteiramente na memória. As estruturas `address_space` no `PCB` existem apenas como pontos de extensão para a Entrega Final (onde serão introduzidas tabelas de páginas, molduras reais e algoritmo FIFO de substituição).
4. **Sistema de Arquivos Inativo:** A tabela de arquivos abertos (`open_files_table`) no `PCB` é uma estrutura mínima reservada; não há persistência ou descritores funcionais ativos nesta entrega.

---

## 5. Estimativa de Progresso e Critérios Transparentes

Para garantir rigor acadêmico, o progresso do projeto é mensurado com base em uma matriz de pesos ponderados, dividida entre os requisitos da **Entrega Intermediária** e o escopo total da **Entrega Final**.

> [!NOTE]
> Os percentuais apresentados refletem estimativas de cumprimento dos requisitos técnicos de engenharia de software da especificação, não constituindo previsão direta de nota.

### 5.1 Atendimento da Primeira Entrega (Entrega Intermediária)

| Requisito da Primeira Entrega | Peso | Concluído | Ponderado |
| :--- | :---: | :---: | :---: |
| Repositório estruturado, `pyproject.toml`, `.gitignore` e CLI | 10% | 100% | 10.0% |
| Descrição da arquitetura (`docs/arquitetura.md`) | 10% | 100% | 10.0% |
| Diagrama de classes Mermaid preliminar (`docs/diagrama_classes.md`) | 10% | 100% | 10.0% |
| Núcleo do clock lógico monotônico e fila de eventos prioritária | 15% | 100% | 15.0% |
| Processos, threads, PCB, TCB e máquina de estados com transições | 20% | 100% | 20.0% |
| Mecanismo de escalonamento, política FCFS e sobrecarga de contexto | 15% | 100% | 15.0% |
| E/S simplificada por evento com bloqueio e interrupção | 10% | 100% | 10.0% |
| Testes automatizados com `pytest` cobrindo cenários do enunciado | 10% | 100% | 10.0% |
| **Total da Primeira Entrega** | **100%** | — | **100.0%** |

**Percentual de atendimento da Entrega Intermediária:** **100%**

---

### 5.2 Progresso em Relação ao Projeto Completo (Semestre)

| Componente Global do Projeto Completo | Peso no Projeto Total | Conclusão Atual | Contribuição Atual |
| :--- | :---: | :---: | :---: |
| **Núcleo de Simulação e Eventos Discretos** (Clock, EventQueue, Engine) | 15% | 100% | 15.0% |
| **Modelo de Processos e Threads** (PCB, TCB, Ciclo de Vida, Validações) | 15% | 100% | 15.0% |
| **Escalonamento de CPU** (FCFS pronto; faltam Round Robin e Prioridades) | 20% | 40% | 8.0% |
| **Gerenciamento de Memória Paginada** (Tabela de páginas, faltas, FIFO) | 20% | 0% | 0.0% |
| **Subsistema de Entrada e Saída** (Dispositivos bloco/caractere, filas) | 15% | 25% | 3.75% |
| **Sistema de Arquivos Hierárquico** (Diretórios, nós-i/FCB, descritores) | 10% | 0% | 0.0% |
| **Experimentos, Análise Comparativa e Relatório Final em PDF** | 5% | 0% | 0.0% |
| **Total Global do Projeto Completo** | **100%** | — | **41.75%** |

**Percentual estimado do projeto completo:** **41.75%**

---

## 6. Plano Ordenado para a Etapa Final

A execução das pendências da Entrega Final seguirá o seguinte cronograma ordenado de desenvolvimento:

1. **Sprint 1 — Políticas de Escalonamento Adicionais:**
   - Implementação de `RoundRobinPolicy` com quantum configurável via CLI (`-q / --quantum`).
   - Implementação do evento `QUANTUM_EXPIRED` e preempção (`EXECUTANDO -> PRONTO`).
   - Implementação de `PriorityPolicy` (declaração de preemptiva vs. não preemptiva e política de desempate).
   - Testes comparativos entre FCFS, RR e Prioridades sob a mesma carga.

2. **Sprint 2 — Gerência de Memória Paginada:**
   - Criação da classe `MemoryManager`, tabela de molduras físicas e tabelas de páginas por processo (`PageTable`).
   - Suporte à tradução de endereços virtuais em endereços físicos na carga.
   - Implementação de faltas de página (*page faults*), com bloqueio da thread solicitante e carregamento simulado.
   - Algoritmo de substituição de páginas por **FIFO** (e extensão opcional LRU/Clock).

3. **Sprint 3 — Subsistema Completo de Entrada e Saída:**
   - Criação dos tipos `BlockDevice` (disco) e `CharacterDevice` (terminal/serial) com tempos de serviço próprios.
   - Fila de requisições por dispositivo e política de atendimento FCFS (com extensão opcional SSTF/SCAN).
   - Operações não bloqueantes com registro de conclusão assíncrona.

4. **Sprint 4 — Sistema de Arquivos Hierárquico:**
   - Estrutura de diretórios a partir de `/` (raiz).
   - Implementação de FCB / nós-i com metadados, permissões e blocos alocados (alocação contígua ou encadeada).
   - Tabela global de arquivos abertos e tabela de descritores por processo.
   - Operações `create`, `open`, `read`, `write`, `close`, `delete` e `list`.

5. **Sprint 5 — Experimentos Finais, Consolidação e Relatório Técnico:**
   - Elaboração dos 3 experimentos comparativos obrigatórios do relatório final:
     1. Comparação entre FCFS, Round Robin e Prioridades na mesma carga.
     2. Análise do efeito de dois ou mais valores de quantum no Round Robin.
     3. Análise do comportamento de memória (faltas de página) ou E/S.
   - Confecção do **Relatório Técnico Final em PDF**, conforme exigido pelo regulamento da disciplina.

---

## 7. Registro de Ferramentas de Apoio e Integridade Acadêmica

Em conformidade estrita com o Artigo 15 da especificação da disciplina, registram-se as ferramentas e materiais externos utilizados:

- **Linguagem e Ambiente:** Python 3.13.7 no sistema operacional Microsoft Windows.
- **Bibliotecas Externas:** Apenas a ferramenta de testes `pytest` (versão 9.1.1) foi utilizada como dependência de desenvolvimento. Nenhuma biblioteca externa para simulação, escalonamento ou estruturas de SO foi empregada.
- **Ferramentas de Apoio à Codificação:** Antigravity AI Assistant (Google DeepMind) para pair-programming, geração de código orientado a objetos, elaboração de testes automatizados e formatação de documentação Markdown.
- **Material Bibliográfico e Teórico de Referência:**
  - DIAS, Maurício Acconcia. *Especificação do Trabalho Prático: Simulador didático de sistemas operacionais*. Disciplina de Sistemas Operacionais, 2026.
  - SILBERSCHATZ, Abraham; GALVIN, Peter B.; GAGNE, Greg. *Operating System Concepts*. 10th ed., Wiley, 2018.
  - TANENBAUM, Andrew S.; BOS, Herbert. *Modern Operating Systems*. 4th ed., Pearson, 2014.
