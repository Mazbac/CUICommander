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

## 2026-09-14 — D010: Execute delegates to live ComfyUI routes

`executeComfyUI` is a generic executor for method/path pairs that already exist in the live ComfyUI aiohttp router. It does not reimplement `/prompt`, queue/history/jobs, or custom-node route behavior. This keeps new upstream/custom-node routes reachable without CUICommander adapters while preserving Full-control gating and explicit confirmation for mutating methods.

## 2026-09-14 — D011: Model ingress is a generic transfer primitive

Large model and asset installation uses one root-targeted background download capability rather than model-family installers. Downloads stream to a partial file, support progress/cancel/retry/checksum verification, finalize atomically, and reject private/local/reserved network destinations including redirect/DNS rebinding paths.

## 2026-09-14 - D012: Custom GPT Actions are the primary ChatGPT integration

CUICommander targets Custom GPT Actions as the primary MVP connection path wherever the user's ChatGPT environment supports them. The embedded setup surface must generate the required instructions, OpenAPI/schema URL, authentication guidance, readiness checks, and copy-ready setup steps. Public plugin/app submission is not an MVP prerequisite; alternative integration methods may be added later without changing the local universal control-plane architecture.

## 2026-09-14 — D013: Local administration is not part of the Action contract

Credential reveal/rotation, access-level changes, and public-endpoint setup are owner operations, not Custom GPT capabilities. They remain loopback/same-origin-only, use non-cacheable responses, stay absent from OpenAPI, and cannot be reached indirectly through `executeComfyUI`. This keeps remote Actions powerful inside the configured ComfyUI boundary without letting them reconfigure that boundary.

## 2026-09-14 — D014: Remote access is isolated and provider-neutral

CUICommander must never require exposing raw ComfyUI to the public internet. Remote transports terminate at a loopback-only Action gateway whose routable surface is derived from the compact Action OpenAPI contract; local setup/admin and unrelated ComfyUI routes remain unreachable through it.

The first built-in zero-cost transport is Tailscale Funnel because it provides public HTTPS without router port forwarding or a paid domain. CUICommander must inspect and preserve pre-existing Tailscale Serve/Funnel configuration, select only an unused allowed Funnel port, and never use reset as part of normal setup or teardown. Manual HTTPS origins and future transport providers remain valid alternatives without changing the Action contract.

## 2026-09-14 — D015: Operator UI composes generic primitives

Resources, Transfers & Jobs, Workflows, Runtime, and Activity are human-facing operational surfaces over the same generic control planes used by Actions. Workflow UI may provide JSON editing, fingerprint-safe persistence, and queue controls, but it must not introduce model-family or custom-node-suite backend adapters. Durable jobs and redacted activity are CUICommander-owned operational state; they may improve recovery and auditability without becoming a second scheduler or workflow engine.

## 2026-09-15 — D016: Bounded results remain continuable

Payload, safety, and UI limits may bound one response, but they must not turn otherwise reachable ComfyUI-owned state into inaccessible state. Discovery and directories use pagination, regular files use chunked reads plus stale-safe range patches, and oversized native responses use temporary continuation handles. A future bound that would silently discard the remainder must add a generic continuation path rather than a provider- or node-specific adapter.
