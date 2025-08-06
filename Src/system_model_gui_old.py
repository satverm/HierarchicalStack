import uuid
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional

# ========== Core Data Model ==========

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
        self.parent_code = parent_code or "000000"
        self.full_code = f"{self.parent_code}{self.code}"  # 12-digit code
        self.attributes: Dict[str, str] = {}
        self.children_codes: List[str] = []
        self.technology_refs: List[str] = []

    def generate_code(self, level: int, index: int) -> str:
        return f"{level:02d}{index:04d}"

    def add_attribute(self, attr_type: str, description: str):
        if attr_type.lower() not in ["mechanical", "fluid", "energy", "state"]:
            raise ValueError("Invalid attribute type.")
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
        if parent_code and parent_code != "000000":
            parent = self.items.get(parent_code)
            if not parent:
                raise ValueError("Parent code not found.")
            level = int(parent.code[:2]) + 1
            siblings = [
                item for item in self.items.values()
                if item.parent_code == parent_code and int(item.code[:2]) == level
            ]
            index = len(siblings) + 1
        elif not parent_code:
            parent_code = "000000"
        item = SystemItem(name, description, parent_code, level, index)
        self.items[item.full_code] = item
        if parent_code in self.items:
            self.items[parent_code].children_codes.append(item.full_code)
        self.save()
        return item

    def get_item(self, full_code: str) -> Optional[SystemItem]:
        return self.items.get(full_code)

    def add_attribute(self, full_code: str, attr_type: str, description: str):
        item = self.get_item(full_code)
        if item:
            item.add_attribute(attr_type, description)
            self.save()

    def export(self) -> List[Dict]:
        return [item.to_dict() for item in self.items.values()]

    def save(self):
        with open(self.db_path, "w") as f:
            json.dump(self.export(), f, indent=2)

    def load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, "r") as f:
                data = json.load(f)
                for obj in data:
                    item = SystemItem.from_dict(obj)
                    self.items[item.full_code] = item

# ========== Tkinter GUI ==========

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

        # Left: controls
        control_frame = tk.Frame(frame)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=8)

        tk.Label(control_frame, text="Name:").pack()
        self.name_entry = tk.Entry(control_frame)
        self.name_entry.pack()
        tk.Label(control_frame, text="Description:").pack()
        self.desc_entry = tk.Entry(control_frame)
        self.desc_entry.pack()
        tk.Label(control_frame, text="Parent (12-digit code, blank=root):").pack()
        self.parent_entry = tk.Entry(control_frame)
        self.parent_entry.pack()
        tk.Button(control_frame, text="Add Item", command=self.add_item).pack(pady=5)

        ttk.Separator(control_frame, orient="horizontal").pack(fill="x", pady=7)

        tk.Label(control_frame, text="Attribute Type:").pack()
        self.attr_type_cb = ttk.Combobox(control_frame, values=["mechanical","fluid","energy","state"])
        self.attr_type_cb.pack()
        tk.Label(control_frame, text="Attribute Description:").pack()
        self.attr_desc_entry = tk.Entry(control_frame)
        self.attr_desc_entry.pack()
        tk.Button(control_frame, text="Add Attribute", command=self.add_attribute).pack(pady=2)

        ttk.Separator(control_frame, orient="horizontal").pack(fill="x", pady=7)
        tk.Button(control_frame, text="Save to File", command=self.model.save).pack(pady=3)

        # Right: hierarchy tree
        right_frame = tk.Frame(frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        tk.Label(right_frame, text="System Hierarchy").pack()
        self.tree = ttk.Treeview(right_frame)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def add_item(self):
        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()
        parent_code = self.parent_entry.get().strip() or None
        if not name:
            messagebox.showerror("Error", "Enter a name")
            return
        try:
            item = self.model.create_item(name, desc, parent_code)
            messagebox.showinfo("Success", f"Created: {item.name} | Code: {item.full_code}")
            self.name_entry.delete(0, tk.END)
            self.desc_entry.delete(0, tk.END)
            self.parent_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Error", str(e))
        self.refresh_tree()

    def add_attribute(self):
        if not self.selected_code:
            messagebox.showerror("Error", "Select an item in the tree")
            return
        attr_type = self.attr_type_cb.get()
        desc = self.attr_desc_entry.get().strip()
        if not attr_type or not desc:
            messagebox.showerror("Error", "Attribute type and description required")
            return
        self.model.add_attribute(self.selected_code, attr_type, desc)
        self.attr_desc_entry.delete(0, tk.END)
        self.refresh_tree()

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        # Find all root (top) nodes
        roots = [item for item in self.model.items.values() if item.parent_code == "000000"]
        for root_item in roots:
            self.insert_node(root_item, "")
    def insert_node(self, item, parent_id):
        node_id = self.tree.insert(parent_id, "end", text=f"{item.name} | {item.full_code}", values=[item.full_code])
        for k, v in item.attributes.items():
            self.tree.insert(node_id, "end", text=f"Attr: {k} - {v}", values=[""])
        # Show children recursively
        for child_code in item.children_codes:
            child = self.model.get_item(child_code)
            if child:
                self.insert_node(child, node_id)

    def on_tree_select(self, event):
        sel = self.tree.selection()
        if sel:
            code = self.tree.item(sel[0])["values"][0]
            if code:
                self.selected_code = code

if __name__ == "__main__":
    root = tk.Tk()
    app = SystemModelGUI(root)
    root.mainloop()
