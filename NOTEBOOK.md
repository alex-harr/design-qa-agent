# Lab notebook: design-system QA agent on Primer

Evidence log for Stage 3. Every number here comes from a file under `runs/` or `tasks/`. Inferences are marked [INFERENCE].

## Setup (frozen before any agent run)

- [x] Design system: Primer primitives v11.10.0 + Primer CSS v22.3.3 (MIT), light theme, plus `lab-components.css` (Box, Label, flash, Progress, avatar, Dialog) written with tokens only.
- [x] 12 clean screens; 7 rules in `design-system/RULES.md`.
- [x] Ground truth by seeded mutation (seed 11): 40 tasks, 2–4 planted problems each, plus clean controls.
- [x] Split by base screen so no screen appears in both: train t01–t24 (screens 01–07, 3 clean controls), held-out t25–t40 (screens 08–12, 1 clean control). Every rule appears in both.
- [x] Agent sandbox: Claude Code headless, Read/Edit/Write/Glob/Grep only, no shell, reads blocked outside its folder; verified it cannot read `truth.json`.
- [x] Code grader (strict): every planted problem restored, no regressions, no lint or contrast failures left, zero false flags on clean controls.

## Pilots

- Pilot 1 found ambiguous numeric fixes (17px sits between two scale steps). Fixed by only planting off-scale values whose nearest scale step is the original. Tasks regenerated.
- Pilot 2: Sonnet 5.5, 4/4 tasks passed, about $0.05 per run.

## Probe: one pass over train with skill v000

| Agent | Strict pass | Detected | Fixed exactly | Says "all fixed" | Cost (24 runs) |
| --- | --- | --- | --- | --- | --- |
| Sonnet 5.5 | 23/24 (95.8%) | 100% | 98.4% | 100% | $1.27 |
| Haiku 5.5 | 17/24 (70.8%) | 98.4% | 90.2% | 100% | $0.13 |

Source: `runs/probe-sonnet`, `runs/probe-haiku`, `lab/report.py`.

### Error analysis round 0: most "failures" were my rules, not the agent

Read every failing run. Of the 8 failing runs (1 Sonnet, 7 Haiku), these traced to rules that two reasonable reviewers could read differently:

- [x] "Done" status pill: both models swapped `Label--danger` to `Label--done` (purple) instead of the intended `Label--success`. The rules listed a `--done` variant but never said what it means. (Sonnet t08, Haiku t07, t08)
- [x] Closed-issue count colored green: Haiku changed it to the `done` color, not muted. Same gap. (Haiku t23)
- [x] Custom cards: Haiku converted `.auth-card` to `.Box` because R6 said "containers are `.Box`. Never hand-build a lookalike." My own clean screen broke my own rule as written. (Haiku t04, t06)
- [x] "Change visibility" in the Danger zone: Haiku removed `.btn-danger` because R7 said danger is only for destructive actions. Defensible reading. (Haiku t18, t20)

Fix: tightened R6 (which components are mandatory; custom surfaces with tokens are fine) and R7 (what danger, success, attention, done and muted each mean). Screens and tasks unchanged.

Real agent errors in round 0: Haiku fixed an 8px "Forgot password?" link to 14px instead of 12px, the nearest step (t06; a judge call, since 14px is also on the scale), and missed a status color on secondary text (t18).

Self-grading: both models said "all fixed" on 100% of runs. Haiku was right 71% of the time. [INFERENCE] This already matches Anthropic's harness-design finding that agents grade their own work too generously; the full baseline will measure it properly.

Clean-screen audit after the fix: all 12 clean screens run as inputs. Opus 5.5 flagged nothing (12/12). Haiku flagged one thing twice: the red "bug" label (R7 didn't say bugs count as failures). Added "bug reports" to R7. Source: `runs/v1/audit-*`.

Probe 2, Haiku on train with the clarified rules, 3 trials: 69/72 strict passes (95.8%), pass^3 91.7%, 0 false flags, 0 regressions. Source: `runs/v1/probe2-haiku`.

**Finding: clarifying two rules moved the small model from 71% to 96% on the same tasks.** Most of the gap was the spec, not the model. [INFERENCE: probe 1 was 1 trial, probe 2 was 3, so the exact size is noisy; the direction is not.]

Consequence: the v1 tasks are too easy to show any skill improvement (3 failing runs out of 72). Moved v1 to `tasks-v1/` and built v2 with the same seed and screens:

- [x] 4–6 planted problems per task instead of 2–4, up to 2 per rule.
- [x] New problem types a token linter can't see: a real token that fails contrast (`--borderColor-default` or `--fgColor-onEmphasis` as text), a safe button styled as danger, any status pill swapped to the wrong status.
- [x] New subtle ones a linter can see: raw border width inside a `border` shorthand, raw font weight.
- [x] Validated: every planted problem visible to a grader, no stray changes, clean controls clean (0 problems). Grader fairness: clean screen passes and untouched input fails on all 40 tasks.

v2: train 106 planted problems over 24 tasks, held-out 79 over 16.

## Protocol (written before any v2 run)

- Agent: Haiku 5.5, skill in the system prompt, 40 turns max. Reference ceiling: Sonnet 5.5 with the same skill.
- Primary result: strict pass rate on held-out, 3 trials per task (48 runs), skill v000 vs the final skill.
- Secondary: pass^3, judge-accepted pass rate, share of problems fixed, false flags, regressions, self-assessment vs reality.
- Noise floor: two independent v000 train runs (A and B, 3 trials each). Noise = the gap in strict passes between them.
- Keep a skill edit only if, on train with 3 trials, it beats the current skill by at least max(3, noise + 2) strict passes and no task drops by 2 or more of its 3 trials. Otherwise revert.
- At most 6 edits. Proposer: Opus 5.5, one focused edit per round, sees train failures only, guarded against leaking element ids, screen class names, task ids or hex values.
- Held-out is run at baseline and once at the end, after Alex approves the final skill. Its transcripts are not read before the final run.

## v2 baseline, first attempt: the split was lopsided

| Split | Strict pass | pass^3 | Failing tasks |
| --- | --- | --- | --- |
| Train (screens 01–07) | 72/72 (100%) | 100% | none |
| Held-out (screens 08–12) | 34/48 (70.8%) | 62.5% | 6 of 16 |

Source: `runs/v2/base-train-a`, `runs/v2/base-heldout`. Train gives the improvement loop nothing to learn from. Screen complexity (elements, CSS rules, buttons) is similar across the two halves. Held-out transcripts stay unread.

Validity check: Opus 5.5 and Sonnet 5.5, once each on all 40 tasks: both 37/40, and both failed the same three held-out tasks Haiku failed most (t27, t35, t40). Every model failing the same task points at the task. Checked those three truth files against Opus's output:

- [x] Generator bug: the hand-built lookalike of a `.btn-invisible` button was given a 1px border, so it looked like a regular outlined button and the intended fix (`.btn-invisible`) couldn't be inferred from the input. (t35, t40)
- [x] Ambiguous fix: a profile bio set to the disabled color. Every model restored it as muted (secondary) text; the design had it as default text. Both fix R5, and the rules don't say which a bio is. (t27)

Fixes for v3: lookalikes keep the real border width; for contrast problems on text, either text token (default or muted) counts as a correct fix in the code grader.

## v3: long pages, interleaved split

- [x] Each task is one long page built from three screens (about 140 lines), 6–9 planted problems, up to 2 per rule.
- [x] Split by screen number parity: odd screens train, even screens held-out. Decided by rule, not by results, before any skill tuning.
- [x] 26 train tasks (2 clean), 18 held-out (2 clean). 174 and 122 planted problems.
- [x] Validated: 0 task problems; grader fairness holds on all 44 (clean passes, untouched input fails). Tested the "either text color" rule on a real task: muted passes, accent fails.

Results on v3 with skill v000:

| Agent | Split | Strict pass | Problems fixed | Says "all fixed" |
| --- | --- | --- | --- | --- |
| Haiku 5.5, 3 trials | train | 75/78 (96.2%) | 99.6% | 100% |
| Sonnet 5.5, 1 trial | all 44 | 42/44 (95.5%) | 99.3% | |
| Haiku 4.5, 1 trial | train | 2/26 (7.7%) | 75.9% | 100% |

Source: `runs/v3-haiku55/`, `runs/probe-h45`.

**Finding: token-level design-system QA is solved for current models.** Even the small current model fixes 99.6% of planted problems on long pages with a one-paragraph skill. I also tried six-screen pages (about 240 lines, 11–14 problems): Haiku 5.5 still passed 8 of 10. [Source: scratch probe, not kept.]

Decision: the agent under test is **Haiku 4.5**, the previous-generation small model. It fails this benchmark (8% strict, 76% of problems fixed, misses most color-meaning problems, flags things that aren't wrong), so a skill change has room to show up. Haiku 5.5 and Sonnet 5.5 are the ceiling. The question becomes: how much of a model generation's gain can a better skill buy back? Regression check at the end: does the tuned skill hurt Haiku 5.5?

Cost note: Haiku 4.5 runs cost about $0.11 each here (more than Haiku 5.5 at about $0.01).

### First Haiku 4.5 baseline surfaced two more spec gaps

Error analysis of the first train baseline (52 runs, 4 strict passes) found false alarms that were the spec's fault, not only the agent's:

- [x] 14 false flags called `--bgColor-transparent` "not a valid token". It is a real Primer token, used by a clean screen, but the token list in RULES.md read as exhaustive.
- [x] 4 false flags called `max-width: 640px` a spacing violation. The intro said "a screen's own CSS may only combine tokens and components," which the clean screens themselves break.

Fixed both in RULES.md (R1–R4 cover color, spacing, type and shape; layout values like widths are free; any token defined in `vendor/` is valid). The other false flags stay as agent errors: calling a `.btn` on an `<a>` a lookalike, demanding explicit colors on headings, and switching the "Done" pill to purple when R7 says purple is only for triaged or merged items. Also fixed a grader bug: a finding about `.note-dot` counted as detecting a problem on `.note` (selector matched as a substring). Detection numbers only; pass/fail unchanged.

The pre-fix baselines are kept in `runs/v3-h45-rules-a/` (train 4/52 strict; held-out 13/54) and re-run on the fixed rules. RULES.md is frozen from here.

### Haiku 4.5 baseline on the frozen rules (skill v000)

| Run | Strict pass | Net fixed | Fixed | Detected | False flags / run | Says "all fixed" |
| --- | --- | --- | --- | --- | --- | --- |
| Train A, 2 trials | 5/52 (9.6%) | 237/348 | 74.4% | 80.2% | 0.27 | 100% |
| Train B, 2 trials | 10/52 (19.2%) | 261/348 | 79.9% | 84.2% | 0.25 | 100% |
| Held-out, 3 trials | 12/54 (22.2%) | 273/366 | 75.7% | 80.1% | 0.02 | 100% |

Noise floor (A vs B, same skill, same tasks): 5 strict passes, 24 net fixed. Keep threshold = max(10, 2 × 24) = **48 net fixed**, and strict passes not lower. Each candidate is compared to the average of A and B. [INFERENCE] A 24-point swing between identical runs is why single-run comparisons can't be trusted here.

## Protocol v3 (replaces the v2 protocol above; written before any Haiku 4.5 baseline)

- Agent: Haiku 4.5, skill in the system prompt, 40 turns max.
- Co-primary results on held-out (3 trials, 54 runs), v000 vs final skill: strict pass rate, and net problems fixed (problems fixed minus regressions minus false flags) out of 366.
- Secondary: pass^3, judge-accepted pass rate, detection rate, false flags, regressions, self-assessment vs reality, cost per run.
- Train evaluation: 2 trials (52 runs). Noise floor: two independent v000 train runs, A and B. Noise = the gap in net fixed between them.
- Keep a skill edit only if, on train, net fixed beats the current skill by at least max(10, 2 × noise) and strict passes don't drop. Otherwise revert.
- At most 6 edits. Proposer: Opus 5.5, one focused edit per round, sees train failures only, guarded against leaking element ids, screen class names, task ids or hex values.
- Held-out runs at baseline and once at the end, after Alex approves the final skill. Its transcripts stay unread until then.

## Improvement loop

### Round 1: v001, reverted (near miss)

- Proposer's target: T1 Meaning not checked. Change: a separate color-meaning pass that lists every element carrying a status color, button variant or pill variant and checks its text against R7.
- Train, 2 trials, vs the average of baseline A and B: strict passes 7.5 → 16; net fixed 249 → 276 (+27). Below the +48 keep bar, so reverted per protocol.
- Per 52 runs, the edit did what it targeted: meaning misses 33 → 13, readability misses 17 → 6, wrong fixes 18 → 11. But incomplete-sweep misses rose 11.5 → 19. The proposer predicted that exact risk ("the pass could crowd out the token sweep on long screens"). [INFERENCE] Attention is a budget: adding a check costs coverage elsewhere.

### Round 2: v002, reverted

- Target: T2 Readability not checked. Change: a text-color role check (disabled only on disabled controls, white-on-emphasis only on emphasis fills, no border or background tokens as text color).
- Train: strict passes 7.5 → 9; net fixed 249 → 256 (+7). Reverted.
- Readability misses went from 17 per 52 runs to 0. The check worked completely. But wrong fixes rose 18 → 26 and sweep misses 11.5 → 21, so the net barely moved.
- Pattern after two rounds: each added check fixes its target and costs coverage somewhere else.

## Judge calibration (20 blind cases from train baseline A, labeled by Alex)

| Question | Agreement | Cohen's kappa | Human "pass" | Judge "pass" |
| --- | --- | --- | --- | --- |
| Would you ship it? (J1) | 15/20 (75%) | 0.52 | 11 | 6 |
| Is the report accurate? (J2) | 20/20 (100%) | 1.00 | 4 | 4 |
| Ship it, human vs strict code grader | 12/20 (60%) | 0.25 | 11 | 3 |

- All 5 J1 disagreements go one way: Alex shipped, the judge didn't. In every one, a planted problem was really still there and subtle: a closed-issue count left red or green instead of muted (2), a 17px margin, an invisible hard-coded weight, an 11px gap fixed to 8 instead of 12. The judge applies the rules; Alex applies "would a user notice."
- J2 agreement is inflated. [INFERENCE] Mid-labeling the page gained a three-line report checklist computed from the same facts the judge sees, so Alex's J2 labels and the judge's share a source. Treat J2 as a sanity check, not independent validation.
- Takeaway: the judge sits between the strict code grader and a designer's eye. Use it as "follows the rules," not as "a designer would ship it."
- Source: `lab/calibration/` (cases_key.json, human/labels, judge.json in each run).

### Round 3: v003, reverted

- Target: T6 Overconfident report. Change: before reporting, re-audit the edited screen rule by rule with one line of evidence per rule; only claim "all fixed" if every rule was checked.
- Train: strict passes 7.5 → 11; net fixed 249 → 265 (+16). Reverted.
- Sweep misses dropped 11.5 → 6 and meaning misses 33 → 26, but the agent still claimed "all fixed" on 41 of 52 runs while passing 11. A self-audit step didn't fix overconfidence. [INFERENCE] Consistent with the harness-design finding that agents grade their own work too generously; asking the same agent to check harder doesn't create an independent check.

Paused after round 3 at Alex's request (usage). Rounds 4–6 not started.

### Protocol amendment before round 4 (cost)

Alex asked to cut usage. Rounds 4–6 use screen-then-confirm: each candidate first runs 1 trial on train (26 runs); if its net fixed is below the baseline's per-trial average, it is reverted without a second trial. Otherwise it gets the second trial and faces the unchanged keep rule (+48 net fixed over the average of baseline A and B, strict passes not lower). The keep bar is not changed. No retest of earlier near misses, to avoid re-running until something passes.

### Rounds 4–6 (screen-then-confirm)

| Round | Target | Change | Screen (1 trial, net fixed vs 124.5) | Train net fixed vs 249 | Passes vs 7.5 | Decision |
| --- | --- | --- | --- | --- | --- | --- |
| v004 | T4 Wrong fix | A fix-value method: round to the nearest scale step, map raw colors by role, swap lookalikes for the real component, pick variants from siblings | 138 | 270 (+21) | 9 | revert |
| v005 | T1 Meaning | A markup-first walk with a role table for every text element, button and pill | 113 | not run | | revert (screened out) |
| v006 | T1 Meaning | Search for meaning words, check each hit's text, "leave it if two readings fit" | 138 | 262 (+13) | 12 | revert |

- v004 did what it targeted: wrong fixes 18 → 10 per 52 runs.
- v005 raised false alarms (13.5 → 20 per 26 runs) and was cut at the screen.
- The proposer never tried the restructure (one combined sweep); it kept adding passes.

## Loop result: no kept edit in 6 rounds

- Every confirmed candidate (5 of 5) scored above the baseline average on net fixed: +27, +7, +16, +21, +13. None reached the +48 keep bar. Against baseline B alone (261), the same five are +15, −5, +4, +9, +1, so they're within noise of the better baseline run. [INFERENCE] The edits probably help a little; this design can't prove it.
- Each edit fixed its own target (meaning misses 33 → 13, readability 17 → 0, wrong fixes 18 → 10) and lost ground elsewhere. Attention is a budget.
- Overconfidence never moved: in every version, 69–83% of runs claimed "all fixed" and failed (36–43 of 52), while only 17–31% passed.
- Final skill = v000. The pre-registered held-out final is moot (no new skill to test).

---

# Stage 4: transfer to a second design system (Spectrum)

Started 2026-10-29. Question: does the Stage 3 agent (skill v000, Haiku 4.5) carry over to a different design system without retuning, and what has to change? Every number below comes from a file under `systems/*/runs/` or `systems/*/tasks/`.

## Decisions

- [x] Second system: **Adobe Spectrum CSS (Spectrum 2), Apache-2.0**, picked by Alex. It has CSS custom properties for every R1–R4 family, so the rules keep Primer's exact R1–R7 shape. Carbon (no radius or border-width tokens) and GOV.UK Frontend (spacing/type/shape Sass-only) were checked and passed over.
- [x] Order change, approved by Alex: generalize the harness first (handoff step 6), so Spectrum plugs in through the same config any designer would fill in.
- [x] Alex auto-approved the Spectrum `RULES.md` (no review gate before runs). It is frozen as committed; citations are in `systems/spectrum/design-system/RULES-SOURCES.md`.

## Harness generalization

- [x] Everything design-system-specific moved into `systems/<name>/design-system/ds.json`: token-family patterns, scales, which files hold the light theme's tokens, component class names, the text/disabled/status tokens the generator uses, and what the agent gets a copy of. `lab/system.py` loads it; `DQA_SYSTEM=<name>` or `DQA_SYSTEM_DIR=<folder>` picks the system.
- [x] Layout: `systems/primer/` and `systems/spectrum/` each hold `design-system/`, `screens/`, `tasks/`, `splits.json`, `runs/`, `analysis/`. `skill/` is shared.
- [x] `skill/v000` needed no change: it never named Primer. All the coupling was in the harness.
- [x] Regression: Primer's 44 tasks rebuilt from the config are **byte-identical** to the Stage 3 kit (132 files plus `splits.json`), before and after every harness change below. Primer validators: 0 screen problems, 0 task problems; grader fairness holds (clean passes, untouched input fails).
- [x] Isolation re-verified after the permission change (the agent is now denied both the lab and the system folder): Read on a `truth.json`, Read on `splits.json` and Glob on `tasks/` all came back "denied by your permission settings".

### Latent Stage 3 bug found during the refactor

- [x] The Stage 3 token resolver read every file in `vendor/`, including the 1 MB Primer component bundle, which redefines **266** generator-relevant tokens (`--bgColor-*`, `--fgColor-*` and others) for dark and high-contrast themes. It kept the first definition it saw, in filesystem listing order. On this machine `theme-light.css` happened to list before `primer-components.css`, so Stage 3's raw-color ground truth is correct. On a filesystem that lists alphabetically, the bundle wins and the planted hex values would be wrong. Its regex also ran values across `}` in minified CSS.
- [x] Fix: `ds.json` names the token files in order (the component bundle is left out), and a block-aware parser can restrict tokens to theme selectors (`.spectrum`, `.spectrum--light`, `.spectrum--medium`) with cascade order. Stage 3's numbers are unaffected (tasks are byte-identical).

### Scales derived automatically

- [x] With `"auto"`, scales come from the tokens themselves. For Primer, auto spacing matches Stage 3's hand-typed list exactly; auto type adds 13px and 40px (real code and display tokens the hand list skipped); auto radius picks up the 9999px "full" radius, now filtered out.

## Spectrum setup

- [x] Vendored as data from npm (`npm pack --ignore-scripts`, nothing run): `@spectrum-css/tokens` 16.0.2 light and medium files, 12 component packages, Apache-2.0 license, versions in `vendor/PROVENANCE.md`. The agent gets the token files (about 140 KB, vs about 134 KB for Primer) and stubs for component CSS, as in Stage 3.
- [x] Font: Spectrum's font token is `adobe clean`, which Adobe restricts to its own products. `lab-components.css` adds a system fallback; no Spectrum color, spacing, type-size or shape token is redefined.
- [x] 12 clean screens, one per Primer screen, same content and surfaces. Mapped: Box → token-styled panels, Label → Badge, flash → In-line alert, form-control → Textfield, Counter → subdued text, Dialog → token-styled panel, Progress → ProgressBar, avatar → placeholder circle. `validate_screens`: 0 problems.

### What Spectrum's own design made hard (findings for the write-up)

- [x] **Spectrum's notice Badge fails WCAG AA.** It is white text on `#fc7d00`: 2.6:1, against the 4.5:1 Spectrum's own text-field accessibility page requires. Our R5 flagged it in the clean screen. The "pending invite" label became a notice StatusLight, which Spectrum's docs list for "pending" anyway, and notice is left out of the badge-swap mutations.
- [x] **`--spectrum-corner-radius-full` is a unitless `0.5`**, a multiplier for `calc()`. Used as `border-radius` it is invalid, and the corner renders square. Found in our own screenshots; R4 now warns about it.
- [x] **No positive, notice or informative text colors.** Spectrum 2 has content colors only for neutral, subdued, accent, negative and disabled. Its "visual" colors are about 3.9:1 on white: fine for dots and icons (3:1), not for body text.
- [x] **Token numbers aren't sizes.** `spacing-100` is 8px; `corner-radius-200` is 10px but `-300` is 6px.
- [x] **Docs vs package drift.** Adobe's design-data site lists `spacing-85` (6px) and `spacing-350` (20px) and different small radii; the 16.0.2 npm package has neither. `RULES.md` lists only what the vendored package defines.
- [x] Badge meanings follow Spectrum's docs ("new" is accent, "in progress" is informative, roles are neutral), so the rules and screens don't disagree.

### Answer-key bug caught before any run

- [x] First Spectrum build: 25 of 44 tasks failed validation with "unexpected style changes". Rebuilding a Spectrum button or badge by hand also changes its inner `-label` element, which has its own `data-qa`. Primer's components have no tagged children, so Stage 3 never hit this. Fix: a markup problem's target includes the component's tagged children. Primer tasks are still byte-identical; Spectrum validation: **0 problems in 44 tasks**; grader fairness holds on all 44.

### Planted-problem mix

| | Tasks | Planted (train / held-out) | R1 | R2 | R3 | R4 | R5 | R6 | R7 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Primer | 44 | 174 / 122 | 64 | 59 | 43 | 9 | 52 | 29 | 40 |
| Spectrum | 44 | 181 / 122 | 69 | 57 | 25 | 35 | 48 | 30 | 39 |

- [x] Same generator, seed (11), page builder and split rule. The mix shifts on R3 and R4: Spectrum's type scale is dense (11, 12, 14, 16, 18, 20, 22, 25 …), so almost no off-scale font size has a single nearest step, and only 2 off-type problems could be planted (Primer: 24). Border-width and radius problems rise instead. [INFERENCE] Per-rule fix rates are the fair comparison; totals carry this mix difference.

## Transfer protocol (written before any Spectrum baseline run)

- Agent: Haiku 4.5, `skill/v000` unchanged, same harness prompt, 40 turns max, same isolation. The only inputs that change are the screen and the design-system folder.
- Runs, mirroring Stage 3 protocol v3: train A (2 trials, 52 runs), train B (2 trials, 52 runs), held-out (3 trials, 54 runs).
- Noise floor: |A − B| in net fixed, as in Stage 3.
- Primary comparison with Primer (same metric definitions, `lab/report.py`): strict pass rate, net fixed as a share of planted problems, fixed %, detected %, false flags per run, "says all fixed".
- Failure mix: `lab/taxonomy.py` T1–T6 on train A+B, compared with Stage 3's v001-input taxonomy (also train A+B, 104 runs).
- Mix caveat stated in advance: Spectrum has fewer R3 and more R4 problems (table above); per-rule detected/fixed is reported for Spectrum, but Stage 3 didn't keep per-rule numbers for its baseline, so the cross-system comparison is on totals and failure types.
- Reading transfer: "carries over" means Spectrum's train net-fixed share lands within the Primer noise band (Primer A and B: 68.1% and 75.0% of 348); clearly below means the agent lost ground on the new system. [INFERENCE] One system is one data point, so this is a transfer check, not a general claim.
- Optional loop rounds: not planned. Decide after the baseline, with Alex.

## Answer-key probe: Sonnet 5.5, one pass over all 44 Spectrum tasks

| Run | Strict pass | Detected | Fixed | False flags | Cost |
| --- | --- | --- | --- | --- | --- |
| Spectrum, first build | 32/44 (72.7%) | 303/303 (100%) | 290/303 (95.7%) | 0 | $4.43 |
| Primer, Stage 3 (for reference) | 42/44 (95.5%) | | 99.3% | | |

Source: `systems/spectrum/runs/probe-sonnet55-v1` (graded against the first task build), numbers from `lab/report.py`. Every model failing the same thing points at the task, so each miss was checked against its truth file:

- [x] **Answer-key bug: "Review" badge.** An informative badge reading "Review" next to "Ana requested your review" can be read as pending (notice). Sonnet chose notice once and neutral once. Changed to "Staging deploy is live" / "Live", Spectrum's own informative example word.
- [x] **Answer-key bug: hidden badge size.** In Spectrum the badge's text size lives on its inner label, so a hand-built lookalike copies the outer element's 16px and the original `--sizeS` can't be inferred. Screens now use the default badge size.
- [x] Shared ambiguity kept: "Cancel invite" as a negative button (Sonnet called it safe once). Primer had the same button and wording, so both systems carry it.
- [x] **Agent errors, kept (answer key unambiguous):** 8 spacing and radius problems restored to a real token that isn't the nearest one (37px → `spacing-500` 32px instead of `spacing-600` 40px; 7px → `spacing-75` 4px instead of 8px; 12px radius → 8px instead of 10px). `RULES.md` lists every token's px size, so the nearest step is knowable. [INFERENCE] Primer's spacing tokens are named by their px size (`--base-size-8`), which makes nearest-step trivial; Spectrum's aren't (`--spectrum-spacing-100` is 8px). This is the clearest early transfer cost, and it hits even the strong model.
- [x] One agent judgment error kept: a near-white card background restored to layer-1 gray instead of white.
- [x] After the two fixes, all 44 tasks rebuilt with identical planted-problem lists; validation 0 problems. Re-probe of the 12 badge tasks (`runs/probe-sonnet55-badges`): 9/12 pass, all badge problems fixed; the 3 misses are the same 32px/40px rounding error.

## Transfer result: train (skill v000, Haiku 4.5, zero retuning)

| Run | Strict pass | Net fixed | Fixed | Detected | False flags / run | Says "all fixed" | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Spectrum train A, 2 trials | 9/52 (17.3%) | 260/362 (71.8%) | 73.8% | 79.6% | 0.13 | 100% | $5.18 |
| Spectrum train B, 2 trials | 7/52 (13.5%) | 263/362 (72.7%) | 74.0% | 78.7% | 0.10 | 100% | $5.48 |
| Primer train A (Stage 3) | 5/52 (9.6%) | 237/348 (68.1%) | 74.4% | 80.2% | 0.27 | 100% | |
| Primer train B (Stage 3) | 10/52 (19.2%) | 261/348 (75.0%) | 79.9% | 84.2% | 0.25 | 100% | |

Source: `systems/spectrum/runs/base-train-{a,b}`, `lab/report.py`; Primer rows from the Stage 3 table above.

- [x] **It carries over.** Averaged, Spectrum is 72.2% net fixed and 15.4% strict pass (16/104); Primer was 71.6% and 14.4% (15/104). Spectrum's train runs land inside Primer's A–B band, which is the pre-registered test.
- [x] Spectrum's noise floor is 3 net fixed (A vs B), against Primer's 24. [INFERENCE] Probably luck of two samples rather than a property of Spectrum; it doesn't change the reading.
- [x] False flags fell from about 0.26 to 0.12 per run, regressions stayed at 0, and the agent still said "all fixed" on every run.

### Failure mix, train A+B (104 runs each, `lab/taxonomy.py`)

| Failure | Primer | Spectrum | Opportunities per 104 runs (Primer / Spectrum) |
| --- | --- | --- | --- |
| T1 Meaning not checked (R7) | 66 | 68 | 96 / 92 |
| T2 Readability not checked (R5) | 34 | 44 | 100 / 104 |
| T3 Incomplete sweep (R1–R4) | 23 | 39 | 500 / 528 (all token and component problems) |
| T4 Wrong fix | 36 | 38 | |
| T5 False alarm | 27 | 12 | |
| T6 Overconfident report | 89 | 88 | 104 / 104 |

Source: `systems/spectrum/analysis/base-train-ab-taxonomy.md`, `systems/primer/analysis/v001-input-taxonomy.md`.

### Where Spectrum cost ground (Spectrum train A+B, by problem type)

| Problem | n | Detected | Fixed |
| --- | --- | --- | --- |
| R1 raw / near color | 172 | 100% | 94% |
| R2 off-scale spacing | 136 | 82% | 68% |
| R3 raw font weight | 52 | 90% | 90% |
| R4 off-scale radius | 40 | 85% | 78% |
| R4 raw border width | 44 | 93% | 93% |
| R5 disabled color on text | 68 | 49% | 49% |
| R5 real token that fails contrast | 36 | 75% | 75% |
| R6 hand-built button / badge | 84 | 99% | 93% |
| R7 status color on secondary text | 44 | 16% | 14% |
| R7 destructive action in accent | 16 | 19% | 19% |
| R7 badge with the wrong meaning | 20 | 40% | 40% |
| R7 safe action styled negative | 12 | 50% | 50% |

- [x] **Spacing is the naming cost.** 82% of off-scale spacing was found but only 68% was put back on the right step; the other 14 points were real tokens one step off, the same error Sonnet made in the probe. Primer's spacing tokens carry their px size in the name; Spectrum's don't.
- [x] **The old blind spots came along unchanged.** Color meaning (T1) and readability (T2) were the two biggest failure types on Primer and still are. Disabled-color text was caught 49% of the time. [INFERENCE] `--spectrum-disabled-content-color` reads like a legitimate text token, which may be why T2 rose (34 → 44).
- [x] **Sweep misses rose (23 → 39)** with more raw values to find on Spectrum's longer token names and the larger R4 share. [INFERENCE] Not separable from the mix shift with this design.
- [x] **Fewer false alarms (27 → 12).** [INFERENCE] The Spectrum rules list every valid family up front (including grays for borders), which leaves less to second-guess. Stage 3's first false-alarm wave came from a token list that read as exhaustive.

## Transfer result: held-out (3 trials)

| Run | Strict pass | Net fixed | Fixed | Detected | False flags / run | Regressions / run | Says "all fixed" | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Spectrum held-out | 6/54 (11.1%) | 246/366 (67.2%) | 69.7% | 75.7% | 0.13 | 0.04 | 100% | $5.77 |
| Primer held-out (Stage 3) | 12/54 (22.2%) | 273/366 (74.6%) | 75.7% | 80.1% | 0.02 | | 100% | |

Source: `systems/spectrum/runs/base-heldout`, `lab/report.py`, `systems/spectrum/analysis/base-heldout-taxonomy.md`.

- [x] **Held-out lost ground: 27 net fixed (7.4 points) and half the strict passes.** That is just above Primer's train noise floor (24) and under the 48-point bar Stage 3 used to call a change real. 4 of the 6 Spectrum passes are clean controls. There is no held-out noise floor for either system (one 3-trial set each), so treat this as a probable, modest loss, not a measured one.
- [x] **Not the mix.** Spectrum's held-out set has fewer readability problems than Primer's (22 vs 27 per trial set) and the same number of meaning problems (16), the two categories the agent is worst at.
- [x] **Where it went: plausible-but-wrong tokens.** Held-out fixes that were found but restored wrong: white card backgrounds (`background-layer-2`) put back as `layer-1` gray or as `negative-subtle` pink inside the Danger zone, a `gray-200` border put back as `layer-1`, spacing one step off (8px ↔ 4px, 24px → 16px). Detected vs fixed: near-off colors 100% vs 81%, spacing 84% vs 75%, safe action styled negative 46% vs 33%. [INFERENCE] Spectrum has several tokens that resolve to the same or nearly the same value under different names (base, layer-1, layer-2, gray-25, white), and names that aren't sizes. The agent finds the problem and then picks a sensible-sounding token that isn't the original.

## Stage 4 verdict

- [x] **The agent transfers without retuning.** On train, Spectrum matches Primer within noise on every headline metric (72.2% vs 71.6% net fixed; 15.4% vs 14.4% strict pass). On held-out it trails by 7.4 points, mostly in fix precision, not in finding problems.
- [x] **What had to change was the harness, not the skill.** The four-line skill never named Primer; every Primer assumption lived in the bench (token patterns, scales, component names, file order). One `ds.json` per system now holds all of it, and Primer still rebuilds byte-identical.
- [x] **What costs ground is the design system's own naming.** Token names that aren't sizes and several tokens with the same value made the agent (and Sonnet 5.5) put a problem back on the wrong real token. [INFERENCE] For a designer adopting this, the rules doc should state each token's value and say which of several equal-valued tokens to use where, the same way Stage 3 found the rules doc was the main lever.
- [x] **The blind spots and the overconfidence travel unchanged.** Meaning (R7) and readability (R5) remain the biggest misses; the agent said "all fixed" on 100% of Spectrum runs while passing 13.9% (22/158).
- [x] Spend: Haiku baseline $16.43 (158 runs), Sonnet probes $5.58 (56 runs), smoke and isolation tests about $0.13.
- [ ] Optional loop rounds on Spectrum: not run.

## Attribution test: was it the agent or the Spectrum rules? (designed 2026-10-29, before these runs)

Question from Alex: is the held-out loss on Spectrum the agent's fault or the rules doc's? Two factors, crossed:

| | Rules v1 (as tested) | Rules v2 (values + look-alike tokens documented) |
| --- | --- | --- |
| Haiku 4.5 (agent under test) | done above | run |
| Haiku 5.5 (current small model) | run | run |

- [x] v2 changes one thing: a "Fixing a value" section (closest value wins; names aren't sizes), hex values for text, background and border tokens, Spectrum's equal-value token groups, and which background layer and border gray to use by role. R1–R7 wording is identical. 742 → 967 words. Folder: `systems/spectrum-v2/` (same screens, tasks and splits).
- [x] **Contamination note:** v2 was written after reading held-out failures (near-white cards restored as gray). Held-out is not blind for v2, so the **train** comparison is the clean test; held-out is reported with that caveat.
- [x] Same protocol per cell: train 2 trials (52 runs), held-out 3 trials (54 runs).
- [x] Reading: if v2 lifts Haiku 4.5 by more than the noise floor (Primer's 24 net fixed on train), the rules doc was at fault. If Haiku 5.5 on v1 is near ceiling, the old agent's capacity was too. Both can be true; the 2×2 sizes each.

### Run-to-run consistency (Spectrum train A+B, 4 runs per task, Haiku 4.5, rules v1)

| Rule | Problems | Fixed in all 4 runs | Fixed in some | Never fixed |
| --- | --- | --- | --- | --- |
| All | 181 | 54% | 36% | 9% |
| R1 color tokens | 43 | 91% | 9% | 0% |
| R2 spacing | 34 | 29% | 68% | 3% |
| R3 type | 13 | 85% | 15% | 0% |
| R4 shape | 21 | 67% | 29% | 5% |
| R5 readability | 26 | 19% | 69% | 12% |
| R6 components | 21 | 81% | 19% | 0% |
| R7 meaning | 23 | 9% | 39% | 52% |

- [x] Pages: no train page passed all 4 runs; 18 of 26 never passed; 3 passed once, 2 twice, 3 three times. Source: `systems/spectrum/runs/base-train-{a,b}` grade files.
- [x] [INFERENCE] For a designer this is the reliability picture: raw colors and hand-built components are dependable, spacing and readability are coin flips from run to run, and color meaning mostly isn't checked at all.

### Cell result: Haiku 5.5, rules v1

| Run | Strict pass | Net fixed | Fixed | Detected | False flags / run | Regressions / run | Cost |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Train, 2 trials | 38/52 (73.1%) | 348/362 (96.1%) | 96.1% | 99.2% | 0 | 0 | $0.43 |
| Held-out, 3 trials | 36/54 (66.7%) | 334/366 (91.3%) | 98.4% | 99.5% | 0.24 | 0.24 | $0.43 |

Source: `systems/spectrum/runs/h55-{train,heldout}`. For reference, Haiku 5.5 on Primer train (Stage 3, 3 trials): 75/78 strict pass, 99.6% fixed.

- [x] The current model gets Spectrum's spacing right with the v1 rules (68/68 train, 68/69 held-out). The naming trap mostly catches the older model.
- [x] What's left is mostly the rules, not the agent. Haiku 5.5's misses and breaks on Spectrum:
  - Danger-zone warning banner (notice) turned negative, 7 regressions on held-out. R7 says "everything in a Danger zone" is negative, and the agent followed it. Primer's rules used the same words.
  - "Available for review" badge (positive) turned informative, 5 regressions and 2 false flags. Spectrum's badge docs list "active, live" under informative; the screen, ported from Primer, says positive.
  - Subdued text put back as primary text, 8 misses on train, including a raw `#505050` that is exactly the subdued value. The v1 rules give spacing values but not color values.
  - One false flag called the plain `<label>` field labels lookalikes of Spectrum's FieldLabel component.
- [x] Added cell v3 = v2 plus three clarifications (R6: plain `<label>` field labels allowed; R7: Danger-zone negative is for its action buttons, the explaining banner is notice; positive includes availability). Run on Haiku 5.5 only. Written after reading Haiku 5.5 held-out failures, so v3's held-out is not blind; train is the clean comparison. Folder `systems/spectrum-v3/`.

### Cell results: rules v2 (Haiku 4.5) and v3 (Haiku 5.5)

| Cell | Split | Strict pass | Net fixed | False flags / run | Regressions / run | Cost |
| --- | --- | --- | --- | --- | --- | --- |
| Haiku 4.5, v1 (avg of A, B) | train | 8/52 | 261.5/362 (72.2%) | 0.12 | 0 | |
| Haiku 4.5, v2 | train | 11/52 (21.2%) | 292/362 (80.7%) | 0.04 | 0.06 | $5.60 |
| Haiku 4.5, v1 | held-out | 6/54 | 246/366 (67.2%) | 0.13 | 0.04 | |
| Haiku 4.5, v2 | held-out | 6/54 (11.1%) | 261/366 (71.3%) | 0.17 | 0.09 | $5.47 |
| Haiku 5.5, v1 | train | 38/52 | 348/362 (96.1%) | 0 | 0 | |
| Haiku 5.5, v3 | train | 42/52 (80.8%) | 351/362 (97.0%) | 0.02 | 0.02 | $0.42 |
| Haiku 5.5, v1 | held-out | 36/54 | 334/366 (91.3%) | 0.24 | 0.24 | |
| Haiku 5.5, v3 | held-out | 26/54 (48.1%) | 310/366 (84.7%) | 0.43 | 0.43 | $0.44 |

Source: `systems/spectrum-v2/runs/h45-*`, `systems/spectrum-v3/runs/h55-*`, `lab/report.py`.

- [x] **v2 lifts the old agent on train by +30.5 net fixed** (72.2% → 80.7%), above Primer's noise floor (24) and under Stage 3's 48 keep bar. Gains: raw colors 81.5 → 86/86, spacing 46 → 56/68, readability 30 → 39/52, meaning 11.5 → 16/46. [INFERENCE] Readability rose without any readability wording change; the hex values next to each text token probably made the disabled color's 1.7:1 easier to spot.
- [x] **Held-out +15** (246 → 261), not blind (see contamination note).
- [x] **v3 made the strong model worse on held-out.** v2's background-role sentence ("cards use layer 2") contradicts the sign-in screen, whose card sits on layer 1 (ported from Primer's muted card). Haiku 5.5 "fixed" that card in 23 of 54 held-out runs, each a regression; Haiku 4.5 did it in only 3. [INFERENCE] The stronger model follows the rules doc more literally, so a rule that contradicts the design costs it more.
- [x] This is Stage 3's custom-card lesson again, and the step that catches it was skipped: run the agent on every clean screen with the new rules before measuring.

### Clean-screen audit (12 clean screens as inputs, 1 run each)

| Rules | Haiku 5.5 | Sonnet 5.5 |
| --- | --- | --- |
| v1 | 11/12 clean; flagged "Available for review" (positive badge) | |
| v3 | 11/12 clean; flagged the sign-in card's layer-1 background | |
| v4 | 12/12 clean, 0 flags | 12/12 clean, 0 flags |

- [x] v4 = v3 with the card-role sentence replaced by "use the one the page already uses for the same kind of element... don't change a surface that already uses a valid token", and the role labels removed from the background list. Source: `systems/spectrum-v*-audit/runs/audit-*`.
- [x] The audit costs about a penny on Haiku 5.5 and found each rules-vs-design contradiction that the 106-run cells exposed. It's now a required step in the designer flow.

### Cell results: rules v2 (Haiku 5.5) and v4 (both agents)

| Cell | Split | Strict pass | Net fixed | False flags / run | Regressions / run | Cost |
| --- | --- | --- | --- | --- | --- | --- |
| Haiku 5.5, v2 | train | 40/52 (76.9%) | 350/362 (96.7%) | 0 | 0 | $0.40 |
| Haiku 5.5, v2 | held-out | 23/54 (42.6%) | 302/366 (82.5%) | 0.54 | 0.54 | $0.42 |
| Haiku 5.5, v4 | train | 43/52 (82.7%) | 353/362 (97.5%) | 0 | 0 | $0.40 |
| Haiku 5.5, v4 | held-out | 49/54 (90.7%) | 359/366 (98.1%) | 0 | 0 | $0.44 |
| Haiku 4.5, v4 | train | 13/52 (25.0%) | 276/362 (76.2%) | 0.08 | 0.06 | $5.30 |
| Haiku 4.5, v4 | held-out | 12/54 (22.2%) | 273/366 (74.6%) | 0.06 | 0.09 | $5.43 |

Source: `systems/spectrum-v2/runs/h55-*`, `systems/spectrum-v4/runs/*`, `lab/report.py`.

## Attribution: agent or rules? (all cells)

Net fixed (strict pass):

| Agent | Split | Primer | Spectrum v1 | v2 | v3 | v4 (audited) |
| --- | --- | --- | --- | --- | --- | --- |
| Haiku 4.5 | train | 71.6% (15/104) | 72.2% (16/104) | 80.7% (11/52) | | 76.2% (13/52) |
| Haiku 4.5 | held-out | 74.6% (12/54) | 67.2% (6/54) | 71.3% (6/54) | | **74.6% (12/54)** |
| Haiku 5.5 | train | 99.6% fixed (75/78, Stage 3) | 96.1% (38/52) | 96.7% (40/52) | 97.0% (42/52) | 97.5% (43/52) |
| Haiku 5.5 | held-out | not run | 91.3% (36/54) | 82.5% (23/54) | 84.7% (26/54) | **98.1% (49/54)** |

- [x] **The Spectrum-vs-Primer gap was the rules doc.** With audited v4 rules, the old agent on Spectrum held-out scores exactly what it scored on Primer held-out: 273/366 net fixed, 12/54 pages. On v1 it was 27 lower. v1 was a faithful port of Primer's rule shape, and that was the problem: it gave sizes but not color values for names that don't encode them, and it carried two Primer meanings ("everything in a Danger zone" is negative; "available" is success) that Spectrum's own docs read differently. [INFERENCE: v2–v4 were written after reading held-out failures, so held-out isn't blind for them. Train, which is clean, moves the same direction: +14.5 to +30.5 net fixed for Haiku 4.5.]
- [x] **The rest of the gap to "reliable" is the agent.** Under the same audited rules, Haiku 4.5 fixes 75–76% and fully passes about 1 page in 4; Haiku 5.5 fixes 98% and fully passes 83–91%. Rules moved Haiku 4.5 by up to 8.5 points on train; the model generation moves it by 21–24.
- [x] **Rules mistakes cost the strong model more.** A rule that contradicts the design (v2's "cards use layer 2" vs the sign-in card) dropped Haiku 5.5's held-out from 91.3% to 82.5% and barely moved Haiku 4.5. The better agent follows the doc more literally, so its quality ceiling is the doc's.
- [x] **The cheap check that prevents it:** run the agent on every clean screen with the new rules. v1 and v3 each failed one clean screen on exactly the contradiction the full runs exposed; v4 passed 12/12 on Haiku 5.5 and Sonnet 5.5.
- [x] **Self-assessment didn't improve anywhere.** Even at 98% fixed, Haiku 5.5 said "all fixed" on 100% of runs, including the 14 of 106 that failed.
- [x] Stage 4 spend, all cells: $48.15 for 898 runs (Haiku 4.5 $38.23 / 370 runs; Sonnet 5.5 $6.34 / 68; Haiku 5.5 $3.59 / 460).

## Can a designer get reliable results? (answer for the write-up)

- [x] **With a current model and an audited rules doc: yes for token-level QA, with a human or the grader as the final check.** 98% of planted problems fixed, 0 false alarms, about 9 in 10 pages left exactly as designed, on a design system the agent had never been tuned for.
- [x] **With an older or smaller model: no.** About 3 in 4 problems fixed, 1 page in 4 fully clean, and over a third of problems fixed in some runs and missed in others.
- [x] **Never from the agent's own report.** Every model said "all fixed" on every run.
- [x] **The work is in the rules doc, and it has a test.** State every token's value, say which of several look-alike tokens to use, check that each rule's meanings match the system's own docs, then run the agent on your clean screens and fix any rule it trips on before measuring anything.
- [ ] Limits: planted problems on made-up screens, one second system, held-out not blind for v2–v4, no held-out noise floor.
