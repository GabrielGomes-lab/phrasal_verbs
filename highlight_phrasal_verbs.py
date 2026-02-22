#!/usr/bin/env python3
"""Highlight phrasal verbs in subtitle files (.srt) or plain text."""

from __future__ import annotations

import argparse
import html
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TIMESTAMP_RE = re.compile(
    r"^\d{2}:\d{2}:\d{2},\d{3}\s+-->\s+\d{2}:\d{2}:\d{2},\d{3}(?:\s+.*)?$"
)

ANSI_COLORS = [
    "\033[91m",  # red
    "\033[92m",  # green
    "\033[93m",  # yellow
    "\033[94m",  # blue
    "\033[95m",  # magenta
    "\033[96m",  # cyan
    "\033[31m",  # dark red
    "\033[32m",  # dark green
    "\033[33m",  # brown/yellow
    "\033[34m",  # dark blue
]
ANSI_RESET = "\033[0m"

HTML_COLORS = [
    "#ef4444",
    "#22c55e",
    "#f59e0b",
    "#3b82f6",
    "#a855f7",
    "#14b8a6",
    "#e11d48",
    "#84cc16",
    "#f97316",
    "#0ea5e9",
]


@dataclass(frozen=True)
class PhrasalVerb:
    base: str
    separable: bool = False

    @property
    def words(self) -> tuple[str, ...]:
        return tuple(self.base.split())


# Small, practical starter list. You can extend this easily.
PHRASAL_VERBS: list[PhrasalVerb] = [
    PhrasalVerb("ask out", separable=True),
    PhrasalVerb("back down"),
    PhrasalVerb("back up", separable=True),
    PhrasalVerb("blow up", separable=True),
    PhrasalVerb("break down"),
    PhrasalVerb("break in"),
    PhrasalVerb("break into"),
    PhrasalVerb("break off"),
    PhrasalVerb("break out"),
    PhrasalVerb("break up", separable=True),
    PhrasalVerb("bring about"),
    PhrasalVerb("bring back", separable=True),
    PhrasalVerb("bring up", separable=True),
    PhrasalVerb("call off", separable=True),
    PhrasalVerb("calm down"),
    PhrasalVerb("carry on"),
    PhrasalVerb("catch up"),
    PhrasalVerb("check in"),
    PhrasalVerb("check out", separable=True),
    PhrasalVerb("cheer up", separable=True),
    PhrasalVerb("clean up", separable=True),
    PhrasalVerb("come across"),
    PhrasalVerb("come back"),
    PhrasalVerb("come in"),
    PhrasalVerb("come on"),
    PhrasalVerb("come out"),
    PhrasalVerb("come over"),
    PhrasalVerb("come up"),
    PhrasalVerb("cut off", separable=True),
    PhrasalVerb("do over", separable=True),
    PhrasalVerb("dress up"),
    PhrasalVerb("drop by"),
    PhrasalVerb("drop off", separable=True),
    PhrasalVerb("eat out"),
    PhrasalVerb("end up"),
    PhrasalVerb("fall apart"),
    PhrasalVerb("fall behind"),
    PhrasalVerb("fall out"),
    PhrasalVerb("figure out", separable=True),
    PhrasalVerb("fill in", separable=True),
    PhrasalVerb("fill out", separable=True),
    PhrasalVerb("find out"),
    PhrasalVerb("get along"),
    PhrasalVerb("get around"),
    PhrasalVerb("get away"),
    PhrasalVerb("get away with"),
    PhrasalVerb("get back"),
    PhrasalVerb("get by"),
    PhrasalVerb("get in"),
    PhrasalVerb("get off"),
    PhrasalVerb("get on"),
    PhrasalVerb("get out"),
    PhrasalVerb("get over"),
    PhrasalVerb("get up"),
    PhrasalVerb("give away", separable=True),
    PhrasalVerb("give back", separable=True),
    PhrasalVerb("give in"),
    PhrasalVerb("give up", separable=True),
    PhrasalVerb("go on"),
    PhrasalVerb("go out"),
    PhrasalVerb("go over"),
    PhrasalVerb("grow up"),
    PhrasalVerb("hand in", separable=True),
    PhrasalVerb("hang on"),
    PhrasalVerb("hang out"),
    PhrasalVerb("hold on"),
    PhrasalVerb("keep on"),
    PhrasalVerb("kick out", separable=True),
    PhrasalVerb("knock out", separable=True),
    PhrasalVerb("let down", separable=True),
    PhrasalVerb("let in", separable=True),
    PhrasalVerb("look after"),
    PhrasalVerb("look at"),
    PhrasalVerb("look for"),
    PhrasalVerb("look forward to"),
    PhrasalVerb("look into"),
    PhrasalVerb("look out"),
    PhrasalVerb("look up", separable=True),
    PhrasalVerb("make up", separable=True),
    PhrasalVerb("move on"),
    PhrasalVerb("pass out"),
    PhrasalVerb("pay back", separable=True),
    PhrasalVerb("pick up", separable=True),
    PhrasalVerb("point out", separable=True),
    PhrasalVerb("put away", separable=True),
    PhrasalVerb("put off", separable=True),
    PhrasalVerb("put on", separable=True),
    PhrasalVerb("put out", separable=True),
    PhrasalVerb("put up"),
    PhrasalVerb("run into"),
    PhrasalVerb("run out of"),
    PhrasalVerb("set up", separable=True),
    PhrasalVerb("show up"),
    PhrasalVerb("shut down", separable=True),
    PhrasalVerb("sit down"),
    PhrasalVerb("sort out", separable=True),
    PhrasalVerb("stand up"),
    PhrasalVerb("take away", separable=True),
    PhrasalVerb("take back", separable=True),
    PhrasalVerb("take off", separable=True),
    PhrasalVerb("take on"),
    PhrasalVerb("take out", separable=True),
    PhrasalVerb("take over"),
    PhrasalVerb("talk about"),
    PhrasalVerb("talk into"),
    PhrasalVerb("think over", separable=True),
    PhrasalVerb("throw away", separable=True),
    PhrasalVerb("try on", separable=True),
    PhrasalVerb("turn down", separable=True),
    PhrasalVerb("turn off", separable=True),
    PhrasalVerb("turn on", separable=True),
    PhrasalVerb("turn out"),
    PhrasalVerb("wake up", separable=True),
    PhrasalVerb("walk away"),
    PhrasalVerb("work out"),
    PhrasalVerb("write down", separable=True),
]


@dataclass
class Match:
    start: int
    end: int
    label: str


def build_patterns(verbs: Iterable[PhrasalVerb]) -> list[tuple[PhrasalVerb, re.Pattern[str]]]:
    patterns: list[tuple[PhrasalVerb, re.Pattern[str]]] = []
    for verb in verbs:
        words = verb.words
        if len(words) < 2:
            continue

        if verb.separable and len(words) == 2:
            # e.g., "pick up" -> "pick it up", "pick the phone up"
            regex = rf"\b{words[0]}\b(?:\s+\w+){{0,2}}\s+\b{words[1]}\b"
        else:
            regex = rf"\b{'\\s+'.join(words)}\b"

        patterns.append((verb, re.compile(regex, flags=re.IGNORECASE)))

    return patterns


def find_matches(text: str, patterns: list[tuple[PhrasalVerb, re.Pattern[str]]]) -> list[Match]:
    candidates: list[Match] = []
    for verb, pattern in patterns:
        for m in pattern.finditer(text):
            candidates.append(Match(m.start(), m.end(), verb.base))

    # Prefer earlier matches, and longer spans when they start at same place.
    candidates.sort(key=lambda x: (x.start, -(x.end - x.start)))

    filtered: list[Match] = []
    current_end = -1
    for c in candidates:
        if c.start >= current_end:
            filtered.append(c)
            current_end = c.end

    return filtered


def highlight_ansi(line: str, matches: list[Match], color_map: dict[str, str]) -> str:
    if not matches:
        return line

    out: list[str] = []
    cursor = 0
    for m in matches:
        out.append(line[cursor : m.start])
        color = color_map[m.label]
        out.append(f"{color}{line[m.start:m.end]}{ANSI_RESET}")
        cursor = m.end
    out.append(line[cursor:])
    return "".join(out)


def highlight_html(line: str, matches: list[Match], color_map: dict[str, str]) -> str:
    if not matches:
        return html.escape(line)

    out: list[str] = []
    cursor = 0
    for m in matches:
        out.append(html.escape(line[cursor : m.start]))
        color = color_map[m.label]
        chunk = html.escape(line[m.start:m.end])
        out.append(f'<span style="color:{color}; font-weight:700;">{chunk}</span>')
        cursor = m.end
    out.append(html.escape(line[cursor:]))
    return "".join(out)


def is_subtitle_metadata(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped.isdigit() or TIMESTAMP_RE.match(stripped))


def choose_color_map(labels: list[str], html_mode: bool, seed: int) -> dict[str, str]:
    rng = random.Random(seed)
    palette = HTML_COLORS[:] if html_mode else ANSI_COLORS[:]
    rng.shuffle(palette)

    color_map: dict[str, str] = {}
    for i, label in enumerate(sorted(set(labels))):
        color_map[label] = palette[i % len(palette)]
    return color_map


def process_text(content: str, html_mode: bool, seed: int) -> tuple[str, int]:
    patterns = build_patterns(PHRASAL_VERBS)
    lines = content.splitlines()

    all_labels: list[str] = []
    line_matches: list[list[Match]] = []

    for line in lines:
        if is_subtitle_metadata(line):
            line_matches.append([])
            continue

        matches = find_matches(line, patterns)
        line_matches.append(matches)
        all_labels.extend(m.label for m in matches)

    color_map = choose_color_map(all_labels, html_mode=html_mode, seed=seed)

    rendered: list[str] = []
    for line, matches in zip(lines, line_matches):
        if not matches:
            rendered.append(html.escape(line) if html_mode else line)
            continue

        if html_mode:
            rendered.append(highlight_html(line, matches, color_map))
        else:
            rendered.append(highlight_ansi(line, matches, color_map))

    return "\n".join(rendered), len(all_labels)


def wrap_html(body: str, source_name: str) -> str:
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Phrasal Verb Highlighter</title>
  <style>
    :root {{
      --bg: #0f172a;
      --panel: #111827;
      --text: #e5e7eb;
      --muted: #9ca3af;
    }}
    body {{
      margin: 0;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      background: radial-gradient(circle at top, #1f2937, var(--bg));
      color: var(--text);
      line-height: 1.55;
    }}
    .wrap {{
      max-width: 980px;
      margin: 1.25rem auto;
      padding: 1rem;
    }}
    .meta {{
      color: var(--muted);
      margin-bottom: 0.75rem;
      font-size: 0.95rem;
    }}
    pre {{
      white-space: pre-wrap;
      word-break: break-word;
      background: var(--panel);
      border: 1px solid #374151;
      border-radius: 10px;
      padding: 1rem;
      margin: 0;
    }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <div class=\"meta\">Source: {html.escape(source_name)}</div>
    <pre>{body}</pre>
  </div>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Highlight phrasal verbs in subtitle/text files")
    parser.add_argument("input", type=Path, help="Path to .srt or .txt file")
    parser.add_argument(
        "--mode",
        choices=["ansi", "html"],
        default="ansi",
        help="ansi = terminal colors, html = colored HTML output",
    )
    parser.add_argument("-o", "--output", type=Path, help="Output file path")
    parser.add_argument("--seed", type=int, default=7, help="Color shuffle seed (default: 7)")

    args = parser.parse_args()
    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    content = args.input.read_text(encoding="utf-8", errors="replace")
    html_mode = args.mode == "html"
    rendered, total = process_text(content, html_mode=html_mode, seed=args.seed)

    if html_mode:
        rendered = wrap_html(rendered, args.input.name)

    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Saved output to: {args.output}")
    else:
        print(rendered)

    print(f"\nDetected phrasal verb matches: {total}")


if __name__ == "__main__":
    main()
