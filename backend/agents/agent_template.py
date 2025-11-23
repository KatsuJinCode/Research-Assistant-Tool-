"""
Agent Template System

Design a template system for creating custom agents.
Provides base agent class with standard interface and example templates.
"""

import yaml
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class ExecutionType(Enum):
    """Agent execution types"""
    AI_QUERY = "ai_query"
    PYTHON_FUNCTION = "python_function"
    CHAIN = "chain"
    CONDITIONAL = "conditional"


class InputType(Enum):
    """Input data types"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class OutputType(Enum):
    """Output data types"""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


@dataclass
class InputSchema:
    """Schema for agent input"""
    name: str
    type: InputType
    description: str = ""
    required: bool = True
    default: Any = None
    validation: Optional[Dict[str, Any]] = None


@dataclass
class OutputSchema:
    """Schema for agent output"""
    name: str
    type: OutputType
    description: str = ""


@dataclass
class Configuration:
    """Agent configuration"""
    max_length: Optional[int] = None
    style: Optional[str] = None
    temperature: float = 0.5
    max_tokens: int = 2000
    timeout: int = 60
    custom: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionConfig:
    """Execution configuration"""
    type: ExecutionType
    prompt: Optional[str] = None
    function_name: Optional[str] = None
    steps: Optional[List[Dict[str, Any]]] = None
    conditions: Optional[List[Dict[str, Any]]] = None


class AgentTemplate:
    """
    Base agent template class.

    Provides standard interface for custom agents with configurable:
    - Name, description, version
    - Input/output schemas
    - Execution method
    - Configuration options
    """

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        inputs: List[InputSchema],
        outputs: List[OutputSchema],
        execution: ExecutionConfig,
        configuration: Configuration
    ):
        self.name = name
        self.version = version
        self.description = description
        self.inputs = inputs
        self.outputs = outputs
        self.execution = execution
        self.configuration = configuration

        # Runtime state
        self.ai_client: Optional[Any] = None
        self.custom_functions: Dict[str, Callable] = {}

    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """
        Validate input data against schema.

        Args:
            inputs: Input data to validate

        Returns:
            True if valid, raises ValueError if invalid
        """
        for schema in self.inputs:
            # Check required inputs
            if schema.required and schema.name not in inputs:
                if schema.default is not None:
                    inputs[schema.name] = schema.default
                else:
                    raise ValueError(f"Required input '{schema.name}' missing")

            # Check type
            if schema.name in inputs:
                value = inputs[schema.name]
                if not self._validate_type(value, schema.type):
                    raise ValueError(
                        f"Input '{schema.name}' has invalid type. "
                        f"Expected {schema.type.value}, got {type(value).__name__}"
                    )

                # Run custom validation
                if schema.validation:
                    if not self._run_validation(value, schema.validation):
                        raise ValueError(
                            f"Input '{schema.name}' failed validation: {schema.validation}"
                        )

        return True

    def _validate_type(self, value: Any, expected_type: InputType) -> bool:
        """Validate value type"""
        type_map = {
            InputType.STRING: str,
            InputType.NUMBER: (int, float),
            InputType.BOOLEAN: bool,
            InputType.ARRAY: list,
            InputType.OBJECT: dict
        }
        expected = type_map[expected_type]
        return isinstance(value, expected)

    def _run_validation(self, value: Any, validation: Dict[str, Any]) -> bool:
        """Run custom validation rules"""
        # Min/max for numbers
        if 'min' in validation and value < validation['min']:
            return False
        if 'max' in validation and value > validation['max']:
            return False

        # Length for strings/arrays
        if 'min_length' in validation and len(value) < validation['min_length']:
            return False
        if 'max_length' in validation and len(value) > validation['max_length']:
            return False

        # Pattern for strings
        if 'pattern' in validation:
            import re
            if not re.match(validation['pattern'], value):
                return False

        return True

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent.

        Args:
            inputs: Input data

        Returns:
            Output data
        """
        # Validate inputs
        self.validate_inputs(inputs)

        # Execute based on type
        if self.execution.type == ExecutionType.AI_QUERY:
            return self._execute_ai_query(inputs)
        elif self.execution.type == ExecutionType.PYTHON_FUNCTION:
            return self._execute_python_function(inputs)
        elif self.execution.type == ExecutionType.CHAIN:
            return self._execute_chain(inputs)
        elif self.execution.type == ExecutionType.CONDITIONAL:
            return self._execute_conditional(inputs)
        else:
            raise ValueError(f"Unknown execution type: {self.execution.type}")

    def _execute_ai_query(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute AI query"""
        if not self.ai_client:
            raise RuntimeError("AI client not configured")

        # Format prompt with inputs
        prompt = self.execution.prompt
        for key, value in inputs.items():
            prompt = prompt.replace(f"{{{{{key}}}}}", str(value))

        # Generate response
        try:
            # Assuming async AI client - would need proper async handling
            import asyncio
            if asyncio.iscoroutinefunction(self.ai_client.generate):
                response = asyncio.run(self.ai_client.generate(
                    prompt,
                    temperature=self.configuration.temperature,
                    max_tokens=self.configuration.max_tokens
                ))
            else:
                response = self.ai_client.generate(prompt)

            # Return structured output
            output_name = self.outputs[0].name if self.outputs else "result"
            return {output_name: response}

        except Exception as e:
            logger.error(f"AI query failed: {e}")
            raise

    def _execute_python_function(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Python function"""
        function_name = self.execution.function_name
        if function_name not in self.custom_functions:
            raise ValueError(f"Function '{function_name}' not registered")

        func = self.custom_functions[function_name]
        return func(**inputs)

    def _execute_chain(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute chain of steps"""
        current_data = inputs.copy()

        for step in self.execution.steps or []:
            step_type = step.get('type')

            if step_type == 'ai_query':
                prompt = step['prompt']
                for key, value in current_data.items():
                    prompt = prompt.replace(f"{{{{{key}}}}}", str(value))

                response = self.ai_client.generate(prompt)
                current_data[step['output']] = response

            elif step_type == 'function':
                func = self.custom_functions[step['function']]
                result = func(**current_data)
                current_data.update(result)

        return current_data

    def _execute_conditional(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conditional logic"""
        for condition in self.execution.conditions or []:
            if self._evaluate_condition(condition['if'], inputs):
                return self.execute({'inputs': inputs, **condition['then']})

        # Default case
        if self.execution.conditions and 'else' in self.execution.conditions[-1]:
            return self.execute({'inputs': inputs, **self.execution.conditions[-1]['else']})

        return {}

    def _evaluate_condition(self, condition: str, data: Dict[str, Any]) -> bool:
        """Evaluate simple condition"""
        # Simple evaluation - could be expanded
        import operator
        ops = {
            '==': operator.eq,
            '!=': operator.ne,
            '>': operator.gt,
            '<': operator.lt,
            '>=': operator.ge,
            '<=': operator.le
        }

        for op_str, op_func in ops.items():
            if op_str in condition:
                left, right = condition.split(op_str)
                left_val = data.get(left.strip(), left.strip())
                right_val = data.get(right.strip(), right.strip())
                return op_func(left_val, right_val)

        return False

    def register_function(self, name: str, func: Callable):
        """Register custom Python function"""
        self.custom_functions[name] = func

    def set_ai_client(self, ai_client: Any):
        """Set AI client for AI queries"""
        self.ai_client = ai_client

    @classmethod
    def from_yaml(cls, yaml_path: str) -> 'AgentTemplate':
        """
        Load agent template from YAML file.

        Args:
            yaml_path: Path to YAML template file

        Returns:
            AgentTemplate instance
        """
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentTemplate':
        """Create agent from dictionary"""
        # Parse inputs
        inputs = [
            InputSchema(
                name=inp['name'],
                type=InputType(inp['type']),
                description=inp.get('description', ''),
                required=inp.get('required', True),
                default=inp.get('default'),
                validation=inp.get('validation')
            )
            for inp in data.get('inputs', [])
        ]

        # Parse outputs
        outputs = [
            OutputSchema(
                name=out['name'],
                type=OutputType(out['type']),
                description=out.get('description', '')
            )
            for out in data.get('outputs', [])
        ]

        # Parse execution
        exec_data = data.get('execution', {})
        execution = ExecutionConfig(
            type=ExecutionType(exec_data['type']),
            prompt=exec_data.get('prompt'),
            function_name=exec_data.get('function_name'),
            steps=exec_data.get('steps'),
            conditions=exec_data.get('conditions')
        )

        # Parse configuration
        config_data = data.get('configuration', {})
        configuration = Configuration(
            max_length=config_data.get('max_length'),
            style=config_data.get('style'),
            temperature=config_data.get('temperature', 0.5),
            max_tokens=config_data.get('max_tokens', 2000),
            timeout=config_data.get('timeout', 60),
            custom=config_data.get('custom', {})
        )

        return cls(
            name=data['name'],
            version=data['version'],
            description=data['description'],
            inputs=inputs,
            outputs=outputs,
            execution=execution,
            configuration=configuration
        )

    def to_dict(self) -> Dict[str, Any]:
        """Export template to dictionary"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'inputs': [
                {
                    'name': inp.name,
                    'type': inp.type.value,
                    'description': inp.description,
                    'required': inp.required,
                    'default': inp.default,
                    'validation': inp.validation
                }
                for inp in self.inputs
            ],
            'outputs': [
                {
                    'name': out.name,
                    'type': out.type.value,
                    'description': out.description
                }
                for out in self.outputs
            ],
            'execution': {
                'type': self.execution.type.value,
                'prompt': self.execution.prompt,
                'function_name': self.execution.function_name,
                'steps': self.execution.steps,
                'conditions': self.execution.conditions
            },
            'configuration': {
                'max_length': self.configuration.max_length,
                'style': self.configuration.style,
                'temperature': self.configuration.temperature,
                'max_tokens': self.configuration.max_tokens,
                'timeout': self.configuration.timeout,
                'custom': self.configuration.custom
            }
        }

    def to_yaml(self, output_path: str):
        """Export template to YAML file"""
        with open(output_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)


class AgentExecutor:
    """
    Executes agent templates with dependency injection.
    """

    def __init__(self, ai_client: Any = None):
        self.ai_client = ai_client
        self.templates: Dict[str, AgentTemplate] = {}

    def register_template(self, template: AgentTemplate):
        """Register an agent template"""
        template.set_ai_client(self.ai_client)
        self.templates[template.name] = template

    def execute(self, agent_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent by name"""
        if agent_name not in self.templates:
            raise ValueError(f"Agent '{agent_name}' not found")

        return self.templates[agent_name].execute(inputs)

    def list_agents(self) -> List[Dict[str, str]]:
        """List all registered agents"""
        return [
            {
                'name': template.name,
                'version': template.version,
                'description': template.description
            }
            for template in self.templates.values()
        ]


# Example template definitions (can be loaded from YAML)
EXAMPLE_TEMPLATES = {
    'document_summarizer': {
        'name': 'document_summarizer',
        'version': '1.0.0',
        'description': 'Summarizes documents with configurable length and style',
        'inputs': [
            {
                'name': 'document_text',
                'type': 'string',
                'description': 'The document text to summarize',
                'validation': {'min_length': 10}
            }
        ],
        'outputs': [
            {
                'name': 'summary',
                'type': 'string',
                'description': 'The generated summary'
            }
        ],
        'configuration': {
            'max_length': 500,
            'style': 'concise',
            'temperature': 0.3
        },
        'execution': {
            'type': 'ai_query',
            'prompt': 'Summarize the following document in a concise manner (max 500 words):\n\n{{document_text}}'
        }
    },

    'claim_extractor': {
        'name': 'claim_extractor',
        'version': '1.0.0',
        'description': 'Extracts factual claims from text',
        'inputs': [
            {
                'name': 'text',
                'type': 'string',
                'description': 'Text to extract claims from'
            }
        ],
        'outputs': [
            {
                'name': 'claims',
                'type': 'array',
                'description': 'List of extracted claims'
            }
        ],
        'configuration': {
            'temperature': 0.1,
            'max_tokens': 3000
        },
        'execution': {
            'type': 'ai_query',
            'prompt': '''Extract all factual claims from this text. Return as JSON array:

{{text}}

Format: [{"claim": "...", "confidence": 0.0-1.0}]'''
        }
    },

    'evidence_finder': {
        'name': 'evidence_finder',
        'version': '1.0.0',
        'description': 'Finds evidence supporting or contradicting a claim',
        'inputs': [
            {
                'name': 'claim',
                'type': 'string',
                'description': 'The claim to investigate'
            },
            {
                'name': 'context',
                'type': 'string',
                'description': 'Context documents to search'
            }
        ],
        'outputs': [
            {
                'name': 'evidence',
                'type': 'array',
                'description': 'List of evidence items'
            }
        ],
        'configuration': {
            'temperature': 0.2
        },
        'execution': {
            'type': 'ai_query',
            'prompt': '''Find evidence for or against this claim:

Claim: {{claim}}

Context:
{{context}}

Return JSON: [{"text": "...", "type": "support/challenge", "relevance": 0.0-1.0}]'''
        }
    },

    'contradiction_checker': {
        'name': 'contradiction_checker',
        'version': '1.0.0',
        'description': 'Checks if two claims contradict each other',
        'inputs': [
            {
                'name': 'claim1',
                'type': 'string'
            },
            {
                'name': 'claim2',
                'type': 'string'
            }
        ],
        'outputs': [
            {
                'name': 'contradicts',
                'type': 'boolean'
            },
            {
                'name': 'explanation',
                'type': 'string'
            }
        ],
        'configuration': {
            'temperature': 0.0
        },
        'execution': {
            'type': 'ai_query',
            'prompt': '''Do these claims contradict each other?

Claim 1: {{claim1}}
Claim 2: {{claim2}}

Return JSON: {"contradicts": true/false, "explanation": "..."}'''
        }
    },

    'custom_research_agent': {
        'name': 'custom_research_agent',
        'version': '1.0.0',
        'description': 'Custom research workflow with multiple steps',
        'inputs': [
            {
                'name': 'topic',
                'type': 'string',
                'description': 'Research topic'
            }
        ],
        'outputs': [
            {
                'name': 'report',
                'type': 'string',
                'description': 'Research report'
            }
        ],
        'configuration': {
            'temperature': 0.5
        },
        'execution': {
            'type': 'chain',
            'steps': [
                {
                    'type': 'ai_query',
                    'prompt': 'Generate 5 key questions about: {{topic}}',
                    'output': 'questions'
                },
                {
                    'type': 'ai_query',
                    'prompt': 'Research these questions:\n{{questions}}',
                    'output': 'answers'
                },
                {
                    'type': 'ai_query',
                    'prompt': 'Write a research report based on:\n{{answers}}',
                    'output': 'report'
                }
            ]
        }
    }
}


def create_example_templates(output_dir: str):
    """Create example template YAML files"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    for name, template_dict in EXAMPLE_TEMPLATES.items():
        template = AgentTemplate.from_dict(template_dict)
        template.to_yaml(str(output_path / f"{name}.yaml"))
        logger.info(f"Created template: {output_path / name}.yaml")
