"""
MusicBrainz lookup for track metadata (composer/artist).
Uses only stdlib — no extra dependencies.
Rate limit: 1 request/second (MusicBrainz requirement).
"""

import json
import time
import urllib.parse
import urllib.request
from urllib.error import URLError, HTTPError

MB_BASE = "https://musicbrainz.org/ws/2"
USER_AGENT = "RAO_Report/1.0 (flowmasters.ru)"
_last_request_time = 0.0


def _get(url: str) -> dict | None:
    """GET JSON from MusicBrainz with rate-limit and error handling."""
    global _last_request_time
    elapsed = time.monotonic() - _last_request_time
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            _last_request_time = time.monotonic()
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, HTTPError, OSError, json.JSONDecodeError):
        _last_request_time = time.monotonic()
        return None


def _extract_composer_from_relations(relations: list) -> str:
    """Pull composer name from work relations list."""
    for rel in relations:
        if rel.get("type") == "composer":
            artist = rel.get("artist", {})
            name = artist.get("name", "")
            if name:
                return name
    return ""


def _lookup_work_composer(work_id: str) -> str:
    """Fetch a work and extract its composer relation."""
    url = f"{MB_BASE}/work/{work_id}?inc=artist-rels&fmt=json"
    data = _get(url)
    if not data:
        return ""
    relations = data.get("relations", [])
    return _extract_composer_from_relations(relations)


def _build_queries(title: str, artist: str) -> list[str]:
    """Генерирует варианты поисковых запросов от точного к широкому."""
    queries = []
    if artist:
        # 1. Точный: "title" AND artist:"artist"
        queries.append(f'recording:"{title}" AND artist:"{artist}"')
        # 2. Без кавычек у artist
        queries.append(f'recording:"{title}" AND artist:{artist}')
        # 3. Просто title + artist как текст
        queries.append(f'{artist} {title}')
    # 4. Только title в кавычках
    queries.append(f'recording:"{title}"')
    # 5. Просто title как текст
    queries.append(title)
    return queries


def lookup_track(title: str, artist: str = "") -> dict:
    """
    Search MusicBrainz for a recording by title (and optionally artist).

    Returns dict with keys:
        composer (str) — composer name, empty string if not found
        artist   (str) — performer name, empty string if not found
    """
    if not title or not title.strip():
        return {"composer": "", "artist": ""}

    title_clean = title.strip()
    artist_clean = artist.strip() if artist else ""

    # Пробуем несколько стратегий поиска
    recordings = []
    for query in _build_queries(title_clean, artist_clean):
        params = urllib.parse.urlencode({"query": query, "limit": 5, "fmt": "json"})
        url = f"{MB_BASE}/recording?{params}"
        data = _get(url)
        if data:
            recordings = data.get("recordings", [])
            if recordings:
                break

    if not recordings:
        return {"composer": "", "artist": ""}

    # Pick the best match (highest score, first in list)
    best = recordings[0]

    # --- Artist (performer) ---
    artist_name = ""
    artist_credits = best.get("artist-credit", [])
    names = []
    for credit in artist_credits:
        if isinstance(credit, dict) and "artist" in credit:
            names.append(credit["artist"].get("name", ""))
    artist_name = ", ".join(n for n in names if n)

    # --- Composer via work relations ---
    composer_name = ""
    relations = best.get("relations", [])
    # Sometimes relations come inline; try them first
    if relations:
        composer_name = _extract_composer_from_relations(relations)

    # If no inline relations, fetch from work
    if not composer_name:
        works = best.get("works", [])
        # works can also appear under relations of type "performance"
        work_id = None
        for rel in best.get("relations", []):
            if rel.get("type") == "performance" and "work" in rel:
                work_id = rel["work"].get("id")
                break
        if work_id:
            composer_name = _lookup_work_composer(work_id)

    # Fallback: if composer still empty, try fetching the full recording with inc
    if not composer_name:
        rec_id = best.get("id", "")
        if rec_id:
            url2 = f"{MB_BASE}/recording/{rec_id}?inc=work-rels+artist-credits&fmt=json"
            full = _get(url2)
            if full:
                for rel in full.get("relations", []):
                    if rel.get("type") == "performance" and "work" in rel:
                        work_id = rel["work"].get("id")
                        if work_id:
                            composer_name = _lookup_work_composer(work_id)
                        break

    return {
        "composer": composer_name,
        "artist": artist_name,
    }
