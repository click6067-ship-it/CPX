"""
관찰·추적(observability) — LangSmith + Langfuse 를 LangGraph 실행에 *선택적*으로 연결.

이 레포 구조: langgraph(오케스트레이션) + raw provider SDK(google.genai/openai/anthropic).
LangChain LLM 래퍼를 안 쓰므로 자동계측이 LLM 호출까지 닿지 않는다 → 2층으로 붙인다.

  ① 노드 트리(generate / review / revise)
      · LangSmith: langgraph 네이티브. env LANGSMITH_TRACING=true + LANGSMITH_API_KEY 면 자동 기록.
      · Langfuse : CallbackHandler 를 graph.invoke(config=...) 로 전달(문서화된 LangGraph 통합 경로).
  ② LLM generation(raw SDK 호출 — 자동계측 사각지대)
      · llm.complete / complete_json 을 @traced(run_type="llm") 로 감싸
        LangSmith span + Langfuse generation 을 명시적으로 생성.

키가 없으면 전부 no-op — 코어 로직·테스트·CI 는 트레이싱 유무와 무관하게 동작한다.

켜는 법 (.env):  먼저 CPX_TRACE_ACK=1 (egress 동의 — 아래 게이트) + 해당 키
  LangSmith → LANGSMITH_API_KEY · (선택) LANGSMITH_PROJECT   ※ LANGSMITH_TRACING 은 코드가 관리(직접 X)
  Langfuse  → LANGFUSE_PUBLIC_KEY · LANGFUSE_SECRET_KEY · (선택) LANGFUSE_HOST
              (HOST 기본 = Langfuse Cloud EU. US 리전/셀프호스트면 명시)

⚠️ 트레이스에는 프롬프트·생성결과가 담긴다. 이 그래프는 *합성* CPX 사례(실제 환자정보 아님)라
   클라우드 전송 위험이 낮지만, ③가상환자·④채점(실제 학생 상호작용) 런타임을 추후 추적할 땐
   data-governance 관점 재검토 필요.
"""
from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


def _truthy(v: str | None) -> bool:
    return (v or "").strip().lower() in ("1", "true", "yes", "on")


# ── 데이터 egress 게이트 (Codex review BLOCKER 반영) ────────────────────────
# 추적을 켜면 프롬프트(사례 JSON·교과서 RAG 발췌 등)가 LangSmith/Langfuse(제3자 SaaS)로
# 전송된다. 부산대 사례·저작권 교과서가 새지 않도록, 키가 있어도 **CPX_TRACE_ACK 를
# 의식적으로 설정**해야만 활성화한다(거버넌스 architecture §7 / data-governance).
# ⚠️ ack 는 "이 실행분은 비식별·합성이거나 egress 를 수용함"의 확인일 뿐, *내용 편집(redaction)
#    은 아직 없다*. 실제 환자·학생 데이터나 저작권 RAG 가 섞인 런에는 켜지 말 것.
_warned = False


def _trace_ack() -> bool:
    return _truthy(os.environ.get("CPX_TRACE_ACK"))


def _warn_unacked(which: str) -> None:
    global _warned
    if not _warned:
        _warned = True
        print(f"[tracing] ⚠️ {which} 키가 있으나 CPX_TRACE_ACK 미설정 → 추적 비활성. "
              "추적을 켜면 프롬프트(사례·교과서 RAG)가 제3자 SaaS 로 전송됨. "
              "비식별·합성 실행분에만 CPX_TRACE_ACK=1 로 켤 것(거버넌스 §7).")


def langsmith_on() -> bool:
    keys = bool(os.environ.get("LANGSMITH_API_KEY"))
    if keys and not _trace_ack():
        _warn_unacked("LangSmith")
        return False
    return keys and _trace_ack()


def langfuse_on() -> bool:
    keys = bool(os.environ.get("LANGFUSE_PUBLIC_KEY") and os.environ.get("LANGFUSE_SECRET_KEY"))
    if keys and not _trace_ack():
        _warn_unacked("Langfuse")
        return False
    return keys and _trace_ack()


# langgraph-native LangSmith 계측은 LANGSMITH_TRACING env 를 *직접* 읽으므로,
# 우리 ack 게이트가 그것까지 통제하도록 모듈 로드 시 프로그램으로 설정한다.
# (사용자는 LANGSMITH_TRACING 을 직접 만지지 말고 CPX_TRACE_ACK 로 켠다.)
os.environ["LANGSMITH_TRACING"] = "true" if langsmith_on() else "false"
if langsmith_on():
    os.environ.setdefault("LANGSMITH_PROJECT", os.environ.get("LANGSMITH_PROJECT") or "cpx-ai")


def status() -> str:
    return f"tracing: LangSmith={'ON' if langsmith_on() else 'off'} · Langfuse={'ON' if langfuse_on() else 'off'}"


@lru_cache(maxsize=1)
def _langfuse_client():
    if not langfuse_on():
        return None
    try:
        from langfuse import get_client
        return get_client()                       # env(LANGFUSE_*)에서 자동 구성
    except Exception as e:                         # noqa: BLE001
        print(f"[tracing] Langfuse client init 실패(무시): {e}")
        return None


@lru_cache(maxsize=1)
def _langfuse_handler():
    if not langfuse_on():
        return None
    try:
        from langfuse.langchain import CallbackHandler
        return CallbackHandler()                   # 전역 client(env) 사용
    except Exception as e:                         # noqa: BLE001
        print(f"[tracing] Langfuse CallbackHandler 실패(무시): {e}")
        return None


def run_config(run_name: str | None = None, metadata: dict | None = None) -> dict:
    """graph.invoke(config=...) 에 넘길 설정.
    Langfuse 콜백(노드 트리) + run_name + metadata 를 담는다.
    LangSmith 는 env 로 자동 기록되므로 콜백 불필요. 트레이서가 없으면 {} 반환(무영향)."""
    cfg: dict = {}
    cbs = [h for h in (_langfuse_handler(),) if h is not None]
    if cbs:
        cfg["callbacks"] = cbs
    if run_name:
        cfg["run_name"] = run_name
    if metadata:
        cfg["metadata"] = metadata
    return cfg


def traced(name: str | None = None, run_type: str = "chain"):
    """함수를 LangSmith span + Langfuse generation/span 으로 감싸는 데코레이터(둘 다 선택적).
    raw SDK LLM 호출(llm.complete*)에 run_type="llm" 으로 붙여 자동계측 사각지대를 메운다.

    · LangSmith traceable: 추적이 꺼져 있으면 호출 시 조용히 단락 → 항상 적용해도 무비용.
    · Langfuse observe   : 키 없으면 경고 로그를 내므로 keys 있을 때만 적용(소음 방지).
    """
    def deco(fn):
        wrapped = fn
        nm = name or fn.__name__
        try:
            from langsmith import traceable
            wrapped = traceable(name=nm, run_type=run_type)(wrapped)
        except Exception:                          # noqa: BLE001 — langsmith 부재 시 무시
            pass
        if langfuse_on():
            try:
                from langfuse import observe
                as_type = "generation" if run_type == "llm" else "span"
                wrapped = observe(name=nm, as_type=as_type)(wrapped)
            except Exception:                      # noqa: BLE001
                pass
        return wrapped
    return deco


def flush() -> None:
    """배경 전송을 강제 flush — 짧은 스크립트가 끝나기 전 트레이스 유실 방지."""
    c = _langfuse_client()
    if c is not None:
        try:
            c.flush()
        except Exception:                          # noqa: BLE001
            pass
    if langsmith_on():
        try:
            from langchain_core.tracers.langchain import wait_for_all_tracers
            wait_for_all_tracers()
        except Exception:                          # noqa: BLE001
            pass
