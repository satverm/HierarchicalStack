"""
connection_stack.py

Defines an abstract stack of connection elements (e.g., Mechanical, Electrical, Data, Logical, etc.)
Each connection element can be part of a hierarchy (with parent, children, attributes as needed).
This module provides the ConnectionElement and ConnectionStack classes.
"""

import uuid
import json
from typing import Dict, List, Optional, Any

class ConnectionElement:
    """
    Represents a single, reusable type of connection—can be hierarchical and have its own attributes.
    """
    def __init__(
        self,
        name: str,
        description: str = "",
        parent_code: Optional[str] = None,
        hierarchy_digits: int = 2,
        sibling_digits: int = 2,
        level_index: int = 0,
        sibling_index: int = 1,
        attributes: Optional[Dict[str, Any]] = None
    ):
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.hierarchy_digits = hierarchy_digits
        self.sibling_digits = sibling_digits
        self.level_index = level_index
        self.sibling_index = sibling_index
        self.code = self.generate_code(level_index, sibling_index)
        self.parent_code = (parent_code[-(hierarchy_digits + sibling_digits):]
            if parent_code and len(parent_code) >= (hierarchy_digits + sibling_digits)
            else "0" * (hierarchy_digits + sibling_digits)
        )
        self.full_code = self.parent_code + self.code
        self.attributes = attributes or {}
        self.children_codes: List[str] = []

    def generate_code(self, level: int, sibling: int) -> str:
        return str(level).zfill(self.hierarchy_digits) + str(sibling).zfill(self.sibling_digits)

    def add_child(self, child: 'ConnectionElement') -> None:
        self.children_codes.append(child.full_code)

    def add_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "uuid": self.uuid,
            "name": self.name,
            "description": self.description,
            "parent_code": self.parent_code,
            "code": self.code,
            "full_code": self.full_code,
            "hierarchy_digits": self.hierarchy_digits,
            "sibling_digits": self.sibling_digits,
            "attributes": self.attributes,
            "children_codes": self.children_codes
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConnectionElement':
        obj = cls(
            name=data["name"],
            description=data.get("description", ""),
            parent_code=data.get("parent_code"),
            hierarchy_digits=int(data.get("hierarchy_digits", 2)),
            sibling_digits=int(data.get("sibling_digits", 2)),
            level_index=int(data["code"][:int(data.get("hierarchy_digits", 2))]),
            sibling_index=int(data["code"][int(data.get("hierarchy_digits", 2)):]),
            attributes=data.get("attributes", {})
        )
        obj.uuid = data.get("uuid", str(uuid.uuid4()))
        obj.children_codes = data.get("children_codes", [])
        return obj

class ConnectionStack:
    """
    Maintains a collection of connection elements (e.g., mechanical, electrical) and supports serialization.
    """
    def __init__(self):
        self.elements: Dict[str, ConnectionElement] = {}  # full_code as key

    def add_element(self, element: ConnectionElement):
        self.elements[element.full_code] = element

    def get_element(self, code: str) -> Optional[ConnectionElement]:
        return self.elements.get(code)

    def to_dict(self) -> Dict[str, Any]:
        return {code: elem.to_dict() for code, elem in self.elements.items()}

    def save(self, path: str):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def load(self, path: str):
        self.elements.clear()
        with open(path, "r") as f:
            data = json.load(f)
            for _, elem_data in data.items():
                element = ConnectionElement.from_dict(elem_data)
                self.elements[element.full_code] = element

# --- Example usage ---
if __name__ == "__main__":
    cstack = ConnectionStack()
    # Add a few types of connections to the stack
    c1 = ConnectionElement("Mechanical", hierarchy_digits=2, sibling_digits=2)
    c2 = ConnectionElement("Electrical", hierarchy_digits=2, sibling_digits=2, sibling_index=2)
    c3 = ConnectionElement("Data", hierarchy_digits=2, sibling_digits=2, sibling_index=3)
    cstack.add_element(c1)
    cstack.add_element(c2)
    cstack.add_element(c3)
    print(cstack.to_dict())  # Show current stack
    # Save/load (uncomment to use as needed)
    # cstack.save("connection_stack.json")
    # cstack.load("connection_stack.json")
