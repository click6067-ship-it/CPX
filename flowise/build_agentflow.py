"""
Flowise Agentflow V2 빌더 — src/cpx/graph.py 의 LangGraph(생성→심사→수정 루프)를
Flowise 캔버스에 *손으로 짜서* 올릴 수 있는 import용 JSON 으로 만든다.

⚠️ 이건 LangGraph 코드를 자동 렌더한 게 아니라(그건 docs/cpx-langgraph.png),
   Flowise라는 별도 빌더의 노드로 **다시 구성**한 것 — 사용자가 요청한 "캔버스 수동 재구성".
   구조(노드·연결·조건분기·루프)는 graph.py 와 1:1로 맞췄고, 실행 세부(모델 자격증명·
   state 변수·structured output)는 캔버스에서 마저 설정하면 된다.

방법: Flowise가 내장한 검증된 마켓플레이스 템플릿에서 노드 블록(거대한 inputParams 포함)을
   그대로 추출 → id/앵커를 일괄 치환 → CPX 7노드로 재조립. (손수 쓰면 노드당 수백 줄·오류위험)

산출물: flowise/cpx-case-loop.agentflow.json  (Flowise UI → Agentflows → Import 로 로드)
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

MP = Path("/home/click/.nvm/versions/node/v20.20.2/lib/node_modules/flowise/marketplaces/agentflowsv2")
OUT = Path(__file__).resolve().parent / "cpx-case-loop.agentflow.json"


def _load(name: str) -> dict:
    return json.loads((MP / name).read_text(encoding="utf-8"))


def grab(template: str, comp_name: str) -> dict:
    """템플릿에서 data.name == comp_name 인 첫 노드를 깊은복사로 가져온다(검증된 inputParams 포함)."""
    for n in _load(template)["nodes"]:
        if n["data"]["name"] == comp_name:
            return copy.deepcopy(n)
    raise SystemExit(f"{comp_name} not found in {template}")


def reid(node: dict, new_id: str, label: str, x: float, y: float) -> dict:
    """노드의 원래 id를 new_id로 *전부* 치환(top-level id·data.id·inputParams id·anchor id 등).
    그 뒤 label·좌표를 세팅. id가 노드 전반에 박혀 있어 문자열 일괄치환이 가장 안전."""
    old_id = node["data"]["id"]
    s = json.dumps(node, ensure_ascii=False).replace(old_id, new_id)
    node = json.loads(s)
    node["id"] = new_id
    node["data"]["id"] = new_id
    node["data"]["label"] = label
    node["position"] = {"x": x, "y": y}
    node["positionAbsolute"] = {"x": x, "y": y}
    node["selected"] = False
    node["data"]["selected"] = False
    return node


def html_var(expr: str) -> str:
    """Flowise 변수 멘션 HTML(에디터 chip 포맷)."""
    return (f'<p><span class="variable" data-type="mention" data-id="{expr}" '
            f'data-label="{expr}">{{{{ {expr} }}}}</span> </p>')


def msg(role: str, content_html: str) -> dict:
    return {"role": role, "content": content_html}


# ──────────────────────────────────────────────────────────────────────────
# 노드 조립 (좌→우 레이아웃; 루프는 revise→review 로 되돌아감)
# ──────────────────────────────────────────────────────────────────────────
X = [60, 300, 560, 820, 1080, 1340, 820]   # 칼럼 x
Y_MAIN, Y_LOOP = 120, 360

start = reid(grab("Structured Output.json", "startAgentflow"), "startAgentflow_0", "Start", X[0], Y_MAIN)
# 주증상/진단을 폼으로 받게(develop_case(symptom, diagnosis) 미러) + rounds state
start["data"]["inputs"].update({
    "startInputType": "formInput",
    "formTitle": "CPX 사례 개발",
    "formDescription": "주증상과 진단을 입력하면 생성→심사→수정 루프가 돈다.",
    "formInputTypes": [
        {"type": "string", "label": "주증상(symptom)", "name": "symptom", "addOptions": ""},
        {"type": "string", "label": "진단(diagnosis)", "name": "diagnosis", "addOptions": ""},
    ],
    "startState": [{"key": "verdict", "value": ""}, {"key": "must_fix", "value": ""}],
})

gen = reid(grab("Structured Output.json", "llmAgentflow"), "llmAgentflow_0", "① generate (생성)", X[1], Y_MAIN)
gen["data"]["inputs"].update({
    "llmMessages": [
        msg("system", "<p>너는 한국 의대 CPX 사례 생성기다. [붙임2] 양식(CpxCase)으로 "
            "인구통계·환자 구어체 현병력·과거력·체크리스트(20+ 항목, domain별 scoring_rule+keywords)를 "
            "임상적으로 일관되게 생성한다. (src/cpx/agents/generator._draft)</p>"),
        msg("user", f"<p>주증상={html_var('$form.symptom')} 진단={html_var('$form.diagnosis')} 로 CPX 사례를 생성하라.</p>"),
    ],
    "llmEnableMemory": False,
    "llmStructuredOutput": "",
})

review = reid(grab("Structured Output.json", "llmAgentflow"), "llmAgentflow_1", "② review (심사: 구조+임상)", X[2], Y_MAIN)
review["data"]["inputs"].update({
    "llmMessages": [
        msg("system", "<p>너는 CPX 심사관이다. ②A 구조심사(verdict: Accept/Minor/Major/Reject) + "
            "②B 임상심사(RAG 근거, must_fix/optional). (src/cpx/agents/reviewer)</p>"),
        msg("user", "<p>아래 사례를 심사하라. verdict 와 must_fix 개수를 state 에 기록한다.</p>"),
    ],
    "llmEnableMemory": False,
    "llmStructuredOutput": [
        {"key": "verdict", "type": "enum", "enumValues": "Accept,Minor,Major,Reject",
         "jsonSchema": "", "description": "②A 구조 판정"},
        {"key": "must_fix", "type": "number", "enumValues": "", "jsonSchema": "",
         "description": "②B 임상 must_fix 지적 수"},
    ],
    "llmUpdateState": [
        {"key": "verdict", "value": html_var("output.verdict")},
        {"key": "must_fix", "value": html_var("output.must_fix")},
    ],
})

cond = reid(grab("Supervisor Worker.json", "conditionAgentflow"), "conditionAgentflow_0", "route (종료? 수정?)", X[3], Y_MAIN)
# route(): (verdict∈{Accept,Minor} AND must_fix==0) → 종료(branch0), 아니면 수정(else)
cond["data"]["inputs"]["conditions"] = [
    {"type": "string", "value1": html_var("$flow.state.verdict"), "operation": "equal", "value2": "<p>Accept</p>"},
    {"type": "string", "value1": html_var("$flow.state.verdict"), "operation": "equal", "value2": "<p>Minor</p>"},
]

reply = reid(grab("Workplace Chat.json", "directReplyAgentflow"), "directReplyAgentflow_0", "✅ confirmed (확정 사례)", X[4], Y_MAIN)

revise = reid(grab("Structured Output.json", "llmAgentflow"), "llmAgentflow_2", "✏️ revise (수정)", X[6], Y_LOOP)
revise["data"]["inputs"].update({
    "llmMessages": [
        msg("system", "<p>너는 CPX 사례 수정자다. ②A fixes + ②B must_fix 지적대로 사례를 보강해 "
            "완성된 CpxCase 로 반환한다. (src/cpx/agents/generator._revise)</p>"),
        msg("user", "<p>심사 의견대로 사례를 수정하라.</p>"),
    ],
    "llmEnableMemory": False,
    "llmStructuredOutput": "",
})

loop = reid(grab("Supervisor Worker.json", "loopAgentflow"), "loopAgentflow_0", "↩ loop → review", X[2], Y_LOOP)
loop["data"]["inputs"] = {"loopBackToNode": f'{review["id"]}-{review["data"]["label"]}', "maxLoopCount": 2}

nodes = [start, gen, review, cond, reply, revise, loop]


# ──────────────────────────────────────────────────────────────────────────
# 엣지 (sourceHandle/targetHandle 포맷은 Structured Output 템플릿과 동일)
# ──────────────────────────────────────────────────────────────────────────
def out_handle(node: dict, idx: int | None = None) -> str:
    if idx is not None:                                   # condition: -output-<idx>
        return f'{node["id"]}-output-{idx}'
    return node["data"]["outputAnchors"][0]["id"]         # 일반: -output-<comp>


def edge(src: dict, tgt: dict, sh: str) -> dict:
    th = tgt["id"]                                        # agentflow v2: targetHandle == 노드 id
    return {
        "source": src["id"], "sourceHandle": sh, "target": tgt["id"], "targetHandle": th,
        "data": {"sourceColor": src["data"].get("color", "#999"),
                 "targetColor": tgt["data"].get("color", "#999"), "isHumanInput": False},
        "type": "agentFlow",
        "id": f'{src["id"]}-{sh}-{tgt["id"]}-{th}',
    }


edges = [
    edge(start, gen, out_handle(start)),
    edge(gen, review, out_handle(gen)),
    edge(review, cond, out_handle(review)),
    edge(cond, reply, out_handle(cond, 0)),              # Accept → 확정
    edge(cond, reply, out_handle(cond, 1)),              # Minor  → 확정
    edge(cond, revise, out_handle(cond, 2)),             # Else(Major/Reject) → 수정
    edge(revise, loop, out_handle(revise)),              # 수정 → loop (review 로 되돌림)
]

flow = {
    "description": "CPX 사례 개발 루프 — src/cpx/graph.py LangGraph 의 Flowise 재구성 "
                   "(START→generate→review→[조건분기]→revise→(loop)→review). 시각화/캔버스용.",
    "usecases": ["Agent"],
    "nodes": nodes,
    "edges": edges,
}

OUT.write_text(json.dumps(flow, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {OUT}  ({len(nodes)} nodes, {len(edges)} edges)")
print("nodes:", [n["data"]["label"] for n in nodes])
