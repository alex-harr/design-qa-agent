# Where each Spectrum rule comes from

Lab-only file: the agent never sees it (it isn't in `ds.json` `agent_copy`). Quotes were checked on 2026-10-29. Pages on spectrum.adobe.com are "Spectrum Hub" (Release 1.0, Sep 30 2026). Token values are read from the vendored `@spectrum-css/tokens` 16.0.2 files, which are what the screens and the grader actually use. `[INFERENCE]` marks a lab decision that isn't stated by Adobe. `[MEASURED]` marks a number computed by the lab from the vendored CSS.

## Setup (intro)
- "On the `<body>` element, start with `.spectrum`, add in `.spectrum--light`, then `.spectrum--medium`." [tokens README](https://github.com/adobe/spectrum-css/blob/main/tokens/README.md)
- "Though the token data in this package focus on only the current context (Spectrum 2)" (same README)
- "`.spectrum--light` - The default theme for Spectrum CSS, used for light mode"; "`.spectrum--medium` - The default scale for Spectrum CSS, used for desktop and tablet devices" [Spectrum CSS README](https://github.com/adobe/spectrum-css/blob/main/README.md)
- Layout values are free: [INFERENCE] same scope as the Primer rules, so the two systems are tested on the same rule shape.

## R1 Colors are tokens
- "Every part of the interface should use a color defined by Spectrum to ensure consistency across products." [Color](https://spectrum.adobe.com/foundations/color)
- "Do not use color functions to modify Spectrum colors." (same page)
- Token families listed in the rule are the semantic and gray aliases in the vendored tokens; `neutral-content-color-default` is `{gray-800}` and `neutral-subdued-content-color-default` is `{gray-700}` per [design data: color aliases](https://opensource.adobe.com/spectrum-design-data/tokens/color-aliases/).
- [INFERENCE] Spectrum 2 has no neutral border alias, so gray tokens are allowed for borders and dividers.

## R2 Spacing / R3 Type / R4 Shape
- Adobe publishes the spacing, type and shape tokens as tables ([layout](https://opensource.adobe.com/spectrum-design-data/tokens/layout/), [typography](https://opensource.adobe.com/spectrum-design-data/tokens/typography/)) but no prose rule saying "use only these". [INFERENCE] R2–R4 apply the R1 principle ("use a color defined by Spectrum") to the other token families, as the Primer rules do.
- "Use Spectrum typography and colors to ensure proper type scale, line height, weight, and contrast for blocks of text." [Inclusive design](https://spectrum.adobe.com/page/inclusive-design/) (Spectrum 1 era page)
- "Spectrum currently recommends using the default weights and widths." [Typography](https://spectrum.adobe.com/foundations/typography)
- [MEASURED] Values in the token lists come from the vendored 16.0.2 files. The design-data site also lists `spacing-85` (6px) and `spacing-350` (20px) and different small radius values; those aren't in the vendored package, so they aren't listed.
- [MEASURED] `--spectrum-corner-radius-full` and `-1000` resolve to `0.5` with no unit. Used as `border-radius` the declaration is invalid and the corner renders square (seen while building the screens).

## R5 Text is readable
- "The visual presentation of text has a contrast ratio of at least 4.5:1." and "The visual presentation of illustrations, icons, and component states have a contrast ratio of at least 3:1." [Text field accessibility, WCAG 2.2 compliance](https://spectrum.adobe.com/fragments/components/text-field/accessibility)
- "Use the appropriate gray tokens and color tokens for text, icons, and illustrations. These tokens are guaranteed to meet or exceed WCAG contrast minimums..." [Color](https://spectrum.adobe.com/foundations/color)
- [MEASURED] On white: neutral 14.6:1, neutral subdued 8.1:1, accent and negative content 4.8:1, every visual color about 3.9–4.0:1, disabled 1.7:1, gray-300 1.4:1. White on the notice background (`#fc7d00`) is 2.6:1, so the vendored notice Badge fails 4.5:1. The screens use a notice StatusLight for "pending" instead.
- [INFERENCE] "Visual color (icons, dots, shapes, not text)": Adobe gives no definition for the visual-color tokens. The note is based on the 3:1 non-text rule above and the measured ratios.

## R6 Use the components
- Button: "Do not use custom colors for buttons." [Button usage](https://spectrum.adobe.com/fragments/components/button/usage-guidelines)
- Badge: "Badges are meant to offer quick context about what category, status, or meaning an item is associated with." [Badge usage](https://spectrum.adobe.com/fragments/components/badge/usage-guidelines)
- Text field: "Text fields collect custom text input." [Text field](https://spectrum.adobe.com/web/rsp/components/text-field)
- Class names and markup: the vendored component CSS and each package's `stories/template.js` (read as text, not run).
- [INFERENCE] The "never hand-build a lookalike" wording is carried over from the Primer rules so the two tests match.

## R7 Color means something
- "The accent button communicates strong emphasis and is reserved for actions that are essential to an experience." / "The negative button is for emphasizing actions that can be destructive or have negative consequences if taken." / "An outline style button has a visible stroke and no background color, and should only be used for secondary actions." [Button options](https://spectrum.adobe.com/fragments/components/button/option-details)
- Badge: "When badges have a semantic meaning, they use semantic colors." Accent "(e.g., new, beta, prototype, draft)"; Informative "(e.g., active, in use, live, published)"; Neutral "(e.g., archived, deleted, paused, not started, ended)"; Positive "(e.g., approved, complete, success, purchased, licensed)"; Notice "(e.g., expiring soon, limited, deprecated)"; Negative "(e.g., error, alert, rejected, failed)". [Badge options](https://spectrum.adobe.com/fragments/components/badge/option-details)
- In-line alert: positive "should be used to inform someone of a successful function or result of an action they took"; notice "can be used to warn about a situation that may need to be addressed soon"; negative "can be used to show an error or a failure". [In-line alert options](https://spectrum.adobe.com/fragments/components/in-line-alert/option-details)
- Status light notice examples include "needs approval, pending, scheduled". [Status light options](https://spectrum.adobe.com/fragments/components/status-light/option-details)
- [INFERENCE] "Neutral subdued for secondary text, metadata and counts: semantic colors never go on plain secondary text" and "Danger zone" wording are carried over from the Primer rules; Spectrum has no single sentence saying this.

## Fonts (not a rule)
- "Adobe Clean, Adobe Clean Serif, and Adobe Clean Han are restricted fonts for the exclusive use of Adobe products and software." [Fonts](https://spectrum.adobe.com/page/fonts) The lab doesn't ship Adobe Clean; `lab-components.css` adds a system fallback.

## v2 additions (Stage 4 attribution test)

- "Fixing a value", hex values and the equal-value groups: values read from the vendored 16.0.2 tokens [MEASURED]. The nearest-value convention is the same one the generator uses for both systems.
- Background roles (cards on layer 2, recessed areas on layer 1, page on base) and border grays by role: [INFERENCE] lab convention taken from how the clean screens use them. Spectrum's color page says "Use background layers for creating application hierarchy" but doesn't say what each layer is for ([Color](https://spectrum.adobe.com/foundations/color)).
- R1–R7 wording is unchanged from v1.

## v3 additions (Stage 4 attribution test)

- R6: plain `<label>` field labels are allowed. [INFERENCE] Lab clarification; Spectrum ships a FieldLabel component but the screens style labels with tokens.
- R7: Danger-zone negative applies to its action buttons; a warning banner explaining the zone is notice. Positive includes availability. [INFERENCE] Lab clarifications where Spectrum's own badge and alert docs (cited above) leave two readings: its badge docs put "active, live" under informative, which a reviewer can read as covering "Available for review".
