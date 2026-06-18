"""
RAG 인덱스 구축 (프로토타입: Harrison 내과 일부 샘플).
실행: PYTHONPATH=src .venv/bin/python scripts/build_rag_index.py
인덱스 → data/working/rag_index/ (gitignore, 저작권). 전체 코퍼스·다책은 후속.
"""
from cpx import rag

MEMBER = "data_clean/textbooks/en/InternalMed_Harrison.txt"
chunks = rag.chunks_from_zip("data_clean.zip", MEMBER, max_chunks=1200)
print(f"{len(chunks)} chunks 추출 → 임베딩 중…")
n = rag.build_index(chunks, "textbooks")
print(f"✅ 인덱스 완료: {n} chunks → data/working/rag_index/textbooks.{{npy,json}}")
