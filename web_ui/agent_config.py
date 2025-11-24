"""
Agent Configuration and Adapter System

Supports multiple AI agent modes:
- SDK Mode (Direct API): Full features, streaming, tool use (Claude, OpenAI, Gemini SDKs)
- CLI Mode (Subprocess): Reduced features, uses external CLI tools

In development: Prefers SDK mode for full features
In production: Falls back to CLI mode if SDK unavailable
"""

import os
import json
import subprocess
import tempfile
import logging
from typing import Dict, Any, List, Optional, Iterator
from pathlib import Path
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Try importing SDK libraries
try:
    from anthropic import Anthropic
    ANTHROPIC_SDK_AVAILABLE = True
except ImportError:
    ANTHROPIC_SDK_AVAILABLE = False
    logger.warning("Anthropic SDK not available - Claude will use CLI mode (reduced features)")

try:
    import openai
    OPENAI_SDK_AVAILABLE = True
except ImportError:
    OPENAI_SDK_AVAILABLE = False
    logger.warning("OpenAI SDK not available - will use CLI mode if needed")


class AgentAdapter(ABC):
    """Base class for AI agent adapters (SDK and CLI modes)"""

    @abstractmethod
    def invoke(self, prompt: str, tools: Optional[List[Dict]] = None, timeout: int = 120) -> str:
        """
        Invoke the agent with a prompt and optional tools.

        Args:
            prompt: The task prompt
            tools: Optional list of tool schemas
            timeout: Timeout in seconds

        Returns:
            Raw response string
        """
        pass

    @abstractmethod
    def parse_tool_response(self, response: str) -> Dict[str, Any]:
        """
        Parse tool use from agent response.

        Args:
            response: Raw response

        Returns:
            Extracted tool input as dict
        """
        pass

    @abstractmethod
    def supports_tools(self) -> bool:
        """Check if this adapter supports tool calling"""
        pass

    @abstractmethod
    def is_sdk_mode(self) -> bool:
        """Check if this adapter uses SDK (True) or CLI (False)"""
        pass

    def get_mode_info(self) -> Dict[str, Any]:
        """
        Get information about the adapter mode.

        Returns:
            Dict with mode, features, limitations
        """
        is_sdk = self.is_sdk_mode()
        return {
            'mode': 'sdk' if is_sdk else 'cli',
            'features': {
                'streaming': is_sdk,
                'tool_use': self.supports_tools(),
                'full_api_control': is_sdk,
                'lower_latency': is_sdk
            },
            'limitations': [] if is_sdk else [
                'No streaming responses',
                'Higher latency (subprocess overhead)',
                'Limited API parameter control',
                'Requires external CLI tool installed'
            ]
        }


class ClaudeCodeAdapter(AgentAdapter):
    """Adapter for Claude Code CLI (claude)"""

    def __init__(self, executable: str = "claude"):
        self.executable = executable

    def invoke(self, prompt: str, tools: Optional[List[Dict]] = None, timeout: int = 120) -> str:
        """Invoke Claude Code CLI"""
        cmd = [self.executable, '-p', prompt, '--output-format', 'json']

        # Add tools if provided
        tool_file_path = None
        if tools:
            # Create temp file with explicit close and write
            fd, tool_file_path = tempfile.mkstemp(suffix='.json', text=True)
            try:
                # Write JSON to file and close file descriptor
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    json.dump(tools, f, ensure_ascii=False, indent=2)
                    f.flush()
                    os.fsync(f.fileno())
            except:
                os.close(fd)
                raise

            cmd.extend(['--tools', tool_file_path])

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
            if tool_file_path:
                try:
                    os.unlink(tool_file_path)
                except:
                    pass

    def parse_tool_response(self, response: str) -> Dict[str, Any]:
        """
        Parse Claude Code tool use response.

        NOTE: This method is deprecated since Claude Code CLI doesn't support
        the --tools flag. Use prompt-based JSON output instead.
        See document_processor._invoke_agent_with_structured_output()
        """
        raise NotImplementedError(
            "Claude Code CLI does not support tool calling. "
            "Use prompt-based JSON output via _invoke_agent_with_structured_output() instead."
        )

    def supports_tools(self) -> bool:
        return True

    def is_sdk_mode(self) -> bool:
        return False  # CLI mode


class ClaudeSDKAdapter(AgentAdapter):
    """Adapter for Claude API via Anthropic SDK (direct API calls using login credentials)"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize Claude SDK adapter.

        Args:
            api_key: Anthropic API key (optional - uses login credentials if not provided)
            model: Claude model to use
        """
        if not ANTHROPIC_SDK_AVAILABLE:
            raise RuntimeError("Anthropic SDK not installed. Run: pip install anthropic")

        self.model = model

        # Try API key first (env var or parameter), then fall back to login credentials
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')

        if self.api_key:
            # Use API key if available
            self.client = Anthropic(api_key=self.api_key)
            logger.info(f"🚀 Claude SDK adapter initialized with API key (model: {model})")
        else:
            # Use login credentials (Agent SDK default)
            try:
                self.client = Anthropic()  # Uses ~/.anthropic credentials
                logger.info(f"🚀 Claude SDK adapter initialized with login credentials (model: {model})")
            except Exception as e:
                raise ValueError(f"Claude SDK initialization failed. Please run 'claude login' or set ANTHROPIC_API_KEY. Error: {str(e)}")

        # Test authentication immediately to fail fast and allow fallback to CLI
        try:
            # Make a minimal test call to verify auth works
            test_response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[{"role": "user", "content": "test"}]
            )
            logger.info("✓ Claude SDK authentication verified")
        except Exception as e:
            error_msg = f"Claude SDK authentication failed: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)

    def invoke(self, prompt: str, tools: Optional[List[Dict]] = None, timeout: int = 120) -> str:
        """Invoke Claude via SDK"""
        try:
            messages = [{"role": "user", "content": prompt}]

            kwargs = {
                "model": self.model,
                "max_tokens": 4096,
                "messages": messages
            }

            if tools:
                kwargs["tools"] = tools

            response = self.client.messages.create(**kwargs)

            # Robust content extraction with detailed error checking
            if not response:
                raise RuntimeError("Claude API returned None response")

            if not hasattr(response, 'content'):
                raise RuntimeError(f"Claude API response has no content attribute. Response: {response}")

            if not response.content:
                logger.warning("Claude API returned empty content")
                return ""

            if not isinstance(response.content, list):
                raise RuntimeError(f"Claude API content is not a list: {type(response.content)}")

            if len(response.content) == 0:
                logger.warning("Claude API returned empty content list")
                return ""

            # Extract first content block
            content_block = response.content[0]
            if content_block is None:
                raise RuntimeError("Claude API first content block is None")

            # Try to get text attribute
            if hasattr(content_block, 'text'):
                return content_block.text
            elif hasattr(content_block, 'content'):
                return str(content_block.content)
            else:
                return str(content_block)

        except Exception as e:
            logger.error(f"Claude SDK error: {str(e)}", exc_info=True)
            raise RuntimeError(f"Claude API call failed: {str(e)}")

    def parse_tool_response(self, response: str) -> Dict[str, Any]:
        """Parse tool use from Claude response"""
        try:
            # Claude SDK returns structured response
            import json
            return json.loads(response)
        except:
            raise RuntimeError("Failed to parse tool response")

    def supports_tools(self) -> bool:
        return True

    def is_sdk_mode(self) -> bool:
        return True  # SDK mode


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

    def is_sdk_mode(self) -> bool:
        return False  # CLI mode


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

    def is_sdk_mode(self) -> bool:
        return False  # CLI mode


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

    def is_sdk_mode(self) -> bool:
        return False  # CLI mode


class AgentConfig:
    """Configuration manager for AI agent selection"""

    # Built-in adapter registry (CLI adapters)
    CLI_ADAPTERS = {
        'claude': ClaudeCodeAdapter,
        'claude-code': ClaudeCodeAdapter,
        'openai': OpenAICodexAdapter,
        'codex': OpenAICodexAdapter,
        'gemini': GeminiCodeAdapter,
        'gemini-code': GeminiCodeAdapter,
    }

    # SDK adapter registry
    SDK_ADAPTERS = {
        'claude': ClaudeSDKAdapter,
        'claude-sdk': ClaudeSDKAdapter,
        # OpenAI SDK adapter can be added here later
        # 'openai': OpenAISDKAdapter,
    }

    def __init__(self):
        """Initialize configuration from environment or defaults"""
        self.current_adapter: Optional[AgentAdapter] = None
        self.is_dev_mode = self._detect_dev_mode()
        self._load_config()

    def _detect_dev_mode(self) -> bool:
        """Detect if running in development mode"""
        # Check environment variable
        flask_env = os.getenv('FLASK_ENV', '').lower()
        if flask_env in ['development', 'dev']:
            return True

        # Check debug flag
        debug_mode = os.getenv('DEBUG', '').lower()
        if debug_mode in ['1', 'true', 'yes']:
            return True

        return False

    def _load_config(self):
        """Load agent configuration with SDK/CLI auto-detection"""
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

        # Default to Claude
        if not agent_type:
            agent_type = 'claude'

        # Try SDK mode first (in development, if SDK available)
        if self.is_dev_mode and agent_type in self.SDK_ADAPTERS:
            try:
                self.current_adapter = self.SDK_ADAPTERS[agent_type]()
                logger.info(f"🚀 Using {agent_type} SDK adapter (full features)")
                return
            except Exception as e:
                logger.warning(f"SDK adapter failed ({str(e)}), falling back to CLI mode")

        # Fall back to CLI adapter
        if agent_type in self.CLI_ADAPTERS:
            self.current_adapter = self.CLI_ADAPTERS[agent_type]()
            logger.info(f"Using {agent_type} CLI adapter (reduced features)")
        else:
            logger.warning(f"Unknown agent type '{agent_type}', falling back to Claude CLI")
            self.current_adapter = ClaudeCodeAdapter()

    def get_adapter(self) -> AgentAdapter:
        """Get the current agent adapter"""
        if not self.current_adapter:
            self._load_config()
        return self.current_adapter

    def get_mode_info(self) -> Dict[str, Any]:
        """
        Get information about the current adapter mode.

        Returns:
            Dict with mode, adapter_type, features, limitations
        """
        adapter = self.get_adapter()
        mode_info = adapter.get_mode_info()

        # Add adapter type
        adapter_class = adapter.__class__.__name__
        if 'Claude' in adapter_class:
            adapter_type = 'Claude'
        elif 'OpenAI' in adapter_class:
            adapter_type = 'OpenAI'
        elif 'Gemini' in adapter_class:
            adapter_type = 'Gemini'
        else:
            adapter_type = 'Custom'

        mode_info['adapter_type'] = adapter_type
        mode_info['is_dev_mode'] = self.is_dev_mode

        return mode_info

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
