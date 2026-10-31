"""Turn CSS and markup into words a designer reads: element names, token names, before/after changes.

Used by label_page.py. Everything returned as HTML is escaped here.
"""

import html as H
import re
from pathlib import Path

import mutate  # token resolution (light theme)
import system

LAB = system.LAB
LABELS = system.CFG.get("labels", {})

SCREEN_TITLES = {s.stem[3:]: re.search(r"<title>(.*?)</title>", s.read_text()).group(1)
                 for s in sorted(system.SCREENS.glob("*.html"))}

COLOR_ROLE = LABELS.get("colors", {})


def _fam(name):
    """Which ds.json token family a token name (without leading dashes) belongs to."""
    for fam, pat in system.TOKENS.items():
        if pat and re.fullmatch(pat, "--" + name):
            return fam
    return None
PROP_LABEL = {
    "color": "Text color", "background": "Background", "background-color": "Background", "border": "Border",
    "border-top": "Top border", "border-bottom": "Bottom border", "border-left": "Left border", "border-right": "Right border",
    "border-color": "Border color", "border-width": "Border width", "border-radius": "Corner radius",
    "margin": "Outer spacing", "margin-top": "Space above", "margin-bottom": "Space below", "margin-left": "Space left",
    "margin-right": "Space right", "padding": "Inner padding", "padding-top": "Top padding", "padding-bottom": "Bottom padding",
    "padding-left": "Left padding", "padding-right": "Right padding", "gap": "Gap between items", "row-gap": "Row gap",
    "column-gap": "Column gap", "font-size": "Text size", "font-weight": "Font weight", "line-height": "Line height",
    "display": "Display", "width": "Width", "max-width": "Max width",
}
SPACE_SCALE = mutate.SCALE_PX


def esc(s):
    return H.escape(str(s), quote=True)


def swatch(hex_or_rgb):
    return f'<i class="sw" style="background:{esc(hex_or_rgb)}"></i>'


def px_of(token):
    return mutate.px(f"var(--{token})")


def _nice(name):
    return name.split("-", 1)[-1].replace("-", " ").capitalize() if "-" in name else name


def token_label(name):
    """name without leading dashes, e.g. 'fgColor-muted' -> chip HTML. Labels come from ds.json, with readable fallbacks."""
    fam = _fam(name)
    if fam == "color":
        hexv = mutate.color_hex(mutate.resolve(f"var(--{name})"))
        role = COLOR_ROLE.get(name) or _nice(name)
        return f'<span class="tok">{swatch(hexv) if hexv else ""}{esc(role)}<small>token</small></span>'
    p = px_of(name)
    if fam == "space":
        return f'<span class="tok">{p:g}px<small>spacing token</small></span>' if p is not None else f'<span class="tok">{esc(name)}<small>spacing token</small></span>'
    if fam == "type":
        v = mutate.resolve(f"var(--{name})")
        if p is None and re.fullmatch(r"\d{3}", v):
            return f'<span class="tok">{esc(_nice(name))} ({esc(v)})<small>weight token</small></span>'
        return f'<span class="tok">{esc(_nice(name))}{f" {p:g}px" if p else ""}<small>type token</small></span>'
    if fam == "radius":
        return f'<span class="tok">{esc(_nice(name))} radius{f" {p:g}px" if p and p < 100 else ""}<small>token</small></span>'
    if fam == "border_width":
        return f'<span class="tok">{esc(_nice(name))} {p:g}px<small>border token</small></span>' if p else f'<span class="tok">{esc(name)}</span>'
    return f'<span class="tok">{esc(name)}<small>token</small></span>'


def value_html(prop, value):
    """A CSS value with tokens as named chips and raw values flagged."""
    out, pos = [], 0
    for m in re.finditer(r"var\(--([\w-]+)(?:,[^)]*)?\)|#[0-9a-fA-F]{3,8}\b|rgba?\([^)]*\)|-?\d*\.?\d+px\b", value):
        out.append(esc(value[pos:m.start()]))
        t = m.group(0)
        if t.startswith("var("):
            out.append(token_label(m.group(1)))
        elif t.startswith(("#", "rgb")):
            out.append(f'<span class="raw">{swatch(t)}{esc(t)}<small>hard-coded</small></span>')
        else:
            n = float(t[:-2])
            note = "hard-coded"
            if prop in ("margin", "padding", "gap") or prop.startswith(("margin-", "padding-")) or prop.endswith("gap"):
                note = "hard-coded, on the scale" if n in SPACE_SCALE or n == 0 else "hard-coded, off the scale"
            out.append(f'<span class="raw">{esc(t)}<small>{note}</small></span>')
        pos = m.end()
    out.append(esc(value[pos:]))
    s = "".join(out).strip()
    if prop == "font-weight" and re.fullmatch(r"\d{3}", value.strip()):
        s = f'<span class="raw">{esc(value)}<small>hard-coded</small></span>'
    return s or "<em>none</em>"


CLASS_PARTS = LABELS.get("classes", {})
BTN, PILL = system.COMPONENTS["button"]["base"], system.COMPONENTS["pill"]["base"]
BANNER = LABELS.get("banner", {"base": None, "prefix": None})


def component_html(classes, style):
    cls = classes.split()
    if style and not set(cls) & set(system.COMPONENTS["lint_classes"]):
        return f'<span class="raw">Hand-built with inline styles<small>not the component</small></span>'
    if BTN in cls:
        mods = [CLASS_PARTS[c] for c in cls if c in CLASS_PARTS and c != BTN]
        return f'<span class="tok">Button{": " + ", ".join(mods) if mods else ": default"}<small>component</small></span>'
    if PILL in cls:
        mods = [CLASS_PARTS[c] for c in cls if c != PILL and c in CLASS_PARTS]
        return f'<span class="tok">Status pill{": " + ", ".join(mods) if mods else ": neutral"}<small>component</small></span>'
    if BANNER["base"] and BANNER["base"] in cls:
        mods = [CLASS_PARTS[c] for c in cls if c != BANNER["base"] and c.startswith(BANNER["prefix"]) and c in CLASS_PARTS]
        return f'<span class="tok">Banner{": " + ", ".join(mods) if mods else ": info"}<small>component</small></span>'
    return esc(classes) or "<em>no classes</em>"


def element_name(qa, info):
    """'Billing › “Pay now” button' from a data-qa id and its DOM facts."""
    stem = next((s for s in sorted(SCREEN_TITLES, key=len, reverse=True) if qa.startswith(s + "-")), None)
    section = SCREEN_TITLES.get(stem, "")
    local = qa[len(stem) + 1:] if stem else qa
    tag, cls, text = info.get("tag", ""), info.get("class", "").split(), (info.get("text") or "").strip()
    kind = ("button" if tag == "button" or BTN in cls else "status pill" if PILL in cls else "banner" if BANNER["base"] in cls
            else "link" if tag == "a" else "heading" if tag in ("h1", "h2", "h3", "h4") else "field label" if tag == "label"
            else "field" if tag in ("input", "textarea", "select") else "text" if tag in ("p", "span", "small", "td", "th", "dd", "dt")
            else None)
    if text and kind:
        short = text if len(text) <= 42 else text[:40].rstrip() + "…"
        name = f"“{short}” {kind}"
    else:
        name = local.replace("-", " ").strip().capitalize() + (f" {kind}" if kind and kind not in local else "")
    return f"{section} › {name}" if section else name
