#!/usr/bin/env python3
"""
Run pytest with coverage reporting and generate comprehensive reports.

Usage:
    python run_tests_with_coverage.py
    python run_tests_with_coverage.py --html
    python run_tests_with_coverage.py --markers "not slow"
    python run_tests_with_coverage.py --parallel

Requirements:
    uv add pytest pytest-cov
"""

import argparse
import subprocess
import sys
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import pytest
        import pytest_cov
    except ImportError as e:
        print(f"Error: Missing dependency: {e.name}", file=sys.stderr)
        print("\nInstall required packages:", file=sys.stderr)
        print("  uv add pytest pytest-cov", file=sys.stderr)
        sys.exit(1)


def run_tests(
    markers: str = None,
    verbose: bool = True,
    html_report: bool = True,
    fail_under: int = 80,
    parallel: bool = False,
    show_slowest: int = 0,
    extra_args: list = None
):
    """
    Run pytest with coverage reporting.

    Args:
        markers: Pytest marker expression (e.g., "not slow")
        verbose: Enable verbose output
        html_report: Generate HTML coverage report
        fail_under: Minimum coverage percentage required
        parallel: Run tests in parallel (requires pytest-xdist)
        show_slowest: Show N slowest tests
        extra_args: Additional pytest arguments
    """
    cmd = ['pytest']

    # Verbose output
    if verbose:
        cmd.append('-v')

    # Marker filtering
    if markers:
        cmd.extend(['-m', markers])

    # Coverage options
    cmd.extend([
        '--cov=src',
        '--cov-report=term-missing',
        f'--cov-fail-under={fail_under}'
    ])

    # HTML report
    if html_report:
        cmd.append('--cov-report=html')

    # Parallel execution
    if parallel:
        try:
            import xdist
            cmd.extend(['-n', 'auto'])
        except ImportError:
            print("Warning: pytest-xdist not installed. Install with: uv add pytest-xdist")
            print("Running tests sequentially...\n")

    # Show slowest tests
    if show_slowest > 0:
        cmd.append(f'--durations={show_slowest}')

    # Add extra arguments
    if extra_args:
        cmd.extend(extra_args)

    print("Running tests with command:")
    print(" ".join(cmd))
    print()

    # Run pytest
    result = subprocess.run(cmd)

    # Print results
    print("\n" + "=" * 70)
    if result.returncode == 0:
        print("[OK] All tests passed!")
        if html_report:
            html_path = Path('htmlcov') / 'index.html'
            if html_path.exists():
                print(f"\nHTML coverage report: {html_path.absolute()}")
    else:
        print("[FAIL] Tests failed!")
        print(f"Exit code: {result.returncode}")

    print("=" * 70)

    return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run pytest with coverage reporting',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests with coverage
  python run_tests_with_coverage.py

  # Run only unit tests
  python run_tests_with_coverage.py -m unit

  # Skip slow tests
  python run_tests_with_coverage.py -m "not slow"

  # Run tests in parallel
  python run_tests_with_coverage.py --parallel

  # Show 10 slowest tests
  python run_tests_with_coverage.py --durations 10

  # Custom coverage threshold
  python run_tests_with_coverage.py --fail-under 90
        """
    )

    parser.add_argument(
        '-m', '--markers',
        type=str,
        help='Pytest marker expression (e.g., "not slow")'
    )

    parser.add_argument(
        '--no-html',
        action='store_true',
        help='Skip HTML coverage report generation'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Less verbose output'
    )

    parser.add_argument(
        '--fail-under',
        type=int,
        default=80,
        help='Minimum coverage percentage required (default: 80)'
    )

    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Run tests in parallel (requires pytest-xdist)'
    )

    parser.add_argument(
        '--durations',
        type=int,
        default=0,
        metavar='N',
        help='Show N slowest tests (default: 0 = disabled)'
    )

    parser.add_argument(
        'pytest_args',
        nargs='*',
        help='Additional arguments to pass to pytest'
    )

    args = parser.parse_args()

    # Check dependencies
    check_dependencies()

    # Run tests
    exit_code = run_tests(
        markers=args.markers,
        verbose=not args.quiet,
        html_report=not args.no_html,
        fail_under=args.fail_under,
        parallel=args.parallel,
        show_slowest=args.durations,
        extra_args=args.pytest_args
    )

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
