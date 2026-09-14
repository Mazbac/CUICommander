# Roadmap

## MVP

### Epic: Control-plane foundation

- [x] Normalize product goal, risk, lifecycle, and no-adapter invariant.
- [x] Select in-process ComfyUI extension architecture and canonical machine vocabulary.
- [x] Ship authenticated manifest/OpenAPI plus live root/node/route discovery.
- [x] Ship bounded read/inspect for filesystem resources with fingerprints.

### Epic: Generic ComfyUI CRUD and transfers

- [x] Create/update/move/delete files and directories inside discovered ComfyUI roots.
- [x] Add background streaming downloads for large models/assets with progress, bounded retry, cancellation, optional checksum verification, and atomic destination finalization.
- [x] Live-accept success, checksum failure cleanup, and cancellation cleanup on the owner's ComfyUI runtime.
- [ ] Verify a genuinely large model transfer into a dynamically registered model root.
- [ ] Add durable activity/recovery semantics where restart survival materially improves safety.

### Epic: Native execution

- [x] Invoke discovered ComfyUI/custom-node HTTP routes through one generic Full-control operation.
- [x] Make native prompt, queue, history, job, and interrupt/cancel surfaces reachable through that same discovered-route executor rather than route-specific adapters.
- [x] Live-accept prompt submission, history/queue inspection, confirmation gating, and an unknown custom-node route on the owner's ComfyUI runtime.

### Epic: Embedded setup and Custom GPT Actions

- [x] Serve the production React console from the same in-process CUICommander extension.
- [x] Load live manifest/root data in the production console after session-only authentication.
- [x] Add repeatable live API and embedded-browser acceptance runners.
- [x] Keep the compact Action schema endpoint as the machine contract.
- [ ] Generate copy-ready Custom GPT instructions from the product control rules.
- [ ] Present the public HTTPS schema URL and bearer-auth setup steps in a guided wizard.
- [ ] Add readiness diagnostics for ComfyUI, CUICommander access level, HTTPS reachability, and Action endpoint health.
- [ ] Complete end-to-end acceptance from an actual Custom GPT Action.

### Epic: Secure external reachability

- [ ] Support a bounded HTTPS edge/tunnel configuration that exposes CUICommander routes without exposing raw ComfyUI.
- [ ] Make the externally visible base URL stable enough for a saved Custom GPT Action.
- [ ] Document credential rotation/revocation and recovery without committing or logging secrets.

### Epic: Full-control fallback

- [ ] Identify ComfyUI-owned operations that cannot be expressed through filesystem CRUD, downloads, or live native routes.
- [ ] Add only the bounded ComfyUI-scoped fallback primitives needed for proven gaps.
- [ ] Verify fallback actions preserve authentication, confirmation, auditability, and root/runtime boundaries.

## Later

- Multi-instance control, scheduled automation, semantic workflow libraries, and optional alternative ChatGPT integration methods are later features. They must not become prerequisites for universal single-instance control through Custom GPT Actions.
