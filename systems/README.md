# Adding a design system

Each folder here is one design system the agent can be tested on. To add yours, copy `systems/spectrum/` (or `systems/primer/`), replace its contents, and run everything with `DQA_SYSTEM=<folder name>`. You can also keep the folder anywhere and point `DQA_SYSTEM_DIR` at it.

```
<your-system>/
  design-system/
    ds.json            how the lab reads your system (fields below)
    RULES.md           the rules the agent and the judge read, R1 to R7
    <entry>.css        one stylesheet your screens link, which @imports the rest
    vendor/            your token and component CSS, plus its license
  screens/             about 10 clean screens, every element tagged with data-qa
```

`tasks/`, `splits.json`, `runs/` and `analysis/` are written by the lab.

## What the lab needs from your system

- [ ] Tokens as CSS custom properties for color, spacing, type and (if you have them) radius and border width. Sass-only variables won't work: the lab reads the CSS.
- [ ] Components as CSS classes: at least a button with a "danger" variant, and a status label (pill or badge) with a few meaning variants.
- [ ] A light theme the lab can find: either flat `:root` files, or selectors you name in `token_source.scopes`.
- [ ] Clean screens that pass `python3 lab/validate_screens.py`: no undefined tokens, no rule violations, all text readable.

## ds.json fields

| Field | What it's for |
| --- | --- |
| `entry_css` | The stylesheet screens link as `design-system/<entry_css>`. |
| `own_css` | Your lab-only CSS files (checked by the screen validator, shown to the loop's proposer). |
| `token_source.files` | Which CSS files define your tokens, in order. Leave out component bundles that redefine tokens for other themes. |
| `token_source.scopes` | `null` for flat `:root` files. Otherwise the theme selectors that hold your tokens, in cascade order (later wins), e.g. `[".spectrum", ".spectrum--light", ".spectrum--medium"]`. |
| `agent_copy.files` / `stubs` | What the agent gets in its folder. Give it the rules and token files; stub out big component bundles. |
| `tokens.color` … `tokens.border_width` | A regex for each token family's custom-property names. Set a family to `null` if your system doesn't have it; its check is skipped. |
| `components.lint_classes` | Classes a screen must use instead of hand-building a lookalike. |
| `components.button` | Button tags, base class, the class prefix, the main (`primary`) and `danger` variants, which variants to swap to danger when planting "safe action styled as danger", and variants never swapped. |
| `components.pill` | Status label tags, base class, prefix, and the meaning variants planted problems swap between. |
| `mutate.*_scale_px` | `"auto"` derives each scale from your tokens; a list overrides it. Include every valid value so "the nearest step" is never ambiguous. |
| `mutate.radius_mutable`, `border_width_mutable` | Which radius and border-width tokens the generator may replace with a raw value. |
| `mutate.text_default`, `text_muted`, `text_link`, `text_disabled` | Your primary, secondary, link and disabled text tokens. |
| `mutate.status_text` | Status colors planted on secondary text (a color-meaning problem). They should pass contrast, so the problem is only about meaning. |
| `mutate.contrast_traps` | Real tokens that fail contrast as text (a border gray, a white). |
| `labels` | Friendly names for the blind review page. Optional. |

## Writing the rules doc

The rules doc decides how good the agent can be. Stage 4 showed the same agent scoring 27 points lower on Spectrum with a rules doc ported from Primer, and exactly matching Primer once the doc was fixed. What made the difference:

- [ ] **State every token's value.** If your names don't encode the size (`spacing-100` is 8px), list the px value next to each token, and the hex next to each color.
- [ ] **Say how to fix a value:** the token with the closest value wins, and the number in a name is not a size.
- [ ] **Name your look-alikes.** If several tokens share a value (base, layer 2 and white are all `#ffffff` in Spectrum), say how to choose between them. Don't prescribe roles your own screens don't follow.
- [ ] **Check meanings against your system's own docs.** A meaning rule copied from another system ("success" covers "available") can disagree with yours.
- [ ] **Audit it.** Run the agent on your clean screens (below). Anything it flags is a rule your own design breaks. A stronger model follows the doc more literally, so it pays more for a wrong rule.

## Then

```
DQA_SYSTEM=<name> python3 lab/validate_screens.py
DQA_SYSTEM=<name> python3 lab/audit.py               # agent on every clean screen: should change nothing
DQA_SYSTEM=<name> python3 -c "import sys; sys.path.insert(0,'lab'); import mutate; mutate.build_v3()"
DQA_SYSTEM=<name> python3 lab/validate_tasks.py
DQA_SYSTEM=<name> python3 lab/run_agent.py --skill skill/v000 --run probe --split train --model claude-sonnet-5-5
```

The audit costs about a penny on Haiku 5.5 and catches rules that contradict your design. Then run a strong model once over every task before measuring anything: a task a strong model fails is usually a broken task. Stage 4 found three answer-key bugs this way, all specific to how Spectrum builds its components.
