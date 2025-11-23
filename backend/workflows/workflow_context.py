"""
Workflow Execution Context.

Tracks the runtime state of workflow execution including variables,
step outputs, execution metadata, and error logs.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

logger = logging.getLogger(__name__)


class WorkflowExecutionState(str, Enum):
    """Workflow execution state."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class StepExecution:
    """Tracks execution details for a single step."""
    step_id: str
    step_name: str
    status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    attempt_count: int = 0


@dataclass
class WorkflowContext:
    """
    Execution context for a workflow run.

    Maintains state, variables, outputs, and metadata throughout
    workflow execution.
    """

    workflow_id: str
    execution_id: str
    state: WorkflowExecutionState = WorkflowExecutionState.PENDING
    variables: Dict[str, Any] = field(default_factory=dict)
    initial_inputs: Dict[str, Any] = field(default_factory=dict)
    step_outputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    step_executions: Dict[str, StepExecution] = field(default_factory=dict)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Execution timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    current_step_id: Optional[str] = None

    # Resource tracking
    total_api_calls: int = 0
    total_documents_processed: int = 0
    total_claims_extracted: int = 0

    def set_variable(self, key: str, value: Any):
        """
        Set a workflow-level variable.

        Args:
            key: Variable name
            value: Variable value
        """
        self.variables[key] = value
        logger.debug(f"Set variable {key} = {value}")

    def get_variable(self, key: str, default: Any = None) -> Any:
        """
        Get a workflow-level variable.

        Args:
            key: Variable name
            default: Default value if not found

        Returns:
            Variable value or default
        """
        return self.variables.get(key, default)

    def set_step_output(self, step_id: str, output_key: str, value: Any):
        """
        Store output from a step.

        Args:
            step_id: Step identifier
            output_key: Output key name
            value: Output value
        """
        if step_id not in self.step_outputs:
            self.step_outputs[step_id] = {}

        self.step_outputs[step_id][output_key] = value
        logger.debug(f"Set step output {step_id}.{output_key}")

    def get_step_output(self, step_id: str, output_key: str = None, default: Any = None) -> Any:
        """
        Get output from a step.

        Args:
            step_id: Step identifier
            output_key: Output key name (if None, returns all outputs for step)
            default: Default value if not found

        Returns:
            Output value or default
        """
        if step_id not in self.step_outputs:
            return default

        if output_key is None:
            return self.step_outputs[step_id]

        return self.step_outputs[step_id].get(output_key, default)

    def get_all_step_outputs(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all step outputs.

        Returns:
            Dictionary mapping step_id -> outputs
        """
        return self.step_outputs.copy()

    def start_step(self, step_id: str, step_name: str):
        """
        Mark the start of step execution.

        Args:
            step_id: Step identifier
            step_name: Step name
        """
        self.current_step_id = step_id
        self.step_executions[step_id] = StepExecution(
            step_id=step_id,
            step_name=step_name,
            status="running",
            start_time=datetime.utcnow()
        )
        logger.info(f"Started step: {step_name} ({step_id})")

    def complete_step(self, step_id: str, outputs: Optional[Dict[str, Any]] = None):
        """
        Mark successful step completion.

        Args:
            step_id: Step identifier
            outputs: Step outputs
        """
        if step_id in self.step_executions:
            execution = self.step_executions[step_id]
            execution.status = "completed"
            execution.end_time = datetime.utcnow()

            if execution.start_time:
                duration = (execution.end_time - execution.start_time).total_seconds()
                execution.duration_seconds = duration

            if outputs:
                execution.outputs = outputs
                for key, value in outputs.items():
                    self.set_step_output(step_id, key, value)

            logger.info(f"Completed step: {execution.step_name} ({step_id}) in {execution.duration_seconds:.2f}s")

    def fail_step(self, step_id: str, error: str):
        """
        Mark step as failed.

        Args:
            step_id: Step identifier
            error: Error message
        """
        if step_id in self.step_executions:
            execution = self.step_executions[step_id]
            execution.status = "failed"
            execution.end_time = datetime.utcnow()
            execution.error = error

            if execution.start_time:
                duration = (execution.end_time - execution.start_time).total_seconds()
                execution.duration_seconds = duration

            logger.error(f"Failed step: {execution.step_name} ({step_id}): {error}")

    def add_error(self, step_id: str, error: str, details: Optional[Dict[str, Any]] = None):
        """
        Record an error.

        Args:
            step_id: Step identifier where error occurred
            error: Error message
            details: Additional error details
        """
        error_entry = {
            "step_id": step_id,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        self.errors.append(error_entry)
        logger.error(f"Error in step {step_id}: {error}")

    def get_errors(self) -> List[Dict[str, Any]]:
        """
        Get all recorded errors.

        Returns:
            List of error entries
        """
        return self.errors.copy()

    def get_step_execution(self, step_id: str) -> Optional[StepExecution]:
        """
        Get execution details for a step.

        Args:
            step_id: Step identifier

        Returns:
            Step execution details or None
        """
        return self.step_executions.get(step_id)

    def get_all_step_executions(self) -> Dict[str, StepExecution]:
        """
        Get all step execution details.

        Returns:
            Dictionary mapping step_id -> StepExecution
        """
        return self.step_executions.copy()

    def get_duration_seconds(self) -> Optional[float]:
        """
        Get total workflow execution duration.

        Returns:
            Duration in seconds or None if not completed
        """
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        elif self.start_time:
            return (datetime.utcnow() - self.start_time).total_seconds()
        return None

    def get_progress(self) -> Dict[str, Any]:
        """
        Get workflow execution progress.

        Returns:
            Progress information
        """
        total_steps = len(self.step_executions)
        completed_steps = sum(
            1 for exec in self.step_executions.values()
            if exec.status == "completed"
        )
        failed_steps = sum(
            1 for exec in self.step_executions.values()
            if exec.status == "failed"
        )

        return {
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "failed_steps": failed_steps,
            "current_step": self.current_step_id,
            "progress_percent": (completed_steps / total_steps * 100) if total_steps > 0 else 0,
            "state": self.state.value,
            "duration_seconds": self.get_duration_seconds()
        }

    def get_final_outputs(self) -> Dict[str, Any]:
        """
        Get final workflow outputs.

        Returns:
            Dictionary of final outputs
        """
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "state": self.state.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.get_duration_seconds(),
            "progress": self.get_progress(),
            "step_outputs": self.get_all_step_outputs(),
            "errors": self.get_errors(),
            "variables": self.variables,
            "metadata": self.metadata,
            "resource_usage": {
                "total_api_calls": self.total_api_calls,
                "total_documents_processed": self.total_documents_processed,
                "total_claims_extracted": self.total_claims_extracted
            }
        }

    def increment_api_calls(self, count: int = 1):
        """Increment API call counter."""
        self.total_api_calls += count

    def increment_documents_processed(self, count: int = 1):
        """Increment documents processed counter."""
        self.total_documents_processed += count

    def increment_claims_extracted(self, count: int = 1):
        """Increment claims extracted counter."""
        self.total_claims_extracted += count

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "state": self.state.value,
            "variables": self.variables,
            "initial_inputs": self.initial_inputs,
            "step_outputs": self.step_outputs,
            "step_executions": {
                step_id: {
                    "step_id": exec.step_id,
                    "step_name": exec.step_name,
                    "status": exec.status,
                    "start_time": exec.start_time.isoformat() if exec.start_time else None,
                    "end_time": exec.end_time.isoformat() if exec.end_time else None,
                    "duration_seconds": exec.duration_seconds,
                    "outputs": exec.outputs,
                    "error": exec.error,
                    "attempt_count": exec.attempt_count
                }
                for step_id, exec in self.step_executions.items()
            },
            "errors": self.errors,
            "metadata": self.metadata,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "current_step_id": self.current_step_id,
            "resource_usage": {
                "total_api_calls": self.total_api_calls,
                "total_documents_processed": self.total_documents_processed,
                "total_claims_extracted": self.total_claims_extracted
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowContext":
        """
        Create context from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            WorkflowContext instance
        """
        context = cls(
            workflow_id=data["workflow_id"],
            execution_id=data["execution_id"],
            state=WorkflowExecutionState(data.get("state", "pending")),
            variables=data.get("variables", {}),
            initial_inputs=data.get("initial_inputs", {}),
            step_outputs=data.get("step_outputs", {}),
            errors=data.get("errors", []),
            metadata=data.get("metadata", {}),
            current_step_id=data.get("current_step_id")
        )

        # Restore timestamps
        if data.get("start_time"):
            context.start_time = datetime.fromisoformat(data["start_time"])
        if data.get("end_time"):
            context.end_time = datetime.fromisoformat(data["end_time"])

        # Restore step executions
        for step_id, exec_data in data.get("step_executions", {}).items():
            execution = StepExecution(
                step_id=exec_data["step_id"],
                step_name=exec_data["step_name"],
                status=exec_data["status"],
                outputs=exec_data.get("outputs", {}),
                error=exec_data.get("error"),
                attempt_count=exec_data.get("attempt_count", 0),
                duration_seconds=exec_data.get("duration_seconds")
            )

            if exec_data.get("start_time"):
                execution.start_time = datetime.fromisoformat(exec_data["start_time"])
            if exec_data.get("end_time"):
                execution.end_time = datetime.fromisoformat(exec_data["end_time"])

            context.step_executions[step_id] = execution

        # Restore resource usage
        resource_usage = data.get("resource_usage", {})
        context.total_api_calls = resource_usage.get("total_api_calls", 0)
        context.total_documents_processed = resource_usage.get("total_documents_processed", 0)
        context.total_claims_extracted = resource_usage.get("total_claims_extracted", 0)

        return context
