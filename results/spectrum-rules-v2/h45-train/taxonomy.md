# Failure taxonomy on h45-train (52 runs)

Counts are planted problems not fixed (T1-T4), false flags (T5), and runs that claimed everything was fixed but failed (T6).

## T1 Meaning not checked: 28
A real token or class carries the wrong meaning and the agent never flags it: status color on plain secondary text, a destructive action in primary green, a safe action in danger red, a status pill showing the wrong status. These pass any token check; only reading what the element says catches them (R7).
- e.g. status pill uses spectrum-Badge--positive, which contradicts what it reports (intended `<div class="spectrum-Badge spectrum-Badge--informative" data-qa="notif`)
- e.g. status pill uses spectrum-Badge--negative, which contradicts what it reports (intended `<div class="spectrum-Badge spectrum-Badge--positive" data-qa="notifica`)
- e.g. secondary text colored var(--spectrum-negative-content-color-default), which signals a status it doesn't have (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. secondary text colored var(--spectrum-accent-content-color-default), which signals a status it doesn't have (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)

## T2 Readability not checked: 13
A real token makes text unreadable and the agent never flags it: the disabled color on body text, a border color used as text, white text on a light surface. Token names look fine; only checking contrast catches them (R5).
- e.g. text color set to var(--spectrum-neutral-visual-color), a real token that fails contrast here (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. text uses the disabled color and fails contrast (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. text uses the disabled color and fails contrast (intended `color: var(--spectrum-neutral-content-color-default)`)
- e.g. text color set to var(--spectrum-gray-300), a real token that fails contrast here (intended `color: var(--spectrum-neutral-content-color-default)`)

## T3 Incomplete sweep: 15
A raw, off-scale value is left in place and never reported, usually in the page's own layout rules (container margins, gaps, weights) rather than in components (R1-R4).
- e.g. gap uses 13px, off the spacing scale (intended `gap: var(--spectrum-spacing-200)`)
- e.g. padding uses 17px, off the spacing scale (intended `padding: var(--spectrum-spacing-300) 0`)
- e.g. gap uses 17px, off the spacing scale (intended `gap: var(--spectrum-spacing-300)`)
- e.g. gap uses 15px, off the spacing scale (intended `gap: var(--spectrum-spacing-300)`)

## T4 Wrong fix: 9
The agent found the problem but fixed it to the wrong value or variant: an off-scale number rounded to the wrong step, a rebuilt component restored with the wrong variant or size.
- e.g. border-radius 12px instead of var(--spectrum-corner-radius-200) (intended `border-radius: var(--spectrum-corner-radius-200)`)
- e.g. button rebuilt by hand instead of using .spectrum-Button (spectrum-Button spectrum-Button--outline spectrum-Button--secondary spectrum-Button--sizeS) (intended `<button class="spectrum-Button spectrum-Button--outline spectrum-Butto`)
- e.g. secondary text colored var(--spectrum-negative-content-color-default), which signals a status it doesn't have (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. status pill rebuilt by hand instead of using .spectrum-Badge (spectrum-Badge spectrum-Badge--neutral member-role) (intended `<div class="spectrum-Badge spectrum-Badge--neutral member-role" data-q`)

## T5 False alarm: 2
The agent flags something the rules allow and often changes it, which breaks what was fine (shows up as regressions).
- e.g. flagged .note-title as R3: Missing explicit font-size token. Element displays text (notification titles) but only has font-weight and color from tokens, no font-size. 
- e.g. flagged .issues-head as R3: Missing explicit font-size token. Element displays text (list header counts) but only has font-weight and color from tokens, no font-size. P

## T6 Overconfident report: 41
The report says everything is fixed when it isn't.

