# Failure taxonomy on h45-heldout (54 runs)

Counts are planted problems not fixed (T1-T4), false flags (T5), and runs that claimed everything was fixed but failed (T6).

## T1 Meaning not checked: 29
A real token or class carries the wrong meaning and the agent never flags it: status color on plain secondary text, a destructive action in primary green, a safe action in danger red, a status pill showing the wrong status. These pass any token check; only reading what the element says catches them (R7).
- e.g. secondary text colored var(--spectrum-accent-content-color-default), which signals a status it doesn't have (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. secondary text colored var(--spectrum-negative-content-color-default), which signals a status it doesn't have (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. safe action "Follow" styled as a danger button (intended `<button class="spectrum-Button spectrum-Button--fill spectrum-Button--`)
- e.g. safe action "Upload" styled as a danger button (intended `<button class="spectrum-Button spectrum-Button--fill spectrum-Button--`)

## T2 Readability not checked: 22
A real token makes text unreadable and the agent never flags it: the disabled color on body text, a border color used as text, white text on a light surface. Token names look fine; only checking contrast catches them (R5).
- e.g. text uses the disabled color and fails contrast (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)
- e.g. text color set to var(--spectrum-gray-300), a real token that fails contrast here (intended `color: var(--spectrum-neutral-content-color-default)`)
- e.g. text uses the disabled color and fails contrast (intended `color: var(--spectrum-neutral-content-color-default)`)
- e.g. text color set to var(--spectrum-gray-300), a real token that fails contrast here (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)

## T3 Incomplete sweep: 20
A raw, off-scale value is left in place and never reported, usually in the page's own layout rules (container margins, gaps, weights) rather than in components (R1-R4).
- e.g. margin uses 7px, off the spacing scale (intended `margin: 0 0 var(--spectrum-spacing-100)`)
- e.g. margin uses 5px, off the spacing scale (intended `margin: 0 0 var(--spectrum-spacing-75)`)
- e.g. padding uses 27px, off the spacing scale (intended `padding: var(--spectrum-spacing-400)`)
- e.g. font-weight hard-coded as 700 instead of var(--spectrum-bold-font-weight) (intended `font-weight: var(--spectrum-bold-font-weight)`)

## T4 Wrong fix: 14
The agent found the problem but fixed it to the wrong value or variant: an off-scale number rounded to the wrong step, a rebuilt component restored with the wrong variant or size.
- e.g. status pill rebuilt by hand instead of using .spectrum-Badge (spectrum-Badge spectrum-Badge--accent) (intended `<div class="spectrum-Badge spectrum-Badge--accent" data-qa="pricing-ba`)
- e.g. color set to an off-palette hex near var(--spectrum-neutral-content-color-default) (intended `color: var(--spectrum-neutral-content-color-default)`)
- e.g. margin-bottom uses 7px, off the spacing scale (intended `margin-bottom: var(--spectrum-spacing-100)`)
- e.g. secondary text colored var(--spectrum-negative-content-color-default), which signals a status it doesn't have (intended `color: var(--spectrum-neutral-subdued-content-color-default)`)

## T5 False alarm: 3
The agent flags something the rules allow and often changes it, which breaks what was fine (shows up as regressions).
- e.g. flagged .confirm-label as R3: Missing explicit font-size declaration while using font-weight token, inconsistent with similar label elements like .auth-label
- e.g. flagged .step-text as R3: Missing explicit font-size declaration on body text paragraph, inconsistent with other body text elements like .danger-desc
- e.g. flagged .onboard-title as R1: Missing color declaration - text color must come from tokens

## T6 Overconfident report: 42
The report says everything is fixed when it isn't.

