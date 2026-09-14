# Current state

## Current

- Mode: active product development
- Epic: universal ComfyUI control-plane foundation
- Branch: `feat/control-plane-foundation`
- CUICommander loads as a ComfyUI custom-node/server extension and registers its API on the live `PromptServer`.
- Universal capability invariant remains: no required adapters for node packs, model families, custom nodes, or future registered ComfyUI paths.
- Filesystem scope includes the complete `folder_paths.base_path` tree plus paths dynamically registered through `folder_paths`.
- The owner-facing React/Mantine overview now replaces the starter showroom and documents connection, control planes, roots, and access levels.

## Implemented and verified

- Bearer credential state with `inspect`, `edit`, and `full` access levels stored outside the repository.
- Authenticated manifest plus compact OpenAPI for discovery, inspect, and generic filesystem CRUD.
- Live discovery of roots, node classes/input declarations, and aiohttp routes.
- Generic create/update/move/delete for files and directories with path containment, protected credential state, explicit delete intent, and stale fingerprints.
- Cross-volume moves are supported for registered roots on separate filesystems/drive volumes.
- Large-file fingerprints use bounded content sampling plus metadata; directory mutation fingerprints cover tree metadata.
- Repository verification includes Python compile/unit tests, frontend unit tests, accessibility/E2E, visual regression, and production build.

## Next

1. Add background streaming download jobs so installing large models/assets is a generic root-targeted operation.
2. Add native workflow/queue/history/interrupt execution primitives and then the bounded ComfyUI-scoped full-control fallback.
3. Add bounded activity/job records for verification, recovery, cancellation, and progress.
4. Turn the operational preview into the final in-ComfyUI setup/connection surface and complete live acceptance against the owner's installed ComfyUI instance.

## Known issues / current boundary

- The user's ComfyUI process has not yet been observed running during this work, so live in-process acceptance is still pending.
- `/execute` is intentionally not advertised in the OpenAPI schema until native execution exists; the current contract is honest about implemented capability.
- The React overview currently uses a development snapshot rather than live manifest data; it is an operational/setup preview, not yet the final embedded ComfyUI screen.
