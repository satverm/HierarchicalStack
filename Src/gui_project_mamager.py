import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

from system_model import SystemModel
from technology_model import TechnologyModel

class ProjectManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("System–Technology Project Workspace")
        self.project_path = None
        self.system_model = None
        self.technology_model = None

        self.setup_ui()

    def setup_ui(self):
        # Top panel with buttons
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
        folder = filedialog.askdirectory(title="Choose an existing system-tech project folder")
        if folder:
            if not os.path.exists(os.path.join(folder, "systems.json")) \
               or not os.path.exists(os.path.join(folder, "technologies.json")):
                messagebox.showwarning("Invalid Project", "Selected folder does not contain valid model files.")
                return
            self.load_project(folder)

    def create_project(self):
        folder = filedialog.askdirectory(title="Select a location to create a new project folder")
        if not folder:
            return
        name = tk.simpledialog.askstring("New Project", "Enter project name:")
        if not name:
            return

        project_dir = os.path.join(folder, name.strip().replace(" ", "_"))
        if not os.path.exists(project_dir):
            os.mkdir(project_dir)

        # Create empty JSON files
        for fname in ["systems.json", "technologies.json"]:
            fname_path = os.path.join(project_dir, fname)
            if not os.path.exists(fname_path):
                with open(fname_path, "w") as f:
                    f.write("[]")

        self.load_project(project_dir)

    def load_project(self, path):
        self.project_path = path
        self.system_model = SystemModel(os.path.join(path, "systems.json"))
        self.technology_model = TechnologyModel(os.path.join(path, "technologies.json"))
        self.project_label.config(text=f"📂 Project: {os.path.basename(path)}", fg="green")
        self.render_basic_view()

    def render_basic_view(self):
        # Clear frame
        for widget in self.editor_frame.winfo_children():
            widget.destroy()

        left_panel = tk.Frame(self.editor_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        right_panel = tk.Frame(self.editor_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=8, pady=8)

        # = System Summary Tree =
        tk.Label(left_panel, text="SYSTEM TREE").pack()
        self.sys_tree = ttk.Treeview(left_panel, height=30)
        self.sys_tree.pack(fill=tk.BOTH, expand=True)
        self.populate_system_tree()

        # = Technology Summary Tree =
        tk.Label(right_panel, text="TECHNOLOGIES").pack()
        self.tech_tree = ttk.Treeview(right_panel, height=30)
        self.tech_tree.pack(fill=tk.BOTH, expand=True)
        self.populate_technology_tree()

    def populate_system_tree(self):
        self.sys_tree.delete(*self.sys_tree.get_children())
        roots = [i for i in self.system_model.items.values() if i.parent_code == "000000"]
        for root in sorted(roots, key=lambda x: x.code):
            self.insert_system_node(root, "")

    def insert_system_node(self, item, parent):
        node_id = self.sys_tree.insert(parent, "end",
            text=f"{item.name} | {item.full_code}", values=[item.full_code])
        for child_code in item.children_codes:
            child = self.system_model.get_item(child_code)
            if child:
                self.insert_system_node(child, node_id)

    def populate_technology_tree(self):
        self.tech_tree.delete(*self.tech_tree.get_children())
        roots = [i for i in self.technology_model.items.values() if i.parent_code == "000000"]
        for root in sorted(roots, key=lambda x: x.code):
            self.insert_technology_node(root, "")

    def insert_technology_node(self, item, parent):
        node_id = self.tech_tree.insert(parent, "end",
            text=f"{item.name} | {item.full_code}", values=[item.full_code])
        for child_code in item.children_codes:
            child = self.technology_model.get_item(child_code)
            if child:
                self.insert_technology_node(child, node_id)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1200x700")
    app = ProjectManagerGUI(root)
    root.mainloop()
