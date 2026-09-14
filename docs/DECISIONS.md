# Durable decisions

Record only decisions a future agent might otherwise undo. Git history is not repeated here.

## 2026-09-11 — D001: Repository is project memory

Chat history is disposable. Product truth, current state, durable decisions, and working rules must live in the repository.

## 2026-09-11 — D002: Speed through constraints

Optimize for fastest path to a professional releasable product: reuse defaults, build vertical slices, automate verification, and avoid speculative infrastructure or corporate ceremony.

## 2026-09-11 — D003: Mantine is the default React component system

Use Mantine and shared product primitives before custom controls. A project may choose another library only for a concrete product/platform reason.

## 2026-09-11 — D004: Standards-led UI

Accessibility follows current WCAG guidance; platform-specific behavior follows current platform guidance; common UX uses mature design-system patterns. AI aesthetic preference is the final fallback, not the source of truth.

## 2026-09-11 — D005: Evolution must be system-wide

Intentional design-system changes update shared primitives/tokens and reviewed baselines. Local exceptions are not an acceptable substitute for coherent evolution.

## Adding decisions

Use: date, stable ID, decision, and short reason. Add only when the choice is durable enough to affect future work.

## 2026-09-14 — D006: CUICommander runs inside ComfyUI

CUICommander is a ComfyUI custom node/server extension and uses the running ComfyUI Python process as its platform. Do not add a second normal-operation backend daemon when `PromptServer`, `nodes`, and `folder_paths` can provide the required source access.

## 2026-09-14 — D007: Universal capability without provider adapters

A ComfyUI-owned or registered subsystem must retain a generic control path without a node-suite, model-family, or vendor adapter. Generic discovery/CRUD/runtime execution are product architecture; specialized adapters are not required for reach.

## 2026-09-14 — D008: The complete ComfyUI tree is a first-class root

`folder_paths.base_path` is the canonical `comfyui` filesystem root. CUICommander also discovers all paths registered through `folder_paths`, including external model folders, so new path categories appear without code changes.

## 2026-09-14 — D009: Machine language is generic CRUD plus Execute

The machine-facing model is Discover/Inspect → Create/Read/Update/Delete → Execute. Installing a model is generic file creation/download into a discovered root; controlling an unknown custom-node route is generic native-route execution.
