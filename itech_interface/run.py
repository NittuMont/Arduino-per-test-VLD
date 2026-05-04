"""Entry-point script for PyInstaller."""
import sys
import os

# Ensure the src directory is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from itech_interface.main import main

if __name__ == "__main__":
    main()
