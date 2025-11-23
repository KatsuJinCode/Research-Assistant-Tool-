"""
Workflow Scheduler - Automated Scheduling.

Provides scheduling capabilities for automated workflow execution including
cron-based scheduling, event-based triggers, and resource management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4

# Optional croniter import
try:
    from croniter import croniter
    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False
    croniter = None

from .workflow_engine import Workflow, WorkflowEngine, WorkflowStatus
from .workflow_manager import WorkflowManager

logger = logging.getLogger(__name__)


class ScheduleType:
    """Schedule type constants."""
    CRON = "cron"
    INTERVAL = "interval"
    ONE_TIME = "one_time"
    EVENT = "event"


class TriggerEvent:
    """Event types that can trigger workflows."""
    DOCUMENT_ADDED = "document_added"
    CLAIM_EXTRACTED = "claim_extracted"
    THRESHOLD_MET = "threshold_met"
    CUSTOM = "custom"


class ScheduledWorkflow:
    """Represents a scheduled workflow."""

    def __init__(
        self,
        schedule_id: str,
        workflow_id: str,
        schedule_type: str,
        schedule_config: Dict[str, Any],
        enabled: bool = True,
        max_concurrent: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize scheduled workflow.

        Args:
            schedule_id: Unique schedule identifier
            workflow_id: ID of workflow to execute
            schedule_type: Type of schedule (cron, interval, one_time, event)
            schedule_config: Schedule configuration
            enabled: Whether schedule is enabled
            max_concurrent: Maximum concurrent executions
            metadata: Additional metadata
        """
        self.schedule_id = schedule_id
        self.workflow_id = workflow_id
        self.schedule_type = schedule_type
        self.schedule_config = schedule_config
        self.enabled = enabled
        self.max_concurrent = max_concurrent
        self.metadata = metadata or {}

        # Runtime state
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.execution_count: int = 0
        self.active_executions: Set[str] = set()

    def can_execute(self) -> bool:
        """
        Check if workflow can be executed now.

        Returns:
            True if can execute
        """
        if not self.enabled:
            return False

        if len(self.active_executions) >= self.max_concurrent:
            logger.debug(f"Schedule {self.schedule_id} at max concurrent executions")
            return False

        if self.schedule_type == ScheduleType.CRON:
            if not CRONITER_AVAILABLE:
                logger.warning("croniter not available, skipping cron schedule")
                return False

            cron_expr = self.schedule_config.get("expression")
            if not cron_expr:
                return False

            # Check if it's time to run
            cron = croniter(cron_expr, self.last_run or datetime.now())
            next_time = cron.get_next(datetime)
            self.next_run = next_time

            return datetime.now() >= next_time

        elif self.schedule_type == ScheduleType.INTERVAL:
            interval_seconds = self.schedule_config.get("interval_seconds", 0)
            if interval_seconds <= 0:
                return False

            if self.last_run is None:
                return True

            next_time = self.last_run + timedelta(seconds=interval_seconds)
            self.next_run = next_time

            return datetime.now() >= next_time

        elif self.schedule_type == ScheduleType.ONE_TIME:
            run_at = self.schedule_config.get("run_at")
            if not run_at:
                return False

            if isinstance(run_at, str):
                run_at = datetime.fromisoformat(run_at)

            return datetime.now() >= run_at and self.last_run is None

        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "schedule_id": self.schedule_id,
            "workflow_id": self.workflow_id,
            "schedule_type": self.schedule_type,
            "schedule_config": self.schedule_config,
            "enabled": self.enabled,
            "max_concurrent": self.max_concurrent,
            "metadata": self.metadata,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "execution_count": self.execution_count,
            "active_executions": list(self.active_executions)
        }


class WorkflowScheduler:
    """
    Manages automated workflow scheduling and execution.

    Supports cron expressions, interval-based scheduling, one-time execution,
    and event-based triggers.
    """

    def __init__(
        self,
        workflow_manager: WorkflowManager,
        workflow_engine: WorkflowEngine,
        max_concurrent_workflows: int = 5
    ):
        """
        Initialize the scheduler.

        Args:
            workflow_manager: Workflow manager instance
            workflow_engine: Workflow engine instance
            max_concurrent_workflows: Maximum concurrent workflow executions
        """
        self.workflow_manager = workflow_manager
        self.workflow_engine = workflow_engine
        self.max_concurrent_workflows = max_concurrent_workflows

        self._schedules: Dict[str, ScheduledWorkflow] = {}
        self._event_handlers: Dict[str, List[ScheduledWorkflow]] = {}
        self._running = False
        self._scheduler_task: Optional[asyncio.Task] = None

        logger.info("WorkflowScheduler initialized")

    def schedule_workflow(
        self,
        workflow_id: str,
        schedule_type: str,
        schedule_config: Dict[str, Any],
        schedule_id: Optional[str] = None,
        enabled: bool = True,
        max_concurrent: int = 1,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Schedule a workflow for automated execution.

        Args:
            workflow_id: ID of workflow to schedule
            schedule_type: Type of schedule (cron, interval, one_time, event)
            schedule_config: Schedule configuration
            schedule_id: Optional schedule ID (generated if not provided)
            enabled: Whether schedule is enabled
            max_concurrent: Maximum concurrent executions
            metadata: Additional metadata

        Returns:
            Schedule ID

        Raises:
            ValueError: If schedule configuration is invalid
        """
        # Validate workflow exists
        workflow = self.workflow_manager.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        # Validate schedule config
        self._validate_schedule_config(schedule_type, schedule_config)

        # Create schedule
        schedule_id = schedule_id or str(uuid4())
        scheduled = ScheduledWorkflow(
            schedule_id=schedule_id,
            workflow_id=workflow_id,
            schedule_type=schedule_type,
            schedule_config=schedule_config,
            enabled=enabled,
            max_concurrent=max_concurrent,
            metadata=metadata
        )

        self._schedules[schedule_id] = scheduled

        # Register event handlers if event-based
        if schedule_type == ScheduleType.EVENT:
            event_type = schedule_config.get("event_type")
            if event_type:
                if event_type not in self._event_handlers:
                    self._event_handlers[event_type] = []
                self._event_handlers[event_type].append(scheduled)

        logger.info(f"Scheduled workflow {workflow_id} with schedule {schedule_id} ({schedule_type})")
        return schedule_id

    def _validate_schedule_config(self, schedule_type: str, config: Dict[str, Any]) -> None:
        """
        Validate schedule configuration.

        Args:
            schedule_type: Schedule type
            config: Schedule configuration

        Raises:
            ValueError: If configuration is invalid
        """
        if schedule_type == ScheduleType.CRON:
            if not CRONITER_AVAILABLE:
                raise ValueError("croniter library not installed, cannot use cron schedules")

            cron_expr = config.get("expression")
            if not cron_expr:
                raise ValueError("Cron schedule requires 'expression' in config")

            # Validate cron expression
            try:
                croniter(cron_expr)
            except Exception as e:
                raise ValueError(f"Invalid cron expression: {e}")

        elif schedule_type == ScheduleType.INTERVAL:
            interval = config.get("interval_seconds")
            if not interval or interval <= 0:
                raise ValueError("Interval schedule requires positive 'interval_seconds' in config")

        elif schedule_type == ScheduleType.ONE_TIME:
            run_at = config.get("run_at")
            if not run_at:
                raise ValueError("One-time schedule requires 'run_at' in config")

        elif schedule_type == ScheduleType.EVENT:
            event_type = config.get("event_type")
            if not event_type:
                raise ValueError("Event schedule requires 'event_type' in config")

        else:
            raise ValueError(f"Unknown schedule type: {schedule_type}")

    def unschedule_workflow(self, schedule_id: str) -> bool:
        """
        Remove a scheduled workflow.

        Args:
            schedule_id: Schedule ID to remove

        Returns:
            True if removed successfully
        """
        scheduled = self._schedules.pop(schedule_id, None)
        if not scheduled:
            return False

        # Remove from event handlers
        if scheduled.schedule_type == ScheduleType.EVENT:
            event_type = scheduled.schedule_config.get("event_type")
            if event_type and event_type in self._event_handlers:
                self._event_handlers[event_type] = [
                    s for s in self._event_handlers[event_type]
                    if s.schedule_id != schedule_id
                ]

        logger.info(f"Unscheduled workflow {schedule_id}")
        return True

    def enable_schedule(self, schedule_id: str) -> bool:
        """
        Enable a schedule.

        Args:
            schedule_id: Schedule ID

        Returns:
            True if enabled successfully
        """
        scheduled = self._schedules.get(schedule_id)
        if not scheduled:
            return False

        scheduled.enabled = True
        logger.info(f"Enabled schedule {schedule_id}")
        return True

    def disable_schedule(self, schedule_id: str) -> bool:
        """
        Disable a schedule.

        Args:
            schedule_id: Schedule ID

        Returns:
            True if disabled successfully
        """
        scheduled = self._schedules.get(schedule_id)
        if not scheduled:
            return False

        scheduled.enabled = False
        logger.info(f"Disabled schedule {schedule_id}")
        return True

    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """
        Get schedule information.

        Args:
            schedule_id: Schedule ID

        Returns:
            Schedule information or None
        """
        scheduled = self._schedules.get(schedule_id)
        if not scheduled:
            return None

        return scheduled.to_dict()

    def list_schedules(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all schedules.

        Args:
            workflow_id: Optional filter by workflow ID

        Returns:
            List of schedule information
        """
        schedules = []
        for scheduled in self._schedules.values():
            if workflow_id is None or scheduled.workflow_id == workflow_id:
                schedules.append(scheduled.to_dict())

        return schedules

    async def start(self):
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler already running")
            return

        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduler started")

    async def stop(self):
        """Stop the scheduler."""
        if not self._running:
            return

        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        logger.info("Scheduler stopped")

    async def _scheduler_loop(self):
        """Main scheduler loop."""
        logger.info("Scheduler loop started")

        while self._running:
            try:
                # Check all schedules
                for scheduled in list(self._schedules.values()):
                    if scheduled.can_execute():
                        await self._execute_scheduled_workflow(scheduled)

                # Sleep before next check
                await asyncio.sleep(10)  # Check every 10 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(10)

        logger.info("Scheduler loop stopped")

    async def _execute_scheduled_workflow(self, scheduled: ScheduledWorkflow):
        """
        Execute a scheduled workflow.

        Args:
            scheduled: Scheduled workflow to execute
        """
        # Check global concurrent limit
        total_active = sum(len(s.active_executions) for s in self._schedules.values())
        if total_active >= self.max_concurrent_workflows:
            logger.debug("Max concurrent workflows reached, deferring execution")
            return

        # Load workflow
        workflow = self.workflow_manager.get_workflow(scheduled.workflow_id)
        if not workflow:
            logger.error(f"Workflow {scheduled.workflow_id} not found")
            return

        # Generate execution ID
        execution_id = str(uuid4())
        workflow.execution_id = execution_id

        # Track execution
        scheduled.active_executions.add(execution_id)
        scheduled.last_run = datetime.now()
        scheduled.execution_count += 1

        logger.info(f"Executing scheduled workflow {scheduled.workflow_id} (schedule: {scheduled.schedule_id})")

        try:
            # Execute workflow in background
            asyncio.create_task(
                self._run_workflow_and_cleanup(workflow, scheduled, execution_id)
            )

        except Exception as e:
            logger.error(f"Failed to execute scheduled workflow: {e}")
            scheduled.active_executions.discard(execution_id)

    async def _run_workflow_and_cleanup(
        self,
        workflow: Workflow,
        scheduled: ScheduledWorkflow,
        execution_id: str
    ):
        """
        Run workflow and cleanup after completion.

        Args:
            workflow: Workflow to execute
            scheduled: Schedule information
            execution_id: Execution ID
        """
        try:
            # Get initial inputs from schedule config
            initial_inputs = scheduled.schedule_config.get("inputs", {})

            # Execute workflow
            result = await self.workflow_engine.execute_workflow(workflow, initial_inputs)

            logger.info(f"Scheduled workflow {workflow.workflow_id} completed successfully")

        except Exception as e:
            logger.error(f"Scheduled workflow {workflow.workflow_id} failed: {e}")

        finally:
            # Cleanup
            scheduled.active_executions.discard(execution_id)

    async def trigger_event(self, event_type: str, event_data: Optional[Dict[str, Any]] = None):
        """
        Trigger event-based workflows.

        Args:
            event_type: Type of event
            event_data: Event data to pass to workflows
        """
        handlers = self._event_handlers.get(event_type, [])

        logger.info(f"Event {event_type} triggered, executing {len(handlers)} workflows")

        for scheduled in handlers:
            if not scheduled.enabled:
                continue

            # Load workflow
            workflow = self.workflow_manager.get_workflow(scheduled.workflow_id)
            if not workflow:
                logger.error(f"Workflow {scheduled.workflow_id} not found")
                continue

            # Check conditions
            conditions = scheduled.schedule_config.get("conditions", {})
            if not self._check_event_conditions(event_data or {}, conditions):
                logger.debug(f"Event conditions not met for schedule {scheduled.schedule_id}")
                continue

            # Execute
            execution_id = str(uuid4())
            workflow.execution_id = execution_id

            scheduled.active_executions.add(execution_id)
            scheduled.last_run = datetime.now()
            scheduled.execution_count += 1

            # Merge event data into inputs
            initial_inputs = scheduled.schedule_config.get("inputs", {})
            initial_inputs["event_data"] = event_data

            asyncio.create_task(
                self._run_workflow_and_cleanup(workflow, scheduled, execution_id)
            )

    def _check_event_conditions(
        self,
        event_data: Dict[str, Any],
        conditions: Dict[str, Any]
    ) -> bool:
        """
        Check if event data meets conditions.

        Args:
            event_data: Event data
            conditions: Conditions to check

        Returns:
            True if conditions are met
        """
        for key, expected_value in conditions.items():
            if key not in event_data:
                return False

            actual_value = event_data[key]

            # Support different comparison operators
            if isinstance(expected_value, dict):
                operator = expected_value.get("operator", "==")
                value = expected_value.get("value")

                if operator == "==":
                    if actual_value != value:
                        return False
                elif operator == ">":
                    if actual_value <= value:
                        return False
                elif operator == "<":
                    if actual_value >= value:
                        return False
                elif operator == ">=":
                    if actual_value < value:
                        return False
                elif operator == "<=":
                    if actual_value > value:
                        return False
                elif operator == "!=":
                    if actual_value == value:
                        return False
            else:
                if actual_value != expected_value:
                    return False

        return True
