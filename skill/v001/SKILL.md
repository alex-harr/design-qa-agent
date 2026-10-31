---
name: design-system-qa
description: Review a UI screen against the design system rules and fix the violations.
---

# Design-system QA

Review the screen against `design-system/RULES.md`.

1. Read `RULES.md` and the screen.
2. Find anything that breaks a rule.
3. Fix each problem in the screen using the design system's tokens and components.
4. Record each problem you found and how you fixed it.

## Meaning pass (R7): do this after the token fixes

A valid token can still carry the wrong meaning. Token checks never catch this, so do a separate pass:

1. List every element that carries a meaning color: any `danger`, `success`, `attention`, `accent` or `done` token in the CSS, every `.btn-primary` and `.btn-danger`, and every `.Label--*`. For a CSS class, find the elements that use it in the HTML.
2. For each one, read the element's visible text and write one line: "<text> → means <destructive / safe / error / success / pending / link / secondary info>".
3. Check that line against R7:
   - Plain secondary text (metadata, counts, notes, ledes, help text) → `--fgColor-muted`, never a status color.
   - Actions that destroy data or access, or are hard to undo (anything in a Danger zone) → `.btn-danger`, never `.btn-primary`.
   - Every other action (it keeps, exports, completes or backs out of something) → `.btn`, or `.btn-primary` for the main one, never `.btn-danger`.
   - A `.Label` variant must match the status its text reports (a failure is danger, not success).
4. Change only what clearly contradicts its text. Success also covers completion, so a finished or shipped item in success is fine; leave anything the rules allow.
