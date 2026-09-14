from __future__ import annotations

from typing import Any


def _json_body(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return {
        "required": True,
        "content": {"application/json": {"schema": schema}},
    }


def build_schema(server_url: str, version: str) -> dict[str, Any]:
    root = {"type": "string", "description": "Root id returned by discoverComfyUI(kind=roots)."}
    path = {"type": "string", "maxLength": 4000, "description": "Relative path inside the selected discovered root."}
    fingerprint = {"type": "string", "pattern": "^[a-f0-9]{64}$"}
    content = {"type": "string", "description": "UTF-8 file content."}
    content64 = {"type": "string", "description": "Base64 file content for arbitrary binary files."}

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "CUICommander",
            "version": version,
            "description": "Generic ComfyUI control plane. Discover first; use filesystem CRUD and native execution without provider-specific adapters.",
        },
        "servers": [{"url": server_url.rstrip("/")}],
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer"},
            }
        },
        "security": [{"bearerAuth": []}],
        "paths": {},
    } | {"paths": _paths(root, path, fingerprint, content, content64)}

def _paths(root: dict[str, Any], path: dict[str, Any], fingerprint: dict[str, Any], content: dict[str, Any], content64: dict[str, Any]) -> dict[str, Any]:
    ok = {"200": {"description": "Successful operation"}}
    return {
        "/cuicommander/v1/manifest": {
            "get": {
                "operationId": "getCUICommanderManifest",
                "summary": "Get live CUICommander/ComfyUI capability state",
                "responses": ok,
            }
        },
        "/cuicommander/v1/discover": {
            "post": {
                "operationId": "discoverComfyUI",
                "summary": "Discover live roots, nodes, or HTTP routes",
                "requestBody": _json_body(
                    {
                        "kind": {"type": "string", "enum": ["roots", "nodes", "routes"]},
                        "query": {"type": "string", "maxLength": 200},
                        "limit": {"type": "integer", "minimum": 1, "maximum": 500},
                    },
                    ["kind"],
                ),
                "responses": ok,
            }
        },
        "/cuicommander/v1/resources/inspect": {
            "post": {
                "operationId": "inspectComfyUIResource",
                "summary": "Inspect any file or directory inside a discovered ComfyUI root",
                "requestBody": _json_body({"root": root, "path": path}, ["root", "path"]),
                "responses": ok,
            }
        },
    } | _mutation_paths(root, path, fingerprint, content, content64, ok) | _advanced_paths(root, path, ok)

def _mutation_paths(root: dict[str, Any], path: dict[str, Any], fingerprint: dict[str, Any], content: dict[str, Any], content64: dict[str, Any], ok: dict[str, Any]) -> dict[str, Any]:
    common_content = {"content": content, "contentBase64": content64}
    return {
        "/cuicommander/v1/resources/create": {
            "post": {
                "operationId": "createComfyUIResource",
                "summary": "Create a file or directory in any discovered ComfyUI root",
                "requestBody": _json_body(
                    {
                        "root": root,
                        "path": path,
                        "type": {"type": "string", "enum": ["file", "directory"]},
                        "parents": {"type": "boolean"},
                        **common_content,
                    },
                    ["root", "path", "type"],
                ),
                "responses": ok,
            }
        },
        "/cuicommander/v1/resources/update": {
            "post": {
                "operationId": "updateComfyUIResource",
                "summary": "Replace a file after fresh-state verification",
                "requestBody": _json_body(
                    {"root": root, "path": path, "expectedFingerprint": fingerprint, **common_content},
                    ["root", "path", "expectedFingerprint"],
                ),
                "responses": ok,
            }
        },
        "/cuicommander/v1/resources/move": {
            "post": {
                "operationId": "moveComfyUIResource",
                "summary": "Move a file or directory between discovered ComfyUI roots",
                "requestBody": _json_body(
                    {
                        "root": root,
                        "path": path,
                        "targetRoot": root,
                        "targetPath": path,
                        "expectedFingerprint": fingerprint,
                    },
                    ["root", "path", "targetRoot", "targetPath"],
                ),
                "responses": ok,
            }
        },
        "/cuicommander/v1/resources/delete": {
            "post": {
                "operationId": "deleteComfyUIResource",
                "summary": "Delete a file or directory after explicit user intent",
                "requestBody": _json_body(
                    {
                        "root": root,
                        "path": path,
                        "expectedFingerprint": fingerprint,
                        "recursive": {"type": "boolean"},
                        "confirmed": {"type": "boolean"},
                    },
                    ["root", "path", "confirmed"],
                ),
                "responses": ok,
            }
        },
    }



def _advanced_paths(root: dict[str, Any], path: dict[str, Any], ok: dict[str, Any]) -> dict[str, Any]:
    job_id = {
        "name": "job_id",
        "in": "path",
        "required": True,
        "schema": {"type": "string", "format": "uuid"},
    }
    return {
        "/cuicommander/v1/downloads": {
            "post": {
                "operationId": "downloadComfyUIResource",
                "summary": "Start a background download into any discovered ComfyUI root",
                "requestBody": _json_body(
                    {
                        "root": root,
                        "path": path,
                        "url": {"type": "string", "format": "uri"},
                        "expectedSha256": {"type": "string", "pattern": "^[a-fA-F0-9]{64}$"},
                        "headers": {"type": "object", "additionalProperties": {"type": "string"}},
                    },
                    ["root", "path", "url"],
                ),
                "responses": {"202": {"description": "Download job accepted"}},
            }
        },
        "/cuicommander/v1/jobs": {
            "get": {
                "operationId": "listCUICommanderJobs",
                "summary": "List recent CUICommander background jobs",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "schema": {"type": "integer", "minimum": 1, "maximum": 100},
                    }
                ],
                "responses": ok,
            }
        },
        "/cuicommander/v1/jobs/{job_id}": {
            "get": {
                "operationId": "getCUICommanderJob",
                "summary": "Inspect one CUICommander background job",
                "parameters": [job_id],
                "responses": ok,
            }
        },
        "/cuicommander/v1/jobs/{job_id}/cancel": {
            "post": {
                "operationId": "cancelCUICommanderJob",
                "summary": "Cancel a running CUICommander background job",
                "parameters": [job_id],
                "requestBody": _json_body({"confirmed": {"type": "boolean"}}, ["confirmed"]),
                "responses": ok,
            }
        },
        "/cuicommander/v1/execute": {
            "post": {
                "operationId": "executeComfyUI",
                "summary": "Invoke a discovered native ComfyUI or custom-node HTTP route",
                "requestBody": _json_body(
                    {
                        "method": {"type": "string", "enum": ["GET", "POST", "PUT", "PATCH", "DELETE"]},
                        "route": {"type": "string", "maxLength": 2000},
                        "query": {"type": "object", "additionalProperties": True},
                        "body": {},
                        "confirmed": {"type": "boolean"},
                    },
                    ["method", "route"],
                ),
                "responses": ok,
            }
        },
    }
