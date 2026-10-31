# Failure taxonomy on base-train-b (52 runs)

Counts are planted problems not fixed (T1-T4), false flags (T5), and runs that claimed everything was fixed but failed (T6).

## T1 Meaning not checked: 34
A real token or class carries the wrong meaning and the agent never flags it: status color on plain secondary text, a destructive action in primary green, a safe action in danger red, a status pill showing the wrong status. These pass any token check; only reading what the element says catches them (R7).
- e.g. status pill uses spectrum-Badge--positive, which contradicts what it reports (intended `<div class="spectrum-Badge spectrum-Badge--informative" data-qa="notif`)
- e.g. status pill uses spectrum-Badge--negative, which contradicts what it reports (intended `<div class="spectrum-Badge spectrum-Badge--positive" data-qa="notifica`)
- e.g. secondary text colored var(--spectrum-negative-content-color-default), which signals a status it doesn't have (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. destructive action styled as the accent (call-to-action) button (intended `<button class="spectrum-Button spectrum-Button--outline spectrum-Butto`)

## T2 Readability not checked: 25
A real token makes text unreadable and the agent never flags it: the disabled color on body text, a border color used as text, white text on a light surface. Token names look fine; only checking contrast catches them (R5).
- e.g. text color set to var(--spectrum-neutral-visual-color), a real token that fails contrast here (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. text uses the disabled color and fails contrast (intended `color: var(--spectrum-neutral-content-color-default)`)
- e.g. text uses the disabled color and fails contrast (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. text color set to var(--spectrum-gray-300), a real token that fails contrast here (intended `color: var(--spectrum-neutral-content-color-default)`)

## T3 Incomplete sweep: 18
A raw, off-scale value is left in place and never reported, usually in the page's own layout rules (container margins, gaps, weights) rather than in components (R1-R4).
- e.g. status pill rebuilt by hand instead of using .spectrum-Badge (spectrum-Badge spectrum-Badge--neutral member-role) (intended `<div class="spectrum-Badge spectrum-Badge--neutral member-role" data-q`)
- e.g. margin-bottom uses 17px, off the spacing scale (intended `margin-bottom: var(--spectrum-spacing-300)`)
- e.g. margin uses 26px, off the spacing scale (intended `margin: 0 0 var(--spectrum-spacing-400)`)
- e.g. font-weight hard-coded as 700 instead of var(--spectrum-bold-font-weight) (intended `font-weight: var(--spectrum-bold-font-weight)`)

## T4 Wrong fix: 17
The agent found the problem but fixed it to the wrong value or variant: an off-scale number rounded to the wrong step, a rebuilt component restored with the wrong variant or size.
- e.g. margin uses 26px, off the spacing scale (intended `margin: 0 0 var(--spectrum-spacing-400)`)
- e.g. margin uses 34px, off the spacing scale (intended `margin: var(--spectrum-spacing-500) auto`)
- e.g. button rebuilt by hand instead of using .spectrum-Button (spectrum-Button spectrum-Button--fill spectrum-Button--accent) (intended `<button class="spectrum-Button spectrum-Button--fill spectrum-Button--`)
- e.g. border-radius 15px instead of var(--spectrum-corner-radius-800) (intended `border-radius: var(--spectrum-corner-radius-800)`)

## T5 False alarm: 5
The agent flags something the rules allow and often changes it, which breaks what was fine (shows up as regressions).
- e.g. flagged .projects-title as R1: Missing color property; text color must explicitly use a Spectrum color token
- e.g. flagged .billing-title as R1: Missing color token for heading text
- e.g. flagged .issues-head as R4: border-radius uses hardcoded 0 values instead of the --spectrum-corner-radius-0 token
- e.g. flagged .projects-title as R1: Title element missing explicit color token, would inherit from body

## T6 Overconfident report: 45
The report says everything is fixed when it isn't.

