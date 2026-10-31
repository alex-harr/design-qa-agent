import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import checks
import system

# a token counts as defined if any design-system CSS file declares it
defined = set()
for f in system.DS.rglob("*.css"):
    defined |= set(re.findall(r"(--[\w-]+)\s*:", f.read_text()))
own_css = [system.DS / f for f in system.CFG.get("own_css", ["lab-components.css"]) if (system.DS / f).exists()]
bad = 0
for src in own_css + sorted(system.SCREENS.glob("*.html")):
    text = src.read_text()
    undefined = sorted(set(re.findall(r"var\((--[\w-]+)", text)) - defined)
    lint = checks.lint_source(text) if src.suffix == ".html" else []
    r = checks.render(src) if src.suffix == ".html" else {"contrast_failures": [], "styles": {}}
    status = "OK" if not (undefined or lint or r["contrast_failures"]) else "PROBLEM"
    bad += status != "OK"
    print(f"{src.name:28s} {status}  elements={len(r['styles'])} undefined={undefined} lint={len(lint)} contrast_fail={[(c['qa'], c['ratio']) for c in r['contrast_failures']]}")
    for l in lint: print("    ", l)
print("problems:", bad)
