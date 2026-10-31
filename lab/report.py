"""Summaries of a run: scores per task and trial, and compact transcript digests for error analysis."""

import json, statistics, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import system

LAB = system.LAB


def load_run(run):
    rows = []
    for g in sorted((system.RUNS / run).glob("*/trial*/grade.json")):
        d = json.loads(g.read_text())
        d["_dir"] = str(g.parent)
        j = g.parent / "judge.json"
        if j.exists():
            d["judge"] = json.loads(j.read_text())
        rows.append(d)
    return rows


def summarize(run):
    rows = load_run(run)
    by_task = defaultdict(list)
    for r in rows:
        by_task[r["task"]].append(r)
    k = max((len(v) for v in by_task.values()), default=0)
    pass_rate = statistics.mean(r["pass"] for r in rows) if rows else 0
    pass_all = statistics.mean(all(x["pass"] for x in v) for v in by_task.values()) if by_task else 0
    pass_any = statistics.mean(any(x["pass"] for x in v) for v in by_task.values()) if by_task else 0
    planted = sum(r["planted"] for r in rows)
    by_rule = defaultdict(lambda: [0, 0, 0])
    for r in rows:
        for m in r["mutations"]:
            by_rule[m["rule"]][0] += 1
            by_rule[m["rule"]][1] += m["detected"]
            by_rule[m["rule"]][2] += m["fixed"]
    selfp = [r for r in rows if isinstance(r.get("self_assessment"), dict)]
    return {
        "run": run, "runs": len(rows), "tasks": len(by_task), "trials_per_task": k,
        "pass_rate": round(pass_rate, 3), f"pass^{k}": round(pass_all, 3), f"pass@{k}": round(pass_any, 3),
        "detected": round(sum(r["detected"] for r in rows) / max(planted, 1), 3),
        "fixed_exact": round(sum(r["fixed"] for r in rows) / max(planted, 1), 3),
        "planted_total": planted,
        "net_fixed": sum(r["fixed"] - r["regressions"] - r["false_flags"] for r in rows),
        "false_flags_per_run": round(statistics.mean(r["false_flags"] for r in rows), 2) if rows else 0,
        "regressions_per_run": round(statistics.mean(r["regressions"] for r in rows), 2) if rows else 0,
        "by_rule_detected_fixed": {k2: f"{v[1]}/{v[0]} detected, {v[2]}/{v[0]} fixed" for k2, v in sorted(by_rule.items())},
        "self_says_all_fixed": round(statistics.mean(bool(r["self_assessment"].get("all_fixed")) for r in selfp), 3) if selfp else None,
        "cost_usd": round(sum((r.get("run") or {}).get("cost_usd") or 0 for r in rows), 2),
        "mean_turns": round(statistics.mean((r.get("run") or {}).get("num_turns") or 0 for r in rows), 1) if rows else 0,
    }


def digest(run_dir, max_chars=3500):
    """Tool calls in order plus the final message, trimmed, for reading a failing transcript quickly."""
    lines = []
    for raw in (Path(run_dir) / "transcript.jsonl").read_text().splitlines():
        try:
            ev = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "assistant":
            for b in ev["message"].get("content", []):
                if b.get("type") == "text" and b["text"].strip():
                    lines.append("SAY: " + b["text"].strip().replace("\n", " ")[:300])
                elif b.get("type") == "tool_use":
                    inp = b["input"]
                    if b["name"] == "Edit":
                        lines.append(f"EDIT: {inp.get('old_string', '')[:120]!r} -> {inp.get('new_string', '')[:120]!r}")
                    else:
                        lines.append(f"{b['name'].upper()}: {json.dumps(inp)[:160]}")
    text = "\n".join(lines)
    return text if len(text) <= max_chars else text[:max_chars // 2] + "\n...\n" + text[-max_chars // 2:]


def per_task(run):
    out = defaultdict(lambda: [0, 0, 0])
    for r in load_run(run):
        out[r["task"]][0] += r["pass"]
        out[r["task"]][1] += 1
        out[r["task"]][2] += r["fixed"] - r["regressions"] - r["false_flags"]
    return dict(out)


def compare_runs(base, cand):
    """Paired comparison on the same tasks: total strict passes and per-task movement."""
    a, b = per_task(base), per_task(cand)
    tasks = sorted(set(a) & set(b))
    pa, pb = sum(a[t][0] for t in tasks), sum(b[t][0] for t in tasks)
    n = sum(a[t][1] for t in tasks)
    na, nb = sum(a[t][2] for t in tasks), sum(b[t][2] for t in tasks)
    moved = {t: f"pass {a[t][0]}/{a[t][1]} -> {b[t][0]}/{b[t][1]}, net fixed {a[t][2]} -> {b[t][2]}" for t in tasks
             if a[t][0] != b[t][0] or a[t][2] != b[t][2]}
    return {"base": base, "candidate": cand, "runs": n, "base_passes": pa, "candidate_passes": pb, "delta_passes": pb - pa,
            "base_net_fixed": na, "candidate_net_fixed": nb, "delta_net_fixed": nb - na, "moved": moved}


if __name__ == "__main__":
    if len(sys.argv) == 3:
        print(json.dumps(compare_runs(sys.argv[1], sys.argv[2]), indent=2))
    else:
        print(json.dumps(summarize(sys.argv[1]), indent=2))
