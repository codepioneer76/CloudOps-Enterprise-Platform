"""CloudOps Enterprise Platform application package."""

import sys
from pathlib import Path

# Ensure 'src' is in sys.path so both 'import app...' and 'import src.app...' resolve seamlessly
_src_dir = Path(__file__).resolve().parent.parent
if str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))
