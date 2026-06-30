"""흉통 온톨로지 YAML → Neo4j Cypher (한 방향 렌더, 시각화용).

정본 = ontology/chest_pain.yaml. Neo4j는 *거울*(보여주기)이지 편집 대상이 아니다.

사용:
  .venv/bin/python scripts/yaml_to_cypher.py            # → ontology/chest_pain.cypher
  cat ontology/chest_pain.cypher | docker exec -i <neo4j> cypher-shell -u neo4j -p <pw>
"""
from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ontology_graph import load_graph  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_YAML = os.path.join(ROOT, "ontology", "chest_pain.yaml")
DEFAULT_OUT = os.path.join(ROOT, "ontology", "chest_pain.cypher")


def _esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def to_cypher(yaml_path: str) -> str:
    _, nodes, edges = load_graph(yaml_path)
    lines = [
        "// 흉통 온톨로지 — YAML→Cypher 자동생성. 정본=ontology/chest_pain.yaml. 손편집 금지.",
        "MATCH (n) DETACH DELETE n;",  # 멱등: 매번 깨끗이 재로드
    ]
    for n in nodes.values():
        lines.append(
            f'MERGE (:{n["type"]} {{id:"{_esc(n["id"])}", label:"{_esc(n["label"])}"}});'
        )
    for src, rel, dst in edges:
        lines.append(
            f'MATCH (a {{id:"{_esc(src)}"}}), (b {{id:"{_esc(dst)}"}}) '
            f"MERGE (a)-[:{rel}]->(b);"
        )
    return "\n".join(lines) + "\n"


def main():
    yaml_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_YAML
    out_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUT
    cypher = to_cypher(yaml_path)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(cypher)
    n_nodes = cypher.count("MERGE (:")
    n_edges = cypher.count("MERGE (a)-[:")
    print(f"wrote {out_path}  ({n_nodes} nodes, {n_edges} edges)")


if __name__ == "__main__":
    main()
