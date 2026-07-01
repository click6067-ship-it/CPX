"""ontology_validator 결정론 스냅샷/회귀 테스트.

- 실 gold(data/cases/chestpain_lee.json)로 검사4 핵심(spontaneous_missing) 핀고정.
- 합성 사례(한국어 라벨 텍스트 fixture)로 통과·실패·위반·모순·스킵·해석에러를 각각 검증.
- 입력 3형태(CpxCase struct / dict / 자유텍스트 str)와 ontology 3주입(path / dict / list) 커버.
- LLM 0회·IO 0~1회 → run-twice 동일성(결정론) 검증.

실행: PYTHONPATH=src .venv/bin/python -m pytest tests/test_ontology_validator.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cpx.ontology_validator import (  # noqa: E402
    DEFAULT_CONFIG,
    CardResolutionError,
    OntologyReport,
    ValidatorConfig,
    load_cards,
    validate,
)

YAML = ROOT / "ontology" / "chest_pain.yaml"
GOLD = ROOT / "data" / "cases" / "chestpain_lee.json"
ACS = "acute_coronary_syndrome"

# 파일 IO 1회(모듈 로드 시) → 이후 list 주입으로 검사들은 파일 IO 0.
DISEASES, LABELS = load_cards(YAML)


# ── fixture helpers ──────────────────────────────────────────────────────────
def _item(**kw) -> dict:
    """case checklist 항목(자유생성 id·한국어 자유텍스트). 필요한 키만 채운다."""
    base = {
        "id": kw.get("id", "x"),
        "domain": kw.get("domain", "병력청취"),
        "question_open": kw.get("question_open"),
        "question_closed": kw.get("question_closed"),
        "scoring_rule": kw.get("scoring_rule", ""),
        "keywords": kw.get("keywords", []),
        "patient_answer": kw.get("patient_answer", ""),
    }
    return base


def _case(**over) -> dict:
    """ACS 합성 사례(자발채널엔 방사/식은땀 없음 = 누설 없음이 기본)."""
    c = {
        "case_id": over.get("case_id", "syn"),
        "title": "합성 흉통 사례",
        "chief_complaint": over.get("chief_complaint", "가슴을 쥐어짜는 듯한 압박감이 있어요"),
        "diagnosis": over.get("diagnosis", "급성 관상동맥증후군(ACS)"),
        "situation_instruction": over.get(
            "situation_instruction", "계단을 오를 때 통증이 발생했습니다"
        ),
        "demographics": over.get("demographics", {"sex": "남", "age": 58, "note": ""}),
        "vitals": over.get("vitals"),
        "patient": over.get("patient", {"sex": "남", "age": 58, "name": "홍길동", "job": "회사원"}),
        "present_illness": over.get("present_illness", []),
        "obgyn_hx": over.get("obgyn_hx"),
        "family_hx": over.get("family_hx", ""),
        "social_hx": over.get("social_hx", ""),
        "past_hx": over.get("past_hx", ""),
        "checklist": over.get("checklist", _full_checklist()),
    }
    return c


def _full_checklist() -> list[dict]:
    """ACS 6항목을 충분히 커버하는 case checklist(asked/probe 채널 — 자발 아님)."""
    return [
        _item(id="hx_onset", scoring_rule="통증 발병 시점을 물었다",
              keywords=["언제", "시작", "갑자기"], patient_answer="오늘 아침에 갑자기 시작했어요"),
        _item(id="hx_char", scoring_rule="통증 양상을 물었다",
              keywords=["조이", "쥐어", "양상"], patient_answer="쥐어짜는 느낌이에요"),
        _item(id="hx_radi", question_open="통증이 어디로 퍼지나요?", scoring_rule="방사통을 물었다",
              keywords=["방사", "어깨", "턱"], patient_answer="왼팔과 턱으로 방사됩니다"),
        _item(id="hx_assoc", scoring_rule="동반증상을 물었다",
              keywords=["식은땀", "호흡곤란", "숨"], patient_answer="식은땀이 나고 숨이 찹니다"),
        _item(id="hx_redflag", scoring_rule="경고증상을 물었다",
              keywords=["실신", "저혈압", "어지러"], patient_answer="실신은 없었어요"),
        _item(id="hx_risk", scoring_rule="심혈관 위험인자를 물었다",
              keywords=["흡연", "고혈압", "당뇨"], patient_answer="담배를 피웁니다"),
    ]


# ── 1. 실 gold: 검사4 spontaneous_missing 핀고정(헤드라인) ──────────────────────
def test_gold_disclosure_spontaneous_missing():
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    r = validate(gold, DISEASES, LABELS)
    assert r.matched_disease_id == ACS          # "급성 심근경색 (감별: 협심증)" → ACS 단일 해석
    disc = r.checks["disclosure"]
    assert disc.status == "fail"
    viol = {h.concept_id: h.note for h in disc.violations}
    assert "chest_pressure" in viol
    assert viol["chest_pressure"] == "spontaneous_missing"
    # 자발채널에 방사/식은땀 없음 → 누설(leaked) 위반은 없어야
    assert all(h.note != "leaked_before_asked" for h in disc.violations)


def test_gold_overall_and_redflags():
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    r = validate(gold, DISEASES, LABELS)
    assert r.overall == "fail"                  # disclosure/red_flags 등 → 최악값 fail
    assert r.checks["red_flags"].status == "fail"   # hypotension·syncope 전부 부재
    # 거짓 모순 금지: 위험인자 질문(generic) 때문에 contradiction 이 켜지면 안 됨
    assert r.checks["contradiction"].status == "pass"


# ── 2. 통과(happy) 합성 사례: required/red_flags/discriminators/disclosure/contradiction pass ──
def test_clean_case_passes_core_checks():
    r = validate(_case(case_id="clean"), DISEASES, LABELS, disease_id=ACS)
    assert r.checks["required_coverage"].status == "pass"     # chest_pressure·exertional 모두 HIGH
    assert r.checks["red_flags"].status == "pass"             # hypotension·syncope 커버
    assert r.checks["discriminators"].status == "pass"        # radiation·diaphoresis·dyspnea HIGH
    assert r.checks["disclosure"].status == "pass"            # 자발 누설 없음 + chest_pressure 자발 present
    assert r.checks["contradiction"].status == "pass"
    assert r.overall in {"pass", "flag"}                      # checklist_mapping 부분→flag 허용


def test_clean_disclosure_present_not_leaked():
    r = validate(_case(case_id="clean2"), DISEASES, LABELS, disease_id=ACS)
    disc = r.checks["disclosure"]
    present_ids = {h.concept_id for h in disc.present}
    assert "chest_pressure" in present_ids       # 자발채널에 압박감 있음(누락 아님)
    assert not disc.violations                    # 방사/식은땀은 checklist(asked)에만 → 누설 아님


# ── 3. 위반: disclose_if_asked 항목을 환자가 자발 노출(leaked_before_asked) ──────
def test_leak_before_asked_is_violation():
    leaky = _case(
        case_id="leak",
        chief_complaint="가슴이 쥐어짜듯 아프고 식은땀이 줄줄 나면서 통증이 왼팔과 턱으로 방사돼요",
    )
    r = validate(leaky, DISEASES, LABELS, disease_id=ACS)
    disc = r.checks["disclosure"]
    assert disc.status == "fail"
    leaked = {h.concept_id for h in disc.violations if h.note == "leaked_before_asked"}
    assert {"radiation_to_left_arm_or_jaw", "diaphoresis"} <= leaked
    # chest_pressure 는 자발에 있어야 정상(누락 위반 아님)
    assert "chest_pressure" not in {h.concept_id for h in disc.violations}


# ── 4. 모순(contradiction) ──────────────────────────────────────────────────
def test_male_with_obgyn_hx_violation():
    c = _case(case_id="m_obgyn", obgyn_hx="자궁근종 절제술 과거력")
    r = validate(c, DISEASES, LABELS, disease_id=ACS)
    con = r.checks["contradiction"]
    assert con.status == "fail"
    assert "male_with_obgyn_hx" in {h.concept_id for h in con.violations}


def test_male_with_empty_obgyn_no_violation():
    # 부정어("없음")는 모순 아님(거짓모순 방지)
    c = _case(case_id="m_obgyn_neg", obgyn_hx="없음")
    r = validate(c, DISEASES, LABELS, disease_id=ACS)
    assert r.checks["contradiction"].status == "pass"


def test_sex_mismatch_violation():
    c = _case(
        case_id="sexmix",
        demographics={"sex": "남", "age": 58, "note": ""},
        patient={"sex": "여", "age": 58, "name": "홍길동"},
        obgyn_hx=None,
    )
    r = validate(c, DISEASES, LABELS, disease_id=ACS)
    con = r.checks["contradiction"]
    assert con.status == "fail"
    assert "sex_mismatch" in {h.concept_id for h in con.violations}


# ── 5. 카드 선택(진단 역매칭) ────────────────────────────────────────────────
def test_diagnosis_resolves_to_acs_head_first():
    c = _case(diagnosis="급성 심근경색 (감별: 협심증)")
    r = validate(c, DISEASES, LABELS)            # disease_id 미지정 → 역매칭
    assert r.matched_disease_id == ACS


def test_unresolvable_diagnosis_raises_when_strict():
    c = _case(diagnosis="원인 미상의 흉통")        # 진단 동의어 0개
    with pytest.raises(CardResolutionError):
        validate(c, DISEASES, LABELS)            # strict_diagnosis_match=True(기본)


def test_unresolvable_diagnosis_falls_back_when_not_strict():
    cfg = ValidatorConfig(strict_diagnosis_match=False)
    c = _case(diagnosis="원인 미상의 흉통")
    r = validate(c, DISEASES, LABELS, config=cfg)
    assert r.matched_disease_id == ACS           # primary 채택
    assert any("diagnosis_unresolved" in w for w in r.warnings)


def test_disease_id_override_skips_resolution():
    c = _case(diagnosis="급성 심근경색 (감별: 협심증)")
    r = validate(c, DISEASES, LABELS, disease_id="gerd")
    assert r.matched_disease_id == "gerd"


# ── 6. 스킵: red_flags=[] (musculoskeletal) · disclosure 없는 카드 ─────────────
def test_skip_empty_redflags_and_missing_disclosure():
    c = _case(diagnosis="근골격계 흉통")
    r = validate(c, DISEASES, LABELS, disease_id="musculoskeletal_chest_pain")
    assert r.checks["red_flags"].status == "skip"     # YAML red_flags: []
    assert r.checks["disclosure"].status == "skip"    # disclosure 키 없음


# ── 7. 입력 3형태 · ontology 3주입 ───────────────────────────────────────────
def test_input_cpxcase_struct():
    from cpx.models import ChecklistItem, CpxCase, Patient

    case = CpxCase(
        case_id="struct",
        title="t",
        chief_complaint="가슴을 쥐어짜는 압박감",
        diagnosis="급성 관상동맥증후군(ACS)",
        patient=Patient(sex="남", age=58, name="홍길동"),
        checklist=[
            ChecklistItem(id="c1", domain="병력청취",
                          scoring_rule="통증 양상을 물었다", keywords=["쥐어", "양상"]),
        ],
    )
    r = validate(case, DISEASES, LABELS)         # CpxCase 그대로 수용(변환 불필요)
    assert isinstance(r, OntologyReport)
    assert r.matched_disease_id == ACS


def test_input_freetext_string():
    r = validate(
        "환자가 가슴을 쥐어짜는 압박감과 식은땀을 호소한다",
        DISEASES, LABELS, disease_id=ACS,
    )
    assert isinstance(r, OntologyReport)
    assert any("freetext_mode" in w for w in r.warnings)   # 자유텍스트 제한 경고


def test_ontology_injection_paths():
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    # (a) yaml 경로 직접
    r_path = validate(gold, str(YAML))
    # (b) raw dict 주입
    raw = {"diseases": DISEASES, "labels": LABELS, "meta": {"review_status": "draft"}}
    r_dict = validate(gold, raw)
    # (c) list 주입(+labels 인자)
    r_list = validate(gold, DISEASES, LABELS)
    assert r_path.matched_disease_id == r_dict.matched_disease_id == r_list.matched_disease_id == ACS
    # 세 경로 결과 동일(결정론)
    assert r_path.to_dict() == r_dict.to_dict() == r_list.to_dict()


# ── 8. 결정론·직렬화 ─────────────────────────────────────────────────────────
def test_determinism_run_twice_identical():
    c = _case(case_id="det")
    r1 = validate(c, DISEASES, LABELS, disease_id=ACS)
    r2 = validate(c, DISEASES, LABELS, disease_id=ACS)
    assert r1.to_dict() == r2.to_dict()


def test_serialization_json_and_markdown():
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    r = validate(gold, DISEASES, LABELS)
    parsed = json.loads(r.to_json())             # JSON 왕복
    assert parsed["matched_disease_id"] == ACS
    assert set(parsed["checks"]) == {
        "required_coverage", "red_flags", "discriminators",
        "disclosure", "contradiction", "checklist_mapping",
    }
    md = r.to_markdown()
    assert "draft 카드 기준" in md                 # 과대주장 차단 면책 노출
    assert "임상 타당성 미검증" in md


# ── 9. config 핀고정(스냅샷 회귀가드) ────────────────────────────────────────
def test_default_config_pinned():
    assert DEFAULT_CONFIG.token_match_ratio == 0.5
    assert DEFAULT_CONFIG.strict_diagnosis_match is True
    assert DEFAULT_CONFIG.strict_discriminators is False
    assert ("exertional_or_rest_onset", "no_exertional_relation") in DEFAULT_CONFIG.mutual_exclusions
    assert "chest_pressure" in DEFAULT_CONFIG.synonyms


# ── 10. 2-렌즈 분리(positive vs asked) + negation (Codex 적대검수 2026-06-30) ──────
def _facts_case(**over) -> dict:
    """환자 사실/체크리스트만 정밀 주입하는 최소 ACS 케이스(렌즈 격리용)."""
    return {
        "case_id": "lens", "title": "t", "diagnosis": "급성 관상동맥증후군(ACS)",
        "chief_complaint": over.get("chief_complaint", "가슴 압박감"),
        "situation_instruction": over.get("situation_instruction", "계단 오를 때"),
        "demographics": {"sex": "남", "age": 58},
        "patient": {"sex": "남", "age": 58, "name": "홍"},
        "present_illness": over.get("present_illness", []),
        "checklist": over.get("checklist", []),
    }


def test_negation_excluded_from_positive():
    # "실신은 없었어요" → syncope 는 polarity=negated → positive 로 안 셈(선별은 인정)
    c = _facts_case(checklist=[
        {"id": "q", "domain": "병력청취", "scoring_rule": "실신을 물었다",
         "keywords": ["실신"], "patient_answer": "실신은 없었어요"},
    ])
    rf = validate(c, DISEASES, LABELS, disease_id=ACS).checks["red_flags"]
    syn = next(h for h in rf.screened + rf.flagged + rf.present if h.concept_id == "syncope")
    assert syn.polarity == "negated"
    assert syn in rf.screened                     # 물었고 환자 부인 → screened(present 아님)
    assert syn not in rf.present
    assert rf.positive_coverage == 0.0           # 환자가 가진 red flag 0
    assert rf.asked_coverage and rf.asked_coverage > 0.0   # 선별은 함


def test_screened_redflag_not_false_fail():
    # 모든 red flag 를 선별(asked)했으면 환자가 부인해도 fail 아님(거짓fail 방지)
    c = _facts_case(checklist=[
        {"id": "q1", "domain": "병력청취", "scoring_rule": "저혈압·실신을 물었다",
         "keywords": ["저혈압", "실신"], "patient_answer": "저혈압이나 실신은 없었습니다"},
    ])
    rf = validate(c, DISEASES, LABELS, disease_id=ACS).checks["red_flags"]
    assert rf.status != "fail"                   # 둘 다 선별 → fail 아님
    assert rf.positive_coverage == 0.0
    assert rf.asked_coverage == 1.0


def test_present_illness_not_spontaneous_but_positive():
    # 현병력 detail 의 방사통·식은땀 → disclosure 누설 아님(자발 아님) + discriminator 는 positive
    c = _facts_case(
        chief_complaint="가슴 압박감",
        present_illness=[{"time_point": "7일전", "detail": "왼팔로 방사되는 통증과 식은땀이 있었다"}],
    )
    r = validate(c, DISEASES, LABELS, disease_id=ACS)
    assert r.checks["disclosure"].status == "pass"
    assert not r.checks["disclosure"].violations
    pres = {h.concept_id for h in r.checks["discriminators"].present}
    assert "radiation_to_left_arm_or_jaw" in pres
    assert "diaphoresis" in pres


def test_required_asked_only_is_fail_not_present():
    # 필수증상을 '물었지만' 환자 사실엔 없음 → present 아님, screened, status=fail
    # (Codex R2: 필수증상은 환자가 *제시*해야 함 — 선별만은 미충족)
    c = _facts_case(
        chief_complaint="가슴이 좀 이상해요", situation_instruction="모르겠어요",
        checklist=[
            {"id": "q", "domain": "병력청취", "scoring_rule": "압박감·운동 연관을 물었다",
             "keywords": ["압박", "운동"], "patient_answer": "글쎄요 잘 모르겠어요"},
        ],
    )
    rq = validate(c, DISEASES, LABELS, disease_id=ACS).checks["required_coverage"]
    assert rq.positive_coverage == 0.0
    assert rq.asked_coverage == 1.0
    assert rq.status == "fail"                   # 선별만(screened) → 미제시 → fail
    assert "chest_pressure" not in {h.concept_id for h in rq.present}
    assert "chest_pressure" in {h.concept_id for h in rq.screened}


def test_two_lens_coverages_serialized():
    # positive_coverage/asked_coverage 가 직렬화에 포함(라운드트립)
    d = validate(_case(), DISEASES, LABELS, disease_id=ACS).to_dict()["checks"]["red_flags"]
    assert "positive_coverage" in d and "asked_coverage" in d


def test_r4_negated_hypotension_no_contradiction():
    # "저혈압은 없어요"(자발 부정) + bp 높음 → R4 수치모순 아님(polarity 체크, Codex R2)
    c = _facts_case(chief_complaint="가슴 압박감이 있고 저혈압은 없어요")
    c["vitals"] = {"bp": "148/92"}
    assert validate(c, DISEASES, LABELS, disease_id=ACS).checks["contradiction"].status == "pass"


def test_r4_affirmed_hypotension_still_flags():
    # 반대로 "저혈압이 심해요"(자발 단언) + bp 높음 → 수치모순 flag(휴리스틱 유지)
    c = _facts_case(chief_complaint="가슴 압박감이 있고 저혈압이 심합니다")
    c["vitals"] = {"bp": "148/92"}
    con = validate(c, DISEASES, LABELS, disease_id=ACS).checks["contradiction"]
    assert con.status == "flag"
    assert any("hypotension_text_vs_bp" in h.note for h in con.flagged)


def test_polarity_affirmed_preferred_across_fields():
    # 한 필드 부정 + 다른 필드 긍정 → 긍정 우선(Codex R3): syncope 는 positive 로 채택
    c = _facts_case(
        chief_complaint="실신은 없었어요",
        present_illness=[{"time_point": "이후", "detail": "이후 실신했습니다"}],
    )
    rf = validate(c, DISEASES, LABELS, disease_id=ACS).checks["red_flags"]
    syn = next(h for h in rf.present + rf.flagged + rf.screened if h.concept_id == "syncope")
    assert syn.polarity == "affirmed"
    assert syn in rf.present


def test_polarity_affirmed_across_synonyms():
    # label "실신" negated + 동의어 "기절" affirmed(다른 필드) → syncope positive(Codex R4 동의어 masking)
    c = _facts_case(
        chief_complaint="실신은 없었어요",
        present_illness=[{"time_point": "이후", "detail": "이후 기절했습니다"}],
    )
    rf = validate(c, DISEASES, LABELS, disease_id=ACS).checks["red_flags"]
    syn = next(h for h in rf.present + rf.flagged + rf.screened if h.concept_id == "syncope")
    assert syn.polarity == "affirmed"
    assert syn in rf.present


def test_no_exertional_relation_no_false_contradiction():
    # "운동과 무관"(GERD 감별)이 exertional '운동' 부분매칭으로 거짓 모순 내면 안 됨(Codex R3)
    c = {
        "case_id": "gerd", "title": "t", "diagnosis": "위식도역류질환(GERD)",
        "chief_complaint": "식후 흉골 뒤 작열감", "situation_instruction": "통증은 운동과 무관합니다",
        "demographics": {"sex": "남", "age": 50}, "patient": {"sex": "남", "age": 50, "name": "김"},
        "present_illness": [], "checklist": [],
    }
    con = validate(c, DISEASES, LABELS, disease_id="gerd").checks["contradiction"]
    assert con.status == "pass"     # exertional 은 관계부정(무관) → 상호배타 안 켜짐


def test_contradiction_ignores_probe_channel():
    # checklist "운동 연관을 물었다"(keyword 운동)만으로 exertional×no_exertional 거짓모순 X (Codex R5)
    # — 모순은 환자 사실(fact) 채널만, probe(질문) 제외.
    c = _facts_case(
        chief_complaint="가슴 압박감", situation_instruction="계단 오를 때 통증",
        checklist=[{"id": "q", "domain": "병력청취", "scoring_rule": "운동 연관을 물었다",
                    "keywords": ["운동"], "patient_answer": "네 계단 오를 때 아파요"}],
    )
    assert validate(c, DISEASES, LABELS, disease_id=ACS).checks["contradiction"].status == "pass"


# ── 11. 실데이터 FP 회귀(Codex 흉통 파이프라인 출력검수 2026-07-01) ──────────────
def test_diaphoresis_not_matched_in_활발한():
    # "활발한"의 "발한" substring 으로 diaphoresis 오매칭 금지(동의어 발한·땀 제거)
    c = _facts_case(chief_complaint="가슴 압박감")
    c["patient"]["mood_usual"] = "평소 활발한 성격이에요"
    pres = {h.concept_id for h in validate(c, DISEASES, LABELS, disease_id=ACS).checks["discriminators"].present}
    assert "diaphoresis" not in pres


def test_hypotension_not_matched_by_혈압_keyword():
    # 위험인자 질문 keyword "혈압"·"고혈압"이 "저혈압"으로 오매칭 금지(겹침 ≥3자)
    c = _facts_case(checklist=[
        {"id": "q", "domain": "병력청취", "scoring_rule": "위험인자를 물었다",
         "keywords": ["고혈압", "혈압", "당뇨"], "patient_answer": "고혈압 있어요"}])
    rf = validate(c, DISEASES, LABELS, disease_id=ACS).checks["red_flags"]
    hyp = next((h for h in rf.present + rf.flagged + rf.missing + getattr(rf, "screened", [])
                if h.concept_id == "hypotension"), None)
    assert hyp is None or hyp.match_level == "NONE"


def test_syncope_negated_worry_and_emphatic():
    # "쓰러질까 봐"(걱정) · "한 번도 없"(강조부정) → syncope 긍정 아님(미제시)
    for ans in ("아니요, 쓰러진 적은 한 번도 없어요", "심장마비로 쓰러질까 봐 걱정돼요"):
        c = _facts_case(checklist=[
            {"id": "q", "domain": "병력청취", "scoring_rule": "실신을 물었다",
             "keywords": ["실신"], "patient_answer": ans}])
        rf = validate(c, DISEASES, LABELS, disease_id=ACS).checks["red_flags"]
        syn = next((h for h in rf.present + rf.flagged + getattr(rf, "screened", [])
                    if h.concept_id == "syncope"), None)
        assert syn not in rf.present, f"{ans!r}: syncope 가 present 이면 안 됨"


if __name__ == "__main__":   # pragma: no cover — pytest 없이도 단독 실행 가능
    sys.exit(pytest.main([__file__, "-q"]))
