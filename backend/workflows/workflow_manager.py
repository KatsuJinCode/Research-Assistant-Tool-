"""
Workflow Manager - Lifecycle Management.

Handles workflow lifecycle operations including loading, saving, validation,
history tracking, and scheduling.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import yaml

from .workflow_engine import (
    Workflow,
    WorkflowStep,
    StepType,
    ErrorHandlingStrategy,
    RetryPolicy,
    WorkflowStatus,
)
from .workflow_context import WorkflowContext, WorkflowExecutionState

logger = logging.getLogger(__name__)


class WorkflowValidationError(Exception):
    """Raised when workflow validation fails."""
    pass


class WorkflowManager:
    """
    Manages workflow lifecycle operations.

    Handles loading, saving, validation, and execution history.
    """

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the workflow manager.

        Args:
            storage_dir: Directory for storing workflows and execution history
        """
        self.storage_dir = Path(storage_dir or os.path.join(os.getcwd(), "workflows_data"))
        self.workflows_dir = self.storage_dir / "workflows"
        self.history_dir = self.storage_dir / "history"
        self.templates_dir = self.storage_dir / "templates"

        # Create directories
        self.workflows_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache
        self._workflows: Dict[str, Workflow] = {}
        self._execution_history: Dict[str, List[Dict[str, Any]]] = {}

        logger.info(f"WorkflowManager initialized with storage at {self.storage_dir}")

    def load_workflow(
        self,
        source: Any,
        workflow_id: Optional[str] = None
    ) -> Workflow:
        """
        Load a workflow from YAML file or dictionary.

        Args:
            source: File path (str/Path) or workflow dictionary
            workflow_id: Optional workflow ID (generated if not provided)

        Returns:
            Loaded Workflow object

        Raises:
            ValueError: If source format is invalid
            FileNotFoundError: If file doesn't exist
        """
        # Load workflow definition
        if isinstance(source, (str, Path)):
            # Load from file
            file_path = Path(source)
            if not file_path.exists():
                raise FileNotFoundError(f"Workflow file not found: {file_path}")

            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix in ['.yaml', '.yml']:
                    workflow_dict = yaml.safe_load(f)
                elif file_path.suffix == '.json':
                    workflow_dict = json.load(f)
                else:
                    raise ValueError(f"Unsupported file format: {file_path.suffix}")

            logger.info(f"Loaded workflow from {file_path}")
        elif isinstance(source, dict):
            workflow_dict = source
        else:
            raise ValueError(f"Unsupported source type: {type(source)}")

        # Parse workflow
        workflow = self._parse_workflow_dict(workflow_dict, workflow_id)

        # Validate
        self.validate_workflow(workflow)

        # Cache
        self._workflows[workflow.workflow_id] = workflow

        return workflow

    def _parse_workflow_dict(self, data: Dict[str, Any], workflow_id: Optional[str] = None) -> Workflow:
        """
        Parse workflow dictionary into Workflow object.

        Args:
            data: Workflow definition dictionary
            workflow_id: Optional workflow ID

        Returns:
            Workflow object
        """
        # Parse steps
        steps = []
        for step_data in data.get("steps", []):
            # Parse retry policy
            retry_policy = None
            if "retry_policy" in step_data:
                rp = step_data["retry_policy"]
                retry_policy = RetryPolicy(
                    max_attempts=rp.get("max_attempts", 3),
                    initial_delay=rp.get("initial_delay", 1.0),
                    max_delay=rp.get("max_delay", 60.0),
                    backoff_multiplier=rp.get("backoff_multiplier", 2.0)
                )

            step = WorkflowStep(
                step_id=step_data["step_id"],
                step_type=StepType(step_data["step_type"]),
                name=step_data["name"],
                description=step_data.get("description", ""),
                inputs=step_data.get("inputs", {}),
                outputs=step_data.get("outputs", []),
                conditions=step_data.get("conditions", {}),
                retry_policy=retry_policy,
                timeout=step_data.get("timeout"),
                depends_on=step_data.get("depends_on", [])
            )
            steps.append(step)

        # Parse error handling strategy
        error_handling_str = data.get("error_handling", "stop")
        error_handling = ErrorHandlingStrategy(error_handling_str)

        # Create workflow
        workflow = Workflow(
            workflow_id=workflow_id or data.get("workflow_id") or str(uuid4()),
            name=data["name"],
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            steps=steps,
            variables=data.get("variables", {}),
            triggers=data.get("triggers", {}),
            error_handling=error_handling,
            metadata=data.get("metadata", {})
        )

        return workflow

    def save_workflow(self, workflow: Workflow, path: Optional[str] = None, format: str = "yaml") -> str:
        """
        Save workflow to file.

        Args:
            workflow: Workflow to save
            path: Output file path (if None, uses default location)
            format: Output format ('yaml' or 'json')

        Returns:
            Path where workflow was saved
        """
        if path is None:
            filename = f"{workflow.workflow_id}.{format}"
            path = str(self.workflows_dir / filename)

        # Convert workflow to dictionary
        workflow_dict = self._workflow_to_dict(workflow)

        # Save based on format
        with open(path, 'w', encoding='utf-8') as f:
            if format == "yaml":
                yaml.dump(workflow_dict, f, default_flow_style=False, sort_keys=False)
            elif format == "json":
                json.dump(workflow_dict, f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Saved workflow {workflow.workflow_id} to {path}")
        return path

    def _workflow_to_dict(self, workflow: Workflow) -> Dict[str, Any]:
        """
        Convert Workflow object to dictionary.

        Args:
            workflow: Workflow object

        Returns:
            Dictionary representation
        """
        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "version": workflow.version,
            "steps": [
                {
                    "step_id": step.step_id,
                    "step_type": step.step_type.value,
                    "name": step.name,
                    "description": step.description,
                    "inputs": step.inputs,
                    "outputs": step.outputs,
                    "conditions": step.conditions,
                    "retry_policy": {
                        "max_attempts": step.retry_policy.max_attempts,
                        "initial_delay": step.retry_policy.initial_delay,
                        "max_delay": step.retry_policy.max_delay,
                        "backoff_multiplier": step.retry_policy.backoff_multiplier
                    } if step.retry_policy else None,
                    "timeout": step.timeout,
                    "depends_on": step.depends_on
                }
                for step in workflow.steps
            ],
            "variables": workflow.variables,
            "triggers": workflow.triggers,
            "error_handling": workflow.error_handling.value,
            "metadata": workflow.metadata
        }

    def list_workflows(self, include_templates: bool = True) -> List[Dict[str, Any]]:
        """
        List all available workflows.

        Args:
            include_templates: Whether to include template workflows

        Returns:
            List of workflow metadata
        """
        workflows = []

        # List saved workflows
        for workflow_file in self.workflows_dir.glob("*.yaml"):
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow_dict = yaml.safe_load(f)

                workflows.append({
                    "workflow_id": workflow_dict.get("workflow_id"),
                    "name": workflow_dict.get("name"),
                    "description": workflow_dict.get("description", ""),
                    "version": workflow_dict.get("version", "1.0.0"),
                    "step_count": len(workflow_dict.get("steps", [])),
                    "source": "custom",
                    "file_path": str(workflow_file)
                })
            except Exception as e:
                logger.warning(f"Failed to load workflow {workflow_file}: {e}")

        # List templates
        if include_templates:
            for template_file in self.templates_dir.glob("*.yaml"):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        workflow_dict = yaml.safe_load(f)

                    workflows.append({
                        "workflow_id": workflow_dict.get("workflow_id"),
                        "name": workflow_dict.get("name"),
                        "description": workflow_dict.get("description", ""),
                        "version": workflow_dict.get("version", "1.0.0"),
                        "step_count": len(workflow_dict.get("steps", [])),
                        "source": "template",
                        "file_path": str(template_file)
                    })
                except Exception as e:
                    logger.warning(f"Failed to load template {template_file}: {e}")

        return workflows

    def validate_workflow(self, workflow: Workflow) -> None:
        """
        Validate workflow for correctness.

        Args:
            workflow: Workflow to validate

        Raises:
            WorkflowValidationError: If validation fails
        """
        errors = []

        # Check basic fields
        if not workflow.name:
            errors.append("Workflow name is required")

        if not workflow.steps:
            errors.append("Workflow must have at least one step")

        # Check step IDs are unique
        step_ids = [step.step_id for step in workflow.steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append("Step IDs must be unique")

        # Check dependencies exist
        for step in workflow.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    errors.append(f"Step {step.step_id} depends on non-existent step {dep}")

        # Check for circular dependencies
        try:
            self._check_circular_dependencies(workflow)
        except ValueError as e:
            errors.append(str(e))

        # Check step types are valid
        for step in workflow.steps:
            if not isinstance(step.step_type, StepType):
                errors.append(f"Invalid step type for step {step.step_id}: {step.step_type}")

        if errors:
            raise WorkflowValidationError("Workflow validation failed:\n" + "\n".join(errors))

        logger.info(f"Workflow {workflow.workflow_id} validated successfully")

    def _check_circular_dependencies(self, workflow: Workflow) -> None:
        """
        Check for circular dependencies using DFS.

        Args:
            workflow: Workflow to check

        Raises:
            ValueError: If circular dependency detected
        """
        # Build adjacency list
        graph: Dict[str, List[str]] = {step.step_id: step.depends_on for step in workflow.steps}

        # Track visited nodes
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        # Check each node
        for step_id in graph:
            if step_id not in visited:
                if dfs(step_id):
                    raise ValueError("Circular dependency detected")

    def get_workflow_history(
        self,
        workflow_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get execution history for a workflow.

        Args:
            workflow_id: Workflow ID
            limit: Maximum number of executions to return

        Returns:
            List of execution records (most recent first)
        """
        history_file = self.history_dir / f"{workflow_id}.json"

        if not history_file.exists():
            return []

        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)

            # Sort by timestamp (most recent first)
            history.sort(key=lambda x: x.get("start_time", ""), reverse=True)

            if limit:
                history = history[:limit]

            return history
        except Exception as e:
            logger.error(f"Failed to load workflow history: {e}")
            return []

    def save_execution(self, workflow: Workflow, context: WorkflowContext) -> None:
        """
        Save workflow execution to history.

        Args:
            workflow: Executed workflow
            context: Execution context
        """
        history_file = self.history_dir / f"{workflow.workflow_id}.json"

        # Load existing history
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load existing history: {e}")

        # Add new execution
        execution_record = {
            "execution_id": context.execution_id,
            "workflow_id": workflow.workflow_id,
            "workflow_name": workflow.name,
            "workflow_version": workflow.version,
            "status": context.state.value,
            "start_time": context.start_time.isoformat() if context.start_time else None,
            "end_time": context.end_time.isoformat() if context.end_time else None,
            "duration_seconds": context.get_duration_seconds(),
            "step_count": len(workflow.steps),
            "completed_steps": sum(
                1 for exec in context.step_executions.values()
                if exec.status == "completed"
            ),
            "failed_steps": sum(
                1 for exec in context.step_executions.values()
                if exec.status == "failed"
            ),
            "errors": context.errors,
            "metadata": workflow.metadata
        }

        history.append(execution_record)

        # Keep only last 100 executions
        history = history[-100:]

        # Save
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2)

            logger.info(f"Saved execution {context.execution_id} to history")
        except Exception as e:
            logger.error(f"Failed to save execution history: {e}")

    def delete_workflow(self, workflow_id: str) -> bool:
        """
        Delete a workflow.

        Args:
            workflow_id: Workflow ID to delete

        Returns:
            True if deleted successfully
        """
        workflow_file = self.workflows_dir / f"{workflow_id}.yaml"

        if workflow_file.exists():
            workflow_file.unlink()
            self._workflows.pop(workflow_id, None)
            logger.info(f"Deleted workflow {workflow_id}")
            return True

        return False

    def clone_workflow(
        self,
        workflow_id: str,
        new_name: Optional[str] = None,
        new_id: Optional[str] = None
    ) -> Workflow:
        """
        Clone an existing workflow.

        Args:
            workflow_id: Source workflow ID
            new_name: Name for cloned workflow (defaults to "Copy of {original}")
            new_id: ID for cloned workflow (generated if not provided)

        Returns:
            Cloned workflow

        Raises:
            ValueError: If source workflow not found
        """
        # Load source workflow
        workflow_file = self.workflows_dir / f"{workflow_id}.yaml"
        if not workflow_file.exists():
            raise ValueError(f"Workflow {workflow_id} not found")

        workflow = self.load_workflow(workflow_file)

        # Clone
        cloned = Workflow(
            workflow_id=new_id or str(uuid4()),
            name=new_name or f"Copy of {workflow.name}",
            description=workflow.description,
            version="1.0.0",
            steps=workflow.steps.copy(),
            variables=workflow.variables.copy(),
            triggers=workflow.triggers.copy(),
            error_handling=workflow.error_handling,
            metadata=workflow.metadata.copy()
        )

        # Save
        self.save_workflow(cloned)

        logger.info(f"Cloned workflow {workflow_id} to {cloned.workflow_id}")
        return cloned

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """
        Get a workflow by ID.

        Args:
            workflow_id: Workflow ID

        Returns:
            Workflow object or None if not found
        """
        # Check cache
        if workflow_id in self._workflows:
            return self._workflows[workflow_id]

        # Try to load from file
        workflow_file = self.workflows_dir / f"{workflow_id}.yaml"
        if workflow_file.exists():
            return self.load_workflow(workflow_file, workflow_id)

        # Try templates
        template_file = self.templates_dir / f"{workflow_id}.yaml"
        if template_file.exists():
            return self.load_workflow(template_file, workflow_id)

        return None
