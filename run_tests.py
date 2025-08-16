"""
Test runner for Camera Privacy Manager
Runs all unit tests and integration tests
"""
import sys
import unittest
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_all_tests():
    """Run all tests in the tests directory"""
    try:
        # Discover and run tests
        loader = unittest.TestLoader()
        start_dir = project_root / "tests"
        
        if not start_dir.exists():
            print(f"Tests directory not found: {start_dir}")
            return False
        
        suite = loader.discover(str(start_dir), pattern='test_*.py')
        
        # Run tests with detailed output
        runner = unittest.TextTestRunner(
            verbosity=2,
            stream=sys.stdout,
            descriptions=True,
            failfast=False
        )
        
        print("=" * 70)
        print("Running Camera Privacy Manager Test Suite")
        print("=" * 70)
        
        result = runner.run(suite)
        
        print("\n" + "=" * 70)
        print("Test Summary")
        print("=" * 70)
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped)}")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"- {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"- {test}: {traceback}")
        
        success = result.wasSuccessful()
        print(f"\nResult: {'PASSED' if success else 'FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def run_specific_test(test_name):
    """Run a specific test module or test case"""
    try:
        # Try to load and run the specific test
        loader = unittest.TestLoader()
        
        # Check if it's a module or specific test
        if '.' in test_name:
            # Specific test case
            suite = loader.loadTestsFromName(test_name)
        else:
            # Test module
            test_module = f"tests.{test_name}"
            suite = loader.loadTestsFromName(test_module)
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
        
    except Exception as e:
        print(f"Error running test '{test_name}': {e}")
        return False


def list_available_tests():
    """List all available test modules"""
    tests_dir = project_root / "tests"
    
    if not tests_dir.exists():
        print("Tests directory not found")
        return
    
    print("Available test modules:")
    for test_file in tests_dir.glob("test_*.py"):
        module_name = test_file.stem
        print(f"  - {module_name}")


if __name__ == "__main__":
    args = sys.argv[1:]
    
    if not args:
        # Run all tests
        success = run_all_tests()
        sys.exit(0 if success else 1)
    elif args[0] == "--list":
        # List available tests
        list_available_tests()
        sys.exit(0)
    elif args[0] == "--help":
        # Show help
        print("""
Test Runner for Camera Privacy Manager

Usage:
    python run_tests.py [options] [test_name]

Options:
    --help      Show this help message
    --list      List available test modules

Examples:
    python run_tests.py                    # Run all tests
    python run_tests.py test_database_manager  # Run specific test module
    python run_tests.py --list             # List available tests
        """)
        sys.exit(0)
    else:
        # Run specific test
        test_name = args[0]
        success = run_specific_test(test_name)
        sys.exit(0 if success else 1)