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
- [ ] Add durable activity/recovery semantics where restart-survival materially improves safety.

### Epic: Native execution

- [x] Invoke discovered ComfyUI/custom-node HTTP routes through one generic Full-control operation.
- [x] Make native prompt, queue, history, job, interrupt/cancel surfaces reachable through that same discovered-route executor rather than route-specific adapters.
- [ ] Complete controlled live acceptance of prompt submission, queue/job inspection, cancellation, and unknown custom-node route execution on the owner's ComfyUI runtime.

### Epic: Custom GPT setup

- [ ] Provide a revocable connection credential and keep it outside the Action schema.
- [x] Provide a compact Action schema endpoint for implemented operations.
- [ ] Provide recommended Custom GPT instructions plus copy-ready setup guidance.
- [ ] Add diagnostics for connection readiness and upstream ComfyUI compatibility.
- [ ] Complete controlled live acceptance against the owner's installed ComfyUI instance.

### Epic: Full-control fallback

- [ ] Identify ComfyUI-owned operations that cannot be expressed through filesystem CRUD, downloads, or live native routes.
- [ ] Add only the bounded ComfyUI-scoped fallback primitives needed for those proven gaps.
- [ ] Verify fallback actions preserve authentication, confirmation, auditability, and root/runtime boundaries.

## Later

- Multi-instance control, scheduled automation, semantic workflow libraries, and optional connection helpers are later features. They must not become prerequisites for universal single-instance control.
