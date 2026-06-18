"""
LLM 어댑터 — **모델 교체 지점**.

지금: Gemini(AI Studio). Claude/GPT로 바꾸려면 이 파일의 함수 본문만 교체(인터페이스 동일).
키는 .env에서 로드. 키 값은 코드/로그에 절대 하드코딩하지 않음.
"""
from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv

# 프로젝트 루트의 .env (src/cpx/llm.py → parents[2] = repo root)
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-lite-latest")


@lru_cache(maxsize=1)
def _client():
    from google import genai
    return genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


def complete(prompt: str, *, model: str | None = None, temperature: float = 0.0) -> str:
    """자유 텍스트 생성."""
    resp = _client().models.generate_content(
        model=model or DEFAULT_MODEL,
        contents=prompt,
        config={"temperature": temperature},
    )
    return resp.text


def complete_json(prompt: str, schema, *, model: str | None = None, temperature: float = 0.0):
    """구조화 출력 — Pydantic schema로 강제. 반환 = 검증된 객체."""
    resp = _client().models.generate_content(
        model=model or DEFAULT_MODEL,
        contents=prompt,
        config={
            "temperature": temperature,
            "response_mime_type": "application/json",
            "response_schema": schema,
        },
    )
    return resp.parsed


EMBED_MODEL = os.environ.get("EMBED_MODEL", "gemini-embedding-001")  # MTEB 상위, 다국어


def embed(texts: list[str], *, model: str | None = None, batch: int = 100) -> list[list[float]]:
    """텍스트 임베딩 (배치). 다국어 — 한국어 질의↔영어 교과서 의미매칭."""
    out: list[list[float]] = []
    for i in range(0, len(texts), batch):
        r = _client().models.embed_content(model=model or EMBED_MODEL, contents=texts[i:i + batch])
        out.extend(e.values for e in r.embeddings)
    return out
