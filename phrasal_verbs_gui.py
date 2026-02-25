#!/usr/bin/env python3
"""Desktop GUI for subtitle phrasal verb highlighting and export."""

from __future__ import annotations

import html
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from highlight_phrasal_verbs import (
    analyze_content,
    build_match_report,
    highlight_html,
    process_text_ass,
    process_text_srt,
    wrap_html,
)


class PhrasalVerbApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Phrasal Verb Highlighter")
        self.root.geometry("980x700")

        self.current_file: Path | None = None
        self.current_content: str = ""
        self.last_rendered_html: str = ""
        self.last_rendered_srt: str = ""
        self.last_rendered_ass: str = ""
        self.last_report: str = ""
        self.seed_var = tk.IntVar(value=7)
        self.sync_ms_var = tk.IntVar(value=0)

        self.is_running = False
        self.analysis_queue: queue.Queue = queue.Queue()
        self._render_index = 0
        self._render_analysis = None
        self._poll_after_id: str | None = None
        self._render_after_id: str | None = None
        self._is_closing = False
        self._run_id = 0
        self._cancel_event = threading.Event()

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)

        self.file_label = ttk.Label(top, text="No file selected")
        self.file_label.pack(side=tk.LEFT, padx=(0, 8))

        self.open_btn = ttk.Button(top, text="Open lyrics/subtitle", command=self.open_file)
        self.open_btn.pack(side=tk.LEFT, padx=4)
        self.paste_btn = ttk.Button(top, text="Paste lyrics", command=self.open_paste_dialog)
        self.paste_btn.pack(side=tk.LEFT, padx=4)
        self.run_btn = ttk.Button(top, text="Run", command=self.run_analysis)
        self.run_btn.pack(side=tk.LEFT, padx=4)
        self.export_srt_btn = ttk.Button(top, text="Export SRT", command=self.export_srt)
        self.export_srt_btn.pack(side=tk.LEFT, padx=4)
        self.export_ass_btn = ttk.Button(top, text="Export ASS", command=self.export_ass)
        self.export_ass_btn.pack(side=tk.LEFT, padx=4)
        self.export_html_btn = ttk.Button(top, text="Export HTML", command=self.export_html)
        self.export_html_btn.pack(side=tk.LEFT, padx=4)
        self.export_report_btn = ttk.Button(top, text="Export Report", command=self.export_report)
        self.export_report_btn.pack(side=tk.LEFT, padx=4)

        ttk.Label(top, text="Seed:").pack(side=tk.LEFT, padx=(16, 4))
        ttk.Entry(top, width=6, textvariable=self.seed_var).pack(side=tk.LEFT)
        ttk.Label(top, text="Sync ms:").pack(side=tk.LEFT, padx=(12, 4))
        ttk.Entry(top, width=8, textvariable=self.sync_ms_var).pack(side=tk.LEFT)

        self.summary = ttk.Label(top, text="Matches: 0")
        self.summary.pack(side=tk.RIGHT)

        status_bar = ttk.Frame(self.root, padding=(10, 0, 10, 8))
        status_bar.pack(fill=tk.X)

        self.status_label = ttk.Label(status_bar, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        self.progress = ttk.Progressbar(status_bar, mode="indeterminate", length=140)
        self.progress.pack(side=tk.RIGHT)

        text_wrap = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        text_wrap.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(text_wrap, wrap=tk.WORD, font=("Consolas", 11), undo=False)
        scroll = ttk.Scrollbar(text_wrap, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.text.insert(
            "1.0",
            "Open or paste lyrics/subtitles, click Run, then export HTML/SRT/ASS/report.",
        )
        self.text.config(state=tk.DISABLED)

    def open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Select lyrics/text/subtitle file",
            filetypes=[
                ("Text files", "*.txt *.text *.md *.lrc *.log *.csv *.tsv"),
                ("Subtitle files", "*.srt *.ass *.vtt"),
                ("All files", "*.*"),
            ],
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
        self._set_loaded_source(str(file_path), "File loaded. Click Run to analyze.")

    def open_paste_dialog(self) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Paste Lyrics")
        dialog.geometry("760x520")
        dialog.transient(self.root)

        frame = ttk.Frame(dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Paste song lyrics or subtitle text:").pack(anchor=tk.W, pady=(0, 6))

        editor = tk.Text(frame, wrap=tk.WORD, font=("Consolas", 11), undo=True)
        editor.pack(fill=tk.BOTH, expand=True)

        btns = ttk.Frame(frame)
        btns.pack(fill=tk.X, pady=(8, 0))

        def load_pasted() -> None:
            content = editor.get("1.0", tk.END).strip("\n")
            if not content.strip():
                messagebox.showwarning("No lyrics", "Paste some text before loading.")
                return
            self.current_file = None
            self.current_content = content
            self._set_loaded_source("Pasted lyrics", "Lyrics loaded from text form. Click Run to analyze.")
            dialog.destroy()

        ttk.Button(btns, text="Load", command=load_pasted).pack(side=tk.RIGHT, padx=(6, 0))
        ttk.Button(btns, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT)

        dialog.grab_set()
        editor.focus_set()

    def _set_loaded_source(self, source_label: str, text_message: str) -> None:
        self.file_label.config(text=source_label)
        self.summary.config(text="Matches: 0")
        self.last_rendered_html = ""
        self.last_rendered_srt = ""
        self.last_rendered_ass = ""
        self.last_report = ""
        self._set_text(text_message)
        self.status_label.config(text="Ready")

    def run_analysis(self) -> None:
        if self.is_running:
            return
        if not self.current_content:
            messagebox.showwarning("No content", "Open or paste lyrics/text first.")
            return

        try:
            seed = int(self.seed_var.get())
        except (TypeError, ValueError):
            messagebox.showerror("Invalid seed", "Seed must be an integer.")
            return
        try:
            sync_ms = int(self.sync_ms_var.get())
        except (TypeError, ValueError):
            messagebox.showerror("Invalid sync", "Sync ms must be an integer.")
            return

        self._run_id += 1
        run_id = self._run_id
        self._cancel_event = threading.Event()

        self._set_busy_ui(True)
        self._set_text("Processing...")
        self.status_label.config(text="Running analysis in background...")

        source_name = self.current_file.name if self.current_file else "lyrics"
        worker = threading.Thread(
            target=self._analysis_worker,
            args=(self.current_content, seed, sync_ms, source_name, run_id, self._cancel_event),
            daemon=True,
        )
        worker.start()
        self._schedule_poll()

    def _analysis_worker(
        self,
        content: str,
        seed: int,
        sync_ms: int,
        source_name: str,
        run_id: int,
        cancel_event: threading.Event,
    ) -> None:
        try:
            analysis = analyze_content(content, html_mode=True, seed=seed)
            if cancel_event.is_set():
                return

            html_lines: list[str] = []
            for idx, (line, matches) in enumerate(zip(analysis.lines, analysis.line_matches)):
                if cancel_event.is_set():
                    return
                if matches:
                    html_lines.append(highlight_html(line, matches, analysis.color_map))
                else:
                    html_lines.append(html.escape(line))
                if idx and idx % 500 == 0 and cancel_event.is_set():
                    return

            rendered_html = wrap_html("\n".join(html_lines), source_name)
            if cancel_event.is_set():
                return
            rendered_srt, _ = process_text_srt(content, seed=seed, shift_ms=sync_ms)
            if cancel_event.is_set():
                return
            rendered_ass, _ = process_text_ass(content, seed=seed, shift_ms=sync_ms)
            if cancel_event.is_set():
                return

            report = build_match_report(analysis)

            self.analysis_queue.put(
                {
                    "ok": True,
                    "run_id": run_id,
                    "analysis": analysis,
                    "html": rendered_html,
                    "srt": rendered_srt,
                    "ass": rendered_ass,
                    "report": report,
                }
            )
        except Exception as exc:  # pragma: no cover - defensive for GUI runtime
            self.analysis_queue.put({"ok": False, "run_id": run_id, "error": str(exc)})

    def _schedule_poll(self) -> None:
        if self._is_closing:
            return
        self._poll_after_id = self.root.after(100, self._poll_worker)

    def _poll_worker(self) -> None:
        self._poll_after_id = None
        if self._is_closing:
            return

        try:
            result = self.analysis_queue.get_nowait()
        except queue.Empty:
            self._schedule_poll()
            return

        if result.get("run_id") != self._run_id:
            self._schedule_poll()
            return

        if not result.get("ok"):
            self._set_busy_ui(False)
            messagebox.showerror("Error", f"Analysis failed:\n{result.get('error', 'Unknown error')}")
            self.status_label.config(text="Analysis failed")
            return

        self.last_rendered_html = result["html"]
        self.last_rendered_srt = result["srt"]
        self.last_rendered_ass = result["ass"]
        self.last_report = result["report"]
        analysis = result["analysis"]
        self.summary.config(text=f"Matches: {analysis.total_matches}")

        self._render_analysis_in_chunks(analysis)

    def _render_analysis_in_chunks(self, analysis) -> None:
        if self._is_closing:
            return

        self._render_analysis = analysis
        self._render_index = 0
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)

        for m in self.text.tag_names():
            if m.startswith("verb_"):
                self.text.tag_delete(m)

        for label, color in analysis.color_map.items():
            tag = f"verb_{label.replace(' ', '_')}"
            self.text.tag_configure(tag, foreground=color)

        self.status_label.config(text="Rendering output...")
        self._render_next_chunk()

    def _render_next_chunk(self, chunk_size: int = 80) -> None:
        if self._is_closing:
            return

        analysis = self._render_analysis
        if analysis is None:
            self._set_busy_ui(False)
            self.status_label.config(text="Ready")
            return

        end = min(self._render_index + chunk_size, len(analysis.lines))
        for idx in range(self._render_index, end):
            line = analysis.lines[idx]
            matches = analysis.line_matches[idx]
            line_no = idx + 1
            self.text.insert(tk.END, line)
            self.text.insert(tk.END, "\n")

            for match in matches:
                tag = f"verb_{match.label.replace(' ', '_')}"
                for span_start, span_end in match.spans:
                    start = f"{line_no}.{span_start}"
                    end_pos = f"{line_no}.{span_end}"
                    self.text.tag_add(tag, start, end_pos)

        self._render_index = end
        if self._render_index < len(analysis.lines):
            self._render_after_id = self.root.after(8, self._render_next_chunk)
            return

        self.text.config(state=tk.DISABLED)
        self._render_analysis = None
        self._set_busy_ui(False)
        self.status_label.config(text="Ready")

    def _set_busy_ui(self, busy: bool) -> None:
        self.is_running = busy
        state = tk.DISABLED if busy else tk.NORMAL
        self.open_btn.config(state=state)
        self.paste_btn.config(state=state)
        self.run_btn.config(state=state)
        self.export_srt_btn.config(state=state)
        self.export_ass_btn.config(state=state)
        self.export_html_btn.config(state=state)
        self.export_report_btn.config(state=state)
        if busy:
            self.progress.start(10)
        else:
            self.progress.stop()

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

    def export_srt(self) -> None:
        if not self.last_rendered_srt:
            messagebox.showwarning("No output", "Run analysis first.")
            return

        default_name = "phrasal_verbs_output.srt"
        if self.current_file:
            default_name = f"{self.current_file.stem}_phrasal_verbs.srt"

        save_path = filedialog.asksaveasfilename(
            title="Export highlighted subtitle",
            defaultextension=".srt",
            initialfile=default_name,
            filetypes=[("SRT subtitle", "*.srt")],
        )
        if not save_path:
            return

        try:
            Path(save_path).write_text(self.last_rendered_srt, encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Error", f"Could not save file:\n{exc}")
            return

        messagebox.showinfo("Saved", f"Exported:\n{save_path}")

    def export_ass(self) -> None:
        if not self.last_rendered_ass:
            messagebox.showwarning("No output", "Run analysis first.")
            return

        default_name = "phrasal_verbs_output.ass"
        if self.current_file:
            default_name = f"{self.current_file.stem}_phrasal_verbs.ass"

        save_path = filedialog.asksaveasfilename(
            title="Export styled subtitle",
            defaultextension=".ass",
            initialfile=default_name,
            filetypes=[("ASS subtitle", "*.ass")],
        )
        if not save_path:
            return

        try:
            Path(save_path).write_text(self.last_rendered_ass, encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Error", f"Could not save file:\n{exc}")
            return

        messagebox.showinfo("Saved", f"Exported:\n{save_path}")

    def export_report(self) -> None:
        if not self.last_report:
            messagebox.showwarning("No output", "Run analysis first.")
            return

        default_name = "phrasal_verbs_report.txt"
        if self.current_file:
            default_name = f"{self.current_file.stem}_phrasal_verbs_report.txt"

        save_path = filedialog.asksaveasfilename(
            title="Export phrasal verb report",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Text file", "*.txt"), ("All files", "*.*")],
        )
        if not save_path:
            return

        try:
            Path(save_path).write_text(self.last_report, encoding="utf-8")
        except OSError as exc:
            messagebox.showerror("Error", f"Could not save file:\n{exc}")
            return

        messagebox.showinfo("Saved", f"Exported:\n{save_path}")

    def _set_text(self, value: str) -> None:
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", value)
        self.text.config(state=tk.DISABLED)

    def _cancel_callbacks(self) -> None:
        if self._poll_after_id is not None:
            try:
                self.root.after_cancel(self._poll_after_id)
            except tk.TclError:
                pass
            self._poll_after_id = None
        if self._render_after_id is not None:
            try:
                self.root.after_cancel(self._render_after_id)
            except tk.TclError:
                pass
            self._render_after_id = None

    def _on_close(self) -> None:
        self._is_closing = True
        self._cancel_event.set()
        self._cancel_callbacks()
        self._render_analysis = None
        try:
            self.root.destroy()
        except tk.TclError:
            pass


def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    app = PhrasalVerbApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
