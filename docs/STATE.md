# Current state

## Current

- Mode: active product development
- Epic: secure external reachability for Custom GPT Actions
- Branch: `feat/control-plane-foundation`
- CUICommander runs as a ComfyUI custom-node/server extension on the owner's real installation through a junction from `custom_nodes/CUICommander` to this repository.
- Primary ChatGPT integration target: Custom GPT Actions. The embedded console generates the setup artifacts instead of requiring users to design the Action contract themselves.
- Universal capability invariant remains: no required adapters for node packs, model families, custom nodes, or future registered ComfyUI paths.
- Current development version: `0.4.0-dev` / package `0.4.0`.

## Implemented and repository-verified

- Bearer credential state with `inspect`, `edit`, and `full` access levels stored outside the repository.
- Authenticated manifest/OpenAPI, live roots/nodes/routes discovery, bounded inspect, generic filesystem CRUD, background transfers/jobs, and generic native route execution.
- Production React console is served by the in-process extension at `/cuicommander/`.
- Localhost setup auto-bootstraps without opening `connection.json`; the browser keeps the access key in session storage only.
- Local-only admin routes can change access level, save a public HTTPS origin, and rotate the access key. They require loopback/same-origin access, use `Cache-Control: no-store`, are excluded from OpenAPI, and cannot be reached through recursive Execute.
- The Custom GPT wizard generates copy-ready instructions, Action schema URL, Bearer-auth guidance, readiness status, access-key management, and final setup steps.
- Environment-provided access/key overrides remain authoritative and cannot be silently replaced from the setup UI.
- A loopback-only Action gateway exposes only routes present in the compact Action OpenAPI contract; raw ComfyUI and local CUICommander administration are not routed through it.
- The Remote access wizard detects Tailscale, preserves existing Serve/Funnel mappings, selects only an unused allowed Funnel port, and can enable/disable its own Funnel without any reset operation.
- Repository verification currently covers 39 Python backend tests plus 5 frontend unit tests before browser/accessibility/visual gates.

## Live acceptance completed

- Real runtime: ComfyUI 0.35.1 on the owner's Windows workstation.
- Discovery found 79 filesystem/model roots and dynamically exposed core plus custom-node routes.
- Full CRUD acceptance passed in the real ComfyUI temp root with cleanup.
- Generic Execute passed against `/system_stats`, native `/prompt`/history/queue flow, and an existing ComfyUI-Manager custom-node route without an adapter.
- A real `EmptyLatentImage -> SaveLatent` prompt completed successfully and its acceptance output was removed afterward.
- Background download success, checksum failure cleanup, cancellation cleanup, and mutation-confirmation rejection were live-tested.
- The 0.3 embedded setup UI was live-accepted in Chromium against an isolated localhost ComfyUI instance: local auto-bootstrap, manifest/root loading, wizard rendering, reload, and Action-schema isolation all passed.
- `scripts/live_acceptance.py` and `scripts/live-ui-acceptance.mjs` make runtime/UI checks repeatable without printing the configured access key.
- Action-gateway isolation acceptance passed against the real runtime: OpenAPI and authenticated CUICommander routes were reachable while `/system_stats` and local setup returned 404 through the gateway.
- A real Tailscale Funnel round-trip was enabled on the free port, verified through its public HTTPS URL, and disabled again; the pre-existing Tailscale 443/8443 mappings were byte-for-byte equivalent before and after the test.

## Next

1. Complete end-to-end acceptance from an actual Custom GPT Action against the generated HTTPS schema URL.
2. Finish zero-knowledge onboarding for users who do not already have Tailscale installed or connected.
3. Verify a genuinely large model transfer into a dynamically registered model root.
4. Add the Resources/Downloads/Jobs management surfaces on top of the already-implemented generic backend primitives.
5. Add higher-level workflow create/read/update/save/test flows while retaining live node/model discovery and the generic control-plane invariant.
6. Add durable activity/recovery semantics where restart survival materially improves safety.

## Known boundary

- The owner's normal ComfyUI instance on port 8188 remains on its prior in-memory code while 0.4 development is live-accepted on a temporary localhost instance loading the same repository junction.
- Background CUICommander job history remains bounded and in-memory and clears on restart.
- The Tailscale HTTPS path is live-accepted from the workstation, but an actual Custom GPT Action has not yet been tested against it. The owner's currently free Funnel port is 10000, so current ChatGPT Actions compatibility with that non-standard HTTPS port must be proven before the remote milestone is called complete.
