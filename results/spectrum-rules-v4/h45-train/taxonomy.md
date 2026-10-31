# Failure taxonomy on h45-train (52 runs)

Counts are planted problems not fixed (T1-T4), false flags (T5), and runs that claimed everything was fixed but failed (T6).

## T1 Meaning not checked: 33
A real token or class carries the wrong meaning and the agent never flags it: status color on plain secondary text, a destructive action in primary green, a safe action in danger red, a status pill showing the wrong status. These pass any token check; only reading what the element says catches them (R7).
- e.g. status pill uses spectrum-Badge--positive, which contradicts what it reports (intended `<div class="spectrum-Badge spectrum-Badge--informative" data-qa="notif`)
- e.g. status pill uses spectrum-Badge--negative, which contradicts what it reports (intended `<div class="spectrum-Badge spectrum-Badge--positive" data-qa="notifica`)
- e.g. secondary text colored var(--spectrum-negative-content-color-default), which signals a status it doesn't have (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. secondary text colored var(--spectrum-accent-content-color-default), which signals a status it doesn't have (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)

## T2 Readability not checked: 20
A real token makes text unreadable and the agent never flags it: the disabled color on body text, a border color used as text, white text on a light surface. Token names look fine; only checking contrast catches them (R5).
- e.g. text color set to var(--spectrum-neutral-visual-color), a real token that fails contrast here (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. text uses the disabled color and fails contrast (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. text uses the disabled color and fails contrast (intended `color: var(--spectrum-neutral-content-color-default)`)
- e.g. text color set to var(--spectrum-neutral-visual-color), a real token that fails contrast here (intended `color: var(--spectrum-accent-content-color-default)`)

## T3 Incomplete sweep: 20
A raw, off-scale value is left in place and never reported, usually in the page's own layout rules (container margins, gaps, weights) rather than in components (R1-R4).
- e.g. font-weight hard-coded as 700 instead of var(--spectrum-bold-font-weight) (intended `font-weight: var(--spectrum-bold-font-weight)`)
- e.g. border width hard-coded instead of var(--spectrum-border-width-100) (intended `border-top: var(--spectrum-border-width-100) solid var(--spectrum-gray`)
- e.g. border-radius 15px instead of var(--spectrum-corner-radius-800) (intended `border-radius: var(--spectrum-corner-radius-800)`)
- e.g. gap uses 13px, off the spacing scale (intended `gap: var(--spectrum-spacing-200)`)

## T4 Wrong fix: 6
The agent found the problem but fixed it to the wrong value or variant: an off-scale number rounded to the wrong step, a rebuilt component restored with the wrong variant or size.
- e.g. margin uses 34px, off the spacing scale (intended `margin: var(--spectrum-spacing-500) auto`)
- e.g. button rebuilt by hand instead of using .spectrum-Button (spectrum-Button spectrum-Button--outline spectrum-Button--secondary spectrum-Button--sizeS) (intended `<button class="spectrum-Button spectrum-Button--outline spectrum-Butto`)
- e.g. secondary text colored var(--spectrum-negative-content-color-default), which signals a status it doesn't have (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. margin uses 5px, off the spacing scale (intended `margin: var(--spectrum-spacing-75) 0 0`)

## T5 False alarm: 4
The agent flags something the rules allow and often changes it, which breaks what was fine (shows up as regressions).
- e.g. flagged .billing-title as R1: Missing color property; heading should have explicit color token
- e.g. flagged .note-title as R3: Missing font-size token. This element had font-weight set to a token but no font-size, causing it to inherit an unscaled size from the paren
- e.g. flagged .note-title as R3: Element sets font-weight and color to tokens but lacks explicit font-size, violating the requirement that type properties use tokens
- e.g. flagged .member-name as R3: Element sets font-weight and color to tokens but lacks explicit font-size, violating the requirement that type properties use tokens

## T6 Overconfident report: 39
The report says everything is fixed when it isn't.

