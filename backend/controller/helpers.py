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
