"""Baseline harness: run the design-system QA agent on tasks with Claude Code in headless mode.

Each run gets a fresh working folder (the screen plus a read-only copy of the design system docs),
an isolated session, the skill under test in its system prompt, and a fixed task prompt.
The agent can read inside its folder and edit there; it cannot run shell commands or read the lab's
ground truth. Everything it does is saved as a transcript for error analysis.

Usage: python lab/run_agent.py --skill skill/v000 --split train --trials 1 --run baseline-pilot [--tasks t01,t02] [--jobs 4]
"""

import argparse, json, os, shutil, subprocess, sys, time, uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import score
import system

LAB = system.LAB
WORK_ROOT = Path(os.environ.get("LAB_WORK_ROOT", str(Path.home() / ".design-qa-lab-work")))  # must sit OUTSIDE the lab folder
MODEL = "claude-haiku-4-5"

HARNESS_SYSTEM = """You are a design-system QA agent. Your working folder contains screen.html (a UI screen) and design-system/ (the design system's rules and CSS). Work only inside this folder.

Follow this skill:

<skill>
{skill}
</skill>"""

TASK_PROMPT = """Review screen.html against the design system.

Fix every design-system violation by editing screen.html in place. Change only what is needed: keep the text, the structure and every data-qa attribute.

Then write findings.json in this folder, in exactly this shape:
{"findings": [{"element": "<data-qa id of the affected element, or the CSS selector you changed>", "rule": "<R1 to R7>", "problem": "<what was wrong>", "fix": "<what you changed>"}],
 "self_assessment": {"all_fixed": <true or false>, "confidence": <number from 0 to 1>}}

If the screen has no violations, leave screen.html unchanged and write an empty findings list."""

# The agent can never read the lab or the system folder (ground truth lives in <system>/tasks).
_DENY = sorted({str(LAB), str(system.ROOT)})
SETTINGS = {"permissions": {"allow": ["Read(./**)", "Edit(./**)", "Glob", "Grep"],
                            "deny": [f"{verb}(/{d}/**)" for d in _DENY for verb in ("Read", "Edit")],
                            "blockReadsOutsideWorkingDirectories": True}}


def _check_work_root():
    w = WORK_ROOT.resolve()
    for d in _DENY:
        if w == Path(d) or Path(d) in w.parents:
            sys.exit(f"LAB_WORK_ROOT ({w}) must sit outside {d}, or the agent could read the ground truth.")


def prepare(work, task_dir):
    """The agent's folder: the screen plus the design-system files listed in ds.json "agent_copy"."""
    work.mkdir(parents=True)
    shutil.copy(task_dir / "input.html", work / "screen.html")
    ds = work / "design-system"
    ds.mkdir()
    copy = system.CFG["agent_copy"]
    for f in copy["files"]:
        (ds / f).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(system.DS / f, ds / f)
    for f, text in copy.get("stubs", {}).items():
        (ds / f).parent.mkdir(parents=True, exist_ok=True)
        (ds / f).write_text(text)


def run_one(task_id, skill_dir, run_name, trial, model=MODEL, max_budget=2.0):
    task_dir = system.TASKS / task_id
    out = system.RUNS / run_name / task_id / f"trial{trial}"
    if (out / "grade.json").exists():
        return json.loads((out / "grade.json").read_text())
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    work = WORK_ROOT / run_name / task_id / f"trial{trial}"
    if work.exists():
        shutil.rmtree(work)
    prepare(work, task_dir)
    skill = (LAB / skill_dir / "SKILL.md").read_text()
    cmd = ["claude", "-p", TASK_PROMPT,
           "--session-id", str(uuid.uuid4()), "--no-session-persistence",
           "--system-prompt", HARNESS_SYSTEM.format(skill=skill),
           "--tools", "Read,Edit,Write,Glob,Grep",
           "--permission-mode", "dontAsk", "--setting-sources", "", "--settings", json.dumps(SETTINGS),
           "--model", model, "--max-turns", "40", "--max-budget-usd", str(max_budget),
           "--output-format", "stream-json", "--verbose"]
    t0 = time.time()
    proc = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=1200)
    elapsed = time.time() - t0
    (out / "transcript.jsonl").write_text(proc.stdout)
    if proc.stderr.strip():
        (out / "stderr.txt").write_text(proc.stderr[-20000:])
    result = {}
    for line in proc.stdout.splitlines():
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "result":
            result = ev
    meta = {"task": task_id, "skill": str(skill_dir), "trial": trial, "model": model, "elapsed_s": round(elapsed, 1),
            "cost_usd": result.get("total_cost_usd"), "num_turns": result.get("num_turns"),
            "stop": result.get("subtype"), "is_error": result.get("is_error"), "returncode": proc.returncode}
    for f in ("screen.html", "findings.json"):
        if (work / f).exists():
            shutil.copy(work / f, out / ("fixed.html" if f == "screen.html" else f))
    g = score.grade(task_dir, out / "fixed.html", out / "findings.json", screenshot=out / "fixed.png")
    g["run"] = meta
    (out / "grade.json").write_text(json.dumps(g, indent=2))
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--split", choices=["train", "heldout"])
    ap.add_argument("--tasks")
    ap.add_argument("--trials", type=int, default=1)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--model", default=MODEL)
    a = ap.parse_args()
    _check_work_root()
    splits = json.loads(system.SPLITS.read_text())
    tasks = a.tasks.split(",") if a.tasks else splits[a.split]
    tasks = [t if (system.TASKS / t).exists() else next(x for x in splits["train"] + splits["heldout"] if x.startswith(t)) for t in tasks]
    jobs = [(t, k) for k in range(1, a.trials + 1) for t in tasks]
    # Playwright's sync API is not thread-safe, so grading happens inside each worker process via a fresh interpreter.
    def work(job):
        t, k = job
        r = subprocess.run([sys.executable, __file__, "--one", t, str(k), a.skill, a.run, a.model], capture_output=True, text=True)
        try:
            return json.loads(r.stdout.strip().splitlines()[-1])
        except Exception:
            return {"task": t, "trial": k, "error": (r.stderr or r.stdout)[-800:]}
    with ThreadPoolExecutor(a.jobs) as ex:
        for g in ex.map(work, jobs):
            m = g.get("run", {})
            print(f"{g.get('task'):26s} trial{m.get('trial', '?')} pass={g.get('pass')} fixed={g.get('fixed')}/{g.get('planted')} "
                  f"detected={g.get('detected')} false={g.get('false_flags')} regr={g.get('regressions')} "
                  f"cost=${m.get('cost_usd')} turns={m.get('num_turns')} {g.get('error', '')[:200]}", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--one":
        t, k, skill, run, model = sys.argv[2], int(sys.argv[3]), sys.argv[4], sys.argv[5], sys.argv[6]
        g = run_one(t, skill, run, k, model)
        print(json.dumps({k2: g[k2] for k2 in ("task", "pass", "planted", "detected", "fixed", "false_flags", "regressions", "run")}))
    else:
        main()
