# Product classification and capability packs

## Product profile

- Distribution: ComfyUI custom node/server extension plus authenticated REST/OpenAPI interface.
- Primary user/input: ComfyUI owner issuing natural-language requests through ChatGPT; Custom GPT Actions are the first packaged connection path.
- Valuable/sensitive assets: workflows, generation inputs/outputs, models, custom-node code, configuration, user data, and registered filesystem paths.
- Expected scale: one workstation/ComfyUI instance per installation; interactive control plus long-running model transfers and workflow jobs.
- Risk: high-consequence because valid operations can consume GPU resources or materially change the ComfyUI installation.

## Activated capability packs

- `auth`: revocable bearer credential, privilege gates, secret handling, and no credential in repository/log output.
- `files-import-export`: path containment, type/size awareness, progress, retry, stale protection, large-file behavior, and portability.
- `background-jobs`: queued/running/succeeded/failed/cancelled state for downloads and ComfyUI work.
- `integrations-webhooks`: stable REST/OpenAPI contract, request validation, replay/idempotency, and public-edge failure handling.
- `ai`: schema constraints, untrusted discovered content, deterministic server verification, and consequential-operation confirmation.
- `user-content`: workflows, node metadata, prompts, filenames, custom-node source, and outputs are untrusted data.

## Generic control capabilities

- Discover live node classes and their declared inputs/outputs/categories from ComfyUI's node registry, with continuation when the result set exceeds one page.
- Discover the active aiohttp route surface, including routes added by custom nodes, with the same pageable contract.
- Discover the ComfyUI base directory plus input/output/temp/user/models/custom-nodes and every model/path root registered through `folder_paths`.
- Inspect files/directories with bounded previews and fingerprints without special knowledge of the file's vendor or model family; previews and directory pages have continuation paths to complete access.
- Read arbitrary regular files completely in bounded UTF-8 or Base64 chunks and make large edits through repeated stale-safe atomic byte-range patches.
- Create, update, move, and delete ComfyUI-scoped filesystem resources with stale-state and path-boundary checks.
- Stream or background-download large files into a selected discovered root so model installation is a generic filesystem operation.
- Submit API-format workflows and inspect/cancel queue/job/history state through native ComfyUI primitives.
- Invoke an existing ComfyUI/custom-node HTTP route generically when that is the narrowest available operation; responses larger than the inline limit remain readable through retained chunked response handles.
- Keep activity/job records bounded and useful for verification/recovery.

## No-adapter rule

A new custom node, route, model type, or registered folder must not require a CUICommander release before ChatGPT can discover and operate it. Specialized knowledge may improve reasoning, but access must compile down to discovery, CRUD, native ComfyUI execution, or the bounded Full-control fallback.
