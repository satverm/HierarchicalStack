import uuid
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional

# ====== Data Structures ====== #

class SystemItem:
    def __init__(
        self,
        name: str,
        description: str = "",
        parent_code: Optional[str] = None,
        level: int = 0,
        child_index: Optional[int] = None
    ):
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.level = level
        self.child_index = child_index or 1
        self.code = self.generate_code(self.level, self.child_index)
        # FIX: Parent code is always last 6 digits (or "000000" for root)
        if parent_code and len(parent_code) >= 6:
            self.parent_code = parent_code[-6:]
        else:
            self.parent_code = "000000"
        self.full_code = f"{self.parent_code}{self.code}"  # Always 12 digits
        self.attributes: Dict[str, str] = {}
        self.children_codes: List[str] = []
        self.technology_refs: List[str] = []

    def generate_code(self, level: int, index: int) -> str:
        return f"{level:02d}{index:04d}"

    def add_attribute(self, attr_type: str, description: str):
        if attr_type.lower() not in ["mechanical", "fluid", "energy", "state"]:
            raise ValueError(f"Invalid type: {attr_type}")
        self.attributes[attr_type.lower()] = description

    def to_dict(self):
        return {
            "uuid": self.uuid,
            "name": self.name,
            "description": self.description,
            "level": self.level,
            "child_index": self.child_index,
            "code": self.code,
            "parent_code": self.parent_code,
            "full_code": self.full_code,
            "attributes": self.attributes,
            "children_codes": self.children_codes,
            "technology_refs": self.technology_refs
        }

    @classmethod
    def from_dict(cls, data):
        item = cls(
            name=data["name"],
            description=data.get("description", ""),
            parent_code=data.get("parent_code", "000000"),
            level=data.get("level", 0),
            child_index=data.get("child_index", 1)
        )
        item.uuid = data["uuid"]
        item.code = data["code"]
        item.full_code = data["full_code"]
        item.attributes = data.get("attributes", {})
        item.children_codes = data.get("children_codes", [])
        item.technology_refs = data.get("technology_refs", [])
        return item

class SystemModel:
    def __init__(self, db_path="systems.json"):
        self.db_path = db_path
        self.items: Dict[str, SystemItem] = {}
        self.load()

    def create_item(self, name: str, description: str = "", parent_code: Optional[str] = None) -> SystemItem:
        level, index = 0, 1
        # Only the last 6 digits for parent_code reference
        parent6 = (parent_code[-6:] if parent_code and len(parent_code) >= 6 else "000000")
        if parent6 != "000000":
            parent = None
            for itm in self.items.values():
                if itm.full_code[-6:] == parent6:
                    parent = itm
                    break
            if not parent:
                raise ValueError("Parent not found.")
            level = int(parent.code[:2]) + 1
            siblings = [
                item for item in self.items.values()
                if item.parent_code == parent6 and int(item.code[:2]) == level
            ]
            index = len(siblings) + 1
        else:
            parent6 = "000000"
        item = SystemItem(name, description, parent6, level, index)
        self.items[item.full_code] = item
        # Register as child in parent
        for itm in self.items.values():
            if itm.code == parent6 and parent6 != "000000":
                itm.children_codes.append(item.full_code)
        self.save()
        return item

    def get_item(self, code: str):
        return self.items.get(code)

    def add_attribute(self, item_code: str, attr_type: str, description: str):
        item = self.get_item(item_code)
        if item:
            item.add_attribute(attr_type, description)
            self.save()

    def save(self):
        with open(self.db_path, "w") as f:
            json.dump([i.to_dict() for i in self.items.values()], f, indent=2)

    def load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path) as f:
                for data in json.load(f):
                    item = SystemItem.from_dict(data)
                    self.items[item.full_code] = item

# ====== Tkinter GUI ====== #

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

        # Left controls
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

        tk.Button(lf, text="Use Selected Tree Item as Parent", command=self.use_selected_as_parent).pack(pady=4)
        tk.Button(lf, text="Add New Item", command=self.add_item).pack(pady=6)

        ttk.Separator(lf).pack(fill=tk.X, pady=6)

        tk.Label(lf, text="Add Attribute to Selected Item:").pack()
        self.attr_cb = ttk.Combobox(lf, values=["mechanical", "fluid", "energy", "state"])
        self.attr_cb.pack(fill=tk.X)
        self.attr_desc = tk.Entry(lf)
        self.attr_desc.pack(fill=tk.X)
        tk.Button(lf, text="Add Attribute", command=self.add_attribute).pack(pady=3)

        tk.Button(lf, text="Save", command=self.model.save).pack(pady=10)
        self.status = tk.Label(lf, text="", fg="green")
        self.status.pack()

        # Right: Tree
        rf = tk.Frame(frame)
        rf.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(rf)
        self.tree.pack(expand=True, fill=tk.BOTH)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

    def use_selected_as_parent(self):
        if self.selected_code:
            item = self.model.get_item(self.selected_code)
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
            messagebox.showerror("Missing Name", "Name is required")
            return
        try:
            item = self.model.create_item(name, desc, parent_code)
            self.status.config(text=f"Created: {item.full_code}")
            self.name_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)
            self.parent_entry.delete(0, tk.END)
            self.parent_cb.set("")
            self.refresh_tree()
            self.refresh_combo()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def add_attribute(self):
        if not self.selected_code:
            messagebox.showinfo("Select Item", "Select item in tree")
            return
        attr_type = self.attr_cb.get()
        desc = self.attr_desc.get().strip()
        if not attr_type or not desc:
            messagebox.showerror("Missing", "Provide attribute type and description")
            return
        self.model.add_attribute(self.selected_code, attr_type, desc)
        self.attr_desc.delete(0, tk.END)
        self.refresh_tree()

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        roots = [item for item in self.model.items.values() if item.parent_code == "000000"]
        for root in sorted(roots, key=lambda x: x.code):
            self.insert_tree_node(root, "")
        self.refresh_combo()

    def insert_tree_node(self, item, parent_node):
        node_id = self.tree.insert(
            parent_node, "end", text=f"{item.name} | {item.full_code}",
            values=[item.full_code]
        )
        for k, v in item.attributes.items():
            self.tree.insert(node_id, "end", text=f"Attr: {k} - {v}")
        for child_code in item.children_codes:
            child = self.model.get_item(child_code)
            if child:
                self.insert_tree_node(child, node_id)

    def refresh_combo(self):
        all_items = self.model.items.values()
        sorted_items = sorted(all_items, key=lambda i: i.full_code)
        self.parent_cb["values"] = [f"{i.name} | {i.full_code}" for i in sorted_items]

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
