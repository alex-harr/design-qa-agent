# Failure taxonomy on h55-heldout (54 runs)

Counts are planted problems not fixed (T1-T4), false flags (T5), and runs that claimed everything was fixed but failed (T6).

## T1 Meaning not checked: 1
A real token or class carries the wrong meaning and the agent never flags it: status color on plain secondary text, a destructive action in primary green, a safe action in danger red, a status pill showing the wrong status. These pass any token check; only reading what the element says catches them (R7).
- e.g. safe action "Upload" styled as a danger button (intended `<button class="spectrum-Button spectrum-Button--fill spectrum-Button--`)

## T2 Readability not checked: 0
A real token makes text unreadable and the agent never flags it: the disabled color on body text, a border color used as text, white text on a light surface. Token names look fine; only checking contrast catches them (R5).

## T3 Incomplete sweep: 1
A raw, off-scale value is left in place and never reported, usually in the page's own layout rules (container margins, gaps, weights) rather than in components (R1-R4).
- e.g. padding uses 17px, off the spacing scale (intended `padding: 0 var(--spectrum-spacing-300)`)

## T4 Wrong fix: 4
The agent found the problem but fixed it to the wrong value or variant: an off-scale number rounded to the wrong step, a rebuilt component restored with the wrong variant or size.
- e.g. status pill rebuilt by hand instead of using .spectrum-Badge (spectrum-Badge spectrum-Badge--accent) (intended `<div class="spectrum-Badge spectrum-Badge--accent" data-qa="pricing-ba`)
- e.g. background set to an off-palette hex near var(--spectrum-background-layer-2-color) (intended `background: var(--spectrum-background-layer-2-color)`)

## T5 False alarm: 13
The agent flags something the rules allow and often changes it, which breaks what was fine (shows up as regressions).
- e.g. flagged danger-zone-warning as R7: The Danger zone warning banner used the notice variant, but everything in a Danger zone should be negative.
- e.g. flagged danger-zone-warning as R7: The Danger zone banner warns that these actions can't be undone, but it used the notice (yellow warning) variant. R7 says negative color is 
- e.g. flagged danger-zone-warning as R7: Notice-colored InLineAlert used inside the Danger zone; everything in a Danger zone must be negative.
- e.g. flagged danger-zone-warning as R7: The warning banner in the Danger zone used the notice color; everything in a Danger zone must use negative.

## T6 Overconfident report: 18
The report says everything is fixed when it isn't.

