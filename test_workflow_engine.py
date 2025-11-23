"""
Test Workflow Engine

Simple test to verify the workflow engine works correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from backend.workflows import (
    Workflow,
    WorkflowStep,
    WorkflowEngine,
    WorkflowManager,
    StepType,
    RetryPolicy
)


async def test_simple_workflow():
    """Test a simple workflow execution."""
    print("=" * 60)
    print("Testing Simple Workflow Execution")
    print("=" * 60)

    # Create a simple workflow
    workflow = Workflow(
        workflow_id="test_workflow_001",
        name="Simple Test Workflow",
        description="A simple test workflow with sequential steps",
        version="1.0.0",
        steps=[
            WorkflowStep(
                step_id="step1",
                step_type=StepType.SEARCH,
                name="Search Papers",
                description="Search for research papers",
                inputs={"query": "machine learning", "max_results": 10},
                outputs=["search_results", "result_count"]
            ),
            WorkflowStep(
                step_id="step2",
                step_type=StepType.FILTER,
                name="Filter Results",
                description="Filter search results",
                inputs={
                    "items": "$step1.search_results",
                    "criteria": {"year_min": 2020}
                },
                outputs=["filtered_items", "filtered_count"],
                depends_on=["step1"]
            ),
            WorkflowStep(
                step_id="step3",
                step_type=StepType.EXPORT,
                name="Export Results",
                description="Export filtered results",
                inputs={
                    "data": "$step2.filtered_items",
                    "format": "json",
                    "output_path": "results.json"
                },
                outputs=["exported"],
                depends_on=["step2"]
            )
        ],
        variables={"project": "test"},
        error_handling="continue"
    )

    # Create engine
    engine = WorkflowEngine()

    print(f"\nWorkflow: {workflow.name}")
    print(f"Steps: {len(workflow.steps)}")
    print(f"Dependencies resolved: ", end="")

    # Test dependency resolution
    try:
        execution_order = engine.resolve_dependencies(workflow)
        print(f"OK")
        print(f"Execution order: {' -> '.join(execution_order)}")
    except Exception as e:
        print(f"FAILED")
        print(f"Error: {e}")
        return False

    # Execute workflow
    print(f"\nExecuting workflow...")
    try:
        result = await engine.execute_workflow(workflow, initial_inputs={})
        print(f"OK - Workflow completed successfully")
        print(f"\nWorkflow Status: {workflow.status.value}")
        print(f"Execution Time: {result.get('duration_seconds', 0):.2f}s")

        print(f"\nStep Execution Summary:")
        for step in workflow.steps:
            status_symbol = "OK" if step.status.value == "completed" else "FAIL"
            print(f"  {status_symbol} {step.name}: {step.status.value}")

        return True

    except Exception as e:
        print(f"FAILED - Workflow failed")
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_workflow_manager():
    """Test workflow manager functionality."""
    print("\n" + "=" * 60)
    print("Testing Workflow Manager")
    print("=" * 60)

    # Initialize manager
    manager = WorkflowManager()

    # Test loading template
    template_path = Path(__file__).parent / "backend" / "workflows" / "templates" / "rapid_review.yaml"

    if template_path.exists():
        print(f"\nLoading template from: {template_path}")
        try:
            workflow = manager.load_workflow(str(template_path))
            print(f"OK - Template loaded successfully")
            print(f"  Workflow: {workflow.name}")
            print(f"  Steps: {len(workflow.steps)}")
            print(f"  Version: {workflow.version}")

            # Validate
            print(f"\nValidating workflow...")
            try:
                manager.validate_workflow(workflow)
                print(f"OK - Workflow is valid")
            except Exception as e:
                print(f"FAILED - Validation failed: {e}")

            return True

        except Exception as e:
            print(f"FAILED - Failed to load template: {e}")
            import traceback
            traceback.print_exc()
            return False
    else:
        print(f"FAILED - Template not found at: {template_path}")
        return False


async def test_circular_dependency_detection():
    """Test that circular dependencies are detected."""
    print("\n" + "=" * 60)
    print("Testing Circular Dependency Detection")
    print("=" * 60)

    # Create workflow with circular dependency
    workflow = Workflow(
        workflow_id="circular_test",
        name="Circular Dependency Test",
        steps=[
            WorkflowStep(
                step_id="step1",
                step_type=StepType.SEARCH,
                name="Step 1",
                depends_on=["step2"]  # Circular!
            ),
            WorkflowStep(
                step_id="step2",
                step_type=StepType.FILTER,
                name="Step 2",
                depends_on=["step1"]  # Circular!
            )
        ]
    )

    engine = WorkflowEngine()

    print(f"\nAttempting to resolve dependencies...")
    try:
        engine.resolve_dependencies(workflow)
        print(f"FAILED - Circular dependency NOT detected (this is a bug!)")
        return False
    except ValueError as e:
        print(f"OK - Circular dependency detected: {e}")
        return True
    except Exception as e:
        print(f"FAILED - Unexpected error: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n")
    print("+" + "=" * 58 + "+")
    print("|" + " WORKFLOW ENGINE TEST SUITE ".center(58) + "|")
    print("+" + "=" * 58 + "+")

    results = []

    # Run tests
    results.append(("Simple Workflow Execution", await test_simple_workflow()))
    results.append(("Workflow Manager", await test_workflow_manager()))
    results.append(("Circular Dependency Detection", await test_circular_dependency_detection()))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{status:8} {name}")

    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
