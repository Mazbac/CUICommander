# CUICommander

CUICommander is a universal control plane for ComfyUI designed for ChatGPT / Custom GPT Actions without building a bespoke adapter for every model family, node pack, or future ComfyUI feature.

It runs as a ComfyUI custom-node/server extension inside the same Python process as ComfyUI, where it can use live `PromptServer`, node-registry, and `folder_paths` state.

## Control model

The stable machine vocabulary is:

`Discover / Inspect -> Create / Read / Update / Delete -> Execute`

The no-adapter invariant is deliberate. CUICommander discovers the running instance instead of maintaining a catalogue of checkpoint, LoRA, custom-node-suite, or provider-specific integrations.

Filesystem reach starts with the complete `folder_paths.base_path` ComfyUI tree and also includes every path dynamically registered through `folder_paths`, including external model roots.

## Current implementation

Implemented and verified:

- bearer-authenticated manifest and compact OpenAPI Action contract;
- live root, node, and HTTP-route discovery;
- generic file/directory inspect, create, update, move, and delete with stale fingerprints and root/symlink containment;
- background HTTP(S) downloads into any discovered root with progress, cancellation, checksum verification, retry, atomic finalization, cleanup, and SSRF protections;
- bounded CUICommander jobs plus one generic `executeComfyUI` operation for live discovered ComfyUI/custom-node routes;
- real runtime acceptance for CRUD, downloads, native prompt/history/queue execution, and an existing custom-node route without an adapter;
- an embedded React/Mantine console served at `/cuicommander/` by the same ComfyUI extension;
- a localhost-only Custom GPT setup wizard for access level, public HTTPS origin, generated GPT instructions, Action schema URL, Bearer key, and key rotation;
- local admin operations excluded from OpenAPI and protected by loopback/same-origin checks; secrets remain outside the repository and production bundle;
- repository-wide Python, TypeScript, unit, browser accessibility, E2E, and visual-regression verification.
  Because Execute delegates to the running ComfyUI HTTP surface, native `/prompt`, queue/job/history endpoints, and routes added later by custom nodes remain reachable without a CUICommander adapter.

Next before a public MVP claim:

- provide a bounded public HTTPS edge/tunnel that exposes CUICommander rather than raw ComfyUI;
- verify the generated setup end-to-end from an actual Custom GPT Action;
- add operator UI for Resources, Downloads/Jobs, and Runtime diagnostics;
- add higher-level workflow create/read/update/save/test flows on top of live node/model discovery;
- verify a genuinely large model transfer into a dynamically registered model root;
- add durable recovery semantics where restart-survival materially improves safety.

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
