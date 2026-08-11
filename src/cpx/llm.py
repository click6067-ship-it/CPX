"""
LLM 어댑터 — **모델 교체 지점** (모델명 prefix로 3사 자동 라우팅).

계획서(임선주 교수) 지정: Claude=①생성·②심사, GPT-4o=③대화·④채점, 임베딩=Gemini.
- claude*  → Anthropic   (ANTHROPIC_API_KEY)
- gpt*/o1* → OpenAI       (OPENAI_API_KEY)
- 그 외     → Gemini       (GOOGLE_API_KEY)
임베딩은 항상 Gemini(Claude/GPT는 임베딩 API 없음). 키·값은 코드/로그에 하드코딩 금지(.env).
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv

from cpx import tracing


def _retry(fn, tries: int = 5, base: float = 4.0):
    """일시적 과부하/레이트리밋 지수 백오프 (3사 공통)."""
    for i in range(tries):
        try:
            return fn()
        except Exception as e:
            msg = str(e)
            transient = any(x in msg for x in (
                "503", "429", "529", "UNAVAILABLE", "RESOURCE_EXHAUSTED",
                "overloaded", "Overloaded", "rate_limit", "rate limit"))
            if i == tries - 1 or not transient:
                raise
            time.sleep(base * (2 ** i))


load_dotenv(Path(__file__).resolve().parents[2] / ".env")
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-lite-latest")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "gemini-embedding-001")
MAX_TOK = int(os.environ.get("MAX_TOKENS", "8192"))
# Gemini 구조화 출력 상한. 기본 16k — CpxCase(체크리스트 20~28항목)가 대략 5~8k 토큰이라 여유 2배.
GEMINI_MAX_OUT = int(os.environ.get("GEMINI_MAX_OUT", "16384"))


def _provider(model: str) -> str:
    m = (model or "").lower()
    if m.startswith("claude"):
        return "anthropic"
    if m.startswith(("gpt", "o1", "o3", "o4", "chatgpt")):
        return "openai"
    return "gemini"


def _oai_temp(model: str, temperature: float) -> dict:
    """추론모델(gpt-5*·o*)은 temperature 미지원 → 생략. gpt-4*만 temperature 전달."""
    m = (model or "").lower()
    if m.startswith(("gpt-5", "o1", "o3", "o4")):
        return {}
    return {"temperature": temperature}


@lru_cache(maxsize=1)
def _gemini():
    from google import genai
    return genai.Client(api_key=os.environ["GOOGLE_API_KEY"])


@lru_cache(maxsize=1)
def _anthropic():
    import anthropic
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


@lru_cache(maxsize=1)
def _openai():
    import openai
    return openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])


@tracing.traced(name="llm.complete", run_type="llm")
def complete(prompt: str, *, model: str | None = None, temperature: float = 0.0) -> str:
    """자유 텍스트 생성."""
    model = model or DEFAULT_MODEL
    p = _provider(model)
    if p == "gemini":
        return _retry(lambda: _gemini().models.generate_content(
            model=model, contents=prompt, config={"temperature": temperature})).text
    if p == "anthropic":
        r = _retry(lambda: _anthropic().messages.create(
            model=model, max_tokens=MAX_TOK, temperature=temperature,
            messages=[{"role": "user", "content": prompt}]))
        return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")
    r = _retry(lambda: _openai().chat.completions.create(
        model=model, messages=[{"role": "user", "content": prompt}], **_oai_temp(model, temperature)))
    return r.choices[0].message.content


@tracing.traced(name="llm.complete_json", run_type="llm")
def complete_json(prompt: str, schema, *, model: str | None = None, temperature: float = 0.0):
    """구조화 출력 — Pydantic schema 강제. 반환 = 검증된 객체."""
    model = model or DEFAULT_MODEL
    p = _provider(model)
    if p == "gemini":
        r = _retry(lambda: _gemini().models.generate_content(
            model=model, contents=prompt,
            config={"temperature": temperature, "response_mime_type": "application/json",
                    "response_schema": schema, "max_output_tokens": GEMINI_MAX_OUT}))
        if r.parsed is None:
            # ⚠️ 조용히 None 을 흘리면 호출부에서 AttributeError 로 터져 원인이 안 보인다.
            #    실제로 그렇게 죽었다(2026-08-12): 상한 없는 "checklist 20개 이상" 지시로 모델이
            #    폭주 → 출력 59,780 토큰 → MAX_TOKENS 로 잘린 JSON → parsed=None → downstream 폭발.
            fr = getattr(r.candidates[0], "finish_reason", "?") if r.candidates else "?"
            out = getattr(r.usage_metadata, "candidates_token_count", "?") if r.usage_metadata else "?"
            raise RuntimeError(
                f"gemini 구조화 출력 파싱 실패 (finish_reason={fr}, 출력토큰={out}). "
                f"MAX_TOKENS 면 프롬프트에서 리스트 길이에 **상한**을 주거나 "
                f"GEMINI_MAX_OUT 환경변수를 올릴 것.")
        return r.parsed
    if p == "openai":
        r = _retry(lambda: _openai().beta.chat.completions.parse(
            model=model, messages=[{"role": "user", "content": prompt}],
            response_format=schema, **_oai_temp(model, temperature)))
        return r.choices[0].message.parsed
    # anthropic: tool-use로 구조화 강제
    tool = {"name": "emit", "description": "Return the structured result.",
            "input_schema": schema.model_json_schema()}
    r = _retry(lambda: _anthropic().messages.create(
        model=model, max_tokens=MAX_TOK, temperature=temperature, tools=[tool],
        tool_choice={"type": "tool", "name": "emit"},
        messages=[{"role": "user", "content": prompt}]))
    for b in r.content:
        if getattr(b, "type", "") == "tool_use":
            return schema.model_validate(b.input)
    raise RuntimeError("anthropic: tool_use 미반환")


def embed(texts: list[str], *, model: str | None = None, batch: int = 100) -> list[list[float]]:
    """텍스트 임베딩 — 항상 Gemini(다국어). Claude/GPT는 임베딩 API 없음."""
    out: list[list[float]] = []
    for i in range(0, len(texts), batch):
        chunk = texts[i:i + batch]
        r = _retry(lambda: _gemini().models.embed_content(model=model or EMBED_MODEL, contents=chunk))
        out.extend(e.values for e in r.embeddings)
    return out
