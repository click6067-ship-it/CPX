"""
③ 가상환자 Agent — 텍스트. 환자 페르소나 유지 + 과공개 제어.

Codex R1-7: "과공개 마라"는 단순 프롬프트 룰은 멀티턴서 약하다 → 답변정책을 명시:
  - 사례의 환자 시나리오 + 체크리스트 환자답변만 '허용 사실'로 제공
  - 묻지 않은 정보는 먼저 말하지 않음 (한 번에 한 가지)
  - 진단명·검사결과 선공개 금지, 환자 구어체

(완전한 유한상태(FSM) 항목별 정책은 다음 단계. 지금은 '허용 사실 + 강한 정책 프롬프트'.)
"""
from __future__ import annotations

from cpx.models import CpxCase
from cpx import llm


def _persona(case: CpxCase) -> str:
    p = case.patient
    facts = "\n".join(
        f"- ({it.scoring_rule}) 에 대해 물으면: {it.patient_answer}"
        for it in case.checklist if it.patient_answer
    )
    return f"""당신은 의과대학 CPX의 표준화환자(SP)를 연기한다. 아래 환자가 되어 의대생의 질문에 답하라.

[환자] {p.age}세 {p.sex}, {p.name}, {p.job}. 주증상: {case.chief_complaint}.
상황: {case.situation_instruction}
배경: 일상영향={p.daily_impact} / 기대={p.expectation}

[알고 있는 사실 — 물어보면 이대로만 답한다]
{facts or '- (제공된 세부 답변 없음: 주증상 범위에서 자연스럽게)'}

[연기 규칙 — 매우 중요]
1. **묻는 것에만 답한다.** 묻지 않은 증상·과거력·위험인자를 먼저 말하지 마라.
   (예: "열 있나요?" → "열은 없어요"만. 기침 등 다른 증상 언급 금지)
2. 한두 문장, 환자 구어체로. 의학용어 쓰지 마라.
3. 위 '사실'에 없는 건 모른다고 하거나 자연스럽게 넘긴다.
4. 진단명·검사결과를 먼저 말하지 마라."""


def reply(case: CpxCase, history: list[dict], student_msg: str, model: str | None = None) -> str:
    """history = [{'role':'student'|'patient','text':...}] 누적. 환자의 다음 발화 반환."""
    convo = "\n".join(
        f"{'의사' if m['role'] == 'student' else '환자'}: {m['text']}" for m in history
    )
    prompt = f"{_persona(case)}\n\n[지금까지 대화]\n{convo}\n\n의사: {student_msg}\n환자:"
    return llm.complete(prompt, model=model).strip()
