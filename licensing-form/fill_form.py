"""
Заполнение лицензионной формы ВГТРК данными из аудиофайлов.

Генерирует Excel-таблицу (.xlsx) с метаданными треков.
Может также заполнять шаблон Word (.docx), если он предоставлен.

Зависимости: pip install mutagen openpyxl
Опционально:  pip install python-docx  (для Word-шаблонов)
"""

import os
import sys
from datetime import datetime

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
except ImportError:
    print("Ошибка: не установлена библиотека openpyxl")
    print("Установите: pip install openpyxl")
    sys.exit(1)

from extract_metadata import extract_from_list, extract_from_directory


# Колонки таблицы — настройте под вашу форму
COLUMNS = [
    ("№ п/п", 6),
    ("Название произведения", 35),
    ("Автор / Исполнитель", 30),
    ("Композитор", 25),
    ("Альбом", 25),
    ("Год", 8),
    ("Хронометраж", 14),
    ("ISRC", 18),
    ("Издатель / Лейбл", 25),
    ("Копирайт", 25),
    ("Жанр", 15),
    ("Примечание", 20),
]


def create_excel(tracks: list[dict], output_path: str, program_name: str = ""):
    """Создаёт Excel-файл с лицензионной таблицей."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Лицензионная форма"

    # --- Стили ---
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    cell_font = Font(name="Arial", size=10)
    cell_alignment = Alignment(vertical="top", wrap_text=True)
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )

    # --- Заголовок документа ---
    row = 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=len(COLUMNS))
    title_cell = ws.cell(row=row, column=1, value="МУЗЫКАЛЬНАЯ СПРАВКА")
    title_cell.font = Font(name="Arial", size=14, bold=True)
    title_cell.alignment = Alignment(horizontal="center")

    row = 2
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=len(COLUMNS))
    subtitle = f"Программа: {program_name}" if program_name else ""
    date_str = datetime.now().strftime("%d.%m.%Y")
    ws.cell(row=row, column=1, value=f"{subtitle}   Дата: {date_str}".strip())
    ws.cell(row=row, column=1).font = Font(name="Arial", size=10)
    ws.cell(row=row, column=1).alignment = Alignment(horizontal="center")

    # --- Заголовки колонок ---
    row = 4
    for col_idx, (col_name, col_width) in enumerate(COLUMNS, 1):
        cell = ws.cell(row=row, column=col_idx, value=col_name)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment
        cell.border = thin_border
        ws.column_dimensions[cell.column_letter].width = col_width

    # --- Данные ---
    for i, track in enumerate(tracks, 1):
        row = 4 + i
        values = [
            i,
            track.get("title", ""),
            track.get("artist", ""),
            track.get("composer", ""),
            track.get("album", ""),
            track.get("year", ""),
            track.get("duration", ""),
            track.get("isrc", ""),
            track.get("publisher", ""),
            track.get("copyright", ""),
            track.get("genre", ""),
            "",  # Примечание — заполняется вручную
        ]
        for col_idx, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col_idx, value=val)
            cell.font = cell_font
            cell.alignment = cell_alignment
            cell.border = thin_border

    # --- Итоговая строка ---
    row = 4 + len(tracks) + 1
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
    ws.cell(row=row, column=1, value=f"Итого треков: {len(tracks)}")
    ws.cell(row=row, column=1).font = Font(name="Arial", size=10, bold=True)

    # Суммарный хронометраж
    total_seconds = sum(t.get("duration_seconds", 0) for t in tracks)
    hours, remainder = divmod(int(total_seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    total_dur = f"{hours:02d}:{minutes:02d}:{secs:02d}"
    ws.cell(row=row, column=7, value=total_dur)
    ws.cell(row=row, column=7).font = Font(name="Arial", size=10, bold=True)
    ws.cell(row=row, column=7).border = thin_border

    # --- Подписи ---
    row += 2
    ws.cell(row=row, column=1, value="Звукорежиссёр: _________________ / _________________ /")
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
    row += 1
    ws.cell(row=row, column=1, value="Дата: ________________")

    # --- Сохранение ---
    wb.save(output_path)
    return output_path


# --- CLI ---
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Заполнение лицензионной музыкальной формы ВГТРК"
    )
    parser.add_argument(
        "files", nargs="*",
        help="Пути к аудиофайлам"
    )
    parser.add_argument(
        "--dir", "-d",
        help="Директория с аудиофайлами"
    )
    parser.add_argument(
        "--output", "-o", default="music_license_form.xlsx",
        help="Имя выходного файла (по умолчанию: music_license_form.xlsx)"
    )
    parser.add_argument(
        "--program", "-p", default="",
        help="Название программы/передачи"
    )
    parser.add_argument(
        "--list", "-l",
        help="Текстовый файл со списком путей (по одному на строку)"
    )

    args = parser.parse_args()

    # Собираем список файлов
    file_paths = []
    if args.files:
        file_paths.extend(args.files)
    if args.list:
        with open(args.list, encoding="utf-8") as f:
            file_paths.extend(line.strip() for line in f if line.strip())
    if args.dir:
        tracks = extract_from_directory(args.dir)
    else:
        if not file_paths:
            parser.print_help()
            print("\nОшибка: укажите файлы, директорию (--dir) или список (--list)")
            sys.exit(1)
        tracks = extract_from_list(file_paths)

    if not tracks:
        print("Не найдено аудиофайлов.")
        sys.exit(1)

    # Выводим что нашли
    print(f"\nНайдено треков: {len(tracks)}")
    for i, t in enumerate(tracks, 1):
        status = "OK" if "error" not in t else t["error"]
        print(f"  {i}. {t.get('artist', '?')} — {t.get('title', '?')} [{t.get('duration', '?')}] ({status})")

    # Генерируем Excel
    output = create_excel(tracks, args.output, args.program)
    print(f"\nФорма сохранена: {os.path.abspath(output)}")
