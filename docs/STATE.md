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
- Live roots/nodes/routes discovery is pageable; filesystem previews remain bounded while complete regular-file content is reachable through stale-safe chunked reads, repeated atomic range patches, ordinary CRUD, background downloads, durable jobs, and generic native-route execution.
- The complete ComfyUI tree plus every runtime `folder_paths` registration is reachable through discovered roots; normalized root-id collisions are disambiguated deterministically.
- Background downloads enforce public HTTP(S), DNS/redirect revalidation, bounded retries/progress/cancellation/checksum verification, partial cleanup, and atomic finalization.
- Jobs persist outside the process. Nonterminal jobs restored after a restart become explicit `interrupted` records instead of disappearing.
- Mutation activity is persisted as a bounded redacted audit feed; credentials, authorization headers, and file contents are not recorded.
- Production React console is served at `/cuicommander/` and now includes Overview, Resources, Transfers & Jobs, Workflows, Runtime, and Activity surfaces.
- Resources browses discovered roots, pages large directories, can load complete large UTF-8 files beyond the preview limit, and supports inspect/create/update/move/delete with stale-state protection.
- Transfers & Jobs starts generic downloads, reports progress/state, and supports cancellation.
- Workflows loads complete API-format prompt JSON through chunked reads when necessary, saves with fingerprint protection, and queues it through the live native `/prompt` route.
- Runtime pages the live node/route registries, invokes existing native routes through the generic Execute primitive, and can continue native responses that exceed the inline response limit.
- Activity exposes the bounded redacted mutation log through both the operator UI and Action API.
- Local setup remains loopback/same-origin only, no-store, absent from OpenAPI, and unreachable through recursive Execute.
- Remote Access uses a loopback-only Action gateway. Built-in Tailscale Funnel setup inventories and preserves existing Serve/Funnel mappings, can use an isolated userspace Action node when the system node's 443 mapping must remain untouched, and never publishes raw ComfyUI.
- First-run remote setup guides missing-Tailscale users to the official installer, detects sign-in/connectivity, chooses only a free supported Funnel port, and supports clean disable/recovery.
- Comfy Registry package metadata, ignore rules, package validation, and a manual release workflow are present. Registry publication still requires the owner to claim/configure the declared publisher and repository publishing secret.

## Verification

- `npm run verify:full` passes with 57 Python backend tests, 6 frontend unit tests, formatting, lint, TypeScript, UI conformance, package metadata, production build, 3 Chromium accessibility/E2E tests, and 5 reviewed visual-regression cases.
- Chromium accessibility/E2E walks every operator page and currently passes with zero axe violations.
- Desktop, mobile, narrow, and dark-mode overview visual regression currently passes.
- Action-gateway isolation and a fresh 0.5 Tailscale Funnel round-trip prove authenticated Action routes are public while raw ComfyUI/local admin remain unreachable; the existing machine Serve/Funnel mappings are unchanged before/after.
- 0.5 embedded UI acceptance passes against an isolated real ComfyUI 0.35.1 runtime, including all six operator pages and duplicate live root registrations.
- Workflow/operator mutation acceptance queues a real tiny native prompt, verifies completion/activity, and cleans up the generated workflow/output.
- On 2026-09-15 a real Custom GPT Action call reached the public HTTPS endpoint, discovered live nodes/routes, submitted a native prompt, and verified successful history/output; this closes the original first-Action network acceptance blocker.
- On 2026-09-15 an isolated real ComfyUI 0.35.1 instance reconstructed a 188,908-byte workflow in two authenticated resource chunks and parsed it as JSON. The same live pass verified repeated append patches plus complete readback/cleanup and completed a tiny native prompt. The sampled `/object_info` response fit below the 2 MiB inline limit, so oversized native-response continuation remains unit-tested rather than live-triggered in that pass.

## Remaining external acceptance / release blockers

1. Restart/deploy the owner's normal 8188 runtime onto this current release-candidate code, refresh the Custom GPT's pasted Action schema/instructions so it knows the new continuation operations, and repeat the large-resource read through the actual GPT UI.
2. With the owner present for Windows UAC, install/verify the `CUICommander Action Tailscale` Scheduled Task so the isolated Action node survives logoff/reboot. The current isolated node is live, but this unattended pass confirmed that the persistence task is not yet installed.
3. Verify one genuinely large public model transfer into a dynamically registered model root if desired before calling transfer acceptance exhaustive.
4. Claim/configure the Comfy Registry publisher and publishing secret before public Manager/Registry release.

## Runtime note

- The owner's normal ComfyUI listener on port 8188 is still the pre-continuation runtime during this unattended pass. New chunked read/patch and pageable/retained-response behavior was loaded and accepted on isolated localhost port 8199, which was stopped afterward. Restarting 8188 remains deliberate so active owner work is not disrupted unattended.

No additional full-control fallback primitive is currently justified: tested ComfyUI-owned surfaces are reachable through discovered filesystem roots or the live native route table. If a future ComfyUI-owned capability is proven unreachable by those planes, add the smallest bounded generic fallback rather than a provider adapter.
