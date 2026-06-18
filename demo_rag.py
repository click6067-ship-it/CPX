"""
RAG 검색 데모 — 한국어 질의로 영어 교과서 의미검색.
실행: PYTHONPATH=src .venv/bin/python demo_rag.py   (먼저 scripts/build_rag_index.py)
"""
from cpx import rag

queries = [
    "급성 신우신염 환자에서 물어봐야 할 병력",
    "흉통 환자의 심근경색 위험인자",
    "만성 설사의 감별진단",
]
for q in queries:
    print(f"\nQ(한국어): {q}")
    for c, s in rag.retrieve(q, 2):
        print(f"  [{s:.2f}] {c[:150]}…")
