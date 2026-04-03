# RAO Report v2 — Design Spec

**Date:** 2026-04-04
**Status:** Approved
**Repo:** automation-hub, branch `claude/automate-licensing-form-MPjjp`
**Path:** `licensing-form/`

## Context

RAO Report v1 is a working desktop app (Python/Tkinter) that generates Excel reports for VGTRK music licensing (RAO). Sound engineers (Soshenko, Vaneev, Shakhov) use it monthly. Current limitation: no persistence between sessions, no composer knowledge base, weak tag search for Russian music.

## Changes

### 1. Session Save/Load (JSON)

**Problem:** Engineers fill 5-6 programs per month but submit the report once at month-end. Currently all data is lost when the app closes.

**Solution:**
- On app exit: auto-save current state to `sessions/{OPERATOR}_{month}_{year}.json`
- On app start: show dialog listing available sessions, user picks one to load (or starts fresh)
- JSON schema:
  ```json
  {
    "operator": "СОШЕНКО",
    "month": "апрель",
    "year": "2026",
    "programs": [
      {
        "name": "АМВ",
        "date": "03.04.26",
        "tracks": [
          {
            "title": "Bad Timing",
            "artist": "Immediate Music",
            "composer": "Immediate Music",
            "duration": "02:30",
            "duration_seconds": 150,
            "play_count": 5,
            "filepath": "C:/music/bad_timing.mp3",
            "filename": "bad_timing.mp3"
          }
        ]
      }
    ]
  }
  ```
- `sessions/` directory created next to exe on first save
- Prompt on exit: "Сохранить сессию?" (Да/Нет/Отмена)

**File:** New `session_manager.py` (~80 lines)

### 2. Program Templates

**Problem:** Same program names (АМВ, ЧС, Утро) typed repeatedly every month.

**Solution:**
- `templates.json` next to exe — list of strings: `["АМВ", "ЧС", "Утро", ...]`
- In each ProgramFrame: Combobox replacing the plain Entry for program name
  - Dropdown shows saved templates
  - User can type freely (editable combobox)
- Button "+" next to name field: saves current name to templates
- Auto-created with empty list on first run

**File:** Logic inline in `app.py` (~30 lines), `templates.json` data file

### 3. Composer Database (SQLite)

**Problem:** Same tracks appear across months. Engineers re-enter composers manually.

**Solution:**
- `composers.db` next to exe — SQLite with one table:
  ```sql
  CREATE TABLE composers (
    title TEXT NOT NULL,
    artist TEXT DEFAULT '',
    composer TEXT NOT NULL,
    UNIQUE(title, artist)
  );
  ```
- **Write:** On every report save, upsert all tracks that have a non-empty composer
- **Read:** On file add (`_add_files`), after extracting metadata, lookup `(title, artist)` in DB. If found, set composer automatically
- No UI for the database — it's invisible, grows silently

**File:** New `composer_db.py` (~60 lines)

### 4. Genius + MusicBrainz Combined Search

**Problem:** MusicBrainz has poor coverage of Russian music. Genius knows Russian artists well.

**Solution:** "Найти теги" button triggers a 3-tier cascade:
1. **Local DB** — check `composers.db` first (instant)
2. **Genius API** — search by title+artist, extract songwriter/composer from song metadata
   - Endpoint: `https://api.genius.com/search?q={title} {artist}`
   - Header: `Authorization: Bearer {token}`
   - From result: follow `song.api_path` → get `song.writer_artists[].name`
   - Token: `cvwa97pjJ_9998-FzRYF67cxcQzGYtUIXvF__OgteACQ1mt-6d_vMm97gpTMXojr`
3. **MusicBrainz** — existing logic (fallback)

"По слепку" remains a separate button (AcoustID + fpcalc).

**File:** New `genius_lookup.py` (~70 lines), modify `tag_lookup.py` to orchestrate cascade

### 5. Hotkeys

- `Ctrl+S` — trigger "Сохранить отчёт (.xlsx)"
- `Ctrl+N` — add new program (same as "+ Добавить передачу")
- `Delete` — remove selected track(s) from focused program

**File:** Bindings added in `app.py` `_build_ui()` (~10 lines)

## File Structure After Changes

```
licensing-form/
  app.py                  ← modified (templates combobox, hotkeys, session UI)
  fill_form.py            ← unchanged
  extract_metadata.py     ← unchanged
  tag_lookup.py           ← modified (orchestrate DB → Genius → MusicBrainz)
  fingerprint_lookup.py   ← unchanged
  genius_lookup.py        ← NEW (Genius API client)
  composer_db.py          ← NEW (SQLite read/write)
  session_manager.py      ← NEW (JSON save/load)
  fpcalc.exe              ← bundled binary
```

Runtime data (created next to exe):
```
sessions/                 ← JSON session files
composers.db              ← SQLite database
templates.json            ← program name templates
```

## Data Flow

```
MP3 files
  → extract_metadata.py (mutagen)
  → composer_db.py lookup (auto-fill composer if known)
  → UI (user edits, adds programs)
  → "Найти теги": composer_db → genius_lookup → tag_lookup (MusicBrainz)
  → "По слепку": fingerprint_lookup (AcoustID)
  → fill_form.py (Excel generation)
  → composer_db.py write (save new composers)
  → session_manager.py save (on exit)
```

## Out of Scope

- PDF export (future v3)
- Dark theme
- Drag-n-drop folders
- Calendar integration
- Music library indexing
