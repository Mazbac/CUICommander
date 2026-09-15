# UI and interaction contract

The UI must feel intentionally designed across time, not merely look good on the first screen. Industry/platform guidance and existing product patterns outrank AI taste.

## Core rules

- KISS: if removing copy, decoration, a container, or a control does not reduce understanding, remove it.
- Friendly means clear labels, sensible defaults, useful errors, and predictable behavior — not verbose explanation.
- Use Mantine components and semantic theme tokens before custom UI or raw values.
- Shared layouts own geometry. Feature screens provide content and product behavior, not bespoke page spacing.
- Consistency across screens beats local visual optimization.
- Do not patch alignment with arbitrary offsets; fix the responsible layout/component.
- One canonical term and action label per product concept.

## Canonical structure

Prefer reusable primitives such as `AppFrame`, `PageHeader`, `Section`, `Toolbar`, `FormActions`, `EmptyState`, `ErrorState`, and table patterns. Create a new pattern only when existing ones cannot express the requirement cleanly.

Before implementing a screen, inspect the closest analogous screen. New list pages should resemble established list pages; settings should use established settings structure; destructive flows should reuse the canonical confirmation pattern.

## Product information architecture

- Primary navigation is **Home / ChatGPT / Activity / Advanced**.
- Home answers whether the bridge is usable, what happened recently, and what needs attention.
- ChatGPT owns setup, access, remote connectivity, credentials, and recovery.
- Activity is the human-readable audit trail for consequential operations.
- Files/resources, transfers/jobs, workflows, and runtime remain fully capable operator tools under Advanced; they do not compete with the core product journey.
- ChatGPT is where the user asks, ComfyUI is where work runs, and CUICommander is where the bridge is configured, supervised, and recovered.

## Visual tokens

Typography, spacing, control sizes, radii, borders, colors, shadows, breakpoints, focus treatment, and motion belong to the theme or shared components. Semantic color communicates status; color is never the only status signal.

## Product visual direction

- The product uses a neutral-first light/dark palette with one deep-blue product accent for interactive emphasis. Green, amber/yellow, and red are reserved for semantic status.
- Raw palette values may exist only in `src/theme/theme.ts`; feature code and CSS consume semantic/theme tokens instead.
- Light mode uses a pale neutral shell with white surfaces; dark mode uses near-black chrome with charcoal surfaces. Both modes preserve the same hierarchy, spacing, and component geometry.
- Appearance supports System, Light, and Dark. System is the default; an explicit user choice persists through Mantine color-scheme storage.
- Cards and setup surfaces use the shared surface radius; controls and navigation use the shared control radius. Feature screens do not invent local corner styles.
- The shell uses a quiet neutral background with white/dark shared surfaces and one border token. Shadows are exceptional, not structural.
- Status is normally expressed with concise text and, when useful, a small semantic indicator. Pills/badges are reserved for compact categorical metadata, not decorative state labels; never rely on color alone.
- First-run setup uses progressive disclosure: show the next required step, keep advanced transport/schema details secondary, and never expose raw ComfyUI as the public endpoint.
- Reflow is a release gate at 320px, 390px, and desktop widths; clipped badges, horizontal overflow, and one-off responsive exceptions are regressions.

## Applicable states

For each feature, explicitly determine which states apply: default, hover/focus/disabled, loading, empty, error, partial/stale data, offline/reconnecting, permission/read-only, success, destructive/reversible, long/missing content, and supported viewport/input modes. Do not implement impossible states merely to satisfy a checklist.

Complex asynchronous or consequential workflows should define valid state transitions instead of accumulating contradictory booleans.

## Accessibility and platform behavior

WCAG 2.2 AA is the web baseline. Use semantic HTML, visible focus, keyboard operation, meaningful labels, sufficient contrast, non-color status cues, zoom/reflow support, reduced-motion/high-contrast preferences, and accessible dynamic status announcements. Use the component library's dialog/menu/popover focus behavior instead of reimplementing it.

Normal browser behavior is part of UX: meaningful state should survive refresh/deep links when appropriate, back/forward should work, and unsaved work needs an explicit autosave/save/discard policy.

## Anti-drift

- Canonical components and the UI showroom are the visual reference.
- Use stress data: long strings, empty values, Unicode, large numbers, many rows, and realistic filenames.
- Visual snapshots are reviewed evidence. Never regenerate them blindly after a failure.
- Token/shared-component changes require checking representative consumers.
- Preview the actual application code; never maintain a separate mock UI that can diverge.
- Intentional system evolution happens centrally and moves affected screens together.
