"""
🔁 루프 데모: 사례 → (스크립트 학생 ↔ 가상환자 대화) → 대화로그 → ④ 채점.
실행: PYTHONPATH=src .venv/bin/python demo_loop.py

= thin-vertical의 심장: "환자랑 대화하고 그 자리에서 채점받는다"를 텍스트로.
"""
import json
from pathlib import Path

from cpx.models import CpxCase
from cpx.agents import patient
from cpx.agents.grader import grade_llm

ROOT = Path(__file__).parent
case = CpxCase(**json.loads((ROOT / "data/cases/chestpain_lee.json").read_text(encoding="utf-8")))

# 스크립트 학생(시뮬). 일부러 '위험인자' 질문을 빠뜨림 → ④가 누락 잡아야 함.
student_qs = [
    "안녕하세요, 어떻게 오셨어요?",
    "언제부터 가슴이 아프셨어요?",
    "통증이 조이는 느낌인가요, 아니면 어떤가요?",
    "그 통증이 팔이나 턱으로도 뻗치나요?",
    "숨쉬기 힘드신 건 없으세요?",
    "많이 놀라고 불안하셨겠어요. 바로 검사 도와드릴게요.",
]

print(f"=== 🔁 루프: {case.title} ({case.diagnosis}) ===\n")
history: list[dict] = []
for q in student_qs:
    a = patient.reply(case, history, q)
    history.append({"role": "student", "text": q})
    history.append({"role": "patient", "text": a})
    print(f"  의사: {q}\n  환자: {a}\n")

transcript = "\n".join(
    f"{'의사' if m['role'] == 'student' else '환자'}: {m['text']}" for m in history
)

print("─" * 50)
res = grade_llm(case, transcript)
print(f"④ 채점: {res['total']} ({res['reached']})  ·  {res['feedback']}\n")

# 과공개 체크: 학생이 안 물은 '위험인자'를 환자가 먼저 흘렸나?
patient_text = " ".join(m["text"] for m in history if m["role"] == "patient")
leaked = [k for k in ["담배", "흡연", "고혈압", "당뇨", "가족력"] if k in patient_text]
print(f"과공개 제어 체크(묻지 않은 위험인자 누출): {leaked or '없음 ✅ (정책 준수)'}")
