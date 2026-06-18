"""
RAG 근거층 (v0: 임베딩 의미검색).

교과서를 청크→Gemini 임베딩→코사인 top-k. **다국어** 임베딩이라 한국어 질의로
영어 교과서(Harrison 등)를 의미검색한다. ①생성·②심사의 의학적 근거(grounding)로 주입.

인덱스는 `data/working/rag_index/`(gitignore — 교과서 저작권). ⚠️ 프로토타입(코퍼스 일부 샘플).
하이브리드(BM25)·전체 코퍼스·리랭커는 후속 (architecture §4). BM25는 동일언어 코퍼스(한국 자료)서 추가.
"""
from __future__ import annotations

import re
import json
import zipfile
from pathlib import Path

import numpy as np
from cpx import llm

INDEX_DIR = Path("data/working/rag_index")


def chunks_from_zip(zip_path: str, member: str, max_chunks: int = 1200, chunk_chars: int = 700) -> list[str]:
    """zip 안 텍스트(교과서)를 문단 단위로 쪼개고, 책 전체에 고르게 max_chunks개 샘플."""
    text = zipfile.ZipFile(zip_path).read(member).decode("utf-8", "replace")
    paras = [p.strip().replace("\n", " ") for p in re.split(r"\n\s*\n", text) if len(p.strip()) > 200]
    if len(paras) > max_chunks:
        stride = len(paras) // max_chunks
        paras = paras[::stride][:max_chunks]
    return [p[:chunk_chars] for p in paras]


def build_index(chunks: list[str], name: str = "textbooks") -> int:
    vecs = np.asarray(llm.embed(chunks), dtype=np.float32)
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    np.save(INDEX_DIR / f"{name}.npy", vecs)
    (INDEX_DIR / f"{name}.json").write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    return len(chunks)


def retrieve(query: str, k: int = 3, name: str = "textbooks") -> list[tuple[str, float]]:
    """질의 임베딩 → 코사인 top-k 청크 반환 [(chunk, score)]."""
    vecs = np.load(INDEX_DIR / f"{name}.npy")
    chunks = json.loads((INDEX_DIR / f"{name}.json").read_text(encoding="utf-8"))
    q = np.asarray(llm.embed([query])[0], dtype=np.float32)
    q /= np.linalg.norm(q) + 1e-9
    sims = vecs @ q
    return [(chunks[i], float(sims[i])) for i in np.argsort(-sims)[:k]]


def grounding(query: str, k: int = 3, name: str = "textbooks") -> str:
    """검색 결과를 프롬프트 주입용 텍스트로. 인덱스 없으면 빈 문자열(grounding 생략)."""
    if not (INDEX_DIR / f"{name}.npy").exists():
        return ""
    hits = retrieve(query, k, name)
    return "\n".join(f"[근거{i+1}] {c}" for i, (c, _) in enumerate(hits))
