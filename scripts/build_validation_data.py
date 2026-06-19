"""
H2 검증 데이터(case 중심, 전체내용) 생성 — Codex 재설계 반영.
실행: PYTHONPATH=src .venv/bin/python scripts/build_validation_data.py [--n=6] [--model=gemini-2.5-pro]

각 사례마다 *페이지에 다 보여줄* 전체내용을 담는다(발췌·생략·출처참조 금지):
  - draft        : 사례 초안 전문 (de-id)
  - expert_review: 전문가 피드백 전문 (de-id, 원문)
  - ai_findings  : ②(강한 모델)가 낸 지적 전체 (②A 구조 + ②B 임상)
  - expert_points: 전문가 피드백을 enumerate한 atomic 지적(+category) — per-point recall용
  - blind        : A/B에 expert/ai를 무작위(결정적) 배치 — case-level blind 비교용

출력(둘 다 data/working/validation_build/, gitignore=학교자산):
  - data.js          → /tmp/cpx-adj-web/lib/data.js 로 복사 후 재배포
  - cases_meta.json  → aggregate_validation.py 입력(blind 매핑·category)
⚠️ 학교자산. git 커밋 금지. ② 모델은 strong(기본 gemini-2.5-pro)로 freeze 대상.
"""
import sys, os, json, glob, re
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
OUT = Path("data/working/validation_build"); OUT.mkdir(parents=True, exist_ok=True)
N = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--n=")), 6)
MODEL = next((a.split("=")[1] for a in sys.argv if a.startswith("--model=")), "gemini-2.5-pro")

Cat = Literal["CLINICAL_CONTENT", "STRUCTURAL", "INTERNAL_LOGIC", "SP_FEASIBILITY",
              "SCORING_VALIDITY", "EDUCATIONAL_ALIGNMENT", "SP_LOGISTICS", "OTHER"]


class Point(BaseModel):
    point: str
    category: Cat


class Points(BaseModel):
    points: list[Point]


class FB(BaseModel):
    feedback: str


def clean(t: str) -> str:
    t = t.replace("\r", "")
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def get_case(k, sym, yr):
    d = [f for f in glob.glob(f"{BASE}/**/{sym}_{yr}_*.hwp", recursive=True) if "초안" in f]
    raw = clean(deid(extract_text(Path(d[0])))) if d else ""
    cf = CACHE / f"{k}.json"
    if cf.exists():
        return CpxCase(**json.loads(cf.read_text(encoding="utf-8"))), raw
    case = to_cpxcase(raw, k)
    cf.write_text(case.model_dump_json(indent=2), encoding="utf-8")
    return case, raw


sp = json.load(open("data/working/splits.json", encoding="utf-8"))
cand = [(k, v) for k, v in sorted(sp["families"].items())
        if v["split"] == "dev_tune" and v["has_draft"] and v["has_final"] and v["year"] in FB_YEARS]
seen, pairs = set(), []
for k, v in cand:
    if v["symptom"] not in seen:
        pairs.append((k, v)); seen.add(v["symptom"])
    if len(pairs) >= N:
        break

fbc, cases, meta = {}, [], []
for idx, (k, v) in enumerate(pairs):
    sym, yr = v["symptom"], v["year"]
    try:
        case, draft = get_case(k, sym, yr)
        if not draft:
            print(f"  skip {k} (초안 없음)"); continue
        # ② 강한 모델, 전체 사례 심사
        rv = reviewer.review(case, model=MODEL)
        cl = reviewer.review_clinical(case, model=MODEL)
        findings = []
        for r in rv.results:
            if not r.passed and r.comment.strip():
                findings.append(r.comment.strip())
        for fx in rv.fixes:
            if fx.strip():
                findings.append(fx.strip())
        for c in cl.critiques:
            t = c.issue.strip()
            if c.suggested_edit.strip():
                t += f" (제안: {c.suggested_edit.strip()})"
            findings.append(t)
        # 중복 제거(앞 60자 기준)
        uniq, sig = [], set()
        for f in findings:
            s = re.sub(r"\s+", "", f)[:60]
            if s and s not in sig:
                sig.add(s); uniq.append(f)
        ai_findings = [{"id": f"F{i}", "text": t} for i, t in enumerate(uniq)]
        # 전문가 피드백 전문
        if yr not in fbc:
            fs = glob.glob(f"{BASE}/**/*피드백*{yr}*.hwp", recursive=True)
            fbc[yr] = clean(deid(extract_text(Path(fs[0])))) if fs else ""
        fb = llm.complete_json(f"아래 연도 피드백서에서 '{sym}'({v['dx']}) 사례에 대한 피드백 부분만 **빠짐없이 원문 그대로** 발췌. JSON feedback. 없으면 빈문자열.\n\n{fbc[yr][:40000]}", FB, model=MODEL)
        expert_text = clean(fb.feedback)
        if not expert_text:
            print(f"  skip {k} (피드백 매칭 실패)"); continue
        pts = llm.complete_json(
            f"다음 전문가 피드백을 개별 지적(atomic)으로 enumerate. 각 지적은 구체적으로(원문 표현·대상 유지). category 부여. JSON.\n\n{expert_text}", Points, model=MODEL).points
        expert_points = [{"id": f"P{i}", "text": p.point, "category": p.category} for i, p in enumerate(pts)]
        # blind A/B (결정적: 짝수 idx면 A=expert)
        blind = {"A": "expert", "B": "ai"} if idx % 2 == 0 else {"A": "ai", "B": "expert"}
        cases.append({"case_id": k, "symptom": sym, "dx": v["dx"], "year": yr,
                      "draft": draft, "expert_review": expert_text,
                      "ai_findings": ai_findings, "expert_points": expert_points, "blind": blind})
        meta.append({"case_id": k, "symptom": sym, "year": yr, "blind": blind,
                     "points": [{"id": p["id"], "category": p["category"]} for p in expert_points],
                     "finding_ids": [f["id"] for f in ai_findings]})
        print(f"  ✅ {k} ({v['dx']}): 초안 {len(draft)}자 · 전문가지적 {len(expert_points)} · ②지적 {len(ai_findings)} · ②verdict {rv.verdict}")
    except Exception as e:
        print(f"  ⚠️ {k}: {str(e)[:90]}")

data_js = ("// 자동생성(build_validation_data.py) — 실제 사례=학교자산. git 커밋 금지.\n"
           f"// ② 모델: {MODEL}\n"
           "const cases = " + json.dumps(cases, ensure_ascii=False) + ";\n"
           "module.exports = { cases, PW: process.env.SURVEY_PW || 'cpx-demo',"
           " ADMIN_PW: process.env.ADMIN_PW || process.env.SURVEY_PW || 'cpx-demo',"
           " IS_DEMO: !process.env.SURVEY_PW, MODEL: " + json.dumps(MODEL) + " };\n")
(OUT / "data.js").write_text(data_js, encoding="utf-8")
(OUT / "cases_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n✅ {OUT}/data.js + cases_meta.json · 사례 {len(cases)} · ② 모델 {MODEL}")
print(f"   전환: cp {OUT}/data.js /tmp/cpx-adj-web/lib/data.js && (cd /tmp/cpx-adj-web && vercel --prod --yes)")
