"""
LangGraph 네이티브 렌더 — src/cpx/graph.py의 *실제 컴파일된* 그래프를 그대로 시각화.

손으로 그린 docs/cpx-flow.* (전체 시스템 아키텍처)와 달리, 이 산출물은
`graph.build().get_graph()` 에서 직접 뽑으므로 코드와 100% 일치한다(재현 가능).

실행:  PYTHONPATH=src .venv/bin/python scripts/render_langgraph.py
산출물: docs/cpx-langgraph.mmd  (mermaid 텍스트 — 네트워크 불필요)
        docs/cpx-langgraph.png  (PNG — mermaid.ink API 사용, 네트워크 필요)
"""
from __future__ import annotations

from pathlib import Path

from cpx import graph

DOCS = Path(__file__).resolve().parent.parent / "docs"


def main() -> None:
    app = graph.build()
    g = app.get_graph()

    # 1) mermaid 텍스트 — 항상 동작(네트워크 불필요), 코드 정본
    mmd = g.draw_mermaid()
    (DOCS / "cpx-langgraph.mmd").write_text(mmd, encoding="utf-8")
    print("=== mermaid (저장: docs/cpx-langgraph.mmd) ===")
    print(mmd)

    # 2) PNG — mermaid.ink API. 네트워크 없으면 .mmd만 남고 여기서 건너뜀.
    try:
        png = g.draw_mermaid_png()
        (DOCS / "cpx-langgraph.png").write_bytes(png)
        print(f"PNG 저장: docs/cpx-langgraph.png ({len(png):,} bytes)")
    except Exception as e:  # noqa: BLE001 — 네트워크/의존성 부재는 치명적 아님
        print(f"PNG 건너뜀 (네트워크/의존성): {e}")
        print("→ docs/cpx-langgraph.mmd 를 mmdc/Mermaid Live 로 렌더하면 됨.")


if __name__ == "__main__":
    main()
