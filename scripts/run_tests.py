#!/usr/bin/env python3
"""
Test runner script for the AssetPlan Property Assistant project.
"""
import sys
import subprocess
import argparse
from pathlib import Path

def run_tests(test_type="all", verbose=True, coverage=True):
    """Run tests with specified options.
    
    Args:
        test_type: Type of tests to run ("unit", "integration", "all")
        verbose: Whether to run in verbose mode
        coverage: Whether to include coverage reporting
    """
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add coverage
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=term-missing"])
    
    # Select test type
    if test_type == "unit":
        cmd.extend(["-m", "not integration"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow and not integration"])
    
    # Add test path
    cmd.append("tests/")
    
    print(f"Running command: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Run tests for AssetPlan Property Assistant")
    parser.add_argument(
        "--type", 
        choices=["unit", "integration", "fast", "all"], 
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--no-coverage", 
        action="store_true",
        help="Disable coverage reporting"
    )
    parser.add_argument(
        "--quiet", 
        action="store_true",
        help="Run in quiet mode"
    )
    
    args = parser.parse_args()
    
    print("🧪 AssetPlan Property Assistant - Test Runner")
    print("=" * 50)
    
    # Check if tests directory exists
    if not Path("tests").exists():
        print("❌ Tests directory not found")
        sys.exit(1)
    
    # Run tests
    success = run_tests(
        test_type=args.type,
        verbose=not args.quiet,
        coverage=not args.no_coverage
    )
    
    if success:
        print("\n✅ All tests passed!")
        print("\n📋 Test Summary:")
        print(f"   - Test type: {args.type}")
        print(f"   - Coverage: {'enabled' if not args.no_coverage else 'disabled'}")
        
        if not args.no_coverage:
            print("\n📊 Coverage report generated:")
            print("   - Terminal: displayed above")
            print("   - HTML: htmlcov/index.html")
        
    else:
        print("\n❌ Some tests failed!")
        print("\nTo run specific test types:")
        print("   python run_tests.py --type unit      # Unit tests only")
        print("   python run_tests.py --type integration  # Integration tests only")
        print("   python run_tests.py --type fast     # Fast tests only")
        
        sys.exit(1)


if __name__ == "__main__":
    main()