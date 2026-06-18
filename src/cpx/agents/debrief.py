"""
④ 질적 디브리핑 — 학생 발화별 피드백 (체크리스트 도달/누락 *위에* 얹는 층).

차원(= CPX 표준 채점 기준; 메튜 리포트가 보여준 것을 우리 식으로 투명하게):
  · 유도성 질문(leading)   · 전문용어 사용(jargon)   · 개방형/폐쇄형   · "다음에 고칠 문장"(rewrite)

⚠️ 이 판정도 하네스로 검증해야 함(아직 미검증). 과대주장 금지.
"""
from __future__ import annotations

from pydantic import BaseModel
from cpx.models import CpxCase


class UtteranceFeedback(BaseModel):
    utterance: str            # 학생(의사) 발화
    q_type: str               # "개방형" | "폐쇄형" | "진술"
    is_leading: bool          # 유도성 질문(답을 제시·유도)
    uses_jargon: bool         # 환자에게 낯선 전문용어 사용
    jargon_terms: list[str]   # 그 용어들
    issue: str                # 문제 한 줄(없으면 "")
    rewrite: str              # 더 나은 표현(문제 있을 때만, 없으면 "")


class DebriefOut(BaseModel):
    items: list[UtteranceFeedback]


def debrief(case: CpxCase, transcript: str, model: str | None = None) -> DebriefOut:
    from cpx import llm
    prompt = f"""당신은 한국 의대 CPX 채점관이다. 아래 대화에서 **의사(학생) 발화만** 각각 평가하라(환자 발화 제외).
각 발화에 대해:
- q_type: 개방형 / 폐쇄형 / 진술
- is_leading: 유도성 질문인가? (답을 직접 제시·유도해 환자를 끌고 감. 예: "왼팔로 방사되죠?")
- uses_jargon + jargon_terms: 환자에게 낯선 전문용어를 썼는가? (예: "방사", "발열", "기왕력") → 해당 용어 나열
- issue: 위 문제를 한 줄로(문제 없으면 "")
- rewrite: 더 나은 표현 한 문장(문제 있을 때만; 없으면 "")

사례 맥락: {case.chief_complaint} / {case.diagnosis}

[대화]
{transcript}

의사 발화 순서대로 JSON으로."""
    return llm.complete_json(prompt, DebriefOut, model=model)
