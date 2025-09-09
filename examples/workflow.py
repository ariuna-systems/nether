"""
Framework Architecture Review and Workflow Examples

This file demonstrates various patterns for event dispatching, commands,
workflows, and pipeline creation using the Nether framework.
"""

import asyncio
import logging
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from nether import Application, execute
from nether.component import Component
from nether.message import Command, Event, Message

# 1. WORKFLOW COMMANDS AND EVENTS


@dataclass(frozen=True, slots=True, kw_only=True)
class StartWorkflow(Command):
    """Command to start a workflow with a unique ID"""

    workflow_id: str
    workflow_type: str
    initial_data: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowStep(Command):
    """Command to execute a specific step in a workflow"""

    workflow_id: str
    step_name: str
    step_data: dict = field(default_factory=dict)
    previous_step: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowCompleted(Event):
    """Event emitted when a workflow completes successfully"""

    workflow_id: str
    workflow_type: str
    final_data: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class WorkflowFailed(Event):
    """Event emitted when a workflow fails"""

    workflow_id: str
    step_name: str
    error: str


@dataclass(frozen=True, slots=True, kw_only=True)
class StepCompleted(Event):
    """Event emitted when a workflow step completes"""

    workflow_id: str
    step_name: str
    result_data: dict = field(default_factory=dict)
    next_steps: list[str] = field(default_factory=list)


# 2. PIPELINE COMMANDS AND EVENTS


@dataclass(frozen=True, slots=True, kw_only=True)
class StartPipeline(Command):
    """Command to start a data processing pipeline"""

    pipeline_id: str
    data: Any


@dataclass(frozen=True, slots=True, kw_only=True)
class PipelineStage(Command):
    """Command to process data through a pipeline stage"""

    pipeline_id: str
    stage_name: str
    data: Any
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class PipelineCompleted(Event):
    """Event emitted when pipeline processing completes"""

    pipeline_id: str
    final_data: Any
    processing_time: float


@dataclass(frozen=True, slots=True, kw_only=True)
class StageProcessed(Event):
    """Event emitted when a pipeline stage completes"""

    pipeline_id: str
    stage_name: str
    processed_data: Any
    next_stage: str | None = None


# 3. CYCLE DETECTION UTILITIES


class CycleDetector:
    """Utility class to detect cycles in workflow definitions"""

    def __init__(self):
        self.graph: dict[str, list[str]] = defaultdict(list)
        self.workflow_definitions: dict[str, dict[str, list[str]]] = {}

    def register_workflow_definition(self, workflow_type: str, step_dependencies: dict[str, list[str]]):
        """
        Register a workflow definition with step dependencies.

        Args:
            workflow_type: Name of the workflow type
            step_dependencies: Dict mapping step names to their dependencies
        """
        self.workflow_definitions[workflow_type] = step_dependencies

        # Build graph for cycle detection
        self.graph[workflow_type] = []
        for step, deps in step_dependencies.items():
            for dep in deps:
                self.graph[dep].append(step)

    def has_cycle(self, workflow_type: str) -> bool:
        """Check if a workflow definition has cycles using DFS"""
        if workflow_type not in self.workflow_definitions:
            return False

        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in self.graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        # Check all nodes in the workflow
        for step in self.workflow_definitions[workflow_type]:
            if step not in visited:
                if dfs(step):
                    return True
        return False

    def get_topological_order(self, workflow_type: str) -> list[str] | None:
        """Get topological ordering of workflow steps (if no cycles exist)"""
        if self.has_cycle(workflow_type):
            return None

        if workflow_type not in self.workflow_definitions:
            return None

        steps = list(self.workflow_definitions[workflow_type].keys())
        in_degree = dict.fromkeys(steps, 0)

        # Calculate in-degrees
        for step, deps in self.workflow_definitions[workflow_type].items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[step] += 1

        # Kahn's algorithm for topological sorting
        queue = deque([step for step, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            # Reduce in-degree for dependent steps
            for step, deps in self.workflow_definitions[workflow_type].items():
                if current in deps:
                    in_degree[step] -= 1
                    if in_degree[step] == 0:
                        queue.append(step)

        return result if len(result) == len(steps) else None


# 4. WORKFLOW ORCHESTRATOR MODULE


class WorkflowOrchestrator(Component[StartWorkflow | WorkflowStep]):
    """Orchestrates workflow execution and step coordination"""

    def __init__(self, application: Application):
        super().__init__(application)
        self.active_workflows: dict[str, dict] = {}
        self.cycle_detector = CycleDetector()
        self._register_workflow_definitions()

    def _register_workflow_definitions(self):
        """Register workflow definitions with dependencies"""

        # Example: Order Processing Workflow
        order_workflow = {
            "validate_order": [],  # No dependencies
            "check_inventory": ["validate_order"],
            "process_payment": ["validate_order"],
            "ship_order": ["check_inventory", "process_payment"],
            "send_confirmation": ["ship_order"],
        }
        self.cycle_detector.register_workflow_definition("order_processing", order_workflow)

        # Example: Data Processing Pipeline
        data_pipeline = {
            "extract_data": [],
            "validate_data": ["extract_data"],
            "transform_data": ["validate_data"],
            "enrich_data": ["transform_data"],
            "load_data": ["enrich_data"],
            "generate_report": ["load_data"],
        }
        self.cycle_detector.register_workflow_definition("data_processing", data_pipeline)

        # Example: Problematic workflow with cycle (for demonstration)
        cyclic_workflow = {"step_a": ["step_c"], "step_b": ["step_a"], "step_c": ["step_b"]}
        self.cycle_detector.register_workflow_definition("cyclic_workflow", cyclic_workflow)

    async def handle(
        self,
        message: StartWorkflow | WorkflowStep,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        match message:
            case StartWorkflow():
                await self._handle_start_workflow(message, handler)
            case WorkflowStep():
                await self._handle_workflow_step(message, handler)

    async def _handle_start_workflow(
        self, command: StartWorkflow, handler: Callable[[Message], Awaitable[None]]
    ) -> None:
        """Handle workflow initialization"""
        self._logger.info(f"Starting workflow {command.workflow_id} of type {command.workflow_type}")

        # Check for cycles
        if self.cycle_detector.has_cycle(command.workflow_type):
            error_msg = f"Workflow {command.workflow_type} contains cycles!"
            self._logger.error(error_msg)
            await handler(WorkflowFailed(workflow_id=command.workflow_id, step_name="initialization", error=error_msg))
            return

        # Get execution order
        execution_order = self.cycle_detector.get_topological_order(command.workflow_type)
        if not execution_order:
            error_msg = f"Could not determine execution order for {command.workflow_type}"
            self._logger.error(error_msg)
            await handler(WorkflowFailed(workflow_id=command.workflow_id, step_name="initialization", error=error_msg))
            return

        # Initialize workflow state
        self.active_workflows[command.workflow_id] = {
            "type": command.workflow_type,
            "execution_order": execution_order,
            "completed_steps": set(),
            "current_data": command.initial_data,
            "step_results": {},
        }

        # Start with first step(s) that have no dependencies
        workflow_def = self.cycle_detector.workflow_definitions[command.workflow_type]
        initial_steps = [step for step, deps in workflow_def.items() if not deps]

        for step in initial_steps:
            await handler(WorkflowStep(workflow_id=command.workflow_id, step_name=step, step_data=command.initial_data))

    async def _handle_workflow_step(self, command: WorkflowStep, handler: Callable[[Message], Awaitable[None]]) -> None:
        """Handle individual workflow step execution"""
        workflow_id = command.workflow_id

        if workflow_id not in self.active_workflows:
            self._logger.error(f"Workflow {workflow_id} not found")
            return

        workflow = self.active_workflows[workflow_id]
        self._logger.info(f"Executing step {command.step_name} in workflow {workflow_id}")

        # Simulate step processing
        await asyncio.sleep(0.1)  # Simulate work

        # Mark step as completed
        workflow["completed_steps"].add(command.step_name)
        workflow["step_results"][command.step_name] = command.step_data

        # Determine next steps
        workflow_def = self.cycle_detector.workflow_definitions[workflow["type"]]
        next_steps = []

        for step, deps in workflow_def.items():
            if step not in workflow["completed_steps"]:
                # Check if all dependencies are satisfied
                if all(dep in workflow["completed_steps"] for dep in deps):
                    next_steps.append(step)

        # Emit step completion event
        await handler(
            StepCompleted(
                workflow_id=workflow_id,
                step_name=command.step_name,
                result_data=command.step_data,
                next_steps=next_steps,
            )
        )

        # Start next steps
        for next_step in next_steps:
            await handler(
                WorkflowStep(
                    workflow_id=workflow_id,
                    step_name=next_step,
                    step_data=workflow["step_results"].get(command.step_name, {}),
                    previous_step=command.step_name,
                )
            )

        # Check if workflow is complete
        if len(workflow["completed_steps"]) == len(workflow_def):
            await handler(
                WorkflowCompleted(
                    workflow_id=workflow_id, workflow_type=workflow["type"], final_data=workflow["current_data"]
                )
            )
            del self.active_workflows[workflow_id]


# 5. STEP PROCESSORS


class OrderValidationProcessor(Component[WorkflowStep]):
    """Processes order validation steps"""

    async def handle(
        self,
        message: WorkflowStep,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        if message.step_name == "validate_order":
            self._logger.info(f"Validating order in workflow {message.workflow_id}")
            # Simulate validation logic
            await asyncio.sleep(0.5)
            # The WorkflowOrchestrator will handle step completion


class InventoryProcessor(Component[WorkflowStep]):
    """Processes inventory-related steps"""

    async def handle(
        self,
        message: WorkflowStep,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        if message.step_name == "check_inventory":
            self._logger.info(f"Checking inventory for workflow {message.workflow_id}")
            await asyncio.sleep(0.3)


class PaymentProcessor(Component[WorkflowStep]):
    """Processes payment-related steps"""

    async def handle(
        self,
        message: WorkflowStep,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        if message.step_name == "process_payment":
            self._logger.info(f"Processing payment for workflow {message.workflow_id}")
            await asyncio.sleep(0.7)


# 6. EVENT LISTENERS


class WorkflowEventListener(Component[WorkflowCompleted | WorkflowFailed | StepCompleted]):
    """Listens to workflow events for monitoring and logging"""

    async def handle(
        self,
        message: WorkflowCompleted | WorkflowFailed | StepCompleted,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        match message:
            case WorkflowCompleted():
                self._logger.info(f" Workflow {message.workflow_id} completed successfully!")

            case WorkflowFailed():
                self._logger.error(f" Workflow {message.workflow_id} failed at {message.step_name}: {message.error}")

            case StepCompleted():
                self._logger.info(f"Step {message.step_name} completed in workflow {message.workflow_id}")
                if message.next_steps:
                    self._logger.info(f"   Next steps: {', '.join(message.next_steps)}")


# 7. DEMONSTRATION APPLICATION


class WorkflowDemoApplication(Application):
    async def main(self) -> None:
        self.logger.info("Starting Workflow Demo Application")

        # Demonstrate cycle detection
        orchestrator = None
        for module in self.modules:
            if isinstance(module, WorkflowOrchestrator):
                orchestrator = module
                break

        if orchestrator:
            # Test cycle detection
            self.logger.info("\n=== CYCLE DETECTION TESTS ===")

            workflows = ["order_processing", "data_processing", "cyclic_workflow"]
            for workflow_type in workflows:
                has_cycle = orchestrator.cycle_detector.has_cycle(workflow_type)
                topological_order = orchestrator.cycle_detector.get_topological_order(workflow_type)

                self.logger.info(f"Workflow: {workflow_type}")
                self.logger.info(f"  Has cycle: {has_cycle}")
                self.logger.info(f"  Execution order: {topological_order}")

        # Start some example workflows
        self.logger.info("\n=== STARTING WORKFLOWS ===")

        async with self.mediator.context() as ctx:
            # Start an order processing workflow
            await ctx.process(
                StartWorkflow(
                    workflow_id="order-001",
                    workflow_type="order_processing",
                    initial_data={"customer_id": "CUST123", "items": ["item1", "item2"]},
                )
            )

            # Start a data processing workflow
            await ctx.process(
                StartWorkflow(
                    workflow_id="data-proc-001",
                    workflow_type="data_processing",
                    initial_data={"source": "database", "table": "users"},
                )
            )

            # Try to start a cyclic workflow (should fail)
            await ctx.process(StartWorkflow(workflow_id="cyclic-001", workflow_type="cyclic_workflow", initial_data={}))

            # Wait a bit for processing
            await asyncio.sleep(3)


# 8. MAIN EXECUTION


async def main():
    import argparse

    configuration = argparse.Namespace()
    configuration.host = "localhost"
    configuration.port = 8082

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    application = WorkflowDemoApplication(configuration=configuration)

    application.attach(WorkflowOrchestrator(application))
    application.attach(OrderValidationProcessor(application))
    application.attach(InventoryProcessor(application))
    application.attach(PaymentProcessor(application))
    application.attach(WorkflowEventListener(application))

    await application.start()


if __name__ == "__main__":
    execute(main())
