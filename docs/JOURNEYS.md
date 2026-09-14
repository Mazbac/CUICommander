# User lifecycle

## Product-specific journey

1. Install CUICommander in ComfyUI `custom_nodes` and restart ComfyUI.
2. Open the CUICommander setup surface and verify the live ComfyUI roots/runtime are detected.
3. Create or rotate the connection credential, choose the intended access level, and copy the Action schema plus GPT instructions.
4. Make the local ComfyUI HTTP endpoint available to the Custom GPT over a user-chosen authenticated HTTPS edge/tunnel; CUICommander does not require one tunnel vendor.
5. In normal use, ChatGPT discovers current node/routes/roots first when needed, uses generic CRUD/native execution, then verifies the resulting ComfyUI state.
6. Long model transfers and workflow runs expose durable job state so reconnects do not require guessing whether work completed.

## Recovery and exit

- Lost/compromised GPT credentials can be rotated without reinstalling CUICommander.
- A failed or stale filesystem mutation must stop rather than overwrite newer state.
- ComfyUI/custom-node updates must preserve the generic discovery contract; missing/deprecated upstream primitives surface as diagnostics, not silent behavior drift.
- Uninstall removes CUICommander-owned settings/activity but never deletes user workflows, models, outputs, or unrelated ComfyUI data.
