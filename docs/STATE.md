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
- Production React console is served at `/cuicommander/` with primary navigation for Home, ChatGPT, Activity, and Advanced. Resources, Transfers & Jobs, Workflows, and Runtime remain fully capable operator tools under Advanced.
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

- `npm run verify:full` passes with 60 Python backend tests, 6 frontend unit tests, formatting, lint, TypeScript, UI conformance, package metadata, production build, 4 Chromium accessibility/E2E tests, and 5 reviewed visual-regression cases.
- Chromium accessibility/E2E covers all primary product pages plus every Advanced operator tool and currently passes with zero axe violations.
- Desktop, mobile, narrow, and dark-mode Home visual regression currently passes after the simplified product-shell redesign.
- Action-gateway isolation and a fresh 0.5 Tailscale Funnel round-trip prove authenticated Action routes are public while raw ComfyUI/local admin remain unreachable; the existing machine Serve/Funnel mappings are unchanged before/after.
- 0.5 embedded UI acceptance passes against an isolated real ComfyUI 0.35.1 runtime, including all six operator pages and duplicate live root registrations.
- Workflow/operator mutation acceptance queues a real tiny native prompt, verifies completion/activity, and cleans up the generated workflow/output.
- On 2026-09-15 a real Custom GPT Action call reached the public HTTPS endpoint, discovered live nodes/routes, submitted a native prompt, and verified successful history/output; this closes the original first-Action network acceptance blocker.
- On 2026-09-15 an isolated real ComfyUI 0.35.1 instance reconstructed a 188,908-byte workflow in two authenticated resource chunks and parsed it as JSON. The same live pass verified repeated append patches plus complete readback/cleanup and completed a tiny native prompt. The sampled `/object_info` response fit below the 2 MiB inline limit, so oversized native-response continuation remains unit-tested rather than live-triggered in that pass.
- Later on 2026-09-15 the owner's normal 8188 runtime was deliberately restarted onto the current release-candidate code with an empty queue. Through the public Tailscale Action endpoint, a current 290,301-byte workflow was reconstructed and JSON-validated in three chunks; a second public mutating pass verified CRUD, repeated chunk patches/readback/cleanup, native `/system_stats`, and a successful tiny prompt plus cleanup.
- The isolated Tailscale Action node now has an enabled highest-privilege at-logon Scheduled Task. A controlled handoff stopped only the CUICommander-owned userspace daemon, started it through that task, verified the Action node online, restored the existing Funnel mapping, and repeated the public large-resource acceptance successfully.
- Final Custom GPT UI acceptance passed on 2026-09-15 after refreshing the pasted Action schema/instructions: the GPT read the current 290,301-byte workflow completely through `readComfyUIResource`, followed continuation to `eof=true` in five successful Action chunks, parsed the full JSON, and reported its top-level keys without modifying the file. This closes the large-resource GPT UI acceptance blocker.

## Remaining external acceptance / release blockers

1. Verify one genuinely large public model transfer into a dynamically registered model root if desired before calling transfer acceptance exhaustive.
2. Claim/configure the Comfy Registry publisher and publishing secret before public Manager/Registry release.

## Runtime note

- The owner's normal ComfyUI listener on port 8188 now runs the current release-candidate code. Its public Action gateway advertises the chunked resource read/patch and retained native-response continuation routes, and both read-only and mutating public acceptance pass after the controlled restart.

No additional full-control fallback primitive is currently justified: tested ComfyUI-owned surfaces are reachable through discovered filesystem roots or the live native route table. If a future ComfyUI-owned capability is proven unreachable by those planes, add the smallest bounded generic fallback rather than a provider adapter.
