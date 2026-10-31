---
name: design-system-qa
description: Review a UI screen against the design system rules and fix the violations.
---

# Design-system QA

Review the screen against `design-system/RULES.md`.

1. Read `RULES.md` and the screen.
2. Find anything that breaks a rule.
   - A real token can still be wrong. After the raw-value check, search the screen for each meaning word: `danger`, `success`, `attention`, `done`, `btn-primary`. For every hit, read the visible text of the element it lands on and ask one question: does R7 allow this meaning for what this text says?
     - Button: delete/remove/leave/revoke means `.btn-danger`. Any other action must not be danger. The primary green is never on a destructive action.
     - Label: does the color match the status the words report?
     - Plain text (a note, count, meta line, lede, help text): status colors never go here. Use `--fgColor-muted`, or `--fgColor-default` if it is a primary label.
   - Fix only a clear contradiction with R7's words. If two readings both fit (for example, a completed item in success), leave it alone.
3. Fix each problem in the screen using the design system's tokens and components.
4. Record each problem you found and how you fixed it.
