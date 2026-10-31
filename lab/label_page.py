"""Build the blind-labeling page for judge calibration.

python3 lab/label_page.py <run> <n> --out <page.html>

Picks n train runs (a mix of strict passes, strict fails and clean controls, seeded), and writes:
- the page, with only what a reviewer needs: screenshots, planted problems, the code change,
  the agent's report. No code-grader result, no judge verdict.
- lab/calibration/cases_key.json mapping opaque case ids back to task and run (kept out of the page).
"""

import argparse, base64, difflib, io, json, random, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import checks
import describe
from report import load_run

import system

LAB = system.LAB
_tok = lambda v: v[len('var(--'):-1]  # 'var(--x)' -> 'x'
CAL = LAB / "lab" / "calibration"
TEMPLATE = LAB / "lab" / "label_template.html"


def pick(run, n, seed=7):
    rows = [r for r in load_run(run)]
    rng = random.Random(seed)
    for r in rows:
        r["_clean"] = json.loads((system.TASKS / r["task"] / "truth.json").read_text())["clean_control"]
    fails = [r for r in rows if not r["pass"] and not r["_clean"]]
    passes = [r for r in rows if r["pass"] and not r["_clean"]]
    clean = [r for r in rows if r["_clean"]]
    n_clean = min(2, len(clean))
    n_pass = min(len(passes), round((n - n_clean) * 0.4))
    n_fail = min(len(fails), n - n_clean - n_pass)
    chosen, seen = [], set()

    def take(pool, k):
        pool = pool[:]
        rng.shuffle(pool)
        # prefer different tasks so one screen doesn't dominate
        pool.sort(key=lambda r: r["task"] in seen)
        for r in pool[:k]:
            chosen.append(r)
            seen.add(r["task"])

    take(fails, n_fail)
    take(passes, n_pass)
    take(clean, n_clean)
    rng.shuffle(chosen)
    return chosen


SNAP_JS = r"""
(boxyClasses) => {
  const BOXY = new RegExp("\\b(" + boxyClasses.join("|") + ")\\b");
  const out = {};
  for (const el of document.querySelectorAll('[data-qa]')) {
    let r = el.getBoundingClientRect();
    const cls = el.getAttribute('class') || '';
    const boxy = ['BUTTON', 'INPUT', 'TEXTAREA', 'SELECT', 'IMG'].includes(el.tagName) || BOXY.test(cls) || el.getAttribute('style');
    if (!boxy && el.children.length <= 2) {
      const rg = document.createRange(); rg.selectNodeContents(el); const t = rg.getBoundingClientRect();
      if (t.width > 0 && t.height > 0) r = t;
    }
    const own = Array.from(el.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent).join(' ').replace(/\s+/g, ' ').trim();
    out[el.dataset.qa] = {tag: el.tagName.toLowerCase(), class: el.getAttribute('class') || '', style: el.getAttribute('style') || '',
      text: own || (el.children.length <= 2 ? el.textContent.replace(/\s+/g, ' ').trim() : ''), rect: [r.x, r.y, r.width, r.height]};
  }
  return out;
}
"""


def snapshot(html_path, png=None):
    """DOM facts per data-qa element, contrast per element, and optionally a full-page screenshot."""
    data = checks.render(html_path, screenshot=png)
    page = checks._page()
    page.goto(Path(html_path).resolve().as_uri())
    page.wait_for_load_state("load")
    els = page.evaluate(SNAP_JS, system.CFG.get("labels", {}).get("boxy_classes", [system.COMPONENTS["button"]["base"], system.COMPONENTS["pill"]["base"]]))
    page.close()
    return {"els": els, "contrast": {c["qa"]: c for c in data["contrast"]}}


def select(html_path, selector):
    page = checks._page()
    page.goto(Path(html_path).resolve().as_uri())
    try:
        ids = page.evaluate("(s) => Array.from(document.querySelectorAll(s)).map(e => e.dataset.qa).filter(Boolean)", selector)
    except Exception:
        ids = []
    page.close()
    return ids


def crop_box(paths, margin=24):
    from PIL import Image, ImageChops
    box = None
    for p in paths:
        im = Image.open(p).convert("RGB")
        bg = Image.new("RGB", im.size, im.getpixel((2, 2)))
        b = ImageChops.difference(im, bg).getbbox() or (0, 0) + im.size
        box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3]))
    w, h = Image.open(paths[0]).size
    return (max(0, box[0] - margin), max(0, box[1] - margin), min(w, box[2] + margin), min(h, box[3] + margin))


def data_uri(path, box):
    from PIL import Image
    im = Image.open(path).convert("RGB").crop(box).quantize(colors=128, method=Image.Quantize.MEDIANCUT)
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def changes(before, after):
    out = []
    for l in difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="", n=0):
        if l.startswith(("+++", "---", "@@")):
            continue
        out.append(l.strip() if l[0] in "+-" else l)
    return [l[0] + " " + l[1:].strip() for l in out]


STYLE_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}")


def css_rules(html):
    rules = {}
    for block in STYLE_RE.findall(html):
        block = re.sub(r"/\*.*?\*/", "", block, flags=re.S)
        for sel, body in RULE_RE.findall(block):
            decls = {}
            for part in body.split(";"):
                if ":" in part:
                    k, v = part.split(":", 1)
                    decls[k.strip().lower()] = v.strip()
            rules[" ".join(sel.split())] = decls
    return rules


def crop(png, rect, pad=12, max_h=200, max_w=640):
    from PIL import Image
    im = Image.open(png).convert("RGB")
    x, y, w, h = rect
    box = (max(0, int(x - pad)), max(0, int(y - pad)), min(im.width, int(x + w + pad)), min(im.height, int(y + min(h, max_h) + pad)))
    if box[2] - box[0] < 8 or box[3] - box[1] < 8:
        return None
    c = im.crop(box)
    if c.width > max_w:
        c = c.resize((max_w, max(1, int(c.height * max_w / c.width))))
    c = c.quantize(colors=96, method=Image.Quantize.MEDIANCUT)
    buf = io.BytesIO()
    c.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def crops_for(qa, shots):
    out = {}
    for k, (png, snap) in shots.items():
        el = snap["els"].get(qa)
        out[k] = crop(png, el["rect"]) if el and el["rect"][2] > 0 and el["rect"][3] > 0 else None
    return out


def ratio(snap, qa):
    c = snap["contrast"].get(qa)
    return f"{c['ratio']}:1" if c else None


PLAIN = {
    "raw_color": "{prop} is a hard-coded color instead of a token.",
    "near_color": "{prop} is an off-palette color, a near miss of a token.",
    "off_space": "{prop} uses a value that isn't on the spacing scale.",
    "off_type": "Text size isn't on the type scale.",
    "off_radius": "Corner radius isn't on the scale.",
    "raw_border_width": "Border width is hard-coded instead of the border token.",
    "raw_weight": "Font weight is hard-coded instead of the weight token.",
    "low_contrast": "Text uses Disabled gray and is too faint to read.",
    "token_contrast": "Text uses a real token that's unreadable on this background.",
    "semantic_text": "Plain secondary text is colored like a status, which signals something it isn't.",
    "semantic_label": "Status pill color contradicts what the pill says.",
    "destructive_primary": "A destructive action is styled as the green primary button.",
    "danger_safe": "A safe action is styled as a red danger button.",
    "rebuild_button": "Button is hand-built with inline styles instead of the Button component.",
    "rebuild_label": "Status pill is hand-built with inline styles instead of the Status pill component.",
}
CODE_ONLY = {"raw_color", "raw_border_width", "raw_weight"}


def build_case(cid, row, work):
    task_dir = system.TASKS / row["task"]
    run_dir = Path(row["_dir"])
    truth = json.loads((task_dir / "truth.json").read_text())
    clean_png, input_png, out_png = work / f"{row['task']}-clean.png", work / f"{row['task']}-input.png", run_dir / "fixed.png"
    snaps = {"design": snapshot(task_dir / "clean.html", clean_png), "received": snapshot(task_dir / "input.html", input_png),
             "shipped": snapshot(run_dir / "fixed.html", out_png)}
    shots = {k: ({"design": clean_png, "received": input_png, "shipped": out_png}[k], v) for k, v in snaps.items()}
    rin, rout = snaps["received"]["els"], snaps["shipped"]["els"]
    name = lambda qa: describe.element_name(qa, rin.get(qa) or rout.get(qa) or {})

    # ---- what the agent changed, per element, in design terms ----
    in_html, out_html = (task_dir / "input.html").read_text(), (run_dir / "fixed.html").read_text()
    a, b = css_rules(in_html), css_rules(out_html)
    groups = []  # {"els": [...], "items": [{what, from, to}]}
    for sel in list(a) + [x for x in b if x not in a]:
        da, db = a.get(sel, {}), b.get(sel, {})
        if da == db:
            continue
        items = []
        for prop in list(da) + [x for x in db if x not in da]:
            va, vb = da.get(prop), db.get(prop)
            if va == vb:
                continue
            label = describe.PROP_LABEL.get(prop, prop)
            items.append({"what": label, "from": describe.value_html(prop, va) if va else "<em>not set</em>",
                          "to": describe.value_html(prop, vb) if vb else "<em>removed</em>"})
        els = select(task_dir / "input.html", sel) or select(run_dir / "fixed.html", sel)
        groups.append({"els": els, "items": items, "src": sel})
    for qa in list(rin) + [x for x in rout if x not in rin]:
        ea, eb = rin.get(qa), rout.get(qa)
        if not ea or not eb:
            groups.append({"els": [qa], "items": [{"what": "Element", "from": "present" if ea else "<em>missing</em>",
                                                  "to": "<em>removed</em>" if ea else "added"}], "src": qa})
            continue
        items = []
        if ea["class"] != eb["class"] or bool(ea["style"]) != bool(eb["style"]):
            fa, fb = describe.component_html(ea["class"], ea["style"]), describe.component_html(eb["class"], eb["style"])
            if fa != fb:
                items.append({"what": "Component", "from": fa, "to": fb})
        if ea["style"] != eb["style"] and ea["style"] and eb["style"]:
            items.append({"what": "Inline style", "from": describe.value_html("", ea["style"]), "to": describe.value_html("", eb["style"])})
        if ea["text"] != eb["text"] and ea["tag"] == eb["tag"]:
            items.append({"what": "Text", "from": describe.esc(ea["text"][:80]), "to": describe.esc(eb["text"][:80])})
        if items:
            groups.append({"els": [qa], "items": items, "src": qa})

    planted_els = set()
    problems = []
    box = crop_box([clean_png, input_png, out_png])
    bw, bh = box[2] - box[0], box[3] - box[1]
    for i, m in enumerate(truth["mutations"], 1):
        els = [e for e in m["elements"] if e in rin]
        planted_els |= set(m["elements"])
        prop, _, oval = m["original"].partition(":") if not m["original"].startswith("<") else ("", "", "")
        prop = prop.strip()
        if m["original"].startswith("<"):
            cls = re.search(r'class="([^"]*)"', m["original"])
            intended = describe.component_html(cls.group(1) if cls else "", "")
        elif m.get("accept_colors"):
            intended = f'{describe.PROP_LABEL.get(prop, prop)}: {describe.token_label(_tok(system.MUTATE["text_default"]))} or {describe.token_label(_tok(system.MUTATE["text_muted"]))}'
        else:
            intended = f'{describe.PROP_LABEL.get(prop, prop)}: {describe.value_html(prop, oval.strip())}'
        did = [it for g in groups if set(g["els"]) & set(m["elements"]) for it in g["items"]]
        first = els[0] if els else (m["elements"][0] if m["elements"] else None)
        contrast = None
        if m["rule"] == "R5" and first:
            contrast = {"received": ratio(snaps["received"], first), "shipped": ratio(snaps["shipped"], first)}
        rects = [rin[e]["rect"] for e in els]
        problems.append({
            "n": i, "rule": m["rule"],
            "where": (name(first) + (f" (and {len(els) - 1} more)" if len(els) > 1 else "")) if first else "",
            "title": PLAIN.get(m["op"], m["description"]).format(prop=describe.PROP_LABEL.get(prop, "Style")),
            "code_only": m["op"] in CODE_ONLY, "intended": intended, "did": did, "contrast": contrast,
            "crops": crops_for(first, shots) if first else {},
            "marks": [[round((x - box[0]) / bw * 100, 2), round((y - box[1]) / bh * 100, 2), round(w / bw * 100, 2), round(h / bh * 100, 2)]
                      for x, y, w, h in rects]})

    others = []
    for g in groups:
        if set(g["els"]) & planted_els or not g["items"]:
            continue
        first = g["els"][0] if g["els"] else None
        others.append({"where": (name(first) + (f" (and {len(g['els']) - 1} more)" if len(g["els"]) > 1 else "")) if first
                       else f"Style rule {g['src']}", "items": g["items"],
                       "crops": {k: v for k, v in crops_for(first, shots).items() if k != "design"} if first else {}})

    try:
        rep = json.loads((run_dir / "findings.json").read_text())
    except Exception:
        rep = {"findings": [], "self_assessment": None, "missing": True}
    report = []
    for f in rep.get("findings", []) if isinstance(rep, dict) else []:
        ref = str(f.get("element", ""))
        ids = [ref] if ref in rin else (select(task_dir / "input.html", ref) if re.match(r"^[.#\[a-zA-Z]", ref) else [])
        if not ids:
            ids = [q for q in rin if re.search(r"(?<![\w-])" + re.escape(q) + r"(?![\w-])", ref + " " + str(f.get("problem", "")))][:3]
        actual = [it for g in groups if set(g["els"]) & set(ids) for it in g["items"]]
        about = [pr["n"] for pr, m in zip(problems, truth["mutations"]) if set(m["elements"]) & set(ids)]
        report.append({"where": (name(ids[0]) + (f" (and {len(ids) - 1} more)" if len(ids) > 1 else "")) if ids else ref,
                       "rule": str(f.get("rule", "")), "problem": describe.value_html("", str(f.get("problem", ""))[:400]),
                       "fix": describe.value_html("", str(f.get("fix", ""))[:400]), "actual": actual, "found": bool(ids),
                       "about": about})
    mentioned = {n for f in report for n in f["about"]}
    check = {"planted": len(problems),
             "missing": [{"n": pr["n"], "where": pr["where"]} for pr in problems if pr["n"] not in mentioned],
             "no_change": [f["where"] for f in report if f["found"] and not f["actual"]],
             "extra": [f["where"] for f in report if not f["about"]]}
    title = re.search(r"<title>(.*?)</title>", (task_dir / "clean.html").read_text()).group(1)
    return {"check": check,
        "id": cid, "screen": title, "clean_control": truth["clean_control"], "problems": problems, "others": others,
        "code": changes(in_html, out_html), "report": report,
        "self": rep.get("self_assessment") if isinstance(rep, dict) else None, "report_missing": bool(rep.get("missing")) if isinstance(rep, dict) else True,
        "img": {"design": data_uri(clean_png, box), "received": data_uri(input_png, box), "output": data_uri(out_png, box)},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("n", type=int)
    ap.add_argument("--out", required=True)
    ap.add_argument("--reuse-key", action="store_true", help="rebuild the same cases, same ids")
    a = ap.parse_args()
    CAL.mkdir(parents=True, exist_ok=True)
    work = CAL / "png"
    work.mkdir(exist_ok=True)
    keyf = CAL / "cases_key.json"
    if a.reuse_key and keyf.exists():
        old = json.loads(keyf.read_text())
        rows = []
        for cid, v in old.items():
            g = json.loads((Path(v["run_dir"]) / "grade.json").read_text())
            g["_dir"] = v["run_dir"]
            rows.append(g)
    else:
        rows = pick(a.run, a.n)
    cases, key = [], {}
    for i, r in enumerate(rows, 1):
        cid = f"c{i:02d}"
        if (system.TASKS / r["task"] / "truth.json").exists() and json.loads((system.TASKS / r["task"] / "truth.json").read_text())["split"] != "train":
            raise SystemExit("calibration cases must come from train")
        cases.append(build_case(cid, r, work))
        key[cid] = {"task": r["task"], "run_dir": r["_dir"], "strict_pass": r["pass"]}
    (CAL / "cases_key.json").write_text(json.dumps(key, indent=2))
    page = TEMPLATE.read_text().replace("/*CASES*/[]", json.dumps(cases))
    Path(a.out).write_text(page)
    print(f"{len(cases)} cases, page {len(page)//1024} KB, strict passes in sample: {sum(v['strict_pass'] for v in key.values())}")


if __name__ == "__main__":
    main()
