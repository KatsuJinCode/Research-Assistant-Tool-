"""
Workflow API Routes for Flask Application.

Provides REST API endpoints for workflow management and execution.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from flask import jsonify, request
from typing import Dict, Any

# Import workflow engine components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.workflows import (
    WorkflowEngine,
    WorkflowManager,
    WorkflowScheduler,
    WorkflowContext,
)

logger = logging.getLogger(__name__)

# Initialize workflow components
WORKFLOWS_DIR = Path(__file__).parent.parent / "backend" / "workflows"
workflow_manager = WorkflowManager(storage_dir=str(WORKFLOWS_DIR.parent / "workflows_data"))
workflow_engine = WorkflowEngine()
workflow_scheduler = WorkflowScheduler(workflow_manager, workflow_engine)

# Track active workflow executions
active_executions: Dict[str, Dict[str, Any]] = {}


def register_workflow_routes(app, socketio=None):
    """
    Register workflow routes with Flask app.

    Args:
        app: Flask application instance
        socketio: Optional SocketIO instance for real-time updates
    """

    @app.route('/api/workflows', methods=['GET'])
    def list_workflows():
        """List all available workflows."""
        try:
            include_templates = request.args.get('include_templates', 'true').lower() == 'true'
            workflows = workflow_manager.list_workflows(include_templates=include_templates)

            return jsonify({
                'success': True,
                'workflows': workflows,
                'count': len(workflows)
            })
        except Exception as e:
            logger.error(f"Error listing workflows: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/workflow/<workflow_id>', methods=['GET'])
    def get_workflow(workflow_id):
        """Get workflow details."""
        try:
            workflow = workflow_manager.get_workflow(workflow_id)

            if not workflow:
                return jsonify({'success': False, 'error': 'Workflow not found'}), 404

            workflow_dict = workflow_manager._workflow_to_dict(workflow)

            return jsonify({
                'success': True,
                'workflow': workflow_dict
            })
        except Exception as e:
            logger.error(f"Error getting workflow {workflow_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/workflow/create', methods=['POST'])
    def create_workflow():
        """Create a new workflow."""
        try:
            data = request.json
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400

            # Load workflow from dict
            workflow = workflow_manager.load_workflow(data)

            # Save workflow
            workflow_manager.save_workflow(workflow)

            return jsonify({
                'success': True,
                'workflow_id': workflow.workflow_id,
                'message': 'Workflow created successfully'
            })
        except Exception as e:
            logger.error(f"Error creating workflow: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/workflow/<workflow_id>/execute', methods=['POST'])
    def execute_workflow(workflow_id):
        """Execute a workflow."""
        try:
            data = request.json or {}
            initial_inputs = data.get('inputs', {})

            # Load workflow
            workflow = workflow_manager.get_workflow(workflow_id)
            if not workflow:
                return jsonify({'success': False, 'error': 'Workflow not found'}), 404

            # Execute in background
            execution_id = _execute_workflow_async(workflow, initial_inputs, socketio)

            return jsonify({
                'success': True,
                'execution_id': execution_id,
                'message': 'Workflow execution started'
            })
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/workflow/<execution_id>/status', methods=['GET'])
    def get_workflow_status(execution_id):
        """Get workflow execution status."""
        try:
            # Check active executions
            if execution_id in active_executions:
                status = active_executions[execution_id]
                return jsonify({
                    'success': True,
                    'status': status
                })

            # Check engine
            status = workflow_engine.get_workflow_status(execution_id)
            if status:
                return jsonify({
                    'success': True,
                    'status': status
                })

            return jsonify({'success': False, 'error': 'Execution not found'}), 404

        except Exception as e:
            logger.error(f"Error getting workflow status {execution_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/workflow/<execution_id>/pause', methods=['POST'])
    def pause_workflow(execution_id):
        """Pause a running workflow."""
        try:
            success = workflow_engine.pause_workflow(execution_id)

            if success:
                return jsonify({
                    'success': True,
                    'message': 'Workflow paused'
                })
            else:
                return jsonify({'success': False, 'error': 'Workflow not found or cannot be paused'}), 404

        except Exception as e:
            logger.error(f"Error pausing workflow {execution_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/workflow/<execution_id>/resume', methods=['POST'])
    def resume_workflow(execution_id):
        """Resume a paused workflow."""
        try:
            success = workflow_engine.resume_workflow(execution_id)

            if success:
                return jsonify({
                    'success': True,
                    'message': 'Workflow resumed'
                })
            else:
                return jsonify({'success': False, 'error': 'Workflow not found or cannot be resumed'}), 404

        except Exception as e:
            logger.error(f"Error resuming workflow {execution_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/workflow/<execution_id>/cancel', methods=['POST'])
    def cancel_workflow(execution_id):
        """Cancel a running workflow."""
        try:
            success = workflow_engine.cancel_workflow(execution_id)

            if success:
                # Remove from active executions
                active_executions.pop(execution_id, None)

                return jsonify({
                    'success': True,
                    'message': 'Workflow cancelled'
                })
            else:
                return jsonify({'success': False, 'error': 'Workflow not found or cannot be cancelled'}), 404

        except Exception as e:
            logger.error(f"Error cancelling workflow {execution_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/workflow/<workflow_id>/history', methods=['GET'])
    def get_workflow_history(workflow_id):
        """Get workflow execution history."""
        try:
            limit = request.args.get('limit', type=int, default=10)
            history = workflow_manager.get_workflow_history(workflow_id, limit=limit)

            return jsonify({
                'success': True,
                'history': history,
                'count': len(history)
            })
        except Exception as e:
            logger.error(f"Error getting workflow history {workflow_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/workflow/upload', methods=['POST'])
    def upload_workflow():
        """Upload a workflow YAML file."""
        try:
            if 'file' not in request.files:
                return jsonify({'success': False, 'error': 'No file provided'}), 400

            file = request.files['file']
            if file.filename == '':
                return jsonify({'success': False, 'error': 'No file selected'}), 400

            # Save temporarily
            temp_path = Path(app.config['UPLOAD_FOLDER']) / file.filename
            file.save(str(temp_path))

            try:
                # Load and validate workflow
                workflow = workflow_manager.load_workflow(str(temp_path))

                # Save to workflows directory
                workflow_manager.save_workflow(workflow)

                return jsonify({
                    'success': True,
                    'workflow_id': workflow.workflow_id,
                    'message': 'Workflow uploaded successfully'
                })
            finally:
                # Clean up temp file
                if temp_path.exists():
                    temp_path.unlink()

        except Exception as e:
            logger.error(f"Error uploading workflow: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/workflow/<workflow_id>/clone', methods=['POST'])
    def clone_workflow(workflow_id):
        """Clone an existing workflow."""
        try:
            data = request.json or {}
            new_name = data.get('name')

            cloned = workflow_manager.clone_workflow(workflow_id, new_name=new_name)

            return jsonify({
                'success': True,
                'workflow_id': cloned.workflow_id,
                'message': 'Workflow cloned successfully'
            })
        except Exception as e:
            logger.error(f"Error cloning workflow {workflow_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/workflow/<workflow_id>/delete', methods=['DELETE'])
    def delete_workflow(workflow_id):
        """Delete a workflow."""
        try:
            success = workflow_manager.delete_workflow(workflow_id)

            if success:
                return jsonify({
                    'success': True,
                    'message': 'Workflow deleted successfully'
                })
            else:
                return jsonify({'success': False, 'error': 'Workflow not found'}), 404

        except Exception as e:
            logger.error(f"Error deleting workflow {workflow_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    # Scheduler endpoints

    @app.route('/api/workflow/<workflow_id>/schedule', methods=['POST'])
    def schedule_workflow(workflow_id):
        """Schedule a workflow for automated execution."""
        try:
            data = request.json
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400

            schedule_type = data.get('schedule_type')
            schedule_config = data.get('schedule_config', {})
            enabled = data.get('enabled', True)
            max_concurrent = data.get('max_concurrent', 1)

            schedule_id = workflow_scheduler.schedule_workflow(
                workflow_id=workflow_id,
                schedule_type=schedule_type,
                schedule_config=schedule_config,
                enabled=enabled,
                max_concurrent=max_concurrent
            )

            return jsonify({
                'success': True,
                'schedule_id': schedule_id,
                'message': 'Workflow scheduled successfully'
            })
        except Exception as e:
            logger.error(f"Error scheduling workflow {workflow_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/schedules', methods=['GET'])
    def list_schedules():
        """List all schedules."""
        try:
            workflow_id = request.args.get('workflow_id')
            schedules = workflow_scheduler.list_schedules(workflow_id=workflow_id)

            return jsonify({
                'success': True,
                'schedules': schedules,
                'count': len(schedules)
            })
        except Exception as e:
            logger.error(f"Error listing schedules: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/schedule/<schedule_id>', methods=['DELETE'])
    def unschedule_workflow(schedule_id):
        """Remove a scheduled workflow."""
        try:
            success = workflow_scheduler.unschedule_workflow(schedule_id)

            if success:
                return jsonify({
                    'success': True,
                    'message': 'Schedule removed successfully'
                })
            else:
                return jsonify({'success': False, 'error': 'Schedule not found'}), 404

        except Exception as e:
            logger.error(f"Error unscheduling {schedule_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    logger.info("Workflow routes registered successfully")


def _execute_workflow_async(workflow, initial_inputs, socketio=None):
    """
    Execute workflow asynchronously in background.

    Args:
        workflow: Workflow to execute
        initial_inputs: Initial input values
        socketio: Optional SocketIO instance

    Returns:
        Execution ID
    """
    import threading

    # Generate execution ID
    from uuid import uuid4
    execution_id = str(uuid4())
    workflow.execution_id = execution_id

    # Track execution
    active_executions[execution_id] = {
        'execution_id': execution_id,
        'workflow_id': workflow.workflow_id,
        'workflow_name': workflow.name,
        'status': 'starting',
        'start_time': datetime.utcnow().isoformat(),
        'progress': 0
    }

    def run_workflow():
        """Run workflow in thread."""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Execute workflow
            result = loop.run_until_complete(
                workflow_engine.execute_workflow(workflow, initial_inputs)
            )

            # Update tracking
            active_executions[execution_id].update({
                'status': 'completed',
                'end_time': datetime.utcnow().isoformat(),
                'result': result
            })

            # Emit completion event
            if socketio:
                socketio.emit('workflow_completed', {
                    'execution_id': execution_id,
                    'workflow_id': workflow.workflow_id,
                    'status': 'completed'
                })

            # Save execution to history
            context = WorkflowContext(
                workflow_id=workflow.workflow_id,
                execution_id=execution_id
            )
            context.start_time = datetime.fromisoformat(active_executions[execution_id]['start_time'])
            context.end_time = datetime.utcnow()
            context.state = 'completed'

            workflow_manager.save_execution(workflow, context)

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")

            # Update tracking
            active_executions[execution_id].update({
                'status': 'failed',
                'end_time': datetime.utcnow().isoformat(),
                'error': str(e)
            })

            # Emit failure event
            if socketio:
                socketio.emit('workflow_failed', {
                    'execution_id': execution_id,
                    'workflow_id': workflow.workflow_id,
                    'error': str(e)
                })
        finally:
            loop.close()

    # Start background thread
    thread = threading.Thread(target=run_workflow, daemon=True)
    thread.start()

    return execution_id


# Start scheduler on module import
import threading

def start_scheduler():
    """Start the workflow scheduler."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(workflow_scheduler.start())

scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
scheduler_thread.start()
logger.info("Workflow scheduler started")
