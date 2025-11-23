"""
Test script to generate an error that the debugging agent should catch.
"""
import logging
import sys

# Configure logging to write to the same location as the web app
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/research_assistant.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Generate a test error
try:
    # This will cause a ModuleNotFoundError
    import nonexistent_module
except ModuleNotFoundError as e:
    logger.error(f"Test error for debugging agent: {str(e)}", exc_info=True)
    print("✓ Test error logged to logs/research_assistant.log")
    print("The debugging agent should detect and display this error.")
