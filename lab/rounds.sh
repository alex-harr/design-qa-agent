#!/bin/bash
# Rounds 4-6. A kept version becomes the base for the next round.
cd "$(dirname "$0")/.."
: "${DQA_SYSTEM:=primer}"; export DQA_SYSTEM  # Stage 3 rounds ran on Primer
cur=skill/v000; currun=base-train-a,base-train-b
for v in v004 v005 v006; do
  python3 lab/loop.py --current $cur --current-run $currun --next $v --threshold 48 --screen > systems/$DQA_SYSTEM/analysis/loop-$v.log 2>&1
  dec=$(python3 -c "import json;print(json.loads(open('systems/'+__import__('os').environ['DQA_SYSTEM']+'/analysis/loop.jsonl').read().splitlines()[-1])['decision'])")
  echo "$v $dec"
  if [ "$dec" = "keep" ]; then cur=skill/$v; currun=$v-train; fi
done
