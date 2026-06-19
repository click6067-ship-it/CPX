"""
② 사례 심사 Agent — `실기문항저자점검표` 루브릭으로 CPX 사례를 검토.

출력: 루브릭 항목별 통과/지적 + 전체 verdict(Accept/Minor/Major/Reject) + 수정 제안.
용도: ①이 생성한 사례(또는 사람이 쓴 초안)를 1차 자동 심사 → 그 다음 교수 HITL.

⚠️ 프로토타입. 전문가 검토를 *대체*하지 않는다. AI 심사가 전문가와 얼마나 맞는지는
   H2 하네스(사례개발피드백 = 전문가 정답지)로 검증 예정. 과대주장 금지.
"""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel
from cpx.models import CpxCase

# 실기문항저자점검표 발췌 (사례선정·상황지침·시나리오·채점표)
RUBRIC = [
    "표준화환자(SP)가 연기로 표현 가능한 사례인가?",
    "초진 사례인가?",
    "흔하거나 위중한(놓치면 안 되는) 질병인가?",
    "학생이 다양한 감별진단을 세울 수 있는가?",
    "제한 시간 내(약 12분) 해결 가능한 분량인가?",
    "상황지침이 '(나이)세 OOO씨가 병원/응급실에 왔다' 형태로 기술되었는가?",
    "환자 시나리오가 환자의 말(구어체)로 기술되었는가? (전문용어 X)",
    "환자의 '생각·걱정·기대·배경'이 구체적으로 기술되었는가?",
    "채점표 항목 수가 적절한가? (대략 30개 전후)",
    "채점표가 한 항목에 한 가지 내용만 평가하는가?",
    "채점표가 관찰가능·행동위주로 기술되었는가?",
    "환자교육 항목이 감별진단·초기 진단계획·교육으로 구성되었는가?",
    "연령·성별·과거력 등 임상 맥락이 진단과 논리적으로 일관되는가? (예: 남성에 산부인과력 X)",
]


class CriterionResult(BaseModel):
    criterion: str
    passed: bool
    comment: str          # 통과/지적 근거 한 줄


class ReviewOut(BaseModel):
    results: list[CriterionResult]
    verdict: Literal["Accept", "Minor", "Major", "Reject"]
    summary: str
    fixes: list[str]      # 우선 수정 제안


# ─────────── ②B 임상 리뷰어 (Codex 검수 후 추가) ───────────
Category = Literal["CLINICAL_CONTENT", "INTERNAL_LOGIC", "SP_FEASIBILITY",
                   "SAFETY_OVERCLAIM", "EDUCATIONAL_ALIGNMENT"]


class Critique(BaseModel):
    category: Category
    issue: str           # 임상 지적
    evidence: str        # 사례 어디서
    suggested_edit: str  # 수정 제안
    severity: Literal["must_fix", "optional"]


class ClinicalReview(BaseModel):
    critiques: list[Critique]
    summary: str


def review_clinical(case: CpxCase, model: str | None = None) -> ClinicalReview:
    """②B: 사례를 *임상적으로* 심사 (구조/형식 제외). 교과서 RAG 근거 위에서."""
    from cpx import llm, rag
    ground = rag.grounding(f"{case.chief_complaint} {case.diagnosis} 핵심 병력 위험인자 신체진찰 감별", k=3)
    gb = f"\n[의학 근거(교과서 RAG) — 이 진단에서 무엇을 물어야/봐야 하는지 참고]\n{ground}\n" if ground else ""
    prompt = f"""당신은 CPX 사례를 **임상적으로** 심사하는 전문의다. 구조/형식이 아니라 **의학 내용**을 본다.
점검 항목:
- 임상 타당성 / 이 진단에서 **꼭 물어야 할 핵심 병력·위험인자 누락**
- red flag(놓치면 안 되는 증상) 누락
- 내적 논리: 연령·성별·직업·과거력·활력징후·진단이 임상적으로 일관한가
- SP 연기 현실성, 인구통계 적합성
- (해당 시) 안전·과대 표현, 교육 정렬
{gb}
각 비평: category(CLINICAL_CONTENT/INTERNAL_LOGIC/SP_FEASIBILITY/SAFETY_OVERCLAIM/EDUCATIONAL_ALIGNMENT) · issue · evidence(사례 근거) · suggested_edit · severity(must_fix/optional). 구조/형식 지적은 하지 말 것(②A 담당).

[사례(JSON)]
{case.model_dump_json(indent=2)[:30000]}"""
    return llm.complete_json(prompt, ClinicalReview, model=model)


def review(case: CpxCase, model: str | None = None) -> ReviewOut:
    from cpx import llm
    rubric = "\n".join(f"{i+1}. {c}" for i, c in enumerate(RUBRIC))
    prompt = f"""당신은 한국 의대 CPX 사례 심사위원이다. 아래 [사례]를 [점검표] 각 항목으로 평가하라.
- 각 항목: passed(true/false) + comment(근거 한 줄, 한국어).
- verdict: Accept(그대로 사용 가능) / Minor(경미한 수정) / Major(중대한 수정) / Reject(부적합).
- summary: 2~3문장 총평. fixes: 우선 수정 제안(있을 때).
임상적 정확성·맥락 일관성을 특히 본다. 과한 칭찬 금지, 문제를 정확히.

[점검표]
{rubric}

[사례(JSON)]
{case.model_dump_json(indent=2, exclude={'demographics'})[:30000]}
"""
    return llm.complete_json(prompt, ReviewOut, model=model)
