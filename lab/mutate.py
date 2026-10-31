"""Seed known design-system violations into clean screens and record ground truth.

Each task = one clean screen + 2-4 planted problems (or none, for clean controls).
Ground truth names the rule, the CSS selector or element, and the original value,
so graders can check both detection and the fix. Seeded and reproducible.
"""

import json, random, re, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import checks
import system
from system import resolve, hex6, color_hex, px, fmt_px  # token resolution (light theme), re-exported for describe.py

LAB = system.LAB
T, M, BTN, PILL = system.TOKENS, system.MUTATE, system.COMPONENTS["button"], system.COMPONENTS["pill"]
SCALE_PX = system.scale("space_scale_px", "space")
TYPE_SCALE = system.scale("type_scale_px", "type")
RADIUS_SCALE = system.scale("radius_scale_px", "radius") if T.get("radius") else set()

COLOR_FULL = re.compile(r"var\(" + T["color"] + r"\)")
SPACE_VAR = re.compile(r"var\((" + T["space"] + r")\)")
RADIUS_FULL = re.compile(r"var\(" + M["radius_mutable"] + r"\)") if M.get("radius_mutable") else None
WIDTH_VAR = re.compile(r"var\((" + M["border_width_mutable"] + r")\)") if M.get("border_width_mutable") else None
TEXT_DEFAULT, TEXT_MUTED, TEXT_LINK, TEXT_DISABLED = M["text_default"], M["text_muted"], M["text_link"], M["text_disabled"]


def jitter(h, rng):
    rgb = [int(h[i:i + 2], 16) for i in (1, 3, 5)]
    i = rng.randrange(3)
    rgb[i] = max(0, min(255, rgb[i] + rng.choice([-6, -5, -4, 4, 5, 6])))
    return "#" + "".join(f"{c:02x}" for c in rgb)


def unambiguous(n, scale):
    """Off-scale integers whose nearest scale value is n and nothing else, so the intended fix is knowable."""
    out = []
    for x in range(max(1, n - 4), n + 5):
        if x == n or x in scale:
            continue
        dists = sorted((abs(x - s), s) for s in scale)
        if dists[0][1] == n and dists[0][0] < dists[1][0]:
            out.append(x)
    return out


# ---- parsing the screen's own <style> block (one rule per line) ----
RULE_LINE = re.compile(r"^(?P<sel>[^{\n]+?)\s*\{(?P<body>[^}\n]*)\}\s*$", re.M)


def style_rules(html):
    block = re.search(r"<style>(.*?)</style>", html, re.S)
    start = block.start(1)
    for m in RULE_LINE.finditer(block.group(1)):
        decls = [d.strip() for d in m.group("body").split(";") if ":" in d]
        yield {"sel": m.group("sel").strip(), "decls": decls, "line": m.group(0), "abs": start + m.start()}


def replace_decl(html, rule, old_decl, new_decl):
    new_line = rule["line"].replace(old_decl, new_decl, 1)
    assert new_line != rule["line"]
    return html.replace(rule["line"], new_line, 1)


# ---- candidate generators: each yields (rule_id, target, html_after, description, original) ----

def cand_style(html, rng, v2=False):
    out = []
    for r in style_rules(html):
        for d in r["decls"]:
            prop, val = [x.strip() for x in d.split(":", 1)]
            # R1 raw / near-miss color
            if prop in ("color", "background", "background-color", "border-color") and COLOR_FULL.fullmatch(val):
                h = color_hex(resolve(val))
                if h:
                    out.append(("raw_color", "R1", r, d, f"{prop}: {h}", f"{prop} hard-coded as {h} instead of {val}"))
                    out.append(("near_color", "R1", r, d, f"{prop}: {jitter(h, rng)}", f"{prop} set to an off-palette hex near {val}"))
            # R2 spacing
            if prop in checks.SPACE_PROPS:
                toks = SPACE_VAR.findall(val)
                if toks:
                    name = rng.choice(toks)
                    n = px(f"var({name})")
                    opts = unambiguous(n, SCALE_PX | {0}) if isinstance(n, int) else []
                    if opts:
                        bad = rng.choice(opts)
                        nv = val.replace(f"var({name})", f"{bad}px", 1)
                        out.append(("off_space", "R2", r, d, f"{prop}: {nv}", f"{prop} uses {bad}px, off the spacing scale"))
            # R3 type
            if prop == "font-size" and "var(" in val:
                n = px(val)
                opts = unambiguous(n, TYPE_SCALE) if isinstance(n, int) and n else []
                if opts:
                    bad = rng.choice(opts)
                    out.append(("off_type", "R3", r, d, f"{prop}: {bad}px", f"font-size {bad}px instead of {val}"))
            # R4 radius
            if prop == "border-radius" and RADIUS_FULL and RADIUS_FULL.fullmatch(val):
                n = px(val)
                opts = unambiguous(n, RADIUS_SCALE) if isinstance(n, int) else []
                if opts:
                    bad = rng.choice(opts)
                    out.append(("off_radius", "R4", r, d, f"{prop}: {bad}px", f"border-radius {bad}px instead of {val}"))
            # R5 contrast and R7 semantics on text color
            if prop == "color" and val in (TEXT_DEFAULT, TEXT_MUTED):
                out.append(("low_contrast", "R5", r, d, f"{prop}: {TEXT_DISABLED}", "text uses the disabled color and fails contrast"))
            if prop == "color" and val == TEXT_MUTED:
                wrong = rng.choice(M["status_text"])
                out.append(("semantic_text", "R7", r, d, f"{prop}: {wrong}", f"secondary text colored {wrong}, which signals a status it doesn't have"))
            if not v2:
                continue
            # v2: valid tokens used where they fail (invisible to a token linter)
            if prop == "color" and val in (TEXT_DEFAULT, TEXT_MUTED, TEXT_LINK):
                bad = rng.choice(M["contrast_traps"])
                out.append(("token_contrast", "R5", r, d, f"{prop}: {bad}", f"text color set to {bad}, a real token that fails contrast here"))
            # v2: raw border width hidden inside a border shorthand
            if (prop in checks.BORDER_SHORTHANDS or prop == "border-width") and WIDTH_VAR and WIDTH_VAR.search(val):
                w = WIDTH_VAR.search(val).group(1)
                nv = val.replace(f"var({w})", fmt_px(px(f"var({w})")), 1)
                out.append(("raw_border_width", "R4", r, d, f"{prop}: {nv}", f"border width hard-coded instead of var({w})"))
            # v2: raw font weight
            if prop == "font-weight" and val.startswith(M["weight_prefix"]):
                out.append(("raw_weight", "R3", r, d, f"{prop}: {resolve(val)}", f"font-weight hard-coded as {resolve(val)} instead of {val}"))
    return [{"op": op, "rule": rule, "target": {"selector": r["sel"]}, "apply": (r, old, new), "desc": desc, "original": old}
            for op, rule, r, old, new, desc in out]


_TAGS = ["button", "a", "span"] + [t for t in BTN["tags"] + PILL["tags"] if t not in ("button", "a", "span")]
TAG_RE = re.compile(r"<(" + "|".join(_TAGS) + r")\b([^>]*)>")


DESTRUCTIVE = re.compile(M.get("destructive_words", r"delete|remove|revoke|cancel invite|archive|leave|transfer|disable|change visibility"), re.I)
SEMANTIC_LABELS = PILL["semantic"]


def inner_text(html, m):
    """Visible text inside the element opened by match m (nested tags stripped), up to its closing tag."""
    close = html.find(f"</{m.group(1)}>", m.end())
    inner = html[m.end():close if close >= 0 else None]
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", inner)).strip()


def cand_markup(html, clean_render, rng, v2=False, v3=False):
    out = []
    for m in TAG_RE.finditer(html):
        tag, attrs = m.group(1), m.group(2)
        cls = re.search(r'class="([^"]*)"', attrs)
        qa = re.search(r'data-qa="([^"]*)"', attrs)
        if not cls or not qa:
            continue
        classes, qa = cls.group(1).split(), qa.group(1)
        s = clean_render["styles"][qa]
        if tag in BTN["tags"] and BTN["base"] in classes:
            bw = s['border-top-width'] if v3 else "1px"
            look = (f"background: {s['background-color']}; color: {s['color']}; border: {bw} solid {s['border-top-color']}; "
                    f"border-radius: {s['border-top-left-radius']}; padding: {s['padding-top']} {s['padding-right']}; "
                    f"font-size: {s['font-size']}; font-weight: {s['font-weight']}")
            extra = [c for c in classes if not c.startswith(BTN["prefix"])]
            new_attrs = re.sub(r'class="[^"]*"', f'class="{" ".join(extra)}" style="{look}"' if extra else f'style="{look}"', attrs)
            out.append({"op": "rebuild_button", "rule": "R6", "target": {"qa": qa}, "apply": ("markup", m.group(0), f"<{tag}{new_attrs}>"),
                        "desc": f"button rebuilt by hand instead of using .{BTN['base']} ({' '.join(classes)})", "original": m.group(0)})
            text = inner_text(html, m)
            if v2 and BTN["danger"] not in classes and not set(BTN["never_danger"]) & set(classes) and not DESTRUCTIVE.search(text):
                swap = next((c for c in BTN["swap_to_danger"] if c in classes), None)
                new_tag = m.group(0).replace(swap, BTN["danger"]) if swap else \
                    m.group(0).replace(f'class="{BTN["base"]}', f'class="{BTN["base"]} {BTN["danger"]}', 1)
                out.append({"op": "danger_safe", "rule": "R7", "target": {"qa": qa}, "apply": ("markup", m.group(0), new_tag),
                            "desc": f"safe action \"{text}\" styled as a danger button", "original": m.group(0)})
            if BTN["danger"] in classes:
                out.append({"op": "destructive_primary", "rule": "R7", "target": {"qa": qa},
                            "apply": ("markup", m.group(0), m.group(0).replace(BTN["danger"], BTN["primary"])),
                            "desc": f"destructive action styled as {BTN['primary_desc']}", "original": m.group(0)})
        if tag in PILL["tags"] and PILL["base"] in classes:
            look = (f"display: inline-block; padding: 0 {s['padding-right']}; font-size: {s['font-size']}; font-weight: {s['font-weight']}; "
                    f"color: {s['color']}; border: 1px solid {s['border-top-color']}; border-radius: 999px")
            extra = [c for c in classes if not c.startswith(PILL["prefix"])]
            new_attrs = re.sub(r'class="[^"]*"', f'class="{" ".join(extra)}" style="{look}"' if extra else f'style="{look}"', attrs)
            out.append({"op": "rebuild_label", "rule": "R6", "target": {"qa": qa}, "apply": ("markup", m.group(0), f"<{tag}{new_attrs}>"),
                        "desc": f"status pill rebuilt by hand instead of using .{PILL['base']} ({' '.join(classes)})", "original": m.group(0)})
            pairs = [(g, b) for g in SEMANTIC_LABELS for b in SEMANTIC_LABELS if g != b] if v2 else \
                [tuple(p) for p in PILL.get("v1_pairs", [])]
            pairs = [p for p in pairs if p[0] in classes]
            if pairs:
                good, bad = rng.choice(pairs) if v2 else pairs[0]  # v1 path draws nothing, so v1 tasks stay reproducible
                out.append({"op": "semantic_label", "rule": "R7", "target": {"qa": qa},
                            "apply": ("markup", m.group(0), m.group(0).replace(good, bad)),
                            "desc": f"status pill uses {bad}, which contradicts what it reports", "original": m.group(0)})
    return out


def apply(html, cand):
    a = cand["apply"]
    if a[0] == "markup":
        assert html.count(a[1]) == 1
        return html.replace(a[1], a[2], 1)
    r, old, new = a
    rule = next(x for x in style_rules(html) if x["sel"] == r["sel"])
    return replace_decl(html, rule, old, new)


def elements_for(html_path, target):
    """data-qa ids a planted problem touches. A markup target includes the component's own tagged children
    (a Spectrum button's -label span, a badge's -label div), since rebuilding or recoloring the component
    changes them too. Primer's components have no tagged children, so its tasks are unchanged."""
    page = checks._page()
    if "qa" in target:
        page.goto(Path(html_path).resolve().as_uri())
        kids = page.evaluate("(q) => { const el = document.querySelector(`[data-qa=\"${q}\"]`); "
                             "return el ? Array.from(el.querySelectorAll('[data-qa]')).map(e => e.dataset.qa) : []; }", target["qa"])
        page.close()
        return [target["qa"]] + kids
    page.goto(Path(html_path).resolve().as_uri())
    ids = page.evaluate("(s) => Array.from(document.querySelectorAll(s)).map(e => e.dataset.qa).filter(Boolean)", target["selector"])
    page.close()
    return ids


def build(seed=11, version=1, interleave=False, variants_per_split=None, clean_per_split=None):
    """version 1/2 pick the mutation set. interleave=True splits screens odd/even instead of 01-07 / 08-12."""
    v2 = version >= 2
    rng = random.Random(seed)
    screens = sorted(system.SCREENS.glob("*.html"))
    if interleave:
        train_screens = [s for s in screens if int(s.name[:2]) % 2 == 1]
        held_screens = [s for s in screens if int(s.name[:2]) % 2 == 0]
    else:
        train_screens = [s for s in screens if int(s.name[:2]) <= 7]
        held_screens = [s for s in screens if int(s.name[:2]) > 7]
    variants_per_split = variants_per_split or {"train": 3, "heldout": 3}
    clean_per_split = clean_per_split or {"train": 3, "heldout": 1}
    tasks_dir = system.TASKS
    if tasks_dir.exists():
        shutil.rmtree(tasks_dir)
    tasks_dir.mkdir()
    plan = [(s, "train") for s in train_screens] + [(s, "heldout") for s in held_screens]
    clean_controls = {"train": rng.sample(train_screens, clean_per_split["train"]),
                      "heldout": rng.sample(held_screens, clean_per_split["heldout"])}
    split = {"train": [], "heldout": []}
    n = 0
    for screen, part in plan:
        clean_html = screen.read_text()
        clean_render = checks.render(screen)
        variants = variants_per_split[part]
        specs = [None] * variants + ([0] if screen in clean_controls[part] else [])
        for v, spec in enumerate(specs):
            n += 1
            tid = f"t{n:02d}-{screen.stem[3:]}"
            tdir = tasks_dir / tid
            tdir.mkdir()
            html, truth, used_rules, used_targets = clean_html, [], set(), set()
            if spec is None:
                want = rng.choice([4, 5, 5, 6]) if v2 else rng.choice([2, 3, 3, 4])
                for _ in range(60):
                    if len(truth) >= want:
                        break
                    cands = cand_style(html, rng, v2) + cand_markup(html, clean_render, rng, v2)
                    cap = 2 if v2 else 1
                    cands = [c for c in cands if sum(1 for t in truth if t["rule"] == c["rule"]) < cap
                             and json.dumps(c["target"]) not in used_targets and c["original"] in html]
                    if not cands:
                        break
                    c = rng.choice(cands)
                    try:
                        after = apply(html, c)
                    except AssertionError:
                        continue
                    if c["op"] in ("low_contrast", "token_contrast"):
                        # keep it only if the text really fails contrast (large text passes at 3:1)
                        probe = tdir / "_probe.html"
                        probe.write_text(after)
                        failing = {x["qa"] for x in checks.render(probe)["contrast_failures"]}
                        probe.unlink()
                        if not failing & set(elements_for(screen, c["target"])):
                            used_targets.add(json.dumps(c["target"]))
                            continue
                    html = after
                    used_rules.add(c["rule"]); used_targets.add(json.dumps(c["target"]))
                    truth.append({"id": f"m{len(truth)+1}", "op": c["op"], "rule": c["rule"], "target": c["target"],
                                  "description": c["desc"], "original": c["original"],
                                  "mutated": c["apply"][2] if c["apply"][0] == "markup" else c["apply"][2]})
            (tdir / "input.html").write_text(html)
            (tdir / "clean.html").write_text(clean_html)
            for t in truth:
                t["elements"] = elements_for(screen, t["target"])
            meta = {"task": tid, "screen": screen.name, "split": part, "clean_control": spec == 0, "mutations": truth}
            (tdir / "truth.json").write_text(json.dumps(meta, indent=2))
            split[part].append(tid)
    system.SPLITS.write_text(json.dumps(split, indent=2))
    return split


TEXT_COLORS = (TEXT_DEFAULT, TEXT_MUTED)


def rgb_of(token):
    h = color_hex(resolve(token))
    return f"rgb({int(h[1:3], 16)}, {int(h[3:5], 16)}, {int(h[5:7], 16)})"


def compose(screens):
    """One long page from several screens: styles merged (selectors are unique across screens),
    bodies stacked, data-qa / id / for prefixed with the screen name so nothing collides."""
    first = screens[0].read_text()
    head = first[:first.index("<style>")]
    titles, styles, bodies = [], [], []
    for scr in screens:
        h = scr.read_text()
        stem = scr.stem[3:]
        titles.append(re.search(r"<title>(.*?)</title>", h).group(1))
        styles.append(re.search(r"<style>\n?(.*?)\n?</style>", h, re.S).group(1))
        body = re.search(r"<body[^>]*>\n?(.*?)\n?</body>", h, re.S).group(1)
        body = re.sub(r'data-qa="([^"]+)"', lambda m: f'data-qa="{stem}-{m.group(1)}"', body)
        body = re.sub(r'\b(id|for)="([^"]+)"', lambda m: f'{m.group(1)}="{stem}-{m.group(2)}"', body)
        bodies.append(f"<section>\n{body}\n</section>")
    head = re.sub(r"<title>.*?</title>", f"<title>{' · '.join(titles)}</title>", head)
    body_tag = re.search(r"<body[^>]*>", first).group(0)
    return head + "<style>\n" + "\n".join(styles) + "\n</style>\n</head>\n" + body_tag + "\n" + "\n".join(bodies) + "\n</body>\n</html>\n"


def build_v3(seed=11, per_page=3, tasks_per_split=None, clean_per_split=None, want_range=(6, 9)):
    """v3: long pages (three screens each), 6-9 planted problems, interleaved split (odd screens train, even held-out)."""
    rng = random.Random(seed)
    screens = sorted(system.SCREENS.glob("*.html"))
    pools = {"train": [s for s in screens if int(s.name[:2]) % 2 == 1],
             "heldout": [s for s in screens if int(s.name[:2]) % 2 == 0]}
    tasks_per_split = tasks_per_split or {"train": 24, "heldout": 16}
    clean_per_split = clean_per_split or {"train": 2, "heldout": 2}
    tasks_dir = system.TASKS
    if tasks_dir.exists():
        shutil.rmtree(tasks_dir)
    tasks_dir.mkdir()
    split = {"train": [], "heldout": []}
    n = 0
    for part in ("train", "heldout"):
        total = tasks_per_split[part] + clean_per_split[part]
        clean_slots = set(rng.sample(range(total), clean_per_split[part]))
        for k in range(total):
            n += 1
            group = sorted(rng.sample(pools[part], per_page))
            tid = f"t{n:02d}-" + "-".join(g.name[:2] for g in group)
            tdir = tasks_dir / tid
            tdir.mkdir()
            clean_html = compose(group)
            (tdir / "clean.html").write_text(clean_html)
            clean_path = tdir / "clean.html"
            clean_render = checks.render(clean_path)
            html, truth, used_targets = clean_html, [], set()
            if k not in clean_slots:
                want = rng.randint(*want_range)
                for _ in range(120):
                    if len(truth) >= want:
                        break
                    cands = cand_style(html, rng, True) + cand_markup(html, clean_render, rng, True, True)
                    cands = [c for c in cands if sum(1 for t in truth if t["rule"] == c["rule"]) < 2
                             and json.dumps(c["target"]) not in used_targets and c["original"] in html]
                    if not cands:
                        break
                    c = rng.choice(cands)
                    try:
                        after = apply(html, c)
                    except AssertionError:
                        continue
                    if c["op"] in ("low_contrast", "token_contrast"):
                        probe = tdir / "_probe.html"
                        probe.write_text(after)
                        failing = {x["qa"] for x in checks.render(probe)["contrast_failures"]}
                        probe.unlink()
                        if not failing & set(elements_for(clean_path, c["target"])):
                            used_targets.add(json.dumps(c["target"]))
                            continue
                    html = after
                    used_targets.add(json.dumps(c["target"]))
                    t = {"id": f"m{len(truth)+1}", "op": c["op"], "rule": c["rule"], "target": c["target"],
                         "description": c["desc"], "original": c["original"], "mutated": c["apply"][2]}
                    # R5 asks for readable text; primary vs secondary text color is a hierarchy call the rules
                    # don't pin down, so either text token counts as a correct fix.
                    if c["op"] in ("low_contrast", "token_contrast") and any(tc in c["original"] for tc in TEXT_COLORS):
                        t["accept_colors"] = [rgb_of(tc) for tc in TEXT_COLORS]
                    truth.append(t)
            (tdir / "input.html").write_text(html)
            for t in truth:
                t["elements"] = elements_for(clean_path, t["target"])
            meta = {"task": tid, "screen": [g.name for g in group], "split": part, "clean_control": k in clean_slots,
                    "mutations": truth}
            (tdir / "truth.json").write_text(json.dumps(meta, indent=2))
            split[part].append(tid)
    system.SPLITS.write_text(json.dumps(split, indent=2))
    return split


if __name__ == "__main__":
    s = build()
    print({k: len(v) for k, v in s.items()})
