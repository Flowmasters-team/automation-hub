"""
AcoustID fingerprint lookup — определение трека по аудиоотпечатку.

Требует fpcalc (Chromaprint) в PATH или рядом с exe.
Скачать: https://acoustid.org/chromaprint
"""

import json
import os
import subprocess
import shutil
import urllib.parse
import urllib.request
from urllib.error import URLError, HTTPError

# AcoustID API
ACOUSTID_URL = "https://api.acoustid.org/v2/lookup"
ACOUSTID_KEY = "cSpUJKpD"
MB_BASE = "https://musicbrainz.org/ws/2"
USER_AGENT = "RAO_Report/1.0 (flowmasters.ru)"


def _find_fpcalc() -> str | None:
    """Ищет fpcalc в PATH и стандартных местах."""
    # В PATH
    found = shutil.which("fpcalc") or shutil.which("fpcalc.exe")
    if found:
        return found

    # Рядом с exe / скриптом
    for base in [os.path.dirname(os.path.abspath(__file__)), os.getcwd()]:
        for name in ["fpcalc.exe", "fpcalc"]:
            path = os.path.join(base, name)
            if os.path.isfile(path):
                return path

    # Стандартные места Windows
    for p in [
        r"C:\Program Files\Chromaprint\fpcalc.exe",
        r"C:\Program Files (x86)\Chromaprint\fpcalc.exe",
        os.path.expanduser(r"~\fpcalc.exe"),
    ]:
        if os.path.isfile(p):
            return p

    return None


def is_available() -> bool:
    """Проверяет доступность fpcalc."""
    return _find_fpcalc() is not None


def _get_fingerprint(filepath: str) -> tuple[int, str] | None:
    """Запускает fpcalc и возвращает (duration, fingerprint)."""
    fpcalc = _find_fpcalc()
    if not fpcalc:
        return None

    try:
        result = subprocess.run(
            [fpcalc, "-json", filepath],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        return (int(data["duration"]), data["fingerprint"])
    except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, OSError):
        return None


def _get_json(url: str) -> dict | None:
    """GET JSON с User-Agent."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, HTTPError, OSError, json.JSONDecodeError):
        return None


def _lookup_composer_from_recording(recording_id: str) -> str:
    """Ищет композитора по MusicBrainz recording ID через work relations."""
    url = f"{MB_BASE}/recording/{recording_id}?inc=work-rels+artist-credits&fmt=json"
    data = _get_json(url)
    if not data:
        return ""

    # Ищем work relation → composer
    for rel in data.get("relations", []):
        if rel.get("type") == "performance" and "work" in rel:
            work_id = rel["work"].get("id")
            if work_id:
                work_url = f"{MB_BASE}/work/{work_id}?inc=artist-rels&fmt=json"
                work_data = _get_json(work_url)
                if work_data:
                    for wrel in work_data.get("relations", []):
                        if wrel.get("type") == "composer":
                            name = wrel.get("artist", {}).get("name", "")
                            if name:
                                return name
    return ""


def lookup_by_fingerprint(filepath: str) -> dict:
    """
    Определяет трек по аудиоотпечатку через AcoustID → MusicBrainz.

    Returns dict: {title, composer, artist} — пустые строки если не найдено.
    """
    empty = {"title": "", "composer": "", "artist": ""}

    fp = _get_fingerprint(filepath)
    if not fp:
        return empty

    duration, fingerprint = fp

    # Запрос к AcoustID
    params = urllib.parse.urlencode({
        "client": ACOUSTID_KEY,
        "duration": duration,
        "fingerprint": fingerprint,
        "meta": "recordings",
    })
    url = f"{ACOUSTID_URL}?{params}"
    data = _get_json(url)
    if not data or data.get("status") != "ok":
        return empty

    results = data.get("results", [])
    if not results:
        return empty

    # Берём лучший результат
    best = results[0]
    recordings = best.get("recordings", [])
    if not recordings:
        return empty

    rec = recordings[0]
    rec_id = rec.get("id", "")
    title = rec.get("title", "")

    # Artist
    artist = ""
    for credit in rec.get("artists", []):
        name = credit.get("name", "")
        if name:
            artist = name
            break

    # Composer через MusicBrainz work relations
    composer = ""
    if rec_id:
        import time
        time.sleep(1)  # rate limit MusicBrainz
        composer = _lookup_composer_from_recording(rec_id)

    return {
        "title": title,
        "composer": composer,
        "artist": artist,
    }
