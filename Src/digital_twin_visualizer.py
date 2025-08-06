"""
digital_twin_visualizer.py

A full-stack digital twin visualization tool.

- Left pane: Collapsed system hierarchy tree for navigation (auto-collapse optional)
- Right (top): Table showing technology assignments for the selected system node
- Right (bottom): Table listing all element-to-element connections (where the selected element is the source)
- Project folders must contain: systems.json, technologies.json, connections.json
- Data model hooks: plug in your system_model.py, technology_model.py, and connections_gui.ConnectionManager

Author: Your Organization
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

# Example: Proper imports from your existing modules
# from system_model import SystemModel
# from technology_model import TechnologyModel
# from connections_gui import ConnectionManager

class DigitalTwinVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Digital Twin Full Stack Visualizer")

        self.project_folder = None
        self.system_model = None
        self.tech_model = None
        self.conn_manager = None

        self.setup_gui()

    def setup_gui(self):
        # --- Project loading ---
        top = tk.Frame(self.root)
        top.pack(fill=tk.X, padx=3, pady=3)
        tk.Button(top, text="Load Project", command=self.load_project).pack(side=tk.LEFT)
        self.lbl_proj = tk.Label(top, text="No project loaded", fg="gray")
        self.lbl_proj.pack(side=tk.RIGHT)

        main = tk.PanedWindow(self.root, sashrelief=tk.RAISED, sashwidth=6)
        main.pack(fill=tk.BOTH, expand=True)

        # Left: System tree
        left = tk.Frame(main)
        tk.Label(left, text="System Hierarchy", font=("Arial", 12, "bold")).pack(pady=3)
        self.tree_sys = ttk.Treeview(left, show="tree", height=28)
        self.tree_sys.pack(fill=tk.BOTH, expand=True, padx=3, pady=4)
        self.tree_sys.bind("<<TreeviewSelect>>", self.on_tree_select)
        main.add(left, minsize=260)

        # Right split vertical for tech/connections
        right = tk.PanedWindow(main, orient=tk.VERTICAL, sashwidth=4)
        main.add(right)

        # Top right: tech assignments
        frame_top = tk.Frame(right)
        tk.Label(frame_top, text="Technology Assignments for Node", font=("Arial", 11, "bold")).pack()
        self.tbl_tech = ttk.Treeview(frame_top, columns=("name","code"), show="headings", height=12)
        self.tbl_tech.heading("name", text="Tech Name")
        self.tbl_tech.heading("code", text="Tech Code")
        self.tbl_tech.pack(fill=tk.BOTH, expand=True)
        right.add(frame_top, minsize=120)

        # Bottom right: connections table
        frame_bot = tk.Frame(right)
        tk.Label(frame_bot, text="Connections for Node (Targets)", font=("Arial", 11, "bold")).pack()
        self.tbl_conn = ttk.Treeview(frame_bot, columns=("target","type","desc"), show="headings", height=14)
        self.tbl_conn.heading("target", text="Target Element")
        self.tbl_conn.heading("type", text="Type")
        self.tbl_conn.heading("desc", text="Description")
        self.tbl_conn.pack(fill=tk.BOTH, expand=True)
        right.add(frame_bot)

    def load_project(self):
        folder = filedialog.askdirectory(title="Select a project folder")
        if not folder:
            return

        required = ["systems.json", "technologies.json", "connections.json"]
        missing = [f for f in required if not os.path.exists(os.path.join(folder, f))]
        if missing:
            messagebox.showerror("Error", f"Missing required files: {missing}")
            return

        # Use your real models here:
        from system_model import SystemModel
        from technology_model import TechnologyModel
        from connections_gui import ConnectionManager
        self.system_model = SystemModel(os.path.join(folder, "systems.json"))
        self.tech_model = TechnologyModel(os.path.join(folder, "technologies.json"))
        self.conn_manager = ConnectionManager(os.path.join(folder, "connections.json"))
        self.project_folder = folder
        self.lbl_proj.config(text=f"Project: {os.path.basename(folder)}", fg="green")
        self.refresh_tree()

    def refresh_tree(self):
        self.tree_sys.delete(*self.tree_sys.get_children())
        if not self.system_model:
            return
        roots = [i for i in self.system_model.items.values() if i.parent_code == "000000"]
        for root in sorted(roots, key=lambda x: x.code):
            self.insert_node(root, "")

    def insert_node(self, item, parent):
        node_id = self.tree_sys.insert(parent, "end", text=f"{item.name} | {item.full_code}", values=[item.full_code])
        for child_code in item.children_codes:
            child = self.system_model.get_item(child_code)
            if child:
                self.insert_node(child, node_id)

    def on_tree_select(self, e):
        sel = self.tree_sys.selection()
        if not sel:
            self.tbl_tech.delete(*self.tbl_tech.get_children())
            self.tbl_conn.delete(*self.tbl_conn.get_children())
            return
        code = self.tree_sys.item(sel[0], "text").split("|")[-1].strip()
        self.update_tech_table(code)
        self.update_conn_table(code)

    def update_tech_table(self, code):
        self.tbl_tech.delete(*self.tbl_tech.get_children())
        if not code or not self.tech_model or not self.system_model:
            return
        item = self.system_model.get_item(code)
        if not item or not getattr(item, 'technology_refs', []):
            return
        for t_code in item.technology_refs:
            t = self.tech_model.get_item(t_code)
            name = t.name if t else "[MISSING]"
            self.tbl_tech.insert("", "end", values=(name, t_code))

    def update_conn_table(self, code):
        self.tbl_conn.delete(*self.tbl_conn.get_children())
        if not code or not self.conn_manager:
            return
        for c in self.conn_manager.connections:
            if c.source == code:
                tgt = self.system_model.get_item(c.target) if hasattr(self.system_model, 'get_item') else None
                tgt_name = f"{tgt.name} | {tgt.full_code}" if tgt else c.target
                self.tbl_conn.insert("", "end", values=(tgt_name, getattr(c, 'type_label', getattr(c, 'type', '[?TYPE]')), getattr(c, 'description', getattr(c, 'desc', ''))))

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1024x660")
    DigitalTwinVisualizer(root)
    root.mainloop()
