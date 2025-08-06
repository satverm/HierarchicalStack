# system_model.py

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

        # Hierarchical Code Generation
        self.level = level                    # 0 = root
        self.child_index = child_index or 1  # default to '0001'
        self.code = self.generate_code(level, self.child_index)
        self.parent_code = parent_code or "000000"
        self.full_code = f"{self.parent_code}{self.code}"  # 12-digit code

        self.attributes: Dict[str, str] = {}      # 'mechanical', 'fluid', 'energy', 'state'
        self.children_codes: List[str] = []       # list of 12-digit codes
        self.technology_refs: List[str] = []      # 12-digit tech codes (to be linked later)

    def generate_code(self, level: int, index: int) -> str:
        """Generate a 6-digit code: LLCCCC"""
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
            description=data["description"],
            parent_code=data["parent_code"],
            level=data["level"],
            child_index=data["child_index"]
        )
        item.uuid = data["uuid"]
        item.attributes = data["attributes"]
        item.children_codes = data["children_codes"]
        item.technology_refs = data["technology_refs"]
        return item


class SystemModel:
    def __init__(self, db_path="systems.json"):
        self.db_path = db_path
        self.items: Dict[str, SystemItem] = {}  # full_code as key
        self.load()

    def create_item(self, name: str, description: str = "", parent_code: Optional[str] = None) -> SystemItem:
        level, index = 0, 1

        # Determine hierarchy
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
            parent_code = "000000"  # Assign to root

        item = SystemItem(name, description, parent_code, level, index)

        self.items[item.full_code] = item

        # Register child in parent
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

    def assign_technology(self, item_code: str, tech_code: str):
        item = self.get_item(item_code)
        if item:
            if tech_code not in item.technology_refs:
                item.technology_refs.append(tech_code)
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
