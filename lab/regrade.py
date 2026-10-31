"""Re-grade saved runs after a grader fix (pass/fail logic unchanged unless stated in LOG.md). Keeps run metadata."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import score
import system

LAB = system.LAB
for run in sys.argv[1:]:
    n = 0
    for g in sorted((system.RUNS / run).glob("*/trial*/grade.json")):
        old = json.loads(g.read_text())
        d = g.parent
        new = score.grade(system.TASKS / old["task"], d / "fixed.html", d / "findings.json")
        new["run"] = old.get("run")
        g.write_text(json.dumps(new, indent=2))
        n += 1
    print(run, "regraded", n)
