import re
def is_valid_password(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"[0-9]", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    if any(c in password for c in ['\n', '\r', '\t', '\v', '\f']):
        return False
    return True



def is_valid_username(username: str) -> bool:
    if not isinstance(username, str):
        return False
    if not (3 <= len(username) <= 20):
        return False
    if not re.match(r"^[A-Za-z0-9_]+$", username):
        return False
    if any(c in username for c in ['\n', '\r', '\t']):
        return False
    if username.isdigit():  # All digits
        return False
    return True

