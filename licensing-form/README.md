# Автозаполнение лицензионной музыкальной формы

Скрипт для звукорежиссёров: извлекает метаданные из аудиофайлов и генерирует Excel-таблицу (музыкальную справку).

## Установка

```bash
pip install -r requirements.txt
```

## Использование

```bash
# Несколько файлов
python fill_form.py track1.mp3 track2.wav track3.flac

# Вся папка с музыкой
python fill_form.py --dir /path/to/music/

# Список из файла
python fill_form.py --list tracklist.txt

# С названием программы и выходным файлом
python fill_form.py --dir ./music/ --program "Вести" --output vesti_music.xlsx
```

## Что извлекается

| Поле | Источник |
|------|----------|
| Название | ID3: TIT2 / Vorbis: title |
| Исполнитель | ID3: TPE1 / Vorbis: artist |
| Композитор | ID3: TCOM / Vorbis: composer |
| Альбом | ID3: TALB / Vorbis: album |
| Год | ID3: TDRC / Vorbis: date |
| Хронометраж | audio.info.length |
| ISRC | ID3: TSRC / Vorbis: isrc |
| Издатель | ID3: TPUB / Vorbis: publisher |
| Копирайт | ID3: TCOP / Vorbis: copyright |
| Жанр | ID3: TCON / Vorbis: genre |

## Поддерживаемые форматы

MP3, WAV, FLAC, OGG, AIFF, M4A/AAC, WMA
