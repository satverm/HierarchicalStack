"""
manager_gui.py

A unified digital twin manager for:
- Multi-project (folder) management
- System and technology stack design/editing
- Assigning technologies to system elements
- Connecting system elements with standardized connections
- Real-time visual summary tables for all structures

Extendable for future visualizations (graph/network view)
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

from system_model import SystemModel
from technology_model import TechnologyModel
# Use your CONNECTION_TYPES, Connection and ConnectionManager from previous answers
from connections_gui import CONNECTION_TYPES, ConnectionManager, Connection

class ManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Unified Digital Twin Manager")
        self.project_path = None
        self.system_model = None
        self.technology_model = None
        self.connection_manager = None
        self.selected_sys_code = None

        self.setup_ui()

    def setup_ui(self):
        top = tk.Frame(self.root)
        top.pack(fill=tk.X, padx=8, pady=8)
        tk.Button(top, text="📁 Open Project", command=self.open_project).pack(side=tk.LEFT)
        tk.Button(top, text="🆕 New Project", command=self.create_project).pack(side=tk.LEFT, padx=8)
        self.project_label = tk.Label(top, text="No project loaded", fg="gray")
        self.project_label.pack(side=tk.RIGHT)

        self.work_frame = tk.Frame(self.root)
        self.work_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(self.work_frame, text="Create or open a project to start modeling.", foreground="gray").pack(pady=20)

    def open_project(self):
        folder = filedialog.askdirectory(title="Open project folder")
        if not folder:
            return
        if not os.path.exists(os.path.join(folder, "systems.json")) or \
           not os.path.exists(os.path.join(folder, "technologies.json")):
            messagebox.showwarning("Invalid Project", "Selected folder missing model files.")
            return
        self.load_project(folder)

    def create_project(self):
        folder = filedialog.askdirectory(title="Select location for new project")
        if not folder:
            return
        name = tk.simpledialog.askstring("New Project", "Project name:")
        if not name:
            return
        project_path = os.path.join(folder, name.strip().replace(" ", "_"))
        os.makedirs(project_path, exist_ok=True)
        for fname in ["systems.json", "technologies.json", "connections.json"]:
            fpath = os.path.join(project_path, fname)
            if not os.path.exists(fpath):
                with open(fpath, "w") as f:
                    f.write("[]")
        self.load_project(project_path)

    def load_project(self, path):
        self.project_path = path
        self.system_model = SystemModel(os.path.join(path, "systems.json"))
        self.technology_model = TechnologyModel(os.path.join(path, "technologies.json"))
        self.connection_manager = ConnectionManager(os.path.join(path, "connections.json"))
        self.project_label.config(text=f"📂 {os.path.basename(path)}", fg="green")
        self.render_workbench()

    def render_workbench(self):
        for w in self.work_frame.winfo_children():
            w.destroy()

        sys_frame = tk.Frame(self.work_frame)
        sys_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=6)
        tech_frame = tk.Frame(self.work_frame)
        tech_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=6)
        conn_frame = tk.Frame(self.work_frame)
        conn_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=6, pady=6)

        # SYSTEM TREE (on the left)
        tk.Label(sys_frame, text="Systems").pack()
        self.sys_tree = ttk.Treeview(sys_frame, height=18)
        self.sys_tree.pack(fill=tk.BOTH, expand=True)
        self.refresh_system_tree()

        # TECHNOLOGY TREE (center left)
        tk.Label(tech_frame, text="Technologies").pack()
        self.tech_tree = ttk.Treeview(tech_frame, height=18)
        self.tech_tree.pack(fill=tk.BOTH, expand=True)
        self.refresh_technology_tree()

        # CONNECTIONS & LINKING
        tk.Label(conn_frame, text="Connect Elements").pack()
        self.src_cb = ttk.Combobox(conn_frame, values=self._system_elem_list(), width=36)
        self.src_cb.pack(pady=4)
        self.tgt_cb = ttk.Combobox(conn_frame, values=self._system_elem_list(), width=36)
        self.tgt_cb.pack(pady=4)
        self.conn_cb = ttk.Combobox(conn_frame, values=[lbl for lbl, _ in CONNECTION_TYPES], state="readonly", width=36)
        self.conn_cb.set("Mechanical")
        self.conn_cb.pack(pady=4)
        self.conn_cb.bind("<<ComboboxSelected>>", self._handle_custom_entry)
        self.custom_conn_entry = tk.Entry(conn_frame, width=24)
        tk.Label(conn_frame, text="Description:").pack()
        self.conn_desc = tk.Entry(conn_frame, width=38)
        self.conn_desc.pack(pady=2)
        tk.Button(conn_frame, text="Create Connection", command=self.create_connection).pack(pady=8)
        self.conn_status = tk.Label(conn_frame, text="", fg="green")
        self.conn_status.pack()

        # CONNECTIONS TABLE
        tk.Label(conn_frame, text="Connections Table:").pack(pady=2)
        self.conn_table = ttk.Treeview(conn_frame, columns=("source", "type", "target", "desc"), show="headings", height=8)
        for col in ("source", "type", "target", "desc"):
            self.conn_table.heading(col, text=col.capitalize())
        self.conn_table.pack(pady=6)
        self.src_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_conn_table())
        self.tgt_cb.bind("<<ComboboxSelected>>", lambda e: self.refresh_conn_table())
        self.refresh_conn_table()

    def _system_elem_list(self):
        return [f"{i.name} | {i.full_code}" for i in self.system_model.items.values()]

    def refresh_system_tree(self):
        self.sys_tree.delete(*self.sys_tree.get_children())
        roots = [i for i in self.system_model.items.values() if i.parent_code == "000000"]
        for root in sorted(roots, key=lambda x: x.code):
            self._insert_sys_node(root, "")

    def _insert_sys_node(self, item, parent):
        node_id = self.sys_tree.insert(parent, "end", text=f"{item.name} | {item.full_code}", values=[item.full_code])
        for child_code in item.children_codes:
            child = self.system_model.get_item(child_code)
            if child:
                self._insert_sys_node(child, node_id)

    def refresh_technology_tree(self):
        self.tech_tree.delete(*self.tech_tree.get_children())
        roots = [j for j in self.technology_model.items.values() if j.parent_code == "000000"]
        for root in sorted(roots, key=lambda x: x.code):
            self._insert_tech_node(root, "")

    def _insert_tech_node(self, item, parent):
        node_id = self.tech_tree.insert(parent, "end", text=f"{item.name} | {item.full_code}", values=[item.full_code])
        for child_code in item.children_codes:
            child = self.technology_model.get_item(child_code)
            if child:
                self._insert_tech_node(child, node_id)

    def _handle_custom_entry(self, event):
        if self.conn_cb.get() == "Custom...":
            self.custom_conn_entry.pack(pady=2)
        else:
            self.custom_conn_entry.pack_forget()

    def create_connection(self):
        if not self.src_cb.get() or not self.tgt_cb.get():
            messagebox.showerror("Error", "Select both source and target elements.")
            return
        if self.src_cb.get() == self.tgt_cb.get():
            messagebox.showerror("Error", "Cannot connect an item to itself.")
            return

        # Parse source/target codes
        source_code = self.src_cb.get().split("|")[-1].strip()
        target_code = self.tgt_cb.get().split("|")[-1].strip()
        type_label = self.conn_cb.get()
        type_id = dict(CONNECTION_TYPES).get(type_label, "CUST")
        if type_label == "Custom...":
            custom_label = self.custom_conn_entry.get().strip()
            if not custom_label:
                messagebox.showerror("Missing", "Provide label for custom connection type.")
                return
            type_label = custom_label

        desc = self.conn_desc.get().strip()
        from connections_gui import Connection
        conn = Connection(source_code, type_id, type_label, target_code, desc)
        self.connection_manager.add_connection(conn)
        self.conn_status.config(text=f"Connection created: {type_label}")
        self.refresh_conn_table()
        self.conn_desc.delete(0, tk.END)

    def refresh_conn_table(self):
        self.conn_table.delete(*self.conn_table.get_children())
        selected_src = self.src_cb.get()
        selected_tgt = self.tgt_cb.get()
        src_code = selected_src.split("|")[-1].strip() if selected_src else None
        tgt_code = selected_tgt.split("|")[-1].strip() if selected_tgt else None

        for c in self.connection_manager.connections:
            show = False
            if src_code and tgt_code:
                show = (c.source == src_code and c.target == tgt_code)
            elif src_code:
                show = c.source == src_code
            elif tgt_code:
                show = c.target == tgt_code
            if show:
                self.conn_table.insert("", tk.END, values=(c.source, c.type_label, c.target, c.description))

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x700")
    ManagerGUI(root)
    root.mainloop()
