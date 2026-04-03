"""
GUI-приложение: Отчёт РАО — автозаполнение музыкальной формы ВГТРК.

Несколько передач в одном отчёте за месяц. Выбор оператора (Сошенко/Ванеев/Шахов).
Собирается в .exe через PyInstaller (см. build.bat).
"""

import os
import sys
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from extract_metadata import extract_metadata
from fill_form import create_rao_report

# Попытка подключить drag-and-drop (tkinterdnd2)
DND_AVAILABLE = False
try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    DND_AVAILABLE = True
except ImportError:
    pass

AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".aiff", ".aif", ".m4a", ".wma"}

MONTHS_RU = [
    "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь",
]

OPERATORS = ["СОШЕНКО", "ВАНЕЕВ", "ШАХОВ"]


class ProgramFrame:
    """Фрейм одной передачи с треками."""

    def __init__(self, parent, app, index):
        self.app = app
        self.index = index
        self.tracks = []

        self.frame = ttk.LabelFrame(parent, text=f"Передача {index + 1}", padding=5)
        self.frame.pack(fill="both", expand=True, pady=(0, 5))

        # --- Параметры передачи ---
        params = ttk.Frame(self.frame)
        params.pack(fill="x", pady=(0, 5))

        ttk.Label(params, text="Название:").pack(side="left")
        self.name_var = tk.StringVar()
        ttk.Entry(params, textvariable=self.name_var, width=35).pack(side="left", padx=(5, 15))

        ttk.Label(params, text="Дата эфира:").pack(side="left")
        self.date_var = tk.StringVar(value=datetime.now().strftime("%d.%m.%y"))
        ttk.Entry(params, textvariable=self.date_var, width=10).pack(side="left", padx=(5, 15))

        ttk.Label(params, text="Кол-во исп.:").pack(side="left")
        self.play_count_var = tk.StringVar(value="1")
        ttk.Entry(params, textvariable=self.play_count_var, width=4).pack(side="left", padx=(5, 10))

        ttk.Button(params, text="Удалить передачу", command=self._remove).pack(side="right")

        # --- Кнопки файлов ---
        btn_frame = ttk.Frame(self.frame)
        btn_frame.pack(fill="x", pady=(0, 3))

        ttk.Button(btn_frame, text="Добавить файлы", command=self._browse_files).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Добавить папку", command=self._browse_folder).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Удалить выбранные", command=self._remove_selected).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Очистить треки", command=self._clear_tracks).pack(side="left", padx=5)

        # --- Таблица ---
        columns = ("num", "title", "composer", "duration", "filename")
        tree_frame = ttk.Frame(self.frame)
        tree_frame.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        self.tree = ttk.Treeview(
            tree_frame, columns=columns, show="headings",
            yscrollcommand=scrollbar.set, selectmode="extended", height=5,
        )
        scrollbar.config(command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        self.tree.heading("num", text="#")
        self.tree.heading("title", text="Название")
        self.tree.heading("composer", text="Композитор")
        self.tree.heading("duration", text="Длительность")
        self.tree.heading("filename", text="Файл")

        self.tree.column("num", width=30, anchor="center")
        self.tree.column("title", width=220)
        self.tree.column("composer", width=180)
        self.tree.column("duration", width=80, anchor="center")
        self.tree.column("filename", width=200)

        # Drag-and-drop
        if DND_AVAILABLE:
            self.tree.drop_target_register(DND_FILES)
            self.tree.dnd_bind("<<Drop>>", self._on_drop)

    def _on_drop(self, event):
        files = _parse_dnd_paths(event.data)
        self._add_files(files)

    def _browse_files(self):
        files = filedialog.askopenfilenames(
            title="Выберите аудиофайлы",
            filetypes=[
                ("Аудиофайлы", "*.mp3 *.wav *.flac *.ogg *.m4a *.wma *.aiff"),
                ("Все файлы", "*.*"),
            ],
        )
        if files:
            self._add_files(list(files))

    def _browse_folder(self):
        folder = filedialog.askdirectory(title="Выберите папку с музыкой")
        if folder:
            files = [
                os.path.join(folder, f) for f in sorted(os.listdir(folder))
                if os.path.splitext(f)[1].lower() in AUDIO_EXTENSIONS
            ]
            if files:
                self._add_files(files)
            else:
                messagebox.showinfo("Пусто", "В папке не найдено аудиофайлов")

    def _add_files(self, file_paths):
        added = 0
        for fpath in file_paths:
            fpath = fpath.strip()
            if not fpath or not os.path.isfile(fpath):
                continue
            if os.path.splitext(fpath)[1].lower() not in AUDIO_EXTENSIONS:
                continue
            if any(t["filepath"] == os.path.abspath(fpath) for t in self.tracks):
                continue
            meta = extract_metadata(fpath)
            self.tracks.append(meta)
            added += 1
        if added > 0:
            self._refresh_table()
            self.app.update_status()

    def _remove_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        for idx in sorted([self.tree.index(item) for item in selected], reverse=True):
            self.tracks.pop(idx)
        self._refresh_table()
        self.app.update_status()

    def _clear_tracks(self):
        self.tracks.clear()
        self._refresh_table()
        self.app.update_status()

    def _remove(self):
        self.app.remove_program(self.index)

    def _refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for i, t in enumerate(self.tracks, 1):
            composer = t.get("artist", "") or t.get("composer", "")
            self.tree.insert("", "end", values=(
                i, t.get("title", ""), composer,
                t.get("duration", ""), t.get("filename", ""),
            ))

    def get_program_data(self, play_count_override=None):
        play_count = play_count_override
        if play_count is None:
            try:
                play_count = int(self.play_count_var.get().strip())
            except ValueError:
                play_count = 1

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

        return {
            "name": self.name_var.get().strip() or "Без названия",
            "air_date": self.date_var.get().strip(),
            "tracks": program_tracks,
        }

    def total_tracks(self):
        return len(self.tracks)


def _parse_dnd_paths(data: str) -> list[str]:
    paths = []
    i = 0
    while i < len(data):
        if data[i] == "{":
            end = data.index("}", i)
            paths.append(data[i + 1:end])
            i = end + 2
        elif data[i] == " ":
            i += 1
        else:
            end = data.find(" ", i)
            if end == -1:
                end = len(data)
            paths.append(data[i:end])
            i = end + 1
    return paths


class RaoReportApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Отчёт РАО — ВГТРК")
        self.root.geometry("950x700")
        self.root.minsize(800, 550)

        self.programs = []  # list of ProgramFrame

        self._build_ui()
        self._add_program()  # одна передача по умолчанию

        # Если файлы переданы через аргументы
        if len(sys.argv) > 1:
            files = [f for f in sys.argv[1:] if os.path.isfile(f)]
            if files and self.programs:
                self.programs[0]._add_files(files)

    def _build_ui(self):
        # --- Верхняя панель ---
        top = ttk.LabelFrame(self.root, text="Параметры отчёта", padding=10)
        top.pack(fill="x", padx=10, pady=(10, 5))

        row1 = ttk.Frame(top)
        row1.pack(fill="x", pady=2)

        ttk.Label(row1, text="Оператор:").pack(side="left")
        self.operator_var = tk.StringVar(value=OPERATORS[0])
        ttk.Combobox(
            row1, textvariable=self.operator_var, values=OPERATORS,
            width=14, state="readonly",
        ).pack(side="left", padx=(5, 20))

        ttk.Label(row1, text="Месяц:").pack(side="left")
        self.month_var = tk.StringVar(value=MONTHS_RU[datetime.now().month - 1])
        ttk.Combobox(
            row1, textvariable=self.month_var, values=MONTHS_RU,
            width=12, state="readonly",
        ).pack(side="left", padx=(5, 20))

        ttk.Label(row1, text="Год:").pack(side="left")
        self.year_var = tk.StringVar(value=datetime.now().strftime("%Y"))
        ttk.Entry(row1, textvariable=self.year_var, width=6).pack(side="left", padx=5)

        # --- Кнопка добавить передачу ---
        btn_bar = ttk.Frame(self.root)
        btn_bar.pack(fill="x", padx=10, pady=5)

        ttk.Button(btn_bar, text="+ Добавить передачу", command=self._add_program).pack(side="left")

        # --- Контейнер для передач (с прокруткой) ---
        self.canvas = tk.Canvas(self.root)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.programs_frame = ttk.Frame(self.canvas)

        self.programs_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.create_window((0, 0), window=self.programs_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=(0, 5))
        self.scrollbar.pack(side="left", fill="y", pady=(0, 5), padx=(0, 10))

        # Прокрутка колёсиком
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1 * (e.delta // 120), "units"))

        # --- Низ: статус + кнопка ---
        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x", padx=10, pady=(0, 10))

        self.status_var = tk.StringVar(value="Добавьте передачи и аудиофайлы")
        ttk.Label(bottom, textvariable=self.status_var).pack(side="left")

        ttk.Button(bottom, text="Сохранить отчёт (.xlsx)", command=self._generate_report).pack(side="right")

    def _add_program(self):
        idx = len(self.programs)
        pf = ProgramFrame(self.programs_frame, self, idx)
        self.programs.append(pf)
        self.update_status()

    def remove_program(self, index):
        if len(self.programs) <= 1:
            messagebox.showinfo("Нельзя", "Должна быть хотя бы одна передача")
            return
        pf = self.programs[index]
        pf.frame.destroy()
        self.programs.pop(index)
        # Перенумеровать
        for i, p in enumerate(self.programs):
            p.index = i
            p.frame.config(text=f"Передача {i + 1}")
        self.update_status()

    def update_status(self):
        total = sum(p.total_tracks() for p in self.programs)
        self.status_var.set(f"Передач: {len(self.programs)}  |  Треков: {total}")

    def _generate_report(self):
        all_programs = []
        total_tracks = 0
        for pf in self.programs:
            if pf.total_tracks() == 0:
                continue
            prog = pf.get_program_data()
            all_programs.append(prog)
            total_tracks += len(prog["tracks"])

        if not all_programs:
            messagebox.showwarning("Нет данных", "Добавьте аудиофайлы хотя бы в одну передачу")
            return

        operator = self.operator_var.get()
        month = self.month_var.get().strip()
        year = self.year_var.get().strip()
        month_upper = month.upper()

        default_name = f"Отчёт за {month_upper} {year} {operator}.xlsx"
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
                all_programs, output_path,
                month=month_upper, year=year,
            )
            self.status_var.set(f"Отчёт сохранён: {output_path}")
            messagebox.showinfo(
                "Готово!",
                f"Отчёт сохранён:\n{output_path}\n\n"
                f"Передач: {len(all_programs)}\n"
                f"Треков: {total_tracks}\n"
                f"Оператор: {operator}",
            )
            if sys.platform == "win32":
                os.startfile(output_path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить отчёт:\n{e}")


def main():
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    RaoReportApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
