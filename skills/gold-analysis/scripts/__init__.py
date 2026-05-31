"""Gold Analysis Skill — path initialization and env loading.

Ensures all sibling scripts can be imported with flat imports regardless
of the working directory.
"""

import sys
from pathlib import Path

_scripts_dir = Path(__file__).resolve().parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

try:
    from dotenv import load_dotenv
    _env = _scripts_dir.parent / ".env"
    if _env.exists():
        load_dotenv(_env)
    else:
        load_dotenv()
except Exception:
    pass
