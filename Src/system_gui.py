import tkinter as tk
from tkinter import ttk, messagebox
from system_model import SystemModel

class SystemModelGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("System Modeler")
        self.model = SystemModel()
        self.selected_code = None
        self.build_ui()
        self.refresh_tree()

    def build_ui(self):
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True)

        # Sidebar Controls
        lf = tk.Frame(frame)
        lf.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        tk.Label(lf, text="Name:").pack()
        self.name_entry = tk.Entry(lf)
        self.name_entry.pack(fill=tk.X)

        tk.Label(lf, text="Description:").pack()
        self.desc_entry = tk.Entry(lf)
        self.desc_entry.pack(fill=tk.X)

        tk.Label(lf, text="Select Parent (optional):").pack()
        self.parent_cb = ttk.Combobox(lf, state="readonly", width=42)
        self.parent_cb.pack(fill=tk.X)

        tk.Label(lf, text="Or Enter Parent Full Code:").pack()
        self.parent_entry = tk.Entry(lf)
        self.parent_entry.pack(fill=tk.X)

        tk.Button(lf, text="Use Tree Selection as Parent", command=self.use_selected_as_parent).pack(pady=4)
        tk.Button(lf, text="Add New System Item", command=self.add_item).pack(pady=8)

        ttk.Separator(lf).pack(fill=tk.X, pady=6)

        tk.Label(lf, text="Add Attribute to Selected Item:").pack()
        self.attr_cb = ttk.Combobox(lf, values=["mechanical", "fluid", "energy", "state"])
        self.attr_cb.pack(fill=tk.X)
        self.attr_desc = tk.Entry(lf)
        self.attr_desc.pack(fill=tk.X)
        tk.Button(lf, text="Add Attribute", command=self.add_attribute).pack(pady=3)

        tk.Button(lf, text="Save All", command=self.model.save).pack(pady=10)
        self.status = tk.Label(lf, text="", fg="green")
        self.status.pack()

        # Tree View
        rf = tk.Frame(frame)
        rf.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(rf)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def use_selected_as_parent(self):
        if self.selected_code:
            item = self.model.get_item(self.selected_code)
            if item:
                self.parent_cb.set(f"{item.name} | {item.full_code}")
                self.parent_entry.delete(0, tk.END)
                self.parent_entry.insert(0, item.full_code)

    def add_item(self):
        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()
        parent_code = None
        if self.parent_cb.get():
            parent_code = self.parent_cb.get().split("|")[-1].strip()
        elif self.parent_entry.get():
            parent_code = self.parent_entry.get().strip()
        if not name:
            messagebox.showerror("Missing Name", "A name is required.")
            return
        try:
            item = self.model.create_item(name, desc, parent_code)
            self.status.config(text=f"Created: {item.full_code}")
            self.name_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)
            self.parent_cb.set("")
            self.parent_entry.delete(0, tk.END)
            self.refresh_tree()
        except Exception as e:
            messagebox.showerror("Creation Failed", str(e))

    def add_attribute(self):
        if not self.selected_code:
            messagebox.showerror("Select Item", "Please select a tree item.")
            return
        attr_type = self.attr_cb.get()
        desc = self.attr_desc.get().strip()
        if not attr_type or not desc:
            messagebox.showerror("Missing Info", "Attribute type and description required.")
            return
        self.model.add_attribute(self.selected_code, attr_type, desc)
        self.attr_desc.delete(0, tk.END)
        self.refresh_tree()

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        roots = [item for item in self.model.items.values() if item.parent_code == "000000"]
        for root in sorted(roots, key=lambda x: x.code):
            self.insert_tree_node(root, "")
        self.update_parent_options()

    def insert_tree_node(self, item, parent):
        node_id = self.tree.insert(parent, "end", text=f"{item.name} | {item.full_code}", values=[item.full_code])
        for k, v in item.attributes.items():
            self.tree.insert(node_id, "end", text=f"Attr: {k} - {v}")
        for child_code in item.children_codes:
            child = self.model.get_item(child_code)
            if child:
                self.insert_tree_node(child, node_id)

    def update_parent_options(self):
        items = sorted(self.model.items.values(), key=lambda i: i.full_code)
        self.parent_cb["values"] = [f"{i.name} | {i.full_code}" for i in items]

    def on_select(self, event):
        sel = self.tree.selection()
        if sel:
            val = self.tree.item(sel[0], "values")
            if val:
                self.selected_code = val[0]

if __name__ == "__main__":
    root = tk.Tk()
    app = SystemModelGUI(root)
    root.mainloop()
