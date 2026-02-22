#!/usr/bin/env python3
"""Desktop GUI for subtitle phrasal verb highlighting and export."""

from __future__ import annotations

import tkinter as tk
import html
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from highlight_phrasal_verbs import analyze_content, highlight_html, wrap_html


class PhrasalVerbApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Phrasal Verb Highlighter")
        self.root.geometry("980x700")

        self.current_file: Path | None = None
        self.current_content: str = ""
        self.last_rendered_html: str = ""
        self.seed_var = tk.IntVar(value=7)

        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)

        self.file_label = ttk.Label(top, text="No file selected")
        self.file_label.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(top, text="Open subtitle", command=self.open_file).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Run", command=self.run_analysis).pack(side=tk.LEFT, padx=4)
        ttk.Button(top, text="Export HTML", command=self.export_html).pack(side=tk.LEFT, padx=4)

        ttk.Label(top, text="Seed:").pack(side=tk.LEFT, padx=(16, 4))
        ttk.Entry(top, width=6, textvariable=self.seed_var).pack(side=tk.LEFT)

        self.summary = ttk.Label(top, text="Matches: 0")
        self.summary.pack(side=tk.RIGHT)

        text_wrap = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        text_wrap.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(text_wrap, wrap=tk.WORD, font=("Consolas", 11), undo=False)
        scroll = ttk.Scrollbar(text_wrap, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.text.insert("1.0", "Open a subtitle file, click Run, then export HTML.")
        self.text.config(state=tk.DISABLED)

    def open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select subtitle/text file",
            filetypes=[("Subtitles and text", "*.srt *.txt"), ("All files", "*.*")],
        )
        if not path:
            return

        file_path = Path(path)
        try:
            self.current_content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            messagebox.showerror("Error", f"Could not open file:\n{exc}")
            return

        self.current_file = file_path
        self.file_label.config(text=str(file_path))
        self.summary.config(text="Matches: 0")
        self._set_text("File loaded. Click Run to analyze.")

    def run_analysis(self) -> None:
        if not self.current_content:
            messagebox.showwarning("No file", "Open a subtitle/text file first.")
            return

        try:
            seed = int(self.seed_var.get())
        except (TypeError, ValueError):
            messagebox.showerror("Invalid seed", "Seed must be an integer.")
            return

        analysis = analyze_content(self.current_content, html_mode=True, seed=seed)
        self._render_colored_text(analysis)
        self.summary.config(text=f"Matches: {analysis.total_matches}")

        html_lines: list[str] = []
        for line, matches in zip(analysis.lines, analysis.line_matches):
            if matches:
                html_lines.append(highlight_html(line, matches, analysis.color_map))
            else:
                html_lines.append(html.escape(line))

        source_name = self.current_file.name if self.current_file else "input"
        self.last_rendered_html = wrap_html("\n".join(html_lines), source_name)

    def _render_colored_text(self, analysis) -> None:
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)

        for idx, (line, matches) in enumerate(zip(analysis.lines, analysis.line_matches), start=1):
            self.text.insert(tk.END, line)
            self.text.insert(tk.END, "\n")

            for m in matches:
                tag = f"verb_{m.label.replace(' ', '_')}"
                self.text.tag_configure(tag, foreground=analysis.color_map[m.label])
                start = f"{idx}.{m.start}"
                end = f"{idx}.{m.end}"
                self.text.tag_add(tag, start, end)

        self.text.config(state=tk.DISABLED)

    def export_html(self) -> None:
        if not self.last_rendered_html:
            messagebox.showwarning("No output", "Run analysis first.")
            return

        default_name = "phrasal_verbs_output.html"
        if self.current_file:
            default_name = f"{self.current_file.stem}_phrasal_verbs.html"

        save_path = filedialog.asksaveasfilename(
            title="Export highlighted file",
            defaultextension=".html",
            initialfile=default_name,
            filetypes=[("HTML file", "*.html")],
        )
        if not save_path:
            return

        try:
            Path(save_path).write_text(self.last_rendered_html, encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Error", f"Could not save file:\n{exc}")
            return

        messagebox.showinfo("Saved", f"Exported:\n{save_path}")

    def _set_text(self, value: str) -> None:
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", value)
        self.text.config(state=tk.DISABLED)


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    app = PhrasalVerbApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
