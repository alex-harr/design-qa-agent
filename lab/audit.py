"""Clean-screen audit: run the agent on every clean screen with your rules, before measuring anything.

A clean screen breaks no rules, so the agent should change nothing and flag nothing. Anything it does flag
is a place where your rules doc and your design disagree. Fix the rule (or the screen) and audit again.
In Stage 4 this one-run-per-screen check found every rules-vs-design contradiction that the full
106-run measurements exposed, for about a penny on Haiku 5.5.

    DQA_SYSTEM=<name> python3 lab/audit.py [--model claude-haiku-5-5] [--run audit]

It builds <system>/audit/ (a copy of the design system, the screens as clean-control tasks) and runs the
agent there, so your real tasks/ and runs/ are untouched.
"""

import argparse, json, os, shutil, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import system


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-haiku-5-5")
    ap.add_argument("--run", default="audit")
    ap.add_argument("--jobs", type=int, default=6)
    a = ap.parse_args()
    out = system.ROOT / "audit"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(system.DS, out / "design-system")
    shutil.copytree(system.SCREENS, out / "screens", ignore=shutil.ignore_patterns("design-system"))
    ids = []
    for scr in sorted(system.SCREENS.glob("*.html")):
        tid = f"a{scr.stem}"
        d = out / "tasks" / tid
        d.mkdir(parents=True)
        shutil.copy(scr, d / "clean.html")
        shutil.copy(scr, d / "input.html")
        (d / "truth.json").write_text(json.dumps({"task": tid, "screen": scr.name, "split": "train",
                                                  "clean_control": True, "mutations": []}, indent=2))
        ids.append(tid)
    (out / "splits.json").write_text(json.dumps({"train": ids, "heldout": []}, indent=2))
    env = dict(os.environ, DQA_SYSTEM_DIR=str(out))
    subprocess.run([sys.executable, str(Path(__file__).parent / "run_agent.py"), "--skill", "skill/v000", "--run", a.run,
                    "--split", "train", "--trials", "1", "--jobs", str(a.jobs), "--model", a.model],
                   cwd=system.LAB, env=env, check=True)
    flagged = []
    for g in sorted((out / "runs" / a.run).glob("*/trial1/grade.json")):
        r = json.loads(g.read_text())
        if not r["pass"]:
            flagged.append((r["task"], r["false_flag_detail"][:3], list(r["regression_detail"])[:5]))
    print(f"\n{len(ids) - len(flagged)}/{len(ids)} clean screens came back untouched.")
    for task, flags, changed in flagged:
        print(f"- {task}: changed {changed or 'nothing'}")
        for f in flags:
            print(f"    flagged {f.get('rule')} on {f.get('element')}: {f.get('problem')}")
    if flagged:
        print("\nEach of these is a rule your clean design breaks. Fix the rule or the screen, then audit again.")


if __name__ == "__main__":
    main()
