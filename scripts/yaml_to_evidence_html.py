"""근거(evidence) 그래프 → 자체완결 HTML (vis-network, 오프라인).

이전 온톨로지 그래프(yaml_to_html.py)와 같은 vis-network 방식.
단, 여기선 *구조*가 아니라 **근거**를 그린다:
  주호소 → 질환(근거수준별 색) → 출처(실사례 △ / 교과서 ▢).
즉 "어느 질환이 무슨 근거로 서 있나"를 한눈에. Neo4j 아님(오프라인 vis-network).

사용:  .venv/bin/python scripts/yaml_to_evidence_html.py   # → docs/ontology-evidence-graph.html
"""
from __future__ import annotations
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yaml  # noqa: E402
from yaml_to_html import _vis_script  # 벤더링된 vis-network 인라인 재사용  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYMS = ["abdominal_pain", "chest_pain", "diarrhea", "constipation"]
OUT = os.path.join(ROOT, "docs", "ontology-evidence-graph.html")

# 근거수준 → (색, 한국어)
LEVEL = {
    "real_case_direct":  ("#15803d", "실사례(직접)"),
    "real_case_related": ("#2563eb", "실사례(연관)"),
    "station_differential_listed": ("#0e7490", "사례 감별목록 명시"),
    "standard_textbook": ("#d97706", "표준 초안·미검증"),
}
SRC_STYLE = {
    "real_cpx_case": ("#dc2626", "triangle", "실사례(부산대 CPX)"),
    "textbook":      ("#6b7280", "square",   "참고문헌(교과서)"),
}


def short_source(sid: str, meta: dict) -> str:
    ref = meta.get("ref", sid)
    if meta.get("type") == "real_cpx_case":
        m = re.search(r"'([^']+)'", ref)
        return "실사례: " + (m.group(1) if m else sid)[:22]
    return re.split(r"[,(]", ref)[0].strip()[:26]


def build():
    nodes, edges, seen = [], [], set()
    sym_ko = []  # 부제용 주호소 한국어 목록(하드코딩 금지 — SYMS에서 도출)

    def add(nid, **kw):
        if nid not in seen:
            seen.add(nid)
            nodes.append({"id": nid, **kw})

    for sym in SYMS:
        with open(os.path.join(ROOT, "ontology", f"{sym}.yaml"), encoding="utf-8") as f:
            data = yaml.safe_load(f)
        labels = data.get("labels", {})
        srcs = data.get("sources", {})
        cc_ko = labels.get(sym, sym)
        sym_ko.append(cc_ko)
        add(sym, label=cc_ko, color="#7c3aed", shape="star", size=34,
            title=f"주호소: {cc_ko}", font={"size": 20})

        for d in data["diseases"]:
            ev = d.get("evidence", {})
            lvl = ev.get("level", "standard_textbook")
            color, lvl_ko = LEVEL[lvl]
            dz = labels.get(d["id"], d["id"])
            tip = f"{dz}\\n근거수준: {lvl_ko}"
            if ev.get("basis"):
                tip += "\\n근거: " + ev["basis"][:120]
            add(d["id"], label=dz, color=color, shape="dot", size=20, title=tip)
            edges.append({"from": sym, "to": d["id"], "color": {"color": "#cfcfcf"},
                          "width": 1})

            for s in ev.get("sources", []):
                meta = srcs.get(s, {})
                scol, shape, _ = SRC_STYLE.get(meta.get("type", "textbook"), SRC_STYLE["textbook"])
                add(s, label=short_source(s, meta), color=scol, shape=shape, size=13,
                    title=meta.get("ref", s), font={"size": 12, "color": scol})
                edges.append({"from": d["id"], "to": s, "label": "출처", "dashes": True,
                              "color": {"color": scol}, "font": {"size": 9, "color": "#999"}})

    legend = " ".join(
        f'<span><i style="background:{c};border-radius:50%"></i>{ko}</span>'
        for c, ko in LEVEL.values()
    ) + " &nbsp;|&nbsp; " + " ".join(
        f'<span><i style="background:{c}">{"△" if sh=="triangle" else "▢"}</i>{ko}</span>'
        for c, sh, ko in SRC_STYLE.values()
    )

    return (
        _TEMPLATE
        .replace("__VISJS__", _vis_script())
        .replace("__NODES__", json.dumps(nodes, ensure_ascii=False))
        .replace("__EDGES__", json.dumps(edges, ensure_ascii=False))
        .replace("__LEGEND__", legend)
        .replace("__SYMLIST__", "·".join(sym_ko))
    )


_TEMPLATE = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CPX 온톨로지 — 근거 그래프</title>
__VISJS__
<style>
  body{margin:0;font-family:'Malgun Gothic',sans-serif;background:#fafafa}
  #hd{padding:10px 16px;border-bottom:1px solid #ddd;background:#fff}
  #hd h1{margin:0;font-size:18px}
  #hd .sub{color:#666;font-size:12px;margin-top:3px}
  #hd .warn{color:#b91c1c;font-size:12px;margin-top:4px;font-weight:bold}
  #legend{padding:6px 16px;font-size:12px;border-bottom:1px solid #eee;background:#fff}
  #legend span{display:inline-block;margin-right:14px}
  #legend i{display:inline-block;width:13px;height:13px;margin-right:4px;vertical-align:middle;text-align:center;line-height:13px;color:#fff;font-size:10px}
  #net{width:100%;height:calc(100vh - 112px)}
</style></head>
<body>
<div id="hd">
  <h1>CPX 온톨로지 — 근거 그래프 (질환 → 출처)</h1>
  <div class="sub">__SYMLIST__ 주호소 → 질환(근거수준별 색) → 출처(실사례 △ / 교과서 ▢) · vis-network(오프라인, Neo4j 아님)</div>
  <div class="warn">⚠ review_status: draft — 임상 내용 교수 검증 전 초안. 주황 = <b>실 CPX 사례 없음</b>(교과서 출처는 있을 수 있음).</div>
</div>
<div id="legend">__LEGEND__</div>
<div id="net"></div>
<script>
  const nodes = new vis.DataSet(__NODES__);
  const edges = new vis.DataSet(__EDGES__);
  new vis.Network(document.getElementById('net'), {nodes, edges}, {
    nodes:{font:{size:15, face:'Malgun Gothic', background:'rgba(255,255,255,0.82)', strokeWidth:0}},
    edges:{arrows:'to', length:190, smooth:{type:'continuous', roundness:0.2}},
    physics:{barnesHut:{gravitationalConstant:-32000, centralGravity:0.10, springLength:200,
                        springConstant:0.02, avoidOverlap:0.7, damping:0.5},
             stabilization:{iterations:700}},
    interaction:{hover:true, tooltipDelay:120}
  });
</script>
</body></html>
"""


def main():
    html = build()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {OUT}  ({len(html)} bytes)")


if __name__ == "__main__":
    main()
