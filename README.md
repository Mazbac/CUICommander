# CUICommander

CUICommander is a universal control plane for ComfyUI designed for use from ChatGPT / Custom GPT Actions without building a bespoke adapter for every model family, node pack, or future ComfyUI feature.

It is implemented as a ComfyUI custom-node/server extension: installing it under `custom_nodes` loads CUICommander into the same Python process as ComfyUI, where it can use live `PromptServer`, node-registry, and `folder_paths` state.

## Control model

The stable machine vocabulary is:

`Discover / Inspect -> Create / Read / Update / Delete -> Execute`

The no-adapter invariant is deliberate. CUICommander discovers the running instance instead of maintaining a catalogue of checkpoint, LoRA, custom-node-suite, or provider-specific integrations.

Filesystem reach starts with the complete `folder_paths.base_path` ComfyUI tree and also includes every path dynamically registered through `folder_paths`, including external model roots.

## Current implementation

Implemented today:

- bearer-authenticated manifest and compact OpenAPI contract;
- live root, node, and HTTP-route discovery;
- generic file/directory inspection plus stale fingerprints;
- generic create, update, move, and delete across the complete ComfyUI tree and registered external roots;
- protected credential state, path/symlink containment, and cross-volume moves;
- background HTTP(S) downloads into any discovered root with bounded progress records, cancellation, checksum verification, transient retry, partial-file cleanup, redirect validation, and private-network/SSRF blocking;
- a single `executeComfyUI` operation that can invoke a route only when the requested method/path exists in the live ComfyUI router; mutating invocations require Full control and explicit confirmation;
- bounded CUICommander job inspection/cancellation endpoints;
- a small React/Mantine operational overview plus repository-wide Python/UI/browser verification.

Because Execute delegates to the running ComfyUI HTTP surface, native `/prompt`, queue/job/history endpoints, and routes added later by custom nodes remain reachable without a CUICommander adapter.

Still in progress before the product can claim completed full-control acceptance:

- live installation/acceptance against the owner's actual ComfyUI runtime, including prompt submission, job inspection/cancellation, and unknown custom-node route execution;
- broaden the bounded ComfyUI-scoped fallback only where filesystem CRUD plus native routes cannot express a legitimate ComfyUI operation;
- durable activity/recovery policy beyond the current bounded in-memory background-job records;
- final embedded setup/connection UI and copy-ready Custom GPT instructions.

## Development

```sh
npm ci
npm run doctor
npm run dev
```

Quality gates:

```sh
npm run verify
npm run verify:full
```

`npm run verify` checks formatting, lint, TypeScript, UI conformance, Python syntax/unit tests, frontend unit tests, and the production build. `verify:full` adds browser accessibility/E2E and visual regression tests.
