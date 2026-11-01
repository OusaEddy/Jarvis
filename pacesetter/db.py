"""Pacesetter's database: One SQLite file on this laptop."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_FILE = Path(__file__).parent.parent / "pacesetter.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tasks(
    id           INTEGER PRIMARY KEY,
    name         TEXT NOT NULL,
    minutes      INTEGER NOT NULL CHECK(minutes > 0),
    deadline     TEXT,
    importance   TEXT NOT NULL,
    focus        TEXT NOT NULL,
    done         INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS work_log(
    id           INTEGER PRIMARY KEY,
    task_id      INTEGER NOT NULL REFERENCES tasks(id),
    day          TEXT NOT NULL,
    minutes      INTEGER NOT NULL CHECK(minutes > 0),
    logged_at    TEXT NOT NULL
);
"""

@contextmanager
def open_db(path: Path = DB_FILE):
    """Open the database for one job: Everything is saved or nothing is."""
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    try:
        with connection:
            yield connection
    finally:
        connection.close()