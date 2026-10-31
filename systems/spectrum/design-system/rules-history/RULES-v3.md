# Design system rules (Spectrum 2, light color, medium scale), v3

Screens load `design-system/spectrum.css` and put `class="spectrum spectrum--light spectrum--medium"` on `<body>`. That provides the tokens as CSS custom properties and the components listed at the end. In a screen's own CSS, colors, spacing, type and shape must come from tokens (R1–R4); layout values such as `width`, `max-width`, `display` and flex settings are free. These are the rules a reviewer checks.

## The rules

| ID | Rule |
| --- | --- |
| R1 | **Colors are tokens.** Every color, background and border color is a Spectrum color token: a semantic color (`var(--spectrum-*-content-color-*)`, `var(--spectrum-*-background-color-*)`, `var(--spectrum-*-border-color-*)`, `var(--spectrum-*-visual-color)`), a background layer (`var(--spectrum-background-base-color)`, `var(--spectrum-background-layer-1-color)`, `var(--spectrum-background-layer-2-color)`) or a gray (`var(--spectrum-gray-*)`). No hex, `rgb()`, `hsl()` or named colors, and no color functions applied to Spectrum colors. |
| R2 | **Spacing is on the scale.** `margin`, `padding` and `gap` use `var(--spectrum-spacing-*)` tokens (or `0` / `auto`). No raw `px`, `rem` or `em`. The number in the name is not the size: `--spectrum-spacing-100` is 8px. |
| R3 | **Type is on the scale.** `font-size` uses `var(--spectrum-font-size-*)`, `font-weight` uses a weight token (`var(--spectrum-regular-font-weight)` and so on) and `line-height` uses `var(--spectrum-line-height-*)`. |
| R4 | **Shape is on the scale.** `border-radius` uses a `var(--spectrum-corner-radius-*)` length token; `border-width` uses `var(--spectrum-border-width-*)`. `--spectrum-corner-radius-full` and `--spectrum-corner-radius-1000` are unitless multipliers, not lengths, so they don't work as a `border-radius` on their own. |
| R5 | **Text is readable.** Text meets WCAG AA contrast against its background: 4.5:1, or 3:1 for large text (24px, or 18.66px bold). |
| R6 | **Use the components.** Buttons are `.spectrum-Button` with a treatment (`--fill`, `--outline`) and a variant (`--accent`, `--primary`, `--secondary`, `--negative`), optional `--sizeS`, and the text in `.spectrum-Button-label`; status labels are `.spectrum-Badge` (text in `.spectrum-Badge-label`) or `.spectrum-StatusLight`; banners are `.spectrum-InLineAlert` (text in `.spectrum-InLineAlert-content`); text inputs are `input.spectrum-Textfield-input` inside `.spectrum-Textfield`; data tables are `.spectrum-Table`. Never hand-build a lookalike of one of these, like a `<div>` styled as a badge or a `<button>` styled as a Spectrum button without its classes. Other surfaces (cards, panels, list containers, drop zones, dots, avatar placeholders) and plain `<label>` field labels may be styled by the screen's own CSS, using tokens. |
| R7 | **Color means something.** Negative (negative tokens, `.spectrum-Button--negative`, `.spectrum-Badge--negative`, `.spectrum-InLineAlert--negative`) only for destructive or hard-to-undo actions (every action button in a Danger zone), errors, failures and bug reports. Positive for success, completion, approval and availability ("Available", "Done"). Notice for warnings and pending states, including a warning banner that explains a Danger zone. Informative for active, live or in-progress items and for informational messages. Accent for the essential call to action, links and "new" labels. Neutral for plain categories and roles. Neutral subdued for secondary text, metadata and counts: semantic colors never go on plain secondary text. The accent button is for the main safe action, never a destructive one. |

## Fixing a value

Spectrum token names don't tell you their size or color, so fix values by looking them up below.

- **Numbers (R2–R4):** replace a raw or off-scale value with the token whose value is closest. The number in a token's name is not its size: 37px is closest to `--spectrum-spacing-600` (40px), not `-500` (32px); 12px radius is closest to `--spectrum-corner-radius-200` (10px).
- **Colors (R1):** replace a raw color with the token whose value is closest, from the family that fits the property: text colors for `color`, backgrounds for `background`, grays or border colors for borders.
- **Tokens that share a value:** pick by role, not by name. `--spectrum-background-base-color`, `--spectrum-background-layer-2-color`, `--spectrum-gray-25` and `--spectrum-white` are all `#ffffff`; `--spectrum-background-layer-1-color` and `--spectrum-gray-50` are both `#f8f8f8`. Cards, panels and dialogs use layer 2 (white); recessed areas, table and list headers, drop zones and page backdrops use layer 1 (light gray); the page itself uses base. Borders use `--spectrum-gray-300` by default, `--spectrum-gray-200` for subtle row dividers and `--spectrum-gray-400` for strong or dashed outlines. A near-white raw color goes back to white, not to light gray.

## Tokens

The most common tokens are listed here. Any token defined in `design-system/vendor/tokens/` is valid, even if it is not listed here.

**Text color:** `--spectrum-neutral-content-color-default` (#292929, primary text), `--spectrum-neutral-subdued-content-color-default` (#505050, secondary text, metadata), `--spectrum-accent-content-color-default` (#3b63fb, links), `--spectrum-negative-content-color-default` (#d73220, error text), `--spectrum-disabled-content-color` (#c6c6c6, disabled controls only; fails contrast as body text). There are no positive, notice or informative text colors.

**Visual color (icons, dots, shapes, not text):** `--spectrum-accent-visual-color`, `--spectrum-positive-visual-color`, `--spectrum-notice-visual-color`, `--spectrum-informative-visual-color`, `--spectrum-negative-visual-color`, `--spectrum-neutral-visual-color`. These are about 3.9:1 on white, below the 4.5:1 body text needs.

**Background:** `--spectrum-background-base-color` (#ffffff, the page), `--spectrum-background-layer-1-color` (#f8f8f8, recessed areas), `--spectrum-background-layer-2-color` (#ffffff, cards and panels), subtle tints such as `--spectrum-accent-subtle-background-color-default` (#e5f0fe) and `--spectrum-negative-subtle-background-color-default` (#ffebe8), and `--spectrum-{neutral,accent,informative,positive,notice,negative}-background-color-default` (strong fills) / `-subtle-background-color-default` (tints).

**Border and gray:** `--spectrum-gray-200` (#e1e1e1, subtle dividers), `--spectrum-gray-300` (#dadada, default border), `--spectrum-gray-400` (#c6c6c6, strong border), `--spectrum-negative-border-color-default` (#d73220). Other grays: `-50` #f8f8f8, `-75` #f3f3f3, `-100` #e9e9e9, `-500` #8f8f8f, `-700` #505050, `-800` #292929. Grays run `--spectrum-gray-25` (white) to `--spectrum-gray-1000` (black).

**Spacing scale:** `--spectrum-spacing-50` (2px), `-75` (4px), `-100` (8px), `-200` (12px), `-300` (16px), `-400` (24px), `-500` (32px), `-600` (40px), `-700` (48px), `-800` (64px), `-900` (80px), `-1000` (96px).

**Type:** sizes `--spectrum-font-size-50` (11px), `-75` (12px), `-100` (14px, body), `-200` (16px), `-300` (18px), `-400` (20px), `-500` (22px), `-600` (25px), `-700` (28px), `-800` (32px), up to `-1300`; weights `--spectrum-light-font-weight` (300), `--spectrum-regular-font-weight` (400), `--spectrum-medium-font-weight` (500), `--spectrum-bold-font-weight` (700), `--spectrum-extra-bold-font-weight` (800), `--spectrum-black-font-weight` (900); line heights `--spectrum-line-height-100` (1.3), `-200` (1.5).

**Shape:** radius `--spectrum-corner-radius-0` (0), `-75` (4px), `-100` (8px), `-200` (10px), `-300` (6px), `-400` (7px), `-500` (8px), `-600` (9px), `-700` (10px), `-800` (16px); the number is not the size. Border width `--spectrum-border-width-100` (1px), `-200` (2px), `-400` (4px).

## Components

`.spectrum-Button` (+ `--fill`, `--outline`, `--accent`, `--primary`, `--secondary`, `--negative`, `--sizeS`, `-label`) · `.spectrum-Badge` (+ `--neutral`, `--accent`, `--informative`, `--positive`, `--notice`, `--negative`, `--sizeS`, `-label`) · `.spectrum-StatusLight` (+ `--neutral`, `--accent`, `--info`, `--positive`, `--notice`, `--negative`, `--sizeM`) · `.spectrum-InLineAlert` (+ `--info`, `--positive`, `--notice`, `--negative`, `-header`, `-content`) · `.spectrum-Textfield` (+ `-input`) · `.spectrum-FieldLabel` · `.spectrum-HelpText` · `.spectrum-Table` (+ `-head`, `-headCell`, `-body`, `-row`, `-cell`, `--sizeM`) · `.spectrum-ProgressBar` (+ `-track`, `-fill`, `--sizeM`) · `.spectrum-Avatar` · `.spectrum-Divider`
