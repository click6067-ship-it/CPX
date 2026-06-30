"""흉통 온톨로지 YAML → 그래프(노드·엣지) 공통 빌더.

정본 = ontology/chest_pain.yaml. yaml_to_cypher.py(Neo4j) · yaml_to_html.py(정적 뷰)가 공유.
한 방향 렌더(YAML → 그래프)만 — 그래프 쪽에서 거꾸로 편집하지 않는다.
"""
from __future__ import annotations
import yaml

# 노드 타입 → (색, 한국어 범례)
NODE_STYLE = {
    "ChiefComplaint":       ("#7c3aed", "주호소"),
    "DiseasePrimary":       ("#dc2626", "대표진단"),
    "DiseaseDifferential":  ("#f87171", "감별질환"),
    "Symptom":              ("#2563eb", "증상/감별단서"),
    "RedFlag":              ("#ea580c", "red flag"),
    "ChecklistItem":        ("#16a34a", "채점항목"),
    "Test":                 ("#6b7280", "검사"),
}

# 관계 타입 → 한국어 표시
REL_KO = {
    "PRESENTS_AS":      "호소",
    "REQUIRES_SYMPTOM": "필수증상",
    "DISCRIMINATOR":    "감별단서",
    "HAS_RED_FLAG":     "red flag",
    "CHECKLIST":        "채점",
    "INDICATED_TEST":   "검사",
    "DIFFERENTIAL_OF":  "감별",
}


def load_graph(yaml_path: str):
    """YAML 정본 → (data, nodes, edges).

    nodes: {id: {"id", "label", "type"}}
    edges: [(src_id, rel, dst_id), ...]
    """
    with open(yaml_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    labels = data.get("labels", {})
    nodes: dict[str, dict] = {}
    edges: list[tuple[str, str, str]] = []

    def add_node(nid: str, ntype: str):
        if nid not in nodes:
            nodes[nid] = {"id": nid, "label": labels.get(nid, nid), "type": ntype}

    cc = data["chief_complaint"]
    add_node(cc, "ChiefComplaint")

    for d in data["diseases"]:
        did = d["id"]
        dtype = "DiseasePrimary" if d.get("role") == "primary" else "DiseaseDifferential"
        add_node(did, dtype)
        edges.append((cc, "PRESENTS_AS", did))

        for s in d.get("required_symptoms", []):
            add_node(s, "Symptom"); edges.append((did, "REQUIRES_SYMPTOM", s))
        for s in d.get("discriminators", []):
            add_node(s, "Symptom"); edges.append((did, "DISCRIMINATOR", s))
        for r in d.get("red_flags", []):
            add_node(r, "RedFlag"); edges.append((did, "HAS_RED_FLAG", r))
        for c in d.get("checklist_items", []):
            add_node(c, "ChecklistItem"); edges.append((did, "CHECKLIST", c))
        for t in d.get("tests", []):
            add_node(t, "Test"); edges.append((did, "INDICATED_TEST", t))

        df = d.get("differential_of")
        if df:
            edges.append((did, "DIFFERENTIAL_OF", df))

    return data, nodes, edges
