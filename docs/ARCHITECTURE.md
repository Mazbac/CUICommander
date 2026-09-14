# Architecture

CUICommander is a ComfyUI custom node/server extension with a small React operational UI and a stable machine-facing control API.

## Platform baseline

- Host runtime: the Python process of the installed ComfyUI instance; do not add a second backend daemon for normal operation.
- Server integration: register routes on ComfyUI's `PromptServer` and use live ComfyUI modules such as `folder_paths` and `nodes` as source-of-truth primitives.
- Admin/setup UI: React 19 + TypeScript + Mantine 9, built with Vite 8 and npm.
- Tests: Vitest for UI/unit behavior; Playwright + axe-core for browser/accessibility/visual behavior; Python compile/contracts plus controlled live ComfyUI acceptance for backend behavior.

## Universal control model

The invariant is: if the running ComfyUI process owns, registers, exposes, or can legitimately operate a ComfyUI subsystem, CUICommander must retain a vendor-independent route to it.

1. **Discovery plane** â€” live nodes, route inventory, registered model/path roots, system state, queue/history, and CUICommander capability manifest.
2. **Structured resource plane** â€” generic CRUD for files/directories and later other stable ComfyUI resource shapes.
3. **Native execution plane** â€” prompt/job submission, queue control, and generic invocation of existing ComfyUI/custom-node HTTP routes.
4. **Full-control plane** â€” bounded ComfyUI-scoped fallback primitives when discovery/CRUD/native execution cannot express a legitimate operation.

There is no required provider adapter layer. Node packs, model families, and software installed later must remain reachable through the same generic planes.

## Filesystem boundary

- `folder_paths.base_path` is exposed as the canonical `comfyui` root, so the complete ComfyUI installation tree can be managed when Full control is enabled.
- Input, output, temp, user, models, custom nodes, and every path in `folder_paths.folder_names_and_paths` are discovered dynamically.
- Registered paths outside the base directory are separate roots; path traversal and symlink escape are rejected.
- Existing-resource mutations use a fresh fingerprint. Small files use full SHA-256, large files use bounded head/tail content sampling plus metadata, and directories use tree metadata so safety checks stay useful without hashing multi-gigabyte models end to end.
- Generic URL/download ingress belongs to the filesystem plane and must be streaming/background-capable; it is not split into checkpoint/LoRA/etc. installers.

## Machine control language

The stable model is **Discover/Inspect â†’ Create/Read/Update/Delete â†’ Execute**. Duplication is Create from an existing resource or file. Model installation is Create/download into a discovered root. Custom-node management is ordinary filesystem/runtime control, not a vendor action.

## External API and authentication

The OpenAPI surface stays compact: manifest/openapi, discover, inspect/read, generic CRUD, execute, jobs/activity. External clients authenticate with a revocable bearer token owned by CUICommander. Setup and privilege changes must not be remotely self-escalating.

## Boundary rule

Prefer native ComfyUI state and routes, then structured CRUD, then bounded full-control primitives. Safety may change method, limits, confirmation, audit, and verification, but must not force a provider-specific adapter to reach a ComfyUI-owned subsystem.
