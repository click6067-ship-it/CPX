"""
🔁 전체 파이프라인 데모 — ① 생성 → ② 심사 → ③ 가상환자 → ④ 채점.
실행: PYTHONPATH=src .venv/bin/python demo_pipeline.py

새 주증상/진단으로 사례를 *생성*해서 4 에이전트를 한 바퀴 돌린다 (toy/가설 — 검증 아님).
"""
from pathlib import Path

from cpx.agents import generator, reviewer, patient
from cpx.agents.grader import grade_llm

SYMPTOM, DIAGNOSIS = "발열", "급성 신우신염"

print(f"━━━ ① 생성: {SYMPTOM} / {DIAGNOSIS} (생성→②심사→수정) ━━━")
case, log = generator.generate(SYMPTOM, DIAGNOSIS, rounds=1)
print(f"  진행: {' → '.join(log)}")
print(f"  ▶ {case.title} · 환자 {case.patient.age}세 {case.patient.sex} · 체크리스트 {len(case.checklist)}항목")
print(f"    상황: {case.situation_instruction}")

print(f"\n━━━ ② 최종 심사 ━━━")
rv = reviewer.review(case)
print(f"  판정: 【{rv.verdict}】 · 통과 {sum(r.passed for r in rv.results)}/{len(rv.results)}")
print(f"  총평: {rv.summary}")

print(f"\n━━━ ③ 가상환자 대화 (스크립트 학생) ━━━")
student_qs = [
    "안녕하세요, 어떻게 오셨어요?",
    "열은 언제부터 났고 몇 도까지 올랐어요?",
    "소변볼 때 따갑거나 자주 마렵진 않으세요?",
    "옆구리나 등 쪽이 아프진 않으세요?",
]
history, lines = [], []
for q in student_qs:
    a = patient.reply(case, history, q)
    history += [{"role": "student", "text": q}, {"role": "patient", "text": a}]
    lines.append(f"의사: {q}\n환자: {a}")
    print(f"  의사: {q}\n  환자: {a}")
transcript = "\n".join(lines)

print(f"\n━━━ ④ 채점 ━━━")
res = grade_llm(case, transcript)
print(f"  {res['total']} ({res['reached']}) · {res['feedback']}")
print("\n✅ ①→②→③→④ 전체 파이프라인 1바퀴 완료 (toy/가설 — 실제 검증은 부산대 사례+전문가 라벨 후)")
