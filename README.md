# Phrasal Verb Highlighter

Desktop + CLI Python app to read subtitles (`.srt`) or text files, highlight phrasal verbs, and export the result.

## 1) Desktop app (recommended)

Run the GUI:

```bash
python3 phrasal_verbs_gui.py
```

In the app:
- Click `Open lyrics/subtitle` to upload your file (`.txt`, `.text`, `.md`, `.lrc`, `.log`, `.csv`, `.tsv`, `.srt`, `.ass`, `.vtt`)
- Optional: click `Paste lyrics` to load song lyrics directly from a text form
- Click `Run` to detect/highlight phrasal verbs
- The app now processes in the background with a progress indicator to keep the GUI responsive
- Optional: set `Sync ms` to shift subtitle timing (positive = later, negative = earlier)
- Click `Export SRT` to save a subtitle file for your video player
- Click `Export ASS` for reliable colored subtitles (recommended for most players)
- Optional: click `Export HTML` for browser review
- Optional: click `Export Report` to save a text report (counts + matched lines), useful for songs/lyrics review

## 2) Command line mode

Print ANSI-colored output in terminal:

```bash
python3 highlight_phrasal_verbs.py episode.srt
```

Export HTML:

```bash
python3 highlight_phrasal_verbs.py episode.srt --mode html -o episode_phrasal_verbs.html
```

Export SRT (subtitle file with color tags):

```bash
python3 highlight_phrasal_verbs.py episode.srt --mode srt -o episode_phrasal_verbs.srt
```

Export ASS (advanced styled subtitles, best compatibility for coloring):

```bash
python3 highlight_phrasal_verbs.py episode.srt --mode ass -o episode_phrasal_verbs.ass
```

Export a plain text report (counts + matched lines):

```bash
python3 highlight_phrasal_verbs.py lyrics.txt --mode report -o lyrics_report.txt
```

Shift subtitle timing by milliseconds while exporting:

```bash
python3 highlight_phrasal_verbs.py episode.srt --mode ass --shift-ms 350 -o episode_shifted.ass
```

## 3) Build executable (.exe)

On Windows (or with a Windows environment), install PyInstaller and build:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name phrasal-verbs-gui phrasal_verbs_gui.py
```

The executable will be created at:

```text
dist/phrasal-verbs-gui.exe
```

## Notes

- Includes common phrasal verbs and several separable patterns (`pick it up`, `put it away`, etc.).
- Detection now supports common present, past, and future forms (`take off`, `took off`, `will take off`, `is going to take off`).
- Highlighting is applied to the phrasal verb words only (e.g., `pick ... up` highlights `pick` and `up`).
- Subtitle metadata lines (index and timestamps) are preserved.
- SRT inline colors are player-dependent; some players ignore SRT styling completely.
- ASS export is the most reliable way to keep colored phrasal-verb highlights.
- Use the `Seed` field to change color assignment.
