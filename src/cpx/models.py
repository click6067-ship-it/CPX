"""
CpxCase 데이터 계약 (= [붙임2] CPX 개발 양식).

모든 Agent(생성·심사·가상환자·채점)가 공유하는 단일 "계약".
LLM은 이 스키마로만 출력(구조화 출력)하게 강제한다.

⚠️ 고도(altitude): Pydantic은 **구조(필드·타입)만** 보장한다.
   의학적 정확성·한국어 자연성·체크리스트 관찰가능성 같은 *내용* 검증은
   별도 validators.py(의미 검증기)의 몫이다. (architecture.md §2, Codex R1-16)
"""
from __future__ import annotations

from typing import Literal, Optional
from pydantic import BaseModel, Field

# CPX 기능 영역 (배점: 병력40·진찰30·교육5·PPI20·사이5 — [붙임2])
Domain = Literal["병력청취", "신체진찰", "환자교육", "환자의사관계", "사이시험"]


class VitalSigns(BaseModel):
    bp: str            # 혈압 "120/80"
    hr: int            # 맥박
    rr: int            # 호흡
    bt: float          # 체온


class HistoryItem(BaseModel):
    """개조식 현병력 (시간순)."""
    time_point: str    # "평소" / "7일 전" / "5일 전" ...
    detail: str


class ChecklistItem(BaseModel):
    """채점 항목 = 의사질문-환자답변 쌍. ④채점의 최소 단위."""
    id: str
    domain: Domain
    question_open: Optional[str] = None    # 개방형
    question_closed: Optional[str] = None  # 폐쇄형
    patient_answer: str = ""
    scoring_rule: str                      # 관찰가능·행동위주, "또는"으로 표현 (D2)
    keywords: list[str] = Field(default_factory=list)  # v0 결정론 채점용(동의어 OR)
    is_binary: bool = True                 # 예/아니오 (D1). PPI는 별도 경로(architecture §3-④)
    points: float = 1.0


class Patient(BaseModel):
    """표준화환자(SP) 시나리오 — 1인칭 연기 지침."""
    sex: str
    age: int
    name: str
    job: str = ""
    daily_impact: str = ""
    mood_usual: str = ""
    mood_now: str = ""
    thoughts_concerns: str = ""
    expectation: str = ""
    background: str = ""
    knows: str = ""           # 증상에 대해 아는 것
    wants_to_know: str = ""   # 알고 싶은 것
    nonverbal: str = ""       # 표정·자세·복장 (비언어 연기)


class FunctionWeights(BaseModel):
    """기능별 배점 (합 100). [붙임2] 기본값."""
    history_taking: int = 40      # 병력청취
    physical_exam: int = 30       # 신체진찰
    patient_education: int = 5    # 환자교육
    ppi: int = 20                 # 환자의사관계
    inter_station: int = 5        # 사이시험


class Demographics(BaseModel):
    """진단조건부 인구통계 prior로 생성 (Codex R1-15)."""
    sex: str = ""
    age: int = 0
    note: str = ""


class CpxCase(BaseModel):
    """CPX 사례 한 건. = [붙임2] 워크시트 1장."""
    case_id: str
    title: str
    chief_complaint: str      # 주증상
    diagnosis: str
    function_weights: FunctionWeights = Field(default_factory=FunctionWeights)
    demographics: Demographics = Field(default_factory=Demographics)
    situation_instruction: str = ""
    vitals: Optional[VitalSigns] = None
    examinee_task: str = ""
    patient: Patient
    present_illness: list[HistoryItem] = Field(default_factory=list)
    family_hx: str = ""
    social_hx: str = ""
    obgyn_hx: Optional[str] = None
    past_hx: str = ""
    checklist: list[ChecklistItem]
