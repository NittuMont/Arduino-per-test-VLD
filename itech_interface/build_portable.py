"""Standalone entry point used by PyInstaller.

PyInstaller cannot follow relative imports inside a package directly,
so this tiny wrapper imports the package and calls main().
"""

import sys
import os

# Ensure the src/ directory is on the path so the package can be found
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from itech_interface.main import main  # noqa: E402

if __name__ == "__main__":
    main()
