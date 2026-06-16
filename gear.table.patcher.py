#!/usr/bin/env python3
"""
Gear Table Patcher
------------------------
Lightweight tkinter tool. Loads an MSV80 .bin, locates a known 12-byte
gear-table signature, and (after confirmation) patches it in place to a
new output file. The original file is never modified.

Search  : DF 5F 15 00 DF 6F 15 00 DF 7F 15 00
Replace : BF 5F 25 80 FF DF 23 80 C2 CF 3C 21
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox

SEARCH_BYTES = bytes.fromhex("DF5F1500DF6F1500DF7F1500")
PATCH_BYTES = bytes.fromhex("BF5F2580FFDF2380C2CF3C21")

assert len(SEARCH_BYTES) == 12 and len(PATCH_BYTES) == 12


def find_all(data: bytes, needle: bytes):
    """Return a list of every offset where needle occurs in data."""
    offsets = []
    start = 0
    while True:
        i = data.find(needle, start)
        if i == -1:
            break
        offsets.append(i)
        start = i + 1  # +1 catches overlapping matches too
    return offsets


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Gear Table Patcher")
        self.root.geometry("520x260")
        self.root.resizable(False, False)

        self.file_path = None      # accepted input file
        self.match_offset = None   # confirmed single match offset

        tk.Label(
            root, text="Gear Table Patcher",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=(16, 4))

        self.status = tk.Label(
            root, text="No file loaded.", font=("Segoe UI", 10),
            fg="#444", wraplength=480, justify="center"
        )
        self.status.pack(pady=(4, 8))

        self.addr_label = tk.Label(
            root, text="", font=("Consolas", 11, "bold"), fg="#0a6"
        )
        self.addr_label.pack(pady=(0, 8))

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=4)

        tk.Button(
            btn_frame, text="Open .bin", width=14, command=self.open_file
        ).grid(row=0, column=0, padx=6)

        self.patch_btn = tk.Button(
            btn_frame, text="Patch", width=14, state="disabled",
            command=self.patch
        )
        self.patch_btn.grid(row=0, column=1, padx=6)

    def reset(self):
        self.file_path = None
        self.match_offset = None
        self.patch_btn.config(state="disabled")
        self.addr_label.config(text="")

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Select MSV80 .bin",
            filetypes=[("BIN files", "*.bin"), ("All files", "*.*")]
        )
        if not path:
            return

        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError as e:
            messagebox.showerror("Error", f"Could not read file:\n{e}")
            return

        offsets = find_all(data, SEARCH_BYTES)

        if len(offsets) == 0:
            # Signature absent -> reject the file entirely.
            self.reset()
            self.status.config(text="No file loaded.", fg="#444")
            messagebox.showwarning(
                "Gear table not found",
                "Gear table not found, update DME to latest version"
            )
            return

        if len(offsets) > 1:
            # Ambiguous -> refuse and ask the user to report it.
            self.reset()
            self.status.config(text="No file loaded.", fg="#444")
            messagebox.showwarning(
                "Multiple matches",
                "2 same 12 byte sequences found in 2 different offsets. "
                "Submit a ticket on github with this warning"
            )
            return

        # Exactly one match -> accept the file and arm the Patch button.
        self.file_path = path
        self.match_offset = offsets[0]
        self.status.config(
            text=f"Loaded: {os.path.basename(path)}\nGear table signature found.",
            fg="#222"
        )
        self.addr_label.config(
            text=f"Address: 0x{self.match_offset:08X}  ({self.match_offset})"
        )
        self.patch_btn.config(state="normal")

    def patch(self):
        if self.file_path is None or self.match_offset is None:
            return

        try:
            with open(self.file_path, "rb") as f:
                data = bytearray(f.read())
        except OSError as e:
            messagebox.showerror("Error", f"Could not read file:\n{e}")
            return

        # Re-verify the signature is still where we expect it.
        off = self.match_offset
        if data[off:off + 12] != SEARCH_BYTES:
            messagebox.showerror(
                "Error",
                "Signature no longer matches at the stored address. "
                "Reload the file and try again."
            )
            self.reset()
            return

        data[off:off + 12] = PATCH_BYTES

        base, ext = os.path.splitext(self.file_path)
        out_path = filedialog.asksaveasfilename(
            title="Save patched .bin",
            defaultextension=ext or ".bin",
            initialfile=os.path.basename(base) + "_patched" + (ext or ".bin"),
            filetypes=[("BIN files", "*.bin"), ("All files", "*.*")]
        )
        if not out_path:
            return

        try:
            with open(out_path, "wb") as f:
                f.write(data)
        except OSError as e:
            messagebox.showerror("Error", f"Could not write file:\n{e}")
            return

        self.status.config(
            text=f"Patched -> {os.path.basename(out_path)}", fg="#0a6"
        )
        self.patch_btn.config(state="disabled")
        messagebox.showwarning(
            "Done", "Before flashing correct checksums!"
        )


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
