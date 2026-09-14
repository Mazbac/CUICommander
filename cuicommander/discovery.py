from __future__ import annotations

from typing import Any

from .roots import discover_roots


def discover_nodes(query: str = "", limit: int = 100) -> list[dict[str, Any]]:
    import nodes

    needle = query.strip().lower()
    items: list[dict[str, Any]] = []
    for name, node_class in nodes.NODE_CLASS_MAPPINGS.items():
        category = str(getattr(node_class, "CATEGORY", ""))
        display_name = str(getattr(node_class, "DESCRIPTION", ""))
        haystack = f"{name} {category} {display_name}".lower()
        if needle and needle not in haystack:
            continue
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
        if len(items) >= max(1, min(limit, 250)):
            break
    return items

def discover_routes(query: str = "", limit: int = 250) -> list[dict[str, Any]]:
    from server import PromptServer

    needle = query.strip().lower()
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    server = PromptServer.instance

    for route in server.app.router.routes():
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
        if len(items) >= max(1, min(limit, 500)):
            break
    return items


def discover(kind: str, query: str = "", limit: int = 100) -> Any:
    if kind == "roots":
        return discover_roots()
    if kind == "nodes":
        return discover_nodes(query, limit)
    if kind == "routes":
        return discover_routes(query, limit)
    raise ValueError("kind must be roots, nodes, or routes.")
