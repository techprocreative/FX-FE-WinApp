#!/usr/bin/env python3
"""
Syntax validation for animation system files
Checks that all Python files have valid syntax without importing PyQt6
"""

import ast
import sys
import os

def check_syntax(file_path):
    """Check if a Python file has valid syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        # Parse the AST to check syntax
        ast.parse(source, filename=file_path)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"

def main():
    """Check syntax of all animation system files"""
    files_to_check = [
        'connector/ui/animation_system.py',
        'connector/ui/page_transitions.py',
        'connector/ui/loading_states.py',
        'connector/ui/components/modern_base.py',
        'connector/ui/design_system.py'
    ]
    
    print("Checking syntax of animation system files...")
    print("=" * 50)
    
    all_valid = True
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            valid, error = check_syntax(file_path)
            if valid:
                print(f"✓ {file_path}")
            else:
                print(f"✗ {file_path}: {error}")
                all_valid = False
        else:
            print(f"✗ {file_path}: File not found")
            all_valid = False
    
    print("=" * 50)
    
    if all_valid:
        print("🎉 All files have valid syntax!")
        return True
    else:
        print("❌ Some files have syntax errors.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)