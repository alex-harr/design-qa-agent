"""The design system under test: where its files live, what its tokens and components are called,
and how token values resolve. Everything system-specific in the lab comes from here.

Pick a system with the DQA_SYSTEM environment variable (a folder name under systems/, default "primer"),
or point DQA_SYSTEM_DIR at any folder laid out the same way:

    <system>/design-system/ds.json   names, patterns and scales (see systems/*/design-system/ds.json)
    <system>/design-system/RULES.md  the rules the agent and the judge read
    <system>/screens/*.html          clean screens, every element tagged with data-qa
    <system>/tasks/, splits.json     built by lab/mutate.py
    <system>/runs/, analysis/        written by the harness
"""

import json, os, re
from pathlib import Path

LAB = Path(__file__).resolve().parents[1]
NAME = os.environ.get("DQA_SYSTEM", "primer")
ROOT = Path(os.environ["DQA_SYSTEM_DIR"]).resolve() if os.environ.get("DQA_SYSTEM_DIR") else LAB / "systems" / NAME
DS = ROOT / "design-system"
SCREENS = ROOT / "screens"
TASKS = ROOT / "tasks"
SPLITS = ROOT / "splits.json"
RUNS = ROOT / "runs"
ANALYSIS = ROOT / "analysis"

CFG = json.loads((DS / "ds.json").read_text())
TOKENS = CFG["tokens"]          # family -> regex for the custom-property name (None if the system has no such family)
COMPONENTS = CFG["components"]
MUTATE = CFG["mutate"]


def family(name):
    """Compiled regex matching `var(--token)` for a token family, or None when the system lacks it."""
    pat = TOKENS.get(name)
    return re.compile(r"var\(" + pat + r"\)") if pat else None


# ---- reading custom properties from vendored CSS ----

def _strip_comments(css):
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _blocks(css):
    """Yield (selector_text, body, inside_at_rule) for innermost rule blocks, tracking @media/@supports nesting."""
    stack, buf, i = [], [], 0
    sel_start = 0
    while i < len(css):
        ch = css[i]
        if ch == "{":
            stack.append((css[sel_start:i].strip(), i + 1))
            sel_start = i + 1
        elif ch == "}":
            if stack:
                sel, start = stack.pop()
                body = css[start:i]
                if "{" not in body:
                    yield sel, body, any(s.startswith("@") for s, _ in stack)
            sel_start = i + 1
        elif ch == ";" and not stack:
            sel_start = i + 1
        i += 1


def _decl_pairs(body):
    return [(n, v.strip()) for n, v in re.findall(r"(--[\w-]+)\s*:\s*([^;}]+)", body)]


def load_tokens():
    """Token table for the configured light theme.

    ds.json "token_source":
      files       vendor files to read, in order (component bundles that redefine tokens for other themes are left out)
      scopes      selectors whose blocks hold the theme's tokens, in cascade order (later wins); null reads every
                  declaration in file order and keeps the first, which is how flat :root token files behave
    """
    src = CFG["token_source"]
    table = {}
    for fname in src["files"]:
        css = _strip_comments((DS / fname).read_text())
        if not src.get("scopes"):
            for n, v in _decl_pairs(css):
                table.setdefault(n, v)
            continue
        scopes = src["scopes"]
        for sel, body, in_at in _blocks(css):
            if in_at:
                continue
            parts = {p.strip() for p in sel.split(",")}
            hit = [s for s in scopes if s in parts]
            if not hit:
                continue
            rank = max(scopes.index(s) for s in hit)
            for n, v in _decl_pairs(body):
                if n not in table or table[n][1] <= rank:
                    table[n] = (v, rank)
    if src.get("scopes"):
        table = {n: v for n, (v, _) in table.items()}
    return table


TOK = load_tokens()


def _find_var(s, start=0):
    """Locate the next var( ... ) with balanced parentheses: (start, end, name, fallback or None)."""
    i = s.find("var(", start)
    if i < 0:
        return None
    depth, j = 0, i + 3
    while j < len(s):
        if s[j] == "(":
            depth += 1
        elif s[j] == ")":
            depth -= 1
            if depth == 0:
                break
        j += 1
    inner = s[i + 4:j]
    name, _, fb = inner.partition(",")
    return i, j + 1, name.strip(), (fb.strip() if _ else None)


def resolve(value, depth=0):
    """Replace every var(--x[, fallback]) in a value with the token's light-theme value, recursively."""
    value = value.strip()
    if depth > 12 or "var(" not in value:
        return value
    out, pos = [], 0
    while True:
        hit = _find_var(value, pos)
        if not hit:
            break
        i, j, name, fb = hit
        out.append(value[pos:i])
        rep = TOK.get(name, fb if fb is not None else value[i:j])
        out.append(resolve(rep, depth + 1))
        pos = j
    out.append(value[pos:])
    return "".join(out).strip()


def hex6(v):
    v = v.strip().lower()
    return v if re.fullmatch(r"#[0-9a-f]{6}", v) else None


def color_hex(v):
    """#rrggbb for an opaque hex or rgb() color, else None (translucent colors are skipped on purpose)."""
    h = hex6(v)
    if h:
        return h
    m = re.fullmatch(r"rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)\s*(?:[,/]\s*(1|1\.0+|100%)\s*)?\)", v.strip().lower())
    if m:
        return "#" + "".join(f"{int(x):02x}" for x in m.groups()[:3])
    return None


def px(value):
    """A resolved length in px (rem at a 16px root), or None."""
    v = resolve(value)
    m = re.fullmatch(r"(-?[\d.]+)(px|rem)", v)
    if not m:
        return None
    n = float(m.group(1)) * (16 if m.group(2) == "rem" else 1)
    return int(round(n)) if abs(n - round(n)) < 1e-6 else n


def fmt_px(n):
    return f"{int(n)}px" if float(n).is_integer() else f"{n}px"


def scale(key, family_name):
    """A px scale from ds.json, or derived from every token in the family when the config says "auto"."""
    s = MUTATE.get(key, "auto")
    if s != "auto":
        return set(s)
    pat = re.compile(TOKENS[family_name])
    return {p for n in TOK if pat.fullmatch(n) for p in [px(f"var({n})")] if isinstance(p, int) and 0 < p < 1000}  # skip 'full' pill radii like 9999px
