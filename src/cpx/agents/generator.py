"""
① 사례 생성 Agent — 멀티에이전트(생성→비평→수정).

연구 반영(research-llm-cpx-sota): 멀티에이전트 > 단일 · checklist-as-seed ·
  진단조건부 인구통계 다양성(65세男흡연자 편향 차단) · 맥락 일관성 self-check.
비평 단계 = ② reviewer 재사용(생성→②심사→수정 루프).

⚠️ 프로토타입/**가설**. 부산대 실제 사례로 로컬 수용률 검증 전엔 "법칙" 아님.
   RAG 교과서 근거는 후속(rag.py). 현재는 LLM parametric + self-check.
"""
from __future__ import annotations

from cpx.models import CpxCase
from cpx.agents import reviewer
from cpx import llm


def _draft(symptom: str, diagnosis: str, model: str | None = None) -> CpxCase:
    from cpx import rag
    ground = rag.grounding(f"{symptom} {diagnosis} 병력청취 신체진찰 진단", k=3)
    ground_block = f"\n[의학 근거 — 교과서 발췌(RAG), 임상 사실 일관성에 참고]\n{ground}\n" if ground else ""
    prompt = f"""한국 의과대학 CPX 사례를 생성하라. 주증상="{symptom}", 진단="{diagnosis}".{ground_block}
[붙임2] 양식(CpxCase 스키마)으로 채운다:
- demographics: 진단에 **현실적으로** 맞는 나이·성별 (흔한 '65세 남성 흡연자' 편향 피하고 진단조건부로 다양하게)
- patient: 주증상 서술 + 생각/걱정/기대/배경을 구체적으로, **환자 구어체**
- present_illness: 시간순 현병력(평소→며칠전→오늘)
- 가족력·사회력·(여성이면)산부인과력·과거력
- checklist: '의사질문-환자답변' 쌍을 **20개 이상**, domain별(병력청취/신체진찰/환자교육/환자의사관계).
  각 항목 scoring_rule(관찰가능·행동위주) + keywords(동의어 3~6, v0 채점용).
자가검토: 연령-성별-과거력-진단이 임상적으로 일관. 비현실 정보·지어낸 수치 금지."""
    return llm.complete_json(prompt, CpxCase, model=model)


def _revise(case: CpxCase, rv: reviewer.ReviewOut, clinical_must=None, model: str | None = None) -> CpxCase:
    lines = [f"- {f}" for f in rv.fixes]
    for c in (clinical_must or []):
        lines.append(f"- [임상·{c.category}] {c.issue} → {c.suggested_edit} (근거: {c.evidence})")
    fixes = "\n".join(lines) or "- (구체 수정안 없음: 전반적 보강)"
    prompt = f"""다음 CPX 사례를 심사 의견대로 수정해 **완성된 CpxCase**로 반환하라.
[②A 구조 판정] {rv.verdict}
[수정 요청 — 구조(②A) + 임상(②B must_fix)]
{fixes}
[현재 사례(JSON)]
{case.model_dump_json(indent=2)[:8000]}
원래 좋은 부분은 유지하고 지적된 부분만 보강한다."""
    return llm.complete_json(prompt, CpxCase, model=model)


def generate(symptom: str, diagnosis: str, model: str | None = None, rounds: int = 1, clinical: bool = True):
    """생성→(②A 구조심사 + ②B 임상심사)→수정 루프. rounds = **최대 수정 횟수**(심사는 rounds+1회).
    각 수정 후 반드시 재심사하며, 종료조건 = ②A verdict∈{Accept,Minor} AND ②B must_fix=0.
    반환: (case, log). log 끝에 종료상태(accepted/budget_exhausted) 기록. optional 임상지적도 log 보존(감사·재현성).
    ⚠️ ②B 연결은 프로토타입 — H2 검증에서 ②B harmful/안전성 확인 후에만 프로덕션(과대주장 금지)."""
    case = _draft(symptom, diagnosis, model)
    log = ["draft"]
    accepted = False
    for i in range(rounds + 1):                                             # 심사 rounds+1회 · 수정 최대 rounds회
        rv = reviewer.review(case, model)                                   # ②A 구조
        cr = reviewer.review_clinical(case, model) if clinical else None    # ②B 임상(RAG 근거)
        must_fix = [c for c in cr.critiques if c.severity == "must_fix"] if cr else []
        optional = [c for c in cr.critiques if c.severity == "optional"] if cr else []
        accepted = rv.verdict in ("Accept", "Minor") and not must_fix
        log.append(f"심사{i}: ②A={rv.verdict} · ②B must_fix={len(must_fix)} · optional={len(optional)}")
        for c in optional:                                                  # optional 보존(blocking은 아니나 기록)
            log.append(f"  [optional·{c.category}] {c.issue}")
        if accepted or i == rounds:
            break
        case = _revise(case, rv, must_fix, model)
        log.append(f"✏️ 수정 R{i+1}")
    log.append("종료: " + ("✅ accepted (②A Accept/Minor · ②B must_fix=0)" if accepted else "⚠️ budget_exhausted — 수정예산 소진·미충족본 반환"))
    return case.model_copy(update={"case_id": f"gen_{symptom}_{diagnosis}"[:40]}), log
