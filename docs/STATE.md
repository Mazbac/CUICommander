# Current state

## Current

- Mode: active product development / 0.5 release-candidate hardening
- Branch: `feat/control-plane-foundation`
- Current development version: `0.5.0-dev` / package `0.5.0`.
- CUICommander runs inside the ComfyUI Python process as a custom-node/server extension; no separate normal-operation backend daemon is required.
- Primary ChatGPT integration target: Custom GPT Actions through the compact authenticated OpenAPI contract.
- Universal invariant remains: no required adapters for model families, node packs, custom-node suites, or future ComfyUI-registered roots/routes.

## Implemented and repository-verified

- Bearer authentication with `inspect`, `edit`, and `full` access levels; local credential state is stored outside the repository.
- Live roots/nodes/routes discovery, bounded filesystem inspection, fingerprint-aware CRUD, background downloads, durable jobs, and generic native-route execution.
- The complete ComfyUI tree plus every runtime `folder_paths` registration is reachable through discovered roots; normalized root-id collisions are disambiguated deterministically.
- Background downloads enforce public HTTP(S), DNS/redirect revalidation, bounded retries/progress/cancellation/checksum verification, partial cleanup, and atomic finalization.
- Jobs persist outside the process. Nonterminal jobs restored after a restart become explicit `interrupted` records instead of disappearing.
- Mutation activity is persisted as a bounded redacted audit feed; credentials, authorization headers, and file contents are not recorded.
- Production React console is served at `/cuicommander/` and now includes Overview, Resources, Transfers & Jobs, Workflows, Runtime, and Activity surfaces.
- Resources browses discovered roots and supports inspect/create/update/move/delete with stale-state protection.
- Transfers & Jobs starts generic downloads, reports progress/state, and supports cancellation.
- Workflows loads/saves API-format prompt JSON with fingerprint protection and queues it through the live native `/prompt` route.
- Runtime searches the live node/route registries and invokes existing native routes through the generic Execute primitive.
- Activity exposes the bounded redacted mutation log through both the operator UI and Action API.
- Local setup remains loopback/same-origin only, no-store, absent from OpenAPI, and unreachable through recursive Execute.
- Remote Access uses a loopback-only Action gateway. Built-in Tailscale Funnel setup inventories and preserves existing Serve/Funnel mappings and never publishes raw ComfyUI.
- First-run remote setup guides missing-Tailscale users to the official installer, detects sign-in/connectivity, chooses only a free supported Funnel port, and supports clean disable/recovery.
- Comfy Registry package metadata, ignore rules, package validation, and a manual release workflow are present. Registry publication still requires the owner to claim/configure the declared publisher and repository publishing secret.

## Verification

- Repository gate currently covers 42 Python backend tests and 5 frontend unit tests plus formatting, lint, TypeScript, UI conformance, package metadata, and production build.
- Chromium accessibility/E2E walks every operator page and currently passes with zero axe violations.
- Desktop/mobile overview visual regression currently passes.
- Action-gateway isolation and a fresh 0.5 Tailscale Funnel round-trip prove authenticated Action routes are public while raw ComfyUI/local admin remain unreachable; the existing machine Serve/Funnel mappings are unchanged before/after.
- 0.5 embedded UI acceptance passes against an isolated real ComfyUI 0.35.1 runtime, including all six operator pages and duplicate live root registrations.
- Workflow/operator mutation acceptance queues a real tiny native prompt, verifies completion/activity, and cleans up the generated workflow/output.

## Remaining external acceptance / release blockers

1. Complete one real Custom GPT Action call against the generated public HTTPS endpoint; this cannot be simulated as proof of current ChatGPT Actions network behavior.
2. Verify one genuinely large public model transfer into a dynamically registered model root if desired before calling transfer acceptance exhaustive.
3. Claim/configure the Comfy Registry publisher and publishing secret before public Manager/Registry release.

## Runtime note

- The owner's normal ComfyUI listener on port 8188 has not been restarted specifically for the 0.5 release candidate. All 0.5 live acceptance above used isolated localhost test instances, so restarting the normal instance remains a deliberate later step rather than an unattended side effect.

No additional full-control fallback primitive is currently justified: tested ComfyUI-owned surfaces are reachable through discovered filesystem roots or the live native route table. If a future ComfyUI-owned capability is proven unreachable by those planes, add the smallest bounded generic fallback rather than a provider adapter.
