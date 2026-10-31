# Design system rules (Primer, light theme)

Screens load `design-system/primer.css`, which provides the tokens as CSS custom properties and the components listed at the end. In a screen's own CSS, colors, spacing, type and shape must come from tokens (R1–R4); layout values such as `width`, `max-width`, `display` and flex settings are free. These are the rules a reviewer checks.

## The rules

| ID | Rule |
| --- | --- |
| R1 | **Colors are tokens.** Every color, background and border color is a `var(--fgColor-*)`, `var(--bgColor-*)` or `var(--borderColor-*)` token. No hex, `rgb()`, `hsl()` or named colors. |
| R2 | **Spacing is on the scale.** `margin`, `padding` and `gap` use `var(--base-size-*)` tokens (or `0` / `auto`). No raw `px`, `rem` or `em`. |
| R3 | **Type is on the scale.** `font-size`, `font-weight` and `line-height` use `var(--text-*)` or `var(--base-text-*)` tokens. |
| R4 | **Shape is on the scale.** `border-radius` uses `var(--borderRadius-*)`; `border-width` uses `var(--borderWidth-*)`. |
| R5 | **Text is readable.** Text meets WCAG AA contrast against its background: 4.5:1, or 3:1 for large text (24px, or 18.66px bold). |
| R6 | **Use the components.** Buttons are `.btn` (+ `.btn-primary`, `.btn-danger`, `.btn-invisible`, `.btn-sm`); status pills are `.Label`; banners are `.flash`; text inputs are `.form-control`; bordered lists of rows are `.Box`. Never hand-build a lookalike of one of these, like a `<span>` styled as a pill or a `<div>` or `<a>` styled as a button. Other surfaces (cards, panels, drop zones, dots, icons) may be styled by the screen's own CSS, using tokens. |
| R7 | **Color means something.** Danger (danger tokens, `.btn-danger`, `.Label--danger`, `.flash-error`) only for destructive or hard-to-undo actions (everything in a Danger zone), errors, failures and bug reports. Success for success, completion or "open". Attention for warnings and pending states. Accent for links and informational emphasis. Done (purple) only for triaged or merged items. Muted for secondary text, metadata and counts: status colors never go on plain secondary text. The primary green button is for the main safe action, never a destructive one. |

## Tokens

The most common tokens are listed here. Any token defined in `design-system/vendor/` is valid, even if it is not listed here.

**Text color:** `--fgColor-default` (primary text), `--fgColor-muted` (secondary text, metadata), `--fgColor-accent` (links), `--fgColor-success`, `--fgColor-attention`, `--fgColor-danger`, `--fgColor-done`, `--fgColor-onEmphasis` (text on emphasis backgrounds), `--fgColor-disabled` (disabled controls only; fails contrast as body text).

**Background:** `--bgColor-default`, `--bgColor-muted`, `--bgColor-inset`, `--bgColor-emphasis`, `--bgColor-accent-muted` / `-emphasis`, `--bgColor-success-muted` / `-emphasis`, `--bgColor-attention-muted` / `-emphasis`, `--bgColor-danger-muted` / `-emphasis`, `--bgColor-done-muted` / `-emphasis`, `--bgColor-neutral-muted` / `-emphasis`.

**Border:** `--borderColor-default`, `--borderColor-muted`, `--borderColor-emphasis`, and `--borderColor-{accent,success,attention,danger,done}-{muted,emphasis}`.

**Spacing scale:** `--base-size-2` (0.125rem), `-4`, `-6`, `-8`, `-12`, `-16`, `-20`, `-24`, `-28`, `-32`, `-36`, `-40`, `-44`, `-48`, `-64`, `-80`, `-96`, `-112`, `-128` (the number is the size in px at a 16px root).

**Type:** sizes `--text-body-size-small` (12px), `--text-body-size-medium` (14px), `--text-body-size-large` (16px), `--text-title-size-small` (16px), `--text-title-size-medium` (20px), `--text-title-size-large` (32px), `--text-caption-size` (12px); weights `--base-text-weight-normal` (400), `-medium` (500), `-semibold` (600), `--text-title-weight-*`; line heights `--base-text-lineHeight-tight`, `-snug`, `-normal`, `-relaxed`.

**Shape:** `--borderRadius-small`, `-medium` (default), `-large`, `-full`; `--borderWidth-thin`, `-thick`.

## Components

`.btn` · `.btn-primary` · `.btn-danger` · `.btn-invisible` · `.btn-sm` · `.form-control` · `.Counter` · `.Box` (+ `-header`, `-title`, `-body`, `-row`, `-footer`) · `.Label` (+ `--accent`, `--success`, `--attention`, `--danger`, `--done`) · `.flash` (+ `-warn`, `-error`, `-success`) · `.Progress` (+ `-item`) · `.avatar` · `.Dialog` (+ `-header`, `-title`, `-body`, `-footer`)
