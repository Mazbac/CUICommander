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
- durable CUICommander jobs plus one generic `executeComfyUI` operation for live discovered ComfyUI/custom-node routes;
- bounded redacted activity history for consequential mutations, remote-access changes, and native execution;
- real runtime acceptance for CRUD, downloads, native prompt/history/queue execution, and an existing custom-node route without an adapter;
- an embedded React/Mantine console served at `/cuicommander/` with Overview, Resources, Transfers & Jobs, Workflows, Runtime, and Activity surfaces;
- a localhost-only Custom GPT setup wizard for access level, generated GPT instructions, Action schema URL, Bearer key, and key rotation;
- a free Remote access flow that detects Tailscale, preserves existing Serve/Funnel mappings, and exposes only an isolated CUICommander Action gateway rather than raw ComfyUI;
- local admin operations excluded from OpenAPI and protected by loopback/same-origin checks; secrets remain outside the repository and production bundle;
- repository-wide Python, TypeScript, unit, browser accessibility, E2E, visual-regression, Action-gateway isolation, and live Tailscale round-trip verification.
  Because Execute delegates to the running ComfyUI HTTP surface, native `/prompt`, queue/job/history endpoints, and routes added later by custom nodes remain reachable without a CUICommander adapter.

Remaining before a public MVP claim:

- verify the generated public HTTPS endpoint end-to-end from an actual Custom GPT Action;
- verify a genuinely large public model transfer into a dynamically registered model root if exhaustive transfer acceptance is required;
- claim/configure the Comfy Registry publisher and repository publishing secret, then publish the first Manager/Registry release.

The repository already contains Comfy Registry package metadata and a manual publish workflow. The declared publisher must be claimed/configured by the repository owner before that workflow can publish.

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
