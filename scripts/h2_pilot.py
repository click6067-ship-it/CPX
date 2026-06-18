"""
H2 파일럿 — ②AI심사가 전문가 피드백을 재현하나? (논문 직결 첫 실험)
실행: PYTHONPATH=src .venv/bin/python scripts/h2_pilot.py

설계(Codex): 초안 → ②심사 → 전문가 피드백(연도 doc에서 해당 사례)과 카테고리 비교 → recall.
⚠️ 파일럿: 소표본 + 자동판정(LLM judge). 본검증은 교수 adjudication + 더 많은 페어 (locked 미사용).
🔒 dev_tune 페어만 사용(locked_eval 봉인).
"""
import sys, json, glob
sys.path.insert(0, "scripts")
from pathlib import Path
from pydantic import BaseModel
from ingest import extract_text, to_cpxcase, deid
from cpx.agents.reviewer import review
from cpx import llm

BASE = "data/raw_private/2026-06-18_pusan/extracted"
FB_YEARS = {"2021", "2022", "2023", "2024", "2026"}
N = 3


class FB(BaseModel):
    feedback: str


class ExpertPoint(BaseModel):
    point: str
    caught_by_ai: bool


class H2Judge(BaseModel):
    expert_points: list[ExpertPoint]
    ai_extra: list[str]


def feedback_text(year):
    fs = glob.glob(f"{BASE}/**/*피드백*{year}*.hwp", recursive=True)
    return deid(extract_text(Path(fs[0]))) if fs else ""


sp = json.load(open("data/working/splits.json", encoding="utf-8"))
pairs = [(k, v) for k, v in sp["families"].items()
         if v["split"] == "dev_tune" and v["has_draft"] and v["has_final"] and v["year"] in FB_YEARS][:N]

fb_cache = {}
rows = []
for k, v in pairs:
    sym, yr = v["symptom"], v["year"]
    drafts = [f for f in glob.glob(f"{BASE}/**/{sym}_{yr}_*.hwp", recursive=True) if "초안" in f]
    if not drafts:
        print(f"  skip {k} (초안 없음)"); continue
    case = to_cpxcase(extract_text(Path(drafts[0])), k)         # ① 초안 → CpxCase
    rv = review(case)                                            # ② 심사
    ai = rv.summary + "\n" + "\n".join(f"- {r.criterion}: {r.comment}" for r in rv.results if not r.passed) \
        + "\n수정제안: " + "; ".join(rv.fixes)
    if yr not in fb_cache:
        fb_cache[yr] = feedback_text(yr)
    fb = llm.complete_json(f"아래 연도 피드백 문서에서 '{sym}'({v['dx']}) 사례에 대한 피드백만 발췌. JSON feedback(str). 없으면 빈 문자열.\n\n{fb_cache[yr][:28000]}", FB)
    if not fb.feedback.strip():
        print(f"  skip {k} (전문가 피드백 매칭 실패)"); continue
    j = llm.complete_json(
        f"전문가 피드백 vs AI심사 결과 비교. 전문가가 지적한 점들을 나열하고 각각 AI가 의미상 잡았는지(caught_by_ai). AI가 추가로 든 점은 ai_extra.\n"
        f"[전문가 피드백]\n{fb.feedback}\n\n[AI ②심사]\n{ai}", H2Judge)
    caught = sum(p.caught_by_ai for p in j.expert_points); tot = len(j.expert_points)
    rows.append((k, v["dx"], rv.verdict, caught, tot, len(j.ai_extra)))
    print(f"\n=== {k} ({v['dx']}) · ②판정 {rv.verdict} ===")
    print(f"  전문가 지적 {tot} 중 ② 포착 {caught} (recall {caught/tot:.0%})" if tot else "  전문가 지적 0")
    for p in j.expert_points:
        print(f"    {'✅' if p.caught_by_ai else '❌누락'} {p.point[:55]}")
    if j.ai_extra:
        print(f"    ＋② 추가지적 {len(j.ai_extra)}개 (예: {j.ai_extra[0][:45]})")

tc = sum(r[3] for r in rows); tt = sum(r[4] for r in rows)
print(f"\n──── H2 파일럿 결과: ② recall {tc}/{tt} = {tc/tt:.0%} (n={len(rows)}페어) ────" if tt else "\n결과 없음")
print("⚠️ 파일럿(소표본·자동 LLM 판정). 본검증 = 교수 adjudication + 페어 확대 + locked 별도.")
