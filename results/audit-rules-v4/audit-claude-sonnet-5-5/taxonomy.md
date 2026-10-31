# Failure taxonomy on audit-claude-sonnet-5-5 (12 runs)

Counts are planted problems not fixed (T1-T4), false flags (T5), and runs that claimed everything was fixed but failed (T6).

## T1 Meaning not checked: 0
A real token or class carries the wrong meaning and the agent never flags it: status color on plain secondary text, a destructive action in primary green, a safe action in danger red, a status pill showing the wrong status. These pass any token check; only reading what the element says catches them (R7).

## T2 Readability not checked: 0
A real token makes text unreadable and the agent never flags it: the disabled color on body text, a border color used as text, white text on a light surface. Token names look fine; only checking contrast catches them (R5).

## T3 Incomplete sweep: 0
A raw, off-scale value is left in place and never reported, usually in the page's own layout rules (container margins, gaps, weights) rather than in components (R1-R4).

## T4 Wrong fix: 0
The agent found the problem but fixed it to the wrong value or variant: an off-scale number rounded to the wrong step, a rebuilt component restored with the wrong variant or size.

## T5 False alarm: 0
The agent flags something the rules allow and often changes it, which breaks what was fine (shows up as regressions).

## T6 Overconfident report: 0
The report says everything is fixed when it isn't.

