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
- [ ] Verify a genuinely large model transfer into a dynamically registered model root.
- [ ] Add durable activity/recovery semantics where restart survival materially improves safety.

### Epic: Native execution

- [x] Invoke discovered ComfyUI/custom-node HTTP routes through one generic Full-control operation.
- [x] Reach native prompt, queue, history, job, interrupt/cancel surfaces through the same discovered-route executor.
- [x] Live-accept prompt submission, history/queue inspection, confirmation gating, and an unknown custom-node route on the owner's runtime.

### Epic: Embedded setup and Custom GPT Actions

- [x] Serve the production React console from the same in-process CUICommander extension.
- [x] Load live manifest/root data in the production console after session-only authentication.
- [x] Add repeatable live API and embedded-browser acceptance runners.
- [x] Keep the compact Action schema endpoint as the machine contract.
- [x] Generate copy-ready Custom GPT instructions from the product control rules.
- [x] Present the Action schema URL, Bearer-auth setup, access level, and credential controls in a guided localhost wizard.
- [x] Keep local setup/admin operations loopback-only and outside the Action schema.
- [x] Live-accept local auto-bootstrap, wizard rendering, reload, and Action-schema isolation against real ComfyUI.
- [ ] Add external endpoint health diagnostics and complete end-to-end acceptance from an actual Custom GPT Action.

### Epic: Secure external reachability

- [ ] Support a bounded HTTPS edge/tunnel configuration that exposes CUICommander routes without exposing raw ComfyUI.
- [ ] Make the externally visible base URL stable enough for a saved Custom GPT Action.
- [x] Provide local access-key rotation and prevent secrets from being committed or bundled.
- [ ] Document revocation/recovery and verify the final remote authentication flow.

### Epic: Operator surfaces

- [ ] Add Resources browser/CRUD UI over live discovered roots.
- [ ] Add Downloads/Jobs UI with progress, cancellation, result verification, and cleanup.
- [ ] Add Runtime diagnostics for discovered nodes/routes, queue/history, and Execute.
- [ ] Add higher-level workflow create/read/update/save/test flows without hardcoded model/node adapters.

### Epic: Full-control fallback

- [ ] Identify ComfyUI-owned operations that cannot be expressed through filesystem CRUD, downloads, or live native routes.
- [ ] Add only the bounded ComfyUI-scoped fallback primitives needed for proven gaps.
- [ ] Verify fallback actions preserve authentication, confirmation, auditability, and root/runtime boundaries.

## Later

- Multi-instance control, scheduled automation, semantic workflow libraries, and optional alternative ChatGPT integration methods are later features. They must not become prerequisites for universal single-instance control through Custom GPT Actions.
