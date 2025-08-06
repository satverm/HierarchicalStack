import tkinter as tk
from tkinter import messagebox, ttk
import uuid
import json
import os

# ───────────────────── Data Structures ─────────────────────

class SystemAttribute:
    def __init__(self, attr_type, description):
        self.type = attr_type
        self.description = description

class Connection:
    def __init__(self, target_id, conn_type, description):
        self.target_id = target_id
        self.conn_type = conn_type
        self.description = description

class SystemItem:
    def __init__(self, name, description="", parent_id=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.parent_id = parent_id
        self.attributes = {}
        self.connections = []

    def add_attribute(self, attr_type, description):
        self.attributes[attr_type] = SystemAttribute(attr_type, description)

    def add_connection(self, target, conn_type, description):
        self.connections.append(Connection(target.id, conn_type, description))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "attributes": {k: vars(v) for k, v in self.attributes.items()},
            "connections": [vars(c) for c in self.connections]
        }

class SystemModel:
    def __init__(self, db_path='system_model.json'):
        self.items = {}
        self.db_path = db_path
        self.load()

    def create_item(self, name, description="", parent_id=None):
        item = SystemItem(name, description, parent_id)
        self.items[item.id] = item
        self.save()
        return item

    def get_item(self, item_id):
        return self.items.get(item_id)

    def add_relationship(self, source, target, conn_type, description):
        source.add_connection(target, conn_type, description)
        self.save()

    def save(self):
        with open(self.db_path, 'w') as f:
            json.dump([item.to_dict() for item in self.items.values()], f, indent=2)

    def load(self):
        if os.path.exists(self.db_path):
            with open(self.db_path, 'r') as f:
                data = json.load(f)
                for item_data in data:
                    item = SystemItem(item_data['name'], item_data.get('description', ''), item_data.get('parent_id'))
                    item.id = item_data['id']
                    for k, v in item_data.get('attributes', {}).items():
                        item.add_attribute(v['type'], v['description'])
                    for c in item_data.get('connections', []):
                        item.connections.append(Connection(c['target_id'], c['conn_type'], c['description']))
                    self.items[item.id] = item

# ───────────────────── Tkinter UI ─────────────────────

class SystemModelUI:
    def __init__(self, root, model):
        self.model = model
        self.root = root
        self.root.title('System Model Builder')
        self.setup_ui()

    def setup_ui(self):
        # Left frame
        control_frame = tk.Frame(self.root)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        tk.Label(control_frame, text="Add New System Item").pack(pady=5)
        tk.Label(control_frame, text="Name:").pack()
        self.name_entry = tk.Entry(control_frame)
        self.name_entry.pack()
        tk.Label(control_frame, text="Description:").pack()
        self.desc_entry = tk.Entry(control_frame)
        self.desc_entry.pack()
        tk.Label(control_frame, text="Parent Item:").pack()
        self.parent_cb = ttk.Combobox(control_frame, values=self.get_item_names())
        self.parent_cb.pack()
        tk.Button(control_frame, text="Create Item", command=self.create_system_item).pack(pady=10)

        tk.Label(control_frame, text="Add Attribute:").pack(pady=5)
        self.attr_type_cb = ttk.Combobox(control_frame, values=['mechanical', 'fluid', 'energy', 'state'])
        self.attr_type_cb.pack()
        self.attr_desc_entry = tk.Entry(control_frame)
        self.attr_desc_entry.pack()
        tk.Button(control_frame, text="Add Attribute to Selected", command=self.add_attribute_to_selected).pack(pady=5)

        tk.Label(control_frame, text="Create Connection:").pack(pady=5)
        tk.Label(control_frame, text="From:").pack()
        self.conn_from_cb = ttk.Combobox(control_frame, values=self.get_item_names())
        self.conn_from_cb.pack()
        tk.Label(control_frame, text="To:").pack()
        self.conn_to_cb = ttk.Combobox(control_frame, values=self.get_item_names())
        self.conn_to_cb.pack()
        tk.Label(control_frame, text="Connection Type:").pack()
        self.conn_type_cb = ttk.Combobox(control_frame, values=['physical', 'flow', 'energy', 'state'])
        self.conn_type_cb.pack()
        self.conn_desc_entry = tk.Entry(control_frame)
        self.conn_desc_entry.pack()
        tk.Button(control_frame, text="Create Connection", command=self.create_connection).pack(pady=5)

        # Visual right frame: Hierarchical & relational view
        viz_frame = tk.Frame(self.root)
        viz_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree = ttk.Treeview(viz_frame)
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.refresh_tree()

    def get_item_names(self):
        return [item.name for item in self.model.items.values()]

    def find_item_by_name(self, name):
        for item in self.model.items.values():
            if item.name == name:
                return item
        return None

    def create_system_item(self):
        name = self.name_entry.get().strip()
        desc = self.desc_entry.get().strip()
        parent_name = self.parent_cb.get().strip()
        if not name:
            messagebox.showerror("Error", "Name is required")
            return
        parent_id = None
        if parent_name:
            parent = self.find_item_by_name(parent_name)
            if not parent:
                messagebox.showerror("Error", "Parent not found")
                return
            parent_id = parent.id

        item = self.model.create_item(name, desc, parent_id)
        messagebox.showinfo("Success", f"Created system item: {name}")
        self.refresh_controls()
        self.refresh_tree()

    def add_attribute_to_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Error", "Select an item from the tree")
            return
        attr_type = self.attr_type_cb.get()
        attr_desc = self.attr_desc_entry.get().strip()
        if not attr_type:
            messagebox.showerror("Error", "Select attribute type")
            return
        if not attr_desc:
            messagebox.showerror("Error", "Attribute description required")
            return
        item_id = self.tree.item(selected[0])['values'][0]
        item = self.model.get_item(item_id)
        if item:
            item.add_attribute(attr_type, attr_desc)
            self.model.save()
            messagebox.showinfo("Success", f"Added attribute to {item.name}")
            self.refresh_tree()

    def create_connection(self):
        from_name = self.conn_from_cb.get().strip()
        to_name = self.conn_to_cb.get().strip()
        conn_type = self.conn_type_cb.get().strip()
        desc = self.conn_desc_entry.get().strip()
        if not from_name or not to_name or not conn_type or not desc:
            messagebox.showerror("Error", "All fields required for connection")
            return
        from_item = self.find_item_by_name(from_name)
        to_item = self.find_item_by_name(to_name)
        if not from_item or not to_item:
            messagebox.showerror("Error", "From or To item not found")
            return
        self.model.add_relationship(from_item, to_item, conn_type, desc)
        messagebox.showinfo("Success", f"Created connection from {from_name} to {to_name}")
        self.refresh_tree()

    def refresh_controls(self):
        names = self.get_item_names()
        self.parent_cb['values'] = names
        self.conn_from_cb['values'] = names
        self.conn_to_cb['values'] = names

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        # Parent-child map
        children_map = {}
        roots = []
        for item in self.model.items.values():
            if item.parent_id:
                children_map.setdefault(item.parent_id, []).append(item)
            else:
                roots.append(item)
        def insert_node(node, parent_tree_id=''):
            display_text = f"{node.name} (ID: {node.id[:8]})"
            tree_id = self.tree.insert(parent_tree_id, 'end', text=display_text, values=[node.id])
            for attr_type, attr in node.attributes.items():
                self.tree.insert(tree_id, 'end', text=f"Attr: {attr_type} - {attr.description}")
            for conn in node.connections:
                target = self.model.get_item(conn.target_id)
                target_name = target.name if target else 'Unknown'
                self.tree.insert(tree_id, 'end', text=f"Conn: {conn.conn_type} to {target_name} ({conn.description})")
            for child in children_map.get(node.id, []):
                insert_node(child, tree_id)
        for root_item in roots:
            insert_node(root_item)
# To run the app:
def run_gui_app():
    root = tk.Tk()
    model = SystemModel()
    app = SystemModelUI(root, model)
    root.mainloop()

if __name__ == '__main__':
    run_gui_app()
