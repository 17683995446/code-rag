#!/usr/bin/env python3
import sys
from pathlib import Path

project_root = Path(__file__).parent
print(f"project_root: {project_root}")

project_dir = project_root / "flask_test_project"
print(f"project_dir: {project_dir}")
print(f"exists: {project_dir.exists()}")

py_files = list(project_dir.rglob("*.py"))
print(f"py_files: {len(py_files)}")

# 过滤
filtered = [
    f for f in py_files 
    if not any(skip in str(f) for skip in [
        '__pycache__', '.git', 'venv', 'node_modules', 
        'test', 'tests', '.venv', 'env'
    ])
]
print(f"filtered: {len(filtered)}")
