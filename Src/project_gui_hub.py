import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

from system_model import SystemModel
from technology_model import TechnologyModel

class UnifiedProjectGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("System–Technology Project Manager")
        self.project_path = None
        self.system_model = None
        self.technology_model = None
        self.selected_sys_code = None

        self.setup_ui()

    def setup_ui(self):
        # Top controls
        top = tk.Frame(self.root)
        top.pack(fill=tk.X, padx=8, pady=8)
        tk.Button(top, text="📁 Open Project", command=self.open_project).pack(side=tk.LEFT, padx=2)
        tk.Button(top, text="🆕 New Project", command=self.create_project).pack(side=tk.LEFT, padx=2)
        self.project_label = tk.Label(top, text="No project loaded", fg="gray")
        self.project_label.pack(side=tk.RIGHT)

        self.editor_frame = tk.Frame(self.root)
        self.editor_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(self.editor_frame, text="Create or open a project to start modeling.", foreground="gray")\
            .pack(pady=20)

    def open_project(self):
        folder = filedialog.askdirectory(title="Open project folder")
        if folder:
            if not os.path.exists(os.path.join(folder, "systems.json")) \
                or not os.path.exists(os.path.join(folder, "technologies.json")):
                messagebox.showwarning("Invalid Project", "Selected folder doesn't have model files.")
                return
            self.load_project(folder)

    def create_project(self):
        folder = filedialog.askdirectory(title="Select location for a new project")
        if not folder:
            return
        name = tk.simpledialog.askstring("New Project", "Enter project name:")
        if not name:
            return
        project_dir = os.path.join(folder, name.strip().replace(" ", "_"))
        if not os.path.exists(project_dir):
            os.mkdir(project_dir)
        for fname in ["systems.json", "technologies.json"]:
            fpath = os.path.join(project_dir, fname)
            if not os.path.exists(fpath):
                with open(fpath, "w") as f:
                    f.write("[]")
        self.load_project(project_dir)

    def load_project(self, path):
        self.project_path = path
        self.system_model = SystemModel(os.path.join(path, "systems.json"))
        self.technology_model = TechnologyModel(os.path.join(path, "technologies.json"))
        self.project_label.config(text=f"📂 {os.path.basename(path)}", fg="green")
        self.render_view()

    def render_view(self):
        # Clear/refresh
        for widget in self.editor_frame.winfo_children():
            widget.destroy()

        lf = tk.Frame(self.editor_frame)
        lf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        rf = tk.Frame(self.editor_frame)
        rf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        pf = tk.Frame(self.editor_frame)
        pf.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=8, pady=8)

        # System tree
        tk.Label(lf, text="SYSTEM TREE").pack()
        self.sys_tree = ttk.Treeview(lf, height=26)
        self.sys_tree.pack(fill=tk.BOTH, expand=True)
        self.sys_tree.bind("<<TreeviewSelect>>", self.on_sys_select)
        self.populate_system_tree()

        # Technology tree
        tk.Label(rf, text="TECHNOLOGIES").pack()
        self.tech_tree = ttk.Treeview(rf, height=26, selectmode='extended')
        self.tech_tree.pack(fill=tk.BOTH, expand=True)
        self.populate_technology_tree()

        # Tech assignment panel
        tk.Label(pf, text="Selected System Node").pack(pady=2)
        self.sys_label = tk.Label(pf, text="-", fg="blue")
        self.sys_label.pack(pady=2)
        tk.Label(pf, text="Assign Technologies:").pack(pady=2)
        self.assign_btn = tk.Button(pf, text="Assign Selected Technologies", command=self.assign_technologies)
        self.assign_btn.pack(pady=4)
        tk.Label(pf, text="Technologies Assigned:").pack(pady=2)
        self.tech_listbox = tk.Listbox(pf, width=44)
        self.tech_listbox.pack(fill=tk.BOTH, expand=True, pady=1)
        self.unassign_btn = tk.Button(pf, text="Unassign Selected Technology", command=self.unassign_technology)
        self.unassign_btn.pack(pady=3)

        # Actions
        actions = tk.Frame(pf)
        actions.pack(fill=tk.X)
        tk.Button(actions, text="Save All", command=self.save_all).pack(side=tk.LEFT, padx=8)
        tk.Button(actions, text="Refresh All", command=self.refresh_all).pack(side=tk.RIGHT, padx=8)

    # ------ Core logic for trees and assignment ------
    def populate_system_tree(self):
        self.sys_tree.delete(*self.sys_tree.get_children())
        roots = [i for i in self.system_model.items.values() if i.parent_code == "000000"]
        for root in sorted(roots, key=lambda x: x.code):
            self.insert_sys_node(root, "")

    def insert_sys_node(self, item, parent):
        node_id = self.sys_tree.insert(parent, "end", text=f"{item.name} | {item.full_code}", values=[item.full_code])
        for child_code in item.children_codes:
            child = self.system_model.get_item(child_code)
            if child:
                self.insert_sys_node(child, node_id)

    def populate_technology_tree(self):
        self.tech_tree.delete(*self.tech_tree.get_children())
        roots = [j for j in self.technology_model.items.values() if j.parent_code == "000000"]
        for root in sorted(roots, key=lambda x: x.code):
            self.insert_tech_node(root, "")

    def insert_tech_node(self, item, parent):
        node_id = self.tech_tree.insert(parent, "end", text=f"{item.name} | {item.full_code}", values=[item.full_code])
        for child_code in item.children_codes:
            child = self.technology_model.get_item(child_code)
            if child:
                self.insert_tech_node(child, node_id)

    def on_sys_select(self, event):
        sel = self.sys_tree.selection()
        self.tech_listbox.delete(0, tk.END)
        if not sel:
            self.selected_sys_code = None
            self.sys_label.config(text="-")
            return
        code = self.sys_tree.item(sel[0], "values")[0]
        self.selected_sys_code = code
        item = self.system_model.get_item(code)
        if item:
            self.sys_label.config(text=f"{item.name}\n({item.full_code})")
            for tech_code in item.technology_refs:
                tech = self.technology_model.get_item(tech_code)
                tline = f"{tech.name} | {tech.full_code}" if tech else tech_code
                self.tech_listbox.insert(tk.END, tline)

    def assign_technologies(self):
        if not self.selected_sys_code:
            messagebox.showinfo("Select System", "Select a system node.")
            return
        selected = self.tech_tree.selection()
        if not selected:
            messagebox.showinfo("Select Technologies", "Select one or more technologies.")
            return
        for sel_node in selected:
            tech_code = self.tech_tree.item(sel_node, "values")[0]
            self.system_model.assign_technology(self.selected_sys_code, tech_code)
        self.on_sys_select(None)
        self.status_popup("Assignment complete and saved.")

    def unassign_technology(self):
        if not self.selected_sys_code:
            return
        sel = self.tech_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        code_line = self.tech_listbox.get(idx)
        tech_code = code_line.split("|")[-1].strip()
        item = self.system_model.get_item(self.selected_sys_code)
        if item and tech_code in item.technology_refs:
            item.technology_refs.remove(tech_code)
            self.system_model.save()
        self.on_sys_select(None)
        self.status_popup("Unassigned and saved.")

    def save_all(self):
        self.system_model.save()
        self.technology_model.save()
        self.status_popup("Saved all data.")

    def refresh_all(self):
        self.system_model.load()
        self.technology_model.load()
        self.populate_system_tree()
        self.populate_technology_tree()
        self.tech_listbox.delete(0, tk.END)
        self.sys_label.config(text="-")
        self.selected_sys_code = None

    def status_popup(self, text):
        messagebox.showinfo("Status", text)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1350x720")
    UnifiedProjectGUI(root)
    root.mainloop()
