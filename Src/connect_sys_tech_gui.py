import tkinter as tk
from tkinter import ttk, messagebox
from system_model import SystemModel
from technology_model import TechnologyModel

class ConnectSysTechGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("System–Technology Mesh Modeler")

        self.system_model = SystemModel()
        self.technology_model = TechnologyModel()
        self.selected_sys_code = None

        # UI Frames
        main_frame = tk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # System Tree
        sys_frame = tk.LabelFrame(main_frame, text="System Hierarchy")
        sys_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.sys_tree = ttk.Treeview(sys_frame, height=25)
        self.sys_tree.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        self.sys_tree.bind("<<TreeviewSelect>>", self.on_sys_tree_select)

        # Tech Tree
        tech_frame = tk.LabelFrame(main_frame, text="Technology Hierarchy")
        tech_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)
        self.tech_tree = ttk.Treeview(tech_frame, height=25, selectmode='extended')
        self.tech_tree.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Assignment panel
        panel_frame = tk.Frame(main_frame)
        panel_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=8, pady=8)
        tk.Label(panel_frame, text="Selected System Node").pack(pady=2)
        self.sys_label = tk.Label(panel_frame, text="-", fg="blue")
        self.sys_label.pack(pady=2)
        tk.Label(panel_frame, text="Assign Technologies:").pack(pady=2)
        self.assign_btn = tk.Button(panel_frame, text="Assign Selected Technologies", command=self.assign_technologies)
        self.assign_btn.pack(pady=5)
        tk.Label(panel_frame, text="Technologies Assigned:").pack(pady=2)
        self.tech_listbox = tk.Listbox(panel_frame, width=46)
        self.tech_listbox.pack(fill=tk.BOTH, expand=True, pady=2)
        self.unassign_btn = tk.Button(panel_frame, text="Unassign Selected Technology", command=self.unassign_technology)
        self.unassign_btn.pack(pady=2)

        # Load/Refresh buttons
        action_frame = tk.Frame(panel_frame)
        action_frame.pack(fill=tk.X)
        tk.Button(action_frame, text="Save All", command=self.save_all).pack(side=tk.LEFT, padx=8)
        tk.Button(action_frame, text="Refresh All", command=self.refresh_all).pack(side=tk.RIGHT, padx=8)

        self.refresh_all()

    # --- System Tree ---
    def refresh_system_tree(self):
        self.sys_tree.delete(*self.sys_tree.get_children())
        roots = [i for i in self.system_model.items.values() if i.parent_code == "000000"]
        for root in sorted(roots, key=lambda x: x.code):
            self.insert_sys_tree_node(root, "")
    def insert_sys_tree_node(self, item, parent):
        node_id = self.sys_tree.insert(parent, "end", text=f"{item.name} | {item.full_code}", values=[item.full_code])
        for child_code in item.children_codes:
            child = self.system_model.get_item(child_code)
            if child:
                self.insert_sys_tree_node(child, node_id)

    # --- Technology Tree ---
    def refresh_technology_tree(self):
        self.tech_tree.delete(*self.tech_tree.get_children())
        roots = [j for j in self.technology_model.items.values() if j.parent_code == "000000"]
        for root in sorted(roots, key=lambda x: x.code):
            self.insert_tech_tree_node(root, "")
    def insert_tech_tree_node(self, item, parent):
        node_id = self.tech_tree.insert(parent, "end", text=f"{item.name} | {item.full_code}", values=[item.full_code])
        for child_code in item.children_codes:
            child = self.technology_model.get_item(child_code)
            if child:
                self.insert_tech_tree_node(child, node_id)

    # --- Assignment Display ---
    def on_sys_tree_select(self, event):
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
            messagebox.showinfo("Select System", "Select a system node to assign to.")
            return
        selected = self.tech_tree.selection()
        if not selected:
            messagebox.showinfo("Select Technologies", "Select one or more technology nodes.")
            return
        for sel_node in selected:
            tech_code = self.tech_tree.item(sel_node, "values")[0]
            self.system_model.assign_technology(self.selected_sys_code, tech_code)
        self.on_sys_tree_select(None)  # Update assigned list
        self.status_popup("Assignment complete – saved.")

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
        self.on_sys_tree_select(None)
        self.status_popup("Unassignment complete – saved.")

    # --- Persist/refresh ---
    def save_all(self):
        self.system_model.save()
        self.technology_model.save()
        self.status_popup("Saved all data.")

    def refresh_all(self):
        self.system_model.load()
        self.technology_model.load()
        self.refresh_system_tree()
        self.refresh_technology_tree()
        self.tech_listbox.delete(0, tk.END)
        self.sys_label.config(text="-")
        self.selected_sys_code = None

    def status_popup(self, text):
        self.status = getattr(self, 'status', None)
        if self.status:
            self.status.config(text=text)
        else:
            messagebox.showinfo("Status", text)

if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1300x700")
    ConnectSysTechGUI(root)
    root.mainloop()
