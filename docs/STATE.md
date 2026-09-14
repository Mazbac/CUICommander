# Current state

## Current

- Mode: active product development
- Epic: universal ComfyUI execution and transfer plane
- Branch: `feat/control-plane-foundation`
- The branch contains the verified control-plane foundation plus generic downloads/jobs/Execute capability.
- CUICommander runs as a ComfyUI custom-node/server extension and registers its API on the live `PromptServer`.
- Universal capability invariant remains: no required adapters for node packs, model families, custom nodes, or future registered ComfyUI paths.
- Filesystem scope includes the complete `folder_paths.base_path` tree plus paths dynamically registered through `folder_paths`.

## Implemented and repository-verified

- Bearer credential state with `inspect`, `edit`, and `full` access levels stored outside the repository.
- Authenticated manifest/OpenAPI, live roots/nodes/routes discovery, bounded inspect, and generic filesystem CRUD.
- Cross-volume moves, stale fingerprints, path/symlink containment, and protected CUICommander credential state.
- Background HTTP(S) downloads into any discovered root with progress, cancellation, optional SHA-256 verification, bounded transient retry, atomic finalization, and partial-file cleanup.
- Download network policy rejects URL credentials and private/local/reserved targets, revalidates redirects/DNS, and strips Authorization on cross-host redirects.
- Bounded in-memory CUICommander job records expose current transfer progress and cancellation state.
- `executeComfyUI` is one Full-control operation for live discovered ComfyUI/custom-node HTTP routes; non-GET execution requires explicit confirmation and CUICommander routes cannot recurse through it.
- Native execution delegates back to the same running ComfyUI HTTP surface, so `/prompt`, queue/job/history APIs, and newly added custom-node routes keep their upstream behavior instead of being reimplemented.
- Repository verification now compiles every Python backend module and currently covers 18 backend unit tests before the frontend/browser gates.

## Next

1. Locate/install into the owner's actual ComfyUI installation and perform controlled live acceptance: discovery, `/prompt`, job inspect/cancel, and an unknown custom-node/native route.
2. Verify a real large-model download into a registered model root, including cancellation and checksum behavior.
3. Add durable activity/recovery semantics where restart-survival materially improves safety; current CUICommander background-job records are intentionally in-memory.
4. Turn the operational preview into the final embedded setup/connection surface and provide copy-ready Custom GPT instructions plus connection diagnostics.
5. Add a narrower ComfyUI-scoped fallback only for legitimate operations that filesystem CRUD plus the live native route surface demonstrably cannot express.

## Known issues / current boundary

- The owner's ComfyUI process has not yet been observed running during this work, so the new native execution and download planes are repository-tested but not yet live-accepted in ComfyUI.
- The React overview still uses a development snapshot rather than live manifest data.
- Background job history is bounded and in-memory; a ComfyUI restart intentionally clears it for now.
