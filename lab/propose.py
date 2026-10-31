"""Proposer: one small, general edit to the QA agent's skill, written by a stronger model.

python3 lab/propose.py --skill skill/v000 --failures <packet.md> --taxonomy <taxonomy.md> --out skill/v001

The proposer sees the current skill, the rules, failure packets from TRAIN runs only, the failure
taxonomy and the changelog of earlier attempts (kept and reverted). It writes a full new SKILL.md
plus a short proposal. A guard rejects edits that leak task specifics (element ids, screen class
names, task ids, hex values) or that are too big to attribute a score change to.
"""

import argparse, difflib, json, os, re, shutil, subprocess, sys, uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import system

LAB = system.LAB
WORK = Path(os.environ.get("LAB_WORK_ROOT", str(Path.home() / ".design-qa-lab-work"))) / "proposer"
MODEL = "claude-opus-5-5"
MAX_CHANGED_LINES = 20

SYSTEM = """You improve a skill file for a design-system QA agent. The agent is a small, fast model. It gets one UI screen (screen.html) and the design system's rules (RULES.md), must find and fix every violation by editing the screen, and must write an honest findings report. The skill is the agent's playbook.

Files here:
- SKILL.md: the current skill
- RULES.md: the design system rules the agent enforces (you cannot change these)
- taxonomy.md: failure categories from error analysis of the agent's training runs, with counts
- failures.md: the failing training runs: what was planted, what the agent did, its tool calls
- CHANGELOG.md: earlier skill edits and whether they were kept or reverted

Your job: make ONE focused change to the skill that targets the most common failure category the skill can plausibly fix. It is tested on these training screens and later on screens you will never see, so it must generalize:
- Teach a method, a check or a habit, not an answer. Never name specific screens, element ids, the screens' own class names, or exact values that appear in the failures. Design-system names from RULES.md are fine.
- Keep everything that works. Don't remove guidance unless it caused failures.
- Small and attributable: change at most about 15 lines. Keep the whole skill under 70 lines.
- Don't repeat an idea the changelog shows was reverted.

Write the complete new skill to NEW_SKILL.md, then write proposal.json:
{"target_category": "<taxonomy category>", "change_summary": "<one sentence>", "why_it_generalizes": "<one sentence>", "risk": "<what could get worse>"}"""


def forbidden_terms():
    terms = set()
    for t in system.TASKS.glob("t*/truth.json"):
        meta = json.loads(t.read_text())
        terms.add(meta["task"])
        for m in meta["mutations"]:
            terms.update(m["elements"])
    for s in system.SCREENS.glob("*.html"):
        terms.add(s.stem[3:])
        style = re.search(r"<style>(.*?)</style>", s.read_text(), re.S)
        if style:
            terms.update(re.findall(r"\.([a-z][\w-]+)", style.group(1)))
    ds = (system.DS / "RULES.md").read_text() + "".join((system.DS / f).read_text() for f in system.CFG.get("own_css", ["lab-components.css"]) if (system.DS / f).exists())
    # plain words ("footer", "actions") are too common to block; hyphenated or numbered names are screen-specific
    return {t for t in terms if re.search(r"[-\d]", t) and t not in ds}


def guard(old, new):
    problems = []
    added = "\n".join(l[1:] for l in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0)
                      if l.startswith("+") and not l.startswith("+++"))
    changed = sum(1 for l in difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0)
                  if l[:1] in "+-" and not l.startswith(("+++", "---")))
    if changed > MAX_CHANGED_LINES * 2:
        problems.append(f"too big: {changed} changed lines")
    if len(new.splitlines()) > 80:
        problems.append(f"skill too long: {len(new.splitlines())} lines")
    leaks = sorted(t for t in forbidden_terms() if re.search(r"(?<![\w-])" + re.escape(t) + r"(?![\w-])", added))
    if leaks:
        problems.append("leaks task specifics: " + ", ".join(leaks[:10]))
    if re.search(r"#[0-9a-fA-F]{6}\b", added):
        problems.append("adds a hex value")
    return problems, changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skill", required=True)
    ap.add_argument("--failures", required=True)
    ap.add_argument("--taxonomy", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = LAB / a.out
    work = WORK / out.name
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    old = (LAB / a.skill / "SKILL.md").read_text()
    (work / "SKILL.md").write_text(old)
    shutil.copy(system.DS / "RULES.md", work / "RULES.md")
    shutil.copy(a.failures, work / "failures.md")
    shutil.copy(a.taxonomy, work / "taxonomy.md")
    log = LAB / "skill" / "CHANGELOG.md"
    (work / "CHANGELOG.md").write_text(log.read_text() if log.exists() else "No earlier edits.\n")
    cmd = ["claude", "-p", "Propose the next skill edit.", "--session-id", str(uuid.uuid4()), "--no-session-persistence",
           "--system-prompt", SYSTEM, "--tools", "Read,Write,Edit,Glob,Grep", "--permission-mode", "dontAsk",
           "--setting-sources", "", "--settings", json.dumps({"permissions": {"allow": ["Read(./**)", "Write(./**)", "Edit(./**)", "Glob", "Grep"],
                                                                          "blockReadsOutsideWorkingDirectories": True}}),
           "--model", MODEL, "--max-turns", "30", "--max-budget-usd", "3", "--output-format", "json"]
    p = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=1200)
    try:
        cost = json.loads(p.stdout).get("total_cost_usd")
    except json.JSONDecodeError:
        cost = None
    new_path, prop_path = work / "NEW_SKILL.md", work / "proposal.json"
    if not new_path.exists():
        print(json.dumps({"ok": False, "error": "no NEW_SKILL.md", "stderr": p.stderr[-500:], "cost_usd": cost}))
        return
    new = new_path.read_text()
    problems, changed = guard(old, new)
    proposal = json.loads(prop_path.read_text()) if prop_path.exists() else {}
    result = {"ok": not problems, "problems": problems, "changed_lines": changed, "proposal": proposal, "cost_usd": cost,
              "diff": "\n".join(difflib.unified_diff(old.splitlines(), new.splitlines(), "before", "after", lineterm="", n=1))}
    if not problems:
        out.mkdir(parents=True, exist_ok=True)
        (out / "SKILL.md").write_text(new)
        (out / "proposal.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
