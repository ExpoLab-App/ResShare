import json
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.error import ErrorCode
from backend.node import Node


class ShareManager:
    """
    Stores references to shared items instead of full snapshots so receivers always
    see the latest state from the sender's root tree.
    """

    def __init__(self, share_list: Optional[Dict[str, List[Dict[str, Any]]]] = None):
        # {from_user: [{"path": "folder/sub", "is_folder": True}]}
        self.share_list: Dict[str, List[Dict[str, Any]]] = share_list or {}

    @staticmethod
    def _normalize_path(path: str) -> str:
        return path.strip("/")

    def receive(self, from_username: str, path: str, is_folder: bool) -> ErrorCode:
        normalized_path = self._normalize_path(path)
        if not normalized_path:
            return ErrorCode.INVALID_PATH

        if from_username not in self.share_list:
            self.share_list[from_username] = []

        if any(entry.get("path") == normalized_path for entry in self.share_list[from_username]):
            return ErrorCode.ALREADY_SHARED

        self.share_list[from_username].append(
            {
                "path": normalized_path,
                "is_folder": bool(is_folder),
            }
        )
        return ErrorCode.SUCCESS

    def to_dict(self) -> Dict[str, List[Dict[str, Any]]]:
        return self.share_list

    def resolve_for_client(
        self,
        root_loader: Callable[[str], Optional[Node]],
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Build a fresh view of shared items using the latest sender roots.
        """
        resolved: Dict[str, List[Dict[str, Any]]] = {}

        for from_user, entries in self.share_list.items():
            root_node = root_loader(from_user)
            if not root_node:
                continue

            nodes: List[Dict[str, Any]] = []
            for entry in entries:
                target_path = entry.get("path")
                if not target_path:
                    continue

                node = root_node.find_node_by_path(target_path)
                if node:
                    nodes.append(node.to_dict())

            if nodes:
                resolved[from_user] = nodes

        return resolved

    def _is_target_authorized(self, entry: Dict[str, Any], normalized_target: str) -> bool:
        shared_path = self._normalize_path(entry.get("path", ""))
        if not shared_path:
            return False

        if entry.get("is_folder", True):
            return normalized_target == shared_path or normalized_target.startswith(f"{shared_path}/")
        return normalized_target == shared_path

    def _split_combined_path(self, path: str) -> Tuple[Optional[str], Optional[str]]:
        parts = path.strip("/").split("/")
        if len(parts) < 2:
            return None, None
        return parts[0], "/".join(parts[1:])

    def resolve_shared_node(
        self,
        combined_path: str,
        root_loader: Callable[[str], Optional[Node]],
    ) -> Optional[Node]:
        """
        combined_path: '<from_user>/<relative_path inside their root>'
        Returns the latest Node if the path is authorized.
        """
        from_user, target_path = self._split_combined_path(combined_path)
        if not from_user or not target_path:
            return None

        entries = self.share_list.get(from_user, [])
        normalized_target = self._normalize_path(target_path)

        if not any(self._is_target_authorized(entry, normalized_target) for entry in entries):
            return None

        root_node = root_loader(from_user)
        if not root_node:
            return None

        return root_node.find_node_by_path(target_path)

    @classmethod
    def from_dict(cls, data: Dict[str, List[Dict[str, Any]]]):
        share_list: Dict[str, List[Dict[str, Any]]] = {}

        for from_user, entry_list in (data or {}).items():
            cleaned_entries: List[Dict[str, Any]] = []

            for entry in entry_list:
                # New format
                if isinstance(entry, dict) and "path" in entry:
                    normalized_path = cls._normalize_path(entry.get("path", ""))
                    if normalized_path:
                        cleaned_entries.append(
                            {
                                "path": normalized_path,
                                "is_folder": bool(entry.get("is_folder", True)),
                            }
                        )
                    continue

                # Legacy node snapshot fallback (assume shared root-level name)
                if isinstance(entry, dict) and "name" in entry and "is_folder" in entry:
                    normalized_path = cls._normalize_path(entry.get("name", ""))
                    if normalized_path:
                        cleaned_entries.append(
                            {
                                "path": normalized_path,
                                "is_folder": bool(entry.get("is_folder", True)),
                            }
                        )

            if cleaned_entries:
                share_list[from_user] = cleaned_entries

        return cls(share_list=share_list)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str):
        return cls.from_dict(json.loads(json_str))

    def delete(self, from_user: str, target_path: str) -> ErrorCode:
        """
        Remove a shared entry for the receiver by path.
        """
        if from_user not in self.share_list:
            return ErrorCode.NODE_NOT_FOUND

        normalized_path = self._normalize_path(target_path)
        entries = self.share_list[from_user]
        new_entries = [entry for entry in entries if entry.get("path") != normalized_path]

        if len(new_entries) == len(entries):
            return ErrorCode.NODE_NOT_FOUND

        if new_entries:
            self.share_list[from_user] = new_entries
        else:
            del self.share_list[from_user]

        return ErrorCode.SUCCESS
