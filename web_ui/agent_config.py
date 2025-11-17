"""
Agent Configuration and CLI Adapter System

Supports multiple AI agent CLIs: Claude Code, OpenAI Codex, Gemini Code, and custom adapters.
"""

import os
import json
import subprocess
import tempfile
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class AgentAdapter(ABC):
    """Base class for AI agent CLI adapters"""

    @abstractmethod
    def invoke(self, prompt: str, tools: Optional[List[Dict]] = None, timeout: int = 120) -> str:
        """
        Invoke the agent CLI with a prompt and optional tools.

        Args:
            prompt: The task prompt
            tools: Optional list of tool schemas
            timeout: Timeout in seconds

        Returns:
            Raw response string from CLI
        """
        pass

    @abstractmethod
    def parse_tool_response(self, response: str) -> Dict[str, Any]:
        """
        Parse tool use from agent response.

        Args:
            response: Raw response from CLI

        Returns:
            Extracted tool input as dict
        """
        pass

    @abstractmethod
    def supports_tools(self) -> bool:
        """Check if this adapter supports tool calling"""
        pass


class ClaudeCodeAdapter(AgentAdapter):
    """Adapter for Claude Code CLI (claude)"""

    def __init__(self, executable: str = "claude"):
        self.executable = executable

    def invoke(self, prompt: str, tools: Optional[List[Dict]] = None, timeout: int = 120) -> str:
        """Invoke Claude Code CLI"""
        cmd = [self.executable, '-p', prompt, '--output-format', 'json']

        # Add tools if provided
        tool_file = None
        if tools:
            tool_file = tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False, encoding='utf-8'
            )
            json.dump(tools, tool_file)
            tool_file.close()
            cmd.extend(['--tools', tool_file.name])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                cwd=str(Path(__file__).parent.parent)
            )

            if result.returncode != 0:
                logger.error(f"Claude Code failed: {result.stderr}")
                raise RuntimeError(f"Agent process failed: {result.stderr}")

            return result.stdout.strip()

        finally:
            # Clean up temp file
            if tool_file:
                try:
                    os.unlink(tool_file.name)
                except:
                    pass

    def parse_tool_response(self, response: str) -> Dict[str, Any]:
        """Parse Claude Code tool use response"""
        response_data = json.loads(response)

        if isinstance(response_data, dict):
            # Look for tool_uses or content blocks
            tool_uses = response_data.get('tool_uses', [])
            if not tool_uses and 'content' in response_data:
                # Try to find tool use in content blocks
                for block in response_data.get('content', []):
                    if isinstance(block, dict) and block.get('type') == 'tool_use':
                        tool_uses.append(block)

            if tool_uses:
                tool_use = tool_uses[0]
                return tool_use.get('input', {})
            else:
                raise RuntimeError("Agent did not call the required tool")
        else:
            raise RuntimeError("Agent returned unexpected format")

    def supports_tools(self) -> bool:
        return True


class OpenAICodexAdapter(AgentAdapter):
    """Adapter for OpenAI Codex CLI (openai or codex)"""

    def __init__(self, executable: str = "openai"):
        self.executable = executable

    def invoke(self, prompt: str, tools: Optional[List[Dict]] = None, timeout: int = 120) -> str:
        """Invoke OpenAI Codex CLI"""
        # OpenAI CLI might use different flags - adjust as needed
        cmd = [self.executable, 'chat', '--model', 'gpt-4', '--json']

        if tools:
            # OpenAI uses function calling
            tool_file = tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False, encoding='utf-8'
            )
            json.dump({'functions': tools}, tool_file)
            tool_file.close()
            cmd.extend(['--functions', tool_file.name])

        # Add prompt as stdin or file
        prompt_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, encoding='utf-8'
        )
        prompt_file.write(prompt)
        prompt_file.close()

        try:
            result = subprocess.run(
                cmd,
                stdin=open(prompt_file.name, 'r'),
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8'
            )

            if result.returncode != 0:
                logger.error(f"OpenAI Codex failed: {result.stderr}")
                raise RuntimeError(f"Agent process failed: {result.stderr}")

            return result.stdout.strip()

        finally:
            try:
                os.unlink(prompt_file.name)
            except:
                pass

    def parse_tool_response(self, response: str) -> Dict[str, Any]:
        """Parse OpenAI function calling response"""
        response_data = json.loads(response)

        # OpenAI format: {"choices": [{"message": {"function_call": {"arguments": "..."}}}]}
        if 'choices' in response_data and len(response_data['choices']) > 0:
            message = response_data['choices'][0].get('message', {})
            function_call = message.get('function_call', {})
            if function_call:
                args_str = function_call.get('arguments', '{}')
                return json.loads(args_str)

        raise RuntimeError("Agent did not call the required function")

    def supports_tools(self) -> bool:
        return True


class GeminiCodeAdapter(AgentAdapter):
    """Adapter for Google Gemini Code CLI (gemini or gcloud)"""

    def __init__(self, executable: str = "gemini"):
        self.executable = executable

    def invoke(self, prompt: str, tools: Optional[List[Dict]] = None, timeout: int = 120) -> str:
        """Invoke Gemini CLI"""
        # Gemini CLI syntax - adjust based on actual CLI
        cmd = [self.executable, 'generate', '--format', 'json']

        if tools:
            tool_file = tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False, encoding='utf-8'
            )
            json.dump({'tools': tools}, tool_file)
            tool_file.close()
            cmd.extend(['--tools', tool_file.name])

        cmd.append(prompt)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8'
            )

            if result.returncode != 0:
                logger.error(f"Gemini failed: {result.stderr}")
                raise RuntimeError(f"Agent process failed: {result.stderr}")

            return result.stdout.strip()

        finally:
            pass

    def parse_tool_response(self, response: str) -> Dict[str, Any]:
        """Parse Gemini tool use response"""
        response_data = json.loads(response)

        # Gemini format - adjust based on actual response format
        if 'functionCall' in response_data:
            return response_data['functionCall'].get('args', {})

        raise RuntimeError("Agent did not call the required tool")

    def supports_tools(self) -> bool:
        return True


class CustomCLIAdapter(AgentAdapter):
    """Adapter for custom CLI tools with configurable command structure"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize custom adapter with configuration.

        Config format:
        {
            "executable": "my-cli",
            "prompt_flag": "-p",
            "tools_flag": "--tools",
            "output_format_flag": "--json",
            "tool_response_path": "content[0].tool_use.input"
        }
        """
        self.config = config
        self.executable = config['executable']

    def invoke(self, prompt: str, tools: Optional[List[Dict]] = None, timeout: int = 120) -> str:
        """Invoke custom CLI"""
        cmd = [self.executable]

        # Add prompt
        if 'prompt_flag' in self.config:
            cmd.extend([self.config['prompt_flag'], prompt])

        # Add output format
        if 'output_format_flag' in self.config:
            cmd.append(self.config['output_format_flag'])

        # Add tools if provided
        tool_file = None
        if tools and 'tools_flag' in self.config:
            tool_file = tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False, encoding='utf-8'
            )
            json.dump(tools, tool_file)
            tool_file.close()
            cmd.extend([self.config['tools_flag'], tool_file.name])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8'
            )

            if result.returncode != 0:
                logger.error(f"Custom CLI failed: {result.stderr}")
                raise RuntimeError(f"Agent process failed: {result.stderr}")

            return result.stdout.strip()

        finally:
            if tool_file:
                try:
                    os.unlink(tool_file.name)
                except:
                    pass

    def parse_tool_response(self, response: str) -> Dict[str, Any]:
        """Parse tool response using configured path"""
        response_data = json.loads(response)

        # Navigate JSON path to extract tool input
        path = self.config.get('tool_response_path', '').split('.')
        current = response_data

        for key in path:
            if '[' in key:
                # Handle array indexing
                name, idx = key.split('[')
                idx = int(idx.rstrip(']'))
                current = current[name][idx]
            else:
                current = current[key]

        return current

    def supports_tools(self) -> bool:
        return 'tools_flag' in self.config


class AgentConfig:
    """Configuration manager for AI agent selection"""

    # Built-in adapter registry
    ADAPTERS = {
        'claude': ClaudeCodeAdapter,
        'claude-code': ClaudeCodeAdapter,
        'openai': OpenAICodexAdapter,
        'codex': OpenAICodexAdapter,
        'gemini': GeminiCodeAdapter,
        'gemini-code': GeminiCodeAdapter,
    }

    def __init__(self):
        """Initialize configuration from environment or defaults"""
        self.current_adapter: Optional[AgentAdapter] = None
        self._load_config()

    def _load_config(self):
        """Load agent configuration from environment or config file"""
        # Check environment variable
        agent_type = os.getenv('AI_AGENT_CLI', '').lower()

        # Check config file
        config_file = Path(__file__).parent / 'agent_config.json'
        if not agent_type and config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    agent_type = config_data.get('agent', '').lower()

                    # Check for custom adapter config
                    if agent_type == 'custom' and 'custom_config' in config_data:
                        self.current_adapter = CustomCLIAdapter(config_data['custom_config'])
                        logger.info(f"Loaded custom agent adapter: {config_data['custom_config']['executable']}")
                        return
            except Exception as e:
                logger.warning(f"Failed to load config file: {e}")

        # Default to Claude Code
        if not agent_type:
            agent_type = 'claude'
            logger.info("No agent configured, defaulting to Claude Code")

        # Create adapter
        if agent_type in self.ADAPTERS:
            self.current_adapter = self.ADAPTERS[agent_type]()
            logger.info(f"Using agent adapter: {agent_type}")
        else:
            logger.warning(f"Unknown agent type '{agent_type}', falling back to Claude Code")
            self.current_adapter = ClaudeCodeAdapter()

    def get_adapter(self) -> AgentAdapter:
        """Get the current agent adapter"""
        if not self.current_adapter:
            self._load_config()
        return self.current_adapter

    def set_adapter(self, agent_type: str, custom_config: Optional[Dict] = None):
        """
        Manually set the agent adapter.

        Args:
            agent_type: Type of agent ('claude', 'openai', 'gemini', 'custom')
            custom_config: Configuration dict for custom adapter
        """
        if agent_type == 'custom' and custom_config:
            self.current_adapter = CustomCLIAdapter(custom_config)
        elif agent_type in self.ADAPTERS:
            self.current_adapter = self.ADAPTERS[agent_type]()
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

        logger.info(f"Agent adapter set to: {agent_type}")

    def save_config(self, agent_type: str, custom_config: Optional[Dict] = None):
        """Save current configuration to file"""
        config_file = Path(__file__).parent / 'agent_config.json'

        config_data = {'agent': agent_type}
        if custom_config:
            config_data['custom_config'] = custom_config

        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

        logger.info(f"Saved agent config to {config_file}")


# Global configuration instance
_config = AgentConfig()


def get_agent_adapter() -> AgentAdapter:
    """Get the current agent adapter (convenience function)"""
    return _config.get_adapter()


def set_agent(agent_type: str, custom_config: Optional[Dict] = None, save: bool = True):
    """
    Set the agent type to use.

    Args:
        agent_type: 'claude', 'openai', 'gemini', or 'custom'
        custom_config: Configuration for custom adapter
        save: Whether to save to config file

    Example:
        set_agent('claude')
        set_agent('custom', {
            'executable': 'my-ai-cli',
            'prompt_flag': '-p',
            'tools_flag': '--tools',
            'output_format_flag': '--json',
            'tool_response_path': 'result.tool_input'
        })
    """
    _config.set_adapter(agent_type, custom_config)
    if save:
        _config.save_config(agent_type, custom_config)
