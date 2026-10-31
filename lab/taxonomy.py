"""Failure taxonomy for the QA agent, counted on a run.

The categories were open-coded by hand from the first Haiku 4.5 train runs (see LOG.md, error analysis).
This script only counts them on later runs so every loop round gets the same lens.

python3 lab/taxonomy.py <run> [<run> ...] [--out file.md]
"""

import argparse, json, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from report import load_run

import system

LAB = system.LAB

MEANING_OPS = {"semantic_text", "destructive_primary", "danger_safe", "semantic_label"}
READABILITY_OPS = {"low_contrast", "token_contrast"}

CATEGORIES = {
    "T1 Meaning not checked": "A real token or class carries the wrong meaning and the agent never flags it: status color on plain secondary text, a destructive action in primary green, a safe action in danger red, a status pill showing the wrong status. These pass any token check; only reading what the element says catches them (R7).",
    "T2 Readability not checked": "A real token makes text unreadable and the agent never flags it: the disabled color on body text, a border color used as text, white text on a light surface. Token names look fine; only checking contrast catches them (R5).",
    "T3 Incomplete sweep": "A raw, off-scale value is left in place and never reported, usually in the page's own layout rules (container margins, gaps, weights) rather than in components (R1-R4).",
    "T4 Wrong fix": "The agent found the problem but fixed it to the wrong value or variant: an off-scale number rounded to the wrong step, a rebuilt component restored with the wrong variant or size.",
    "T5 False alarm": "The agent flags something the rules allow and often changes it, which breaks what was fine (shows up as regressions).",
    "T6 Overconfident report": "The report says everything is fixed when it isn't.",
}


def count(runs):
    c = Counter()
    ex = defaultdict(list)
    n = 0
    for run in runs:
        for r in load_run(run):
            n += 1
            truth = {m["id"]: m for m in json.loads((system.TASKS / r["task"] / "truth.json").read_text())["mutations"]}
            for m in r["mutations"]:
                t = truth[m["id"]]
                if m["fixed"]:
                    continue
                if not m["detected"]:
                    cat = "T1 Meaning not checked" if t["op"] in MEANING_OPS else \
                        "T2 Readability not checked" if t["op"] in READABILITY_OPS else "T3 Incomplete sweep"
                else:
                    cat = "T4 Wrong fix"
                c[cat] += 1
                ex[cat].append(f"{t['description']} (intended `{t['original'][:70]}`)")
            for f in r.get("false_flag_detail") or []:
                c["T5 False alarm"] += 1
                ex["T5 False alarm"].append(f"flagged {str(f.get('element'))[:40]} as {f.get('rule')}: {str(f.get('problem'))[:140]}")
            sa = r.get("self_assessment") or {}
            if sa.get("all_fixed") and not r["pass"]:
                c["T6 Overconfident report"] += 1
    return n, c, ex


def render(runs):
    n, c, ex = count(runs)
    lines = [f"# Failure taxonomy on {', '.join(runs)} ({n} runs)", "",
             "Counts are planted problems not fixed (T1-T4), false flags (T5), and runs that claimed everything was fixed but failed (T6).", ""]
    for cat, desc in CATEGORIES.items():
        lines.append(f"## {cat}: {c[cat]}")
        lines.append(desc)
        seen = []
        for e in ex[cat]:
            if e not in seen:
                seen.append(e)
            if len(seen) == 4:
                break
        lines += [f"- e.g. {e}" for e in seen]
        lines.append("")
    return "\n".join(lines), c


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out")
    a = ap.parse_args()
    text, _ = render(a.runs)
    if a.out:
        Path(a.out).write_text(text)
    print(text)
