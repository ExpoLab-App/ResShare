from pathlib import Path

FILE_SIZE_LIMIT_BYTES = 1024 * 1024
SUPPORTED_UPLOAD_EXTENSIONS = frozenset({"pdf", "docx", "txt"})


class ValidationError(ValueError):
    pass


def _reject_traversal(path: str) -> None:
    normalized = path.replace("\\", "/")
    if ".." in normalized.split("/"):
        raise ValidationError("Path must not contain '..' segments")


def normalize_tree_path(path: str) -> str:
    cleaned = path.strip()
    if not cleaned:
        raise ValidationError("Path is required")
    _reject_traversal(cleaned)
    return cleaned.strip("/")


def validate_folder_path(folder_path: str) -> str:
    normalized = normalize_tree_path(folder_path)
    if not normalized:
        raise ValidationError("folder_path cannot be empty")
    return normalized


def validate_share_path(path: str) -> str:
    normalized = normalize_tree_path(path)
    if normalized in {"", "root"}:
        raise ValidationError("Cannot share the root folder")
    return normalized


def validate_target_username(target: str) -> str:
    cleaned = target.strip()
    if not cleaned:
        raise ValidationError("target username is required")
    return cleaned


def validate_file_path(path: str) -> str:
    normalized = normalize_tree_path(path)
    if not normalized:
        raise ValidationError("path cannot be empty")
    return normalized


def validate_local_upload_file(local_path: str) -> tuple[Path, str]:
    cleaned = local_path.strip()
    if not cleaned:
        raise ValidationError("local_path is required")

    path = Path(cleaned).expanduser()
    if not path.is_file():
        raise ValidationError(f"local_path is not a file: {local_path}")

    size = path.stat().st_size
    if size > FILE_SIZE_LIMIT_BYTES:
        raise ValidationError(
            f"File exceeds 1 MB limit ({size} bytes). Maximum is {FILE_SIZE_LIMIT_BYTES} bytes."
        )

    extension = path.suffix.lower().lstrip(".")
    if extension and extension not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type '.{extension}'. Supported: pdf, docx, txt."
        )

    return path, path.name
