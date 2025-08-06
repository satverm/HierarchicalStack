import uuid
import json
import os
from typing import Dict, List, Optional


class TechnologyItem:
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
        self.code = self.generate_code(level, self.child_index)

        if parent_code and len(parent_code) >= 6:
            self.parent_code = parent_code[-6:]
        else:
            self.parent_code = "000000"

        self.full_code = self.parent_code + self.code
        self.attributes: Dict[str, str] = {}
        self.children_codes: List[str] = []

    def generate_code(self, level: int, index: int) -> str:
        return f"{level:02d}{index:04d}"

    def add_attribute(self, attr_type: str, description: str):
        if attr_type.lower() not in ["mechanical", "fluid", "energy", "state"]:
            raise ValueError(f"Invalid attribute type: {attr_type}")
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
            "children_codes": self.children_codes
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
        item.uuid = data.get("uuid", str(uuid.uuid4()))
        item.code = data["code"]
        item.full_code = data["full_code"]
        item.attributes = data.get("attributes", {})
        item.children_codes = data.get("children_codes", [])
        return item


class TechnologyModel:
    def __init__(self, db_path="technologies.json"):
        self.db_path = db_path
        self.items: Dict[str, TechnologyItem] = {}
        self.load()

    def create_item(self, name: str, description: str = "", parent_code: Optional[str] = None) -> TechnologyItem:
        level, index = 0, 1
        parent6 = parent_code[-6:] if parent_code and len(parent_code) >= 6 else "000000"

        if parent6 != "000000":
            parent = next((i for i in self.items.values() if i.full_code[-6:] == parent6), None)
            if not parent:
                raise ValueError("Parent not found.")
            level = int(parent.code[:2]) + 1
            siblings = [
                i for i in self.items.values()
                if i.parent_code == parent6 and int(i.code[:2]) == level
            ]
            index = len(siblings) + 1

        item = TechnologyItem(name, description, parent6, level, index)
        self.items[item.full_code] = item

        # Register child in parent
        parent_item = next((i for i in self.items.values() if i.code == parent6), None)
        if parent_item and parent6 != "000000":
            parent_item.children_codes.append(item.full_code)

        self.save()
        return item

    def get_item(self, full_code: str) -> Optional[TechnologyItem]:
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
                    item = TechnologyItem.from_dict(obj)
                    self.items[item.full_code] = item

