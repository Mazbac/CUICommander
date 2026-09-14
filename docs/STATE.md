# Current state

## Current

- Mode: active product development
- Epic: embedded setup and Custom GPT Actions connection
- Branch: `feat/control-plane-foundation`
- CUICommander runs as a ComfyUI custom-node/server extension and registers its API on the live `PromptServer`.
- The control plane is installed into the owner's real ComfyUI through a junction from `custom_nodes/CUICommander` to this repository.
- Primary ChatGPT integration target: Custom GPT Actions, with CUICommander generating the setup artifacts instead of requiring users to design the Action contract themselves.
- Universal capability invariant remains: no required adapters for node packs, model families, custom nodes, or future registered ComfyUI paths.

## Implemented and repository-verified

- Bearer credential state with `inspect`, `edit`, and `full` access levels stored outside the repository.
- Authenticated manifest/OpenAPI, live roots/nodes/routes discovery, bounded inspect, and generic filesystem CRUD.
- Cross-volume moves, stale fingerprints, path/symlink containment, and protected CUICommander credential state.
- Background HTTP(S) downloads with progress, cancellation, optional SHA-256 verification, bounded retry, atomic finalization, SSRF protections, and partial cleanup.
- One Full-control `executeComfyUI` operation delegates to method/path pairs already present in the live ComfyUI/custom-node aiohttp router.
- Production React build is emitted under `web/console` and served by the same in-process CUICommander extension at `/cuicommander/`.
- The embedded production UI authenticates with a session-only browser key, then loads the live manifest and root discovery instead of a development snapshot.
- Repository verification compiles every Python backend module and currently covers 18 backend unit tests before frontend/browser gates.

## Live acceptance completed

- Real runtime: ComfyUI 0.35.1 on the owner's Windows workstation.
- Live discovery found 79 filesystem/model roots and dynamically exposed core plus custom-node routes.
- Full CRUD acceptance passed in the real ComfyUI temp root with cleanup.
- Generic Execute passed against `/system_stats`, native `/prompt`/history/queue flow, and an existing ComfyUI-Manager custom-node route without an adapter.
- A real `EmptyLatentImage -> SaveLatent` prompt completed successfully and its acceptance output was removed afterward.
- Background download success, checksum failure cleanup, cancellation cleanup, and mutation-confirmation rejection were live-tested.
- Embedded UI HTML/assets were served from a temporary localhost ComfyUI instance; Chromium acceptance passed connect, live data, reload/session persistence, and disconnect.
- `scripts/live_acceptance.py` and `scripts/live-ui-acceptance.mjs` make these checks repeatable without printing the configured access key.

## Next

1. Finish and verify the embedded-console slice, then commit/push it.
2. Build the Custom GPT Setup wizard: generated instructions, schema URL, authentication guidance, readiness checks, and copy-ready step-by-step setup.
3. Add an HTTPS edge configuration path so Actions can reach only CUICommander, never raw ComfyUI.
4. Verify a genuinely large model transfer into a dynamically registered model root.
5. Add durable activity/recovery semantics where restart survival materially improves safety.

## Known boundary

- The owner's normal ComfyUI instance on port 8188 was deliberately not force-restarted during remote work; the latest embedded UI code was live-accepted on an isolated temporary localhost instance loading the same repository junction.
- Background CUICommander job history remains bounded and in-memory and clears on restart.
- External HTTPS reachability and end-to-end execution from an actual Custom GPT Action are not yet implemented/accepted.
