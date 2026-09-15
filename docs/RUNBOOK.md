# Runbook

## Local start

1. `npm ci` after a fresh clone.
2. `npm run doctor` to confirm the supported runtime and required files.
3. `npm run dev` for the live preview.

## Verification

- `npm run verify` — fast default gate: formatting, lint, types, UI conformance, unit tests, build.
- `npm run verify:full` — adds E2E/accessibility and visual regression.
- `npm run test:visual:update` — only after confirming a visual change is intentional.

## Failure protocol

First reproduce and identify blast radius. Preserve local/user work, inspect current state and recent changes, then choose the smallest reversible fix. Do not change global machine configuration or unrelated code merely to make a check pass.

If an environment/check cannot run, record the work as unverified and state why. Never regenerate visual baselines, delete tests, loosen validation, or reset Git simply to turn red checks green.

## Release/operations

A real project should add deployment, rollback, monitoring, backup/recovery, supported-platform, and production-data rules only when those concerns become applicable. Production changes require explicit safeguards; local test/debug workflows must not casually target production data or credentials.

## Parallel work

Default: one AI writer per working tree. If parallel work is useful, create separate branches/worktrees, verify independently, then integrate deliberately.

## Controlled live acceptance

Live acceptance is separate from the default repository gate because it requires a running ComfyUI instance and a credential stored outside the repository.

- Read-only API acceptance: set `CUICOMMANDER_TOKEN_FILE` to the runtime `connection.json`, optionally set `CUICOMMANDER_BASE_URL`, then run `python scripts/live_acceptance.py`.
- Mutating acceptance: run the same script with `--mutating` only against a deliberately Full-control local instance. The runner creates uniquely named acceptance resources and removes them afterward.
- Embedded browser acceptance: with the same environment variables, run `node scripts/live-ui-acceptance.mjs`.
- Workflow/operator mutation acceptance: on an isolated Full-control-capable instance, set `CUICOMMANDER_ACCEPT_MUTATIONS=1` and run `node scripts/operator-live-acceptance.mjs`; it queues a tiny native workflow and cleans up its generated file/output.
- Never print, commit, or paste the configured access key into test source or shell history.
- Do not force-restart an owner's active ComfyUI session merely to validate a development build; prefer an isolated localhost test instance when practical.

## Remote access recovery

- If a Custom GPT credential is lost or suspected compromised, use the localhost CUICommander setup page to **Rotate key**, then update the Custom GPT Action authentication value.
- If remote exposure must stop immediately, use **Disable remote access**. CUICommander removes only the Funnel entry it owns and leaves unrelated Tailscale Serve/Funnel services intact.
- Never use `tailscale serve reset` or `tailscale funnel reset` as a CUICommander recovery step; existing user services may share the same tailnet machine.
- If Tailscale is absent, install/sign in with the official Tailscale client, then use **Refresh detection** in CUICommander. If it is disconnected, restore Tailscale connectivity before enabling the managed Funnel.
- Manual HTTPS origins remain supported, but they must terminate at the isolated CUICommander Action API rather than raw ComfyUI port 8188.

## Comfy Registry release

- `npm run package:check` verifies package/version metadata consistency before release.
- The repository owner must claim/configure the `[tool.comfy].PublisherId` and add the required Registry publishing secret to GitHub before publishing.
- Registry publishing is intentionally manual through `.github/workflows/publish-registry.yml`; do not publish merely because CI is green.
- Publish only after the real Custom GPT Action acceptance has passed and the release commit/tag matches the package version.
