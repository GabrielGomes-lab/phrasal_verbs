# Phrasal Verb Highlighter

Desktop + CLI Python app to read subtitles (`.srt`) or text files, highlight phrasal verbs, and export the result.

## 1) Desktop app (recommended)

Run the GUI:

```bash
python3 phrasal_verbs_gui.py
```

In the app:
- Click `Open subtitle` to upload your file
- Click `Run` to detect/highlight phrasal verbs
- Click `Export HTML` to save the colored output

## 2) Command line mode

Print ANSI-colored output in terminal:

```bash
python3 highlight_phrasal_verbs.py episode.srt
```

Export HTML:

```bash
python3 highlight_phrasal_verbs.py episode.srt --mode html -o episode_phrasal_verbs.html
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
- Subtitle metadata lines (index and timestamps) are preserved.
- Use the `Seed` field to change color assignment.
