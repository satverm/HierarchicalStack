import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json
import uuid

# Standard connection types
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
        if os.path.exists(self.save_path):
            with open(self.save_path, "r") as f:
                data = json.load(f)
                for item in data:
                    c = Connection(
                        item["source"], item["type_id"], item["type_label"],
                        item["target"], item.get("description", "")
                    )
                    c.uuid = item["uuid"]
                    self.connections.append(c)

class ConnectionGUI:
    def __init__(self, root, system_elements, save_folder):
        self.root = root
        self.system_elements = system_elements
        self.save_path = os.path.join(save_folder, "connections.json")
        self.manager = ConnectionManager(self.save_path)

        tk.Label(root, text="Source Element").grid(row=0, column=0, sticky="e")
        self.src_cb = ttk.Combobox(root, values=self._element_list(), width=42)
        self.src_cb.grid(row=0, column=1)

        tk.Label(root, text="Target Element").grid(row=1, column=0, sticky="e")
        self.tgt_cb = ttk.Combobox(root, values=self._element_list(), width=42)
        self.tgt_cb.grid(row=1, column=1)

        tk.Label(root, text="Connection Type").grid(row=2, column=0, sticky="e")
        self.conn_cb = ttk.Combobox(root, values=[label for label, _ in CONNECTION_TYPES], state="readonly", width=42)
        self.conn_cb.set("Mechanical")
        self.conn_cb.grid(row=2, column=1)

        self.custom_type_entry = tk.Entry(root)  # dynamically shown if needed
        self.conn_cb.bind("<<ComboboxSelected>>", self._conn_type_selected)

        tk.Label(root, text="Description (optional)").grid(row=3, column=0, sticky="e")
        self.desc = tk.Entry(root, width=44)
        self.desc.grid(row=3, column=1)

        tk.Button(root, text="Create Connection", command=self.create_connection).grid(row=5, column=1, pady=10)
        self.status = tk.Label(root, text="", fg="green")
        self.status.grid(row=6, column=0, columnspan=2)

    def _element_list(self):
        return [f"{e['name']} | {e['full_code']}" for e in self.system_elements]

    def _conn_type_selected(self, event=None):
        if self.conn_cb.get() == "Custom...":
            self.custom_type_entry.grid(row=2, column=2, padx=5)
        else:
            self.custom_type_entry.grid_forget()

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
            custom_label = self.custom_type_entry.get().strip()
            if not custom_label:
                messagebox.showerror("Custom Type Missing", "Enter a name for custom connection.")
                return
            type_label = custom_label

        desc = self.desc.get().strip()
        conn = Connection(source_code, type_id, type_label, target_code, desc)
        self.manager.add_connection(conn)

        self.status.config(text="✅ Connection saved.")
        self.desc.delete(0, tk.END)
        self.custom_type_entry.delete(0, tk.END)
        self.conn_cb.set("Mechanical")

# Test execution
if __name__ == "__main__":
    # Example simulated system elements
    system_elements = [
        {"name": "Engine", "full_code": "010001020001"},
        {"name": "Battery", "full_code": "010002020002"},
        {"name": "Controller", "full_code": "010003020003"},
    ]

    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(title="Select Project Folder")
    if not folder:
        messagebox.showerror("No Folder", "No project folder selected.")
        exit()

    root.deiconify()
    root.title("System Element Interconnection")
    root.geometry("600x260")
    ConnectionGUI(root, system_elements, folder)
    root.mainloop()
