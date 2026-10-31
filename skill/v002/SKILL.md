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

## Text-color role check (R5)

A real token can still be the wrong token: being a valid `var(--…)` does not make text readable. For every `color:` that applies to text (in CSS rules and inline `style`), ask: is this token's role in RULES.md the job this text is doing?

- `--fgColor-default` or `--fgColor-muted`: fine for ordinary text.
- `--fgColor-disabled`: only on a disabled control. On any other text it fails contrast. Fix: `--fgColor-default` for primary text (titles, names, labels, cell values), `--fgColor-muted` for secondary text (help, notes, meta, headers).
- `--fgColor-onEmphasis`: only on a `*-emphasis` background. Find the element's actual background; if it is a default, muted or `*-muted` surface, the text is near-invisible. Fix with default or muted as above.
- Any `--borderColor-*` or `--bgColor-*` token used as a text color: wrong role, fails contrast. Fix with default or muted as above.

Report each of these as R5. Don't flag a token that is in its documented role.
