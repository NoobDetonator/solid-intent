"""Pytest bootstrap: make the workspace ``scripts`` package importable."""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
