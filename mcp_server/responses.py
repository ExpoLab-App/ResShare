from typing import Any, Optional


def tool_response(
    *,
    ok: bool,
    message: str,
    data: Optional[dict[str, Any]] = None,
    sources: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": ok, "message": message}
    if data is not None:
        payload["data"] = data
    if sources is not None:
        payload["sources"] = sources
    return payload
