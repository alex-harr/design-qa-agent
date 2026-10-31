"""Deterministic checks for the design-system QA lab.

lint_source(html)        -> R1-R4 and R6 violations found by reading the CSS and markup
render(html_path)        -> computed styles per [data-qa] element + R5 contrast results (Playwright)
compare(clean, other)    -> per-element style differences between two renders
"""

import re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import system

LAB = system.LAB

COLOR_PROPS = {"color", "background", "background-color", "border-color", "border-top-color", "border-right-color",
               "border-bottom-color", "border-left-color", "outline-color", "fill", "stroke"}
BORDER_SHORTHANDS = {"border", "border-top", "border-right", "border-bottom", "border-left"}
SPACE_PROPS = {"margin", "margin-top", "margin-right", "margin-bottom", "margin-left", "margin-block", "margin-inline",
               "padding", "padding-top", "padding-right", "padding-bottom", "padding-left", "padding-block",
               "padding-inline", "gap", "row-gap", "column-gap"}
TYPE_PROPS = {"font-size", "font-weight", "line-height"}
RADIUS_PROPS = {"border-radius", "border-top-left-radius", "border-top-right-radius", "border-bottom-left-radius",
                "border-bottom-right-radius"}
BORDER_WIDTH_PROPS = {"border-width", "border-top-width", "border-right-width", "border-bottom-width", "border-left-width"}

NAMED_COLORS = {"red", "green", "blue", "white", "black", "gray", "grey", "orange", "yellow", "purple", "pink",
                "silver", "maroon", "navy", "teal", "olive", "lime", "aqua", "fuchsia", "brown", "gold"}
RAW_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgb|rgba|hsl|hsla)\(")
RAW_LENGTH = re.compile(r"(?<![\w-])-?\d*\.?\d+(?:px|rem|em)\b")
# Token families come from the system's ds.json. A family the system doesn't have is None and its check is skipped.
COLOR_TOKEN = system.family("color")
SPACE_TOKEN = system.family("space")
TYPE_TOKEN = system.family("type")
RADIUS_TOKEN = system.family("radius")
WIDTH_TOKEN = system.family("border_width")

COMPONENT_CLASSES = set(system.COMPONENTS["lint_classes"])
BUTTON = system.COMPONENTS["button"]


def _decls(body):
    for part in body.split(";"):
        if ":" in part:
            prop, val = part.split(":", 1)
            yield prop.strip().lower(), val.strip()


def _check_decl(prop, val):
    """Return a list of (rule, reason) for one declaration."""
    out = []
    low = val.lower()
    words = set(re.findall(r"[a-z]+", low))
    if prop in COLOR_PROPS or prop in BORDER_SHORTHANDS:
        if RAW_COLOR.search(val) or (words & NAMED_COLORS and "var(" not in low):
            out.append(("R1", "raw color value"))
    if prop in SPACE_PROPS:
        if RAW_LENGTH.search(val):
            out.append(("R2", "spacing off the token scale"))
    if prop in TYPE_PROPS and TYPE_TOKEN:
        if not TYPE_TOKEN.search(val) and val not in ("inherit", "normal"):
            out.append(("R3", "type value is not a token"))
    if prop == "font" and TYPE_TOKEN and not TYPE_TOKEN.search(val):
        out.append(("R3", "font shorthand is not a token"))
    if prop in RADIUS_PROPS and RADIUS_TOKEN:
        if RAW_LENGTH.search(val) or "%" in val:
            out.append(("R4", "radius off the token scale"))
    if (prop in BORDER_WIDTH_PROPS or prop in BORDER_SHORTHANDS) and WIDTH_TOKEN:
        stripped = WIDTH_TOKEN.sub("", COLOR_TOKEN.sub("", val) if COLOR_TOKEN else val)
        if RAW_LENGTH.search(stripped):
            out.append(("R4", "border width off the token scale"))
    return out


STYLE_BLOCK = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
TAG = re.compile(r"<([a-zA-Z][\w-]*)([^<>]*)>")
ATTR = lambda name: re.compile(r'\b' + name + r'\s*=\s*"([^"]*)"')


def lint_source(html):
    """R1-R4 from <style> blocks and inline styles, plus R6 component checks from markup."""
    found = []
    for block in STYLE_BLOCK.findall(html):
        block = re.sub(r"/\*.*?\*/", "", block, flags=re.S)
        for sel, body in RULE.findall(block):
            sel = " ".join(sel.split())
            for prop, val in _decls(body):
                for rule, why in _check_decl(prop, val):
                    found.append({"rule": rule, "where": sel, "property": prop, "value": val, "why": why})
    for tag, attrs in TAG.findall(html):
        qa = (ATTR("data-qa").search(attrs) or [None, None])[1]
        classes = set((ATTR("class").search(attrs) or [None, ""])[1].split())
        style = ATTR("style").search(attrs)
        where = f'[data-qa="{qa}"]' if qa else tag
        if style:
            decls = dict(_decls(style.group(1)))
            for prop, val in decls.items():
                for rule, why in _check_decl(prop, val):
                    found.append({"rule": rule, "where": where, "property": prop, "value": val, "why": why})
            looks_like_component = any(p.startswith("border-radius") for p in decls) and any(
                p.startswith("background") or p.startswith("border") and p != "border-radius" for p in decls)
            if looks_like_component and not (classes & COMPONENT_CLASSES):
                found.append({"rule": "R6", "where": where, "property": "style", "value": style.group(1)[:80],
                              "why": "hand-built lookalike of a component"})
        if tag.lower() == "button" and BUTTON["base"] not in classes:
            found.append({"rule": "R6", "where": where, "property": "class", "value": " ".join(sorted(classes)),
                          "why": f"button without the .{BUTTON['base']} component"})
    return found


STYLE_PROPS = ["color", "background-color", "font-size", "font-weight", "line-height", "text-decoration-line",
               "padding-top", "padding-right", "padding-bottom", "padding-left",
               "margin-top", "margin-right", "margin-bottom", "margin-left", "row-gap", "column-gap",
               "border-top-width", "border-right-width", "border-bottom-width", "border-left-width",
               "border-top-color", "border-right-color", "border-bottom-color", "border-left-color",
               "border-top-style", "border-top-left-radius", "border-top-right-radius",
               "border-bottom-left-radius", "border-bottom-right-radius", "box-shadow", "display"]

EXTRACT_JS = r"""
(props) => {
  const parse = (c) => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null;
    const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; };
  const over = (top, under) => { const a = top[3]; return [0,1,2].map(i => top[i]*a + under[i]*(1-a)).concat([1]); };
  const lum = (c) => { const f = v => { v /= 255; return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4); };
    return 0.2126*f(c[0]) + 0.7152*f(c[1]) + 0.0722*f(c[2]); };
  const bgOf = (el) => { const stack = []; for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
      const c = parse(getComputedStyle(n).backgroundColor); if (c && c[3] > 0) stack.push(c); }
    let base = [255,255,255,1]; for (let i = stack.length - 1; i >= 0; i--) base = over(stack[i], base); return base; };
  const styles = {}, contrast = [];
  for (const el of document.querySelectorAll('[data-qa]')) {
    const cs = getComputedStyle(el), o = {};
    for (const p of props) o[p] = cs.getPropertyValue(p);
    const own = Array.from(el.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim();
    o.__text = own; o.__class = el.getAttribute('class') || ''; o.__tag = el.tagName.toLowerCase();
    const anc = []; for (let n = el.parentElement; n; n = n.parentElement) if (n.dataset && n.dataset.qa) anc.push(n.dataset.qa); o.__ancestors = anc;
    styles[el.dataset.qa] = o;
    const isInput = el.tagName === 'INPUT';
    const text = isInput ? (el.value || '') : own;
    if (text && cs.visibility !== 'hidden' && cs.display !== 'none') {
      const bg = bgOf(el); const fg = over(parse(cs.color), bg);
      const l1 = lum(fg), l2 = lum(bg); const ratio = (Math.max(l1,l2)+0.05)/(Math.min(l1,l2)+0.05);
      const size = parseFloat(cs.fontSize), weight = parseInt(cs.fontWeight);
      const large = size >= 24 || (size >= 18.66 && weight >= 700);
      contrast.push({qa: el.dataset.qa, ratio: Math.round(ratio*100)/100, size, weight, large,
                     pass: ratio >= (large ? 3 : 4.5)});
    }
  }
  return {styles, contrast};
}
"""

_browser = None


def _page():
    global _browser
    if _browser is None:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        _browser = pw.chromium.launch()
    return _browser.new_page(viewport={"width": 1000, "height": 900})


def ensure_ds_link(folder):
    """Screens link design-system/<entry css> relative to themselves."""
    link = Path(folder) / "design-system"
    if not link.exists() and not link.is_symlink():
        link.symlink_to(system.DS)


def render(html_path, screenshot=None):
    html_path = Path(html_path).resolve()
    ensure_ds_link(html_path.parent)
    page = _page()
    page.goto(html_path.as_uri())
    page.wait_for_load_state("load")
    data = page.evaluate(EXTRACT_JS, STYLE_PROPS)
    if screenshot:
        page.screenshot(path=str(screenshot), full_page=True)
    page.close()
    data["contrast_failures"] = [c for c in data["contrast"] if not c["pass"]]
    return data


def compare(clean, other, props=STYLE_PROPS):
    """Elements whose computed style or own text differs between two renders."""
    diffs = {}
    for qa, cs in clean["styles"].items():
        ot = other["styles"].get(qa)
        if ot is None:
            diffs[qa] = {"__missing": True}
            continue
        d = {p: (cs.get(p), ot.get(p)) for p in list(props) + ["__text"] if cs.get(p) != ot.get(p)}
        # centered blocks (margin: ... auto) get layout-derived side margins; ignore those when both stay symmetric
        if ("margin-left" in d or "margin-right" in d) and cs.get("margin-left") == cs.get("margin-right") \
                and ot.get("margin-left") == ot.get("margin-right"):
            d.pop("margin-left", None)
            d.pop("margin-right", None)
        if d:
            diffs[qa] = d
    for qa in other["styles"]:
        if qa not in clean["styles"]:
            diffs[qa] = {"__added": True}
    return diffs
