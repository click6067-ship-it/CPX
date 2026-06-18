"""
적대 transcript 팩 — 채점 강건성 + 오류 surfacing.
실행: PYTHONPATH=src .venv/bin/python adversarial_smoke.py

각 stress 대화를 ④LLM 채점 → gold와 비교 → 불일치(FP/FN)를 원인 후보와 함께 노출.
(오류 taxonomy의 원재료: FP=헛점, FN=놓침)
"""
import json
from collections import Counter
from pathlib import Path

from cpx.models import CpxCase
from cpx.agents.grader import grade_llm

ROOT = Path(__file__).parent
cases = {p.stem: CpxCase(**json.loads(p.read_text(encoding="utf-8")))
         for p in (ROOT / "data/cases").glob("*.json")}
pack = json.loads((ROOT / "data/adversarial.json").read_text(encoding="utf-8"))

errors = Counter()
total_items = 0
total_err = 0
for fx in pack:
    case = cases[fx["case"]]
    res = grade_llm(case, fx["transcript"])
    pred = {r["id"]: r["reached"] for r in res["items"]}
    print(f"\n=== {fx['name']} ===")
    for it in case.checklist:
        p, g = bool(pred.get(it.id)), bool(fx["gold"].get(it.id))
        total_items += 1
        if p == g:
            continue
        total_err += 1
        kind = "FP(헛점)" if (p and not g) else "FN(놓침)"
        errors[kind] += 1
        print(f"   ✗ {it.id}: AI={'도달' if p else '누락'} vs gold={'도달' if g else '누락'}  [{kind}]")
    if all(bool(pred.get(it.id)) == bool(fx["gold"].get(it.id)) for it in case.checklist):
        print("   ✅ 전 항목 gold 일치 (강건)")

print(f"\n── 요약: {total_items - total_err}/{total_items} 일치 · 오류 {dict(errors)} ──")
print("  (FP=AI가 안 한 걸 했다 함=과대평가 위험 / FN=한 걸 놓침=과소평가)")
