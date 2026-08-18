"""
Thin wrapper kept for Phase 3 docs/commands.

Prefer: python scripts/register_experiment.py ...
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from register_experiment import main


if __name__ == "__main__":
    raise SystemExit(main())
