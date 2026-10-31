"""Code grader: score one agent output against a task's ground truth.

Pass/fail is strict on purpose: every planted problem fixed back to the design system's
intended value, nothing else changed, no rule violations left. The LLM judge (judge.py)
handles the cases where a different fix might still be acceptable.
"""

import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import checks
import system  # noqa: F401  (selects the design system for checks)

INHERITED = {"color", "font-size", "font-weight", "line-height", "text-decoration-line"}
COLORISH = {"color", "border-top-color", "border-right-color", "border-bottom-color", "border-left-color"}


def _mentions(text, ids, selector):
    text = text or ""
    # a selector counts only as a whole name: ".note" must not match inside ".note-dot"
    if selector and selector.strip() and re.search(re.escape(selector.strip()) + r"(?![\w-])", text):
        return True
    return any(re.search(r'(?<![\w-])' + re.escape(i) + r'(?![\w-])', text) for i in ids)


def load_findings(path):
    try:
        data = json.loads(Path(path).read_text())
    except Exception:
        return [], None, "findings.json missing or invalid"
    items = data.get("findings", []) if isinstance(data, dict) else data
    items = [f for f in items if isinstance(f, dict)]
    return items, (data.get("self_assessment") if isinstance(data, dict) else None), None


def grade(task_dir, fixed_html, findings_json, screenshot=None):
    task_dir = Path(task_dir)
    meta = json.loads((task_dir / "truth.json").read_text())
    clean_r = checks.render(task_dir / "clean.html")
    fixed_path = Path(fixed_html)
    if not fixed_path.exists():
        return {"task": meta["task"], "error": "no output screen", "pass": False}
    out_r = checks.render(fixed_path, screenshot=screenshot)
    lint = checks.lint_source(fixed_path.read_text())
    diffs = checks.compare(clean_r, out_r)
    findings, self_assessment, findings_error = load_findings(findings_json)

    touched = {e for m in meta["mutations"] for e in m["elements"]}
    results = []
    for m in meta["mutations"]:
        els, sel = set(m["elements"]), m["target"].get("selector")
        detected = any(_mentions(f.get("element", "") + " " + f.get("problem", ""), els, sel) for f in findings)
        lint_left = [l for l in lint if (sel and l["where"] == sel) or any(f'"{e}"' in l["where"] for e in els)]
        contrast_left = [c for c in out_r["contrast_failures"] if c["qa"] in els]
        style_left = {e: diffs[e] for e in els if e in diffs}
        if m.get("accept_colors"):
            # either text token is a correct contrast fix (see mutate.build_v3)
            style_left = {e: d for e, d in style_left.items()
                          if not (set(d) <= COLORISH and d.get("color", [None, None])[1] in m["accept_colors"])}
        results.append({"id": m["id"], "op": m["op"], "rule": m["rule"], "detected": detected,
                        "fixed": not (lint_left or contrast_left or style_left),
                        "left": {"lint": lint_left, "contrast": contrast_left, "style": style_left}})

    def is_regression(qa):
        d = diffs[qa]
        if d.get("__missing") or d.get("__added"):
            return True
        anc = set(out_r["styles"].get(qa, {}).get("__ancestors", []))
        if anc & touched and set(d) <= INHERITED:
            return False
        return True

    regressions = {q: diffs[q] for q in diffs if q not in touched and is_regression(q)}
    false_flags = [f for f in findings
                   if not any(_mentions(f.get("element", "") + " " + f.get("problem", ""), set(m["elements"]), m["target"].get("selector"))
                              for m in meta["mutations"])]
    n = len(results)
    all_fixed = all(r["fixed"] for r in results)
    passed = all_fixed and not regressions and not lint and not out_r["contrast_failures"]
    if meta["clean_control"]:
        passed = passed and not false_flags  # a clean screen should come back unflagged and unchanged
    return {
        "task": meta["task"], "split": meta["split"], "clean_control": meta["clean_control"],
        "pass": passed,
        "planted": n, "detected": sum(r["detected"] for r in results), "fixed": sum(r["fixed"] for r in results),
        "false_flags": len(false_flags), "regressions": len(regressions),
        "lint_left": len(lint), "contrast_left": len(out_r["contrast_failures"]),
        "mutations": results, "regression_detail": regressions, "false_flag_detail": false_flags[:10],
        "self_assessment": self_assessment, "findings_error": findings_error,
    }


if __name__ == "__main__":
    t, html, fj = sys.argv[1:4]
    print(json.dumps(grade(t, html, fj), indent=2)[:4000])
