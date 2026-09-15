from __future__ import annotations

from typing import Any

from .roots import discover_roots

MAX_NODE_PAGE = 250
MAX_ROUTE_PAGE = 500
MAX_ROOT_PAGE = 500


def _page(items: list[dict[str, Any]], offset: int, limit: int, maximum: int) -> dict[str, Any]:
    if offset < 0:
        raise ValueError("offset must be zero or greater.")
    bounded_limit = max(1, min(int(limit), maximum))
    page = items[offset : offset + bounded_limit]
    next_offset = offset + len(page)
    complete = next_offset >= len(items)
    return {
        "items": page,
        "offset": offset,
        "limit": bounded_limit,
        "totalItems": len(items),
        "nextOffset": None if complete else next_offset,
        "complete": complete,
    }


def discover_nodes(query: str = "", limit: int = 100, offset: int = 0) -> dict[str, Any]:
    import nodes

    needle = query.strip().lower()
    matches: list[tuple[str, Any, str]] = []
    for name, node_class in nodes.NODE_CLASS_MAPPINGS.items():
        category = str(getattr(node_class, "CATEGORY", ""))
        description = str(getattr(node_class, "DESCRIPTION", ""))
        if needle and needle not in f"{name} {category} {description}".lower():
            continue
        matches.append((name, node_class, category))
    matches.sort(key=lambda item: item[0].lower())

    bounded_limit = max(1, min(int(limit), MAX_NODE_PAGE))
    selected = matches[offset : offset + bounded_limit]
    items: list[dict[str, Any]] = []
    for name, node_class, category in selected:
        item: dict[str, Any] = {
            "name": name,
            "category": category,
            "module": getattr(node_class, "__module__", ""),
            "returnTypes": list(getattr(node_class, "RETURN_TYPES", ()) or ()),
            "function": str(getattr(node_class, "FUNCTION", "")),
        }
        try:
            input_types = node_class.INPUT_TYPES()
            item["inputTypes"] = input_types if isinstance(input_types, dict) else {}
        except Exception as error:
            item["inputTypesError"] = type(error).__name__
        items.append(item)

    next_offset = offset + len(items)
    complete = next_offset >= len(matches)
    return {
        "items": items,
        "offset": offset,
        "limit": bounded_limit,
        "totalItems": len(matches),
        "nextOffset": None if complete else next_offset,
        "complete": complete,
    }


def discover_routes(query: str = "", limit: int = 250, offset: int = 0) -> dict[str, Any]:
    from server import PromptServer

    needle = query.strip().lower()
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for route in PromptServer.instance.app.router.routes():
        resource = getattr(route, "resource", None)
        canonical = getattr(resource, "canonical", None)
        path = str(canonical or resource or "")
        method = str(getattr(route, "method", ""))
        key = (method, path)
        if not path or key in seen:
            continue
        if needle and needle not in f"{method} {path}".lower():
            continue
        seen.add(key)
        items.append({"method": method, "path": path, "source": "aiohttp"})
    items.sort(key=lambda item: (str(item["path"]).lower(), str(item["method"])))
    return _page(items, offset, limit, MAX_ROUTE_PAGE)


def discover(kind: str, query: str = "", limit: int = 100, offset: int = 0) -> dict[str, Any]:
    if kind == "roots":
        return _page(discover_roots(), offset, limit, MAX_ROOT_PAGE)
    if kind == "nodes":
        return discover_nodes(query, limit, offset)
    if kind == "routes":
        return discover_routes(query, limit, offset)
    raise ValueError("kind must be roots, nodes, or routes.")
