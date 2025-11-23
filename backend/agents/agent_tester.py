"""
Agent Testing Framework

Testing tools for custom agents including:
- Unit test generation
- Test data fixtures
- Performance benchmarks
- Output validation
- Test reports
"""

import time
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """Individual test case"""
    name: str
    inputs: Dict[str, Any]
    expected_outputs: Optional[Dict[str, Any]] = None
    validation_fn: Optional[Callable] = None
    timeout: int = 60
    description: str = ""


@dataclass
class TestResult:
    """Result of a test case"""
    test_name: str
    passed: bool
    actual_outputs: Optional[Dict[str, Any]] = None
    expected_outputs: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class TestSuite:
    """Collection of test cases"""
    name: str
    description: str
    test_cases: List[TestCase] = field(default_factory=list)
    setup: Optional[Callable] = None
    teardown: Optional[Callable] = None


@dataclass
class BenchmarkResult:
    """Performance benchmark result"""
    operation: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    min_time_ms: float
    max_time_ms: float
    throughput_per_sec: float


class AgentTester:
    """
    Testing framework for custom agents.

    Provides comprehensive testing capabilities including unit tests,
    performance benchmarks, and output validation.
    """

    def __init__(self, agent_executor: Any = None):
        """
        Initialize agent tester.

        Args:
            agent_executor: AgentExecutor instance to test agents
        """
        self.agent_executor = agent_executor
        self.test_suites: Dict[str, TestSuite] = {}
        self.results: List[TestResult] = []

    def create_test_suite(
        self,
        name: str,
        description: str = "",
        setup: Optional[Callable] = None,
        teardown: Optional[Callable] = None
    ) -> TestSuite:
        """
        Create a new test suite.

        Args:
            name: Suite name
            description: Suite description
            setup: Setup function run before tests
            teardown: Teardown function run after tests

        Returns:
            TestSuite instance
        """
        suite = TestSuite(
            name=name,
            description=description,
            setup=setup,
            teardown=teardown
        )
        self.test_suites[name] = suite
        return suite

    def add_test_case(
        self,
        suite_name: str,
        test_case: TestCase
    ):
        """Add test case to suite"""
        if suite_name not in self.test_suites:
            raise ValueError(f"Test suite '{suite_name}' not found")

        self.test_suites[suite_name].test_cases.append(test_case)

    def run_test_case(
        self,
        agent_name: str,
        test_case: TestCase
    ) -> TestResult:
        """
        Run a single test case.

        Args:
            agent_name: Name of agent to test
            test_case: Test case to run

        Returns:
            TestResult
        """
        start_time = time.time()

        try:
            # Execute agent
            actual_outputs = self.agent_executor.execute(
                agent_name,
                test_case.inputs
            )

            execution_time = (time.time() - start_time) * 1000  # ms

            # Validate outputs
            passed = True
            error = None

            if test_case.expected_outputs:
                # Compare expected vs actual
                if actual_outputs != test_case.expected_outputs:
                    passed = False
                    error = f"Output mismatch. Expected: {test_case.expected_outputs}, Got: {actual_outputs}"

            if test_case.validation_fn:
                # Run custom validation
                try:
                    validation_result = test_case.validation_fn(actual_outputs)
                    if not validation_result:
                        passed = False
                        error = "Custom validation failed"
                except Exception as e:
                    passed = False
                    error = f"Validation error: {str(e)}"

            return TestResult(
                test_name=test_case.name,
                passed=passed,
                actual_outputs=actual_outputs,
                expected_outputs=test_case.expected_outputs,
                error=error,
                execution_time_ms=execution_time
            )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"Test case '{test_case.name}' failed: {e}")

            return TestResult(
                test_name=test_case.name,
                passed=False,
                error=str(e),
                execution_time_ms=execution_time
            )

    def run_test_suite(
        self,
        suite_name: str,
        agent_name: str
    ) -> List[TestResult]:
        """
        Run all tests in a suite.

        Args:
            suite_name: Name of test suite
            agent_name: Name of agent to test

        Returns:
            List of test results
        """
        if suite_name not in self.test_suites:
            raise ValueError(f"Test suite '{suite_name}' not found")

        suite = self.test_suites[suite_name]
        results = []

        # Run setup
        if suite.setup:
            try:
                suite.setup()
            except Exception as e:
                logger.error(f"Setup failed: {e}")
                return results

        # Run each test
        for test_case in suite.test_cases:
            result = self.run_test_case(agent_name, test_case)
            results.append(result)
            self.results.append(result)

        # Run teardown
        if suite.teardown:
            try:
                suite.teardown()
            except Exception as e:
                logger.error(f"Teardown failed: {e}")

        return results

    def run_all_suites(self, agent_name: str) -> Dict[str, List[TestResult]]:
        """
        Run all test suites for an agent.

        Args:
            agent_name: Name of agent to test

        Returns:
            Dictionary mapping suite names to results
        """
        all_results = {}

        for suite_name in self.test_suites.keys():
            results = self.run_test_suite(suite_name, agent_name)
            all_results[suite_name] = results

        return all_results

    def benchmark_agent(
        self,
        agent_name: str,
        inputs: Dict[str, Any],
        iterations: int = 100
    ) -> BenchmarkResult:
        """
        Benchmark agent performance.

        Args:
            agent_name: Name of agent to benchmark
            inputs: Input data
            iterations: Number of iterations to run

        Returns:
            BenchmarkResult
        """
        times = []

        for i in range(iterations):
            start = time.time()
            try:
                self.agent_executor.execute(agent_name, inputs)
                elapsed = (time.time() - start) * 1000  # ms
                times.append(elapsed)
            except Exception as e:
                logger.error(f"Benchmark iteration {i} failed: {e}")

        if not times:
            raise RuntimeError("All benchmark iterations failed")

        total_time = sum(times)
        avg_time = total_time / len(times)
        min_time = min(times)
        max_time = max(times)
        throughput = 1000.0 / avg_time if avg_time > 0 else 0.0

        return BenchmarkResult(
            operation=agent_name,
            iterations=len(times),
            total_time_ms=total_time,
            avg_time_ms=avg_time,
            min_time_ms=min_time,
            max_time_ms=max_time,
            throughput_per_sec=throughput
        )

    def generate_test_report(
        self,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive test report.

        Args:
            output_path: Optional path to save report JSON

        Returns:
            Report dictionary
        """
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.passed)
        failed_tests = total_tests - passed_tests
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        avg_execution_time = (
            sum(r.execution_time_ms for r in self.results) / total_tests
            if total_tests > 0 else 0
        )

        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'pass_rate': f"{pass_rate:.1f}%",
                'avg_execution_time_ms': f"{avg_execution_time:.2f}"
            },
            'test_results': [
                {
                    'test_name': r.test_name,
                    'passed': r.passed,
                    'execution_time_ms': r.execution_time_ms,
                    'error': r.error,
                    'timestamp': r.timestamp
                }
                for r in self.results
            ],
            'failed_tests': [
                {
                    'test_name': r.test_name,
                    'error': r.error,
                    'expected': r.expected_outputs,
                    'actual': r.actual_outputs
                }
                for r in self.results if not r.passed
            ]
        }

        if output_path:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Test report saved to {output_path}")

        return report

    def generate_test_fixtures(
        self,
        agent_name: str,
        num_fixtures: int = 10,
        output_dir: str = "test_fixtures"
    ):
        """
        Generate test data fixtures.

        Args:
            agent_name: Agent to generate fixtures for
            num_fixtures: Number of fixtures to generate
            output_dir: Directory to save fixtures
        """
        fixtures_path = Path(output_dir)
        fixtures_path.mkdir(parents=True, exist_ok=True)

        # TODO: Implement intelligent fixture generation based on agent schema
        # For now, create template fixtures

        fixtures = []
        for i in range(num_fixtures):
            fixture = {
                'id': i + 1,
                'name': f"fixture_{i+1}",
                'inputs': {},
                'expected_outputs': {}
            }
            fixtures.append(fixture)

        output_file = fixtures_path / f"{agent_name}_fixtures.json"
        with open(output_file, 'w') as f:
            json.dump(fixtures, f, indent=2)

        logger.info(f"Generated {num_fixtures} fixtures: {output_file}")

    def validate_output_schema(
        self,
        outputs: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate agent outputs against schema.

        Args:
            outputs: Actual outputs
            schema: Expected schema

        Returns:
            (is_valid, error_message)
        """
        try:
            for field_name, field_type in schema.items():
                if field_name not in outputs:
                    return False, f"Missing required output field: {field_name}"

                actual_type = type(outputs[field_name]).__name__
                if actual_type != field_type:
                    return False, f"Type mismatch for {field_name}: expected {field_type}, got {actual_type}"

            return True, None

        except Exception as e:
            return False, str(e)

    def clear_results(self):
        """Clear all test results"""
        self.results = []


def create_example_tests(tester: AgentTester):
    """Create example test suite"""

    # Example test suite for document summarizer
    suite = tester.create_test_suite(
        name="document_summarizer_tests",
        description="Test suite for document summarizer agent"
    )

    # Test case 1: Simple summarization
    tester.add_test_case(
        "document_summarizer_tests",
        TestCase(
            name="test_simple_summary",
            inputs={
                'document_text': "This is a test document. It contains multiple sentences. "
                                 "The goal is to test the summarization capability."
            },
            validation_fn=lambda outputs: (
                'summary' in outputs and
                len(outputs['summary']) > 0 and
                len(outputs['summary']) < len("This is a test document...")
            ),
            description="Test basic summarization"
        )
    )

    # Test case 2: Empty input
    tester.add_test_case(
        "document_summarizer_tests",
        TestCase(
            name="test_empty_input",
            inputs={'document_text': ""},
            validation_fn=lambda outputs: 'summary' in outputs,
            description="Test handling of empty input"
        )
    )

    # Test case 3: Long document
    tester.add_test_case(
        "document_summarizer_tests",
        TestCase(
            name="test_long_document",
            inputs={
                'document_text': " ".join(["This is sentence number {}.".format(i) for i in range(100)])
            },
            validation_fn=lambda outputs: (
                'summary' in outputs and
                len(outputs['summary']) < 500  # Should be under max_length
            ),
            description="Test summarization of long document"
        )
    )

    logger.info("Created example test suite with 3 test cases")
