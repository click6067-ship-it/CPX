"""온톨로지 validator 데모 — 미팅용(합성 사례, 결정론·LLM 0회).

"그래프가 필수요소를 강제 + 과공개를 막는다"를 한눈에 — 같은 ACS 카드, 사례 품질만 다름:
  ① 정상 사례    → pass            (모든 검사 통과)
  ② 과공개 결함   → disclosure fail (물어야 답할 정보를 환자가 자발 노출 = CPX 고유 위반)
  ③ 필수누락 결함  → required/red_flags fail (강제 요소가 통째로 빠짐)

실행: PYTHONPATH=src .venv/bin/python demo_ontology_validator.py
주의: 합성 사례(손작성). 'pass'=구조·어휘 정합일 뿐 '임상 타당' 아님(교수 검증 전 draft 카드).
      실 사례 핀고정은 tests/ + data/cases/chestpain_lee.json.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
from cpx.ontology_validator import validate, load_cards  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
YAML = os.path.join(ROOT, "ontology", "chest_pain.yaml")
ACS = "acute_coronary_syndrome"


def _checklist() -> list[dict]:
    """ACS 카드 6항목을 모두 다루는 case checklist(질문·답변 = '질문 시' 채널, 자발 아님)."""
    return [
        {"id": "hx_onset", "domain": "병력청취", "scoring_rule": "통증 발병 시점을 물었다",
         "keywords": ["언제", "시작", "갑자기"], "patient_answer": "오늘 아침 갑자기 시작했어요"},
        {"id": "hx_char", "domain": "병력청취", "scoring_rule": "통증 양상을 물었다",
         "keywords": ["조이", "쥐어", "양상"], "patient_answer": "쥐어짜는 느낌이에요"},
        {"id": "hx_radi", "domain": "병력청취", "question_open": "어디로 퍼지나요?",
         "scoring_rule": "방사통을 물었다",
         "keywords": ["방사", "어깨", "턱"], "patient_answer": "왼팔과 턱으로 방사됩니다"},
        {"id": "hx_aggrav", "domain": "병력청취", "scoring_rule": "악화·완화 인자를 물었다",
         "keywords": ["악화", "완화", "쉬면"], "patient_answer": "쉬면 조금 나아져요"},
        {"id": "hx_assoc", "domain": "병력청취", "scoring_rule": "동반증상을 물었다",
         "keywords": ["식은땀", "호흡곤란", "숨"], "patient_answer": "식은땀이 나고 숨이 찹니다"},
        {"id": "hx_redflag", "domain": "병력청취", "scoring_rule": "경고증상(실신·저혈압)을 물었다",
         "keywords": ["실신", "저혈압", "어지러"], "patient_answer": "실신은 없었어요"},
        {"id": "hx_risk", "domain": "병력청취", "scoring_rule": "심혈관 위험인자를 물었다",
         "keywords": ["흡연", "고혈압", "당뇨"], "patient_answer": "담배를 피웁니다"},
    ]


def _base(**over) -> dict:
    """ACS 합성 사례 골격. over 로 chief_complaint·situation·checklist 만 바꿔 결함을 주입."""
    return {
        "case_id": over.get("case_id", "demo"),
        "title": over.get("title", "합성 흉통 사례(데모)"),
        "chief_complaint": over.get("chief_complaint", ""),
        "diagnosis": "급성 관상동맥증후군(ACS)",
        "situation_instruction": over.get("situation_instruction", "계단을 오를 때 통증이 발생했습니다"),
        "demographics": {"sex": "남", "age": 58, "note": ""},
        "patient": {"sex": "남", "age": 58, "name": "홍길동", "job": "회사원"},
        "present_illness": [],
        "checklist": over.get("checklist", _checklist()),
    }


CASES = [
    (
        "① 정상 사례 (잘 만든 사례)",
        "자발 채널엔 압박감만, 방사·식은땀은 '물었을 때'만 답함 → 과공개 0, 필수 다 충족",
        _base(case_id="clean", chief_complaint="가슴을 쥐어짜는 듯한 압박감이 있어요"),
    ),
    (
        "② 과공개 결함 (over-disclosure)",
        "환자가 묻기도 전에 방사통·식은땀을 자발 노출 → CPX 과공개 위반"
        " (SNOMED 등 표준 온톨로지는 못 잡는 CPX 고유 규칙)",
        _base(
            case_id="overdisclose",
            chief_complaint="가슴이 쥐어짜듯 아프고 식은땀이 줄줄 나면서 통증이 왼팔과 턱으로 방사돼요",
        ),
    ),
    (
        "③ 필수누락 결함 (missing required)",
        "그래프가 강제한 필수요소(쥐어짜는 압박감·운동 연관)와 red flag(저혈압·실신)가 통째로 빠짐"
        " → '근거 갖고 생성'의 반례를 결정론으로 검출",
        _base(
            case_id="missing_required",
            chief_complaint="어제부터 가슴이 답답한 느낌이 들어요",
            situation_instruction="언제 생기는지는 잘 모르겠어요",
            checklist=[
                {"id": "hx_onset", "domain": "병력청취", "scoring_rule": "발병을 물었다",
                 "keywords": ["언제"], "patient_answer": "어제부터요"},
                {"id": "hx_dur", "domain": "병력청취", "scoring_rule": "기간을 물었다",
                 "keywords": ["기간", "얼마나"], "patient_answer": "하루 정도 됐어요"},
            ],
        ),
    ),
]


def main() -> None:
    diseases, labels = load_cards(YAML)
    bar = "=" * 72
    print(bar)
    print("온톨로지 validator 데모 — 흉통 ACS 카드 대조 (결정론·LLM 0회·재현가능)")
    print("같은 카드, 사례 품질만 다름 → validator 가 결함을 기계적으로 짚어냄")
    print(bar)

    summary: list[tuple[str, str, list[str]]] = []
    for title, caption, case in CASES:
        r = validate(case, diseases, labels, disease_id=ACS)
        print(f"\n\n{'━' * 72}\n▶ {title}\n  {caption}\n{'━' * 72}")
        print(r.to_markdown())
        hot: list[str] = []
        for key, c in r.checks.items():
            if c.status not in ("fail", "flag"):
                continue
            if c.violations:
                detail = " · ".join(f"{h.concept_id}={h.note}" for h in c.violations)
            elif c.missing:
                detail = "missing " + ", ".join(h.concept_id for h in c.missing)
            else:
                detail = ""
            hot.append(f"{key}={c.status}({detail})" if detail else f"{key}={c.status}")
        summary.append((title, r.overall, hot))

    print(f"\n\n{bar}\n요약 (overall + 핵심 검출)\n{bar}")
    for title, overall, hot in summary:
        print(f"  {overall.upper():5} | {title}")
        for h in hot:
            print(f"            - {h}")
    print(
        "\n⚠ 합성 사례(손작성). 'pass'=구조·어휘 정합일 뿐 '임상 타당' 아님"
        " (교수 검증 전 draft 카드)."
    )


if __name__ == "__main__":
    main()
