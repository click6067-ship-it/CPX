"""
② 사례 심사 데모 — 점검표 루브릭으로 CPX 사례 검토.
실행: PYTHONPATH=src .venv/bin/python demo_review.py [case_id]
"""
import json
import sys
from pathlib import Path

from cpx.models import CpxCase
from cpx.agents.reviewer import review

ROOT = Path(__file__).parent
cid = sys.argv[1] if len(sys.argv) > 1 else "diarrhea_kim"
case = CpxCase(**json.loads((ROOT / f"data/cases/{cid}.json").read_text(encoding="utf-8")))

out = review(case)
print(f"=== ② 심사: {case.title} ({case.diagnosis}) ===\n")
for r in out.results:
    print(f"  {'✅' if r.passed else '⚠️ '} {r.criterion}")
    if not r.passed:
        print(f"       → {r.comment}")
n_pass = sum(r.passed for r in out.results)
print(f"\n  통과 {n_pass}/{len(out.results)}  ·  판정: 【{out.verdict}】")
print(f"  총평: {out.summary}")
if out.fixes:
    print("  우선 수정:")
    for f in out.fixes:
        print(f"    - {f}")
