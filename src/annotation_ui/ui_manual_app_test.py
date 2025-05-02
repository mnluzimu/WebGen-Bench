# jsonl_annotation_ui_tk.py
"""
Tkinter‑based annotation tool for JSONL datasets (no Streamlit).

Usage (Python ≥ 3.8):
    python jsonl_annotation_ui_tk.py --input data.jsonl --output annotations.jsonl

The program shows one record at a time:
  • Instruction text at the top.
  • For every item in "ui_instruct" it displays the task (and expected result)
    with three buttons: YES / PARTIAL / NO.
  • Selecting a button stores the choice, colours the selected button, and
    persists to *annotations.jsonl* immediately.
  • Navigate records with "Previous" / "Next".  Existing annotations load on
    start‑up and can be changed any time.

Dependencies: **only the Python standard library** (Tkinter).
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import tkinter as tk
from tkinter import ttk, messagebox

CHOICES = ["YES", "PARTIAL", "NO"]
BTN_COLOURS = {
    "YES": "#2ecc71",       # green
    "PARTIAL": "#f1c40f",   # yellow
    "NO": "#e74c3c",        # red
}
DEFAULT_BTN_BG = "SystemButtonFace"  # fallback to OS default

################################################################################
# File helpers
################################################################################

def load_jsonl(path: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf‑8") as fh:
        for line in fh:
            if line.strip():
                records.append(json.loads(line))
    return records


def load_annotations(path: Path) -> Dict[int, List[str]]:
    if not path.exists():
        return {}
    ann: Dict[int, List[str]] = {}
    with path.open("r", encoding="utf‑8") as fh:
        for line in fh:
            if line.strip():
                obj = json.loads(line)
                ann[int(obj["index"])] = obj["annotations"]
    return ann


def save_annotations(path: Path, annotations: Dict[int, List[str]]):
    tmp = path.with_suffix(".tmp")
    with tmp.open("w", encoding="utf‑8") as fh:
        for idx, ann in sorted(annotations.items()):
            json.dump({"index": idx, "annotations": ann}, fh, ensure_ascii=False)
            fh.write("\n")
    tmp.replace(path)

################################################################################
# GUI application
################################################################################

class AnnotationApp(tk.Tk):
    def __init__(self, data: List[Dict[str, Any]], out_path: Path):
        super().__init__()
        self.title("JSONL Annotation Tool")
        self.geometry("1000x700")

        self.data = data
        self.total = len(data)
        self.out_path = out_path

        self.annotations: Dict[int, List[str]] = load_annotations(out_path)
        # pick first un‑annotated record or 0
        self.idx: int = next((i for i in range(self.total) if i not in self.annotations), 0)

        self._build_widgets()
        self._load_record()

    # --------------------------------------------------------------------- UI
    def _build_widgets(self):
        # navigation frame
        nav = ttk.Frame(self)
        nav.pack(fill="x", pady=4)

        self.prev_btn = ttk.Button(nav, text="← Previous", command=self.prev_record)
        self.prev_btn.pack(side="left", padx=5)

        self.progress_lbl = ttk.Label(nav, text="")
        self.progress_lbl.pack(side="left", padx=10)

        self.next_btn = ttk.Button(nav, text="Next →", command=self.next_record)
        self.next_btn.pack(side="right", padx=5)

        # instruction
        self.instruction_txt = tk.Text(self, wrap="word", height=8, state="disabled", bg="#f9f9f9")
        self.instruction_txt.pack(fill="x", padx=10, pady=(0, 10))

        # scrollable canvas for tasks
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        self.tasks_frame = ttk.Frame(canvas)

        self.tasks_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )

        canvas.create_window((0, 0), window=self.tasks_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # ------------------------------------------------------------------ helpers
    def _load_record(self):
        rec = self.data[self.idx]
        tasks = rec.get("ui_instruct", [])
        # ensure annotation list size matches tasks
        ann_list = self.annotations.get(self.idx, [None] * len(tasks))
        if len(ann_list) < len(tasks):
            ann_list.extend([None] * (len(tasks) - len(ann_list)))
        self.annotations[self.idx] = ann_list

        # update instruction text
        self.instruction_txt.configure(state="normal")
        self.instruction_txt.delete("1.0", "end")
        self.instruction_txt.insert("1.0", rec.get("instruction", "(no instruction)"))
        self.instruction_txt.configure(state="disabled")

        # clear previous task widgets
        for child in self.tasks_frame.winfo_children():
            child.destroy()

        # build task rows
        for t_i, task in enumerate(tasks):
            frame = ttk.Frame(self.tasks_frame)
            frame.pack(fill="x", pady=5, padx=10, anchor="w")

            # task text
            task_lbl = ttk.Label(frame, text=f"Task {t_i + 1}: {task.get('task', '')}", wraplength=900, justify="left")
            task_lbl.pack(anchor="w")

            exp = task.get("expected_result")
            if exp:
                exp_lbl = ttk.Label(frame, text=f"Expected: {exp}", wraplength=900, justify="left", foreground="#555")
                exp_lbl.pack(anchor="w", padx=(20, 0))

            # button row
            btn_row = ttk.Frame(frame)
            btn_row.pack(anchor="w", pady=2)

            btns = {}
            for choice in CHOICES:
                btn = tk.Button(
                    btn_row,
                    text=choice,
                    width=8,
                    command=lambda c=choice, i=t_i: self.set_choice(i, c),
                )
                btn.pack(side="left", padx=2)
                btns[choice] = btn
            frame.btns = btns  # type: ignore

        # store references to frames to update colours later
        self.task_frames = self.tasks_frame.winfo_children()

        self._refresh_button_colours()
        self._update_nav_state()
        self._update_progress()

    # ------------------------------------------------------------------ actions
    def set_choice(self, task_index: int, choice: str):
        self.annotations[self.idx][task_index] = choice
        save_annotations(self.out_path, self.annotations)
        self._refresh_button_colours()

    def prev_record(self):
        if self.idx > 0:
            self.idx -= 1
            self._load_record()

    def next_record(self):
        if self.idx < self.total - 1:
            self.idx += 1
            self._load_record()

    # ---------------------------------------------------------- UI state helpers
    def _refresh_button_colours(self):
        ann_list = self.annotations.get(self.idx, [])
        for t_i, frame in enumerate(self.task_frames):
            btns = getattr(frame, "btns", {})
            selected = ann_list[t_i] if t_i < len(ann_list) else None
            for choice, btn in btns.items():
                if choice == selected:
                    btn.configure(bg=BTN_COLOURS[choice], fg="white", relief="sunken")
                else:
                    btn.configure(bg=DEFAULT_BTN_BG, fg="black", relief="raised")

    def _update_nav_state(self):
        self.prev_btn["state"] = "disabled" if self.idx == 0 else "normal"
        self.next_btn["state"] = "disabled" if self.idx == self.total - 1 else "normal"

    def _update_progress(self):
        completed = len(self.annotations)
        self.progress_lbl.configure(text=f"Record {self.idx + 1}/{self.total}    •    Annotated {completed}/{self.total}")

################################################################################
# Main entry point
################################################################################

def main():
    parser = argparse.ArgumentParser(description="Tkinter JSONL annotation tool")
    parser.add_argument("--input", default="data/test.jsonl", help="Input JSONL file")
    parser.add_argument("--output", default="data/test-manual_claude-3-5-sonnet.jsonl", help="Output JSONL file")
    args = parser.parse_args()

    data_path = Path(args.input)
    if not data_path.exists():
        raise SystemExit(f"Input file '{data_path}' not found.")

    data = load_jsonl(data_path)
    if not data:
        raise SystemExit("Input file is empty or invalid JSONL.")

    out_path = Path(args.output)

    app = AnnotationApp(data, out_path)
    app.mainloop()


if __name__ == "__main__":
    main()
