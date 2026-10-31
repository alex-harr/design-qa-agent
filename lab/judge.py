"""LLM judge for the two calls code can't make with certainty.

J1 fix_acceptable: would a design-system reviewer accept how each planted problem was resolved,
   even where the fix differs from the original intended value?
J2 report_accurate: does findings.json describe what was wrong and what changed, truthfully,
   without false alarms?

One isolated judge call per dimension (Anthropic's evals post recommends grading each dimension
with its own judge and letting it answer "unknown"). The judge sees screenshots, the ground truth,
the code grader's per-problem results and the agent's report. It runs on a different model than
the agent to reduce shared bias.
"""

import json, shutil, subprocess, sys, uuid
from pathlib import Path

import system

LAB = system.LAB
JUDGE_MODEL = "claude-opus-5-5"

COMMON = """You are a senior design-systems reviewer grading an automated design-system QA agent.
The design system's rules are in rules.md. A clean screen was seeded with known problems; the agent had to find and fix them.
Files in this folder:
- clean.png: the screen as designed (the intended result)
- input.png: the screen with the planted problems (what the agent received)
- output.png: the screen after the agent's fixes
- case.json: the planted problems with their intended fixes, the code grader's result for each, any other style changes the agent made, and the agent's findings report
Look at all three images and case.json before answering. Answer with only a JSON object on the last line."""

J1 = COMMON + """

Question: Is the agent's handling of the planted problems acceptable to ship?
PASS only if every planted problem is resolved in a way a design-system reviewer would approve: either the intended fix, or an alternative that follows rules.md just as well and preserves the design's hierarchy and intent. Any planted problem left unresolved, or "fixed" with a token or component that a reviewer would reject, is a FAIL. Changes to things that weren't broken are a FAIL if they visibly alter the design.
If the case is a clean control (no planted problems), PASS only if the screen came back visually unchanged.
Output: {"verdict": "pass" | "fail" | "unknown", "reason": "<one or two sentences>"}"""

J2 = COMMON + """

Question: Is the agent's findings report accurate?
PASS only if the report names each planted problem it found with the right element and a correct description, does not claim fixes that weren't made, and does not raise false alarms about things that are fine. Missing a planted problem in the report is a FAIL. Minor wording issues are fine.
If the case is a clean control, PASS only if the report has no findings or only findings that are real issues.
Output: {"verdict": "pass" | "fail" | "unknown", "reason": "<one or two sentences>"}"""

DIMENSIONS = {"fix_acceptable": J1, "report_accurate": J2}


def build_case(task_dir, run_dir):
    meta = json.loads((task_dir / "truth.json").read_text())
    grade = json.loads((run_dir / "grade.json").read_text())
    try:
        report = json.loads((run_dir / "findings.json").read_text())
    except Exception:
        report = "missing or invalid findings.json"
    return {
        "clean_control": meta["clean_control"],
        "planted_problems": [{"id": m["id"], "rule": m["rule"], "what": m["description"], "elements": m["elements"],
                              "intended": m["original"]} for m in meta["mutations"]],
        "code_grader": [{"id": r["id"], "exact_intended_fix_restored": r["fixed"], "still_differs": r["left"]["style"],
                         "rule_violations_left": r["left"]["lint"], "contrast_failures_left": r["left"]["contrast"]}
                        for r in grade["mutations"]],
        "other_changes_vs_design": grade["regression_detail"],
        "agent_report": report,
    }


def prepare(task_dir, run_dir, work):
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    import checks  # noqa: local import keeps Playwright out of the judge subprocess path
    checks.render(task_dir / "clean.html", screenshot=work / "clean.png")
    checks.render(task_dir / "input.html", screenshot=work / "input.png")
    shutil.copy(run_dir / "fixed.png", work / "output.png")
    shutil.copy(system.DS / "RULES.md", work / "rules.md")
    (work / "case.json").write_text(json.dumps(build_case(task_dir, run_dir), indent=2))


def ask(work, prompt, model=JUDGE_MODEL):
    cmd = ["claude", "-p", "Grade this case.", "--session-id", str(uuid.uuid4()), "--no-session-persistence",
           "--system-prompt", prompt, "--tools", "Read", "--permission-mode", "dontAsk", "--setting-sources", "",
           "--settings", json.dumps({"permissions": {"allow": ["Read(./**)"], "blockReadsOutsideWorkingDirectories": True}}),
           "--model", model, "--max-turns", "10", "--max-budget-usd", "1", "--output-format", "json"]
    p = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=600)
    try:
        d = json.loads(p.stdout)
    except json.JSONDecodeError:
        return {"verdict": "unknown", "reason": "judge call failed", "cost_usd": None}
    text = (d.get("result") or "").strip().splitlines()
    verdict = {"verdict": "unknown", "reason": "unparseable"}
    for line in reversed(text):
        line = line.strip().strip("`")
        if line.startswith("{"):
            try:
                verdict = json.loads(line)
                break
            except json.JSONDecodeError:
                pass
    verdict["cost_usd"] = d.get("total_cost_usd")
    return verdict


def judge_run(task_id, run_dir, work_root, model=JUDGE_MODEL):
    task_dir = system.TASKS / task_id
    run_dir = Path(run_dir).resolve()
    out = run_dir / "judge.json"
    if out.exists():
        return json.loads(out.read_text())
    work = Path(work_root) / "judge" / run_dir.relative_to(system.RUNS)
    prepare(task_dir, run_dir, work)
    res = {dim: ask(work, prompt, model) for dim, prompt in DIMENSIONS.items()}
    res["model"] = model
    out.write_text(json.dumps(res, indent=2))
    return res


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))
    task_id, run_dir, work_root = sys.argv[1:4]
    print(json.dumps(judge_run(task_id, run_dir, work_root)))
