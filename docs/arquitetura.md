# Documento de Arquitetura do Simulador de SO

**Disciplina de Sistemas Operacionais**  
**Etapa: Primeira Entrega (Entrega Intermediária)**

---

## 1. Visão Geral e Princípios de Projeto

O simulador foi concebido como um ambiente puramente educacional para demonstrar os mecanismos centrais de um Sistema Operacional multiprogramado. Ele adota o paradigma da **Simulação Orientada a Eventos Discretos (Discrete-Event Simulation - DES)**, garantindo:

1. **Independência de Hardware:** O tempo decorrido não se baseia no relógio de parede (*wall-clock*) nem em chamadas de atraso real (`time.sleep`). O tempo avança por saltos discretos correspondentes aos instantes em que eventos de interesse ocorrem.
2. **Determinismo Absoluto:** Dadas a mesma carga de entrada e a mesma configuração de parâmetros, a simulação produz exatamente a mesma sequência de eventos e as mesmas métricas.
3. **Separação entre Mecanismo e Política:** Os componentes responsáveis por gerenciar recursos (despacho, trocas de contexto, controle de interrupções) são independentes dos algoritmos de decisão (regras de seleção da fila de prontos).
4. **Alta Coesão e Baixo Acoplamento:** As entidades do modelo (`Process`, `SimulatedThread`, `PCB`, `TCB`, `Scheduler`, `Clock`, `EventQueue`, `IOManager`) possuem responsabilidades estritas e bem delimitadas.

---

## 2. Núcleo da Simulação (Core)

```
+-------------------------------------------------------------------+
|                        SimulationEngine                           |
+---------------------------------+---------------------------------+
                                  |
            +---------------------+---------------------+
            |                     |                     |
     +------v------+       +------v------+       +------v------+
     |    Clock    |       | EventQueue  |       |  Scheduler  |
     +-------------+       +-------------+       +-------------+
```

### 2.1 Relógio Lógico (`Clock`)
- Mantém o tempo lógico da simulação em unidades inteiras abstratas (*ticks*).
- Garante **monotonicidade estrita**: uma tentativa de avançar para um instante anterior ao tempo atual gera uma exceção `ValueError`.
- O relógio avança apenas quando o próximo evento é retirado da fila (`EventQueue.pop_next()`), avançando o tempo mesmo quando a CPU está ociosa (saltando diretamente para a próxima chegada ou término de E/S).

### 2.2 Fila de Eventos (`EventQueue`) e Ordem de Desempate
A fila de eventos é implementada como uma fila de prioridade (*min-heap*) utilizando a biblioteca padrão `heapq`.

Cada evento na fila é ordenado pela tupla de três chaves:
$$\text{Ordem} = (\text{instante\_do\_evento}, \text{prioridade\_intrínseca}, \text{número\_sequencial})$$

#### Hierarquia de Prioridades Intrínsecas para Eventos Simultâneos:
Quando dois ou mais eventos ocorrem no mesmo instante de tempo $T$, a ordem de processamento deve respeitar a causalidade física do sistema uniprocessador, sem que duas tarefas ocupem a CPU simultaneamente:

1. **`IO_COMPLETION` (Prioridade 1):** Uma operação de E/S é concluída por interrupção simulada de hardware. A thread correspondente deve ser desbloqueada e devolvida à fila de prontos *antes* que novas decisões de escalonamento sejam avaliadas em $T$.
2. **`PROCESS_ARRIVAL` (Prioridade 2):** Novo processo e suas threads chegam ao sistema. São admitidos e posicionados na fila de prontos antes do despacho da CPU em $T$.
3. **`CONTEXT_SWITCH_END` (Prioridade 3):** A sobrecarga de troca de contexto termina. A thread selecionada transiciona para `EXECUTANDO` e inicia seu surto de CPU.
4. **`CPU_BURST_END` (Prioridade 4):** A thread que estava na CPU conclui seu surto. Ela libera a CPU (indo para E/S ou terminando), permitindo que o escalonador seja acionado.
5. **`SCHEDULE_DECISION` (Prioridade 5):** O mecanismo de escalonamento verifica se a CPU está ociosa e, havendo threads na fila de prontos, seleciona a próxima de acordo com a política.

O campo `número_sequencial` é um contador estritamente crescente gerenciado pela `EventQueue`, garantindo que eventos com mesmo instante e mesma prioridade sejam processados em ordem estrita de agendamento (FIFO determinístico).

---

## 3. Modelo de Processos e Threads

```
+-------------------------------------------------------------+
|                           Process                           |
|  - pcb: PCB (pid, state, priority, creation_time, ...)      |
|  - threads: list[SimulatedThread]                           |
+------------------------------+------------------------------+
                               | 1..* (Composição)
                               v
+-------------------------------------------------------------+
|                       SimulatedThread                       |
|  - tcb: TCB (tid, pid, state, registers, stack, ops, ...)   |
+-------------------------------------------------------------+
```

### 3.1 Unidade Escalonável
A unidade básica de alocação de tempo de CPU no simulador é a **Thread** (`SimulatedThread`), não o Processo.
- Cada thread pertence a **exatamente um processo**.
- O processo agrupa recursos, metadados globais e possui um ou mais threads concorrentes.
- Se uma thread de um processo bloquear em E/S, outra thread do **mesmo processo** (ou de outro processo) que esteja no estado `PRONTO` pode ser despachada e executar livremente.
- O processo só transiciona para o estado `FINALIZADO` quando **todas** as suas threads terminarem suas operações.

### 3.2 Estruturas de Controle: PCB e TCB

#### Bloco de Controle de Processo (`PCB`):
- `pid`: Identificador único do processo no sistema.
- `state`: Estado derivado do processo (`NOVO`, `PRONTO`, `EXECUTANDO`, `BLOQUEADO`, `FINALIZADO`).
- `priority`: Prioridade base atribuída ao processo.
- `creation_time`: Instante de admissão no sistema.
- `completion_time`: Instante em que a última thread foi concluída.
- `program_counter` e `registers`: Registradores de controle global do processo.
- `address_space`: Estrutura reservada para o mapeamento da tabela de páginas (Entrega 2).
- `open_files_table`: Tabela reservada para os descritores locais de arquivos abertos (Entrega 2).
- `state_history`: Registro auditável de todas as transições de estado do processo.

#### Bloco de Controle de Thread (`TCB`):
- `tid`: Identificador da thread (único no escopo do processo).
- `process_id`: Referência ao processo proprietário.
- `state`: Estado de execução atual da thread.
- `registers`: Dicionário com registradores lógicos simulados (`{"PC": int, "R0": int, "R1": int, "SP": int}`).
  - **Função no simulador:** Não se emula um conjunto completo de instruções (ISA), mas sim a preservação de contexto arquitetural. O registrador `PC` aponta para o índice da operação corrente na lista de operações da thread; `R0` e `R1` armazenam dados de trabalho incrementados durante a execução; e `SP` representa o apontador da pilha lógica privada da thread.
- `stack`: Lista representando a pilha lógica da thread (`["main()", ...]`), simulando o escopo de execução local da thread.
- `operations`: Lista de surtos alternados de CPU e E/S.
- Métricas acumuladas: `admission_time`, `first_execution_time`, `completion_time`, `total_cpu_time`, `total_io_time`, `total_ready_wait_time`, `last_ready_entry_time`.

### 3.3 Ciclo de Vida e Regras de Transição

```
               +--------------+
               |     NOVO     |
               +-------+------+
                       | Admissão
                       v
               +-------+------+       Despacho       +------------+
        +----->|    PRONTO    |-------------------->| EXECUTANDO |
        |      +-------+------+                     +-----+------+
        |              ^                                  |
Retorno |              | Fim de Quantum / Preempção       |
de E/S  |              | (planejado - Entrega 2)          |
        |              +----------------------------------+
        |                                                 | Bloqueio
        |      +--------------+                           | de E/S
        +------|  BLOQUEADO   |<--------------------------+
               +--------------+                           |
                                                          | Conclusão
                                                          v
                                                    +------------+
                                                    | FINALIZADO |
                                                    +------------+
```

#### Tabela de Transições Válidas para Threads:
- $\text{NOVO} \rightarrow \text{PRONTO}$: Ocorre na admissão do processo/thread no sistema.
- $\text{PRONTO} \rightarrow \text{EXECUTANDO}$: Ocorre quando o escalonador despacha a thread para a CPU.
- $\text{EXECUTANDO} \rightarrow \text{BLOQUEADO}$: Ocorre quando um surto de CPU termina e a próxima operação da thread é de E/S.
- $\text{EXECUTANDO} \rightarrow \text{FINALIZADO}$: Ocorre quando a thread completa sua última operação de CPU.
- $\text{EXECUTANDO} \rightarrow \text{PRONTO}$: Ocorre na preempção de tempo/prioridade (ponto de extensão para Round Robin/Prioridades na Entrega 2).
- $\text{BLOQUEADO} \rightarrow \text{PRONTO}$: Ocorre quando a interrupção de E/S sinaliza a conclusão da operação.

Qualquer transição direta fora dessa matriz (ex.: $\text{NOVO} \rightarrow \text{EXECUTANDO}$, $\text{PRONTO} \rightarrow \text{BLOQUEADO}$, ou alteração de estado em thread `FINALIZADA`) levanta imediatamente `InvalidStateTransitionError`, impedindo corrupção do modelo.

### 3.4 Regra de Derivação do Estado do Processo
O processo não possui fluxo de instruções próprio; seu estado reflete a composição de suas threads:
1. Se **todas** as threads estiverem em `FINALIZADO`, o processo é `FINALIZADO`.
2. Se **ao menos uma** thread estiver em `EXECUTANDO`, o processo é `EXECUTANDO`.
3. Se **ao menos uma** thread estiver em `PRONTO` (e nenhuma em `EXECUTANDO`), o processo é `PRONTO`.
4. Se **todas** as threads ativas (não finalizadas) estiverem em `BLOQUEADO`, o processo é `BLOQUEADO`.
5. Se **todas** as threads estiverem em `NOVO`, o processo é `NOVO`.

---

## 4. Escalonamento e Troca de Contexto

### 4.1 Separação Mecanismo vs. Política
A arquitetura adota o padrão Strategy para desacoplar a política de escalonamento do mecanismo operacional:

- **`Scheduler` (Mecanismo):** Mantém a referência à CPU (`SimulatedCPU`), controla o início e conclusão de trocas de contexto, acumula tempo de sobrecarga e interage com o `SimulationEngine`.
- **`SchedulingPolicy` (Interface Abstrata):** Define a assinatura dos métodos `add_thread`, `select_next_thread`, `peek_next_thread`, `remove_thread` e `get_ready_threads`.
- **`FCFSPolicy` (Política Concreta):** Implementa a política *First-Come, First-Served* não preemptiva utilizando uma fila estritamente FIFO (`collections.deque`).

### 4.2 Desempate na Fila de Prontos (FCFS)
- A seleção na fila de prontos ocorre em ordem FIFO de chegada.
- Uma thread que retorna de E/S é inserida no final da fila.
- Caso duas threads entrem na fila de prontos no **mesmo tick lógico**, o desempate determinístico segue a chave:
  $$\text{Chave de Desempate} = (\text{instante\_de\_admissão}, \text{PID}, \text{TID})$$

### 4.3 Custo e Sobrecarga de Troca de Contexto

A troca de contexto possui custo configurável $C \ge 0$ ticks:

1. **Momento da Cobrança:** A sobrecarga é cobrada **sempre que uma thread é despachada para a CPU**, inclusive no primeiro despacho após a CPU estar ociosa.
2. **Durante o Intervalo $[T, T + C]$:**
   - O estado da CPU é alterado para `CONTEXT_SWITCHING` (Troca de Contexto).
   - Nenhuma instrução útil da carga de trabalho é executada durante este intervalo.
   - O contador de trocas de contexto é incrementado em 1 e a sobrecarga acumulada em $C$.
   - Um evento `CONTEXT_SWITCH_END` é agendado para $T + C$.
3. **No Instante $T + C$:**
   - O evento `CONTEXT_SWITCH_END` é processado: a thread transiciona para `EXECUTANDO`, a CPU torna-se `BUSY` e o surto útil de CPU é agendado para $T + C + \text{duração}$.
4. **Caso $C = 0$:**
   - A troca é instantânea: a thread transiciona para `EXECUTANDO` imediatamente em $T$, a contagem de trocas é incrementada, mas o tempo de sobrecarga acumulado é 0.

#### Impacto Matemático da Troca de Contexto nas Métricas:
- **Tempo de Espera ($\text{Waiting Time}$):** Mede estritamente o tempo que a thread permaneceu aguardando na fila de prontos até ser selecionada pelo escalonador no instante $T_{\text{seleção}}$.
- **Tempo de Resposta ($\text{Response Time}$):** Mede o tempo desde a chegada da thread até o início da primeira execução útil:
  $$\text{Response Time} = T_{\text{início\_útil}} - T_{\text{chegada}} = (T_{\text{seleção}} + C) - T_{\text{chegada}} = \text{Waiting Time} + C$$
  Portanto, um custo de troca de contexto $C > 0$ aumenta diretamente o tempo de resposta inicial das threads em $C$ unidades por troca.

---

## 5. Gerenciamento Simplificado de Entrada e Saída

Na primeira entrega, a E/S opera sob um modelo bloqueante simplificado orientado a eventos:
1. Quando uma thread conclui um surto de CPU e possui uma operação de E/S subsequente, a thread transiciona para `BLOQUEADO` e a CPU é imediatamente liberada (`IDLE`).
2. O `SimplifiedIOManager` registra o bloqueio e calcula o instante de término: $T_{\text{fim}} = T_{\text{atual}} + \text{duração\_es}$.
3. Um evento `IO_COMPLETION` é agendado no relógio lógico para $T_{\text{fim}}$.
4. Enquanto a thread está bloqueada, **outras threads prontas podem executar normalmente** na CPU.
5. Em $T_{\text{fim}}$, uma **interrupção simulada** é gerada: a thread desbloqueia, avança sua operação e é reinserida no final da fila de prontos (`PRONTO`), tornando-se novamente elegível para escalonamento.
6. **Ausência de Espera Ativa:** Nenhuma thread consome tempo de CPU enquanto aguarda E/S.

---

## 6. Pontos de Extensão para a Entrega Final

A arquitetura atual foi intencionalmente modularizada com interfaces desacopladas, estabelecendo pontos de extensão limpos para a conclusão do projeto sem a necessidade de refatorações estruturais invasivas:

| Módulo Futuro | Ponto de Extensão Existente | Plano de Implementação |
| :--- | :--- | :--- |
| **Round Robin (RR)** | Subclasse de `SchedulingPolicy` | Implementar `RoundRobinPolicy` com controle de `quantum`. O `SimulationEngine` agendará evento `QUANTUM_EXPIRED` caso o surto de CPU exceda o quantum, provocando preempção (`EXECUTANDO -> PRONTO`). |
| **Escalonamento por Prioridades** | Subclasse de `SchedulingPolicy` | Implementar `PriorityPolicy` com ordenação por `thread.priority`. Caso configurado como preemptivo, a chegada de uma thread de maior prioridade gera preempção da thread atual na CPU. |
| **Gerência de Memória Paginada** | Campo `address_space` no `PCB` | Implementar `MemoryManager` com tabelas de páginas por processo, controle de molduras livres e substituição de páginas por **FIFO** (e opcional LRU). Falta de página agendará evento de falta, bloqueando a thread até o carregamento. |
| **Dispositivos Completos de E/S** | Módulo `simulator.io` | Substituir `SimplifiedIOManager` por classes `Device`, `BlockDevice` (disco com FCFS/SSTF/SCAN) e `CharacterDevice` (teclado/terminal) com filas de requisição independentes e operações assíncronas (não bloqueantes). |
| **Sistema de Arquivos Hierárquico** | Campo `open_files_table` no `PCB` | Criar `FileSystem` com diretório raiz, nós-i/FCB simplificados, tabela global de arquivos abertos e descritores por processo, implementando alocação contígua ou encadeada de blocos. |
