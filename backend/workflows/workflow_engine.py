"""
Core Workflow Execution Engine.

Provides the fundamental engine for executing multi-step research workflows
with dependency resolution, error handling, and async execution support.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


class StepType(str, Enum):
    """Supported workflow step types."""
    SEARCH = "search"
    EXTRACT = "extract"
    ANALYZE = "analyze"
    FILTER = "filter"
    SYNTHESIZE = "synthesize"
    EXPORT = "export"
    CUSTOM = "custom"
    PARALLEL = "parallel"
    LOOP = "loop"
    CONDITION = "condition"


class StepStatus(str, Enum):
    """Step execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorHandlingStrategy(str, Enum):
    """Error handling strategies for workflows."""
    CONTINUE = "continue"  # Continue to next steps
    STOP = "stop"  # Stop entire workflow
    RETRY = "retry"  # Retry failed step


@dataclass
class RetryPolicy:
    """Retry policy for workflow steps."""
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    backoff_multiplier: float = 2.0
    retry_on_exceptions: List[type] = field(default_factory=lambda: [Exception])


@dataclass
class WorkflowStep:
    """
    Represents a single step in a workflow.

    Attributes:
        step_id: Unique identifier for the step
        step_type: Type of step (search, extract, etc.)
        name: Human-readable step name
        description: Detailed description of what the step does
        inputs: Input parameters for the step
        outputs: Expected output keys
        conditions: Conditions that must be met for step to execute
        retry_policy: Retry configuration
        timeout: Maximum execution time in seconds
        depends_on: List of step_ids that must complete first
        handler: Custom function to execute (for CUSTOM step type)
    """
    step_id: str
    step_type: StepType
    name: str
    description: str = ""
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    retry_policy: Optional[RetryPolicy] = None
    timeout: Optional[float] = None  # seconds
    depends_on: List[str] = field(default_factory=list)
    handler: Optional[Callable] = None

    # Runtime state (populated during execution)
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error: Optional[str] = None
    attempt_count: int = 0


@dataclass
class Workflow:
    """
    Represents a complete workflow definition.

    Attributes:
        workflow_id: Unique identifier
        name: Workflow name
        description: Workflow description
        version: Version string
        steps: List of workflow steps
        variables: Workflow-level variables accessible to all steps
        triggers: Trigger configuration (manual, scheduled, event-based)
        error_handling: Error handling strategy
        metadata: Additional metadata
    """
    workflow_id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    steps: List[WorkflowStep] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    triggers: Dict[str, Any] = field(default_factory=dict)
    error_handling: ErrorHandlingStrategy = ErrorHandlingStrategy.STOP
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Runtime state
    status: WorkflowStatus = WorkflowStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_step: Optional[str] = None
    execution_id: Optional[str] = None


class WorkflowEngine:
    """
    Core workflow execution engine.

    Handles workflow execution, dependency resolution, error handling,
    and state management.
    """

    def __init__(self):
        """Initialize the workflow engine."""
        self._executing_workflows: Dict[str, Workflow] = {}
        self._step_handlers: Dict[StepType, Callable] = {}
        self._register_default_handlers()
        self._paused_workflows: Set[str] = set()
        self._cancelled_workflows: Set[str] = set()

    def register_step_handler(self, step_type: StepType, handler: Callable):
        """
        Register a handler function for a step type.

        Args:
            step_type: The step type to handle
            handler: Async function that executes the step
        """
        self._step_handlers[step_type] = handler
        logger.info(f"Registered handler for step type: {step_type}")

    def _register_default_handlers(self):
        """Register default handlers for built-in step types."""
        # These will be implemented based on existing system capabilities
        self._step_handlers[StepType.SEARCH] = self._handle_search_step
        self._step_handlers[StepType.EXTRACT] = self._handle_extract_step
        self._step_handlers[StepType.ANALYZE] = self._handle_analyze_step
        self._step_handlers[StepType.FILTER] = self._handle_filter_step
        self._step_handlers[StepType.SYNTHESIZE] = self._handle_synthesize_step
        self._step_handlers[StepType.EXPORT] = self._handle_export_step
        self._step_handlers[StepType.CUSTOM] = self._handle_custom_step
        self._step_handlers[StepType.PARALLEL] = self._handle_parallel_step
        self._step_handlers[StepType.LOOP] = self._handle_loop_step
        self._step_handlers[StepType.CONDITION] = self._handle_condition_step

    async def execute_workflow(
        self,
        workflow: Workflow,
        initial_inputs: Optional[Dict[str, Any]] = None,
        context: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a complete workflow.

        Args:
            workflow: The workflow to execute
            initial_inputs: Initial input values
            context: Workflow execution context

        Returns:
            Final workflow outputs

        Raises:
            ValueError: If workflow has circular dependencies
            RuntimeError: If workflow execution fails
        """
        from .workflow_context import WorkflowContext, WorkflowExecutionState

        # Generate execution ID
        if not workflow.execution_id:
            workflow.execution_id = str(uuid4())

        # Track executing workflow
        self._executing_workflows[workflow.execution_id] = workflow

        # Initialize context
        if context is None:
            context = WorkflowContext(
                workflow_id=workflow.workflow_id,
                execution_id=workflow.execution_id,
                variables=workflow.variables.copy(),
                initial_inputs=initial_inputs or {}
            )

        try:
            # Resolve dependencies
            execution_order = self.resolve_dependencies(workflow)

            # Update workflow status
            workflow.status = WorkflowStatus.RUNNING
            workflow.start_time = datetime.utcnow()
            context.state = WorkflowExecutionState.RUNNING
            context.start_time = workflow.start_time

            logger.info(f"Starting workflow execution: {workflow.name} (ID: {workflow.execution_id})")

            # Execute steps in order
            for step_id in execution_order:
                # Check for pause/cancel
                if workflow.execution_id in self._cancelled_workflows:
                    workflow.status = WorkflowStatus.CANCELLED
                    context.state = WorkflowExecutionState.CANCELLED
                    logger.info(f"Workflow {workflow.execution_id} cancelled")
                    break

                if workflow.execution_id in self._paused_workflows:
                    workflow.status = WorkflowStatus.PAUSED
                    context.state = WorkflowExecutionState.PAUSED
                    logger.info(f"Workflow {workflow.execution_id} paused")
                    # Wait until resumed
                    while workflow.execution_id in self._paused_workflows:
                        await asyncio.sleep(0.5)
                    workflow.status = WorkflowStatus.RUNNING
                    context.state = WorkflowExecutionState.RUNNING
                    logger.info(f"Workflow {workflow.execution_id} resumed")

                step = next(s for s in workflow.steps if s.step_id == step_id)
                workflow.current_step = step_id
                context.current_step_id = step_id

                # Check conditions
                if not self._check_conditions(step, context):
                    step.status = StepStatus.SKIPPED
                    logger.info(f"Step {step_id} skipped (conditions not met)")
                    continue

                # Execute step
                try:
                    await self.execute_step(step, context)
                except Exception as e:
                    logger.error(f"Step {step_id} failed: {str(e)}")
                    context.add_error(step_id, str(e))
                    step.error = str(e)

                    # Handle error based on strategy
                    if workflow.error_handling == ErrorHandlingStrategy.STOP:
                        raise
                    elif workflow.error_handling == ErrorHandlingStrategy.CONTINUE:
                        continue
                    # RETRY is handled within execute_step

            # Check final status
            if workflow.status != WorkflowStatus.CANCELLED:
                workflow.status = WorkflowStatus.COMPLETED
                context.state = WorkflowExecutionState.COMPLETED

            workflow.end_time = datetime.utcnow()
            context.end_time = workflow.end_time

            logger.info(f"Workflow {workflow.execution_id} finished with status: {workflow.status}")

            return context.get_final_outputs()

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.end_time = datetime.utcnow()
            context.state = WorkflowExecutionState.FAILED
            context.end_time = workflow.end_time
            logger.error(f"Workflow {workflow.execution_id} failed: {str(e)}")
            raise RuntimeError(f"Workflow execution failed: {str(e)}") from e
        finally:
            # Cleanup
            self._executing_workflows.pop(workflow.execution_id, None)
            self._paused_workflows.discard(workflow.execution_id)
            self._cancelled_workflows.discard(workflow.execution_id)

    async def execute_step(self, step: WorkflowStep, context: Any) -> Any:
        """
        Execute a single workflow step.

        Args:
            step: The step to execute
            context: Workflow execution context

        Returns:
            Step output

        Raises:
            RuntimeError: If step execution fails after retries
        """
        retry_policy = step.retry_policy or RetryPolicy()

        step.status = StepStatus.RUNNING
        step.start_time = datetime.utcnow()

        logger.info(f"Executing step: {step.name} (ID: {step.step_id})")

        for attempt in range(retry_policy.max_attempts):
            step.attempt_count = attempt + 1

            try:
                # Get handler
                handler = step.handler or self._step_handlers.get(step.step_type)
                if not handler:
                    raise ValueError(f"No handler registered for step type: {step.step_type}")

                # Resolve inputs from context
                resolved_inputs = self._resolve_inputs(step.inputs, context)

                # Execute with timeout
                if step.timeout:
                    result = await asyncio.wait_for(
                        handler(step, resolved_inputs, context),
                        timeout=step.timeout
                    )
                else:
                    result = await handler(step, resolved_inputs, context)

                # Store outputs
                if step.outputs and isinstance(result, dict):
                    for output_key in step.outputs:
                        if output_key in result:
                            context.set_step_output(step.step_id, output_key, result[output_key])
                else:
                    context.set_step_output(step.step_id, "result", result)

                step.status = StepStatus.COMPLETED
                step.end_time = datetime.utcnow()

                logger.info(f"Step {step.step_id} completed successfully")
                return result

            except asyncio.TimeoutError:
                error_msg = f"Step {step.step_id} timed out after {step.timeout}s"
                logger.warning(error_msg)
                step.error = error_msg

                if attempt < retry_policy.max_attempts - 1:
                    delay = min(
                        retry_policy.initial_delay * (retry_policy.backoff_multiplier ** attempt),
                        retry_policy.max_delay
                    )
                    logger.info(f"Retrying step {step.step_id} in {delay}s (attempt {attempt + 2}/{retry_policy.max_attempts})")
                    await asyncio.sleep(delay)
                else:
                    step.status = StepStatus.FAILED
                    step.end_time = datetime.utcnow()
                    raise RuntimeError(error_msg)

            except Exception as e:
                error_msg = f"Step {step.step_id} failed: {str(e)}"
                logger.error(error_msg)
                step.error = error_msg

                # Check if should retry
                should_retry = any(
                    isinstance(e, exc_type)
                    for exc_type in retry_policy.retry_on_exceptions
                )

                if should_retry and attempt < retry_policy.max_attempts - 1:
                    delay = min(
                        retry_policy.initial_delay * (retry_policy.backoff_multiplier ** attempt),
                        retry_policy.max_delay
                    )
                    logger.info(f"Retrying step {step.step_id} in {delay}s (attempt {attempt + 2}/{retry_policy.max_attempts})")
                    await asyncio.sleep(delay)
                else:
                    step.status = StepStatus.FAILED
                    step.end_time = datetime.utcnow()
                    raise

    def resolve_dependencies(self, workflow: Workflow) -> List[str]:
        """
        Resolve step dependencies using topological sort.

        Args:
            workflow: The workflow to analyze

        Returns:
            Ordered list of step IDs

        Raises:
            ValueError: If circular dependencies detected
        """
        # Build dependency graph
        graph: Dict[str, Set[str]] = {}
        in_degree: Dict[str, int] = {}

        for step in workflow.steps:
            graph[step.step_id] = set(step.depends_on)
            in_degree[step.step_id] = len(step.depends_on)

        # Topological sort (Kahn's algorithm)
        queue = [step_id for step_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            step_id = queue.pop(0)
            result.append(step_id)

            # Find steps that depend on this one
            for other_step in workflow.steps:
                if step_id in graph.get(other_step.step_id, set()):
                    in_degree[other_step.step_id] -= 1
                    if in_degree[other_step.step_id] == 0:
                        queue.append(other_step.step_id)

        # Check for cycles
        if len(result) != len(workflow.steps):
            raise ValueError("Circular dependency detected in workflow")

        return result

    def _check_conditions(self, step: WorkflowStep, context: Any) -> bool:
        """
        Check if step conditions are met.

        Args:
            step: The step to check
            context: Workflow execution context

        Returns:
            True if conditions are met
        """
        if not step.conditions:
            return True

        # Evaluate conditions
        for key, expected_value in step.conditions.items():
            # Check if variable exists in context
            actual_value = context.variables.get(key)

            if actual_value != expected_value:
                return False

        return True

    def _resolve_inputs(self, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """
        Resolve input values from context variables and step outputs.

        Args:
            inputs: Input specification
            context: Workflow execution context

        Returns:
            Resolved input values
        """
        resolved = {}

        for key, value in inputs.items():
            # Check if value is a reference to context variable or step output
            if isinstance(value, str) and value.startswith("$"):
                # Format: $variable_name or $step_id.output_key
                ref = value[1:]  # Remove $

                if "." in ref:
                    # Step output reference
                    step_id, output_key = ref.split(".", 1)
                    resolved[key] = context.get_step_output(step_id, output_key)
                else:
                    # Variable reference
                    resolved[key] = context.variables.get(ref, value)
            else:
                resolved[key] = value

        return resolved

    def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a workflow execution.

        Args:
            execution_id: Workflow execution ID

        Returns:
            Status information or None if not found
        """
        workflow = self._executing_workflows.get(execution_id)
        if not workflow:
            return None

        return {
            "execution_id": execution_id,
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "status": workflow.status.value,
            "current_step": workflow.current_step,
            "start_time": workflow.start_time.isoformat() if workflow.start_time else None,
            "end_time": workflow.end_time.isoformat() if workflow.end_time else None,
            "steps": [
                {
                    "step_id": step.step_id,
                    "name": step.name,
                    "status": step.status.value,
                    "error": step.error
                }
                for step in workflow.steps
            ]
        }

    def pause_workflow(self, execution_id: str) -> bool:
        """
        Pause a running workflow.

        Args:
            execution_id: Workflow execution ID

        Returns:
            True if paused successfully
        """
        if execution_id in self._executing_workflows:
            self._paused_workflows.add(execution_id)
            logger.info(f"Paused workflow: {execution_id}")
            return True
        return False

    def resume_workflow(self, execution_id: str) -> bool:
        """
        Resume a paused workflow.

        Args:
            execution_id: Workflow execution ID

        Returns:
            True if resumed successfully
        """
        if execution_id in self._paused_workflows:
            self._paused_workflows.remove(execution_id)
            logger.info(f"Resumed workflow: {execution_id}")
            return True
        return False

    def cancel_workflow(self, execution_id: str) -> bool:
        """
        Cancel a running workflow.

        Args:
            execution_id: Workflow execution ID

        Returns:
            True if cancelled successfully
        """
        if execution_id in self._executing_workflows:
            self._cancelled_workflows.add(execution_id)
            logger.info(f"Cancelled workflow: {execution_id}")
            return True
        return False

    # Default step handlers (to be implemented based on existing system capabilities)

    async def _handle_search_step(self, step: WorkflowStep, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle search step - search for papers."""
        logger.info(f"Search step: {step.name}")
        # TODO: Integrate with existing search functionality
        # For now, return mock data
        query = inputs.get("query", "")
        max_results = inputs.get("max_results", 10)

        return {
            "results": [],
            "query": query,
            "count": 0
        }

    async def _handle_extract_step(self, step: WorkflowStep, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle extract step - extract claims from documents."""
        logger.info(f"Extract step: {step.name}")
        # TODO: Integrate with existing extraction functionality
        documents = inputs.get("documents", [])

        return {
            "claims": [],
            "document_count": len(documents)
        }

    async def _handle_analyze_step(self, step: WorkflowStep, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle analyze step - run analysis on claims/evidence."""
        logger.info(f"Analyze step: {step.name}")
        # TODO: Integrate with existing analysis functionality
        data = inputs.get("data", [])

        return {
            "analysis_results": {},
            "processed_count": len(data)
        }

    async def _handle_filter_step(self, step: WorkflowStep, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle filter step - filter results by criteria."""
        logger.info(f"Filter step: {step.name}")
        items = inputs.get("items", [])
        criteria = inputs.get("criteria", {})

        # Simple filtering logic
        filtered = [item for item in items if self._matches_criteria(item, criteria)]

        return {
            "filtered_items": filtered,
            "original_count": len(items),
            "filtered_count": len(filtered)
        }

    async def _handle_synthesize_step(self, step: WorkflowStep, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle synthesize step - synthesize findings."""
        logger.info(f"Synthesize step: {step.name}")
        # TODO: Integrate with existing synthesis functionality
        findings = inputs.get("findings", [])

        return {
            "synthesis": "",
            "findings_count": len(findings)
        }

    async def _handle_export_step(self, step: WorkflowStep, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle export step - export results."""
        logger.info(f"Export step: {step.name}")
        # TODO: Integrate with existing export functionality
        data = inputs.get("data", {})
        format_type = inputs.get("format", "json")
        output_path = inputs.get("output_path", "")

        return {
            "exported": True,
            "format": format_type,
            "path": output_path
        }

    async def _handle_custom_step(self, step: WorkflowStep, inputs: Dict[str, Any], context: Any) -> Any:
        """Handle custom step - execute custom function."""
        logger.info(f"Custom step: {step.name}")
        if not step.handler:
            raise ValueError(f"Custom step {step.step_id} requires a handler function")

        return await step.handler(inputs, context)

    async def _handle_parallel_step(self, step: WorkflowStep, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle parallel step - execute multiple steps in parallel."""
        logger.info(f"Parallel step: {step.name}")
        parallel_steps = inputs.get("steps", [])

        # Execute all steps in parallel
        tasks = [self.execute_step(s, context) for s in parallel_steps]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "results": results,
            "step_count": len(parallel_steps)
        }

    async def _handle_loop_step(self, step: WorkflowStep, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle loop step - iterate over items."""
        logger.info(f"Loop step: {step.name}")
        items = inputs.get("items", [])
        loop_step = inputs.get("step")

        results = []
        for item in items:
            # Create a copy of the loop step with item as input
            loop_inputs = {"item": item}
            result = await self.execute_step(loop_step, context)
            results.append(result)

        return {
            "results": results,
            "iteration_count": len(items)
        }

    async def _handle_condition_step(self, step: WorkflowStep, inputs: Dict[str, Any], context: Any) -> Dict[str, Any]:
        """Handle condition step - conditional branching."""
        logger.info(f"Condition step: {step.name}")
        condition = inputs.get("condition", False)
        true_step = inputs.get("true_step")
        false_step = inputs.get("false_step")

        if condition:
            if true_step:
                result = await self.execute_step(true_step, context)
                return {"branch": "true", "result": result}
        else:
            if false_step:
                result = await self.execute_step(false_step, context)
                return {"branch": "false", "result": result}

        return {"branch": "true" if condition else "false", "result": None}

    def _matches_criteria(self, item: Any, criteria: Dict[str, Any]) -> bool:
        """Check if item matches filter criteria."""
        if not isinstance(item, dict):
            return False

        for key, expected in criteria.items():
            if key not in item:
                return False
            if item[key] != expected:
                return False

        return True
