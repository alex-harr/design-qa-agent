# Skill changelog

Each entry: version, the failure category it targeted, the change, the train result against the version it was built on, and the decision. Reverted versions stay in `skill/` for the record but are never built on.

## v000 (baseline)

- Written before any run. One paragraph: read the rules and the screen, fix violations with tokens and components, record each problem.

## v001 (revert)

- Built on: skill/v000 (train run `base-train-a,base-train-b`)
- Target: T1 Meaning not checked
- Change: Add a separate R7 meaning pass: list every element carrying a meaning color, button variant or Label variant, write what its visible text means, and check that against R7's mapping, changing only clear contradictions.
- Why it should generalize (proposer): It's a procedure keyed to RULES.md's meaning categories and component names, not to any screen's classes or values, so it applies to any element on any screen that pairs a status color with text.
- Risk (proposer): More false alarms (T5) from over-reading meaning, e.g. recoloring a correct Label or muting text that legitimately signals status; the pass also adds steps that could crowd out the token sweep (T3) on long screens.
- Train, 2 trials: strict passes 7.5 -> 16 (+8.5); net fixed 249 -> 276 (+27); keep rule: net fixed +48 or more and passes not lower

## v002 (revert)

- Built on: skill/v000 (train run `base-train-a,base-train-b`)
- Target: T2 Readability not checked
- Change: Add a short R5 check that goes through every text color declaration and compares the token's documented role from RULES.md with what the text does, with fixed mappings for disabled, onEmphasis and border/bg tokens used as text.
- Why it should generalize (proposer): The check is keyed to token roles that RULES.md itself defines (disabled controls only, onEmphasis only on emphasis backgrounds, fgColor tokens for text), so it applies to any `color:` declaration on any screen, with no screen-specific classes or values.
- Risk (proposer): The agent could over-apply it: muting text that sits on a real emphasis background, or touching a correctly disabled control (T5 regressions). It could also pick default where muted was meant (T4). The extra steps might also crowd out the raw-value sweep (T3).
- Train, 2 trials: strict passes 7.5 -> 9 (+1.5); net fixed 249 -> 256 (+7); keep rule: net fixed +48 or more and passes not lower

## v003 (revert)

- Built on: skill/v000 (train run `base-train-a,base-train-b`)
- Target: T6 Overconfident report
- Change: Before the report, add a required audit of the edited screen, one rule at a time (R1-R7), with one evidence line per rule. Only allow an all-fixed claim when every rule was actually checked, and otherwise name the unchecked or uncertain rules and lower confidence.
- Why it should generalize (proposer): It's a verification and calibration habit keyed to RULES.md's own rule IDs, with no screen, class or value references, so it works on any screen. It also gives the agent a second look at the rules it most often skips (R5, R7, raw values in layout CSS).
- Risk (proposer): The audit may push the agent to make new changes, so false flags and regressions (T5) could rise. Lower stated confidence could also cost points on runs that were actually clean. Longer runs could cut the sweep short on large screens.
- Train, 2 trials: strict passes 7.5 -> 11 (+3.5); net fixed 249 -> 265 (+16); keep rule: net fixed +48 or more and passes not lower

## v004 (revert)

- Built on: skill/v000 (train run `base-train-a,base-train-b`)
- Target: T4 Wrong fix
- Change: Expand step 3 with a short fix-value method: round raw numbers to the nearest scale token (checking vendor values when unlisted), map raw colors by role, replace hand-built lookalikes' inline styles entirely with component classes while keeping existing classes/attributes, and choose button/Label variant and size from what the element does and its siblings.
- Why it should generalize (proposer): It's a procedure keyed to RULES.md's own scales, tokens and component variants (nearest-step arithmetic, role-based token choice, full component replacement, sibling matching), so it applies to any off-scale value or rebuilt component on any screen without naming screen classes or values.
- Risk (proposer): Variant guidance may nudge the agent to re-style buttons that were already correct (more T5 regressions), and longer step 3 could slightly crowd out the sweep (T3); T1/T2 misses are not addressed, so passes may move little even if net fixed rises.
- Train, 2 trials: strict passes 7.5 -> 9 (+1.5); net fixed 249 -> 270 (+21); keep rule: net fixed +48 or more and passes not lower
- Screen, 1 trial: net fixed 138 vs baseline 124.5 per trial (passed to confirm)

## v005 (revert (screened out))

- Built on: skill/v000 (train run `base-train-a,base-train-b`)
- Target: T1 Meaning not checked
- Change: Add a markup-first walk: for every text element, button and .Label in the HTML body, name its role from its text and placement, then check its actual color token and button/Label variant against a role table taken from R5 and R7, fixing only clear contradictions.
- Why it should generalize (proposer): It starts from what each element is, not from a list of suspicious tokens, and the role-to-token table comes entirely from RULES.md. So it applies to any screen, and it catches valid-but-wrong tokens for both meaning (R7) and readability (R5) in the same pass.
- Risk (proposer): Assigning roles may cause more false flags (T5), such as recoloring a correct Label, adding colors to inherited text, or demoting a legitimately primary button. On long screens the walk may also crowd out the raw-value CSS sweep (T3). It also overlaps with the reverted v001 and v002 directions, so the gain may again fall short of the +48 keep bar.
- Screen, 1 trial: net fixed 113 vs baseline 124.5 per trial (screened out, not confirmed)

## v006 (revert)

- Built on: skill/v000 (train run `base-train-a,base-train-b`)
- Target: T1 Meaning not checked
- Change: Add a short check inside step 2: search the screen for the R7 meaning words (danger, success, attention, done, btn-primary), and for each hit read the element's visible text and keep it only if R7 allows that meaning, using one-line rules for buttons, Labels and plain text, plus a 'leave it if two readings fit' guard.
- Why it should generalize (proposer): It uses only RULES.md's own meaning vocabulary and component names as search terms, so it finds every meaning-bearing token or variant on any screen without a full inventory pass. The verdict comes from the element's own text, not from any screen's classes or values.
- Risk (proposer): This is the third T1 attempt (v001 and v005 were reverted); it differs by being a targeted search inside the existing sweep instead of a separate full walk, but the gain may still miss the +48 bar. False flags (T5) could rise if the agent over-reads Labels or recolors legitimate status text. The examples of destructive verbs could be over-matched, and the extra step could still slightly crowd out the raw-value sweep (T3).
- Train, 2 trials: strict passes 7.5 -> 12 (+4.5); net fixed 249 -> 262 (+13); keep rule: net fixed +48 or more and passes not lower
- Screen, 1 trial: net fixed 138 vs baseline 124.5 per trial (passed to confirm)
