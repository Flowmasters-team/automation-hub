"""
Genius API lookup for song composers/writers.
Better coverage of Russian music than MusicBrainz.
"""

import json
import urllib.parse
import urllib.request
from urllib.error import URLError, HTTPError

GENIUS_TOKEN = "cvwa97pjJ_9998-FzRYF67cxcQzGYtUIXvF__OgteACQ1mt-6d_vMm97gpTMXojr"
GENIUS_BASE = "https://api.genius.com"
USER_AGENT = "RAO_Report/1.0 (flowmasters.ru)"


def _get(url: str) -> dict | None:
    """GET JSON from Genius API."""
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Authorization": f"Bearer {GENIUS_TOKEN}",
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("response", data)
    except (URLError, HTTPError, OSError, json.JSONDecodeError):
        return None


def lookup_genius(title: str, artist: str = "") -> dict:
    """
    Search Genius for a song by title (and optionally artist).

    Returns dict:
        composer (str) — writer/composer name(s), empty if not found
        artist   (str) — primary artist, empty if not found
    """
    if not title or not title.strip():
        return {"composer": "", "artist": ""}

    query = f"{artist} {title}".strip() if artist else title.strip()
    params = urllib.parse.urlencode({"q": query})
    url = f"{GENIUS_BASE}/search?{params}"

    data = _get(url)
    if not data:
        return {"composer": "", "artist": ""}

    hits = data.get("hits", [])
    if not hits:
        return {"composer": "", "artist": ""}

    # Take best hit
    song = hits[0].get("result", {})
    artist_name = song.get("primary_artist", {}).get("name", "")

    # Get full song info for writer_artists
    song_path = song.get("api_path", "")
    composer_name = ""
    if song_path:
        song_data = _get(f"{GENIUS_BASE}{song_path}")
        if song_data:
            song_detail = song_data.get("song", {})
            writers = song_detail.get("writer_artists", [])
            writer_names = [w.get("name", "") for w in writers if w.get("name")]
            if writer_names:
                composer_name = ", ".join(writer_names)

    return {
        "composer": composer_name,
        "artist": artist_name,
    }
