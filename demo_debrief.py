"""
④ 질적 디브리핑 데모 — 일부러 유도성·전문용어 섞은 대화를 평가.
실행: PYTHONPATH=src .venv/bin/python demo_debrief.py
"""
import json
from pathlib import Path

from cpx.models import CpxCase
from cpx.agents.debrief import debrief

ROOT = Path(__file__).parent
case = CpxCase(**json.loads((ROOT / "data/cases/chestpain_lee.json").read_text(encoding="utf-8")))

# 일부러 결함 섞음: 유도성("왼팔이?") + 전문용어("방사")
transcript = """의사: 안녕하세요 이상철님이시죠? 어떻게 오셨어요?
환자: 아침에 갑자기 가슴이 쥐어짜듯 아파서요. 식은땀도 났고요.
의사: 통증이 방사되는 느낌이 있으세요? 왼팔이?
환자: 어깨 쪽으로 좀 묵직하게 가는 것 같아요.
의사: 혹시 담배 피우세요? 술은요?
환자: 담배는 하루 한 갑 정도 피웁니다."""

out = debrief(case, transcript)
print(f"=== 디브리핑: {case.title} ===\n")
for f in out.items:
    flags = []
    if f.is_leading: flags.append("⚠️유도성")
    if f.uses_jargon: flags.append(f"⚠️전문용어{f.jargon_terms}")
    tag = f"  [{f.q_type}]" + (" " + " ".join(flags) if flags else " ✅")
    print(f"  의사: {f.utterance}{tag}")
    if f.issue:
        print(f"        → {f.issue}")
    if f.rewrite:
        print(f"        ✍️ 이렇게: \"{f.rewrite}\"")
