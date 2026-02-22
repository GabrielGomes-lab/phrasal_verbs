# Phrasal Verb Highlighter

Python script to read subtitles (`.srt`) or text files and highlight phrasal verbs with different colors.

## Run

```bash
python3 highlight_phrasal_verbs.py episode.srt
```

## Save colored HTML

```bash
python3 highlight_phrasal_verbs.py episode.srt --mode html -o episode_phrasal_verbs.html
```

## Notes

- Supports common phrasal verbs and many separable forms (example: `pick it up`).
- Subtitle metadata lines (index/timestamps) are preserved.
- You can change color assignment with `--seed`.
