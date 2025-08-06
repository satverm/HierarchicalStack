"""
connections_gui.py

GUI to connect system elements using standardized connection types (or a custom one).
Displays a real-time table listing all connections matching source/target selection.
Saves connections to <project_folder>/connections.json.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import uuid

# ✅ Standard connection types
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
    ("Custom...", "CUST")
]

# ✅ Basic data model
class Connection:
    def __init__(self, source, conn_type_id, conn_type_label, target, description=""):
        self.uuid = str(uuid.uuid4())
        self.source = source
        self.type_id = conn_type_id
        self.type_label = conn_type_label
        self.target = target
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

    def add_connection(self, conn: Connection):
        self.connections.append(conn)
        self.save()

    def save(self):
        with open(self.save_path, "w") as f:
            json.dump([c.to_dict() for c in self.connections], f, indent=2)

    def load(self):
        self.connections.clear()
        if os.path.exists(self.save_path):
            with open(self.save_path, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict):
                            conn = Connection(
                                item["source"], item["type_id"], item["type_label"],
                                item["target"], item.get("description", "")
                            )
                            conn.uuid = item.get("uuid", str(uuid.uuid4()))
                            self.connections.append(conn)

# ✅ GUI class
class ConnectionGUI:
    def __init__(self, root, system_elements, save_folder):
        self.root = root
        self.system_elements = system_elements
        self.save_path = os.path.join(save_folder, "connections.json")
        self.manager = ConnectionManager(self.save_path)

        tk.Label(root, text="Source Element").grid(row=0, column=0, sticky="e", padx=4)
        self.src_cb = ttk.Combobox(root, values=self._element_list(), width=42)
        self.src_cb.grid(row=0, column=1, padx=4)
        self.src_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())

        tk.Label(root, text="Target Element").grid(row=1, column=0, sticky="e", padx=4)
        self.tgt_cb = ttk.Combobox(root, values=self._element_list(), width=42)
        self.tgt_cb.grid(row=1, column=1, padx=4)
        self.tgt_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_table())

        tk.Label(root, text="Connection Type").grid(row=2, column=0, sticky="e", padx=4)
        self.conn_cb = ttk.Combobox(root, values=[label for label, _ in CONNECTION_TYPES], state="readonly", width=42)
        self.conn_cb.set("Mechanical")
        self.conn_cb.grid(row=2, column=1, padx=4)
        self.conn_cb.bind("<<ComboboxSelected>>", self.on_conn_type_change)

        # Optional custom label
        self.custom_entry = tk.Entry(root, width=30)

        tk.Label(root, text="Description (optional)").grid(row=3, column=0, sticky="e", padx=4)
        self.desc_entry = tk.Entry(root, width=44)
        self.desc_entry.grid(row=3, column=1, padx=4)

        tk.Button(root, text="Create Connection", command=self.create_connection).grid(row=4, column=1, pady=8)
        self.status = tk.Label(root, text="", fg="green")
        self.status.grid(row=5, column=0, columnspan=2)

        # 📊 Table of related connections
        tk.Label(root, text="Matching Connections:").grid(row=6, column=0, sticky="ne", padx=4)
        self.conn_table = ttk.Treeview(root, columns=("source", "type", "target", "desc"), show="headings", height=6)
        self.conn_table.heading("source", text="Source")
        self.conn_table.heading("type", text="Type")
        self.conn_table.heading("target", text="Target")
        self.conn_table.heading("desc", text="Description")
        self.conn_table.grid(row=6, column=1, padx=4, pady=5)

    # ✅ Build input options
    def _element_list(self):
        return [f"{e['name']} | {e['full_code']}" for e in self.system_elements]

    def on_conn_type_change(self, event):
        if self.conn_cb.get() == "Custom...":
            self.custom_entry.grid(row=2, column=2, padx=3)
            self.custom_entry.delete(0, tk.END)
            self.custom_entry.insert(0, "Enter custom label")
        else:
            self.custom_entry.grid_forget()

    def create_connection(self):
        if not self.src_cb.get() or not self.tgt_cb.get():
            messagebox.showerror("Error", "Select both source and target.")
            return
        if self.src_cb.get() == self.tgt_cb.get():
            messagebox.showerror("Error", "Cannot connect element to itself.")
            return

        source_code = self.src_cb.get().split("|")[-1].strip()
        target_code = self.tgt_cb.get().split("|")[-1].strip()
        type_label = self.conn_cb.get()
        type_id = dict(CONNECTION_TYPES).get(type_label, "CUST")

        if type_label == "Custom...":
            type_label = self.custom_entry.get().strip()
            if not type_label:
                messagebox.showerror("Custom Type Missing", "Enter a label for the custom connection.")
                return

        desc = self.desc_entry.get().strip()
        conn = Connection(source_code, type_id, type_label, target_code, desc)
        self.manager.add_connection(conn)

        self.status.config(text="✅ Connection saved.")
        self.desc_entry.delete(0, tk.END)
        self.custom_entry.delete(0, tk.END)
        self.conn_cb.set("Mechanical")
        self.refresh_table()

    def refresh_table(self):
        self.conn_table.delete(*self.conn_table.get_children())
        selected_src = self.src_cb.get()
        selected_tgt = self.tgt_cb.get()

        src_code = selected_src.split("|")[-1].strip() if selected_src else None
        tgt_code = selected_tgt.split("|")[-1].strip() if selected_tgt else None

        for c in self.manager.connections:
            match = (
                (src_code and c.source == src_code) or
                (tgt_code and c.target == tgt_code) or
                (src_code == c.source and tgt_code == c.target)
            )
            if match:
                self.conn_table.insert(
                    "", tk.END,
                    values=(c.source, c.type_label, c.target, c.description)
                )

# 🔧 Entry point
if __name__ == "__main__":
    # Replace with dynamic load from systems.json if desired
    example_system_elements = [
        {"name": "Battery", "full_code": "010001"},
        {"name": "Inverter", "full_code": "010002"},
        {"name": "Electric Motor", "full_code": "010003"},
    ]

    root = tk.Tk()
    root.withdraw()
    project_folder = filedialog.askdirectory(title="Select Project Folder to Store connections.json")
    if not project_folder:
        messagebox.showinfo("Cancelled", "No folder selected. Exiting.")
        exit()

    root.deiconify()
    root.geometry("750x460")
    app = ConnectionGUI(root, example_system_elements, project_folder)
    root.mainloop()
