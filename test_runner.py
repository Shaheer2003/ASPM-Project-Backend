"""
Test Runner Script

Provides convenient commands for running tests with various configurations.
Supports running all tests, specific test files, tests by marker, or with coverage.

Usage:
    python test_runner.py                 # Run all tests
    python test_runner.py --coverage      # Run with coverage report
    python test_runner.py --unit          # Run only unit tests
    python test_runner.py --integration   # Run only integration tests
    python test_runner.py --auth          # Run only auth tests
    python test_runner.py -v              # Verbose output
    python test_runner.py --failed        # Run only previously failed tests
"""

import subprocess
import sys
import argparse
from pathlib import Path


class TestRunner:
    """Manages test execution with various options."""
    
    def __init__(self):
        """Initialize test runner with project paths."""
        self.project_root = Path(__file__).parent
        self.tests_dir = self.project_root / "tests"
    
    def run_all_tests(self, verbose=False, coverage=False):
        """
        Run all tests.
        
        Args:
            verbose (bool): Enable verbose output
            coverage (bool): Generate coverage report
        """
        cmd = ["pytest", str(self.tests_dir)]
        
        if verbose:
            cmd.append("-v")
        if coverage:
            cmd.extend(["--cov=app", "--cov-report=html"])
        
        return self._execute_command(cmd)
    
    def run_unit_tests(self, verbose=False):
        """
        Run only unit tests (models, utils).
        
        Args:
            verbose (bool): Enable verbose output
        """
        cmd = ["pytest", str(self.tests_dir), "-m", "unit"]
        
        if verbose:
            cmd.append("-v")
        
        return self._execute_command(cmd)
    
    def run_integration_tests(self, verbose=False):
        """
        Run only integration tests (endpoints).
        
        Args:
            verbose (bool): Enable verbose output
        """
        cmd = ["pytest", str(self.tests_dir), "-m", "integration"]
        
        if verbose:
            cmd.append("-v")
        
        return self._execute_command(cmd)
    
    def run_auth_tests(self, verbose=False):
        """
        Run only authentication tests.
        
        Args:
            verbose (bool): Enable verbose output
        """
        cmd = ["pytest", "tests/test_auth.py"]
        
        if verbose:
            cmd.append("-v")
        
        return self._execute_command(cmd)
    
    def run_admin_tests(self, verbose=False):
        """Run only admin endpoint tests."""
        cmd = ["pytest", "tests/test_admin.py"]
        
        if verbose:
            cmd.append("-v")
        
        return self._execute_command(cmd)
    
    def run_teacher_tests(self, verbose=False):
        """Run only teacher endpoint tests."""
        cmd = ["pytest", "tests/test_teacher.py"]
        
        if verbose:
            cmd.append("-v")
        
        return self._execute_command(cmd)
    
    def run_student_tests(self, verbose=False):
        """Run only student endpoint tests."""
        cmd = ["pytest", "tests/test_student.py"]
        
        if verbose:
            cmd.append("-v")
        
        return self._execute_command(cmd)
    
    def run_model_tests(self, verbose=False):
        """Run only model tests."""
        cmd = ["pytest", "tests/test_models.py"]
        
        if verbose:
            cmd.append("-v")
        
        return self._execute_command(cmd)
    
    def run_failed_only(self, verbose=False):
        """
        Run only previously failed tests.
        
        Args:
            verbose (bool): Enable verbose output
        """
        cmd = ["pytest", str(self.tests_dir), "--lf"]
        
        if verbose:
            cmd.append("-v")
        
        return self._execute_command(cmd)
    
    def run_with_markers(self, marker, verbose=False):
        """
        Run tests with specific marker.
        
        Args:
            marker (str): Pytest marker name
            verbose (bool): Enable verbose output
        """
        cmd = ["pytest", str(self.tests_dir), "-m", marker]
        
        if verbose:
            cmd.append("-v")
        
        return self._execute_command(cmd)
    
    def generate_coverage_report(self):
        """Generate HTML coverage report."""
        cmd = [
            "pytest",
            str(self.tests_dir),
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing"
        ]
        
        result = self._execute_command(cmd)
        
        if result == 0:
            print("\n✓ Coverage report generated at: htmlcov/index.html")
        
        return result
    
    def run_with_profile(self):
        """
        Run tests with profiling information.
        
        Shows which tests are slowest.
        """
        cmd = [
            "pytest",
            str(self.tests_dir),
            "--durations=10",
            "-v"
        ]
        
        return self._execute_command(cmd)
    
    @staticmethod
    def _execute_command(cmd):
        """
        Execute shell command and return exit code.
        
        Args:
            cmd (list): Command and arguments to execute
            
        Returns:
            int: Exit code (0 = success)
        """
        print(f"Executing: {' '.join(cmd)}\n")
        print("-" * 70)
        
        try:
            result = subprocess.run(cmd, check=False)
            return result.returncode
        except FileNotFoundError:
            print("Error: pytest not installed. Install with: pip install pytest pytest-cov")
            return 1


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Test runner for ASPM Backend API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_runner.py                # Run all tests
  python test_runner.py --coverage     # Run with coverage report
  python test_runner.py --unit         # Run only unit tests
  python test_runner.py --auth -v      # Run auth tests verbosely
  python test_runner.py --profile      # Show slowest tests
        """
    )
    
    # Test selection arguments
    parser.add_argument("--all", action="store_true", help="Run all tests (default)")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--auth", action="store_true", help="Run authentication tests")
    parser.add_argument("--admin", action="store_true", help="Run admin endpoint tests")
    parser.add_argument("--teacher", action="store_true", help="Run teacher endpoint tests")
    parser.add_argument("--student", action="store_true", help="Run student endpoint tests")
    parser.add_argument("--models", action="store_true", help="Run model tests")
    parser.add_argument("--failed", action="store_true", help="Run only failed tests")
    
    # Report arguments
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--profile", action="store_true", help="Show slowest tests")
    
    # Output arguments
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    exit_code = 0
    
    # Determine which tests to run
    if args.coverage:
        exit_code = runner.generate_coverage_report()
    elif args.profile:
        exit_code = runner.run_with_profile()
    elif args.unit:
        exit_code = runner.run_unit_tests(verbose=args.verbose)
    elif args.integration:
        exit_code = runner.run_integration_tests(verbose=args.verbose)
    elif args.auth:
        exit_code = runner.run_auth_tests(verbose=args.verbose)
    elif args.admin:
        exit_code = runner.run_admin_tests(verbose=args.verbose)
    elif args.teacher:
        exit_code = runner.run_teacher_tests(verbose=args.verbose)
    elif args.student:
        exit_code = runner.run_student_tests(verbose=args.verbose)
    elif args.models:
        exit_code = runner.run_model_tests(verbose=args.verbose)
    elif args.failed:
        exit_code = runner.run_failed_only(verbose=args.verbose)
    else:
        # Default: run all tests
        exit_code = runner.run_all_tests(
            verbose=args.verbose,
            coverage=args.coverage
        )
    
    # Print summary
    print("\n" + "=" * 70)
    if exit_code == 0:
        print("✓ All tests passed!")
    else:
        print(f"✗ Tests failed with exit code: {exit_code}")
    print("=" * 70 + "\n")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
