"""
LangGraph 데모 — 사례 개발 그래프(① 생성 → ② 심사 → 수정 루프).
실행: PYTHONPATH=src .venv/bin/python demo_graph.py
"""
from cpx import graph

result = graph.develop_case("어지러움", "양성돌발두위현훈(BPPV)", max_rounds=2)

print("=== LangGraph 사례 개발 ===")
print("  경로:", " → ".join(result["log"]))
case = result["case"]
print(f"  최종 사례: {case.title} · {case.patient.age}세 {case.patient.sex} · 체크리스트 {len(case.checklist)}항목")
print(f"  최종 심사: 【{result['review'].verdict}】 — {result['review'].summary[:80]}…")
