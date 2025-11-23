"""
Development Debugging Agent - Log Monitor

Monitors application logs in real-time, detects errors, and provides
intelligent debugging assistance through the chat interface.

Only active in development mode.
"""

import os
import re
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Callable
from datetime import datetime
from queue import Queue, Empty
from threading import Thread
import traceback

logger = logging.getLogger(__name__)


class LogMonitor:
    """
    Real-time log monitoring for debugging assistance.

    Watches log files, detects errors, and generates debugging suggestions.
    """

    def __init__(self, log_dir: str = "logs", callback: Optional[Callable] = None):
        self.log_dir = Path(log_dir)
        self.callback = callback  # Callback to send debug messages
        self.is_running = False
        self.error_queue = Queue()
        self.monitor_thread = None

        # Error patterns to detect
        self.error_patterns = {
            'exception': re.compile(r'(Exception|Error):\s*(.+)'),
            'traceback': re.compile(r'Traceback \(most recent call last\):'),
            'failed': re.compile(r'(failed|failure|error):', re.IGNORECASE),
            'warning': re.compile(r'WARNING:\s*(.+)'),
            'critical': re.compile(r'CRITICAL:\s*(.+)')
        }

        # Known issues and solutions
        self.known_issues = {
            'ModuleNotFoundError': {
                'explanation': 'A required Python package is not installed',
                'solution': 'Install the missing package with: pip install <package-name>',
                'severity': 'high'
            },
            'ConnectionRefusedError': {
                'explanation': 'Cannot connect to database (Neo4j or Redis)',
                'solution': 'Ensure Neo4j and Redis are running. Check connection settings.',
                'severity': 'critical'
            },
            'FileNotFoundError': {
                'explanation': 'A required file is missing',
                'solution': 'Check the file path and ensure the file exists',
                'severity': 'medium'
            },
            'PermissionError': {
                'explanation': 'Insufficient permissions to access file or directory',
                'solution': 'Check file permissions or run with appropriate privileges',
                'severity': 'medium'
            },
            'JSONDecodeError': {
                'explanation': 'Invalid JSON data encountered',
                'solution': 'Check JSON syntax in config files or API responses',
                'severity': 'medium'
            },
            'KeyError': {
                'explanation': 'Required dictionary key is missing',
                'solution': 'Check that all required fields are present in the data',
                'severity': 'low'
            },
            'ValueError': {
                'explanation': 'Invalid value or data type',
                'solution': 'Check input validation and data conversion',
                'severity': 'low'
            }
        }

    def start(self):
        """Start monitoring logs"""
        if self.is_running:
            logger.warning("Log monitor already running")
            return

        self.is_running = True
        self.monitor_thread = Thread(target=self._monitor_logs, daemon=True)
        self.monitor_thread.start()
        logger.info("🐛 Debugging agent started - monitoring logs")

    def stop(self):
        """Stop monitoring logs"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("🐛 Debugging agent stopped")

    def _monitor_logs(self):
        """Monitor log files for errors"""
        log_file = self.log_dir / "research_assistant.log"
        error_log = self.log_dir / "research_assistant_errors.log"

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Track last position in log files
        positions = {
            log_file: 0,
            error_log: 0
        }

        while self.is_running:
            try:
                for log_path in [log_file, error_log]:
                    if not log_path.exists():
                        continue

                    # Read new log entries
                    with open(log_path, 'r', encoding='utf-8') as f:
                        f.seek(positions[log_path])
                        new_lines = f.readlines()
                        positions[log_path] = f.tell()

                    # Process new log entries
                    if new_lines:
                        self._process_log_entries(new_lines, str(log_path))

                # Brief sleep to avoid CPU spinning
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Error in log monitor: {str(e)}")
                time.sleep(1)

    def _process_log_entries(self, lines: List[str], log_file: str):
        """Process new log entries and detect errors"""
        current_error = None
        traceback_lines = []

        for line in lines:
            # Check for traceback start
            if self.error_patterns['traceback'].search(line):
                current_error = {
                    'type': 'exception',
                    'traceback': [line],
                    'timestamp': datetime.now(),
                    'log_file': log_file
                }
                traceback_lines = [line]
                continue

            # Collect traceback lines
            if current_error and (line.startswith(' ') or line.startswith('File')):
                traceback_lines.append(line)
                current_error['traceback'].append(line)
                continue

            # Check for exception line (end of traceback)
            exception_match = self.error_patterns['exception'].search(line)
            if exception_match and current_error:
                current_error['exception_type'] = exception_match.group(1)
                current_error['message'] = exception_match.group(2).strip()
                current_error['traceback'].append(line)

                # Analyze and send error
                self._analyze_error(current_error)
                current_error = None
                traceback_lines = []
                continue

            # Check for other error patterns
            for pattern_name, pattern in self.error_patterns.items():
                if pattern_name in ['exception', 'traceback']:
                    continue

                match = pattern.search(line)
                if match:
                    error = {
                        'type': pattern_name,
                        'message': match.group(1) if match.groups() else line,
                        'timestamp': datetime.now(),
                        'log_file': log_file,
                        'severity': 'medium' if pattern_name == 'warning' else 'high'
                    }
                    self._analyze_error(error)

    def _analyze_error(self, error: Dict):
        """Analyze error and generate debugging message"""
        try:
            # Extract error type
            error_type = error.get('exception_type', error.get('type', 'Unknown'))
            message = error.get('message', '')

            # Look for known issue
            known_issue = None
            for issue_type, info in self.known_issues.items():
                if issue_type in error_type or issue_type in message:
                    known_issue = info
                    break

            # Generate debugging message
            debug_message = self._generate_debug_message(error, known_issue)

            # Send to callback (WebSocket)
            if self.callback:
                self.callback(debug_message)

            # Also log it
            logger.info(f"🐛 Debugging assistant: {debug_message['title']}")

        except Exception as e:
            logger.error(f"Error analyzing error: {str(e)}")

    def _generate_debug_message(self, error: Dict, known_issue: Optional[Dict]) -> Dict:
        """Generate user-friendly debugging message"""
        error_type = error.get('exception_type', error.get('type', 'Error'))
        message = error.get('message', 'Unknown error')
        timestamp = error.get('timestamp', datetime.now())

        debug_msg = {
            'type': 'debug_alert',
            'timestamp': timestamp.isoformat(),
            'severity': known_issue.get('severity', 'medium') if known_issue else 'medium',
            'title': f"🐛 Detected: {error_type}",
            'error_message': message,
            'file': error.get('log_file', 'unknown')
        }

        # Add explanation and solution if known
        if known_issue:
            debug_msg['explanation'] = known_issue['explanation']
            debug_msg['solution'] = known_issue['solution']
        else:
            # Generate generic help
            debug_msg['explanation'] = f"An error occurred: {message}"
            debug_msg['solution'] = "Check the logs for more details and review the stack trace."

        # Add traceback if available
        if 'traceback' in error:
            debug_msg['traceback'] = ''.join(error['traceback'])

            # Extract file and line number
            file_match = re.search(r'File "([^"]+)", line (\d+)', debug_msg['traceback'])
            if file_match:
                debug_msg['error_file'] = file_match.group(1)
                debug_msg['error_line'] = file_match.group(2)

        # Add suggestions
        debug_msg['suggestions'] = self._generate_suggestions(error_type, message)

        return debug_msg

    def _generate_suggestions(self, error_type: str, message: str) -> List[str]:
        """Generate helpful suggestions based on error"""
        suggestions = []

        # Import errors
        if 'ModuleNotFound' in error_type or 'ImportError' in error_type:
            module_match = re.search(r"No module named '([^']+)'", message)
            if module_match:
                module = module_match.group(1)
                suggestions.append(f"Install missing module: pip install {module}")
            suggestions.append("Check requirements.txt is up to date")
            suggestions.append("Verify virtual environment is activated")

        # Connection errors
        elif 'Connection' in error_type or 'connection' in message.lower():
            suggestions.append("Check if Neo4j is running (should be at bolt://localhost:7687)")
            suggestions.append("Check if Redis is running (should be at localhost:6379)")
            suggestions.append("Verify database credentials in configuration")

        # File errors
        elif 'FileNotFound' in error_type:
            suggestions.append("Verify the file path is correct")
            suggestions.append("Check if file was moved or deleted")
            suggestions.append("Ensure file permissions are correct")

        # Permission errors
        elif 'Permission' in error_type:
            suggestions.append("Check file/directory permissions")
            suggestions.append("Try running with appropriate privileges")
            suggestions.append("Verify user has access to the resource")

        # JSON errors
        elif 'JSON' in error_type:
            suggestions.append("Check JSON syntax in configuration files")
            suggestions.append("Verify API response format")
            suggestions.append("Use a JSON validator to check formatting")

        # Generic suggestions
        if not suggestions:
            suggestions.append("Review the error message and stack trace")
            suggestions.append("Check recent code changes")
            suggestions.append("Search for similar errors in documentation")

        return suggestions


class DebugAgent:
    """
    Main debugging agent that coordinates log monitoring and user interaction.
    """

    def __init__(self, socketio=None):
        self.socketio = socketio
        self.log_monitor = None
        self.is_enabled = False
        self.is_dev_mode = self._detect_dev_mode()

    def _detect_dev_mode(self) -> bool:
        """Detect if we're in development mode"""
        # Check environment variable
        flask_env = os.getenv('FLASK_ENV', '').lower()
        if flask_env in ['development', 'dev']:
            return True

        # Check if running with --debug flag
        # This is a heuristic - not perfect
        import sys
        if '--debug' in sys.argv or '--reload' in sys.argv:
            return True

        # Check config file for debug flag
        # (You can add a config.py check here)

        return False

    def enable(self):
        """Enable debugging agent"""
        if self.is_enabled:
            return

        self.is_enabled = True

        # Start log monitor
        self.log_monitor = LogMonitor(callback=self._send_debug_message)
        self.log_monitor.start()

        logger.info("🐛 Debugging agent enabled")

        # Notify user via WebSocket
        if self.socketio:
            self.socketio.emit('debug_status', {
                'enabled': True,
                'message': '🐛 Debugging assistant is now active - monitoring for errors'
            })

    def disable(self):
        """Disable debugging agent"""
        if not self.is_enabled:
            return

        self.is_enabled = False

        # Stop log monitor
        if self.log_monitor:
            self.log_monitor.stop()
            self.log_monitor = None

        logger.info("🐛 Debugging agent disabled")

        # Notify user via WebSocket
        if self.socketio:
            self.socketio.emit('debug_status', {
                'enabled': False,
                'message': '🐛 Debugging assistant deactivated'
            })

    def toggle(self) -> bool:
        """Toggle debugging agent on/off"""
        if self.is_enabled:
            self.disable()
        else:
            self.enable()

        return self.is_enabled

    def get_status(self) -> Dict:
        """Get current debugging agent status"""
        return {
            'enabled': self.is_enabled,
            'dev_mode': self.is_dev_mode,
            'monitoring': self.log_monitor is not None
        }

    def _send_debug_message(self, debug_msg: Dict):
        """Send debugging message to user via WebSocket"""
        if self.socketio:
            self.socketio.emit('debug_message', debug_msg)


# Global debugging agent instance
_debug_agent = None


def get_debug_agent(socketio=None) -> DebugAgent:
    """Get or create global debugging agent instance"""
    global _debug_agent

    if _debug_agent is None:
        _debug_agent = DebugAgent(socketio=socketio)

    return _debug_agent
