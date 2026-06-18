"""
H4-smoke 하네스: 손-라벨 fixture에 ④채점을 돌려 정답(gold) 대비 일치도(kappa)를 측정.

⚠️ SMOKE only — 손 라벨 + 소표본이라 *엔지니어링 단위테스트*다.
   타당성(validity) kappa가 아니다. 진짜 H4-real = 실제 학생 transcript + 임상교원 라벨. (architecture §5)
"""
from __future__ import annotations

import json
from pathlib import Path

from cpx.models import CpxCase
from cpx.agents.grader import grade_llm
from cpx.harness.metrics import accuracy, cohen_kappa, prf


def load_fixtures(root: Path):
    fx = json.loads((root / "data/fixtures.json").read_text(encoding="utf-8"))
    cache: dict[str, CpxCase] = {}
    out = []
    for f in fx:
        cid = f["case"]
        if cid not in cache:
            cache[cid] = CpxCase(**json.loads((root / "data/cases" / f"{cid}.json").read_text(encoding="utf-8")))
        transcript = (root / "data/transcripts" / f["transcript"]).read_text(encoding="utf-8")
        out.append((cache[cid], transcript, f["gold"]))
    return out


def run(root: Path, grader) -> dict:
    """grader(case, transcript) 를 모든 fixture에 돌려 gold와 비교 (항목 평탄화)."""
    pred: list[bool] = []
    gold: list[bool] = []
    for case, transcript, goldmap in load_fixtures(root):
        res = grader(case, transcript)
        for it in res["items"]:
            pred.append(bool(it["reached"]))
            gold.append(bool(goldmap.get(it["id"], False)))
    return {"n": len(pred), "accuracy": accuracy(pred, gold), "kappa": cohen_kappa(pred, gold), **prf(pred, gold)}


def consistency(root: Path, n: int = 3) -> dict:
    """LLM 채점 일관성(연구문제 4-2): 같은 fixture를 n회 → 첫 회 대비 판정 안정성."""
    case, transcript, _ = load_fixtures(root)[0]
    runs = [[bool(r["reached"]) for r in grade_llm(case, transcript)["items"]] for _ in range(n)]
    agrees = [accuracy(runs[0], r) for r in runs[1:]]
    return {"case": case.case_id, "runs": n, "stability": sum(agrees) / len(agrees) if agrees else 1.0}
