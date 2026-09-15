# Roadmap

## MVP

### Epic: Control-plane foundation

- [x] Normalize product goal, risk, lifecycle, and no-adapter invariant.
- [x] Select in-process ComfyUI extension architecture and canonical machine vocabulary.
- [x] Ship authenticated manifest/OpenAPI plus live root/node/route discovery.
- [x] Ship bounded read/inspect for filesystem resources with fingerprints.

### Epic: Generic ComfyUI CRUD and transfers

- [x] Create/update/move/delete files and directories inside discovered ComfyUI roots.
- [x] Add background streaming downloads with progress, retry, cancellation, checksum verification, and atomic finalization.
- [x] Live-accept success, checksum failure cleanup, and cancellation cleanup on the owner's ComfyUI runtime.
- [x] Add durable job recovery plus bounded redacted activity history across restarts.
- [ ] Verify a genuinely large public model transfer into a dynamically registered model root.

### Epic: Native execution

- [x] Invoke discovered ComfyUI/custom-node HTTP routes through one generic Full-control operation.
- [x] Reach native prompt, queue, history, job, interrupt/cancel surfaces through the same discovered-route executor.
- [x] Live-accept prompt submission, history/queue inspection, confirmation gating, and an unknown custom-node route on the owner's runtime.

### Epic: Embedded setup and Custom GPT Actions

- [x] Serve the production React console from the same in-process CUICommander extension.
- [x] Load live manifest/root data in the production console after session-only authentication.
- [x] Generate copy-ready Custom GPT instructions, schema URL, Bearer-auth guidance, readiness state, and credential controls.
- [x] Keep local setup/admin loopback-only, non-cacheable, outside OpenAPI, and unreachable through Execute.
- [x] Live-accept local auto-bootstrap, reload, setup isolation, and all operator pages against real ComfyUI.
- [x] Add external endpoint health diagnostics for the isolated Action gateway.
- [ ] Complete end-to-end acceptance from an actual Custom GPT Action.

### Epic: Secure external reachability

- [x] Support a bounded HTTPS Action gateway plus free Tailscale Funnel path without exposing raw ComfyUI.
- [x] Preserve existing Tailscale Serve/Funnel mappings, avoid reset, and select only an unused supported Funnel port.
- [x] Guide first-run users when Tailscale is missing or disconnected and provide clean enable/disable/recovery paths.
- [x] Provide local access-key rotation and document revocation through key rotation / Remote Access disable.
- [ ] Prove the generated public endpoint works with the current Custom GPT Actions network policy from an actual GPT.

### Epic: Operator surfaces

- [x] Add Resources browser/CRUD UI over live discovered roots.
- [x] Add Transfers/Jobs UI with progress, cancellation, durable state, and result visibility.
- [x] Add Runtime diagnostics for discovered nodes/routes plus generic Execute.
- [x] Add higher-level workflow load/edit/save/queue flows without model/node adapters.
- [x] Add a bounded redacted Activity surface for consequential mutations and remote-access changes.

### Epic: Full-control fallback

- [x] Audit tested ComfyUI-owned operations for gaps beyond filesystem CRUD/transfers and live native routes.
- [x] Keep the fallback policy explicit: add no extra primitive until a real ComfyUI-owned capability is proven unreachable by existing generic planes.
- [x] Require any future fallback primitive to preserve authentication, confirmation, auditability, and ComfyUI-scoped boundaries.

### Epic: Distribution

- [x] Add Comfy Registry package metadata, package-content exclusions, consistency checks, and a release workflow.
- [ ] Claim/configure the declared Comfy Registry publisher and repository publishing secret.
- [ ] Publish the first public Registry/Manager release after real Custom GPT acceptance.

## Later

- Multi-instance control, scheduled automation, semantic workflow libraries, and an optional tray companion are later features. They must not become prerequisites for universal single-instance control through Custom GPT Actions.
