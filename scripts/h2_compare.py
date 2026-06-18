"""
H2 비교 — structural-only(②A) vs structural+clinical(②A+②B) 의 전문가 피드백 recall.
실행: PYTHONPATH=src .venv/bin/python scripts/h2_compare.py

공정성: 전문가 지적을 사례당 **1회 고정**(atomic list) → 두 모드를 같은 분모로 채점.
효율: 변환한 draft를 data/working/dev_drafts/ 에 캐시(재변환 안 함, 과부하 회피).
⚠️ 파일럿·자동판정. 🔒 dev_tune only. 인간 adjudication은 pending(교수).
"""
import sys, json, glob
sys.path.insert(0, "scripts")
from pathlib import Path
from pydantic import BaseModel
from ingest import extract_text, to_cpxcase, deid
from cpx.models import CpxCase
from cpx.agents import reviewer
from cpx import llm

BASE = "data/raw_private/2026-06-18_pusan/extracted"
FB_YEARS = {"2021", "2022", "2023", "2024", "2026"}
CACHE = Path("data/working/dev_drafts"); CACHE.mkdir(parents=True, exist_ok=True)
N = 3


class FB(BaseModel):
    feedback: str


class PointSet(BaseModel):
    points: list[str]


class CaughtSet(BaseModel):
    caught: list[bool]


def get_draft(k, sym, yr):
    cf = CACHE / f"{k}.json"
    if cf.exists():
        return CpxCase(**json.loads(cf.read_text(encoding="utf-8")))
    d = [f for f in glob.glob(f"{BASE}/**/{sym}_{yr}_*.hwp", recursive=True) if "초안" in f]
    case = to_cpxcase(extract_text(Path(d[0])), k)
    cf.write_text(case.model_dump_json(indent=2), encoding="utf-8")
    return case


def caught_count(points, findings):
    if not points:
        return 0
    j = llm.complete_json(
        f"전문가 지적 리스트를 같은 순서로, AI 심사가 의미상 잡았으면 true.\n[지적]\n"
        + "\n".join(f"{i+1}. {p}" for i, p in enumerate(points))
        + f"\n[AI 심사]\n{findings}", CaughtSet)
    return sum(bool(x) for x in j.caught[:len(points)])


sp = json.load(open("data/working/splits.json", encoding="utf-8"))
pairs = [(k, v) for k, v in sp["families"].items()
         if v["split"] == "dev_tune" and v["has_draft"] and v["has_final"] and v["year"] in FB_YEARS][:N]

fbc = {}
tot_pts = sc = fc = 0
for k, v in pairs:
    sym, yr = v["symptom"], v["year"]
    try:
        case = get_draft(k, sym, yr)
    except Exception as e:
        print(f"  skip {k} (변환 실패: {str(e)[:40]})"); continue
    rv = reviewer.review(case)
    cl = reviewer.review_clinical(case)
    f_struct = rv.summary + " " + " ".join(r.comment for r in rv.results if not r.passed) + " " + " ".join(rv.fixes)
    f_full = f_struct + " [임상] " + " ".join(c.issue for c in cl.critiques)
    if yr not in fbc:
        fs = glob.glob(f"{BASE}/**/*피드백*{yr}*.hwp", recursive=True)
        fbc[yr] = deid(extract_text(Path(fs[0]))) if fs else ""
    fb = llm.complete_json(f"아래 연도 피드백서 '{sym}'({v['dx']}) 사례 피드백만 발췌. JSON feedback. 없으면 빈문자열.\n\n{fbc[yr][:28000]}", FB)
    if not fb.feedback.strip():
        print(f"  skip {k} (피드백 매칭 실패)"); continue
    pts = llm.complete_json(f"이 전문가 피드백을 개별 지적(atomic)으로 분해. JSON points(list[str]).\n{fb.feedback}", PointSet).points
    cs = caught_count(pts, f_struct)
    cf2 = caught_count(pts, f_full)
    tot_pts += len(pts); sc += cs; fc += cf2
    print(f"  {k} ({v['dx']}): 전문가 {len(pts)}지적 · 구조만 {cs} → 구조+임상 {cf2}  [②B {len(cl.critiques)}개]")

if tot_pts:
    print(f"\n──── 종합(공정 비교, 같은 분모 {tot_pts}) ────")
    print(f"  구조만(②A):       {sc}/{tot_pts} = {sc/tot_pts:.0%}")
    print(f"  구조+임상(②A+②B): {fc}/{tot_pts} = {fc/tot_pts:.0%}   (②B 효과 {(fc-sc)/tot_pts*100:+.0f}%p)")
print("⚠️ 파일럿·자동판정. 본검증=인간 adjudication(교수)+카테고리별+CI+페어확대.")
