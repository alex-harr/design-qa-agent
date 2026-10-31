"""Check every seeded task: each planted problem is visible to at least one grader, and nothing else changed."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import checks
import system
problems = 0
for tdir in sorted(p for p in system.TASKS.iterdir() if p.is_dir()):
    meta = json.loads((tdir / "truth.json").read_text())
    clean = checks.render(tdir / "clean.html"); mut = checks.render(tdir / "input.html")
    lint = checks.lint_source((tdir / "input.html").read_text())
    diffs = checks.compare(clean, mut)
    touched = {e for m in meta["mutations"] for e in m["elements"]}
    notes = []
    for m in meta["mutations"]:
        els = set(m["elements"])
        by_lint = any(any(f'"{e}"' in l["where"] for e in els) or l["where"] == m["target"].get("selector") for l in lint)
        by_contrast = any(c["qa"] in els for c in mut["contrast_failures"])
        by_diff = any(e in diffs for e in els)
        visible = {"R1": by_lint, "R2": by_lint, "R3": by_lint, "R4": by_lint, "R5": by_contrast, "R6": by_lint, "R7": by_diff}[m["rule"]]
        if not visible or not els:
            notes.append(f"{m['id']} {m['op']} not visible (lint={by_lint} contrast={by_contrast} diff={by_diff} els={len(els)})")
    stray = [q for q in diffs if q not in touched]
    # children can inherit color changes; allow stray diffs only in inherited props
    stray = [q for q in stray if set(diffs[q]) - {"color", "border-top-color", "border-right-color", "border-bottom-color", "border-left-color", "text-decoration-line", "font-size", "font-weight", "line-height"}]
    if stray: notes.append(f"unexpected style changes: {stray}")
    if meta["clean_control"] and (diffs or lint): notes.append("clean control is not clean")
    problems += bool(notes)
    print(f"{meta['task']:28s} {meta['split']:8s} {'CLEAN' if meta['clean_control'] else ', '.join(m['op'] for m in meta['mutations']):60s} {'; '.join(notes) or 'ok'}")
print("tasks with problems:", problems)
