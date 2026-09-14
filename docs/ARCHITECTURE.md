# Architecture

CUICommander is a ComfyUI custom-node/server extension with a small React operational UI and a stable machine-facing control API.

## Platform baseline

- Host runtime: the Python process of the installed ComfyUI instance; do not add a second normal-operation backend daemon.
- Server integration: register routes on ComfyUI's `PromptServer` and use live `folder_paths`, node registry, router, queue, and job surfaces as source-of-truth primitives.
- Admin/setup UI: React 19 + TypeScript + Mantine 9, built with Vite 8 and npm.
- Tests: Python compile/unit checks plus Vitest, Playwright, axe-core, visual regression, and controlled live ComfyUI acceptance.

## Universal control model

The invariant is: if the running ComfyUI process owns, registers, exposes, or can legitimately operate a ComfyUI subsystem, CUICommander must retain a vendor-independent route to it.

1. **Discovery plane** â€” live nodes, route inventory, registered model/path roots, system state, and CUICommander capability manifest.
2. **Structured resource plane** â€” generic filesystem CRUD, background downloads, and bounded job records.
3. **Native execution plane** â€” one generic executor for routes that exist in the live ComfyUI/custom-node aiohttp router.
4. **Full-control fallback plane** â€” bounded ComfyUI-scoped primitives only for proven gaps that discovery, CRUD/transfers, and native routes cannot express.

There is no required provider adapter layer. Node packs, model families, and software installed later must remain reachable through the same generic planes.

## Filesystem and transfer boundary

- `folder_paths.base_path` is the canonical `comfyui` root, so the complete ComfyUI installation tree is reachable.
- Input, output, temp, user, models, custom nodes, and every path in `folder_paths.folder_names_and_paths` are discovered dynamically.
- Registered paths outside the base directory are separate roots; traversal, absolute-path injection, symlink escape, and CUICommander credential-state access are rejected.
- Existing-resource mutations require fresh fingerprints. Small files use full SHA-256, large files use bounded content sampling plus metadata, and directories use tree metadata.
- Large model/assets ingress is one generic background download primitive, not checkpoint/LoRA/provider installers.
- Downloads stream into partial files, report bounded progress, support cancellation and optional SHA-256 verification, retry bounded transient failures, and finalize atomically.
- Download URLs are constrained to public HTTP(S) destinations; DNS and redirects are revalidated and cross-origin redirects do not retain Authorization.

## Native execution boundary

`executeComfyUI` does not reproduce ComfyUI's `/prompt`, queue, history, jobs, or custom-node handlers. It first verifies that the requested method/path exists in the live router, then invokes that route on the same running ComfyUI instance. GET is read-only; non-GET execution requires Full control plus explicit confirmation. CUICommander routes cannot recursively execute themselves.

This means upstream changes and newly installed custom-node routes remain reachable without adding route-specific CUICommander code, while ComfyUI keeps ownership of its own validation and runtime behavior.

## Machine control language

The stable model is **Discover/Inspect â†’ Create/Read/Update/Delete â†’ Execute**. Model installation is Create/download into a discovered root. Workflow submission and queue/job control are Execute against discovered native routes. Custom-node management is ordinary filesystem/runtime control, not a vendor action.

## External API and authentication

The OpenAPI surface stays compact: manifest/openapi, discover, inspect/read, generic CRUD, downloads/jobs, and execute. External clients authenticate with a revocable bearer token owned by CUICommander. Setup and privilege changes must not be remotely self-escalating.

## Boundary rule

Prefer live ComfyUI state/routes, then structured CRUD/transfers, then bounded full-control fallback primitives. Safety may change method, limits, confirmation, audit, and verification, but must not force a provider-specific adapter to reach a ComfyUI-owned subsystem.
