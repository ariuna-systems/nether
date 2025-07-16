# Nether Framework Architecture Review

## Framework Overview

The Nether framework is a sophisticated event-driven architecture built around the **Mediator Pattern** with support for asynchronous message processing, modular design, and workflow orchestration.

## ⚠️ Critical Architectural Guidance: DDD and Separation of Concerns

### **The Problem: Mixing Framework Modules with Business Logic**

❌ **COMMON MISTAKE**: Putting business workflows and domain logic directly in framework modules

```python
# ❌ WRONG - Business logic in framework module
class OrderProcessingSaga(Module[ProcessOrder]):
    async def handle(self, message: ProcessOrder, *, dispatch, join_stream):
        # ❌ Business rules and workflows directly in framework module
        if message.total_amount > 1000:
            # Apply enterprise discount
            discount = message.total_amount * 0.1
        
        # ❌ Domain logic mixed with message handling
        if not self._validate_inventory(message.items):
            raise InvalidInventoryError()
        
        # ❌ Complex business workflow in infrastructure layer
        await self._process_payment_with_retry_logic(message)
```

### **The Solution: Proper DDD Layering**

✅ **CORRECT**: Framework modules delegate to application services

```python
# ✅ RIGHT - Framework module is thin, delegates to application service
class OrderCommandHandler(Module[ProcessOrder]):
    def __init__(self, app: Application, order_service: OrderProcessingService):
        super().__init__(app)
        self._order_service = order_service  # Application layer
    
    async def handle(self, message: ProcessOrder, *, dispatch, join_stream):
        # ✅ Delegate to application service
        success, result = await self._order_service.process_order(
            message.order_id, message.customer_id, message.items
        )
        
        # ✅ Framework only handles coordination and events
        if success:
            await dispatch(OrderCreated(order_id=message.order_id))
        else:
            await dispatch(OrderFailed(order_id=message.order_id, error=result))
```

### **Architecture Layers**

```text
┌─────────────────────────────────────────┐
│ INFRASTRUCTURE LAYER                    │
│ • Framework Modules (Message Handlers)  │ ← Nether modules go here
│ • Repositories (Implementations)        │
│ • External Service Adapters            │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ APPLICATION LAYER                       │
│ • Application Services (Use Cases)      │ ← Business workflows go here
│ • Command/Query Handlers                │
│ • Workflow Orchestration                │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│ DOMAIN LAYER                           │
│ • Entities & Value Objects             │ ← Business logic goes here
│ • Domain Services                      │
│ • Business Rules & Invariants          │
└─────────────────────────────────────────┘
```

### **What Framework Modules Should Do**

✅ **Framework modules should be THIN and only handle:**

1. **Message Routing**: Dispatch messages to appropriate application services
2. **Event Emission**: Convert service results into domain events
3. **Coordination**: Orchestrate calls between different services
4. **Cross-cutting Concerns**: Logging, metrics, error handling

### **What Framework Modules Should NOT Do**

❌ **Framework modules should NEVER contain:**

1. **Business Rules**: Domain logic belongs in domain/application layers
2. **Workflow Logic**: Complex business processes belong in application services
3. **Data Validation**: Business validation belongs in domain entities
4. **State Management**: Domain state belongs in entities and aggregates

### **Example: Proper Separation**

See [`examples/proper_ddd_example.py`](../examples/proper_ddd_example.py) for a complete demonstration of:

- ✅ Domain entities with business logic
- ✅ Application services with use cases
- ✅ Framework modules that only handle messages
- ✅ Clear dependency flow: Infrastructure → Application → Domain

## Core Components

### 1. **Message Types** (`common.py`)

```python
@dataclass(frozen=True, kw_only=True)
class Message:
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))

@dataclass(frozen=True)
class Command(Message): ...    # Intent to change state

@dataclass(frozen=True)  
class Query(Message): ...      # Request for information

@dataclass(frozen=True)
class Event(Message): ...      # Something that happened
```

**Key Features:**

- **Commands**: Represent intent to perform an action (imperative)
- **Queries**: Request information without side effects
- **Events**: Notifications about something that occurred (past tense)
- All messages are immutable (`frozen=True`) and include timestamps

### 2. **Mediator** (`mediator.py`)

The central orchestrator that routes messages between modules.

**Key Features:**

- **Singleton Pattern**: Ensures single instance across application
- **Context Management**: Isolated units of work with dedicated queues
- **Asynchronous Processing**: Non-blocking message handling
- **Module Registration**: Dynamic service discovery and routing

**Architecture:**

```text
Application
    ↓
Mediator (Singleton)
    ↓
Context (Unit of Work)
    ↓
Modules (Message Handlers)
```

### 3. **Modules** (`module.py`)

Self-contained units that handle specific message types.

```python
class Module[T: Message](ModuleProtocol[T]):
    @property
    def supports(self) -> type[T]:
        # Automatically determined from generic type parameter
        
    async def handle(self, message: Message, *, dispatch, join_stream):
        # Process the message and optionally dispatch new messages
```

### 4. **Application** (`application.py`)

The main application container that manages the lifecycle.

## What You Can Do with Event Dispatching and Commands

### 1. **Simple Command-Event Flow**

```python
# Command: Intent to do something
@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessOrder(Command):
    order_id: str
    customer_id: str

# Event: Something that happened
@dataclass(frozen=True, slots=True, kw_only=True)
class OrderProcessed(Event):
    order_id: str
    status: str

class OrderProcessor(Module[ProcessOrder]):
    async def handle(self, message: ProcessOrder, *, dispatch, join_stream):
        # Process the order
        result = await self._process_order(message.order_id)
        
        # Dispatch result event
        await dispatch(OrderProcessed(
            order_id=message.order_id,
            status="completed"
        ))
```

### 2. **Chain of Events (Event Sourcing Pattern)**

```python
class OrderEventListener(Module[OrderProcessed]):
    async def handle(self, message: OrderProcessed, *, dispatch, join_stream):
        # React to order being processed
        if message.status == "completed":
            await dispatch(SendConfirmationEmail(order_id=message.order_id))
            await dispatch(UpdateInventory(order_id=message.order_id))
```

### 3. **Saga Pattern for Distributed Transactions**

```python
class PaymentSaga(Module[OrderProcessed | PaymentFailed]):
    async def handle(self, message, *, dispatch, join_stream):
        match message:
            case OrderProcessed():
                await dispatch(ProcessPayment(order_id=message.order_id))
            case PaymentFailed():
                await dispatch(RefundOrder(order_id=message.order_id))
```

## Creating Workflows and Pipelines

### 1. **Sequential Workflows**

```python
# Define workflow steps
steps = ["validate", "process", "notify"]

class WorkflowManager(Module[StartWorkflow]):
    async def handle(self, message: StartWorkflow, *, dispatch, join_stream):
        for step in steps:
            await dispatch(WorkflowStep(
                workflow_id=message.workflow_id,
                step_name=step
            ))
```

### 2. **Parallel Processing Pipelines**

```python
class DataPipeline(Module[ProcessData]):
    async def handle(self, message: ProcessData, *, dispatch, join_stream):
        # Start parallel processing stages
        tasks = []
        for processor in ["validator", "enricher", "transformer"]:
            tasks.append(dispatch(ProcessDataStage(
                data=message.data,
                processor=processor
            )))
        
        await asyncio.gather(*tasks)
```

### 3. **Conditional Workflows**

```python
class ConditionalWorkflow(Module[WorkflowStep]):
    async def handle(self, message: WorkflowStep, *, dispatch, join_stream):
        if message.step_name == "decision_point":
            if self._should_approve(message.data):
                await dispatch(WorkflowStep(step_name="approve"))
            else:
                await dispatch(WorkflowStep(step_name="reject"))
```

## Cycle Detection in Workflows

### Why Cycle Detection Matters

- **Infinite Loops**: Prevents workflows from running indefinitely
- **Resource Exhaustion**: Avoids memory/CPU consumption from circular dependencies
- **Deadlocks**: Prevents mutual dependencies that can't be resolved

### Implementation Approaches

#### 1. **Depth-First Search (DFS) Cycle Detection**

```python
class CycleDetector:
    def has_cycle(self, workflow_type: str) -> bool:
        visited = set()
        rec_stack = set()  # Recursion stack for DFS
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:  # Back edge = cycle
                    return True
                    
            rec_stack.remove(node)
            return False
        
        # Check all components
        for step in self.workflow_definitions[workflow_type]:
            if step not in visited:
                if dfs(step):
                    return True
        return False
```

#### 2. **Topological Sort for Execution Order**

```python
def get_topological_order(self, workflow_type: str) -> list[str] | None:
    """Returns execution order if no cycles, None if cycles exist"""
    
    # Kahn's Algorithm
    in_degree = dict.fromkeys(steps, 0)
    
    # Calculate in-degrees
    for step, deps in workflow_definitions.items():
        for dep in deps:
            in_degree[step] += 1
    
    # Start with steps having no dependencies
    queue = deque([step for step, degree in in_degree.items() if degree == 0])
    result = []
    
    while queue:
        current = queue.popleft()
        result.append(current)
        
        # Update dependent steps
        for dependent in self._get_dependents(current):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
    
    # If not all steps processed, there's a cycle
    return result if len(result) == len(steps) else None
```

### 3. **Runtime Cycle Prevention**

```python
class WorkflowExecutor:
    def __init__(self):
        self.execution_stack: dict[str, set[str]] = {}
    
    async def execute_step(self, workflow_id: str, step_name: str):
        if workflow_id not in self.execution_stack:
            self.execution_stack[workflow_id] = set()
            
        if step_name in self.execution_stack[workflow_id]:
            raise CyclicExecutionError(f"Cycle detected: {step_name}")
            
        self.execution_stack[workflow_id].add(step_name)
        try:
            await self._do_execute_step(step_name)
        finally:
            self.execution_stack[workflow_id].remove(step_name)
```

## Advanced Patterns

### 1. **Event Streaming with Join Streams**

```python
class StreamProcessor(Module[DataEvent]):
    async def handle(self, message: DataEvent, *, dispatch, join_stream):
        stream_queue, stop_event = join_stream()
        
        # Subscribe to real-time events
        while not stop_event.is_set():
            try:
                event_data = await asyncio.wait_for(
                    stream_queue.get(), 
                    timeout=1.0
                )
                await self._process_stream_data(event_data)
            except asyncio.TimeoutError:
                continue
```

### 2. **Message Aggregation**

```python
class OrderAggregator(Module[OrderItemProcessed]):
    def __init__(self, application):
        super().__init__(application)
        self.pending_orders: dict[str, set[str]] = {}
        
    async def handle(self, message: OrderItemProcessed, *, dispatch, join_stream):
        order_id = message.order_id
        item_id = message.item_id
        
        if order_id not in self.pending_orders:
            self.pending_orders[order_id] = set()
            
        self.pending_orders[order_id].add(item_id)
        
        # Check if all items processed
        if len(self.pending_orders[order_id]) >= message.total_items:
            await dispatch(OrderFullyProcessed(order_id=order_id))
            del self.pending_orders[order_id]
```

### 3. **Circuit Breaker Pattern**

```python
class CircuitBreakerModule(Module[ExternalServiceCall]):
    def __init__(self, application):
        super().__init__(application)
        self.failure_count = 0
        self.last_failure_time = 0
        self.circuit_open = False
        
    async def handle(self, message: ExternalServiceCall, *, dispatch, join_stream):
        if self._should_allow_request():
            try:
                result = await self._call_external_service(message)
                self._on_success()
                await dispatch(ExternalServiceSuccess(result=result))
            except Exception as e:
                self._on_failure()
                await dispatch(ExternalServiceFailure(error=str(e)))
```

## Workflow Examples and Use Cases

### 1. **E-commerce Order Processing**

```python
# Workflow definition with dependencies
order_workflow = {
    "validate_order": [],                    # Entry point
    "check_inventory": ["validate_order"],   # Depends on validation
    "process_payment": ["validate_order"],   # Parallel with inventory
    "ship_order": ["check_inventory", "process_payment"],  # Waits for both
    "send_confirmation": ["ship_order"]      # Final step
}
```

**Flow Visualization:**

```text
validate_order
    ↓
[check_inventory] [process_payment]
    ↓                ↓
    └── ship_order ──┘
           ↓
    send_confirmation
```

### 2. **Data Processing Pipeline**

```python
# ETL Pipeline with sequential dependencies
data_pipeline = {
    "extract_data": [],
    "validate_data": ["extract_data"],
    "transform_data": ["validate_data"],
    "enrich_data": ["transform_data"],
    "load_data": ["enrich_data"],
    "generate_report": ["load_data"]
}
```

### 3. **Content Publishing Workflow**

```python
# Complex workflow with multiple branches
publishing_workflow = {
    "draft_content": [],
    "review_content": ["draft_content"],
    "approve_content": ["review_content"],
    "format_content": ["approve_content"],
    "generate_thumbnail": ["approve_content"],
    "publish_content": ["format_content", "generate_thumbnail"],
    "notify_subscribers": ["publish_content"],
    "update_analytics": ["publish_content"]
}
```

## Compensation and Error Handling

### 1. **Saga Pattern with Compensation**

```python
class OrderSaga(Module[OrderEvent]):
    def __init__(self, application):
        super().__init__(application)
        self.compensation_stack: dict[str, list[str]] = {}
    
    async def handle(self, message: OrderEvent, *, dispatch, join_stream):
        match message:
            case PaymentFailed():
                # Execute compensation in reverse order
                compensations = self.compensation_stack.get(message.order_id, [])
                for action in reversed(compensations):
                    await dispatch(CompensationAction(action=action))
```

### 2. **Circuit Breaker for External Services**

```python
class ExternalServiceModule(Module[ExternalCall]):
    def __init__(self, application):
        super().__init__(application)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_time=30,
            expected_exception=ServiceUnavailableError
        )
    
    async def handle(self, message: ExternalCall, *, dispatch, join_stream):
        try:
            result = await self.circuit_breaker.call(
                self._make_external_call, message.data
            )
            await dispatch(ExternalCallSuccess(result=result))
        except CircuitBreakerOpenError:
            await dispatch(ExternalCallFailed(reason="circuit_breaker_open"))
```

## Benefits of This Architecture

1. **Loose Coupling**: Modules don't directly depend on each other
2. **Testability**: Easy to test individual components in isolation
3. **Scalability**: Can distribute modules across different processes/machines
4. **Maintainability**: Clear separation of concerns
5. **Flexibility**: Easy to add new features without modifying existing code
6. **Error Isolation**: Failures in one module don't crash the entire system
7. **Auditability**: All messages are logged and traceable
8. **Workflow Validation**: Built-in cycle detection prevents infinite loops

## Best Practices

### 1. **Message Design**

- Keep messages immutable and focused
- Use clear, descriptive names (OrderProcessed vs MessageReceived)
- Include all necessary data to avoid additional lookups
- Version your messages for backward compatibility

### 2. **Module Responsibility**

- Each module should have a single responsibility
- Modules should be stateless where possible
- Use dependency injection for external services
- Handle errors gracefully and emit appropriate events

### 3. **Workflow Design**

- Always validate workflow definitions for cycles
- Design for idempotency - steps should be safe to retry
- Include compensation logic for complex workflows
- Monitor workflow execution and completion rates

### 4. **Performance Considerations**

- Monitor message processing times and queue depths
- Use connection pooling for database/external service calls
- Implement backpressure handling for high-throughput scenarios
- Consider batching for bulk operations

### 5. **Error Handling**

- Always handle exceptions and emit appropriate events
- Implement circuit breakers for external service calls
- Use exponential backoff for retries
- Log errors with sufficient context for debugging

### 6. **Testing Strategies**

- Unit test individual modules in isolation
- Integration test workflow scenarios
- Use mock dispatch functions for testing
- Test error scenarios and compensation logic

This architecture provides a solid foundation for building complex, distributed systems with clear message flows, proper error handling, and scalable workflow orchestration.
