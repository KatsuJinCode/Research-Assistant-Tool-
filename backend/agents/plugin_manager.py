"""
Plugin System for User-Defined Agents

Allows users to create and load custom agents dynamically.
Features:
- Plugin discovery (scan plugins/ directory)
- Dynamic loading of agent plugins
- Sandboxed execution
- Plugin validation
"""

import os
import sys
import importlib
import importlib.util
import logging
import inspect
from typing import Dict, Any, List, Optional, Type
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod
import traceback

logger = logging.getLogger(__name__)


class AgentPlugin(ABC):
    """
    Base interface for agent plugins.

    Custom plugins must inherit from this class and implement all abstract methods.
    """

    @abstractmethod
    def validate(self) -> bool:
        """
        Validate plugin configuration and dependencies.

        Returns:
            True if plugin is valid and ready to execute
        """
        pass

    @abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent plugin.

        Args:
            inputs: Input data dictionary

        Returns:
            Output data dictionary
        """
        pass

    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get plugin metadata.

        Returns:
            Dictionary with:
                - name: Plugin name
                - version: Plugin version
                - description: Plugin description
                - author: Plugin author
                - inputs: List of input schemas
                - outputs: List of output schemas
        """
        pass


@dataclass
class PluginMetadata:
    """Plugin metadata"""
    name: str
    version: str
    description: str
    author: str
    file_path: str
    class_name: str
    inputs: List[Dict[str, Any]]
    outputs: List[Dict[str, Any]]
    validated: bool = False
    error: Optional[str] = None


class PluginManager:
    """
    Manages loading, validation, and execution of agent plugins.

    Features:
    - Auto-discovery of plugins in specified directory
    - Dynamic loading with error handling
    - Plugin validation before execution
    - Sandboxed execution (basic - could be enhanced with RestrictedPython)
    """

    def __init__(self, plugins_dir: str = "plugins", enable_sandbox: bool = False):
        """
        Initialize plugin manager.

        Args:
            plugins_dir: Directory to scan for plugins
            enable_sandbox: Enable sandboxed execution (requires RestrictedPython)
        """
        self.plugins_dir = Path(plugins_dir)
        self.plugins_dir.mkdir(parents=True, exist_ok=True)

        self.enable_sandbox = enable_sandbox
        self.plugins: Dict[str, AgentPlugin] = {}
        self.metadata: Dict[str, PluginMetadata] = {}

    def discover_plugins(self) -> List[str]:
        """
        Discover all plugin files in plugins directory.

        Returns:
            List of plugin file paths
        """
        plugin_files = []

        # Scan for Python files
        for file_path in self.plugins_dir.glob("**/*.py"):
            if file_path.name.startswith("_"):
                continue  # Skip private files

            plugin_files.append(str(file_path))

        logger.info(f"Discovered {len(plugin_files)} plugin files")
        return plugin_files

    def load_plugin(self, plugin_path: str) -> Optional[str]:
        """
        Load a single plugin from file.

        Args:
            plugin_path: Path to plugin Python file

        Returns:
            Plugin name if successful, None if failed
        """
        try:
            # Load module
            spec = importlib.util.spec_from_file_location(
                f"plugin_{Path(plugin_path).stem}",
                plugin_path
            )
            if not spec or not spec.loader:
                raise ImportError(f"Failed to load spec for {plugin_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)

            # Find AgentPlugin subclass
            plugin_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, AgentPlugin) and obj is not AgentPlugin:
                    plugin_class = obj
                    break

            if not plugin_class:
                raise ValueError("No AgentPlugin subclass found in module")

            # Instantiate plugin
            plugin_instance = plugin_class()

            # Validate plugin
            if not plugin_instance.validate():
                raise ValueError("Plugin validation failed")

            # Get metadata
            metadata_dict = plugin_instance.get_metadata()

            # Create metadata
            metadata = PluginMetadata(
                name=metadata_dict['name'],
                version=metadata_dict['version'],
                description=metadata_dict['description'],
                author=metadata_dict.get('author', 'Unknown'),
                file_path=plugin_path,
                class_name=plugin_class.__name__,
                inputs=metadata_dict.get('inputs', []),
                outputs=metadata_dict.get('outputs', []),
                validated=True
            )

            # Register plugin
            self.plugins[metadata.name] = plugin_instance
            self.metadata[metadata.name] = metadata

            logger.info(f"Loaded plugin: {metadata.name} v{metadata.version}")
            return metadata.name

        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_path}: {e}")
            logger.debug(traceback.format_exc())

            # Store error metadata
            error_metadata = PluginMetadata(
                name=Path(plugin_path).stem,
                version="unknown",
                description="Failed to load",
                author="unknown",
                file_path=plugin_path,
                class_name="unknown",
                inputs=[],
                outputs=[],
                validated=False,
                error=str(e)
            )
            self.metadata[error_metadata.name] = error_metadata

            return None

    def load_all_plugins(self) -> Dict[str, bool]:
        """
        Load all discovered plugins.

        Returns:
            Dictionary mapping plugin names to load success status
        """
        plugin_files = self.discover_plugins()
        results = {}

        for plugin_path in plugin_files:
            plugin_name = self.load_plugin(plugin_path)
            results[plugin_path] = plugin_name is not None

        logger.info(
            f"Loaded {sum(results.values())}/{len(results)} plugins successfully"
        )
        return results

    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Reload a plugin (useful for development).

        Args:
            plugin_name: Name of plugin to reload

        Returns:
            True if successful
        """
        if plugin_name not in self.metadata:
            logger.error(f"Plugin {plugin_name} not found")
            return False

        plugin_path = self.metadata[plugin_name].file_path

        # Unload existing
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
        if plugin_name in self.metadata:
            del self.metadata[plugin_name]

        # Reload
        return self.load_plugin(plugin_path) is not None

    def execute_plugin(
        self,
        plugin_name: str,
        inputs: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a plugin with inputs.

        Args:
            plugin_name: Name of plugin to execute
            inputs: Input data
            timeout: Optional execution timeout in seconds

        Returns:
            Output data from plugin
        """
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin '{plugin_name}' not found")

        plugin = self.plugins[plugin_name]

        # Validate inputs against schema
        metadata = self.metadata[plugin_name]
        self._validate_inputs(inputs, metadata.inputs)

        # Execute
        try:
            if self.enable_sandbox:
                # Sandboxed execution (requires RestrictedPython)
                return self._execute_sandboxed(plugin, inputs, timeout)
            else:
                # Direct execution
                if timeout:
                    # Simple timeout using signals (Unix) or threading (Windows)
                    import signal
                    import platform

                    if platform.system() != 'Windows':
                        def timeout_handler(signum, frame):
                            raise TimeoutError("Plugin execution timed out")

                        signal.signal(signal.SIGALRM, timeout_handler)
                        signal.alarm(timeout)

                    try:
                        result = plugin.execute(inputs)
                        if platform.system() != 'Windows':
                            signal.alarm(0)  # Cancel alarm
                        return result
                    except TimeoutError:
                        logger.error(f"Plugin {plugin_name} timed out after {timeout}s")
                        raise
                else:
                    return plugin.execute(inputs)

        except Exception as e:
            logger.error(f"Plugin execution failed: {e}")
            logger.debug(traceback.format_exc())
            raise

    def _validate_inputs(
        self,
        inputs: Dict[str, Any],
        input_schemas: List[Dict[str, Any]]
    ):
        """Validate inputs against schema"""
        required_inputs = {
            schema['name'] for schema in input_schemas
            if schema.get('required', True)
        }

        provided_inputs = set(inputs.keys())

        missing = required_inputs - provided_inputs
        if missing:
            raise ValueError(f"Missing required inputs: {missing}")

    def _execute_sandboxed(
        self,
        plugin: AgentPlugin,
        inputs: Dict[str, Any],
        timeout: Optional[int]
    ) -> Dict[str, Any]:
        """
        Execute plugin in sandbox.

        Note: This is a placeholder. Full sandboxing requires RestrictedPython
        or running in a separate process/container.
        """
        # TODO: Implement proper sandboxing with RestrictedPython
        # For now, just execute directly
        logger.warning("Sandbox mode not fully implemented, executing directly")
        return plugin.execute(inputs)

    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List all loaded plugins.

        Returns:
            List of plugin metadata dictionaries
        """
        return [
            {
                'name': metadata.name,
                'version': metadata.version,
                'description': metadata.description,
                'author': metadata.author,
                'validated': metadata.validated,
                'error': metadata.error,
                'inputs': metadata.inputs,
                'outputs': metadata.outputs
            }
            for metadata in self.metadata.values()
        ]

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed info about a plugin"""
        if plugin_name not in self.metadata:
            return None

        metadata = self.metadata[plugin_name]
        return {
            'name': metadata.name,
            'version': metadata.version,
            'description': metadata.description,
            'author': metadata.author,
            'file_path': metadata.file_path,
            'class_name': metadata.class_name,
            'inputs': metadata.inputs,
            'outputs': metadata.outputs,
            'validated': metadata.validated,
            'error': metadata.error
        }

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        if plugin_name in self.plugins:
            del self.plugins[plugin_name]
        if plugin_name in self.metadata:
            del self.metadata[plugin_name]
        return True


def create_example_plugin(output_path: str):
    """Create an example plugin file"""
    example_code = '''"""
Example Agent Plugin

This is a simple example of a custom agent plugin.
"""

from backend.agents.plugin_manager import AgentPlugin
from typing import Dict, Any


class ExampleSentimentAnalyzer(AgentPlugin):
    """Example plugin that performs sentiment analysis"""

    def validate(self) -> bool:
        """Validate plugin is ready"""
        # Check dependencies, config, etc.
        return True

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sentiment analysis"""
        text = inputs.get('text', '')

        # Simple keyword-based sentiment
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'poor']

        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        if positive_count > negative_count:
            sentiment = 'positive'
            score = 0.6 + (positive_count * 0.1)
        elif negative_count > positive_count:
            sentiment = 'negative'
            score = 0.4 - (negative_count * 0.1)
        else:
            sentiment = 'neutral'
            score = 0.5

        return {
            'sentiment': sentiment,
            'score': max(0.0, min(1.0, score)),
            'positive_count': positive_count,
            'negative_count': negative_count
        }

    def get_metadata(self) -> Dict[str, Any]:
        """Get plugin metadata"""
        return {
            'name': 'sentiment_analyzer',
            'version': '1.0.0',
            'description': 'Simple keyword-based sentiment analysis',
            'author': 'Research Assistant Team',
            'inputs': [
                {
                    'name': 'text',
                    'type': 'string',
                    'description': 'Text to analyze',
                    'required': True
                }
            ],
            'outputs': [
                {
                    'name': 'sentiment',
                    'type': 'string',
                    'description': 'Sentiment: positive/negative/neutral'
                },
                {
                    'name': 'score',
                    'type': 'number',
                    'description': 'Confidence score 0.0-1.0'
                }
            ]
        }
'''

    with open(output_path, 'w') as f:
        f.write(example_code)

    logger.info(f"Created example plugin: {output_path}")
