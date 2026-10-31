"""Failure packets for error analysis and for the skill proposer.

python3 lab/failures.py <run> [--out file.md] [--max N]

Train runs only: refuses held-out runs so nothing from the held-out set can leak into the skill.
Each failing run gets: the planted problems and how each was handled, regressions, false flags,
the agent's own report and self-assessment, and a digest of its tool calls.
"""

import argparse, json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from report import load_run, digest

import system

LAB = system.LAB


def outcome(m):
    if m["fixed"]:
        return "fixed"
    left = m["left"]
    bits = []
    if left["lint"]:
        bits.append("still breaks " + ", ".join(sorted({l["rule"] for l in left["lint"]})))
    if left["contrast"]:
        bits.append("still fails contrast")
    if left["style"]:
        props = sorted({p for d in left["style"].values() for p in d})
        bits.append("looks different from the design (" + ", ".join(props[:4]) + ")")
    return "; ".join(bits) or "not fixed"


def packet(row, with_digest=True):
    task = row["task"]
    truth = json.loads((system.TASKS / task / "truth.json").read_text())
    if truth["split"] != "train":
        raise SystemExit(f"refusing to build a packet from held-out task {task}")
    lines = [f"### {task} trial {row['run']['trial']}: {'clean control' if truth['clean_control'] else str(row['planted']) + ' planted problems'}"]
    by_id = {m["id"]: m for m in truth["mutations"]}
    for m in row["mutations"]:
        t = by_id[m["id"]]
        lines.append(f"- [{t['rule']} {t['op']}] {t['description']} | elements {', '.join(t['elements'])} | "
                     f"intended: `{t['original'][:90]}` | found: {'yes' if m['detected'] else 'NO'} | result: {outcome(m)}")
    if row["regression_detail"]:
        for qa, d in list(row["regression_detail"].items())[:5]:
            changes = [f"{p} {v[0]} -> {v[1]}" if isinstance(v, list) else f"{p}" for p, v in list(d.items())[:3]]
            lines.append(f"- REGRESSION (changed something that wasn't broken) on {qa}: " + ", ".join(changes))
    for f in row.get("false_flag_detail") or []:
        lines.append(f"- FALSE FLAG: {f.get('element')} {f.get('rule')}: {str(f.get('problem'))[:160]} -> {str(f.get('fix'))[:120]}")
    if row.get("lint_left") or row.get("contrast_left"):
        lines.append(f"- left on screen: {row['lint_left']} lint violations, {row['contrast_left']} contrast failures")
    lines.append(f"- self-assessment: {row.get('self_assessment')}")
    if with_digest:
        text = re.sub(r"/\S*?/lab-work/[^/]+/[^/]+/trial\d+/?", "./", digest(row["_dir"], 2500))
        lines.append("```\n" + text + "\n```")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--out")
    ap.add_argument("--max", type=int, default=999)
    ap.add_argument("--digests", type=int, default=999, help="tool-call digests for the first N failing runs only")
    ap.add_argument("--no-digest", action="store_true")
    a = ap.parse_args()
    rows = [r for run in a.runs for r in load_run(run) if not r["pass"]]
    # spread across tasks: one run per task first, then seconds, ...
    by_task = {}
    for r in rows:
        by_task.setdefault(r["task"], []).append(r)
    ordered = [lst[i] for i in range(max((len(v) for v in by_task.values()), default=0)) for lst in by_task.values() if i < len(lst)]
    picked = ordered[:a.max]
    parts = [packet(r, (not a.no_digest) and i < a.digests) for i, r in enumerate(picked)]
    text = f"# Failing runs in {', '.join(a.runs)}: {len(rows)} (showing {len(picked)})\n\n" + "\n\n".join(parts)
    if a.out:
        Path(a.out).write_text(text)
        print(f"wrote {a.out}: {len(rows)} failing runs, {len(picked)} shown")
    else:
        print(text)


if __name__ == "__main__":
    main()
