"""흉통 온톨로지 스캐폴드 생성 — '전체과정' 기계적 스모크 데모 (n=1 paired).

baseline(온톨로지 미제약 자유생성) vs scaffolded(그래프-스캐폴드 제약) — **같은 model/temp/rounds/clinical**.
각각: ①생성(→②심사→수정 루프) → ontology_validator 2-렌즈 검증 → coverage 비교.

⚠️ 주장 상한 (Codex 설계검수 2026-07-01 반영):
   같은 **draft** 카드 기준, **n=1 일화적 기계 데모**. 임상 타당성·교수 수준 품질·통계적 개선·
   GraphRAG 우월성·논문 효과크기 주장 **불가**(review_status:draft·professor_approved:false).
   라벨 누수 완화: scaffold 는 환자 구어 표현 지시(평가 라벨 verbatim 금지). matched_by 분해로 trivial/의미 구분.

실행: PYTHONPATH=src .venv/bin/python demo_ontology_pipeline.py   (GOOGLE_API_KEY 필요)
"""
from __future__ import annotations

import collections
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
os.environ.setdefault("CPX_TRACE_ACK", "0")   # 데모는 트레이싱·SaaS egress 안 함(명시 CPX_TRACE_ACK=1 이면 존중)
from cpx.agents import generator                                   # noqa: E402
from cpx.ontology_validator import CHECK_KEYS, load_cards, validate  # noqa: E402

ROOT = Path(__file__).resolve().parent
YAML = ROOT / "ontology" / "chest_pain.yaml"
ACS = "acute_coronary_syndrome"
MODEL = os.environ.get("GEN_MODEL", "gemini-2.5-flash")
ROUNDS = int(os.environ.get("GEN_ROUNDS", "1"))
OUT = ROOT / "data" / "working" / "ontology_pipeline"   # gitignore(data/working/)
OUT.mkdir(parents=True, exist_ok=True)

diseases, labels = load_cards(YAML)
acs_card = next(d for d in diseases if d["id"] == ACS)


def run(tag: str, ontology, reuse: bool = False):
    cj = OUT / f"{tag}_case.json"
    if reuse and cj.exists():
        from cpx.models import CpxCase
        case = CpxCase.model_validate_json(cj.read_text(encoding="utf-8"))
        log = ["(재사용: 저장된 case.json)"]
    else:
        case, log = generator.generate("흉통", "급성 관상동맥증후군", model=MODEL, rounds=ROUNDS,
                                       clinical=True, ontology=ontology)
        cj.write_text(case.model_dump_json(indent=2), encoding="utf-8")
        (OUT / f"{tag}_genlog.txt").write_text("\n".join(log), encoding="utf-8")
    rep = validate(case, diseases, labels, disease_id=ACS)
    (OUT / f"{tag}_report.md").write_text(rep.to_markdown(), encoding="utf-8")
    return case, log, rep


def _matched_by(rep) -> collections.Counter:
    """모든 검사의 present/flagged/screened hit → matched_by 집계. label_phrase=trivial(라벨 verbatim)."""
    c: collections.Counter = collections.Counter()
    for k in CHECK_KEYS:
        ch = rep.checks.get(k)
        if not ch:
            continue
        for h in (ch.present + ch.flagged + getattr(ch, "screened", [])):
            c[h.matched_by] += 1
    return c


def summary(tag: str, rep) -> None:
    print(f"\n── {tag} ── overall=`{rep.overall}`")
    for k in CHECK_KEYS:
        ch = rep.checks[k]
        cov = "" if ch.coverage is None else f" pos={ch.coverage:.2f}"
        ask = "" if ch.asked_coverage is None else f" asked={ch.asked_coverage:.2f}"
        viol = f"  ⛔viol={len(ch.violations)}" if ch.violations else ""
        print(f"   {k:20} {ch.status:5}{cov}{ask}{viol}")
    mb = _matched_by(rep)
    triv, tot = mb.get("label_phrase", 0), sum(mb.values())
    print(f"   matched_by={dict(mb)}  → label_phrase(trivial 누수)={triv}/{tot}")


def main() -> None:
    bar = "=" * 72
    print(bar)
    print("흉통 온톨로지 스캐폴드 생성 — 기계적 스모크 데모 (n=1 paired)")
    print(f"모델={MODEL} · rounds={ROUNDS} · 동일 조건, ontology 제약만 차이")
    print("⚠️ 일화적 데모(통계 아님) · draft 카드 · 임상타당·논문효과 주장 불가")
    print(bar)

    reuse_b = bool(os.environ.get("REUSE_BASELINE"))
    print(f"\n[1/2] baseline (온톨로지 미제약 자유생성) {'재사용' if reuse_b else '생성'}·검증 …")
    _c0, _l0, r0 = run("baseline", None, reuse=reuse_b)
    print("[2/2] scaffolded (그래프-스캐폴드 제약) 생성·심사·검증 …")
    _c1, _l1, r1 = run("scaffolded", (acs_card, labels))

    summary("BASELINE  ", r0)
    summary("SCAFFOLDED", r1)

    print(f"\n{bar}\n비교 (baseline → scaffolded) — 같은 draft 카드 기준, n=1")
    for k in ("required_coverage", "red_flags", "discriminators"):
        p0, p1 = r0.checks[k].coverage or 0, r1.checks[k].coverage or 0
        a0, a1 = r0.checks[k].asked_coverage or 0, r1.checks[k].asked_coverage or 0
        print(f"   {k:20} positive {p0:.2f}→{p1:.2f}   ·   asked {a0:.2f}→{a1:.2f}")
    dv0 = sum(len(r0.checks[k].violations) for k in CHECK_KEYS)
    dv1 = sum(len(r1.checks[k].violations) for k in CHECK_KEYS)
    print(f"   위반 합계(disclosure 자발누락+사전누설·모순)  {dv0} → {dv1}")
    print(f"\n산출물: {OUT.relative_to(ROOT)}/ (baseline/scaffolded × case.json·report.md·genlog.txt)")
    print("⚠️ matched_by 는 참고용: label_phrase=verbatim 라벨누수, synonym/keyword 도 짧은 조각 FP 가능(수동 확인 필요).")
    print("⚠️ 이 데모가 보이는 것 = '스캐폴드가 draft 카드 요소를 강제해 표면화'. 보이지 *않는* 것 = 임상 타당성·일반화·통계.")


if __name__ == "__main__":
    main()
