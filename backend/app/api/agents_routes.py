"""
API Routes for Custom Agent Framework

Endpoints:
- GET  /api/agents/templates - List agent templates
- POST /api/agents/create - Create custom agent
- POST /api/agents/execute - Execute agent
- GET  /api/agents/plugins - List plugins
- POST /api/agents/test - Test agent
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import logging

from backend.agents import AgentTemplate, AgentExecutor, PluginManager, AgentTester

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])

# Global instances (in production, use dependency injection)
agent_executor = AgentExecutor()
plugin_manager = PluginManager(plugins_dir="plugins")
agent_tester = AgentTester(agent_executor)


class CreateAgentRequest(BaseModel):
    """Request to create custom agent"""
    agent_definition: Dict[str, Any]
    save_as_template: bool = False


class ExecuteAgentRequest(BaseModel):
    """Request to execute agent"""
    agent_name: str
    inputs: Dict[str, Any]
    timeout: Optional[int] = None


class TestAgentRequest(BaseModel):
    """Request to test agent"""
    agent: Dict[str, Any]
    inputs: Dict[str, Any]


@router.get("/templates")
async def list_templates():
    """List all available agent templates"""
    try:
        templates = agent_executor.list_agents()
        return {
            "success": True,
            "templates": templates
        }
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_agent(request: CreateAgentRequest):
    """Create a custom agent from definition"""
    try:
        # Create agent template from definition
        template = AgentTemplate.from_dict(request.agent_definition)

        # Register with executor
        agent_executor.register_template(template)

        # Optionally save as YAML template
        if request.save_as_template:
            from pathlib import Path
            templates_dir = Path("templates/agents")
            templates_dir.mkdir(parents=True, exist_ok=True)
            template.to_yaml(str(templates_dir / f"{template.name}.yaml"))

        return {
            "success": True,
            "agent_name": template.name,
            "message": f"Agent '{template.name}' created successfully"
        }

    except Exception as e:
        logger.error(f"Failed to create agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/execute")
async def execute_agent(request: ExecuteAgentRequest):
    """Execute an agent with inputs"""
    try:
        result = agent_executor.execute(request.agent_name, request.inputs)

        return {
            "success": True,
            "agent_name": request.agent_name,
            "outputs": result
        }

    except Exception as e:
        logger.error(f"Failed to execute agent: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plugins")
async def list_plugins():
    """List all loaded plugins"""
    try:
        plugins = plugin_manager.list_plugins()
        return {
            "success": True,
            "plugins": plugins
        }
    except Exception as e:
        logger.error(f"Failed to list plugins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plugins/reload")
async def reload_plugins():
    """Reload all plugins"""
    try:
        results = plugin_manager.load_all_plugins()
        loaded = sum(1 for success in results.values() if success)

        return {
            "success": True,
            "total_plugins": len(results),
            "loaded_successfully": loaded,
            "results": results
        }
    except Exception as e:
        logger.error(f"Failed to reload plugins: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plugins/execute/{plugin_name}")
async def execute_plugin(plugin_name: str, inputs: Dict[str, Any]):
    """Execute a plugin"""
    try:
        result = plugin_manager.execute_plugin(plugin_name, inputs)

        return {
            "success": True,
            "plugin_name": plugin_name,
            "outputs": result
        }
    except Exception as e:
        logger.error(f"Failed to execute plugin: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/test")
async def test_agent(request: TestAgentRequest):
    """Test an agent with test inputs"""
    try:
        # Create temporary agent
        template = AgentTemplate.from_dict(request.agent)
        agent_executor.register_template(template)

        # Execute with test inputs
        result = agent_executor.execute(template.name, request.inputs)

        return {
            "success": True,
            "agent_name": template.name,
            "test_inputs": request.inputs,
            "outputs": result,
            "message": "Test passed successfully"
        }

    except Exception as e:
        logger.error(f"Agent test failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Test failed"
        }


@router.post("/test/suite/{suite_name}/{agent_name}")
async def run_test_suite(suite_name: str, agent_name: str):
    """Run a test suite for an agent"""
    try:
        results = agent_tester.run_test_suite(suite_name, agent_name)

        passed = sum(1 for r in results if r.passed)
        total = len(results)

        return {
            "success": True,
            "suite_name": suite_name,
            "agent_name": agent_name,
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "results": [
                {
                    "test_name": r.test_name,
                    "passed": r.passed,
                    "error": r.error,
                    "execution_time_ms": r.execution_time_ms
                }
                for r in results
            ]
        }

    except Exception as e:
        logger.error(f"Failed to run test suite: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/test/report")
async def get_test_report():
    """Get comprehensive test report"""
    try:
        report = agent_tester.generate_test_report()
        return {
            "success": True,
            "report": report
        }
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload-plugin")
async def upload_plugin(file: UploadFile = File(...)):
    """Upload a custom plugin file"""
    try:
        from pathlib import Path

        # Save plugin file
        plugins_dir = Path("plugins")
        plugins_dir.mkdir(parents=True, exist_ok=True)

        file_path = plugins_dir / file.filename
        content = await file.read()

        with open(file_path, 'wb') as f:
            f.write(content)

        # Load plugin
        plugin_name = plugin_manager.load_plugin(str(file_path))

        if plugin_name:
            return {
                "success": True,
                "plugin_name": plugin_name,
                "message": f"Plugin '{plugin_name}' uploaded and loaded successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to load plugin"
            }

    except Exception as e:
        logger.error(f"Failed to upload plugin: {e}")
        raise HTTPException(status_code=400, detail=str(e))
