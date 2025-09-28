#!/usr/bin/env python3
"""
Print Statement Replacement Tool

Automatically replaces debug print statements with proper logger calls
in the DFakeSeeder codebase.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


def detect_class_name(file_content: str, line_number: int) -> str:
    """Detect the class name from the file content."""
    lines = file_content.split('\n')

    # Look backwards from the current line to find the class definition
    for i in range(line_number - 1, -1, -1):
        line = lines[i].strip()
        if line.startswith('class '):
            # Extract class name
            match = re.match(r'class\s+(\w+)', line)
            if match:
                return match.group(1)

    # If no class found, try to extract from filename
    return "UnknownClass"


def extract_class_from_print(print_statement: str) -> str:
    """Extract class name from print statement if it contains [ClassName] pattern."""
    match = re.search(r'\[(\w+)\]', print_statement)
    if match:
        return match.group(1)
    return None


def replace_print_statement(print_statement: str, class_name: str) -> str:
    """Replace a single print statement with logger call."""

    # Handle different print statement patterns
    if 'print(f"[' in print_statement:
        # Extract the message part after the class name and timestamp
        pattern = r'print\(f"\[.*?\]\s*(?:\[.*?\]\s*)?(.+?)"\)'
        match = re.search(pattern, print_statement)
        if match:
            message = match.group(1)
            # Clean up any remaining format strings
            message = re.sub(r'\{.*?\}', '', message)
            message = message.strip()
            if message:
                return f'logger.debug("{message}", "{class_name}")'

    elif 'print("[' in print_statement:
        # Handle simple print statements with [ClassName] prefix
        pattern = r'print\("\[.*?\]\s*(.+?)"\)'
        match = re.search(pattern, print_statement)
        if match:
            message = match.group(1)
            return f'logger.debug("{message}", "{class_name}")'

    elif 'print(f"' in print_statement:
        # Handle f-string prints without class prefix
        pattern = r'print\(f"(.+?)"\)'
        match = re.search(pattern, print_statement)
        if match:
            message = match.group(1)
            # Remove format strings
            message = re.sub(r'\{.*?\}', '...', message)
            return f'logger.debug("{message}", "{class_name}")'

    elif 'print("' in print_statement:
        # Handle simple string prints
        pattern = r'print\("(.+?)"\)'
        match = re.search(pattern, print_statement)
        if match:
            message = match.group(1)
            return f'logger.debug("{message}", "{class_name}")'

    # Fallback - comment out the print statement
    return f'# {print_statement.strip()}  # TODO: Convert to logger'


def has_logger_import(file_content: str) -> bool:
    """Check if file already imports logger."""
    return 'from lib.logger import logger' in file_content


def add_logger_import(file_content: str) -> str:
    """Add logger import to file if not present."""
    if has_logger_import(file_content):
        return file_content

    lines = file_content.split('\n')

    # Find the right place to insert the import
    insert_index = 0
    for i, line in enumerate(lines):
        if line.strip().startswith('import ') or line.strip().startswith('from '):
            insert_index = i + 1
        elif line.strip() == '' and insert_index > 0:
            break

    # Insert the logger import
    lines.insert(insert_index, 'from lib.logger import logger')
    return '\n'.join(lines)


def process_file(file_path: Path) -> bool:
    """Process a single file to replace print statements."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip files that don't have print statements
        if 'print(' not in content:
            return False

        # Add logger import if needed
        original_content = content
        content = add_logger_import(content)

        lines = content.split('\n')
        modified = False

        for i, line in enumerate(lines):
            if 'print(' in line and not line.strip().startswith('#'):
                # Detect class name
                class_name = detect_class_name(content, i + 1)

                # Try to extract class name from print statement
                extracted_class = extract_class_from_print(line)
                if extracted_class:
                    class_name = extracted_class

                # Replace the print statement
                new_line = replace_print_statement(line, class_name)

                # Preserve indentation
                indent = len(line) - len(line.lstrip())
                new_line = ' ' * indent + new_line

                if new_line != line:
                    lines[i] = new_line
                    modified = True

        if modified:
            new_content = '\n'.join(lines)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True

        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in the directory."""
    python_files = []

    for file_path in directory.rglob("*.py"):
        # Skip certain directories and files
        skip_patterns = [
            'plans/',
            'tools/',
            '__pycache__',
            '.git',
            'venv',
            'env',
            'build/',
            'dist/',
        ]

        if any(pattern in str(file_path) for pattern in skip_patterns):
            continue

        python_files.append(file_path)

    return python_files


def main():
    """Main function to process all files."""
    if len(sys.argv) > 1:
        target_dir = Path(sys.argv[1])
    else:
        # Default to the DFakeSeeder directory
        target_dir = Path(__file__).parent.parent

    print(f"Processing Python files in: {target_dir}")

    python_files = find_python_files(target_dir)
    print(f"Found {len(python_files)} Python files")

    processed_count = 0

    for file_path in python_files:
        print(f"Processing: {file_path.relative_to(target_dir)}")
        if process_file(file_path):
            processed_count += 1
            print(f"  ✅ Modified")
        else:
            print(f"  ⏭️ No changes needed")

    print(f"\nCompleted! Modified {processed_count} files")


if __name__ == "__main__":
    main()