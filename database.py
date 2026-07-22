# database.py
# ----------------------------------------------------------------------
# Simple SQLite wrapper for storing groups where the bot is admin.
# The chat_id column is UNIQUE, so duplicate groups can never be stored.
# ----------------------------------------------------------------------

import sqlite3
from typing import List, Tuple

DB_NAME = "bot.db"


def init_db() -> None:
    """Create the groups table if it doesn't already exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER UNIQUE NOT NULL,
            title TEXT NOT NULL,
            added_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


def add_group(chat_id: int, title: str) -> None:
    """Insert a group, or update its title if it already exists.
    The UNIQUE constraint on chat_id prevents duplicate rows."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO groups (chat_id, title) VALUES (?, ?)
        ON CONFLICT(chat_id) DO UPDATE SET title = excluded.title
        """,
        (chat_id, title),
    )
    conn.commit()
    conn.close()


def remove_group(chat_id: int) -> None:
    """Remove a group (e.g. bot was kicked or lost admin rights)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM groups WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()


def get_all_groups() -> List[Tuple[int, int, str]]:
    """Return all saved groups as (id, chat_id, title) tuples."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, chat_id, title FROM groups ORDER BY title COLLATE NOCASE")
    rows = cursor.fetchall()
    conn.close()
    return rows


def group_exists(chat_id: int) -> bool:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM groups WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None
