@echo off
chcp 65001 >nul
echo ========================================
echo  Сборка: Отчёт РАО (ВГТРК)
echo ========================================
echo.

REM Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo Установите Python 3.10+ с python.org
    pause
    exit /b 1
)

echo [1/3] Установка зависимостей...
pip install mutagen openpyxl pyinstaller tkinterdnd2

echo.
echo [2/3] Сборка .exe...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "RAO_Report" ^
    --add-data "extract_metadata.py;." ^
    --add-data "fill_form.py;." ^
    --hidden-import mutagen ^
    --hidden-import mutagen.mp3 ^
    --hidden-import mutagen.id3 ^
    --hidden-import mutagen.flac ^
    --hidden-import mutagen.wave ^
    --hidden-import mutagen.oggvorbis ^
    --hidden-import mutagen.aiff ^
    --hidden-import mutagen.asf ^
    --hidden-import mutagen.mp4 ^
    --hidden-import openpyxl ^
    --hidden-import tkinterdnd2 ^
    app.py

echo.
if exist "dist\RAO_Report.exe" (
    echo ========================================
    echo  ГОТОВО!
    echo  Файл: dist\RAO_Report.exe
    echo ========================================
    echo.
    echo Скопируйте RAO_Report.exe на рабочий компьютер.
    echo Drag-and-drop MP3 файлов работает двумя способами:
    echo   1. Перетащите файлы прямо в окно программы
    echo   2. Перетащите файлы на иконку RAO_Report.exe
) else (
    echo ОШИБКА: Сборка не удалась!
    echo Проверьте ошибки выше.
)

echo.
pause
