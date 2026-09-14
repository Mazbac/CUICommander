# Current state

## Current

- Mode: active product development
- Epic: secure external reachability for Custom GPT Actions
- Branch: `feat/control-plane-foundation`
- CUICommander runs as a ComfyUI custom-node/server extension on the owner's real installation through a junction from `custom_nodes/CUICommander` to this repository.
- Primary ChatGPT integration target: Custom GPT Actions. The embedded console generates the setup artifacts instead of requiring users to design the Action contract themselves.
- Universal capability invariant remains: no required adapters for node packs, model families, custom nodes, or future registered ComfyUI paths.
- Current development version: `0.3.0-dev` / package `0.3.0`.

## Implemented and repository-verified

- Bearer credential state with `inspect`, `edit`, and `full` access levels stored outside the repository.
- Authenticated manifest/OpenAPI, live roots/nodes/routes discovery, bounded inspect, generic filesystem CRUD, background transfers/jobs, and generic native route execution.
- Production React console is served by the in-process extension at `/cuicommander/`.
- Localhost setup auto-bootstraps without opening `connection.json`; the browser keeps the access key in session storage only.
- Local-only admin routes can change access level, save a public HTTPS origin, and rotate the access key. They require loopback/same-origin access, use `Cache-Control: no-store`, are excluded from OpenAPI, and cannot be reached through recursive Execute.
- The Custom GPT wizard generates copy-ready instructions, Action schema URL, Bearer-auth guidance, readiness status, access-key management, and final setup steps.
- Environment-provided access/key overrides remain authoritative and cannot be silently replaced from the setup UI.
- Repository verification currently covers 29 Python backend tests plus 4 frontend unit tests before browser/accessibility/visual gates.

## Live acceptance completed

- Real runtime: ComfyUI 0.35.1 on the owner's Windows workstation.
- Discovery found 79 filesystem/model roots and dynamically exposed core plus custom-node routes.
- Full CRUD acceptance passed in the real ComfyUI temp root with cleanup.
- Generic Execute passed against `/system_stats`, native `/prompt`/history/queue flow, and an existing ComfyUI-Manager custom-node route without an adapter.
- A real `EmptyLatentImage -> SaveLatent` prompt completed successfully and its acceptance output was removed afterward.
- Background download success, checksum failure cleanup, cancellation cleanup, and mutation-confirmation rejection were live-tested.
- The 0.3 embedded setup UI was live-accepted in Chromium against an isolated localhost ComfyUI instance: local auto-bootstrap, manifest/root loading, wizard rendering, reload, and Action-schema isolation all passed.
- `scripts/live_acceptance.py` and `scripts/live-ui-acceptance.mjs` make runtime/UI checks repeatable without printing the configured access key.

## Next

1. Add a bounded HTTPS edge/tunnel path that exposes CUICommander without exposing raw ComfyUI.
2. Add external endpoint health diagnostics and complete end-to-end acceptance from an actual Custom GPT Action.
3. Verify a genuinely large model transfer into a dynamically registered model root.
4. Add the Resources/Downloads/Jobs management surfaces on top of the already-implemented generic backend primitives.
5. Add higher-level workflow create/read/update/save/test flows while retaining live node/model discovery and the generic control-plane invariant.
6. Add durable activity/recovery semantics where restart survival materially improves safety.

## Known boundary

- The owner's normal ComfyUI instance on port 8188 was deliberately not force-restarted during remote work; the latest 0.3 Python/UI code was live-accepted on a temporary localhost instance loading the same repository junction.
- Background CUICommander job history remains bounded and in-memory and clears on restart.
- A public HTTPS Action endpoint and end-to-end execution from an actual Custom GPT Action are not yet live-accepted.
