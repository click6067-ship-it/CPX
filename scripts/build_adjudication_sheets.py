"""
교수 adjudication 배치1 시트 생성 (10페어, 교수 3명 별도 CSV).
실행: PYTHONPATH=src .venv/bin/python scripts/build_adjudication_sheets.py

각 페어: 초안→①변환 → ②A+②B 심사 → 전문가 피드백 atomic 분해+카테고리 → ②후보매칭+잠정판정.
교수는 받아서 PROF_verdict만 채움(빈칸 채우기 아니라 확인/수정). → data/working/adjudication/ (gitignore, 학교자산).
🔒 dev_tune only. 자동판정=잠정(교수가 최종). 결과는 Fleiss kappa + 다수결 합의로 집계.
"""
import sys, json, glob, csv
sys.path.insert(0, "scripts")
from pathlib import Path
from typing import Literal
from pydantic import BaseModel
from ingest import extract_text, to_cpxcase, deid
from cpx.models import CpxCase
from cpx.agents import reviewer
from cpx import llm

BASE = "data/raw_private/2026-06-18_pusan/extracted"
FB_YEARS = {"2021", "2022", "2023", "2024", "2026"}
CACHE = Path("data/working/dev_drafts"); CACHE.mkdir(parents=True, exist_ok=True)
OUT = Path("data/working/adjudication"); OUT.mkdir(parents=True, exist_ok=True)
N = 10

Cat = Literal["CLINICAL_CONTENT", "STRUCTURAL", "INTERNAL_LOGIC", "SP_FEASIBILITY",
              "SCORING_VALIDITY", "EDUCATIONAL_ALIGNMENT", "SP_LOGISTICS", "OTHER"]


class Point(BaseModel):
    point: str
    category: Cat
    case_quality: bool   # ②가 잡아야 하는 사례품질 사항? (SP섭외·일정 등 운영은 False)


class Points(BaseModel):
    points: list[Point]


class Match(BaseModel):
    point: str
    ai_candidate: str    # 대응하는 ② 지적(없으면 "")
    tentative: Literal["caught", "missed"]


class Matches(BaseModel):
    matches: list[Match]


class FB(BaseModel):
    feedback: str


def get_draft(k, sym, yr):
    cf = CACHE / f"{k}.json"
    if cf.exists():
        return CpxCase(**json.loads(cf.read_text(encoding="utf-8")))
    d = [f for f in glob.glob(f"{BASE}/**/{sym}_{yr}_*.hwp", recursive=True) if "초안" in f]
    case = to_cpxcase(extract_text(Path(d[0])), k)
    cf.write_text(case.model_dump_json(indent=2), encoding="utf-8")
    return case


# 다양한 증상으로 10페어 선택
sp = json.load(open("data/working/splits.json", encoding="utf-8"))
cand = [(k, v) for k, v in sorted(sp["families"].items())
        if v["split"] == "dev_tune" and v["has_draft"] and v["has_final"] and v["year"] in FB_YEARS]
seen, pairs = set(), []
for k, v in cand:
    if v["symptom"] not in seen:
        pairs.append((k, v)); seen.add(v["symptom"])
    if len(pairs) >= N:
        break

fbc, rows = {}, []
for k, v in pairs:
    sym, yr = v["symptom"], v["year"]
    try:
        case = get_draft(k, sym, yr)
        rv = reviewer.review(case)
        cl = reviewer.review_clinical(case)
        ai_all = [r.comment for r in rv.results if not r.passed] + list(rv.fixes) + [c.issue for c in cl.critiques]
        if yr not in fbc:
            fs = glob.glob(f"{BASE}/**/*피드백*{yr}*.hwp", recursive=True)
            fbc[yr] = deid(extract_text(Path(fs[0]))) if fs else ""
        fb = llm.complete_json(f"아래 연도 피드백서 '{sym}'({v['dx']}) 사례 피드백만 발췌. JSON feedback. 없으면 빈문자열.\n\n{fbc[yr][:28000]}", FB)
        if not fb.feedback.strip():
            print(f"  skip {k} (피드백 매칭 실패)"); continue
        pts = llm.complete_json(
            f"다음 전문가 피드백을 개별 지적(atomic)으로 분해. 각 지적에 category와 case_quality(②리뷰어가 잡아야 할 *사례 품질* 사항이면 true; SP섭외·일정·교육과정 운영 등은 false). JSON.\n\n{fb.feedback}", Points).points
        mt = llm.complete_json(
            f"전문가 지적 각각에 대해, 아래 AI 심사 지적 중 의미상 대응하는 것(ai_candidate, 없으면 \"\")과 잠정판정(대응 있으면 caught, 없으면 missed)을 같은 순서로.\n[전문가 지적]\n"
            + "\n".join(f"{i+1}. {p.point}" for i, p in enumerate(pts))
            + "\n[AI 심사 지적]\n" + "\n".join(f"- {a}" for a in ai_all), Matches).matches
        mmap = {m.point: m for m in mt}
        for p in pts:
            m = mmap.get(p.point)
            rows.append({"pair": k, "row_type": "EXPERT_POINT", "item": p.point, "category": p.category,
                         "case_quality": "Y" if p.case_quality else "N",
                         "ai_candidate": (m.ai_candidate if m else ""), "ai_tentative": (m.tentative if m else "missed"),
                         "PROF_verdict": "", "PROF_note": ""})
        for a in ai_all:
            rows.append({"pair": k, "row_type": "AI_FINDING", "item": a, "category": "", "case_quality": "",
                         "ai_candidate": "", "ai_tentative": "", "PROF_verdict": "", "PROF_note": ""})
        print(f"  ✅ {k} ({v['dx']}): 전문가 {len(pts)}지적 · ②지적 {len(ai_all)}")
    except Exception as e:
        print(f"  ⚠️ {k}: {str(e)[:60]}")

cols = ["pair", "row_type", "item", "category", "case_quality", "ai_candidate", "ai_tentative", "PROF_verdict", "PROF_note"]
for j in ["J1", "J2", "J3"]:
    with open(OUT / f"adjudication_batch1_{j}.csv", "w", encoding="utf-8-sig", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=cols); w.writeheader(); w.writerows(rows)

ep = sum(1 for r in rows if r["row_type"] == "EXPERT_POINT")
print(f"\n생성: 페어 {len(set(r['pair'] for r in rows))} · EXPERT_POINT {ep}행 · AI_FINDING {len(rows)-ep}행")
print(f"→ {OUT}/adjudication_batch1_{{J1,J2,J3}}.csv (gitignore)")
