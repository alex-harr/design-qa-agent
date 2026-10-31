# Failure taxonomy on base-heldout (54 runs)

Counts are planted problems not fixed (T1-T4), false flags (T5), and runs that claimed everything was fixed but failed (T6).

## T1 Meaning not checked: 33
A real token or class carries the wrong meaning and the agent never flags it: status color on plain secondary text, a destructive action in primary green, a safe action in danger red, a status pill showing the wrong status. These pass any token check; only reading what the element says catches them (R7).
- e.g. secondary text colored var(--spectrum-accent-content-color-default), which signals a status it doesn't have (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. secondary text colored var(--spectrum-negative-content-color-default), which signals a status it doesn't have (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. safe action "Follow" styled as a danger button (intended `<button class="spectrum-Button spectrum-Button--fill spectrum-Button--`)
- e.g. safe action "Sign in" styled as a danger button (intended `<button class="spectrum-Button spectrum-Button--fill spectrum-Button--`)

## T2 Readability not checked: 34
A real token makes text unreadable and the agent never flags it: the disabled color on body text, a border color used as text, white text on a light surface. Token names look fine; only checking contrast catches them (R5).
- e.g. text uses the disabled color and fails contrast (intended `color: var(--spectrum-neutral-content-color-default)`)
- e.g. text uses the disabled color and fails contrast (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. text color set to var(--spectrum-gray-300), a real token that fails contrast here (intended `color: var(--spectrum-neutral-content-color-default)`)
- e.g. text color set to var(--spectrum-gray-300), a real token that fails contrast here (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)

## T3 Incomplete sweep: 21
A raw, off-scale value is left in place and never reported, usually in the page's own layout rules (container margins, gaps, weights) rather than in components (R1-R4).
- e.g. font-weight hard-coded as 700 instead of var(--spectrum-bold-font-weight) (intended `font-weight: var(--spectrum-bold-font-weight)`)
- e.g. margin uses 7px, off the spacing scale (intended `margin: 0 0 var(--spectrum-spacing-100)`)
- e.g. margin uses 5px, off the spacing scale (intended `margin: 0 0 var(--spectrum-spacing-75)`)
- e.g. border width hard-coded instead of var(--spectrum-border-width-100) (intended `border: var(--spectrum-border-width-100) solid var(--spectrum-gray-300`)

## T4 Wrong fix: 23
The agent found the problem but fixed it to the wrong value or variant: an off-scale number rounded to the wrong step, a rebuilt component restored with the wrong variant or size.
- e.g. color set to an off-palette hex near var(--spectrum-neutral-content-color-default) (intended `color: var(--spectrum-neutral-content-color-default)`)
- e.g. margin uses 31px, off the spacing scale (intended `margin: 0 0 var(--spectrum-spacing-500)`)
- e.g. margin-bottom uses 7px, off the spacing scale (intended `margin-bottom: var(--spectrum-spacing-100)`)
- e.g. border-radius 14px instead of var(--spectrum-corner-radius-800) (intended `border-radius: var(--spectrum-corner-radius-800)`)

## T5 False alarm: 7
The agent flags something the rules allow and often changes it, which breaks what was fine (shows up as regressions).
- e.g. flagged .auth-label as R1: Missing color property - visible text label with font-size and font-weight but no color token
- e.g. flagged .confirm-label as R1, R3: Missing font-size and color properties - styled label without complete type and color tokens
- e.g. flagged .onboard-title as R1: Missing color property - heading with font-size and font-weight but no color token
- e.g. flagged .auth-label as R1: Missing color property. Text elements must use color tokens explicitly.

## T6 Overconfident report: 48
The report says everything is fixed when it isn't.

