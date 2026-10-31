# Failure taxonomy on h55-train (52 runs)

Counts are planted problems not fixed (T1-T4), false flags (T5), and runs that claimed everything was fixed but failed (T6).

## T1 Meaning not checked: 3
A real token or class carries the wrong meaning and the agent never flags it: status color on plain secondary text, a destructive action in primary green, a safe action in danger red, a status pill showing the wrong status. These pass any token check; only reading what the element says catches them (R7).
- e.g. status pill uses spectrum-Badge--positive, which contradicts what it reports (intended `<div class="spectrum-Badge spectrum-Badge--informative" data-qa="notif`)
- e.g. destructive action styled as the accent (call-to-action) button (intended `<button class="spectrum-Button spectrum-Button--outline spectrum-Butto`)

## T2 Readability not checked: 0
A real token makes text unreadable and the agent never flags it: the disabled color on body text, a border color used as text, white text on a light surface. Token names look fine; only checking contrast catches them (R5).

## T3 Incomplete sweep: 1
A raw, off-scale value is left in place and never reported, usually in the page's own layout rules (container margins, gaps, weights) rather than in components (R1-R4).
- e.g. font-weight hard-coded as 700 instead of var(--spectrum-bold-font-weight) (intended `font-weight: var(--spectrum-bold-font-weight)`)

## T4 Wrong fix: 5
The agent found the problem but fixed it to the wrong value or variant: an off-scale number rounded to the wrong step, a rebuilt component restored with the wrong variant or size.
- e.g. destructive action styled as the accent (call-to-action) button (intended `<button class="spectrum-Button spectrum-Button--outline spectrum-Butto`)
- e.g. secondary text colored var(--spectrum-negative-content-color-default), which signals a status it doesn't have (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. secondary text colored var(--spectrum-accent-content-color-default), which signals a status it doesn't have (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)

## T5 False alarm: 1
The agent flags something the rules allow and often changes it, which breaks what was fine (shows up as regressions).
- e.g. flagged billing-summary-flash as R7: The invoice-due banner used the informative variant (spectrum-InLineAlert--info). A payment due date is a pending state, which the rules say

## T6 Overconfident report: 10
The report says everything is fixed when it isn't.

