"""
Session save/load for RAO Report.
Stores program state as JSON next to the exe.
"""

import json
import os
import sys


def _sessions_dir() -> str:
    """Return path to sessions/ directory next to exe or script."""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    d = os.path.join(base, "sessions")
    os.makedirs(d, exist_ok=True)
    return d


def _session_filename(operator: str, month: str, year: str) -> str:
    """Generate session filename."""
    return f"{operator}_{month}_{year}.json"


def save_session(operator: str, month: str, year: str, programs: list[dict]) -> str:
    """
    Save session to JSON. Returns filepath.

    programs: list of dicts, each with keys:
        name (str), date (str), tracks (list of track dicts)
    """
    data = {
        "operator": operator,
        "month": month,
        "year": year,
        "programs": programs,
    }
    fname = _session_filename(operator, month, year)
    fpath = os.path.join(_sessions_dir(), fname)
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return fpath


def load_session(filepath: str) -> dict:
    """Load session from JSON file. Returns dict with operator, month, year, programs."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def list_sessions() -> list[dict]:
    """
    List available sessions.
    Returns list of dicts: {filename, filepath, operator, month, year, programs_count}
    """
    d = _sessions_dir()
    sessions = []
    for fname in sorted(os.listdir(d), reverse=True):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(d, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            sessions.append({
                "filename": fname,
                "filepath": fpath,
                "operator": data.get("operator", ""),
                "month": data.get("month", ""),
                "year": data.get("year", ""),
                "programs_count": len(data.get("programs", [])),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return sessions
