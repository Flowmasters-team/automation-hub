# RAO Report v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add session persistence, composer database, program templates, Genius API search, and hotkeys to the RAO Report desktop app.

**Architecture:** Three new standalone modules (session_manager, composer_db, genius_lookup) plus integration into existing app.py and tag_lookup.py. All data files stored next to exe. No new UI dependencies.

**Tech Stack:** Python 3.12, Tkinter/ttk, SQLite3 (stdlib), JSON (stdlib), Genius REST API, urllib (stdlib)

---

### Task 1: Composer Database (composer_db.py)

**Files:**
- Create: `licensing-form/composer_db.py`

No dependencies on other tasks — pure data layer.

- [ ] **Step 1: Create composer_db.py**

```python
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
```

- [ ] **Step 2: Verify module loads**

Run: `cd /c/Users/user/automation-hub/licensing-form && python -c "from composer_db import lookup, save_many; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Quick smoke test**

Run:
```bash
python -c "
from composer_db import lookup, save_many
save_many([{'title': 'Test Song', 'artist': 'Test Artist', 'composer': 'Test Composer'}])
print(lookup('Test Song', 'Test Artist'))
print(lookup('Test Song'))
"
```
Expected: `Test Composer` printed twice. Delete `composers.db` after test.

- [ ] **Step 4: Commit**

```bash
git add licensing-form/composer_db.py
git commit -m "feat: add composer database (SQLite)"
```

---

### Task 2: Genius API Lookup (genius_lookup.py)

**Files:**
- Create: `licensing-form/genius_lookup.py`

- [ ] **Step 1: Create genius_lookup.py**

```python
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
```

- [ ] **Step 2: Verify import**

Run: `python -c "from genius_lookup import lookup_genius; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Test with known track**

Run:
```bash
python -c "
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from genius_lookup import lookup_genius
r = lookup_genius('Улыбайся', 'IOWA')
print(f'composer: {r[\"composer\"]}')
print(f'artist: {r[\"artist\"]}')
"
```
Expected: Non-empty composer (Genius knows IOWA).

- [ ] **Step 4: Commit**

```bash
git add licensing-form/genius_lookup.py
git commit -m "feat: add Genius API lookup for composers"
```

---

### Task 3: Session Manager (session_manager.py)

**Files:**
- Create: `licensing-form/session_manager.py`

- [ ] **Step 1: Create session_manager.py**

```python
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
    Returns list of dicts: {filename, filepath, operator, month, year}
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
```

- [ ] **Step 2: Verify import**

Run: `python -c "from session_manager import save_session, load_session, list_sessions; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add licensing-form/session_manager.py
git commit -m "feat: add session manager (JSON save/load)"
```

---

### Task 4: Rewire tag_lookup.py — cascade search (DB → Genius → MusicBrainz)

**Files:**
- Modify: `licensing-form/tag_lookup.py`

- [ ] **Step 1: Add cascade function to tag_lookup.py**

Add at the end of `tag_lookup.py`, after the existing `lookup_track` function:

```python
def lookup_cascade(title: str, artist: str = "") -> dict:
    """
    3-tier composer search: local DB → Genius → MusicBrainz.
    Returns dict with composer, artist keys.
    """
    from composer_db import lookup as db_lookup
    from genius_lookup import lookup_genius

    # 1. Local database
    composer = db_lookup(title, artist)
    if composer:
        return {"composer": composer, "artist": artist}

    # 2. Genius API
    result = lookup_genius(title, artist)
    if result.get("composer"):
        return result

    # 3. MusicBrainz (existing)
    return lookup_track(title, artist)
```

- [ ] **Step 2: Verify import**

Run: `python -c "from tag_lookup import lookup_cascade; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add licensing-form/tag_lookup.py
git commit -m "feat: add cascade search (DB → Genius → MusicBrainz)"
```

---

### Task 5: Integrate everything into app.py

**Files:**
- Modify: `licensing-form/app.py`

This is the largest task. Changes:
1. Add imports for new modules
2. Replace program name Entry with editable Combobox + "+" button (templates)
3. Wire `_add_files` to check composer_db
4. Wire `_find_tags_async` to use `lookup_cascade` instead of `lookup_track`
5. Wire `_generate_report` to save composers to DB
6. Add session save on exit, load on start
7. Add hotkeys

- [ ] **Step 1: Add imports at top of app.py**

After the existing imports (line 29), add:

```python
from tag_lookup import lookup_cascade
from session_manager import save_session, load_session, list_sessions
from composer_db import lookup as db_lookup_composer, save_many as db_save_composers
```

- [ ] **Step 2: Add template loading helper**

After the `OPERATORS` list (around line 53), add:

```python
def _templates_path() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), "templates.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates.json")

def _load_templates() -> list[str]:
    try:
        with open(_templates_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _save_templates(templates: list[str]):
    import json as _json
    with open(_templates_path(), "w", encoding="utf-8") as f:
        _json.dump(templates, f, ensure_ascii=False, indent=2)
```

Also add `import json` to the top imports if not already present.

- [ ] **Step 3: Replace program name Entry with Combobox + "+" button in ProgramFrame.__init__**

Replace these lines in `__init__` (around line 71-73):

```python
        ttk.Label(params, text="Название:").pack(side="left")
        self.name_var = tk.StringVar()
        ttk.Entry(params, textvariable=self.name_var, width=40).pack(side="left", padx=(5, 15))
```

With:

```python
        ttk.Label(params, text="Название:").pack(side="left")
        self.name_var = tk.StringVar()
        self.name_combo = ttk.Combobox(
            params, textvariable=self.name_var, values=_load_templates(), width=37,
        )
        self.name_combo.pack(side="left", padx=(5, 3))
        ttk.Button(params, text="+", width=2, command=self._save_template).pack(side="left", padx=(0, 15))
```

Add the `_save_template` method to ProgramFrame (after `_remove`):

```python
    def _save_template(self):
        """Save current program name to templates."""
        name = self.name_var.get().strip()
        if not name:
            return
        templates = _load_templates()
        if name not in templates:
            templates.append(name)
            _save_templates(templates)
            # Update all comboboxes
            for pf in self.app.programs:
                pf.name_combo["values"] = templates
```

- [ ] **Step 4: Wire _add_files to check composer_db**

In `ProgramFrame._add_files`, after `meta["play_count"] = 1` (line 432), add:

```python
            # Auto-fill composer from database
            if not meta.get("composer"):
                db_composer = db_lookup_composer(meta.get("title", ""), meta.get("artist", ""))
                if db_composer:
                    meta["composer"] = db_composer
```

- [ ] **Step 5: Wire _find_tags_async to use lookup_cascade**

In `ProgramFrame._find_tags_async`, in the worker function, replace:

```python
                result = lookup_track(title, artist_hint)
```

With:

```python
                result = lookup_cascade(title, artist_hint)
```

- [ ] **Step 6: Wire _generate_report to save composers to DB**

In `RaoReportApp._generate_report`, after `create_rao_report(...)` succeeds (around line 653, inside the try block), add:

```python
            # Save composers to database for future auto-fill
            all_tracks = []
            for prog in all_programs:
                for t in prog["tracks"]:
                    all_tracks.append(t)
            db_save_composers(all_tracks)
```

- [ ] **Step 7: Add session save on exit**

In `RaoReportApp.__init__`, after `self._add_program()` (line 520), add:

```python
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
```

Add `_on_close` method to `RaoReportApp`:

```python
    def _on_close(self):
        """Prompt to save session on exit."""
        if any(pf.total_tracks() > 0 for pf in self.programs):
            answer = messagebox.askyesnocancel(
                "Сохранить сессию?",
                "Сохранить текущую сессию перед выходом?",
            )
            if answer is None:  # Cancel
                return
            if answer:  # Yes
                self._save_current_session()
        self.root.destroy()

    def _save_current_session(self):
        """Save current state to JSON."""
        operator = self.operator_var.get()
        month = self.month_var.get()
        year = self.year_var.get()
        programs_data = []
        for pf in self.programs:
            programs_data.append({
                "name": pf.name_var.get().strip(),
                "date": pf.get_date(),
                "tracks": [
                    {
                        "title": t.get("title", ""),
                        "artist": t.get("artist", ""),
                        "composer": t.get("composer", ""),
                        "duration": t.get("duration", ""),
                        "duration_seconds": t.get("duration_seconds", 0),
                        "play_count": t.get("play_count", 1),
                        "filepath": t.get("filepath", ""),
                        "filename": t.get("filename", ""),
                    }
                    for t in pf.tracks
                ],
            })
        path = save_session(operator, month, year, programs_data)
        self.status_var.set(f"Сессия сохранена: {path}")
```

- [ ] **Step 8: Add session load on start**

In `RaoReportApp.__init__`, after `self._add_program()` and the WM_DELETE_WINDOW binding, add:

```python
        # Offer to load a previous session
        self.root.after(100, self._offer_load_session)
```

Add `_offer_load_session` and `_load_session` methods:

```python
    def _offer_load_session(self):
        """Show dialog to load a previous session on startup."""
        sessions = list_sessions()
        if not sessions:
            return
        names = [f"{s['operator']} — {s['month']} {s['year']} ({s['programs_count']} перед.)" for s in sessions]
        dialog = tk.Toplevel(self.root)
        dialog.title("Загрузить сессию")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Доступные сессии:").pack(pady=(10, 5))
        listbox = tk.Listbox(dialog, height=10)
        for name in names:
            listbox.insert(tk.END, name)
        listbox.pack(fill="both", expand=True, padx=10)

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill="x", padx=10, pady=10)

        def load_selected():
            sel = listbox.curselection()
            if sel:
                self._load_session(sessions[sel[0]]["filepath"])
            dialog.destroy()

        ttk.Button(btn_frame, text="Загрузить", command=load_selected).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Новая сессия", command=dialog.destroy).pack(side="right", padx=5)

    def _load_session(self, filepath: str):
        """Load session from file, replacing current state."""
        data = load_session(filepath)
        self.operator_var.set(data.get("operator", OPERATORS[0]))
        self.month_var.set(data.get("month", MONTHS_RU[0]))
        self.year_var.set(data.get("year", datetime.now().strftime("%Y")))

        # Remove all current programs
        for pf in self.programs[:]:
            pf.frame.destroy()
        self.programs.clear()

        # Create programs from session
        for prog_data in data.get("programs", []):
            self._add_program()
            pf = self.programs[-1]
            pf.name_var.set(prog_data.get("name", ""))
            pf.date_var.set(prog_data.get("date", ""))
            for t in prog_data.get("tracks", []):
                t.setdefault("play_count", 1)
                pf.tracks.append(t)
            pf._refresh_table()

        if not self.programs:
            self._add_program()
        self.update_status()
        self.status_var.set(f"Сессия загружена: {os.path.basename(filepath)}")
```

- [ ] **Step 9: Add hotkeys**

In `RaoReportApp._build_ui`, after the mousewheel binding (around line 582), add:

```python
        # Hotkeys
        self.root.bind_all("<Control-s>", lambda e: self._generate_report())
        self.root.bind_all("<Control-n>", lambda e: self._add_program())
        self.root.bind_all("<Delete>", self._delete_selected_track)
```

Add `_delete_selected_track` method to `RaoReportApp`:

```python
    def _delete_selected_track(self, event=None):
        """Delete selected track from the focused program's table."""
        focus = self.root.focus_get()
        for pf in self.programs:
            if pf.tree == focus or focus and str(focus).startswith(str(pf.tree)):
                selected = pf.tree.selection()
                if selected:
                    for idx in sorted([pf.tree.index(item) for item in selected], reverse=True):
                        pf.tracks.pop(idx)
                    pf._refresh_table()
                    self.update_status()
                return
```

- [ ] **Step 10: Verify app starts**

Run: `python -c "from app import main; print('imports OK')"`
Expected: `imports OK`

- [ ] **Step 11: Commit**

```bash
git add licensing-form/app.py
git commit -m "feat: integrate sessions, templates, composer DB, cascade search, hotkeys"
```

---

### Task 6: Rebuild exe and push

**Files:**
- Rebuild: `licensing-form/dist/RAO_Report.exe`

- [ ] **Step 1: Clean build with all new modules**

```bash
cd /c/Users/user/automation-hub/licensing-form
rm -rf build dist
python -m PyInstaller --onefile --windowed --name "RAO_Report" \
    --add-data "extract_metadata.py;." \
    --add-data "fill_form.py;." \
    --add-data "tag_lookup.py;." \
    --add-data "fingerprint_lookup.py;." \
    --add-data "genius_lookup.py;." \
    --add-data "composer_db.py;." \
    --add-data "session_manager.py;." \
    --add-binary "fpcalc.exe;." \
    --hidden-import mutagen --hidden-import mutagen.mp3 \
    --hidden-import mutagen.id3 --hidden-import mutagen.flac \
    --hidden-import mutagen.wave --hidden-import mutagen.oggvorbis \
    --hidden-import mutagen.aiff --hidden-import mutagen.asf \
    --hidden-import mutagen.mp4 --hidden-import openpyxl \
    --hidden-import tkinterdnd2 --hidden-import tkcalendar \
    --hidden-import babel.numbers --hidden-import sv_ttk \
    --exclude-module ttkbootstrap \
    app.py
```

- [ ] **Step 2: Verify exe size is reasonable**

Run: `ls -lh dist/RAO_Report.exe`
Expected: ~46-50 MB (same range as v1)

- [ ] **Step 3: Push all changes**

```bash
cd /c/Users/user/automation-hub
git add licensing-form/dist/RAO_Report.exe
git commit -m "build: RAO Report v2 exe with sessions, composer DB, Genius, templates"
git push origin claude/automate-licensing-form-MPjjp
```
