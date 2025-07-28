"""
setup_paths.py - Ensures the project root and src directory are in the Python path.
"""
import os
import sys
from pathlib import Path

# Get the project root (the directory containing this file)
PROJECT_ROOT = Path(__file__).parent.absolute()
SRC_DIR = PROJECT_ROOT / 'src'

# Add to Python path if not already there
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Print debug information if needed
DEBUG = True
if DEBUG:
    print("\n=== Python Path Configuration ===")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Source directory: {SRC_DIR}")
    print("\nCurrent Python path:")
    for p in sys.path:
        print(f"- {p}")
    print("\nContents of src directory:")
    try:
        for f in SRC_DIR.iterdir():
            print(f"- {f.name} (dir: {f.is_dir()})")
    except Exception as e:
        print(f"Could not list src directory: {e}")
    print("\n=== End of Python Path Configuration ===\n")
