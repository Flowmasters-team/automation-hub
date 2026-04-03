"""
Извлечение метаданных из аудиофайлов для лицензионной формы ВГТРК.

Поддерживаемые форматы: MP3, WAV, FLAC, OGG, AIFF, WMA, M4A/AAC.
Зависимости: pip install mutagen
"""

import os
import sys
from pathlib import Path
from datetime import timedelta

try:
    from mutagen import File as MutagenFile
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3
    from mutagen.flac import FLAC
    from mutagen.wave import WAVE
    from mutagen.oggvorbis import OggVorbis
    from mutagen.aiff import AIFF
    from mutagen.asf import ASF
    from mutagen.mp4 import MP4
except ImportError:
    print("Ошибка: не установлена библиотека mutagen")
    print("Установите: pip install mutagen")
    sys.exit(1)


def format_duration(seconds: float) -> str:
    """Форматирует длительность в ЧЧ:ММ:СС или ММ:СС."""
    td = timedelta(seconds=int(seconds))
    total_seconds = int(td.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def _get_tag(audio, keys, default=""):
    """Извлекает значение тега, перебирая возможные ключи."""
    for key in keys:
        val = audio.get(key)
        if val:
            if isinstance(val, list):
                return str(val[0])
            return str(val)
    return default


def _get_id3_tag(tags, keys, default=""):
    """Извлекает значение из ID3-тегов."""
    if tags is None:
        return default
    for key in keys:
        val = tags.get(key)
        if val:
            return str(val)
    return default


def extract_metadata(filepath: str) -> dict:
    """
    Извлекает метаданные из аудиофайла.

    Возвращает словарь:
        - filename: имя файла
        - title: название трека
        - artist: исполнитель
        - album: альбом
        - year: год
        - genre: жанр
        - duration: длительность (форматированная строка)
        - duration_seconds: длительность в секундах
        - isrc: ISRC-код (если есть)
        - composer: композитор (если есть)
        - publisher: издатель (если есть)
        - copyright: копирайт (если есть)
    """
    filepath = os.path.abspath(filepath)
    if not os.path.isfile(filepath):
        return {"filename": os.path.basename(filepath), "error": "Файл не найден"}

    result = {
        "filename": os.path.basename(filepath),
        "filepath": filepath,
        "title": "",
        "artist": "",
        "album": "",
        "year": "",
        "genre": "",
        "duration": "",
        "duration_seconds": 0,
        "isrc": "",
        "composer": "",
        "publisher": "",
        "copyright": "",
    }

    try:
        audio = MutagenFile(filepath)
        if audio is None:
            result["error"] = "Не удалось прочитать файл (неизвестный формат)"
            return result

        # Длительность
        if audio.info and audio.info.length:
            result["duration_seconds"] = round(audio.info.length, 2)
            result["duration"] = format_duration(audio.info.length)

        ext = Path(filepath).suffix.lower()

        # ID3-based форматы (MP3, WAV, AIFF)
        if ext in (".mp3", ".wav", ".aiff", ".aif"):
            tags = audio.tags
            result["title"] = _get_id3_tag(tags, ["TIT2"])
            result["artist"] = _get_id3_tag(tags, ["TPE1"])
            result["album"] = _get_id3_tag(tags, ["TALB"])
            result["year"] = _get_id3_tag(tags, ["TDRC", "TYER"])
            result["genre"] = _get_id3_tag(tags, ["TCON"])
            result["composer"] = _get_id3_tag(tags, ["TCOM"])
            result["publisher"] = _get_id3_tag(tags, ["TPUB"])
            result["copyright"] = _get_id3_tag(tags, ["TCOP"])
            # ISRC
            isrc_frame = tags.get("TSRC") if tags else None
            if isrc_frame:
                result["isrc"] = str(isrc_frame)

        # Vorbis Comment (FLAC, OGG)
        elif ext in (".flac", ".ogg", ".oga"):
            result["title"] = _get_tag(audio, ["title"])
            result["artist"] = _get_tag(audio, ["artist"])
            result["album"] = _get_tag(audio, ["album"])
            result["year"] = _get_tag(audio, ["date", "year"])
            result["genre"] = _get_tag(audio, ["genre"])
            result["composer"] = _get_tag(audio, ["composer"])
            result["publisher"] = _get_tag(audio, ["publisher", "organization"])
            result["copyright"] = _get_tag(audio, ["copyright"])
            result["isrc"] = _get_tag(audio, ["isrc"])

        # MP4/M4A/AAC
        elif ext in (".m4a", ".mp4", ".aac", ".alac"):
            result["title"] = _get_tag(audio, ["\xa9nam"])
            result["artist"] = _get_tag(audio, ["\xa9ART"])
            result["album"] = _get_tag(audio, ["\xa9alb"])
            result["year"] = _get_tag(audio, ["\xa9day"])
            result["genre"] = _get_tag(audio, ["\xa9gen"])
            result["composer"] = _get_tag(audio, ["\xa9wrt"])
            result["copyright"] = _get_tag(audio, ["cprt"])

        # WMA/ASF
        elif ext in (".wma", ".asf"):
            result["title"] = _get_tag(audio, ["Title"])
            result["artist"] = _get_tag(audio, ["Author"])
            result["album"] = _get_tag(audio, ["WM/AlbumTitle"])
            result["year"] = _get_tag(audio, ["WM/Year"])
            result["genre"] = _get_tag(audio, ["WM/Genre"])
            result["composer"] = _get_tag(audio, ["WM/Composer"])
            result["publisher"] = _get_tag(audio, ["WM/Publisher"])
            result["copyright"] = _get_tag(audio, ["Copyright"])
            result["isrc"] = _get_tag(audio, ["WM/ISRC"])

        # Fallback — если title пустой, парсим имя файла
        if not result["title"]:
            stem = Path(filepath).stem
            # Пробуем шаблон "Исполнитель - Название"
            if " - " in stem:
                parts = stem.split(" - ", 1)
                if not result["artist"] and not result["composer"]:
                    result["artist"] = parts[0].strip()
                    result["composer"] = parts[0].strip()
                result["title"] = parts[1].strip()
            else:
                result["title"] = stem

    except Exception as e:
        result["error"] = f"Ошибка чтения: {e}"

    return result


def extract_from_list(file_paths: list[str]) -> list[dict]:
    """Извлекает метаданные из списка файлов."""
    results = []
    for path in file_paths:
        path = path.strip()
        if not path:
            continue
        meta = extract_metadata(path)
        results.append(meta)
    return results


def extract_from_directory(directory: str, recursive: bool = True) -> list[dict]:
    """Извлекает метаданные из всех аудиофайлов в директории."""
    audio_extensions = {
        ".mp3", ".wav", ".flac", ".ogg", ".oga", ".aiff", ".aif",
        ".m4a", ".mp4", ".aac", ".alac", ".wma", ".asf",
    }
    results = []
    dir_path = Path(directory)

    pattern = "**/*" if recursive else "*"
    for fpath in sorted(dir_path.glob(pattern)):
        if fpath.suffix.lower() in audio_extensions and fpath.is_file():
            meta = extract_metadata(str(fpath))
            results.append(meta)

    return results


# --- CLI ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование:")
        print(f"  python {sys.argv[0]} файл1.mp3 файл2.wav ...")
        print(f"  python {sys.argv[0]} --dir /path/to/music/")
        sys.exit(0)

    if sys.argv[1] == "--dir":
        directory = sys.argv[2] if len(sys.argv) > 2 else "."
        tracks = extract_from_directory(directory)
    else:
        tracks = extract_from_list(sys.argv[1:])

    for i, track in enumerate(tracks, 1):
        print(f"\n{'='*60}")
        print(f"  Трек #{i}: {track['filename']}")
        print(f"{'='*60}")
        if "error" in track:
            print(f"  ⚠ {track['error']}")
        print(f"  Название:    {track.get('title', '—')}")
        print(f"  Исполнитель: {track.get('artist', '—')}")
        print(f"  Альбом:      {track.get('album', '—')}")
        print(f"  Год:         {track.get('year', '—')}")
        print(f"  Жанр:        {track.get('genre', '—')}")
        print(f"  Длительность:{track.get('duration', '—')}")
        print(f"  Композитор:  {track.get('composer', '—')}")
        print(f"  Издатель:    {track.get('publisher', '—')}")
        print(f"  ISRC:        {track.get('isrc', '—')}")
        print(f"  Копирайт:    {track.get('copyright', '—')}")
