"""CPX 온톨로지 대조 validator (결정론·LLM 0회).

models.py 모듈 docstring(7~9행)이 예약한 "내용 검증은 별도 validators.py 몫"의 구현체.
Pydantic은 *구조*만 보장한다. 이 모듈은 생성 사례(CpxCase / dict / 자유텍스트)를
흉통 온톨로지 카드(ontology/chest_pain.yaml)와 **규칙으로 대조**해 6가지 검사를 돌린다.

설계 정본 = docs 의 "CPX validators.py 최종 통합 설계"(안2 백본 + 안3 3-tier + 안1 핀고정).
요구사항 정본 = 이 레포 task: 파일명 ontology_validator.py · **PyYAML만 의존, 표준라이브러리 위주**
· 반환은 **dataclass/dict 리포트**. → 그래서 출력 모델은 (Pydantic이 아니라) stdlib dataclass로
구현하되, 설계가 요구한 직렬화(`to_dict`/`to_json`/`to_markdown`)·스냅샷·governance 연동을 그대로 제공한다.

핵심 성질
- 외부 IO = yaml.safe_load 1회뿐(또는 dict/list 주입 시 0회). LLM 호출 없음 → 완전 결정론.
- case에는 온톨로지 영문 id가 전혀 없다(ChecklistItem.id조차 LLM 자유생성). 따라서 모든 매칭은
  "영문 id → labels[id] 한국어 라벨/동의어 → case 자유텍스트 부분문자열·키워드"로만 간다(id 동등비교 금지).
- 과대주장 차단: review_status / professor_approved / disclaimer 를 리포트 표면에 강제 노출.
  overall=="pass" 의 의미는 "draft 카드와 **구조적으로 정합 / 어휘 커버리지 충족**"일 뿐,
  "임상 타당"이 아니다(프로젝트 규칙).
- coverage 2-렌즈 분리(Codex 적대검수 2R, 2026-06-30): **positive**(환자가 *가짐* — 사실 채널 spontaneous/asked/history,
  부정문 제외) vs **asked**(학생이 *선별* — probe 채널). `_negated`(한국어 후치부정 "실신은 없었어요")로 부정을 positive 에서 제외.
  ⚠ negation 은 *제한적 휴리스틱*(이중부정·복합문 불완전)이고, 검사별 임상정책(required=제시 필수·red_flags=다뤄짐 등)은
  교수 검증 전 draft 다. "임상 타당" 주장 아님.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

import yaml

__all__ = [
    "validate",
    "load_cards",
    "ValidatorConfig",
    "DEFAULT_CONFIG",
    "Hit",
    "CheckResult",
    "OntologyReport",
    "CardResolutionError",
]

# 6검사 키(고정 순서) — 리포트 checks dict 의 정본 키.
CHECK_KEYS = (
    "required_coverage",
    "red_flags",
    "discriminators",
    "disclosure",
    "contradiction",
    "checklist_mapping",
)


class CardResolutionError(ValueError):
    """case.diagnosis 로 카드를 단일 해석하지 못함(추측 진행 금지, Karpathy 룰1).

    `disease_id=` 를 명시하거나 config.strict_diagnosis_match=False 로 우회 가능.
    """


# ─────────────────────────────────────────────────────────────────────────────
# 1. 설정(노브) — frozen dataclass. 임계·동의어·배타쌍을 전부 여기에 핀고정(회귀가드).
# ─────────────────────────────────────────────────────────────────────────────
def _default_synonyms() -> dict[str, tuple[str, ...]]:
    """영문 id → 한국어 임상 동의어 표면형(validator 보유·버전관리; src에 헬퍼 없음).

    증상/감별단서/red flag + (검사6용) 체크리스트 항목 동의어를 함께 둔다.
    동의어 매칭은 generic stoplist 의 영향을 받지 않는다(표면형 그대로 부분문자열).
    """
    return {
        # ── 증상·감별단서·red flag ──
        "chest_pressure": ("쥐어짜", "짓누르", "압박", "조이", "뻐근", "누르"),
        "diaphoresis": ("식은땀", "발한", "진땀", "땀"),
        "syncope": ("실신", "기절", "쓰러", "의식 소실", "정신을 잃"),
        "dyspnea": ("숨차", "호흡곤란", "숨이", "숨쉬기", "숨 쉬기"),
        "radiation_to_left_arm_or_jaw": ("방사", "뻗치", "퍼지", "어깨", "왼팔", "좌측 팔"),
        "exertional_or_rest_onset": ("운동", "계단", "활동", "안정", "쉴 때", "가만", "움직이면"),
        "hypotension": ("저혈압",),
        "no_exertional_relation": ("운동과 무관", "운동 무관", "활동과 무관", "운동과 상관없"),
        "retrosternal_burning": ("작열감", "타는", "쓰리", "화끈"),
        "acid_regurgitation": ("산 역류", "신물", "역류"),
        "relation_to_meals_or_lying_down": ("식후", "누우면", "눕기", "식사 후"),
        "palpitations": ("두근", "심장이 뛰"),
        "sudden_tearing_pain": ("찢어지", "째지", "갑작스런", "갑자기"),
        "radiation_to_back": ("등으로", "등 쪽", "등쪽", "등 뒤"),
        "bp_differential_between_arms": ("양팔 혈압", "혈압차", "양쪽 혈압"),
        "bp_differential": ("양팔 혈압", "혈압차", "양쪽 혈압"),
        "hypertension_hx": ("고혈압",),
        # ── 검사6: 체크리스트 항목(행동) 동의어 — ACS 카드 6항목 위주 ──
        "ask_onset_duration": ("발병", "발생", "시작", "언제", "기간", "시점", "얼마나"),
        "ask_character": ("양상", "어떻게", "조이", "쥐어", "누르", "답답", "성상"),
        "ask_radiation": ("방사", "퍼지", "뻗", "어깨", "방사통"),
        "ask_aggravating_relieving": ("악화", "완화", "심해", "나아", "쉬면", "안정 시"),
        "ask_associated_sx": ("동반", "호흡곤란", "식은땀", "오심", "구역", "두근"),
        "ask_cardiac_risk_factors": ("위험인자", "흡연", "담배", "고혈압", "당뇨", "가족력", "고지혈"),
    }


def _default_diagnosis_synonyms() -> dict[str, tuple[str, ...]]:
    """case.diagnosis(자유 한국어) → disease id 역매칭용 임상 동의어셋.

    실 gold "급성 심근경색 (감별: 협심증)" → head "급성 심근경색" → '심근경색' 매칭 → ACS 단일.
    """
    return {
        "acute_coronary_syndrome": (
            "급성심근경색", "심근경색", "협심증", "불안정협심증", "관상동맥",
            "급성 관상동맥증후군", "ami", "stemi", "nstemi", "acs",
        ),
        "gerd": ("위식도역류", "역류성식도염", "gerd", "역류"),
        "musculoskeletal_chest_pain": ("근골격", "늑연골염", "흉벽통", "늑간", "근육통"),
        "panic_anxiety": ("공황", "불안", "공황장애"),
        "aortic_dissection": ("대동맥박리", "대동맥 박리", "박리", "대동맥"),
    }


def _default_mutual_exclusions() -> tuple[tuple[str, str], ...]:
    """상호배타 라벨쌍(명시표·버전관리; 자동도출 금지=재현성).

    장기 승격처는 YAML `mutual_exclusions:` 키(코드 TODO). 지금은 시드 2쌍.
    """
    return (
        ("exertional_or_rest_onset", "no_exertional_relation"),  # 운동/안정 시 발생 ↔ 운동과 무관
        ("young_low_risk", "hypertension_hx"),                   # 젊고 위험인자 적음 ↔ 고혈압 병력
    )


@dataclass(frozen=True)
class ValidatorConfig:
    """임계·동의어·배타쌍 노브. 기본값 고정 + 테스트 스냅샷 핀고정(회귀가드)."""

    synonyms: Mapping[str, tuple[str, ...]] = field(default_factory=_default_synonyms)
    diagnosis_synonyms: Mapping[str, tuple[str, ...]] = field(
        default_factory=_default_diagnosis_synonyms
    )
    mutual_exclusions: tuple[tuple[str, str], ...] = field(
        default_factory=_default_mutual_exclusions
    )
    male_tokens: frozenset[str] = field(
        default_factory=lambda: frozenset({"남", "남자", "남성", "male", "m"})
    )
    female_tokens: frozenset[str] = field(
        default_factory=lambda: frozenset({"여", "여자", "여성", "female", "f"})
    )
    # 산부인과력 "비어있음" 표현 — 정규화 후 비교(_norm). "-" 는 정규화 시 ""→ 자동으로 빈값 취급.
    obgyn_negations: frozenset[str] = field(
        default_factory=lambda: frozenset({"없음", "해당 없음", "해당없음", "n/a", "na", "무"})
    )
    # 단일 토큰만으로는 HIGH 승격 금지(거짓양성 방지)할 일반 토큰.
    generic_token_stoplist: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"팔", "땀", "시", "통증", "가슴", "흉통", "호흡", "동작", "증상", "등",
             "산", "뒤", "통", "여부", "원인", "위험인자", "정도", "느낌"}
        )
    )
    # 체크리스트 라벨의 동작 접미(검사6에서 핵심명사만 남김).
    checklist_stop_tokens: frozenset[str] = field(
        default_factory=lambda: frozenset({"묻기", "확인", "측정", "진찰", "설명", "배제"})
    )
    token_match_ratio: float = 0.5     # 코어토큰 AND 판정 임계(precision 핀)
    strict_diagnosis_match: bool = True  # 진단 역매칭 실패 시 에러(추측 금지). False면 primary+warning
    strict_discriminators: bool = False  # 감별단서 전수 HIGH 요구 여부
    r4_systolic_normal_min: int = 130    # 이 이상 수축기면 "저혈압 강단언"과 수치모순(R4, 휴리스틱)


DEFAULT_CONFIG = ValidatorConfig()


# ─────────────────────────────────────────────────────────────────────────────
# 2. 출력 모델(stdlib dataclass) — 직렬화·스냅샷·governance 연동.
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Hit:
    """모든 매칭의 증거 provenance. 식별 정본은 영문 concept_id, label 은 표시용."""

    concept_id: str
    label: str
    match_level: str = "NONE"                 # HIGH | LOW | NONE
    channel: Optional[str] = None             # spontaneous | asked | probe | union | None
    field: Optional[str] = None               # 매칭 case 필드경로 예) "checklist[2].keywords"
    evidence: str = ""                        # 실제 매칭 표면형 예) "synonym:식은땀"
    matched_by: str = "absent"                # label_phrase|synonym|keyword|label_tokens_AND|label_tokens_partial|field_rule|absent
    note: str = ""                            # "label_missing" | "spontaneous_missing" | "leaked_before_asked" ...
    polarity: str = "affirmed"                # affirmed | negated  — 텍스트 매칭만 의미(부정문 "없음" 검출)

    def to_dict(self) -> dict:
        return {
            "concept_id": self.concept_id,
            "label": self.label,
            "match_level": self.match_level,
            "channel": self.channel,
            "field": self.field,
            "evidence": self.evidence,
            "matched_by": self.matched_by,
            "note": self.note,
            "polarity": self.polarity,
        }


@dataclass
class CheckResult:
    name: str
    status: str                               # pass | flag | fail | skip
    coverage: Optional[float] = None          # 주 렌즈 비율(coverage_checks=positive)
    present: list[Hit] = field(default_factory=list)
    missing: list[Hit] = field(default_factory=list)
    flagged: list[Hit] = field(default_factory=list)
    violations: list[Hit] = field(default_factory=list)
    # 선별/질문은 됐으나 환자 사실로 *제시되지 않음*(asked-only · 물었고 부인=negated). flagged(검토필요)와 구분.
    screened: list[Hit] = field(default_factory=list)
    notes: str = ""
    # 2-렌즈 분리(Codex 적대검수 2026-06-30): 환자가 *가졌나* vs 학생이 *선별했나*.
    positive_coverage: Optional[float] = None  # 환자 사실로 *제시*된 비율(부정문 제외)
    asked_coverage: Optional[float] = None     # 체크리스트가 *선별/질문*한 비율(polarity 무관)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "coverage": self.coverage,
            "positive_coverage": self.positive_coverage,
            "asked_coverage": self.asked_coverage,
            "present": [h.to_dict() for h in self.present],
            "missing": [h.to_dict() for h in self.missing],
            "flagged": [h.to_dict() for h in self.flagged],
            "violations": [h.to_dict() for h in self.violations],
            "screened": [h.to_dict() for h in self.screened],
            "notes": self.notes,
        }


_DISCLAIMER = "draft 카드 기준 · 어휘 커버리지/구조 정합만 검사 · 임상 타당성 미검증"


@dataclass
class OntologyReport:
    case_id: str
    matched_disease_id: str
    disease_label: str
    diagnosis_text: str
    review_status: str
    professor_approved: bool
    checks: dict[str, CheckResult]
    overall: str                              # pass | flag | fail
    warnings: list[str] = field(default_factory=list)
    disclaimer: str = _DISCLAIMER

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "matched_disease_id": self.matched_disease_id,
            "disease_label": self.disease_label,
            "diagnosis_text": self.diagnosis_text,
            "review_status": self.review_status,
            "professor_approved": self.professor_approved,
            "disclaimer": self.disclaimer,
            "overall": self.overall,
            "warnings": list(self.warnings),
            "checks": {k: self.checks[k].to_dict() for k in self.checks},
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def to_markdown(self) -> str:
        """사람/논문용 — 영문 id + 한국어 라벨 병기."""
        def _ids(hits: Sequence[Hit]) -> str:
            if not hits:
                return "—"
            return ", ".join(f"{h.concept_id}({h.label})" for h in hits)

        lines: list[str] = []
        lines.append(f"# 온톨로지 대조 리포트 — {self.case_id}")
        lines.append(f"> ⚠️ {self.disclaimer}")
        lines.append(
            f"> review_status=`{self.review_status}` · "
            f"professor_approved=`{self.professor_approved}` "
            "(pass=구조정합/어휘커버리지일 뿐 '임상 타당' 아님)"
        )
        lines.append("")
        lines.append(f"- 진단(case): {self.diagnosis_text}")
        lines.append(f"- 매칭 카드: `{self.matched_disease_id}` ({self.disease_label})")
        lines.append(f"- **종합(overall): `{self.overall}`**")
        lines.append("")
        lines.append("## 검사별 결과")
        for key in CHECK_KEYS:
            c = self.checks.get(key)
            if c is None:
                continue
            cov = "" if c.coverage is None else f" · positive={c.coverage:.2f}"
            if c.asked_coverage is not None:
                cov += f" · asked={c.asked_coverage:.2f}"
            lines.append(f"### {key} — `{c.status}`{cov}")
            if c.present:
                lines.append(f"- present: {_ids(c.present)}")
            if c.flagged:
                lines.append(f"- flagged(검토): {_ids(c.flagged)}")
            if c.screened:
                lines.append(f"- screened(선별·환자 미제시): {_ids(c.screened)}")
            if c.missing:
                lines.append(f"- missing: {_ids(c.missing)}")
            if c.violations:
                lines.append(f"- ⛔ violations: {_ids(c.violations)}")
            if c.notes:
                lines.append(f"- note: {c.notes}")
        if self.warnings:
            lines.append("")
            lines.append("## 경고(indeterminate)")
            for w in self.warnings:
                lines.append(f"- {w}")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# 3. 정규화·토큰화 (한국어 매칭의 토대)
# ─────────────────────────────────────────────────────────────────────────────
_PUNCT_RE = re.compile(r"[^0-9a-z가-힣]+")
_WS_RE = re.compile(r"\s+")
# 조사·접미(긴 것 우선). strip 후 길이 2 미만이면 적용 안 함(과절단 방지).
_JOSA = tuple(
    sorted({"으로", "은", "는", "이", "가", "을", "를", "에", "의", "로", "와", "과", "도", "만", "시"},
           key=len, reverse=True)
)


def _norm(s: Any) -> str:
    """NFKC + lower(약어 ACS/GERD 흡수) + 구두점→공백 + 공백압축. None/숫자 안전."""
    if s is None:
        return ""
    s = unicodedata.normalize("NFKC", str(s)).lower()
    s = _PUNCT_RE.sub(" ", s)
    return _WS_RE.sub(" ", s).strip()


def _strip_josa(tok: str) -> str:
    for j in _JOSA:
        if tok.endswith(j) and len(tok) - len(j) >= 2:
            return tok[: -len(j)]
    return tok


def _core_tokens(label: str, config: ValidatorConfig) -> list[str]:
    """라벨 → 코어토큰. ·/공백/괄호 split(_norm이 처리) → 조사 strip → len≥2 → 동작접미 제거.

    예) "좌측 팔·턱 방사"→[좌측,방사] · "양팔 혈압차"→[양팔,혈압차]
        · "급성 관상동맥증후군(ACS)"→[급성,관상동맥증후군,acs] · "발병·기간 묻기"→[발병,기간]
    """
    out: list[str] = []
    seen: set[str] = set()
    for raw in _norm(label).split():
        t = _strip_josa(raw)
        if len(t) < 2:
            continue
        if t in config.checklist_stop_tokens:
            continue
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def _is_generic(tok: str, config: ValidatorConfig) -> bool:
    return tok in config.generic_token_stoplist


def _anchor(core: Sequence[str], config: ValidatorConfig) -> Optional[str]:
    """가장 특이적인 코어토큰(len≥3 우선, generic 제외). 없으면 None → keyword-HIGH 승격 차단."""
    cands = [t for t in core if not _is_generic(t, config)]
    if not cands:
        return None
    # len≥3 우선, 그 다음 길이 긴 것. max 는 첫 최대값을 반환(결정론).
    return max(cands, key=lambda t: (len(t) >= 3, len(t)))


def _bidir(a: str, b: str) -> bool:
    """양방향 substring — 실데이터 필수("쥐어"⊂"쥐어짜는")."""
    return a in b or b in a


# 한국어 후치 부정 단서(예: "실신은 없었어요"·"저혈압 아님"·"방사통 부인"·"경험하지 않음"). polarity 판정용.
# 관계부정("운동과 무관"·"식사와 관련없"): exertional synonym "운동"이 no_exertional 문장에 substring 끼는 충돌 차단(Codex R3).
_NEG_CUES = ("없", "아니", "부인", "부정", "음성", "않", "못",
             "무관하", "무관합", "무관한", "관련 없", "관련없", "상관없", "상관 없")
# 이중부정(="긍정") — 부정으로 오판 방지("실신이 없지는 않았어요" = 있었음).
_DOUBLE_NEG = ("없지 않", "없지는 않", "없진 않", "아니지 않", "없는 것은 아니", "없는것은 아니")


def _negated(text: str, surface: str) -> bool:
    """text 내 surface 의 *모든* 출현이 부정 문맥이면 True. 한 번이라도 긍정이면 False.

    한국어는 부정이 명사 뒤에 온다("실신은 없었어요") → surface 직후 window(10자)에서 부정어 탐색.
    이중부정("없지 않")은 긍정으로 처리. ⚠ 제한적 휴리스틱(복합문·간접부정 불완전 — Codex 적대검수 인정).
    보수적(긍정 우선): 한 출현이라도 긍정이면 "환자가 가짐"으로 본다(positive 과소계산 방지).
    """
    if not surface:
        return False
    idx = text.find(surface)
    if idx == -1:
        return False
    while idx != -1:
        after = text[idx + len(surface): idx + len(surface) + 10]
        if any(dn in after for dn in _DOUBLE_NEG):      # 이중부정 → 긍정
            return False
        if not any(cue in after for cue in _NEG_CUES):
            return False                                # 긍정 출현 발견 → 부정 아님
        idx = text.find(surface, idx + 1)
    return True                                         # 모든 출현이 부정 문맥


# ─────────────────────────────────────────────────────────────────────────────
# 4. 채널(FieldIndex) — 구조 필드를 명명 텍스트채널로 투영(None→"" coerce, 빈텍스트 skip)
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class _Channel:
    name: str
    fields: list[tuple[str, str]]   # (필드경로, 정규화 텍스트)
    combined: str                   # 정규화 텍스트 concat(빠른 contains)


def _mk_channel(name: str, raw_fields: Sequence[tuple[str, Any]]) -> _Channel:
    fields: list[tuple[str, str]] = []
    parts: list[str] = []
    for path, raw in raw_fields:
        t = _norm(raw)
        if t:
            fields.append((path, t))
            parts.append(t)
    return _Channel(name, fields, " ".join(parts))


# Patient 의 str 필드(1인칭 SP 연기지침) — age(int) 제외.
_PATIENT_STR_FIELDS = (
    "sex", "name", "job", "daily_impact", "mood_usual", "mood_now",
    "thoughts_concerns", "expectation", "background", "knows", "wants_to_know", "nonverbal",
)


def _build_channels(
    c: Mapping[str, Any],
) -> tuple[_Channel, _Channel, _Channel, _Channel, _Channel, list[str]]:
    """case dict → (spontaneous, asked, probe, history, extra, 평탄화 keywords).

    채널 의미(2-렌즈 분리 — Codex 적대검수 2026-06-30):
      - spontaneous = 초기 *자발* 발화(주증상·상황지시·patient 페르소나). disclosure 누설판정 정본.
      - asked       = checklist[].patient_answer(질문에 답한 환자 발화).
      - probe       = checklist 질문/scoring_rule/keywords(학생이 *선별*한 것 = asked 렌즈).
      - history     = 현병력 detail·과거/가족/사회력(환자 *사실*이나 초기 자발 아님 → 누설 과플래그 방지).
      - extra       = 진단/제목/과제/demo.note(메타 — 환자 사실 아님; 모순·체크리스트 union 보조).
    positive 렌즈(환자가 가졌나)=[spontaneous,asked,history] · asked 렌즈(선별)=[probe].
    """
    patient = c.get("patient") or {}
    checklist = c.get("checklist") or []
    present_illness = c.get("present_illness") or []
    demo = c.get("demographics") or {}

    # spontaneous(초기 자발) = 주증상 + 상황지시 + patient.*  (현병력은 history 로 분리)
    spont_raw: list[tuple[str, Any]] = [
        ("chief_complaint", c.get("chief_complaint")),
        ("situation_instruction", c.get("situation_instruction")),
    ]
    for k in _PATIENT_STR_FIELDS:
        spont_raw.append((f"patient.{k}", patient.get(k)))

    # asked(질문시) = checklist[].patient_answer 만
    asked_raw: list[tuple[str, Any]] = [
        (f"checklist[{i}].patient_answer", (ci or {}).get("patient_answer"))
        for i, ci in enumerate(checklist)
    ]

    # probe(선별) = checklist[].question_open/closed + scoring_rule + keywords
    probe_raw: list[tuple[str, Any]] = []
    keywords_flat: list[str] = []
    for i, ci in enumerate(checklist):
        ci = ci or {}
        probe_raw.append((f"checklist[{i}].question_open", ci.get("question_open")))
        probe_raw.append((f"checklist[{i}].question_closed", ci.get("question_closed")))
        probe_raw.append((f"checklist[{i}].scoring_rule", ci.get("scoring_rule")))
        kws = ci.get("keywords") or []
        probe_raw.append((f"checklist[{i}].keywords", " ".join(kws)))
        for k in kws:
            kn = _norm(k)
            if kn:
                keywords_flat.append(kn)

    # history(환자 사실 · 초기 자발 아님) = 현병력 detail + 과거/가족/사회력
    history_raw: list[tuple[str, Any]] = [
        (f"present_illness[{i}].detail", (hi or {}).get("detail"))
        for i, hi in enumerate(present_illness)
    ]
    history_raw += [
        ("past_hx", c.get("past_hx")),
        ("family_hx", c.get("family_hx")),
        ("social_hx", c.get("social_hx")),
    ]

    # extra(메타 — 환자 사실 아님) = 진단/제목/과제/demo.note
    extra_raw: list[tuple[str, Any]] = [
        ("diagnosis", c.get("diagnosis")),
        ("title", c.get("title")),
        ("examinee_task", c.get("examinee_task")),
        ("demographics.note", demo.get("note")),
    ]

    spont = _mk_channel("spontaneous", spont_raw)
    asked = _mk_channel("asked", asked_raw)
    probe = _mk_channel("probe", probe_raw)
    history = _mk_channel("history", history_raw)
    extra = _mk_channel("union", extra_raw)
    # keyword 중복 제거(결정론·순서보존)
    seen: set[str] = set()
    kw: list[str] = []
    for k in keywords_flat:
        if k not in seen:
            seen.add(k)
            kw.append(k)
    return spont, asked, probe, history, extra, kw


def _locate(scope: Sequence[_Channel], surface: str) -> tuple[Optional[str], Optional[str], str]:
    """surface 가 등장하는 (채널, 필드경로, polarity). **긍정 출현 우선** — 한 필드라도 긍정이면 affirmed.

    "긍정 우선" 원칙(Codex R3): 같은 개념이 한 필드선 부정·다른 필드선 긍정이면 긍정 채택
    (예: chief "실신 없음" + 현병력 "이후 실신함" → syncope positive). 모든 출현 부정일 때만 negated.
    """
    first_negated: Optional[tuple[Optional[str], Optional[str], str]] = None
    for ch in scope:
        for path, t in ch.fields:
            if surface and surface in t:
                if _negated(t, surface):
                    if first_negated is None:
                        first_negated = (ch.name, path, "negated")
                else:
                    return ch.name, path, "affirmed"     # 긍정 출현 즉시 채택
    if first_negated is not None:
        return first_negated                              # 전부 부정 → 첫 부정 증거
    return None, None, "affirmed"


# ─────────────────────────────────────────────────────────────────────────────
# 5. 매칭 엔진 — 안2 코어 + 안3 3-tier + 안1 AND 정밀도
# ─────────────────────────────────────────────────────────────────────────────
def _match(
    concept_id: str,
    scope: Sequence[_Channel],
    case_keywords: Sequence[str],
    *,
    labels: Mapping[str, str],
    config: ValidatorConfig,
    warnings: list[str],
) -> Hit:
    """concept_id 를 scope 채널들에서 찾아 HIGH/LOW/NONE 으로 등급.

    우선순위: (a) 라벨 전체구 → (b) 동의어 → (c) keyword⋈anchor → (d) 코어토큰 AND.
    먼저 잡힌 HIGH 가 승자(증거에 어느 규칙인지 기록). 임계는 silent 가 아니라 *명시 등급*으로 노출.
    """
    label = labels.get(concept_id, concept_id)
    missing_label = concept_id not in labels
    if missing_label:
        warnings.append(f"label_missing:{concept_id}")

    label_norm = _norm(label)
    core = _core_tokens(label, config)
    anchor = _anchor(core, config)
    combined = " ".join(ch.combined for ch in scope if ch.combined)

    def _hit(level, surface, matched_by, evidence, note=""):
        chn, fld, pol = _locate(scope, surface)          # 긍정 우선 polarity(전체 scope)
        return Hit(concept_id, label, level, chn, fld, evidence, matched_by, note, pol)

    # (a)+(b) HIGH-tier: 라벨 전체구 + 동의어 후보를 모아 *긍정 우선* 선택(Codex R4).
    #   한 후보(예 라벨 "실신")가 negated 라도 다른 후보(동의어 "기절")가 affirmed 면 affirmed 채택 →
    #   동의어 간 polarity masking 방지(chief "실신 없음" + 현병력 "기절함" → syncope positive).
    #   영문-only id(label 누락)는 한국어 텍스트와 매칭 불가라 라벨 후보 제외.
    high_cands: list[tuple[str, str, str]] = []          # (surface, matched_by, evidence)
    if not missing_label and len(label_norm) >= 2:
        high_cands.append((label_norm, "label_phrase", f"label:{label}"))
    for s in config.synonyms.get(concept_id, ()):  # type: ignore[union-attr]
        sn = _norm(s)
        if len(sn) >= 2:
            high_cands.append((sn, "synonym", f"synonym:{s}"))
    high_fallback: Optional[Hit] = None
    for surf, mb, ev in high_cands:
        if surf in combined:
            h = _hit("HIGH", surf, mb, ev)
            if h.polarity == "affirmed":
                return h                                 # 긍정 후보 즉시 채택
            if high_fallback is None:
                high_fallback = h                        # 첫 negated 후보 보관(긍정 없을 때)
    if high_fallback is not None:
        return high_fallback

    # (c) checklist keyword 가 앵커토큰과 양방향매칭(앵커가 generic 이면 승격 금지)
    if anchor is not None:
        for k in case_keywords:
            if len(k) >= 2 and k in combined and _bidir(k, anchor):
                direction = f"{k}⊂{anchor}" if k in anchor else f"{anchor}⊂{k}"
                return _hit("HIGH", k, "keyword", f"kw:{direction}")

    # (d) 코어토큰 AND/부분 — "양팔 혈압차"는 양팔+혈압 동반 필수(precision)
    matched = [t for t in core if t in combined]
    ratio = (len(matched) / len(core)) if core else 0.0
    specific = [t for t in matched if not _is_generic(t, config)]
    if core and ratio >= config.token_match_ratio:
        # 전부(AND) → 1개 이상 특이토큰이면 HIGH. 부분(≥ratio) → 특이토큰 2개 이상이어야 HIGH.
        need_specific = 1 if ratio >= 1.0 else 2
        if len(specific) >= need_specific:
            mb = "label_tokens_AND" if ratio >= 1.0 else "label_tokens_partial"
            return _hit("HIGH", specific[0], mb, f"tokens {len(matched)}/{len(core)}:[{','.join(matched)}]")

    if matched:
        # 부분만(OR) 또는 일반 단일토큰 hit → LOW(거짓양성 위험 → 인간검토). generic-only 는 note 표시.
        note = "" if specific else "generic_only"
        return _hit(
            "LOW", (specific or matched)[0], "label_tokens_partial",
            f"tokens {len(matched)}/{len(core)}:[{','.join(matched)}]", note,
        )

    # 어디에도 없음. 단 label 누락 id 는 NONE(확정 누락)이 아니라 LOW(indeterminate)로(절대 silent pass 안 함).
    if missing_label:
        return Hit(concept_id, label, "LOW", None, None, "", "absent", "label_missing")
    return Hit(concept_id, label, "NONE", None, None, "", "absent")


def _coverage_rows(ids, fact_scope, probe_scope, kw, labels, config, warnings):
    """각 concept → (cid, positive_hit, asked_hit). 2-렌즈 분리.

    positive = 환자 사실 채널(fact_scope)에서 매칭(+부정문이면 polarity=negated). keyword 미사용(선별어 아님).
    asked    = probe 채널(probe_scope)에서 매칭(질문/keyword, polarity 무관).
    """
    rows = []
    for cid in ids:
        pos = _match(cid, fact_scope, (), labels=labels, config=config, warnings=warnings)
        ask = _match(cid, probe_scope, kw, labels=labels, config=config, warnings=warnings)
        rows.append((cid, pos, ask))
    return rows


def _categorize(
    rows,
) -> tuple[list[Hit], list[Hit], list[Hit], list[Hit], Optional[float], Optional[float]]:
    """2-렌즈 rows → (present, weak, screened, missing, positive_coverage, asked_coverage).

    present  = positive HIGH(부정 아님; 환자가 명확히 *가짐*)
    weak     = positive LOW(부정 아님; 약한 제시 → 검토)
    screened = 물었으나 환자 부인(negated) | 질문만(asked_only) — *다뤄졌으나 제시 아님*
    missing  = 어디에도 없음(positive·asked 모두 NONE)
    """
    present: list[Hit] = []
    weak: list[Hit] = []
    screened: list[Hit] = []
    missing: list[Hit] = []
    n_pos_high = n_asked = 0
    total = len(rows)
    for _cid, pos, ask in rows:
        asked_hit = ask.match_level in ("HIGH", "LOW")
        if asked_hit:
            n_asked += 1
        if pos.match_level == "HIGH" and pos.polarity != "negated":
            n_pos_high += 1
            present.append(pos)
        elif pos.match_level in ("HIGH", "LOW") and pos.polarity != "negated":
            pos.note = (pos.note + ";weak_positive").strip(";")
            weak.append(pos)
        elif pos.match_level in ("HIGH", "LOW"):            # positive 매칭됐으나 부정문(물었고 환자 부인)
            pos.note = (pos.note + ";negated").strip(";")
            screened.append(pos)
        elif asked_hit:                                     # 환자 사실 없음, 질문만(선별)
            ask.note = (ask.note + ";asked_only").strip(";")
            screened.append(ask)
        else:                                               # 진짜 누락(선별도 제시도 없음)
            missing.append(pos)
    pos_cov = (n_pos_high / total) if total else None
    ask_cov = (n_asked / total) if total else None
    return present, weak, screened, missing, pos_cov, ask_cov


# ─────────────────────────────────────────────────────────────────────────────
# 6. 카드 선택(진단 역매칭) + 온톨로지 로딩
# ─────────────────────────────────────────────────────────────────────────────
def load_cards(yaml_path: str | Path = "ontology/chest_pain.yaml") -> tuple[list[dict], dict[str, str]]:
    """YAML 정본을 raw dict 로 직읽기 → (diseases, labels).

    load_graph(시각화 전용)는 disclosure/risk_factors/tests/education 을 버리므로 쓰지 않는다.
    """
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["diseases"], data.get("labels", {})


def _load_ontology(
    ontology: str | Path | Mapping | Sequence,
    labels_arg: Optional[Mapping[str, str]],
) -> tuple[list[dict], dict[str, str], dict]:
    """ontology 인자(경로|raw dict|diseases 리스트|단일 disease dict) → (diseases, labels, meta)."""
    if isinstance(ontology, (str, Path)):
        with open(ontology, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data["diseases"], dict(data.get("labels", {})), dict(data.get("meta", {}))
    if isinstance(ontology, Mapping):
        if "diseases" in ontology:
            labels = dict(ontology.get("labels", {}) or (labels_arg or {}))
            return list(ontology["diseases"]), labels, dict(ontology.get("meta", {}))
        # 단일 disease dict
        return [dict(ontology)], dict(labels_arg or {}), {}
    if isinstance(ontology, Sequence):
        return list(ontology), dict(labels_arg or {}), {}
    raise TypeError(f"지원하지 않는 ontology 타입: {type(ontology)!r}")


def _candidate_disease_ids(text: str, diseases: Sequence[Mapping], config: ValidatorConfig) -> list[str]:
    tnorm = _norm(text)
    if not tnorm:
        return []
    found: list[str] = []
    for d in diseases:
        did = d.get("id")
        for syn in config.diagnosis_synonyms.get(did, ()):  # type: ignore[union-attr]
            if _norm(syn) in tnorm:
                if did not in found:
                    found.append(did)
                break
    return found


def _split_diagnosis_head(diagnosis: str) -> str:
    """'급성 심근경색 (감별: 협심증)' → 대표진단부 '급성 심근경색'(감별부 절단)."""
    return re.split(r"\(?\s*감별", diagnosis or "", maxsplit=1)[0]


def _resolve_disease(
    diagnosis: str,
    diseases: Sequence[Mapping],
    config: ValidatorConfig,
    disease_id: Optional[str],
) -> tuple[dict, Optional[str]]:
    """진단 텍스트 → 단일 카드. disease_id 명시 시 역매칭 전체 스킵(결정성/override)."""
    if disease_id is not None:
        for d in diseases:
            if d.get("id") == disease_id:
                return dict(d), None
        raise CardResolutionError(f"disease_id='{disease_id}' 가 ontology 에 없음")

    if len(diseases) == 1:  # 단일 disease 주입 → 그대로
        return dict(diseases[0]), None

    primary = next((d for d in diseases if d.get("role") == "primary"), diseases[0])

    # head(대표진단부) 먼저
    head_ids = _candidate_disease_ids(_split_diagnosis_head(diagnosis), diseases, config)
    if len(head_ids) == 1:
        return dict(next(d for d in diseases if d.get("id") == head_ids[0])), None

    # full 문자열 재시도
    full_ids = _candidate_disease_ids(diagnosis, diseases, config)
    if len(full_ids) == 1:
        return dict(next(d for d in diseases if d.get("id") == full_ids[0])), None

    if config.strict_diagnosis_match:
        raise CardResolutionError(
            f"진단 '{diagnosis}' 을 단일 카드로 해석 실패(head={head_ids}, full={full_ids}). "
            "disease_id= 로 지정하거나 strict_diagnosis_match=False 로 우회."
        )
    return dict(primary), (
        f"diagnosis_unresolved: '{diagnosis}' → primary({primary.get('id')}) 채택(head={head_ids}, full={full_ids})"
    )


# ─────────────────────────────────────────────────────────────────────────────
# 7. case 입력 정규화 (CpxCase | dict | 자유텍스트 str)
# ─────────────────────────────────────────────────────────────────────────────
def _case_to_dict(case: Any) -> tuple[dict, bool]:
    """반환 (case_dict, freetext여부). CpxCase(.model_dump)·dict·str 모두 수용."""
    if hasattr(case, "model_dump"):       # pydantic CpxCase
        return case.model_dump(), False
    if isinstance(case, Mapping):
        return dict(case), False
    if isinstance(case, str):             # 자유텍스트 — chief_complaint(자발채널)로 투영
        return {
            "case_id": "(freetext)",
            "chief_complaint": case,
            "diagnosis": "",
            "patient": {},
            "present_illness": [],
            "checklist": [],
        }, True
    raise TypeError(f"지원하지 않는 case 타입: {type(case)!r}")


# ─────────────────────────────────────────────────────────────────────────────
# 8. 6검사
# ─────────────────────────────────────────────────────────────────────────────
def _check_required(disease, labels, fact_scope, probe_scope, kw, config, warnings) -> CheckResult:
    ids = disease.get("required_symptoms") or []
    rows = _coverage_rows(ids, fact_scope, probe_scope, kw, labels, config, warnings)
    present, weak, screened, missing, pos_cov, ask_cov = _categorize(rows)
    # 필수증상은 환자가 *제시*(positive)해야 함 → 미제시(선별만/부정=screened·누락)는 fail(Codex R2).
    if screened or missing:
        status = "fail"
    elif weak:
        status = "flag"          # 약한 제시만 → 검토
    else:
        status = "pass"          # 전부 명확 제시
    return CheckResult(
        "required_coverage", status, pos_cov, present, missing, weak, [], screened,
        notes="필수증상 = 환자가 *제시*(positive) 필수. screened(선별만/부정)·missing=미제시=fail.",
        positive_coverage=pos_cov, asked_coverage=ask_cov,
    )


def _check_red_flags(disease, labels, fact_scope, probe_scope, kw, config, warnings) -> CheckResult:
    ids = disease.get("red_flags") or []
    if not ids:                  # 빈 리스트(musculoskeletal) → skip
        return CheckResult("red_flags", "skip", None, notes="이 카드는 red_flags 미정의 → 검사 제외.")
    rows = _coverage_rows(ids, fact_scope, probe_scope, kw, labels, config, warnings)
    present, weak, screened, missing, pos_cov, ask_cov = _categorize(rows)
    # red flag 는 *명확히 다뤄짐*(present∪screened)이 목표 → 전부 명확→pass · 약함(weak)/일부누락→flag · 전무→fail.
    if not missing and not weak:
        status = "pass"          # 전부 명확 제시·선별됨
    elif present or weak or screened:
        status = "flag"          # 약한 제시 또는 일부 누락 → 검토
    else:
        status = "fail"          # 전부 누락(선별 0·제시 0)
    return CheckResult(
        "red_flags", status, pos_cov, present, missing, weak, [], screened,
        notes="red flag = 다뤄짐(screened 선별 ∪ present 제시) 기준. coverage=positive 제시율 · asked=선별율.",
        positive_coverage=pos_cov, asked_coverage=ask_cov,
    )


def _check_discriminators(disease, labels, fact_scope, probe_scope, kw, config, warnings) -> CheckResult:
    ids = disease.get("discriminators") or []
    rows = _coverage_rows(ids, fact_scope, probe_scope, kw, labels, config, warnings)
    present, weak, screened, missing, pos_cov, ask_cov = _categorize(rows)
    all_positive = bool(rows) and not weak and not screened and not missing   # 전부 positive HIGH
    if config.strict_discriminators:
        status = "pass" if all_positive else ("fail" if missing else "flag")
    else:
        # 감별단서는 부분이 정상 → pass/flag(절대 fail 아님)
        status = "pass" if all_positive else "flag"
    return CheckResult(
        "discriminators", status, pos_cov, present, missing, weak, [], screened,
        notes="감별단서 = 제시(positive) 우선. 약함/선별만/부정은 flag. 비-strict.",
        positive_coverage=pos_cov, asked_coverage=ask_cov,
    )


def _check_disclosure(disease, labels, spont, kw, config, warnings) -> CheckResult:
    disc = disease.get("disclosure")
    if not disc:                 # 감별 카드 4개 → 키 없음 → skip
        return CheckResult("disclosure", "skip", None, notes="이 카드는 disclosure 미정의 → 검사 제외.")
    scope = [spont]              # 검사4 정본 채널 = spontaneous 만
    present: list[Hit] = []
    flagged: list[Hit] = []
    violations: list[Hit] = []

    # (a) 누락: spontaneous 에 *있어야* 하는 항목이 자발채널에 NONE → 위반(spontaneous_missing)
    for cid in disc.get("spontaneous") or []:
        h = _match(cid, scope, kw, labels=labels, config=config, warnings=warnings)
        if h.match_level == "HIGH":
            present.append(h)
        elif h.match_level == "LOW":
            h.note = (h.note + ";weak_spontaneous").strip(";")
            flagged.append(h)
        else:
            h.note = "spontaneous_missing"
            violations.append(h)

    # (b) 사전누설: 물어봐야 답할 항목이 자발채널에 HIGH 출현 → 위반(leaked_before_asked)
    for cid in disc.get("disclose_if_asked") or []:
        h = _match(cid, scope, kw, labels=labels, config=config, warnings=warnings)
        if h.match_level == "HIGH":
            h.note = "leaked_before_asked"
            violations.append(h)
        elif h.match_level == "LOW":
            h.note = (h.note + ";ambiguous_leak").strip(";")
            flagged.append(h)
        # NONE = 정상(물어보기 전엔 자발노출 없음). asked 채널 출현은 무시(정상).

    status = "fail" if violations else ("flag" if flagged else "pass")
    return CheckResult(
        "disclosure", status, None, present, [], flagged, violations,
        notes="자발(spontaneous) 채널만 검사. 누락=spontaneous_missing · 사전노출=leaked_before_asked.",
    )


def _appears_for_contradiction(h: Hit) -> bool:
    """상호배타 판정에서 '출현'으로 칠지 — HIGH 또는 (특이 증거의) LOW. negated/generic-only/indeterminate 제외."""
    if h.polarity == "negated":        # "운동과 관련 없다" 등 부정 출현은 모순 신호 아님(Codex R2)
        return False
    if h.match_level == "HIGH":
        return True
    if h.match_level == "LOW" and h.matched_by != "absent" and "generic_only" not in h.note:
        return True
    return False


def _parse_systolic(bp: Any) -> Optional[int]:
    m = re.match(r"\s*(\d{2,3})", str(bp or ""))
    return int(m.group(1)) if m else None


def _check_contradiction(c, disease, labels, fact_scope, config, warnings) -> CheckResult:
    # ⚠ 모순은 *환자 사실*(fact_scope: spontaneous/asked/history)에서만 본다 — probe(질문·keyword)는
    #    "운동 연관을 물었다"가 exertional×no_exertional 거짓모순을 만들어 제외(Codex 적대검수 R5, 2026-06-30).
    violations: list[Hit] = []
    flagged: list[Hit] = []
    notes: list[str] = []

    demo = c.get("demographics") or {}
    patient = c.get("patient") or {}

    def _gender(x: str) -> Optional[str]:
        n = _norm(x)
        if not n:
            return None
        # 장식 텍스트("남성(58세)"→"남성 58세")에 강건 — 토큰 단위로 성별어 추출
        toks = set(n.split())
        if n in config.male_tokens or toks & config.male_tokens:
            return "M"
        if n in config.female_tokens or toks & config.female_tokens:
            return "F"
        return n  # 알 수 없는 표기끼리만 원문 비교

    demo_sex_raw, pat_sex_raw = demo.get("sex", ""), patient.get("sex", "")
    g_demo, g_pat = _gender(demo_sex_raw), _gender(pat_sex_raw)
    is_male = "M" in (g_demo, g_pat)

    # R1 남성 + 산부인과력
    obgyn = c.get("obgyn_hx")
    obgyn_n = _norm(obgyn)
    neg = {_norm(x) for x in config.obgyn_negations}
    obgyn_filled = bool(obgyn_n) and obgyn_n not in neg
    if is_male and obgyn_filled:
        violations.append(Hit(
            "male_with_obgyn_hx", "남성+산부인과력", "HIGH", None, "obgyn_hx",
            f"sex={demo_sex_raw or pat_sex_raw} & obgyn_hx={obgyn!r}", "field_rule", "male_with_obgyn_hx",
        ))

    # R2 성별 정합(둘 다 있을 때만)
    if g_demo and g_pat and g_demo != g_pat:
        violations.append(Hit(
            "sex_mismatch", "성별 불일치", "HIGH", None, "demographics.sex/patient.sex",
            f"demographics={demo_sex_raw!r} vs patient={pat_sex_raw!r}", "field_rule", "sex_mismatch",
        ))

    # R3 상호배타 라벨쌍(명시표). 둘 다 HIGH→위반 · 한쪽 HIGH+다른쪽(특이)LOW→flag.
    #    둘 다 약한 LOW(특히 generic-only)면 신호 부족 → 무시(거짓모순 방지).
    for a, b in config.mutual_exclusions:
        ha = _match(a, fact_scope, (), labels=labels, config=config, warnings=warnings)
        hb = _match(b, fact_scope, (), labels=labels, config=config, warnings=warnings)
        if _appears_for_contradiction(ha) and _appears_for_contradiction(hb):
            if ha.match_level == "HIGH" and hb.match_level == "HIGH":
                for hh in (ha, hb):
                    hh.note = f"mutual_exclusion:{a}×{b}"
                    violations.append(hh)
            elif ha.match_level == "HIGH" or hb.match_level == "HIGH":
                for hh in (ha, hb):
                    hh.note = f"mutual_exclusion(weak):{a}×{b}"
                    flagged.append(hh)

    # R4(옵션·휴리스틱) 저혈압 강단언 vs 정상/높은 수축기 → 수치모순(flag). vitals None 이면 skip.
    # ⚠ 자발(spontaneous) 채널의 *환자 사실 단언*만 본다 — "저혈압을 물었다"(질문/scoring_rule)는
    #    모순이 아니다(Codex 적대검수 2026-06-30). channel!=spontaneous 면 무시.
    vitals = c.get("vitals")
    if vitals:
        sys = _parse_systolic(vitals.get("bp"))
        hyp = _match("hypotension", fact_scope, (), labels=labels, config=config, warnings=warnings)
        if (sys is not None and sys >= config.r4_systolic_normal_min
                and hyp.match_level == "HIGH" and hyp.channel == "spontaneous"
                and hyp.polarity == "affirmed"):           # "저혈압 없음"(부정)은 모순 아님
            hyp.note = f"hypotension_text_vs_bp(sys={sys})"
            flagged.append(hyp)

    if violations:
        status = "fail"
    elif flagged:
        status = "flag"
    else:
        status = "pass"
    notes.append("순수 결정론 표(R1 남성+산부인과력·R2 성별·R3 상호배타쌍·R4 저혈압-수치).")
    return CheckResult("contradiction", status, None, [], [], flagged, violations, notes="; ".join(notes))


def _expected_domain(card_item_id: str) -> Optional[str]:
    if card_item_id.startswith(("exam_", "measure_")):
        return "신체진찰"
    if card_item_id.startswith("explain_"):
        return "환자교육"
    if card_item_id.startswith("ask_"):
        return "병력청취"
    return None


def _check_checklist(disease, labels, c, config, warnings) -> CheckResult:
    card_ids = disease.get("checklist_items") or []
    case_items = c.get("checklist") or []

    # 각 case checklist 항목을 미니채널로(질문/채점규칙/keywords/답변).
    mini: list[tuple[int, dict, _Channel, list[str]]] = []
    for j, ci in enumerate(case_items):
        ci = ci or {}
        kws = ci.get("keywords") or []
        raw = [(
            f"checklist[{j}]",
            " ".join(filter(None, [
                ci.get("question_open"), ci.get("question_closed"),
                ci.get("scoring_rule"), " ".join(kws), ci.get("patient_answer"),
            ])),
        )]
        mini.append((j, ci, _mk_channel("union", raw), [_norm(k) for k in kws]))

    present: list[Hit] = []
    missing: list[Hit] = []
    flagged: list[Hit] = []
    matched_case_idx: set[int] = set()

    for cid in card_ids:
        best: Optional[Hit] = None
        best_j: Optional[int] = None
        best_item: Optional[dict] = None
        best_low: Optional[Hit] = None        # HIGH 없을 때 보존할 약한 매핑(증거 소실 방지)
        for j, ci, ch, kws in mini:
            h = _match(cid, [ch], kws, labels=labels, config=config, warnings=warnings)
            if h.match_level == "HIGH":
                best, best_j, best_item = h, j, ci
                break
            if h.match_level == "LOW" and best_low is None:
                h.field = f"checklist[{j}]"
                best_low = h
        if best is not None:
            matched_case_idx.add(best_j)
            best.field = f"checklist[{best_j}]"
            best.note = f"maps_to:{(best_item or {}).get('id', best_j)}"
            present.append(best)
            # 보조신호(2차 flag, fail 아님): 카드 항목 성격 vs case domain 불일치
            exp = _expected_domain(cid)
            dom = (best_item or {}).get("domain")
            if exp and dom and dom != exp:
                flagged.append(Hit(
                    cid, labels.get(cid, cid), "LOW", "union", best.field,
                    f"domain:{dom}≠{exp}", "field_rule", "domain_mismatch",
                ))
        elif best_low is not None:
            # 약한 매핑 = "검토 필요"(완전 누락 아님). 증거 보존(Codex 적대검수 2026-06-30).
            best_low.note = (best_low.note + ";weak_checklist_map").strip(";")
            flagged.append(best_low)
        else:
            missing.append(_match(cid, [], [], labels=labels, config=config, warnings=warnings))

    coverage = (len(present) / len(card_ids)) if card_ids else None
    if coverage is None:
        status = "skip"
    elif coverage == 1.0:
        status = "pass"
    elif coverage == 0.0:
        status = "fail"
    else:
        status = "flag"

    orphans = [
        (case_items[j] or {}).get("id", j) for j in range(len(case_items)) if j not in matched_case_idx
    ]
    note = "카드 checklist_items → case 항목 매핑 커버리지."
    if orphans:
        note += f" orphan(case 전용) 항목: {orphans}"
    return CheckResult("checklist_mapping", status, coverage, present, missing, flagged, [], notes=note)


# ─────────────────────────────────────────────────────────────────────────────
# 9. 공개 진입점
# ─────────────────────────────────────────────────────────────────────────────
def _overall(checks: Mapping[str, CheckResult]) -> str:
    statuses = {c.status for c in checks.values()}
    if "fail" in statuses:
        return "fail"
    if "flag" in statuses:
        return "flag"
    return "pass"     # 전부 pass/skip


def validate(
    case: Any,
    ontology: str | Path | Mapping | Sequence,
    labels: Optional[Mapping[str, str]] = None,
    *,
    disease_id: Optional[str] = None,
    config: ValidatorConfig = DEFAULT_CONFIG,
) -> OntologyReport:
    """생성 사례를 흉통 온톨로지 카드와 6검사로 대조한 결정론 리포트.

    Parameters
    ----------
    case : CpxCase | dict | str
        구조체(CpxCase/dict) 권장. str 이면 자유텍스트로 보고 자발채널에 투영(검사4·6 신뢰도↓).
        ⚠ 자유텍스트는 diagnosis 가 비어 카드 역매칭 불가 → 다중카드·strict(기본)면 `disease_id=`
        (또는 strict_diagnosis_match=False) 필요. 안 주면 CardResolutionError.
    ontology : 경로 | raw dict | diseases 리스트 | 단일 disease dict
        경로/ dict 면 labels·meta 까지 읽음. 리스트면 labels= 인자 사용(파일 IO 0).
    labels : dict[str,str] | None
        ontology 가 리스트일 때 영문 id→한국어 라벨 맵.
    disease_id : str | None
        명시 시 진단 역매칭 스킵(테스트 결정성/override).
    config : ValidatorConfig
        임계·동의어·배타쌍 노브(기본값 핀고정).
    """
    diseases, labelmap, meta = _load_ontology(ontology, labels)
    c, freetext = _case_to_dict(case)
    warnings: list[str] = []

    disease, warn = _resolve_disease(c.get("diagnosis", ""), diseases, config, disease_id)
    if warn:
        warnings.append(warn)
    did = disease.get("id", "(unknown)")
    dlabel = labelmap.get(did, did)

    spont, asked, probe, history, extra, kw = _build_channels(c)
    fact_scope = [spont, asked, history]              # 환자 사실 렌즈(positive·모순 — 가졌나)
    probe_scope = [probe]                              # 선별 렌즈(asked — 학생이 물었나)

    checks: dict[str, CheckResult] = {
        "required_coverage": _check_required(disease, labelmap, fact_scope, probe_scope, kw, config, warnings),
        "red_flags": _check_red_flags(disease, labelmap, fact_scope, probe_scope, kw, config, warnings),
        "discriminators": _check_discriminators(disease, labelmap, fact_scope, probe_scope, kw, config, warnings),
        "disclosure": _check_disclosure(disease, labelmap, spont, kw, config, warnings),
        "contradiction": _check_contradiction(c, disease, labelmap, fact_scope, config, warnings),
        "checklist_mapping": _check_checklist(disease, labelmap, c, config, warnings),
    }
    # 키 순서 고정(CHECK_KEYS)
    checks = {k: checks[k] for k in CHECK_KEYS}

    if freetext:
        warnings.append(
            "freetext_mode: 자유텍스트 입력 — 채널 분리 제한(disclosure/checklist 검사 신뢰도↓)."
        )

    return OntologyReport(
        case_id=c.get("case_id", "(unknown)"),
        matched_disease_id=did,
        disease_label=dlabel,
        diagnosis_text=c.get("diagnosis", ""),
        review_status=str(meta.get("review_status", "draft")),
        professor_approved=bool(meta.get("professor_approved", False)),
        checks=checks,
        overall=_overall(checks),
        warnings=sorted(set(warnings)),
    )


# 손쉬운 수동 점검(결정론 데모) — `PYTHONPATH=src .venv/bin/python -m cpx.ontology_validator`
if __name__ == "__main__":  # pragma: no cover
    import sys

    root = Path(__file__).resolve().parents[2]
    yaml_path = root / "ontology" / "chest_pain.yaml"
    gold_path = root / "data" / "cases" / "chestpain_lee.json"
    if yaml_path.exists() and gold_path.exists():
        diseases, labels = load_cards(yaml_path)
        gold = json.loads(gold_path.read_text(encoding="utf-8"))
        report = validate(gold, diseases, labels)
        print(report.to_markdown())
    else:
        print("정본 yaml/gold 가 없어 데모 생략", file=sys.stderr)
