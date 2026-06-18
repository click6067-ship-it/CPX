"""
④ 채점 Agent. aristo-mini `score→판정` 오마주 (각 체크리스트 항목에 점수→도달/누락).

- grade()      = v0 결정론 키워드 (의존성·API 0, smoke/단위테스트용)
- grade_llm()  = LLM 의미매칭 (동의어·의역 인식 — v0 한계 극복)

⚠️ 어느 쪽 점수든 타당성(kappa) 주장은 실제 학생 transcript + 인간 라벨로
   H4-real을 돌린 뒤에만. (architecture §5, Codex R2)
"""
from __future__ import annotations

from pydantic import BaseModel
from cpx.models import CpxCase, ChecklistItem


# ─────────── v0: 결정론 키워드 ───────────
def _reached_v0(item: ChecklistItem, transcript: str) -> bool:
    """keywords 중 하나라도 있으면 도달 (동의어 OR = D2 "또는"). 의미는 못 봄."""
    return any(kw in transcript for kw in item.keywords) if item.keywords else False


# ─────────── LLM: 의미매칭 ───────────
class _ItemVerdict(BaseModel):
    id: str
    reached: bool
    reason: str


class _GradeOut(BaseModel):
    verdicts: list[_ItemVerdict]


def _verdicts_llm(case: CpxCase, transcript: str, model: str | None = None) -> dict[str, _ItemVerdict]:
    from cpx import llm
    items_desc = "\n".join(f"- {it.id} [{it.domain}]: {it.scoring_rule}" for it in case.checklist)
    prompt = f"""당신은 한국 의과대학 CPX(임상수행평가) 채점관이다.
아래 [대화]를 보고 각 [체크리스트] 항목을 학생이 *수행했는지* 예/아니오로 판정하라.
- 표현이 달라도 의미가 같으면 '수행함'으로 인정한다 (예: "심장마비"="심근경색", "묽게 나와요"="설사 형태 질문").
- 학생이 묻거나 행하지 않았으면 '안함'.
- 의사(학생)의 발화 기준으로만 판정.

[대화]
{transcript}

[체크리스트]
{items_desc}

각 항목 id마다 reached(true/false)와 한 줄 reason(한국어)을 JSON으로 출력."""
    out = llm.complete_json(prompt, _GradeOut, model=model)
    return {v.id: v for v in out.verdicts}


# ─────────── 공통 집계 ───────────
def _aggregate(case: CpxCase, reached_map: dict, reasons: dict | None = None) -> dict:
    reasons = reasons or {}
    items = []
    for it in case.checklist:
        reached = reached_map.get(it.id, False)
        items.append({
            "id": it.id, "domain": it.domain, "reached": reached,
            "score": it.points if reached else 0.0, "max": it.points,
            "rule": it.scoring_rule, "reason": reasons.get(it.id, ""),
        })
    by_domain: dict[str, dict] = {}
    for r in items:
        d = by_domain.setdefault(r["domain"], {"got": 0.0, "max": 0.0, "missed": []})
        d["max"] += r["max"]
        d["got"] += r["score"] if r["reached"] else 0.0
        if not r["reached"]:
            d["missed"].append(r["id"])
    got = sum(r["score"] for r in items)
    mx = sum(r["max"] for r in items)
    n = sum(1 for r in items if r["reached"])
    return {
        "case": case.case_id, "items": items, "by_domain": by_domain,
        "total": f"{got:g}/{mx:g}", "reached": f"{n}/{len(items)}",
        "feedback": _feedback(items),
    }


def grade(case: CpxCase, transcript: str) -> dict:
    """v0 결정론 키워드 채점."""
    return _aggregate(case, {it.id: _reached_v0(it, transcript) for it in case.checklist})


def grade_llm(case: CpxCase, transcript: str, model: str | None = None) -> dict:
    """LLM 의미매칭 채점."""
    vmap = _verdicts_llm(case, transcript, model)
    return _aggregate(
        case,
        {k: v.reached for k, v in vmap.items()},
        {k: v.reason for k, v in vmap.items()},
    )


def _feedback(items: list[dict]) -> str:
    missed = [r["id"] for r in items if not r["reached"]]
    if not missed:
        return "모든 체크리스트 항목 도달 ✅"
    return f"누락 {len(missed)}개: {', '.join(missed)} — 이 항목들을 물어보지 않았습니다."
