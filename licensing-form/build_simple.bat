@echo off
chcp 65001 >nul
echo ========================================
echo  Сборка УПРОЩЁННАЯ (без drag-and-drop)
echo  Если tkinterdnd2 не ставится
echo ========================================
echo.

pip install mutagen openpyxl pyinstaller

echo.
echo Сборка .exe...
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
    app.py

echo.
if exist "dist\RAO_Report.exe" (
    echo ГОТОВО! Файл: dist\RAO_Report.exe
) else (
    echo ОШИБКА сборки!
)
pause
