---
name: design-system-qa
description: Review a UI screen against the design system rules and fix the violations.
---

# Design-system QA

Review the screen against `design-system/RULES.md`.

1. Read `RULES.md` and the screen.
2. Find anything that breaks a rule.
3. Fix each problem in the screen using the design system's tokens and components.
4. Before writing the report, re-read the edited screen in full and do a rule-by-rule audit, R1 through R7, one rule at a time:
   - For each rule, write one line: the rule ID, which parts of the screen you checked against it (the page's own layout CSS, inline styles, and every component), and what you found.
   - A rule counts as checked only if you looked at evidence for it. Token names alone are not evidence for R5 (you must judge the text color against its actual background) or R7 (you must read what the element says or does).
   - If the audit turns up something new, fix it and audit that rule again.
5. Record each problem you found and how you fixed it. Be honest about doubt:
   - Claim everything is fixed only if every rule in the audit was actually checked and nothing is left.
   - If any rule was skipped, only partly checked, or has something you were unsure about, say so in the report, name the rule, and lower your confidence to match.
