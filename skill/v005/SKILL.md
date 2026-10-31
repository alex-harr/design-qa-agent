---
name: design-system-qa
description: Review a UI screen against the design system rules and fix the violations.
---

# Design-system QA

Review the screen against `design-system/RULES.md`.

1. Read `RULES.md` and the screen.
2. Find anything that breaks a rule.
3. Walk the screen's HTML body top to bottom (markup, not the CSS). A real token can still be wrong for the element it is on. For each element that shows text, plus every button and `.Label`:
   - Name its role from what it says and where it sits: heading, body text, secondary/metadata/count, link, status pill, safe action, main safe action, destructive action.
   - Look up the color and variant it actually gets (its classes, its CSS rule, inline style), then check that against the role:
     - heading/body → `--fgColor-default`; secondary, metadata, counts → `--fgColor-muted`; links → `--fgColor-accent`.
     - Text never uses `--fgColor-disabled` (unless it is a disabled control), `--fgColor-onEmphasis` (unless its own background is an emphasis one), or a `--borderColor-*`/`--bgColor-*` token.
     - Destructive or hard-to-undo action → `.btn-danger`. Safe action → never `.btn-danger`; `.btn-primary` only for the main safe action.
     - `.Label` variant matches the status its text states, per R7's mapping.
   - Fix only clear contradictions. Leave alone any token defined in `design-system/vendor/` that fits the role, and don't add colors to elements that inherit them.
4. Fix each problem in the screen using the design system's tokens and components.
5. Record each problem you found and how you fixed it.
