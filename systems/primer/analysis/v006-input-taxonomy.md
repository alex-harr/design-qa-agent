# Failure taxonomy on base-train-a, base-train-b (104 runs)

Counts are planted problems not fixed (T1-T4), false flags (T5), and runs that claimed everything was fixed but failed (T6).

## T1 Meaning not checked: 66
A real token or class carries the wrong meaning and the agent never flags it: status color on plain secondary text, a destructive action in primary green, a safe action in danger red, a status pill showing the wrong status. These pass any token check; only reading what the element says catches them (R7).
- e.g. secondary text colored var(--fgColor-success), which signals a status it doesn't have (intended `color: var(--fgColor-muted)`)
- e.g. safe action "Mark all as read" styled as a danger button (intended `<button class="btn btn-sm" type="button" data-qa="notifications-btn-ma`)
- e.g. destructive action styled as the primary green button (intended `<button class="btn btn-sm btn-danger" type="button" data-qa="team-memb`)
- e.g. safe action "Download invoice" styled as a danger button (intended `<button class="btn" type="button" data-qa="billing-summary-btn-downloa`)

## T2 Readability not checked: 34
A real token makes text unreadable and the agent never flags it: the disabled color on body text, a border color used as text, white text on a light surface. Token names look fine; only checking contrast catches them (R5).
- e.g. text uses the disabled color and fails contrast (intended `color: var(--fgColor-default)`)
- e.g. text uses the disabled color and fails contrast (intended `color: var(--fgColor-muted)`)
- e.g. text color set to var(--fgColor-onEmphasis), a real token that fails contrast here (intended `color: var(--fgColor-muted)`)
- e.g. text color set to var(--fgColor-onEmphasis), a real token that fails contrast here (intended `color: var(--fgColor-accent)`)

## T3 Incomplete sweep: 23
A raw, off-scale value is left in place and never reported, usually in the page's own layout rules (container margins, gaps, weights) rather than in components (R1-R4).
- e.g. margin uses 25px, off the spacing scale (intended `margin: 0 auto var(--base-size-24)`)
- e.g. gap uses 13px, off the spacing scale (intended `gap: var(--base-size-12)`)
- e.g. margin uses 39px, off the spacing scale (intended `margin: var(--base-size-40) auto`)
- e.g. border width hard-coded instead of var(--borderWidth-thin) (intended `border: var(--borderWidth-thin) solid var(--borderColor-accent-muted)`)

## T4 Wrong fix: 36
The agent found the problem but fixed it to the wrong value or variant: an off-scale number rounded to the wrong step, a rebuilt component restored with the wrong variant or size.
- e.g. status pill rebuilt by hand instead of using .Label (Label Label--accent member-role) (intended `<span class="Label Label--accent member-role" data-qa="team-members-ro`)
- e.g. margin-right uses 9px, off the spacing scale (intended `margin-right: var(--base-size-8)`)
- e.g. font-size 24px instead of var(--text-title-size-medium) (intended `font-size: var(--text-title-size-medium)`)
- e.g. gap uses 11px, off the spacing scale (intended `gap: var(--base-size-12)`)

## T5 False alarm: 27
The agent flags something the rules allow and often changes it, which breaks what was fine (shows up as regressions).
- e.g. flagged .note-dot-read as R1: background: var(--bgColor-transparent) uses 'transparent' which is a named color, not a valid design system token
- e.g. flagged .note-dot-read as R1: Used invalid token var(--bgColor-transparent) not in design system
- e.g. flagged notifications-label-3 as R7: Label used Label--success class for 'Done' text, but done items should use the done (purple) color, not success
- e.g. flagged notifications-label-3 as R7: Used Label--success (green) for 'Done' status, but done colors (purple) should be used for triaged/merged/completed items

## T6 Overconfident report: 89
The report says everything is fixed when it isn't.
