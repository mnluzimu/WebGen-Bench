import os
import json
import tkinter as tk
from tkinter import ttk, scrolledtext

class JSONLEditor:
    def __init__(self, master, records, output_file, saved_records=None):
        """
        :param master: The Tk root window.
        :param records: List of records read from input.jsonl.
        :param output_file: Path to output.jsonl for saving.
        :param saved_records: (Optional) Dict of records loaded from output.jsonl if it exists.
        """
        self.master = master
        self.records = records
        self.output_file = output_file
        self.current_index = 0
        self.current_record = None
        # If no saved_records are passed in, default to an empty dict
        self.saved_records = saved_records if saved_records is not None else {}

        # Configure main window
        master.title("JSONL Editor")
        master.geometry("1000x800")

        # KEY BINDINGS
        master.bind("<Right>", self.on_next_key)    # Move to next record
        master.bind("<Left>", self.on_previous_key) # Move to previous record
        master.bind("<Down>", self.on_save_key)     # Save the current record

        # Main container
        main_frame = ttk.Frame(master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Status bar (displays record count, etc.)
        self.status_label = ttk.Label(main_frame, text="", font=("TkDefaultFont", 10, "bold"))
        self.status_label.pack(anchor=tk.W, pady=2)

        # Instruction Section
        instruction_label = ttk.Label(main_frame, text="Instruction:")
        instruction_label.pack(anchor=tk.W)
        self.instruction_text = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD, height=10)
        self.instruction_text.pack(fill=tk.X, pady=5)

        # UI Instructions Section
        ui_instruct_label = ttk.Label(main_frame, text="UI Instructions:")
        ui_instruct_label.pack(anchor=tk.W)

        # Canvas and Scrollbar for tasks
        self.canvas = tk.Canvas(main_frame, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # Load the first record
        self.load_record()

    def on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def load_record(self):
        """Load the record at self.current_index into the UI."""
        # Guard against out-of-range indices
        if self.current_index < 0:
            self.current_index = 0
        if self.current_index >= len(self.records):
            tk.messagebox.showinfo("End", "No more records to display.")
            if self.current_index >= len(self.records):
                self.current_index = len(self.records) - 1
            return

        # Get the URL to see if this record was previously saved
        url = self.records[self.current_index].get("url", "")
        if url in self.saved_records:
            # Use the previously saved data instead of the original
            self.current_record = self.saved_records[url].copy()
        else:
            # Otherwise, start with the record from input.jsonl
            self.current_record = self.records[self.current_index].copy()

        self.clear_ui()

        # Load instruction
        self.instruction_text.delete(1.0, tk.END)
        self.instruction_text.insert(tk.END, self.current_record.get("instruction", ""))

        # Load UI instructions
        for task in self.current_record.get("ui_instruct", []):
            self.add_task(task.get("task", ""), task.get("expected_result", ""))

        # Update status label
        self.update_status_label()

    def clear_ui(self):
        """Remove all widgets inside the scrollable frame."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

    def add_task(self, task="", expected_result=""):
        """Add a single row (task + expected result) to the UI."""
        task_frame = ttk.Frame(self.scrollable_frame)
        task_frame.grid_columnconfigure(0, weight=1)
        task_frame.grid_columnconfigure(1, weight=1)
        task_frame.grid_columnconfigure(2, weight=0)

        # Add to scrollable_frame using grid (so resizing works correctly)
        task_frame.pack(fill=tk.X, pady=2, expand=True)

        task_text = scrolledtext.ScrolledText(task_frame, wrap=tk.WORD, height=4)
        task_text.insert(tk.END, task)
        task_text.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        expected_text = scrolledtext.ScrolledText(task_frame, wrap=tk.WORD, height=4)
        expected_text.insert(tk.END, expected_result)
        expected_text.grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

        delete_btn = ttk.Button(task_frame, text="×", width=3, command=lambda f=task_frame: f.destroy())
        delete_btn.grid(row=0, column=2, sticky="ne", padx=2, pady=2)

    def save_record(self):
        """Collect current UI data and store it in saved_records."""
        if not self.current_record:
            return

        # Update the instruction text
        self.current_record["instruction"] = self.instruction_text.get(1.0, tk.END).strip()

        # Helper function to recursively find ScrolledText widgets
        def find_scrolledtext_widgets(widget):
            """Recursively find all ScrolledText widgets within a widget."""
            scrolledtext_widgets = []
            for child in widget.winfo_children():
                if isinstance(child, scrolledtext.ScrolledText):
                    scrolledtext_widgets.append(child)
                else:
                    scrolledtext_widgets.extend(find_scrolledtext_widgets(child))
            return scrolledtext_widgets

        # Collect ui_instruct tasks from ScrolledText widgets
        ui_instruct = []
        for task_frame in self.scrollable_frame.winfo_children():
            # Debugging: Print the children of each task_frame
            print("task_frame children:", task_frame.winfo_children())

            # Recursively find ScrolledText widgets
            st_children = find_scrolledtext_widgets(task_frame)
            print("Filtered ScrolledText widgets:", st_children)  # Debugging

            if len(st_children) >= 2:
                task = st_children[0].get("1.0", tk.END).strip()
                expected = st_children[1].get("1.0", tk.END).strip()
                print(f"Task: {task}, Expected: {expected}")  # Debugging
                if task or expected:  # Only add non-empty tasks
                    ui_instruct.append({"task": task, "expected_result": expected})

        # Debugging: Print collected ui_instruct
        print("Collected ui_instruct:", ui_instruct)

        self.current_record["ui_instruct"] = ui_instruct

        # Save in-memory
        url = self.current_record.get("url", "")
        if url:
            self.saved_records[url] = self.current_record.copy()

        # Update status label (no message box)
        self.update_status_label()

    def next_record(self):
        self.current_index += 1
        self.load_record()

    def previous_record(self):
        self.current_index -= 1
        self.load_record()

    # --- EVENT HANDLERS FOR KEY BINDS ---
    def on_next_key(self, event):
        """Handler for right arrow key."""
        self.next_record()

    def on_previous_key(self, event):
        """Handler for left arrow key."""
        self.previous_record()

    def on_save_key(self, event):
        """Handler for down arrow key."""
        self.save_record()

    def update_status_label(self):
        """Update the status label with record count info."""
        total_records = len(self.records)
        current_index = self.current_index + 1  # Convert to 1-based for display
        saved_count = len(self.saved_records)
        self.status_label.config(
            text=f"Record {current_index} of {total_records} | Saved: {saved_count}"
        )

    def on_closing(self):
        """Save records to file when closing."""
        if self.saved_records:
            with open(self.output_file, "w", encoding="utf-8") as f:
                for record in self.saved_records.values():
                    f.write(json.dumps(record) + "\n")
        self.master.destroy()

def main():
    import tkinter.messagebox  # Needed for "No more records" message
    input_file = "data/test.jsonl"
    output_file = "data/test1.jsonl"

    # Read input JSONL
    records = []
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            for line in f:
                records.append(json.loads(line))
    except FileNotFoundError:
        tk.messagebox.showerror("Error", f"Input file {input_file} not found!")
        return

    # Attempt to load previously saved records if output_file already exists
    saved_records = {}
    if os.path.isfile(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    existing = json.loads(line)
                    url = existing.get("url")
                    if url:
                        saved_records[url] = existing
                except json.JSONDecodeError:
                    # If there's a malformed line, skip it
                    continue

    root = tk.Tk()
    editor = JSONLEditor(root, records, output_file, saved_records)
    root.protocol("WM_DELETE_WINDOW", editor.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
