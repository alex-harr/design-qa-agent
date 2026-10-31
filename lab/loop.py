"""One round of the improvement loop: propose, test on train, keep or revert, log.

python3 lab/loop.py --current skill/v000 --current-run base-train-a --next v001 --threshold 10

1. Failure packet + taxonomy from the current skill's train run (train only).
2. Proposer (Opus) writes skill/<next>/SKILL.md, guarded against leaks and oversized edits.
3. The candidate runs on train, 2 trials per task.
4. Keep if net fixed improves by >= threshold and strict passes don't drop; else revert.
5. Appends the round to skill/CHANGELOG.md and analysis/loop.jsonl.
"""

import argparse, json, subprocess, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from report import compare_runs, summarize
import taxonomy

import system

LAB = system.LAB
AN = system.ANALYSIS


def sh(cmd, **kw):
    return subprocess.run(cmd, cwd=LAB, capture_output=True, text=True, **kw)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--current", required=True)
    ap.add_argument("--current-run", required=True)
    ap.add_argument("--next", required=True)
    ap.add_argument("--threshold", type=int, required=True)
    ap.add_argument("--trials", type=int, default=2)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--screen", action="store_true", help="1-trial screen first; confirm with the full trials only if it at least breaks even")
    a = ap.parse_args()
    AN.mkdir(exist_ok=True)
    t0 = time.time()
    fail_md, tax_md = AN / f"{a.next}-input-failures.md", AN / f"{a.next}-input-taxonomy.md"
    base_runs = a.current_run.split(",")
    sh([sys.executable, "lab/failures.py", *base_runs, "--out", str(fail_md), "--max", "30", "--digests", "10"])
    text, counts = taxonomy.render(base_runs)
    tax_md.write_text(text)

    p = sh([sys.executable, "lab/propose.py", "--skill", a.current, "--failures", str(fail_md), "--taxonomy", str(tax_md),
            "--out", f"skill/{a.next}"], timeout=1500)
    try:
        prop = json.loads(p.stdout)
    except json.JSONDecodeError:
        prop = {"ok": False, "error": p.stdout[-500:] + p.stderr[-500:]}
    record = {"round": a.next, "base": a.current, "base_run": a.current_run, "proposal": prop.get("proposal"),
              "guard_problems": prop.get("problems"), "proposer_cost_usd": prop.get("cost_usd"), "diff": prop.get("diff")}
    if not prop.get("ok"):
        record["decision"] = "rejected by guard (not tested)"
    else:
        run = f"{a.next}-train"
        screened_out = False
        if a.screen:
            sh([sys.executable, "lab/run_agent.py", "--skill", f"skill/{a.next}", "--run", run, "--split", "train",
                "--trials", "1", "--jobs", str(a.jobs)], timeout=7200)
            from report import load_run
            cand1 = sum(r["fixed"] - r["regressions"] - r["false_flags"] for r in load_run(run) if r["run"]["trial"] == 1)
            base1 = sum(r["fixed"] - r["regressions"] - r["false_flags"] for b in base_runs for r in load_run(b)) / len(base_runs) / a.trials
            record["screen"] = {"candidate_net_fixed_1trial": cand1, "base_net_fixed_per_trial": base1}
            screened_out = cand1 < base1
        if not screened_out:
            sh([sys.executable, "lab/run_agent.py", "--skill", f"skill/{a.next}", "--run", run, "--split", "train",
                "--trials", str(a.trials), "--jobs", str(a.jobs)], timeout=7200)
    if prop.get("ok") and screened_out:
        record["decision"] = "revert (screened out)"
    elif prop.get("ok"):
        cs = [compare_runs(b, run) for b in base_runs]  # several base runs of the current skill: average them
        cmp = {"base_passes": sum(c["base_passes"] for c in cs) / len(cs), "candidate_passes": cs[0]["candidate_passes"],
               "base_net_fixed": sum(c["base_net_fixed"] for c in cs) / len(cs), "candidate_net_fixed": cs[0]["candidate_net_fixed"],
               "runs": cs[0]["runs"], "moved": cs[0]["moved"]}
        cmp["delta_passes"] = cmp["candidate_passes"] - cmp["base_passes"]
        cmp["delta_net_fixed"] = cmp["candidate_net_fixed"] - cmp["base_net_fixed"]
        summ = summarize(run)
        keep = cmp["delta_net_fixed"] >= a.threshold and cmp["delta_passes"] >= 0
        record.update({"run": run, "compare": {k: v for k, v in cmp.items() if k != "moved"}, "summary": summ,
                       "decision": "keep" if keep else "revert"})
    record["minutes"] = round((time.time() - t0) / 60, 1)
    with open(AN / "loop.jsonl", "a") as f:
        f.write(json.dumps(record) + "\n")

    pr = record.get("proposal") or {}
    c = record.get("compare") or {}
    entry = [f"\n## {a.next} ({record['decision']})", "",
             f"- Built on: {a.current} (train run `{a.current_run}`)",
             f"- Target: {pr.get('target_category', '-')}",
             f"- Change: {pr.get('change_summary', '-')}",
             f"- Why it should generalize (proposer): {pr.get('why_it_generalizes', '-')}",
             f"- Risk (proposer): {pr.get('risk', '-')}"]
    if c:
        entry.append(f"- Train, {a.trials} trials: strict passes {c['base_passes']} -> {c['candidate_passes']} "
                     f"({c['delta_passes']:+g}); net fixed {c['base_net_fixed']:g} -> {c['candidate_net_fixed']} "
                     f"({c['delta_net_fixed']:+g}); keep rule: net fixed +{a.threshold} or more and passes not lower")
    if record.get("screen"):
        sc = record["screen"]
        entry.append(f"- Screen, 1 trial: net fixed {sc['candidate_net_fixed_1trial']} vs baseline {sc['base_net_fixed_per_trial']:g} per trial"
                     + (" (screened out, not confirmed)" if record["decision"].startswith("revert (screened") else " (passed to confirm)"))
    if record.get("guard_problems"):
        entry.append(f"- Guard: {'; '.join(record['guard_problems'])}")
    with open(LAB / "skill" / "CHANGELOG.md", "a") as f:
        f.write("\n".join(entry) + "\n")
    print(json.dumps({k: record.get(k) for k in ("round", "decision", "compare", "proposal", "guard_problems", "minutes")}, indent=2))


if __name__ == "__main__":
    main()
