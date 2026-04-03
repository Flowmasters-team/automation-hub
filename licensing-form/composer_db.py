"""
SQLite database for known composer mappings.
DB file lives next to the exe/script. Grows silently over time.
"""

import os
import sys
import sqlite3


def _db_path() -> str:
    """Return path to composers.db next to exe or script."""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "composers.db")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.execute("""
        CREATE TABLE IF NOT EXISTS composers (
            title TEXT NOT NULL,
            artist TEXT DEFAULT '',
            composer TEXT NOT NULL,
            UNIQUE(title, artist)
        )
    """)
    conn.commit()
    return conn


def lookup(title: str, artist: str = "") -> str:
    """Return composer for title+artist pair, or empty string."""
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT composer FROM composers WHERE title = ? AND artist = ?",
            (title.strip(), artist.strip()),
        ).fetchone()
        if row:
            return row[0]
        # Fallback: try title-only match
        row = conn.execute(
            "SELECT composer FROM composers WHERE title = ? ORDER BY rowid DESC LIMIT 1",
            (title.strip(),),
        ).fetchone()
        return row[0] if row else ""
    finally:
        conn.close()


def save_many(tracks: list[dict]) -> int:
    """Save composer mappings from a list of track dicts. Returns count saved."""
    conn = _connect()
    saved = 0
    try:
        for t in tracks:
            title = t.get("title", "").strip()
            composer = t.get("composer", "").strip()
            if not title or not composer:
                continue
            artist = t.get("artist", "").strip()
            conn.execute(
                "INSERT OR REPLACE INTO composers (title, artist, composer) VALUES (?, ?, ?)",
                (title, artist, composer),
            )
            saved += 1
        conn.commit()
        return saved
    finally:
        conn.close()
