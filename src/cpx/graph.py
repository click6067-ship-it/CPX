"""
LangGraph 오케스트레이션 — 사례 개발 루프(① 생성 → ② 심사 → 미흡하면 수정 → 재심사).

LangGraph 개념 (배우는 용):
  · State   = 노드들이 공유하며 갱신하는 딕셔너리(여기선 사례·심사·라운드)
  · Node    = 상태를 받아 일부를 갱신해 반환하는 함수(=우리 에이전트 호출)
  · Edge    = 노드 연결. add_conditional_edges = **분기/루프**(심사 결과로 종료 or 수정)
이 그래프가 함수 호출 대비 주는 것: 상태·분기·루프·(추후 LangSmith)추적·중단/재개를 선언적으로.

⚠️ ③가상환자·④채점은 *학생과 상호작용하는 런타임*이라 이 개발 그래프와 별도(demo_pipeline 참고).
"""
from __future__ import annotations

from typing import Optional, TypedDict
from langgraph.graph import StateGraph, START, END

from cpx.models import CpxCase
from cpx.agents import generator, reviewer


class CaseState(TypedDict):
    symptom: str
    diagnosis: str
    case: Optional[CpxCase]
    review: Optional[reviewer.ReviewOut]            # ②A 구조
    clinical: Optional[reviewer.ClinicalReview]     # ②B 임상
    use_clinical: bool                              # ②B 켜기/끄기 스위치
    rounds: int
    max_rounds: int
    log: list[str]


def n_generate(s: CaseState) -> dict:
    case = generator._draft(s["symptom"], s["diagnosis"])   # ① (RAG 근거 주입됨)
    return {"case": case, "rounds": 0, "log": s.get("log", []) + ["① 생성"]}


def n_review(s: CaseState) -> dict:
    rv = reviewer.review(s["case"])                                                      # ②A 구조
    cr = reviewer.review_clinical(s["case"]) if s.get("use_clinical", True) else None    # ②B 임상(스위치)
    mf = sum(1 for c in cr.critiques if c.severity == "must_fix") if cr else 0
    opt = sum(1 for c in cr.critiques if c.severity == "optional") if cr else 0
    return {"review": rv, "clinical": cr, "log": s["log"] + [f"② 심사: ②A={rv.verdict}·②B must_fix={mf}·optional={opt}"]}


def n_revise(s: CaseState) -> dict:
    must = [c for c in s["clinical"].critiques if c.severity == "must_fix"] if s.get("clinical") else []
    case = generator._revise(s["case"], s["review"], must)   # ① 수정(②A fixes + ②B must_fix)
    return {"case": case, "rounds": s["rounds"] + 1, "log": s["log"] + [f"✏️ 수정 R{s['rounds']+1}"]}


def route(s: CaseState) -> str:
    """② 후 분기: (②A Accept/Minor AND ②B must_fix=0) 또는 라운드 소진 → 종료, 아니면 수정 루프."""
    mf = sum(1 for c in s["clinical"].critiques if c.severity == "must_fix") if s.get("clinical") else 0
    if (s["review"].verdict in ("Accept", "Minor") and mf == 0) or s["rounds"] >= s["max_rounds"]:
        return "end"
    return "revise"


def build():
    g = StateGraph(CaseState)
    g.add_node("generate", n_generate)
    g.add_node("review", n_review)
    g.add_node("revise", n_revise)
    g.add_edge(START, "generate")
    g.add_edge("generate", "review")
    g.add_conditional_edges("review", route, {"end": END, "revise": "revise"})
    g.add_edge("revise", "review")          # 수정 후 다시 심사 = 루프
    return g.compile()


def develop_case(symptom: str, diagnosis: str, max_rounds: int = 2, use_clinical: bool = True) -> CaseState:
    """그래프 실행: (②A Accept/Minor AND ②B must_fix=0) 또는 max_rounds(최대 수정 횟수)까지 개발.
    종료 후 log에 상태(accepted/미충족) 기록."""
    app = build()
    out = app.invoke({"symptom": symptom, "diagnosis": diagnosis,
                      "case": None, "review": None, "clinical": None, "use_clinical": use_clinical,
                      "rounds": 0, "max_rounds": max_rounds, "log": []})
    mf = sum(1 for c in out["clinical"].critiques if c.severity == "must_fix") if out.get("clinical") else 0
    acc = out["review"].verdict in ("Accept", "Minor") and mf == 0
    out["log"].append("종료: " + ("✅ accepted" if acc else f"⚠️ 미충족 (max_rounds {max_rounds} 소진)"))
    return out
