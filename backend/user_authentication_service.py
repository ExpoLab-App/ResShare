import hashlib

from backend.share_manager import ShareManager
from backend.util import is_valid_password, is_valid_username

from backend.error import ErrorCode
from backend.RSDB_kv_service import get_kv, set_kv
from backend.node import Node

def sign_up(username, password):
    if get_kv(username).strip():
        return ErrorCode.USER_EXISTS
    if not is_valid_username(username):
        return ErrorCode.INVALID_USERNAME
    if not is_valid_password(password):
        return ErrorCode.INVALID_PASSWORD
    hashed = hashlib.sha256(password.encode()).hexdigest()
    set_kv(username, hashed)
    set_kv(username + " ROOT", Node("root", True).to_json())
    set_kv(username + " SHARE_MANAGER", ShareManager().to_json())
    return ErrorCode.SUCCESS

def login(username, password):
    stored = get_kv(username).strip()
    if not stored:
        return ErrorCode.USER_NOT_FOUND
    hashed = hashlib.sha256(password.encode()).hexdigest()
    if stored != hashed:
        return ErrorCode.INCORRECT_PASSWORD
    return ErrorCode.SUCCESS
