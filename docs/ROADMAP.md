# Roadmap

## MVP

### Epic: Control-plane foundation

- [x] Normalize product goal, risk, lifecycle, and no-adapter invariant.
- [x] Select in-process ComfyUI extension architecture and canonical machine vocabulary.
- [x] Ship authenticated manifest/OpenAPI plus live root/node/route discovery.
- [x] Ship bounded read/inspect for filesystem resources with fingerprints.

### Epic: Generic ComfyUI CRUD

- [x] Create/update/move/delete files and directories inside discovered ComfyUI roots.
- [ ] Add background streaming download jobs for large model/assets with progress, retry, cancellation, and destination verification.
- [ ] Add bounded activity plus stale-safe recovery semantics where practical.

### Epic: Native execution

- [ ] Submit API-format workflows through ComfyUI's native prompt/job machinery.
- [ ] Inspect queue/history/job/output state and interrupt/cancel work.
- [ ] Invoke discovered ComfyUI/custom-node HTTP routes through one generic operation.

### Epic: Custom GPT setup

- [ ] Provide a revocable connection credential and keep it outside the Action schema.
- [x] Provide a compact Action schema endpoint for implemented operations.
- [ ] Provide recommended Custom GPT instructions plus copy-ready setup guidance.
- [ ] Add diagnostics for connection readiness and upstream ComfyUI compatibility.
- [ ] Complete controlled live acceptance against the user's installed ComfyUI instance.

## Later

- Multi-instance control, scheduled automation, semantic workflow libraries, and optional connection helpers are later features. They must not become prerequisites for universal single-instance control.
