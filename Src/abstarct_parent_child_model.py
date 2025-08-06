import uuid
from typing import List, Dict, Optional, Any

class AbstractElement:
    def __init__(self,
                 name: str,
                 description: str = "",
                 parent_code: Optional[str] = None,
                 hierarchy_digits: int = 2,   # number of digits for each hierarchy level
                 sibling_digits: int = 4,     # number of digits for siblings/child index
                 level_index: Optional[int] = None,
                 sibling_index: Optional[int] = None,
                 attributes: Optional[Dict[str, Any]] = None):
        self.uuid = str(uuid.uuid4())
        self.name = name
        self.description = description
        self.hierarchy_digits = hierarchy_digits
        self.sibling_digits = sibling_digits
        self.level_index = level_index if level_index is not None else 0
        self.sibling_index = sibling_index if sibling_index is not None else 1
        self.code_length = 2 * hierarchy_digits + 2 * sibling_digits  # parent code + self code

        # Ensure parent_code is the right length (or zeros for root)
        if parent_code and len(parent_code) == self.code_length // 2:
            self.parent_code = parent_code
        else:
            self.parent_code = '0' * (self.code_length // 2)

        # Generate element code
        self.self_code = self.generate_code(self.level_index, self.sibling_index)

        # Full code is parent + self code (for graph/traversal/lookup)
        self.full_code = self.parent_code + self.self_code

        self.attributes = attributes or {}
        self.children_codes: List[str] = []
        self.connected_elements: List['AbstractElement'] = []
        self.functions: Dict[str, Any] = {}  # {name: function}

    def generate_code(self, level: int, sibling: int) -> str:
        return str(level).zfill(self.hierarchy_digits) + str(sibling).zfill(self.sibling_digits)

    def add_child(self, child: 'AbstractElement') -> None:
        self.children_codes.append(child.full_code)

    def add_connected_element(self, element: 'AbstractElement') -> None:
        self.connected_elements.append(element)

    def add_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def get_attribute(self, key: str) -> Optional[Any]:
        return self.attributes.get(key)

    def add_function(self, name: str, function: Any) -> None:
        self.functions[name] = function

    def call_function(self, name: str, *args, **kwargs) -> Any:
        func = self.functions.get(name)
        if func:
            return func(self, *args, **kwargs)
        raise ValueError(f"Function '{name}' not found in element '{self.name}'")

    def to_dict(self) -> Dict[str, Any]:
        return {
            'uuid': self.uuid,
            'name': self.name,
            'description': self.description,
            'parent_code': self.parent_code,
            'self_code': self.self_code,
            'full_code': self.full_code,
            'attributes': self.attributes,
            'children_codes': self.children_codes,
            'connected_elements_count': len(self.connected_elements),
            'functions': list(self.functions.keys()),
            'hierarchy_digits': self.hierarchy_digits,
            'sibling_digits': self.sibling_digits
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AbstractElement':
        obj = cls(
            name=data['name'],
            description=data.get('description', ''),
            parent_code=data.get('parent_code'),
            hierarchy_digits=data.get('hierarchy_digits', 2),
            sibling_digits=data.get('sibling_digits', 4),
            level_index=int(data['self_code'][:data.get('hierarchy_digits', 2)]),
            sibling_index=int(data['self_code'][data.get('hierarchy_digits', 2):]),
            attributes=data.get('attributes', {})
        )
        obj.uuid = data.get('uuid', str(uuid.uuid4()))
        obj.children_codes = data.get('children_codes', [])
        # connected_elements/functions not restored by default in simple deserialization
        return obj

# ====== Usage Example ======

if __name__ == "__main__":
    # Root element: 2 digits for level, 3 for siblings (can be set to any)
    root = AbstractElement("RootSystem", hierarchy_digits=2, sibling_digits=3)
    print("Root Code:", root.full_code)

    # Child with hierarchy position, custom attributes
    child1 = AbstractElement("Child1", parent_code=root.self_code,
                             hierarchy_digits=2, sibling_digits=3, level_index=1, sibling_index=12)
    root.add_child(child1)
    root.add_attribute("mechanical", "Root mechanical subassembly")
    child1.add_attribute("fluid", "Child1 fluid property")

    # Attach & invoke arbitrary functions (bring to life in the next phase)
    def my_action(elem, msg):
        print(f"{elem.name} does: {msg}")
    root.add_function("act", my_action)
    root.call_function("act", "hello abstraction!")

    # Show structure
    print(root.to_dict())
    print(child1.to_dict())
