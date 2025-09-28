#!/usr/bin/env python3

import os
import re
import sys

def find_and_fix_broken_comments(file_path):
    """Find and fix broken comment blocks that start with '# print('."""

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False

    original_content = content

    # Pattern to match broken comment blocks
    # Matches: # print(  # TODO: Convert to logger
    #             f"some text"
    #         )
    pattern = r'([ \t]*)# print\(\s*# TODO: Convert to logger\s*\n((?:\1[ \t]+.*\n)*)\1\)'

    def replace_broken_comment(match):
        indent = match.group(1)
        lines = match.group(2).strip().split('\n')

        # Extract the message content from f-strings
        message_parts = []
        for line in lines:
            line = line.strip()
            if line.startswith('f"') and line.endswith('"'):
                # Remove f" and " and extract content
                content_part = line[2:-1]
                # Find class name pattern like [ClassName]
                class_match = re.search(r'\[(\w+)\]', content_part)
                if class_match:
                    class_name = class_match.group(1)
                    # Remove the [ClassName] part and timestamp
                    content_part = re.sub(r'\[.*?\]\s*\[.*?\]\s*', '', content_part)
                    content_part = re.sub(r'\[.*?\]\s*', '', content_part)
                message_parts.append(content_part)

        if message_parts:
            message = ''.join(message_parts)
            # Try to detect class name from message
            class_match = re.search(r'\[(\w+)\]', message)
            if class_match:
                class_name = class_match.group(1)
                message = re.sub(r'\[.*?\]\s*', '', message)
            else:
                # Try to infer from file path
                file_name = os.path.basename(file_path)
                if 'translation_manager' in file_name:
                    class_name = 'TranslationManager'
                elif 'torrents' in file_name:
                    class_name = 'Torrents'
                elif 'model' in file_name:
                    class_name = 'Model'
                elif 'view' in file_name:
                    class_name = 'View'
                else:
                    class_name = 'UnknownClass'

            return f'{indent}logger.debug("{message}", "{class_name}")'

        return match.group(0)  # Return original if can't parse

    # Apply the replacement
    content = re.sub(pattern, replace_broken_comment, content, flags=re.MULTILINE)

    # Check if content changed
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed broken comments in: {file_path}")
            return True
        except Exception as e:
            print(f"Error writing {file_path}: {e}")
            return False

    return False

def main():
    """Main function to process all Python files."""

    # Find all Python files in d_fake_seeder
    python_files = []
    for root, dirs, files in os.walk('d_fake_seeder'):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    print(f"Found {len(python_files)} Python files")

    modified_count = 0
    for file_path in python_files:
        if find_and_fix_broken_comments(file_path):
            modified_count += 1

    print(f"Modified {modified_count} files with broken comment fixes")

if __name__ == "__main__":
    main()