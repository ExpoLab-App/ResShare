import logging
from functools import wraps
from typing import Optional

from flask import jsonify, session

from backend.RSDB_kv_service import get_kv
from backend.error import ErrorCode
from backend.node import Node
from backend.share_manager import ShareManager

route_logger = logging.getLogger(__name__)


def init_helpers(logger):
    global route_logger
    route_logger = logger or logging.getLogger(__name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            route_logger.info("User not logged in")
            return jsonify({'message': ErrorCode.NOT_LOGGED_IN.name}), 401
        return f(*args, **kwargs)

    return decorated_function


def get_root_node(username: str) -> Optional[Node]:
    root_json = get_kv(username + " ROOT")
    if not root_json or root_json.strip() in ["", "\n", " "]:
        return None
    return Node.from_json(root_json)


def get_share_manager(username: str) -> ShareManager:
    share_json = get_kv(username + " SHARE_MANAGER")
    if not share_json or share_json.strip() in ["", "\n", " "]:
        return ShareManager()
    return ShareManager.from_json(share_json)


def get_resolved_share_list(username: str):
    share_manager = get_share_manager(username)
    return share_manager.resolve_for_client(get_root_node)


def collect_files_recursively(node, current_path=''):
    """
    Recursively collect all files from a folder node.
    Returns a list of tuples: (relative_path, file_obj)
    """
    files = []

    if node.is_folder:
        for child_name, child_node in node.children.items():
            child_path = f"{current_path}/{child_name}" if current_path else child_name
            if child_node.is_folder:
                files.extend(collect_files_recursively(child_node, child_path))
            else:
                if child_node.file_obj:
                    files.append((child_path, child_node.file_obj))

    return files


def collect_indexed_document_ids(node):
    """Return ready RAG document IDs contained by a file or folder node."""
    if not node.is_folder:
        file_obj = node.file_obj
        if file_obj and file_obj.rag_status == "ready":
            return [file_obj.document_id]
        return []

    document_ids = []
    for child_node in node.children.values():
        document_ids.extend(collect_indexed_document_ids(child_node))
    return document_ids


def get_indexed_file_stats(root):
    """Build knowledge-base statistics from authoritative file metadata."""
    indexed_files = []
    for path, file_obj in collect_files_recursively(root):
        if file_obj.rag_status == "ready":
            indexed_files.append((path, file_obj))

    return {
        "total_chunks": sum(file_obj.chunk_count for _, file_obj in indexed_files),
        "total_files": len(indexed_files),
        "files": sorted(file_obj.filename for _, file_obj in indexed_files),
    }
