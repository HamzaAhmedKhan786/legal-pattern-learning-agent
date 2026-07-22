"""Initialize the PostgreSQL schema for the production-shaped backend."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "web" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from database import database_url, init_database


if __name__ == "__main__":
    init_database()
    print(f"Database initialized: {database_url()}")
