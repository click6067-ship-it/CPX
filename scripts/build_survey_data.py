"""
adjudication CSV → 배포 설문 데이터(data.js) + 분석용 메타(items_meta.json).
실행: PYTHONPATH=src .venv/bin/python scripts/build_survey_data.py [CSV] [--pairs=N] [--with-ai]
기본 입력: data/working/adjudication/adjudication_batch1_J1.csv
출력(둘 다 data/working/survey_build/, gitignore=학교자산):
  - data.js        → /tmp/cpx-adj-web/lib/data.js 로 복사 후 재배포 (실데이터 전환)
  - items_meta.json→ aggregate_adjudication.py 입력 (id별 카테고리·case_quality)

⚠️ data.js/items_meta.json은 실제 사례 피드백 = 학교자산. git 커밋 금지(data/working는 gitignore).
"""
import csv, json, sys
from pathlib import Path

_pos = [a for a in sys.argv[1:] if not a.startswith("--")]
SRC = _pos[0] if _pos else "data/working/adjudication/adjudication_batch1_J1.csv"
INCLUDE_AI = "--with-ai" in sys.argv
MAX_PAIRS = next((int(a.split("=")[1]) for a in sys.argv if a.startswith("--pairs=")), None)
OUT = Path("data/working/survey_build"); OUT.mkdir(parents=True, exist_ok=True)

rows = list(csv.DictReader(open(SRC, encoding="utf-8-sig")))
if MAX_PAIRS:
    keep = list(dict.fromkeys(r["pair"] for r in rows))[:MAX_PAIRS]
    rows = [r for r in rows if r["pair"] in keep]

items, meta = [], []   # items=앱용(최소), meta=분석용(전체)
for i, r in enumerate(rows):
    if r["row_type"] == "EXPERT_POINT" and r["case_quality"] == "Y":
        items.append({"id": f"E{i}", "type": "EXPERT", "pair": r["pair"], "item": r["item"],
                      "cat": r["category"], "cand": r["ai_candidate"], "tent": r["ai_tentative"]})
        meta.append({"id": f"E{i}", "type": "EXPERT", "pair": r["pair"], "category": r["category"],
                     "case_quality": "Y", "item": r["item"], "ai_candidate": r["ai_candidate"],
                     "ai_tentative": r["ai_tentative"]})
if INCLUDE_AI:
    for i, r in enumerate(rows):
        if r["row_type"] == "AI_FINDING":
            items.append({"id": f"A{i}", "type": "AI", "pair": r["pair"], "item": r["item"]})
            meta.append({"id": f"A{i}", "type": "AI", "pair": r["pair"],
                         "category": r["category"] or "AI_FINDING", "case_quality": "", "item": r["item"]})

data_js = ("// 자동생성(build_survey_data.py) — 실제 사례 피드백=학교자산. git 커밋 금지.\n"
           "const items = " + json.dumps(items, ensure_ascii=False) + ";\n"
           "module.exports = { items, PW: process.env.SURVEY_PW || 'cpx-demo',"
           " ADMIN_PW: process.env.ADMIN_PW || process.env.SURVEY_PW || 'cpx-demo',"
           " IS_DEMO: !process.env.SURVEY_PW };\n")
(OUT / "data.js").write_text(data_js, encoding="utf-8")
(OUT / "items_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

n_e = sum(1 for m in meta if m["type"] == "EXPERT")
cats = {}
for m in meta:
    if m["type"] == "EXPERT":
        cats[m["category"]] = cats.get(m["category"], 0) + 1
print(f"✅ {OUT}/data.js + items_meta.json")
print(f"   페어 {len(set(m['pair'] for m in meta))} · 전문가지적 {n_e} · ②지적 {len(meta)-n_e}")
print(f"   카테고리별 전문가지적: " + ", ".join(f"{k}={v}" for k, v in sorted(cats.items(), key=lambda x: -x[1])))
print(f"\n실데이터 전환: cp {OUT}/data.js /tmp/cpx-adj-web/lib/data.js && (cd /tmp/cpx-adj-web && vercel --prod --yes)")
