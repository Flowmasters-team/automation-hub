"""
GUI-приложение: Отчёт РАО — автозаполнение музыкальной формы ВГТРК.

Перетащи MP3-файлы в окно, заполни название передачи — получи Excel.
Собирается в .exe через PyInstaller (см. build.bat).
"""

import os
import sys
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from extract_metadata import extract_metadata
from fill_form import create_rao_report, _fmt_duration, _multiply_duration

# Попытка подключить drag-and-drop (tkinterdnd2)
# Если не установлен — работаем через кнопку "Добавить файлы"
DND_AVAILABLE = False
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    pass

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".aiff", ".aif", ".m4a", ".wma"}

# Русские названия месяцев
MONTHS_RU = [
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
]


class RaoReportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Отчёт РАО — ВГТРК")
        self.root.geometry("900x650")
        self.root.minsize(750, 500)

        # Данные
        self.tracks = []  # список словарей с метаданными

        self._build_ui()

        # Drag-and-drop
        if DND_AVAILABLE:
            self.file_list.drop_target_register(DND_FILES)
            self.file_list.dnd_bind("<<Drop>>", self._on_drop)
            self.drop_zone.drop_target_register(DND_FILES)
            self.drop_zone.dnd_bind("<<Drop>>", self._on_drop)

        # Если файлы переданы через аргументы (перетаскивание на .exe)
        if len(sys.argv) > 1:
            files = [f for f in sys.argv[1:] if os.path.isfile(f)]
            if files:
                self._add_files(files)

    def _build_ui(self):
        # --- Верхняя панель: параметры ---
        params_frame = ttk.LabelFrame(self.root, text="Параметры отчёта", padding=10)
        params_frame.pack(fill="x", padx=10, pady=(10, 5))

        # Строка 1: Название передачи + Дата эфира
        row1 = ttk.Frame(params_frame)
        row1.pack(fill="x", pady=2)

        ttk.Label(row1, text="Передача:").pack(side="left")
        self.program_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.program_var, width=40).pack(side="left", padx=(5, 20))

        ttk.Label(row1, text="Дата эфира:").pack(side="left")
        self.date_var = tk.StringVar(value=datetime.now().strftime("%d.%m.%y"))
        ttk.Entry(row1, textvariable=self.date_var, width=12).pack(side="left", padx=(5, 20))

        ttk.Label(row1, text="Кол-во исп.:").pack(side="left")
        self.play_count_var = tk.StringVar(value="1")
        ttk.Entry(row1, textvariable=self.play_count_var, width=5).pack(side="left", padx=5)

        # Строка 2: Месяц + Год
        row2 = ttk.Frame(params_frame)
        row2.pack(fill="x", pady=2)

        ttk.Label(row2, text="Месяц:").pack(side="left")
        self.month_var = tk.StringVar(value=MONTHS_RU[datetime.now().month - 1])
        month_combo = ttk.Combobox(row2, textvariable=self.month_var, values=MONTHS_RU, width=12, state="readonly")
        month_combo.pack(side="left", padx=(5, 20))

        ttk.Label(row2, text="Год:").pack(side="left")
        self.year_var = tk.StringVar(value=datetime.now().strftime("%Y"))
        ttk.Entry(row2, textvariable=self.year_var, width=8).pack(side="left", padx=5)

        # --- Зона drag-and-drop / кнопки ---
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(fill="x", padx=10, pady=5)

        ttk.Button(btn_frame, text="Добавить файлы", command=self._browse_files).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Добавить папку", command=self._browse_folder).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Удалить выбранные", command=self._remove_selected).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Очистить всё", command=self._clear_all).pack(side="left", padx=5)

        # --- Drop zone label ---
        if DND_AVAILABLE:
            self.drop_zone = ttk.Label(
                self.root,
                text="Перетащите MP3-файлы сюда",
                relief="groove",
                anchor="center",
                padding=8,
            )
        else:
            self.drop_zone = ttk.Label(
                self.root,
                text="Используйте кнопки выше для добавления файлов  (для drag-and-drop установите tkinterdnd2)",
                relief="groove",
                anchor="center",
                padding=8,
            )
        self.drop_zone.pack(fill="x", padx=10, pady=(0, 5))

        # --- Таблица файлов ---
        columns = ("num", "title", "composer", "duration", "filename")
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        self.file_list = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=scrollbar.set,
            selectmode="extended",
        )
        scrollbar.config(command=self.file_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.file_list.pack(fill="both", expand=True)

        self.file_list.heading("num", text="#")
        self.file_list.heading("title", text="Название")
        self.file_list.heading("composer", text="Композитор")
        self.file_list.heading("duration", text="Длительность")
        self.file_list.heading("filename", text="Файл")

        self.file_list.column("num", width=40, anchor="center")
        self.file_list.column("title", width=250)
        self.file_list.column("composer", width=200)
        self.file_list.column("duration", width=90, anchor="center")
        self.file_list.column("filename", width=250)

        # --- Статус + кнопка генерации ---
        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill="x", padx=10, pady=(0, 10))

        self.status_var = tk.StringVar(value="Добавьте аудиофайлы для начала работы")
        ttk.Label(bottom_frame, textvariable=self.status_var).pack(side="left")

        ttk.Button(
            bottom_frame,
            text="Сохранить отчёт (.xlsx)",
            command=self._generate_report,
        ).pack(side="right")

    def _on_drop(self, event):
        """Обработка drag-and-drop файлов."""
        # tkinterdnd2 возвращает пути, разделённые пробелами
        # Пути с пробелами обёрнуты в {}
        raw = event.data
        files = self._parse_dnd_paths(raw)
        self._add_files(files)

    @staticmethod
    def _parse_dnd_paths(data: str) -> list[str]:
        """Парсит строку путей из tkinterdnd2 (обрабатывает {} и пробелы)."""
        paths = []
        i = 0
        while i < len(data):
            if data[i] == "{":
                end = data.index("}", i)
                paths.append(data[i + 1 : end])
                i = end + 2  # skip } and space
            elif data[i] == " ":
                i += 1
            else:
                end = data.find(" ", i)
                if end == -1:
                    end = len(data)
                paths.append(data[i:end])
                i = end + 1
        return paths

    def _browse_files(self):
        files = filedialog.askopenfilenames(
            title="Выберите аудиофайлы",
            filetypes=[
                ("Аудиофайлы", "*.mp3 *.wav *.flac *.ogg *.m4a *.wma *.aiff"),
                ("MP3", "*.mp3"),
                ("Все файлы", "*.*"),
            ],
        )
        if files:
            self._add_files(list(files))

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку с музыкой")
        if folder:
            files = []
            for f in sorted(os.listdir(folder)):
                ext = os.path.splitext(f)[1].lower()
                if ext in AUDIO_EXTENSIONS:
                    files.append(os.path.join(folder, f))
            if files:
                self._add_files(files)
            else:
                messagebox.showinfo("Пусто", "В папке не найдено аудиофайлов")

    def _add_files(self, file_paths: list[str]):
        """Добавляет файлы в таблицу, извлекая метаданные."""
        added = 0
        for fpath in file_paths:
            fpath = fpath.strip()
            if not fpath or not os.path.isfile(fpath):
                continue
            ext = os.path.splitext(fpath)[1].lower()
            if ext not in AUDIO_EXTENSIONS:
                continue

            # Проверяем дубликат
            already = any(t["filepath"] == os.path.abspath(fpath) for t in self.tracks)
            if already:
                continue

            meta = extract_metadata(fpath)
            self.tracks.append(meta)
            added += 1

        if added > 0:
            self._refresh_table()
            self.status_var.set(f"Треков: {len(self.tracks)}  |  Добавлено: {added}")

    def _remove_selected(self):
        selected = self.file_list.selection()
        if not selected:
            return
        indices = sorted(
            [self.file_list.index(item) for item in selected],
            reverse=True,
        )
        for idx in indices:
            self.tracks.pop(idx)
        self._refresh_table()
        self.status_var.set(f"Треков: {len(self.tracks)}")

    def _clear_all(self):
        self.tracks.clear()
        self._refresh_table()
        self.status_var.set("Список очищен")

    def _refresh_table(self):
        """Перерисовывает таблицу из self.tracks."""
        self.file_list.delete(*self.file_list.get_children())
        for i, t in enumerate(self.tracks, 1):
            composer = t.get("artist", "") or t.get("composer", "")
            self.file_list.insert("", "end", values=(
                i,
                t.get("title", ""),
                composer,
                t.get("duration", ""),
                t.get("filename", ""),
            ))

    def _generate_report(self):
        """Генерирует Excel-файл с отчётом РАО."""
        if not self.tracks:
            messagebox.showwarning("Нет данных", "Добавьте аудиофайлы перед генерацией отчёта")
            return

        program_name = self.program_var.get().strip() or "Без названия"
        air_date = self.date_var.get().strip()
        month = self.month_var.get().strip()
        year = self.year_var.get().strip()

        try:
            play_count = int(self.play_count_var.get().strip())
        except ValueError:
            play_count = 1

        # Формируем структуру программы
        program_tracks = []
        for t in self.tracks:
            composer = t.get("artist", "") or t.get("composer", "")
            program_tracks.append({
                "title": t.get("title", ""),
                "composer": composer,
                "lyricist": "",
                "duration_seconds": t.get("duration_seconds", 0),
                "play_count": play_count,
                "genre": "пьеса",
                "performer": "инстр. Анс",
            })

        program = {
            "name": program_name,
            "air_date": air_date,
            "tracks": program_tracks,
        }

        # Диалог сохранения
        default_name = f"Отчёт_{month}_{year}_{program_name}.xlsx"
        # Убираем недопустимые символы из имени файла
        default_name = re.sub(r'[<>:"/\\|?*]', '_', default_name)

        output_path = filedialog.asksaveasfilename(
            title="Сохранить отчёт",
            defaultextension=".xlsx",
            initialfile=default_name,
            filetypes=[("Excel", "*.xlsx"), ("Все файлы", "*.*")],
        )
        if not output_path:
            return

        try:
            create_rao_report(
                [program],
                output_path,
                month=month,
                year=year,
            )
            self.status_var.set(f"Отчёт сохранён: {output_path}")
            messagebox.showinfo(
                "Готово!",
                f"Отчёт сохранён:\n{output_path}\n\n"
                f"Треков: {len(self.tracks)}\n"
                f"Передача: {program_name}\n"
                f"Дата эфира: {air_date}",
            )
            # Открываем файл в системе
            os.startfile(output_path) if sys.platform == "win32" else None
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить отчёт:\n{e}")


def main():
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    app = RaoReportApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
