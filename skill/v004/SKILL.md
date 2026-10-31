---
name: design-system-qa
description: Review a UI screen against the design system rules and fix the violations.
---

# Design-system QA

Review the screen against `design-system/RULES.md`.

1. Read `RULES.md` and the screen.
2. Find anything that breaks a rule.
3. Fix each problem in the screen using the design system's tokens and components. Pick the fix value carefully:
   - **Raw number → token:** convert to px (1rem = 16px), list the scale tokens just below and just above, and pick the one with the smaller difference. Never round down by habit. If a token's px value isn't in RULES.md, look it up in `design-system/vendor/` before choosing.
   - **Raw color → token:** pick the token whose role matches what the element is (body text → default, secondary/metadata → muted, link → accent), not only the nearest hex.
   - **Hand-built lookalike → component:** replace the element's inline `style` entirely with the component classes; don't just swap its raw values for tokens. Keep the element's own existing classes, `data-*` attributes, `type` and text.
   - **Choosing variant and size:** take the variant from what the element does (main safe action → `btn-primary`, destructive → `btn-danger`, low-emphasis inline action → `btn-invisible`, otherwise plain `btn`; Label color from the status it reports). Add `btn-sm` when the lookalike was compact or sits beside other `btn-sm` buttons in the same row or list. Match sibling elements that already use the component.
4. Record each problem you found and how you fixed it.
