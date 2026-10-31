# Failure taxonomy on h55-heldout (54 runs)

Counts are planted problems not fixed (T1-T4), false flags (T5), and runs that claimed everything was fixed but failed (T6).

## T1 Meaning not checked: 1
A real token or class carries the wrong meaning and the agent never flags it: status color on plain secondary text, a destructive action in primary green, a safe action in danger red, a status pill showing the wrong status. These pass any token check; only reading what the element says catches them (R7).
- e.g. secondary text colored var(--spectrum-accent-content-color-default), which signals a status it doesn't have (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)

## T2 Readability not checked: 0
A real token makes text unreadable and the agent never flags it: the disabled color on body text, a border color used as text, white text on a light surface. Token names look fine; only checking contrast catches them (R5).

## T3 Incomplete sweep: 3
A raw, off-scale value is left in place and never reported, usually in the page's own layout rules (container margins, gaps, weights) rather than in components (R1-R4).
- e.g. font-weight hard-coded as 400 instead of var(--spectrum-regular-font-weight) (intended `font-weight: var(--spectrum-regular-font-weight)`)
- e.g. border width hard-coded instead of var(--spectrum-border-width-100) (intended `border: var(--spectrum-border-width-100) solid var(--spectrum-gray-300`)

## T4 Wrong fix: 3
The agent found the problem but fixed it to the wrong value or variant: an off-scale number rounded to the wrong step, a rebuilt component restored with the wrong variant or size.
- e.g. status pill rebuilt by hand instead of using .spectrum-Badge (spectrum-Badge spectrum-Badge--accent) (intended `<div class="spectrum-Badge spectrum-Badge--accent" data-qa="pricing-ba`)
- e.g. color set to an off-palette hex near var(--spectrum-neutral-content-color-default) (intended `color: var(--spectrum-neutral-content-color-default)`)
- e.g. button rebuilt by hand instead of using .spectrum-Button (spectrum-Button spectrum-Button--outline spectrum-Button--secondary spectrum-Button--sizeS) (intended `<button class="spectrum-Button spectrum-Button--outline spectrum-Butto`)

## T5 False alarm: 0
The agent flags something the rules allow and often changes it, which breaks what was fine (shows up as regressions).

## T6 Overconfident report: 5
The report says everything is fixed when it isn't.

