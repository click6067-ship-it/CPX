"""
③ 가상환자 검증 probe — 과공개 제어 + 응답 일관성 (연구문제 3-1·3-3).
실행: PYTHONPATH=src .venv/bin/python vp_probe.py

· 과공개: 좁은 yes/no 질문에 묻지 않은 정보를 자발적으로 흘리나? (LLM 심판)
· 일관성: 같은 질문 N회 → 같은 답을 하나?
⚠️ smoke 규모. 본 검증은 사례·반복 N 늘려서.
"""
import json
from pathlib import Path

from pydantic import BaseModel
from cpx.models import CpxCase
from cpx.agents import patient
from cpx import llm

ROOT = Path(__file__).parent
case = CpxCase(**json.loads((ROOT / "data/cases/diarrhea_kim.json").read_text(encoding="utf-8")))


class ODJudge(BaseModel):
    over_disclosed: bool
    volunteered: str


class ConsistJudge(BaseModel):
    consistent: bool
    note: str


def judge_od(q: str, r: str) -> ODJudge:
    p = (f'질문: "{q}"\n환자 답변: "{r}"\n'
         '환자가 질문에 직접 답한 것 외에 *묻지 않은* 다른 증상·과거력·정보를 자발적으로 말했는가? '
         'JSON: over_disclosed(bool), volunteered(그 내용, 없으면 "").')
    return llm.complete_json(p, ODJudge)


print(f"=== VP probe: {case.title} ===\n")

print("[1] 과공개 제어 (좁은 질문에 더 흘리나)")
for q in ["혹시 열이 나세요?", "구토는 하셨어요?"]:
    r = patient.reply(case, [], q)
    j = judge_od(q, r)
    mark = "⚠️ 과공개" if j.over_disclosed else "✅ 절제"
    print(f"  Q: {q}\n  A: {r}\n  → {mark}" + (f" ({j.volunteered})" if j.over_disclosed else ""))

print("\n[2] 응답 일관성 (같은 질문 3회)")
q = "설사는 하루에 몇 번 정도 하세요?"
answers = [patient.reply(case, [], q) for _ in range(3)]
for i, a in enumerate(answers, 1):
    print(f"  {i}: {a}")
cj = llm.complete_json(
    "다음 3개 답변이 핵심 정보(횟수)에서 서로 일치하는가? JSON: consistent(bool), note(str).\n"
    + "\n".join(f"- {a}" for a in answers),
    ConsistJudge,
)
print(f"  → {'✅ 일관' if cj.consistent else '⚠️ 불일치'}: {cj.note}")
