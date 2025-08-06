"""
connections_gui.py

GUI to create and manage connections (by relationship type) between any two system elements,
with optional custom description. Connections stored as unique-UUID entries in a project's connections.json.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import uuid

# Standard connection types with internal IDs
CONNECTION_TYPES = [
    ("Mechanical", "MECH"),
    ("Electrical", "ELEC"),
    ("Magnetic", "MAGN"),
    ("Data", "DATA"),
    ("Logical", "LOGI"),
    ("Hydraulic", "HYDR"),
    ("Pneumatic", "PNUM"),
    ("Spring", "SPRG"),
    ("Ground", "GRND"),
    ("RF", "RF___"),
    ("Flexible", "FLEX"),
    ("String", "STRN"),
    ("Cable", "CABL"),
    ("Custom...", "CUST"),
]

class Connection:
    def __init__(self, source_code, conn_type_id, conn_type_label, target_code, description=""):
        self.uuid = str(uuid.uuid4())
        self.source = source_code
        self.type_id = conn_type_id
        self.type_label = conn_type_label
        self.target = target_code
        self.description = description

    def to_dict(self):
        return {
            "uuid": self.uuid,
            "source": self.source,
            "type_id": self.type_id,
            "type_label": self.type_label,
            "target": self.target,
            "description": self.description
        }

class ConnectionManager:
    def __init__(self, save_path):
        self.save_path = save_path
        self.connections = []
        self.load()

    def add_connection(self, conn):
        self.connections.append(conn)
        self.save()

    def save(self):
        with open(self.save_path, "w") as f:
            json.dump([c.to_dict() for c in self.connections], f, indent=2)

    def load(self):
        if os.path.exists(self.save_path):
            with open(self.save_path, "r") as f:
                for entry in json.load(f):
                    self.connections.append(Connection(
                        entry["source"], entry["type_id"], entry["type_label"],
                        entry["target"], entry.get("description", "")
                    ))

class ConnectionGUI:
    def __init__(self, root, system_elements, project_folder):
        self.root = root
        self.root.title("Create System Element Connections")
        self.system_elements = system_elements
        self.conn_mgr = ConnectionManager(os.path.join(project_folder, "connections.json"))

        tk.Label(root, text="Source Element:").grid(row=0, column=0, sticky="e", padx=4, pady=5)
        tk.Label(root, text="Connection Type:").grid(row=1, column=0, sticky="e", padx=4, pady=5)
        tk.Label(root, text="Target Element:").grid(row=2, column=0, sticky="e", padx=4, pady=5)
        tk.Label(root, text="Description:").grid(row=3, column=0, sticky="e", padx=4, pady=5)

        self.src_cb = ttk.Combobox(root, values=[f"{e['name']} | {e['full_code']}" for e in self.system_elements], width=38)
        self.src_cb.grid(row=0, column=1, padx=4, pady=5)
        self.conn_cb = ttk.Combobox(root, values=[lbl for lbl, _ in CONNECTION_TYPES], width=38, state="readonly")
        self.conn_cb.set(CONNECTION_TYPES[0][0])
        self.conn_cb.grid(row=1, column=1, padx=4, pady=5)
        self.tgt_cb = ttk.Combobox(root, values=[f"{e['name']} | {e['full_code']}" for e in self.system_elements], width=38)
        self.tgt_cb.grid(row=2, column=1, padx=4, pady=5)
        self.desc_entry = tk.Entry(root, width=40)
        self.desc_entry.grid(row=3, column=1, padx=4, pady=5)
        self.custom_type_entry = tk.Entry(root, width=32)  # Hidden, if "Custom..." picked

        tk.Button(root, text="Create Connection", command=self.create).grid(row=4, column=1, pady=10)
        self.status_lbl = tk.Label(root, text="", fg="green")
        self.status_lbl.grid(row=5, column=0, columnspan=2)

        # Show/hide custom label entry as needed
        self.conn_cb.bind("<<ComboboxSelected>>", self.on_conn_type_change)

    def on_conn_type_change(self, event):
        if self.conn_cb.get() == "Custom...":
            self.custom_type_entry.grid(row=1, column=2, padx=4)
            self.custom_type_entry.delete(0, tk.END)
            self.custom_type_entry.insert(0, "Enter type label")
        else:
            self.custom_type_entry.grid_forget()

    def create(self):
        src = self.src_cb.get()
        tgt = self.tgt_cb.get()
        if not src or not tgt or src == tgt:
            messagebox.showerror("Selection Error", "Pick two distinct elements.")
            return
        src_code = src.split("|")[-1].strip()
        tgt_code = tgt.split("|")[-1].strip()
        ctype_label = self.conn_cb.get()
        idx = [lbl for lbl, _ in CONNECTION_TYPES].index(ctype_label)
        ctype_id = CONNECTION_TYPES[idx][1]
        if ctype_label == "Custom...":
            label = self.custom_type_entry.get().strip()
            if not label:
                messagebox.showerror("Type Error", "Custom type label required.")
                return
            ctype_label = label
        desc = self.desc_entry.get().strip()
        conn = Connection(src_code, ctype_id, ctype_label, tgt_code, desc)
        self.conn_mgr.add_connection(conn)
        self.status_lbl.config(text=f"Connection created: {src_code} -> {ctype_label} -> {tgt_code}")
        self.desc_entry.delete(0, tk.END)

if __name__ == "__main__":
    # Example—replace with load from your system_model/JSON:
    system_elements = [
        {"name": "Engine", "full_code": "000000010001"},
        {"name": "Battery", "full_code": "000000020001"},
        {"name": "Inverter", "full_code": "000000030001"},
        {"name": "Pump", "full_code": "000000040001"},
    ]
    # Prompt user for project folder:
    root = tk.Tk()
    root.withdraw()
    project_folder = filedialog.askdirectory(title="Select Project Folder For Connections DB")
    if not project_folder:
        messagebox.showinfo("No Project", "No folder selected, exiting.")
        exit()
    root.deiconify()
    root.geometry("530x230")
    ConnectionGUI(root, system_elements, project_folder)
    root.mainloop()
