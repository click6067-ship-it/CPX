"""
④ 채점 데모 — v0(키워드) vs LLM(의미매칭) 비교.
실행: PYTHONPATH=src .venv/bin/python demo_grade.py
"""
import json
from pathlib import Path

from cpx.models import CpxCase
from cpx.agents.grader import grade, grade_llm

ROOT = Path(__file__).parent
case = CpxCase(**json.loads((ROOT / "data/cases/diarrhea_kim.json").read_text(encoding="utf-8")))
transcript = (ROOT / "data/transcripts/diarrhea_kim_demo.txt").read_text(encoding="utf-8")

print(f"=== {case.title} ({case.diagnosis}) ===")
print("   v0 = 키워드 매칭(API 0)  ·  LLM = 의미매칭(Gemini)\n")

v0 = grade(case, transcript)
llm = grade_llm(case, transcript)
v0m = {r["id"]: r for r in v0["items"]}
lm = {r["id"]: r for r in llm["items"]}

print(f"  {'항목':18s} v0   LLM   비고")
for it in case.checklist:
    a, b = v0m[it.id]["reached"], lm[it.id]["reached"]
    flag = "  ← 불일치: LLM이 의역 캐치" if a != b else ""
    print(f"  {it.id:18s} {'✅' if a else '❌'}   {'✅' if b else '❌'}{flag}")

print(f"\n  총점  v0: {v0['total']} ({v0['reached']})   |   LLM: {llm['total']} ({llm['reached']})")
print(f"  LLM 피드백: {llm['feedback']}")
print("\n  [LLM 판정 근거 — 누락 항목]")
for it in case.checklist:
    r = lm[it.id]
    if not r["reached"]:
        print(f"    · {it.id}: {r['reason']}")
