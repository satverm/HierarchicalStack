import uuid
import json
import os
from typing import Dict, List, Optional

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
        # Parent code = always last 6 digits of parent's code (or 000000 for top)
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
        # Use only last 6 digits for parent code reference
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

    def assign_technology(self, item_code: str, tech_code: str):
        item = self.get_item(item_code)
        if item and tech_code not in item.technology_refs:
            item.technology_refs.append(tech_code)
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

# Usage Example (uncomment to test directly):
# if __name__ == "__main__":
#     model = SystemModel()
#     root = model.create_item("Top System", "Main")
#     ch1 = model.create_item("First Child", "Child 1", parent_code=root.full_code)
#     ch2 = model.create_item("Second Child", "Child 2", parent_code=root.full_code)
#     sub = model.create_item("Subchild", "A child of child 1", parent_code=ch1.full_code)
#     model.add_attribute(sub.full_code, "mechanical", "Bracket part")
#     for code, item in model.items.items():
#         print(f"{item.name} | {item.full_code}")

