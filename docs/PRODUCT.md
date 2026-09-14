# Product

CUICommander lets an authorized ChatGPT client control a local ComfyUI installation without building an adapter for every node, model family, custom node, or workflow.

## Goal

- Problem: ComfyUI behavior is spread across workflows, the live node registry, HTTP/WebSocket routes, queue/history state, models, inputs/outputs, custom nodes, configuration, user data, and files.
- Target user: a ComfyUI owner/operator who wants to state a result in ChatGPT and let the client discover and perform the relevant ComfyUI operation.
- Core successful outcome: install CUICommander as a ComfyUI custom node/server extension, connect a Custom GPT, then manage ComfyUI state without a provider adapter first.
- Why this product should exist: ComfyUI already exposes generic runtime, node-registry, workflow, queue, route, and filesystem primitives. CUICommander should turn those foundations into one stable authenticated control plane.

## Product profile

- Surface/distribution: installable ComfyUI custom node/server extension with a small operational UI plus an authenticated REST/OpenAPI interface for ChatGPT Actions.
- Primary environment: current maintained ComfyUI on a user-controlled workstation; Windows is the first development environment without making Windows-specific product assumptions.
- Risk level: high-consequence because changes can materially affect generation workflows and the local ComfyUI installation.
- Valuable/sensitive assets affected: workflows, models, custom nodes, configuration, inputs/outputs, user data, queue/history, and other paths registered into the running ComfyUI instance.

## MVP

- Connect one authorized ChatGPT client to one ComfyUI instance with a revocable bearer credential and copy-ready OpenAPI schema/instructions.
- Discover the live node registry, ComfyUI routes, registered model folders, queue/history/runtime state, and filesystem roots without assuming a specific custom node vendor.
- Use one generic control language: Discover/Inspect, Create, Read, Update, Delete, then Execute when ordinary resource CRUD cannot express the requested result.
- Treat the complete ComfyUI base directory as a first-class managed root and also include external paths registered through `folder_paths`, such as extra model directories.
- Allow generic file transfer/download into registered ComfyUI roots so new models and assets do not require model-specific endpoints.
- Queue and control workflows through ComfyUI's native prompt/job primitives and inspect their results.
- Keep mutations stale-aware, bounded, authenticated, auditable, and followed by explicit verification where practical.
- Keep a full-control fallback for ComfyUI-owned runtime, routes, and filesystem capabilities that are not covered by structured CRUD.

## Product rules / non-goals

- No adapter catalog for checkpoints, LoRAs, ControlNet, custom-node suites, workflow packs, or future node types.
- A node or custom node installed tomorrow must be discoverable from the live registry and usable through generic workflow/runtime primitives without a CUICommander release first.
- A new model folder registered tomorrow must appear through root discovery without adding a CUICommander model adapter.
- Full control stays scoped to the running ComfyUI installation and paths ComfyUI itself owns or registers.
- ChatGPT remains the conversational planner; CUICommander is the deterministic ComfyUI control plane.

## Success

The first useful version succeeds when a supported ComfyUI install can add CUICommander, connect a Custom GPT, discover unknown nodes and registered folders, manage files/models generically, submit and monitor workflows, inspect resulting state, and use a bounded generic fallback without provider-specific adapters.
