#!/usr/bin/env python3
"""
Generate a test file from a source Python file.

Usage:
    python generate_test_file.py path/to/source.py
    python generate_test_file.py path/to/source.py --output tests/test_source.py
"""

import argparse
import ast
import sys
from pathlib import Path
from typing import List, Tuple


def extract_functions_and_classes(source_path: Path) -> Tuple[List[str], List[str]]:
    """
    Extract function and class names from a Python source file.

    Args:
        source_path: Path to the Python source file

    Returns:
        Tuple of (function_names, class_names)
    """
    with open(source_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        print(f"Error parsing {source_path}: {e}", file=sys.stderr)
        return [], []

    functions = []
    classes = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Only include top-level functions (not methods)
            if not any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)):
                if not node.name.startswith('_'):  # Skip private functions
                    functions.append(node.name)

        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith('_'):  # Skip private classes
                classes.append(node.name)

    return functions, classes


def generate_test_content(
    source_path: Path,
    functions: List[str],
    classes: List[str]
) -> str:
    """
    Generate pytest test file content.

    Args:
        source_path: Path to the source file
        functions: List of function names to test
        classes: List of class names to test

    Returns:
        Generated test file content
    """
    module_name = source_path.stem
    import_path = str(source_path).replace('/', '.').replace('\\', '.').replace('.py', '')

    content = f'''"""
Tests for {module_name}.

Generated test file for {source_path.name}
"""

import pytest
from {import_path} import (
'''

    # Add imports
    all_items = functions + classes
    if all_items:
        for item in all_items:
            content += f'    {item},\n'
    else:
        content += '    # Add your imports here\n'

    content += ')\n\n'

    # Generate test functions
    if functions:
        content += '\n# ============================================================================\n'
        content += '# Function tests\n'
        content += '# ============================================================================\n\n'

        for func in functions:
            content += f'''def test_{func}():
    """Test {func} function."""
    # Arrange
    # TODO: Set up test data

    # Act
    # result = {func}()

    # Assert
    # TODO: Add assertions
    pass


'''

    # Generate test classes
    if classes:
        content += '\n# ============================================================================\n'
        content += '# Class tests\n'
        content += '# ============================================================================\n\n'

        for cls in classes:
            content += f'''class Test{cls}:
    """Tests for {cls} class."""

    @pytest.fixture
    def {cls.lower()}_instance(self):
        """Fixture providing a {cls} instance."""
        # TODO: Initialize {cls} instance
        return {cls}()

    def test_{cls.lower()}_creation(self, {cls.lower()}_instance):
        """Test {cls} instance creation."""
        assert {cls.lower()}_instance is not None

    # TODO: Add more test methods for {cls}


'''

    # Add parametrized test examples
    content += '''# ============================================================================
# Parametrized tests (examples)
# ============================================================================

# @pytest.mark.parametrize("input,expected", [
#     (1, 2),
#     (2, 4),
#     (3, 6),
# ])
# def test_parametrized_example(input, expected):
#     """Example parametrized test."""
#     assert input * 2 == expected


# ============================================================================
# Fixtures (examples)
# ============================================================================

# @pytest.fixture
# def sample_data():
#     """Provide sample data for tests."""
#     return {"key": "value"}
'''

    return content


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate pytest test file from Python source file'
    )
    parser.add_argument(
        'source_file',
        type=str,
        help='Path to the source Python file'
    )
    parser.add_argument(
        '-o', '--output',
        type=str,
        help='Output path for the test file (default: tests/test_<source>.py)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing test file'
    )

    args = parser.parse_args()

    # Validate source file
    source_path = Path(args.source_file)
    if not source_path.exists():
        print(f"Error: Source file not found: {source_path}", file=sys.stderr)
        sys.exit(1)

    if not source_path.suffix == '.py':
        print(f"Error: Source file must be a Python file (.py)", file=sys.stderr)
        sys.exit(1)

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = Path('tests') / f'test_{source_path.name}'

    # Check if output file exists
    if output_path.exists() and not args.force:
        print(f"Error: Test file already exists: {output_path}", file=sys.stderr)
        print("Use --force to overwrite", file=sys.stderr)
        sys.exit(1)

    # Create output directory if needed
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Extract functions and classes
    print(f"Analyzing {source_path}...")
    functions, classes = extract_functions_and_classes(source_path)

    print(f"Found {len(functions)} functions and {len(classes)} classes")

    # Generate test content
    test_content = generate_test_content(source_path, functions, classes)

    # Write test file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(test_content)

    print(f"[OK] Generated test file: {output_path}")
    print(f"\nNext steps:")
    print(f"1. Review and customize the generated tests")
    print(f"2. Run tests: pytest {output_path}")
    print(f"3. Add specific test cases and assertions")


if __name__ == '__main__':
    main()
