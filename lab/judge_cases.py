"""Run the LLM judge on every calibration case (lab/calibration/cases_key.json), several at a time."""
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
LAB = Path(__file__).resolve().parents[1]
import os
WORK = os.environ.get("LAB_WORK_ROOT", os.path.expanduser("~/.design-qa-lab-work"))
key = json.loads((LAB / "lab" / "calibration" / "cases_key.json").read_text())

def one(item):
    cid, v = item
    r = subprocess.run([sys.executable, str(LAB / "lab" / "judge.py"), v["task"], v["run_dir"], WORK], capture_output=True, text=True)
    try:
        return cid, json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:
        return cid, {"error": (r.stderr or r.stdout)[-400:]}

with ThreadPoolExecutor(5) as ex:
    for cid, res in ex.map(one, key.items()):
        print(cid, json.dumps({k: (v.get("verdict") if isinstance(v, dict) else v) for k, v in res.items()}), flush=True)
