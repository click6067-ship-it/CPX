"""흉통 온톨로지 YAML → 인터랙티브 HTML 그래프 (서버 0, 브라우저로 바로 열기).

정본 = ontology/chest_pain.yaml. Neo4j가 없어도 미팅에서 *살아있는 흉통 그래프*를 보여주는 fallback.
vis-network(CDN) 한 파일. 노드 드래그·줌·hover 가능.

사용:  .venv/bin/python scripts/yaml_to_html.py   # → docs/chest_pain-graph.html
"""
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ontology_graph import load_graph, NODE_STYLE, REL_KO  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_YAML = os.path.join(ROOT, "ontology", "chest_pain.yaml")
DEFAULT_OUT = os.path.join(ROOT, "docs", "chest_pain-graph.html")

_TEMPLATE = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>흉통 온톨로지 그래프 (CPX)</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  body{margin:0;font-family:'Malgun Gothic',sans-serif;background:#fafafa}
  #hd{padding:10px 16px;border-bottom:1px solid #ddd;background:#fff}
  #hd h1{margin:0;font-size:18px}
  #hd .sub{color:#666;font-size:12px;margin-top:3px}
  #hd .warn{color:#b91c1c;font-size:12px;margin-top:4px;font-weight:bold}
  #legend{padding:6px 16px;font-size:12px;border-bottom:1px solid #eee;background:#fff}
  #legend span{display:inline-block;margin-right:14px}
  #legend i{display:inline-block;width:11px;height:11px;border-radius:50%;margin-right:4px;vertical-align:middle}
  #net{width:100%;height:calc(100vh - 110px)}
</style></head>
<body>
<div id="hd">
  <h1>흉통(chest pain) 온톨로지 — CPX 사례 생성 뼈대</h1>
  <div class="sub">__TITLE__ · 정본 ontology/chest_pain.yaml → 한 방향 렌더(거울)</div>
  <div class="warn">⚠ review_status: draft — 임상 내용은 교수 검증 전 구조 시연용 초안</div>
</div>
<div id="legend">__LEGEND__</div>
<div id="net"></div>
<script>
  const nodes = new vis.DataSet(__NODES__);
  const edges = new vis.DataSet(__EDGES__);
  new vis.Network(document.getElementById('net'), {nodes, edges}, {
    nodes:{shape:'dot', size:15, font:{size:14, face:'Malgun Gothic'}},
    edges:{arrows:'to', font:{size:9, color:'#888', strokeWidth:3, strokeColor:'#fff'},
           color:{color:'#bbb', highlight:'#555'}, smooth:{type:'continuous'}},
    physics:{barnesHut:{gravitationalConstant:-9000, springLength:130, avoidOverlap:0.3},
             stabilization:{iterations:250}},
    interaction:{hover:true, tooltipDelay:120}
  });
</script>
</body></html>
"""


def build_html(yaml_path: str) -> str:
    _, nodes, edges = load_graph(yaml_path)

    vis_nodes = []
    for n in nodes.values():
        color, _ = NODE_STYLE.get(n["type"], ("#999999", n["type"]))
        size = 28 if n["type"] == "ChiefComplaint" else (22 if n["type"].startswith("Disease") else 14)
        vis_nodes.append({
            "id": n["id"], "label": n["label"], "title": f'{n["label"]} ({n["type"]})',
            "color": color, "size": size,
        })

    vis_edges = []
    for src, rel, dst in edges:
        vis_edges.append({
            "from": src, "to": dst, "label": REL_KO.get(rel, rel), "title": rel,
            "dashes": rel == "DIFFERENTIAL_OF",
        })

    legend = " ".join(
        f'<span><i style="background:{color}"></i>{ko}</span>'
        for _t, (color, ko) in NODE_STYLE.items()
    )
    title = f"질환 {sum(1 for n in nodes.values() if n['type'].startswith('Disease'))}개 · 노드 {len(nodes)} · 엣지 {len(edges)}"

    return (
        _TEMPLATE
        .replace("__NODES__", json.dumps(vis_nodes, ensure_ascii=False))
        .replace("__EDGES__", json.dumps(vis_edges, ensure_ascii=False))
        .replace("__LEGEND__", legend)
        .replace("__TITLE__", title)
    )


def main():
    yaml_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_YAML
    out_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT
    html = build_html(yaml_path)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"wrote {out_path}  ({len(html)} bytes)")


if __name__ == "__main__":
    main()
