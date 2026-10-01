# Copyright (C) 2024-2026 Arash Kazemi
# SPDX-License-Identifier: AGPL-3.0-only
import os
from pathlib import Path
import sqlite3
from contextlib import closing

def create_database(db_path=None):
    """Initialize a new database without replacing existing data or schema."""
    path = Path(db_path or os.getenv("DB_PATH", str(Path(__file__).resolve().parent / "plates.db")))
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS plates (id INTEGER PRIMARY KEY AUTOINCREMENT,
              name TEXT, 
              name2 TEXT, 
              plate TEXT, 
              time_detected TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

if __name__ == "__main__":
    create_database()
