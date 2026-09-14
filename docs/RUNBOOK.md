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
- Never print, commit, or paste the configured access key into test source or shell history.
- Do not force-restart an owner's active ComfyUI session merely to validate a development build; prefer an isolated localhost test instance when practical.
