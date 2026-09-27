# Diagrama de Classes do Simulador de SO

**Disciplina de Sistemas Operacionais**  
**Prof. Maurício Acconcia Dias**

---

## 1. Diagrama de Classes Implementado (Primeira Entrega)

O diagrama abaixo representa com fidelidade as classes, atributos, métodos, composições, agregações e interfaces efetivamente implementadas na primeira entrega do projeto.

```mermaid
classDiagram
    direction TB

    class SimulationEngine {
        -Clock clock
        -EventQueue event_queue
        -Scheduler scheduler
        -SimplifiedIOManager io_manager
        -EventLogger logger
        -MetricsCollector metrics_collector
        -list~Process~ processes
        -bool _schedule_pending
        +load_workload(processes)
        +run() tuple~SystemMetrics, list~ProcessMetrics~~
        -_handle_process_arrival(event)
        -_handle_schedule_decision(event)
        -_handle_context_switch_end(event)
        -_handle_cpu_burst_end(event)
        -_handle_io_completion(event)
        -_request_schedule()
    }

    class Clock {
        -int _current_time
        +time() int
        +advance_to(new_time) int
        +reset(initial_time) void
    }

    class EventQueue {
        -list~Event~ _heap
        -int _seq_counter
        +schedule(time, event_type, pid, tid, desc, payload) Event
        +pop_next() Event
        +peek_next() Event
        +is_empty() bool
        +clear() void
    }

    class Event {
        +int time
        +int priority
        +int seq
        +EventType event_type
        +int pid
        +int tid
        +str description
        +dict payload
    }

    class EventType {
        <<enumeration>>
        IO_COMPLETION = 1
        PROCESS_ARRIVAL = 2
        CONTEXT_SWITCH_END = 3
        CPU_BURST_END = 4
        SCHEDULE_DECISION = 5
    }

    class Process {
        -PCB pcb
        -list~SimulatedThread~ _threads
        +pid() int
        +state() ProcessState
        +priority() int
        +creation_time() int
        +completion_time() int
        +turnaround_time() int
        +add_thread(thread) void
        +update_derived_state(current_time, cause) ProcessState
        +is_terminated() bool
    }

    class PCB {
        +int pid
        +int priority
        +int creation_time
        +ProcessState state
        +int completion_time
        +int program_counter
        +dict registers
        +Any address_space
        +list open_files_table
        +list state_history
        +record_transition(current_time, state, cause) void
    }

    class SimulatedThread {
        -TCB tcb
        +tid() int
        +process_id() int
        +id_str() str
        +state() ThreadState
        +priority() int
        +arrival_time() int
        +waiting_time() int
        +response_time() int
        +turnaround_time() int
        +transition_to(target_state, current_time, cause) void
        +get_current_operation() Operation
        +advance_operation() Operation
        +has_more_operations() bool
        +is_terminated() bool
    }

    class TCB {
        +int tid
        +int process_id
        +int priority
        +int arrival_time
        +list~Operation~ operations
        +ThreadState state
        +int current_op_index
        +dict registers
        +list~str~ stack
        +int first_execution_time
        +int completion_time
        +int total_cpu_time
        +int total_io_time
        +int total_ready_wait_time
        +record_transition(current_time, state, cause) void
    }

    class Operation {
        +OperationType op_type
        +int duration
    }

    class OperationType {
        <<enumeration>>
        CPU
        IO
    }

    class ProcessState {
        <<enumeration>>
        NEW = "NOVO"
        READY = "PRONTO"
        RUNNING = "EXECUTANDO"
        BLOCKED = "BLOQUEADO"
        TERMINATED = "FINALIZADO"
    }

    class ThreadState {
        <<enumeration>>
        NEW = "NOVO"
        READY = "PRONTO"
        RUNNING = "EXECUTANDO"
        BLOCKED = "BLOQUEADO"
        TERMINATED = "FINALIZADO"
    }

    class Scheduler {
        -SchedulingPolicy policy
        -SimulatedCPU cpu
        +int context_switch_cost
        +int context_switches_count
        +int total_context_switch_time
        +add_ready_thread(thread, current_time, cause) void
        +select_next_thread() SimulatedThread
        +start_context_switch(thread) void
        +finish_context_switch(thread, current_time, cause) void
        +dispatch_immediately(thread, current_time, cause) void
        +release_cpu() SimulatedThread
        +is_cpu_idle() bool
        +has_ready_threads() bool
    }

    class SimulatedCPU {
        +CPUState state
        +SimulatedThread current_thread
        +is_idle() bool
        +is_busy() bool
        +is_switching() bool
        +start_context_switch(thread) void
        +start_execution(thread) void
        +release() SimulatedThread
    }

    class CPUState {
        <<enumeration>>
        IDLE = "OCIOSA"
        CONTEXT_SWITCHING = "TROCA_DE_CONTEXTO"
        BUSY = "EXECUTANDO"
    }

    class SchedulingPolicy {
        <<interface>>
        +name() str*
        +add_thread(thread)* void
        +select_next_thread()* SimulatedThread
        +peek_next_thread()* SimulatedThread
        +remove_thread(thread)* bool
        +is_empty()* bool
        +get_ready_threads()* list~SimulatedThread~
    }

    class FCFSPolicy {
        -deque~SimulatedThread~ _ready_queue
        +name() str
        +add_thread(thread) void
        +select_next_thread() SimulatedThread
        +peek_next_thread() SimulatedThread
        +remove_thread(thread) bool
        +is_empty() bool
        +get_ready_threads() list~SimulatedThread~
    }

    class SimplifiedIOManager {
        -dict _blocked_threads
        +start_io(thread, duration, current_time, cause) int
        +complete_io(thread, current_time, cause) SimulatedThread
        +get_blocked_count() int
        +is_blocked(thread) bool
    }

    class WorkloadLoader {
        +load_from_file(filepath) list~Process~
        +load_from_dict(data) list~Process~
    }

    class EventLogger {
        +str config_summary
        +list~LogEntry~ entries
        +log(clock, event_type, pid, tid, desc) LogEntry
        +get_text() str
        +write_to_file(filepath) void
    }

    class MetricsCollector {
        +compute(processes, sim_time, switches, cs_time) tuple
        +format_report(system_metrics, process_metrics) str
    }

    %% Relacionamentos
    SimulationEngine *-- Clock : compõe
    SimulationEngine *-- EventQueue : compõe
    SimulationEngine *-- Scheduler : compõe
    SimulationEngine *-- SimplifiedIOManager : compõe
    SimulationEngine *-- EventLogger : compõe
    SimulationEngine *-- MetricsCollector : compõe
    SimulationEngine o-- Process : gerencia

    EventQueue o-- Event : enfileira
    Event --> EventType : tipifica

    Process *-- PCB : possui
    Process *-- "1..*" SimulatedThread : agrega
    PCB --> ProcessState : reflete

    SimulatedThread *-- TCB : possui
    TCB --> ThreadState : reflete
    TCB *-- "1..*" Operation : contém
    Operation --> OperationType : tipifica

    Scheduler *-- SimulatedCPU : controla
    Scheduler o-- SchedulingPolicy : utiliza
    SimulatedCPU --> CPUState : reflete
    SimulatedCPU o-- SimulatedThread : executa

    SchedulingPolicy <|.. FCFSPolicy : implementa
    FCFSPolicy o-- SimulatedThread : enfileira
    SimplifiedIOManager o-- SimulatedThread : monitora
```

---

## 2. Diagrama de Classes Planejado para a Entrega Final

O diagrama a seguir descreve a **arquitetura planejada** que expandirá o simulador na Entrega Final, integrando as novas políticas de escalonamento, memória virtual paginada, subsistema completo de E/S com dispositivos independentes e sistema de arquivos hierárquico.

```mermaid
classDiagram
    direction TB

    %% Políticas de Escalonamento Adicionais
    class SchedulingPolicy {
        <<interface>>
        +select_next_thread()* SimulatedThread
        +add_thread(thread)* void
    }

    class FCFSPolicy {
        +select_next_thread() SimulatedThread
    }

    class RoundRobinPolicy {
        -int quantum
        -deque~SimulatedThread~ _ready_queue
        +select_next_thread() SimulatedThread
        +check_quantum_expiration(current_burst) bool
    }

    class PriorityPolicy {
        -bool is_preemptive
        -list~SimulatedThread~ _priority_queue
        +select_next_thread() SimulatedThread
        +apply_aging() void
    }

    SchedulingPolicy <|.. FCFSPolicy : implementa
    SchedulingPolicy <|.. RoundRobinPolicy : implementa (planejada)
    SchedulingPolicy <|.. PriorityPolicy : implementa (planejada)

    %% Subsistema de Memória Paginada
    class MemoryManager {
        -int page_size
        -int total_frames
        -list~Frame~ frames
        -PageReplacementPolicy replacement_policy
        +translate_address(process, logical_addr) int
        +handle_page_fault(process, page_number) Frame
    }

    class PageTable {
        -dict~int, PageTableEntry~ entries
        +is_present(page_num) bool
        +get_frame(page_num) int
        +map(page_num, frame_num) void
    }

    class PageReplacementPolicy {
        <<interface>>
        +select_victim(frames)* int
    }

    class FIFOReplacementPolicy {
        -deque~int~ frame_order
        +select_victim(frames) int
    }

    MemoryManager *-- PageReplacementPolicy : utiliza
    PageReplacementPolicy <|.. FIFOReplacementPolicy : implementa
    Process o-- PageTable : possui (via PCB)

    %% Subsistema de E/S e Dispositivos
    class DeviceManager {
        -dict~str, Device~ devices
        +request_io(device_id, thread, req_type, block_num) void
        +dispatch_device_queues() void
    }

    class Device {
        <<abstract>>
        +str device_id
        +int service_time
        +bool is_busy
        +DeviceQueue queue
        +process_next_request()* void
    }

    class BlockDevice {
        -int current_track
        -DiskSchedulingPolicy disk_scheduler
        +read_block(block_num) void
        +write_block(block_num) void
    }

    class CharacterDevice {
        +read_char() str
        +write_char(char) void
    }

    Device <|-- BlockDevice : herda
    Device <|-- CharacterDevice : herda
    DeviceManager *-- Device : gerencia

    %% Subsistema de Arquivos
    class FileSystem {
        -Directory root_directory
        -GlobalOpenFileTable global_open_table
        +create_file(path, permissions) FCB
        +open_file(process, path, mode) int
        +read_file(process, fd, bytes) bytes
        +write_file(process, fd, data) int
        +close_file(process, fd) void
    }

    class FCB {
        +str name
        +str file_type
        +int size_bytes
        +int permissions
        +list~int~ allocated_blocks
    }

    class GlobalOpenFileTable {
        -dict~int, OpenFileEntry~ open_files
        +register_open(fcb, mode) int
        +deregister_open(entry_id) void
    }

    FileSystem *-- GlobalOpenFileTable : coordena
    FileSystem o-- FCB : manipula
    Process o-- "open_files_table" : mapeia descritor local
```
