import json
from datetime import datetime

from backend.error import ErrorCode
from backend.file import File


class Node:
    def __init__(self, name, is_folder, file_obj=None):
        self.name = name
        self.is_folder = is_folder
        self.children = {} if is_folder else None
        self.file_obj = file_obj if not is_folder else None

    def __repr__(self):
        if self.is_folder:
            return f"[DIR] {self.name}"
        else:
            return f"[FILE] {self.name} ({self.file_obj})"

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return (
            self.name == other.name and
            self.is_folder == other.is_folder and
            self.file_obj == other.file_obj
        )

    def add_child(self, child_node):
        if not self.is_folder:
            return ErrorCode.ADD_CHILD_TO_FILE_NODE

        if child_node.name in self.children:
            return ErrorCode.DUPLICATE_NAME

        self.children[child_node.name] = child_node
        return ErrorCode.SUCCESS

    def find_node_by_path(self, path):
        parts = path.strip("/").split("/")
        if parts == ['']:
            return self
        elif parts and parts[0] == self.name:
            parts = parts[1:]

        node = self
        for part in parts:
            if not node.is_folder or part not in node.children:
                return None
            node = node.children[part]
        return node

    def to_dict(self):
        node_dict = {
            "name": self.name,
            "is_folder": self.is_folder
        }
        if self.is_folder:
            node_dict["children"] = {name: child.to_dict() for name, child in self.children.items()}
        else:
            node_dict["file_obj"] = {
                "cid": self.file_obj.cid,
                "size": self.file_obj.size,
                "filename": self.file_obj.filename,
                "creation_date": self.file_obj.creation_date.isoformat()
            }
        return node_dict

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data):
        if data["is_folder"]:
            node = cls(data["name"], is_folder=True)
            for name, child_data in data.get("children", {}).items():
                node.add_child(cls.from_dict(child_data))
        else:
            file_data = data["file_obj"]
            file_obj = File(
                cid=file_data["cid"],
                size=file_data["size"],
                filename=file_data["filename"],
                creation_date=datetime.fromisoformat(file_data["creation_date"])
            )
            node = cls(data["name"], is_folder=False, file_obj=file_obj)
        return node

    @classmethod
    def from_json(cls, json_str):
        return cls.from_dict(json.loads(json_str))

