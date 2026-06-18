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
    review: Optional[reviewer.ReviewOut]
    rounds: int
    max_rounds: int
    log: list[str]


def n_generate(s: CaseState) -> dict:
    case = generator._draft(s["symptom"], s["diagnosis"])   # ① (RAG 근거 주입됨)
    return {"case": case, "rounds": 0, "log": s.get("log", []) + ["① 생성"]}


def n_review(s: CaseState) -> dict:
    rv = reviewer.review(s["case"])                          # ②
    return {"review": rv, "log": s["log"] + [f"② 심사:{rv.verdict}"]}


def n_revise(s: CaseState) -> dict:
    case = generator._revise(s["case"], s["review"])         # ① 수정
    return {"case": case, "rounds": s["rounds"] + 1, "log": s["log"] + [f"✏️ 수정 R{s['rounds']+1}"]}


def route(s: CaseState) -> str:
    """② 심사 후 분기: Accept거나 라운드 소진 → 종료, 아니면 수정 루프."""
    if s["review"].verdict == "Accept" or s["rounds"] >= s["max_rounds"]:
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


def develop_case(symptom: str, diagnosis: str, max_rounds: int = 2) -> CaseState:
    """그래프 실행: 사례를 Accept 또는 max_rounds까지 개발."""
    app = build()
    return app.invoke({"symptom": symptom, "diagnosis": diagnosis,
                       "case": None, "review": None, "rounds": 0,
                       "max_rounds": max_rounds, "log": []})
