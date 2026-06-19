"""
RAG 근거층 — **하이브리드 검색(dense 임베딩 + sparse BM25)**.

- dense  : Gemini 임베딩(다국어) → 코사인. 한국어 질의로 영어 교과서를 *의미* 검색.
- sparse : BM25(rank_bm25, **로컬 계산·API 없음**) → 정확 단어/용어 매칭. 동일언어 코퍼스에 강함.
- 병합   : RRF(Reciprocal Rank Fusion). ①생성·②심사의 의학적 근거(grounding)로 주입.

서버 불필요: 임베딩=API 1회, 저장=로컬 .npy/.json, BM25·병합=메모리 계산, 생성=LLM API.
인덱스 `data/working/rag_index/`(gitignore — 교과서 저작권). 코퍼스 출처·모델 = `docs/transparency.md`.
⚠️ 프로토타입: 현재 MedQA 교과서 중 Harrison 1권 샘플(1200청크). 전체 코퍼스·한국 자료·리랭커는 후속.
"""
from __future__ import annotations

import re
import json
import zipfile
from pathlib import Path

import numpy as np
from cpx import llm

INDEX_DIR = Path("data/working/rag_index")
_bm25_cache: dict = {}


def chunks_from_zip(zip_path: str, member: str, max_chunks: int = 1200, chunk_chars: int = 700) -> list[str]:
    text = zipfile.ZipFile(zip_path).read(member).decode("utf-8", "replace")
    paras = [p.strip().replace("\n", " ") for p in re.split(r"\n\s*\n", text) if len(p.strip()) > 200]
    if len(paras) > max_chunks:
        stride = len(paras) // max_chunks
        paras = paras[::stride][:max_chunks]
    return [p[:chunk_chars] for p in paras]


def build_index(chunks: list[str], name: str = "textbooks") -> int:
    """dense 임베딩 인덱스 저장. (BM25는 검색 시 .json에서 즉석 구축 — 별도 저장 불필요)"""
    vecs = np.asarray(llm.embed(chunks), dtype=np.float32)
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    np.save(INDEX_DIR / f"{name}.npy", vecs)
    (INDEX_DIR / f"{name}.json").write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    return len(chunks)


def _tok(s: str) -> list[str]:
    """간이 토크나이저(영문 단어 + 한글 어절). Korean 형태소분석은 후속."""
    return re.findall(r"[a-z0-9]+|[가-힣]+", s.lower())


def _chunks(name: str) -> list[str]:
    return json.loads((INDEX_DIR / f"{name}.json").read_text(encoding="utf-8"))


def _bm25(name: str):
    """BM25 인덱스 — .json 청크에서 즉석 구축(프로세스 캐시). 로컬·API 없음."""
    if name not in _bm25_cache:
        from rank_bm25 import BM25Okapi
        chunks = _chunks(name)
        _bm25_cache[name] = (BM25Okapi([_tok(c) for c in chunks]), chunks)
    return _bm25_cache[name]


def retrieve(query: str, k: int = 3, name: str = "textbooks") -> list[tuple[str, float]]:
    """dense(임베딩) 단독 검색 — 하위호환/폴백."""
    vecs = np.load(INDEX_DIR / f"{name}.npy")
    chunks = _chunks(name)
    q = np.asarray(llm.embed([query])[0], dtype=np.float32)
    q /= np.linalg.norm(q) + 1e-9
    sims = vecs @ q
    return [(chunks[i], float(sims[i])) for i in np.argsort(-sims)[:k]]


def retrieve_hybrid(query: str, k: int = 3, name: str = "textbooks", n: int = 12) -> list[str]:
    """dense top-n + sparse(BM25) top-n → RRF 병합 → top-k 청크."""
    chunks = _chunks(name)
    vecs = np.load(INDEX_DIR / f"{name}.npy")
    q = np.asarray(llm.embed([query])[0], dtype=np.float32); q /= np.linalg.norm(q) + 1e-9
    dense = list(np.argsort(-(vecs @ q))[:n])
    bm, _ = _bm25(name)
    sparse = list(np.argsort(-bm.get_scores(_tok(query)))[:n])
    rrf: dict = {}
    for r, i in enumerate(dense):
        rrf[int(i)] = rrf.get(int(i), 0.0) + 1.0 / (60 + r)
    for r, i in enumerate(sparse):
        rrf[int(i)] = rrf.get(int(i), 0.0) + 1.0 / (60 + r)
    top = sorted(rrf, key=lambda i: -rrf[i])[:k]
    return [chunks[i] for i in top]


def grounding(query: str, k: int = 3, name: str = "textbooks") -> str:
    """하이브리드 검색 → 프롬프트 주입용. 인덱스 없으면 빈 문자열. BM25 실패 시 dense 폴백."""
    if not (INDEX_DIR / f"{name}.npy").exists():
        return ""
    try:
        hits = retrieve_hybrid(query, k, name)
    except Exception:
        hits = [c for c, _ in retrieve(query, k, name)]
    return "\n".join(f"[근거{i+1}] {c}" for i, c in enumerate(hits))
