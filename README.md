# Design QA Agent

A small AI agent that reviews a UI screen against your design system, fixes what breaks the rules, and tells you what it changed. Around it sits a test bench that measures how often the agent is actually right, because an agent that says "all fixed" is not the same as an agent that fixed everything.

I built this as a designer learning how agent harnesses work, and I tested it on two open design systems: GitHub's Primer and Adobe's Spectrum. The agent itself is four lines of instructions. Almost everything interesting turned out to live in the rules doc and in the measuring.

## What it does

You give the agent a screen (HTML) and a design-system folder: your rules doc plus your token CSS. It reads the rules, edits the screen in place, and writes a short report. It runs in Claude Code's headless mode with read and edit tools only, no shell, inside a folder that can't see the answer key.

The test bench plants known problems into clean screens (a hard-coded hex, a 13px gap, a safe button styled as destructive, gray text on gray), runs the agent, and grades the result three ways:

- **Code grader.** Strict: every planted problem restored, nothing else changed, no rule broken, all text readable.
- **LLM judge.** Would a design-system reviewer ship this, and is the agent's report accurate? Checked against 20 blind labels from a human designer.
- **The agent's own claim.** Whether it said "all fixed", so you can see how often that claim is wrong.

## Bring your rules doc and about 10 screens

Everything specific to a design system lives in one folder. To point the agent at yours, you need:

1. **Your tokens as CSS custom properties**, for color, spacing, type and (if you have them) radius and border width, plus your components as CSS classes.
2. **A rules doc** in the same shape as `systems/spectrum/design-system/RULES.md`: seven short, checkable rules (tokens for color, spacing, type and shape; readable text; use the real components; color means something).
3. **About 10 clean screens** in your system, with a `data-qa` attribute on every element.
4. **A `ds.json`** that tells the bench what your tokens and components are called.

[`systems/README.md`](systems/README.md) walks through every `ds.json` field. Copy `systems/spectrum/` as a starting point.

Write the rules doc carefully. On Primer, rewording two unclear rules moved the agent from 71% to 96% on the same screens, a bigger jump than any change to the agent.

## Run it

You need Python 3.10+, [Claude Code](https://docs.claude.com) installed and logged in, and Playwright's Chromium.

```bash
pip install -r requirements.txt
python -m playwright install chromium

export DQA_SYSTEM=spectrum            # or primer, or your own folder name
# export DQA_SYSTEM_DIR=/path/to/your-system   # if your system lives elsewhere

python lab/validate_screens.py        # your clean screens break no rules
python lab/audit.py                   # the agent leaves your clean screens alone (else a rule contradicts your design)
python -c "import sys; sys.path.insert(0,'lab'); import mutate; mutate.build_v3()"   # plant problems, write tasks/
python lab/validate_tasks.py          # every planted problem is visible to a grader

# one strong model over every task first: a task it fails is usually a broken task
python lab/run_agent.py --skill skill/v000 --run probe --split train --model claude-sonnet-5-5

# the measurement
python lab/run_agent.py --skill skill/v000 --run base-a --split train --trials 2
python lab/report.py base-a
python lab/taxonomy.py base-a
```

The agent's working folders go to `~/.design-qa-lab-work` (change it with `LAB_WORK_ROOT`). They must sit outside this repo, and the agent is denied read access to the repo, so it never sees the answers.

## What the scores mean

| Score | Plain meaning |
| --- | --- |
| Strict pass | The whole page came back exactly as designed: every planted problem fixed, nothing else touched. Hard on purpose. |
| Net fixed | Problems fixed, minus anything the agent broke and anything it wrongly flagged. The best single number for "did it help". |
| Detected | Share of planted problems the agent mentioned at all. |
| Says "all fixed" | How often the agent claimed it was done. Compare it with the pass rate. |
| T1 to T6 | Why runs failed: meaning not checked, readability not checked, incomplete sweep, wrong fix, false alarm, overconfident report. |

Two identical runs can differ a lot (by 24 net fixed on Primer's train set), so compare averages of repeated runs, never single runs.

## What I found

**The rules doc mattered more than the agent.** On Primer, most of the early "agent failures" turned out to be my own rules being unclear: a purple "done" label the rules never defined, a custom card the rules accidentally banned. Rewording two rules took the current small model from 71% to 96% on the same screens.

**Current models already handle token-level QA.** With the four-line skill, Haiku 5.5 fixed 99.6% of planted problems on Primer and Sonnet 5.5 passed 42 of 44 pages. So I tested on an older model, Haiku 4.5, where there was room to improve, and ran a self-improving loop on it. Six rounds, zero kept edits: every edit fixed the failure it aimed at and lost ground somewhere else, and none cleared the noise between two identical runs.

**The same agent carried over to a second design system with no retuning, and the rules doc decided how well.** Moving from Primer to Spectrum changed every token name, every component class and the way the theme loads, and the agent didn't need a single new line of instructions. With a rules doc ported straight from Primer, it matched Primer on the practice set but fell about 7 points behind on held-out screens. So I tested whether the agent or the rules were at fault, crossing two agents with four versions of the Spectrum rules. Once the rules stated every token's value, named Spectrum's look-alike tokens (base, layer 2 and white are all the same white), and stopped carrying over two Primer meanings that Spectrum's own docs read differently, the older agent on Spectrum's held-out screens scored exactly what it scored on Primer's: 273 of 366 problems, 12 of 54 pages.

**The rest of the distance to "reliable" is the model.** Under the same audited rules, Haiku 4.5 fixed about 75% of problems and fully cleaned about 1 page in 4, while Haiku 5.5 fixed 98% and left about 9 in 10 pages exactly as designed, with no false alarms. Better rules bought the old agent up to 8.5 points; a newer model bought it more than 20.

**A better model makes your rules doc's mistakes louder.** One rule I added ("cards use layer 2") contradicted a sign-in card in my own clean screens. The old agent mostly ignored it; the new one followed it and "fixed" that card in 23 of 54 runs, dropping its score from 91% to 82%. The check that catches this costs about a penny: run the agent on your untouched screens and see what it flags. It found every contradiction the full measurements did, so it's now step one in [`systems/README.md`](systems/README.md).

**What else didn't carry over was in the bench and in Spectrum itself.** All the Primer-specific code lived in the test bench, so it moved into one config file per system. Spectrum's notice badge renders white on orange at 2.6:1, under the contrast bar Spectrum's own accessibility page sets, and its "full" corner radius is a unitless multiplier that renders square when used directly.

**Some things didn't change at all.** On every system and every model, the agent said "all fixed" on every single run, including the ones that failed. Use the grader or your own eyes for the final call, never the agent's report.

| Held-out screens | Primer | Spectrum, ported rules | Spectrum, audited rules |
| --- | --- | --- | --- |
| Haiku 4.5: problems fixed (net) | 74.6% | 67.2% | 74.6% |
| Haiku 4.5: pages left exactly as designed | 12/54 | 6/54 | 12/54 |
| Haiku 5.5: problems fixed (net) | | 91.3% | 98.1% |
| Haiku 5.5: pages left exactly as designed | | 36/54 | 49/54 |
| Said "all fixed" | 100% | 100% | 100% |

Same four-line skill everywhere. The Spectrum rules shipped here are the audited version; earlier versions are in `systems/spectrum/design-system/rules-history/`. One caveat: the later rules were written after looking at held-out failures, so treat the held-out gains as likely rather than proven. The practice-set gains, which were never looked at that way, point the same direction.

The full record, with every number and the runs it came from, is in [`NOTEBOOK.md`](NOTEBOOK.md). Per-run summaries are in [`results/`](results/), and [`examples/spectrum-one-run/`](examples/spectrum-one-run/) shows one run end to end.

## What's in here

| Folder | What it holds |
| --- | --- |
| `lab/` | The bench: agent runner, problem planter, graders, judge, failure taxonomy, and the self-improving loop |
| `skill/` | The agent's instructions. `v000` is the one that stuck; `v001` to `v006` are the loop's attempts, with the reasons each was reverted in `CHANGELOG.md` |
| `systems/primer/`, `systems/spectrum/` | Each design system: rules, vendored CSS and license, clean screens, planted tasks |
| `results/` | One summary per run (no transcripts), grouped by system and rules version, plus the clean-screen audits |
| `NOTEBOOK.md` | The lab notebook |

## Credits and licenses

The code in this repo is MIT. The vendored CSS keeps its own license: [Primer](https://primer.style) by GitHub (MIT) and [Spectrum CSS](https://opensource.adobe.com/spectrum-css/) by Adobe (Apache-2.0), with the license files in each `vendor/` folder. Adobe Clean, Spectrum's typeface, is restricted to Adobe products, so it isn't included; the Spectrum screens fall back to system fonts. The screens and their content are made up.
