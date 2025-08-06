"""
manager_gui_editable.py

Unified project manager GUI for system-tech digital twins with:
- In-place view/edit/add/delete of system and tech elements
- Project folder structure, JSON persistence
- Built-in modal editing style via double-click
- Ready for technology linking and interconnection extensions

Author: Your Team
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
from system_model import SystemModel
from technology_model import TechnologyModel

class EditableManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Editable Digital Twin Manager")
        self.project_path = None
        self.system_model = None
        self.technology_model = None

        self.build_gui()

    def build_gui(self):
        top = tk.Frame(self.root)
        top.pack(fill=tk.X, padx=8, pady=4)
        tk.Button(top, text="📁 Open Project", command=self.open_project).pack(side=tk.LEFT)
        tk.Button(top, text="➕ New Project", command=self.new_project).pack(side=tk.LEFT, padx=7)
        self.project_label = tk.Label(top, text="No project loaded", fg="gray")
        self.project_label.pack(side=tk.RIGHT)

        self.content = tk.Frame(self.root)
        self.content.pack(fill=tk.BOTH, expand=True)

        self.tip = tk.Label(self.content, text="Create or open a project folder to begin", fg="gray")
        self.tip.pack(pady=30)

    def open_project(self):
        folder = filedialog.askdirectory(title="Select project folder")
        if not folder:
            return
        if not all(os.path.exists(os.path.join(folder, f))
                   for f in ["systems.json", "technologies.json"]):
            messagebox.showerror("Invalid Folder", "Missing systems.json or technologies.json")
            return
        self.load_project(folder)

    def new_project(self):
        parent = filedialog.askdirectory(title="Select location to create project")
        if not parent:
            return
        name = simpledialog.askstring("New Project", "Enter project name:")
        if not name:
            return
        folder = os.path.join(parent, name.replace(" ", "_"))
        os.makedirs(folder, exist_ok=True)
        for file in ["systems.json", "technologies.json"]:
            path = os.path.join(folder, file)
            with open(path, "w") as f:
                f.write("[]")
        self.load_project(folder)

    def load_project(self, folder):
        self.project_path = folder
        self.system_model = SystemModel(os.path.join(folder, "systems.json"))
        self.technology_model = TechnologyModel(os.path.join(folder, "technologies.json"))
        self.render_edit_interface()
        self.project_label.config(text=f"📂 Project: {os.path.basename(folder)}")

    def render_edit_interface(self):
        for w in self.content.winfo_children():
            w.destroy()

        frame_l = tk.Frame(self.content)
        frame_l.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        frame_r = tk.Frame(self.content)
        frame_r.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(frame_l, text="Systems", font=("Arial", 12, "bold")).pack()
        self.tree_sys = ttk.Treeview(frame_l, height=22)
        self.tree_sys.pack(fill=tk.BOTH, expand=True)
        self.tree_sys.bind("<Double-1>", self.edit_system_item)

        tk.Button(frame_l, text="➕ Add System", command=self.add_system_item).pack(pady=5)
        tk.Button(frame_l, text="❌ Delete Selected", command=self.delete_system_item).pack()

        tk.Label(frame_r, text="Technologies", font=("Arial", 12, "bold")).pack()
        self.tree_tech = ttk.Treeview(frame_r, height=22)
        self.tree_tech.pack(fill=tk.BOTH, expand=True)
        self.tree_tech.bind("<Double-1>", self.edit_tech_item)

        tk.Button(frame_r, text="➕ Add Technology", command=self.add_tech_item).pack(pady=5)
        tk.Button(frame_r, text="❌ Delete Selected", command=self.delete_tech_item).pack()

        self.refresh_trees()

    def refresh_trees(self):
        self.tree_sys.delete(*self.tree_sys.get_children())
        self.tree_tech.delete(*self.tree_tech.get_children())

        roots = [i for i in self.system_model.items.values() if i.parent_code == "000000"]
        for root in sorted(roots, key=lambda x: x.code):
            self.insert_node(self.tree_sys, root, self.system_model)

        roots = [i for i in self.technology_model.items.values() if i.parent_code == "000000"]
        for root in sorted(roots, key=lambda x: x.code):
            self.insert_node(self.tree_tech, root, self.technology_model)

    def insert_node(self, tree, item, model, parent=""):
        node_id = tree.insert(parent, "end", text=f"{item.name} | {item.full_code}")
        for child_code in item.children_codes:
            child = model.get_item(child_code)
            if child:
                self.insert_node(tree, child, model, parent=node_id)

    def add_system_item(self):
        name = simpledialog.askstring("New System Item", "Enter name:")
        desc = simpledialog.askstring("Description", "Enter optional description:") or ""
        parent_code = None

        sel = self.tree_sys.selection()
        if sel:
            sel_code = self.tree_sys.item(sel[0], "text").split("|")[-1].strip()
            parent_code = sel_code

        self.system_model.create_item(name=name, description=desc, parent_code=parent_code)
        self.system_model.save()
        self.refresh_trees()

    def add_tech_item(self):
        name = simpledialog.askstring("New Technology", "Enter name:")
        desc = simpledialog.askstring("Description", "Enter optional description:") or ""
        parent_code = None

        sel = self.tree_tech.selection()
        if sel:
            sel_code = self.tree_tech.item(sel[0], "text").split("|")[-1].strip()
            parent_code = sel_code

        self.technology_model.create_item(name=name, description=desc, parent_code=parent_code)
        self.technology_model.save()
        self.refresh_trees()

    def edit_system_item(self, event):
        sel = self.tree_sys.selection()
        if not sel:
            return
        code = self.tree_sys.item(sel[0], "text").split("|")[-1].strip()
        item = self.system_model.get_item(code)
        if not item:
            return
        new_name = simpledialog.askstring("Edit Name", "Enter new name:", initialvalue=item.name)
        new_desc = simpledialog.askstring("Edit Description", "Enter new description:", initialvalue=item.description)
        if new_name:
            item.name = new_name
        if new_desc is not None:
            item.description = new_desc
        self.system_model.save()
        self.refresh_trees()

    def edit_tech_item(self, event):
        sel = self.tree_tech.selection()
        if not sel:
            return
        code = self.tree_tech.item(sel[0], "text").split("|")[-1].strip()
        item = self.technology_model.get_item(code)
        if not item:
            return
        new_name = simpledialog.askstring("Edit Name", "Enter new name:", initialvalue=item.name)
        new_desc = simpledialog.askstring("Edit Description", "Enter new description:", initialvalue=item.description)
        if new_name:
            item.name = new_name
        if new_desc is not None:
            item.description = new_desc
        self.technology_model.save()
        self.refresh_trees()

    def delete_system_item(self):
        sel = self.tree_sys.selection()
        if not sel:
            return
        code = self.tree_sys.item(sel[0], "text").split("|")[-1].strip()
        if messagebox.askyesno("Confirm", "Delete this system item (and children)?"):
            self.system_model.items.pop(code, None)
            self.system_model.save()
            self.refresh_trees()

    def delete_tech_item(self):
        sel = self.tree_tech.selection()
        if not sel:
            return
        code = self.tree_tech.item(sel[0], "text").split("|")[-1].strip()
        if messagebox.askyesno("Confirm", "Delete this technology item (and children)?"):
            self.technology_model.items.pop(code, None)
            self.technology_model.save()
            self.refresh_trees()

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x700")
    app = EditableManagerGUI(root)
    root.mainloop()
