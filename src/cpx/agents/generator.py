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
    prompt = f"""한국 의과대학 CPX 사례를 생성하라. 주증상="{symptom}", 진단="{diagnosis}".
[붙임2] 양식(CpxCase 스키마)으로 채운다:
- demographics: 진단에 **현실적으로** 맞는 나이·성별 (흔한 '65세 남성 흡연자' 편향 피하고 진단조건부로 다양하게)
- patient: 주증상 서술 + 생각/걱정/기대/배경을 구체적으로, **환자 구어체**
- present_illness: 시간순 현병력(평소→며칠전→오늘)
- 가족력·사회력·(여성이면)산부인과력·과거력
- checklist: '의사질문-환자답변' 쌍을 **20개 이상**, domain별(병력청취/신체진찰/환자교육/환자의사관계).
  각 항목 scoring_rule(관찰가능·행동위주) + keywords(동의어 3~6, v0 채점용).
자가검토: 연령-성별-과거력-진단이 임상적으로 일관. 비현실 정보·지어낸 수치 금지."""
    return llm.complete_json(prompt, CpxCase, model=model)


def _revise(case: CpxCase, rv: reviewer.ReviewOut, model: str | None = None) -> CpxCase:
    fixes = "\n".join(f"- {f}" for f in rv.fixes) or "- (구체 수정안 없음: 전반적 보강)"
    prompt = f"""다음 CPX 사례를 심사 의견대로 수정해 **완성된 CpxCase**로 반환하라.
[심사 판정] {rv.verdict}
[수정 요청]
{fixes}
[현재 사례(JSON)]
{case.model_dump_json(indent=2)[:8000]}
원래 좋은 부분은 유지하고 지적된 부분만 보강한다."""
    return llm.complete_json(prompt, CpxCase, model=model)


def generate(symptom: str, diagnosis: str, model: str | None = None, rounds: int = 1):
    """생성→(②심사→수정) rounds회. 반환: (case, [라운드별 verdict])."""
    case = _draft(symptom, diagnosis, model)
    log = ["draft"]
    for i in range(rounds):
        rv = reviewer.review(case, model)
        log.append(f"R{i+1}:{rv.verdict}")
        if rv.verdict == "Accept":
            break
        case = _revise(case, rv, model)
    return case.model_copy(update={"case_id": f"gen_{symptom}_{diagnosis}"[:40]}), log
