# CUICommander

CUICommander is a universal control plane for ComfyUI designed for use from ChatGPT / Custom GPT Actions without building a bespoke adapter for every model family, node pack, or future ComfyUI feature.

It is implemented as a ComfyUI custom-node/server extension: installing it under `custom_nodes` loads CUICommander into the same Python process as ComfyUI, where it can use live `PromptServer`, node-registry, and `folder_paths` state.

## Control model

The stable machine vocabulary is:

`Discover / Inspect -> Create / Read / Update / Delete -> Execute`

The no-adapter invariant is deliberate. CUICommander discovers the running instance instead of maintaining a catalogue of checkpoint, LoRA, custom-node-suite, or provider-specific integrations.

Filesystem reach starts with the complete `folder_paths.base_path` ComfyUI tree and also includes every path dynamically registered through `folder_paths`, including external model roots.

## Current foundation

Implemented today:

- bearer-authenticated manifest and compact OpenAPI contract;
- live root, node, and HTTP-route discovery;
- generic file/directory inspection with fingerprints;
- generic create, update, move, and delete operations;
- containment checks that prevent root escape and protect CUICommander credential state;
- stale-state checks for file and directory mutations;
- cross-root moves, including registered roots on another filesystem/volume;
- a small React/Mantine operational overview used while developing the in-ComfyUI setup surface;
- Python backend checks integrated into the repository verification gate.

Still in progress before the product can claim full ComfyUI control:

- native workflow, queue, job, history, interrupt, and result execution primitives;
- safe background downloads for models and other large ComfyUI resources;
- the gated ComfyUI-scoped full-control fallback for operations not expressible through narrower primitives;
- live installation/acceptance against the owner's actual ComfyUI runtime;
- final in-ComfyUI setup/connection UI and Custom GPT instructions.

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
