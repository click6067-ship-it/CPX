"""
H4-smoke 하네스 실행 — v0(키워드) vs LLM(의미) 채점을 gold 라벨과 비교.
실행: PYTHONPATH=src .venv/bin/python harness_smoke.py
"""
from pathlib import Path

from cpx.agents.grader import grade, grade_llm
from cpx.harness import runner

ROOT = Path(__file__).parent


def interp(k: float) -> str:
    if k < 0.2: return "미미"
    if k < 0.4: return "약함"
    if k < 0.6: return "보통"
    if k < 0.8: return "상당"
    return "거의완벽"


print("=== H4-smoke 하네스 (손-라벨 fixture 3건) ===\n")
v0 = runner.run(ROOT, grade)
llm = runner.run(ROOT, grade_llm)

print(f"  채점 항목 수: {v0['n']}개 (gold 라벨 대비)\n")
print(f"  {'채점기':9s} {'정확도':>5s} {'P':>5s} {'R':>5s} {'F1':>5s} {'kappa':>6s}  해석")
for name, r in [("v0(키워드)", v0), ("LLM(의미)", llm)]:
    print(f"  {name:9s} {r['accuracy']:>5.2f} {r['precision']:>5.2f} {r['recall']:>5.2f} {r['f1']:>5.2f} {r['kappa']:>6.2f}  {interp(r['kappa'])}")
print("  (P=정밀도: 헛점 안 주나 · R=재현율: 안 놓치나 · F1=조화평균 · kappa=우연보정 일치)")

c = runner.consistency(ROOT, n=3)
print(f"\n  LLM 일관성({c['case']}, {c['runs']}회 반복): 안정성 {c['stability']:.2f}")
print("\n  ⚠️ SMOKE: 손 라벨·소표본 = 단위테스트. 타당성 kappa는 실제 학생 transcript + 임상교원 라벨 후(H4-real).")
