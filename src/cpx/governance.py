"""거버넌스 유틸 — 데이터 누수·저작권·재현성 방어 (Codex '놓친 필수' 반영, 2026-06-20).

- near-copy 탐지 : 생성/색인 텍스트가 원본(부산대 사례·교과서)을 베끼지 않았나 (n-gram 자카드, 로컬 계산)
- provenance     : 산출물에 출처·모델·버전 스탬프 (재현·감사 추적)
- version freeze : 코드·프롬프트 버전 고정 (검증 전 freeze)
- cost           : 모델 단가표 + 추정 (예산 상한 점검)

⚠️ 전부 **로컬 계산** — 실제 사례·교과서 원문을 외부로 전송하지 않는다.
"""
from __future__ import annotations

import re

# ── 버전 freeze (검증 산출물에 박아 재현 보장) ──
VERSION = "cpx-0.3"
PROMPT_VERSION = {"generator": "g1", "reviewer_A": "a1", "reviewer_B": "b1"}

# ── 모델 단가 (USD per 1M tokens, in/out) ──
# ⚠️ 추정·변동값. 실제 청구 전 각 provider 콘솔에서 재확인. None=미확정.
PRICING = {
    "gpt-5.5": (5.0, 30.0),                  # OpenAI 공식(2026-06, in/out per 1M) — Codex 확인
    "gemini-2.5-flash": (0.30, 2.50),        # Google 공식
    "gemini-embedding-001": (0.15, 0.0),     # 임베딩(출력 토큰 없음)
}


def _char_ngrams(text: str, n: int = 10) -> set:
    s = re.sub(r"\s+", "", (text or "").lower())
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def _containment(a_set: set, b_set: set) -> float:
    """a의 조각이 b에 얼마나 포함되나 = |a∩b|/|a| (분모=작은 쪽 → 부분복제에 민감)."""
    return len(a_set & b_set) / len(a_set) if a_set else 0.0


def near_copy_ratio(a: str, b: str, n: int = 10) -> float:
    """char n-gram **containment**(양방향 max). 자카드와 달리 긴 텍스트의 부분 복제에도 민감(Codex 반영)."""
    A, B = _char_ngrams(a, n), _char_ngrams(b, n)
    return max(_containment(A, B), _containment(B, A)) if (A and B) else 0.0


def check_near_copy(text: str, originals: list[str], win: int = 40, thresh: float = 0.6) -> dict:
    """생성 text가 원본 일부를 복제했는지: **text를 win(어절) 창으로** 슬라이드하며
    '그 창이 원본에 통째로 들어있나'(char n-gram containment)의 최대치. 복제 구간이 한 창에 잡히면 1.0에 근접 → flag.
    (휴리스틱 1차 필터 — 패러프레이즈/문장 재배열은 못 잡음. 통과가 '독창성 증명' 아님.)"""
    gwords = re.findall(r"[a-z0-9가-힣]+", (text or "").lower())
    gwins = [" ".join(gwords[j:j + win]) for j in range(0, max(1, len(gwords) - win + 1), max(1, win // 2))] or [text]
    best, idx = 0.0, -1
    for i, o in enumerate(originals):
        ochar = _char_ngrams(o)
        for gw in gwins:
            r = _containment(_char_ngrams(gw), ochar)   # 생성 창이 원본에 통째 있나
            if r > best:
                best, idx = r, i
    return {"max_ratio": round(best, 3), "match_idx": idx, "flag": best >= thresh, "thresh": thresh, "win": win}


def provenance(kind: str, source: str, model: str | None, seed_id: str | None = None) -> dict:
    """산출물 출처 스탬프(재현·감사). kind=case|index 등, source=seed 출처/코퍼스명."""
    return {"kind": kind, "source": source, "model": model, "seed_id": seed_id,
            "code_version": VERSION, "prompt_version": dict(PROMPT_VERSION)}


def est_cost(model: str, in_tok: int, out_tok: int = 0) -> float | None:
    """추정 비용(USD). 단가 미확정이면 None(=청구 전 확인 필요)."""
    p = PRICING.get(model)
    if not p or p[0] is None:
        return None
    return round(in_tok / 1e6 * p[0] + out_tok / 1e6 * (p[1] or 0.0), 4)
