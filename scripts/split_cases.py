"""
누수안전 분할 — **파일명 메타만** 보고 케이스 패밀리를 train_prompt/dev_tune/locked_eval로.
내용은 절대 안 연다(분할 전 leakage 방지). 결과 → data/working/splits.json (gitignore).
사용: PYTHONPATH=src .venv/bin/python scripts/split_cases.py
"""
import os
import re
import json
import random
from collections import defaultdict

random.seed(42)  # 재현성
BASE = "data/raw_private/2026-06-18_pusan/extracted"
LOCKED_ALLOC = {"2021": 2, "2022": 3, "2023": 5, "2024": 3, "2026": 3, "hybrid": 1}
TRAIN_N = 25


def year_of(parts):
    for p in parts:
        if re.fullmatch(r"20\d\d", p):
            return p
        if p.lower() in ("hyb",) or "hyb" in p.lower():
            return "hybrid"
    return "unknown"


# 1) 패밀리 수집 (증상_연도 키), 파일명만
fam = defaultdict(lambda: {"final": [], "draft": [], "year": None, "symptom": None, "dx": None, "hybrid": False})
for r, _, files in os.walk(BASE):
    cat = "최종" if "최종" in r else "초안" if "초안" in r else None
    if not cat:
        continue
    for f in files:
        if not f.lower().endswith(".hwp"):
            continue
        parts = f[:-4].split("_")
        y = year_of(parts)
        sym = parts[0]
        key = f"{sym}_{y}"
        fm = fam[key]
        fm["year"] = y; fm["symptom"] = sym; fm["hybrid"] = (y == "hybrid")
        if cat == "최종":
            fm["final"].append(f)
            if len(parts) >= 3:
                fm["dx"] = parts[-1]
        else:
            fm["draft"].append(f)

families = list(fam.keys())

# 2) 층화 분할: 연도별 locked 우선 배정
by_year = defaultdict(list)
for k, v in fam.items():
    by_year["hybrid" if v["hybrid"] else v["year"]].append(k)

split = {}
for y, alloc in LOCKED_ALLOC.items():
    cands = sorted(by_year.get(y, []))
    random.shuffle(cands)
    for k in cands[:alloc]:
        split[k] = "locked_eval"

# 3) 나머지 → train_prompt(25) / dev_tune(rest)
rest = sorted(k for k in families if k not in split)
random.shuffle(rest)
for k in rest[:TRAIN_N]:
    split[k] = "train_prompt"
for k in rest[TRAIN_N:]:
    split[k] = "dev_tune"

# 4) 저장 (data/working = gitignore)
out = {
    "rule": "파일명 메타만으로 층화. 케이스 패밀리(초안+최종) 단위. seed=42. locked는 봉인.",
    "locked_alloc": LOCKED_ALLOC,
    "counts": {s: sum(1 for v in split.values() if v == s) for s in ["train_prompt", "dev_tune", "locked_eval"]},
    "families": {k: {"split": split[k], **{kk: fam[k][kk] for kk in ("year", "symptom", "dx", "hybrid")},
                     "has_final": bool(fam[k]["final"]), "has_draft": bool(fam[k]["draft"])}
                 for k in sorted(families)},
}
os.makedirs("data/working", exist_ok=True)
json.dump(out, open("data/working/splits.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("패밀리:", len(families), "· 분할:", out["counts"])
pair = sum(1 for v in fam.values() if v["final"] and v["draft"])
print(f"초안↔최종 페어 패밀리: {pair} · 최종만: {sum(1 for v in fam.values() if v['final'] and not v['draft'])} · 초안만: {sum(1 for v in fam.values() if v['draft'] and not v['final'])}")
print("locked_eval 연도분포:", {y: sum(1 for k, v in split.items() if v == 'locked_eval' and fam[k]['year'] == y) for y in LOCKED_ALLOC})
print("→ data/working/splits.json (gitignore)")
