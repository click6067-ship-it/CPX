"""
공개용 *redaction 적용* 샘플 트레이스 생성 — 실제 graph 1회 실행.

목적: "추적은 켜되 사례·교과서(RAG) 본문은 마스킹되어 공개 가능"을 *실데이터*로 증명.
  · 각 LLM 호출의 input/output 을 tracing._mask 로 마스킹해 기록(= SaaS 로 나가는 것과 동일 규칙).
  · graph 의 진행 로그(비민감: 단계·verdict·must_fix)는 그대로 — 흐름은 투명, 본문은 비노출.

실행:  CPX_TRACE_ACK=1 PYTHONPATH=src .venv/bin/python scripts/sample_trace.py
       (ACK=1 이면 LangSmith 로도 라이브 업로드 — 내용은 HIDE 로 비공개. 키 없어도 로컬 산출물은 생성.)
산출물: docs/sample-trace-redacted.{json,md,html}
"""
from __future__ import annotations

import html as _html
import json
import time
from pathlib import Path

from cpx import llm, tracing, graph

DOCS = Path(__file__).resolve().parent.parent / "docs"
records: list[dict] = []


def _wrap(name, fn):
    def inner(*a, **k):
        prompt = a[0] if a else k.get("prompt", "")
        model = k.get("model") or (a[2] if name == "complete_json" and len(a) > 2 else None) or llm.DEFAULT_MODEL
        t0 = time.time()
        out = fn(*a, **k)
        dt = int((time.time() - t0) * 1000)
        out_repr = out if isinstance(out, str) else out
        records.append({
            "step": len(records) + 1,
            "fn": name,
            "model": model,
            "ms": dt,
            "input_redacted": tracing._mask(prompt),
            "output_redacted": tracing._mask(out_repr),
            "output_chars": len(out if isinstance(out, str) else (out.model_dump_json() if hasattr(out, "model_dump_json") else str(out))),
        })
        return out
    return inner


def main() -> None:
    print(tracing.status())
    llm.complete = _wrap("complete", llm.complete)
    llm.complete_json = _wrap("complete_json", llm.complete_json)

    symptom, diagnosis = "어지러움", "양성돌발두위현훈(BPPV)"
    t0 = time.time()
    result = graph.develop_case(symptom, diagnosis, max_rounds=1, use_clinical=True)
    total_ms = int((time.time() - t0) * 1000)

    pipeline_log = result["log"]                                  # 비민감: 단계·verdict·must_fix
    payload = {
        "what": "CPX 사례개발 graph(LangGraph) 1회 실행의 redaction 적용 트레이스",
        "input": {"symptom": symptom, "diagnosis": diagnosis, "max_rounds": 1, "use_clinical": True},
        "model_default": llm.DEFAULT_MODEL,
        "total_ms": total_ms,
        "redaction": "tracing._mask — 사례·교과서(RAG) 본문 → <redacted:Nc sha256:..>, 도메인모델 → <Type redacted>",
        "pipeline_log": pipeline_log,
        "llm_calls_redacted": records,
    }
    (DOCS / "sample-trace-redacted.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # ── 사람이 읽는 md ──
    md = [f"# 공개 샘플 트레이스 (redaction 적용)\n",
          "> 실제 LangGraph 사례개발 그래프 **1회 실행**. 사례·교과서(RAG) 본문은 `tracing._mask` 로 "
          "마스킹(길이+sha256). 흐름·verdict 같은 비민감 정보는 그대로 — *투명성은 유지, 본문은 비노출*.\n",
          f"- 입력: 주증상=`{symptom}` · 진단=`{diagnosis}` · max_rounds=1 · ②B(임상)=on",
          f"- 기본 모델: `{llm.DEFAULT_MODEL}` · 총 {total_ms:,} ms · LLM 호출 {len(records)}회\n",
          "## 파이프라인 로그 (비민감)\n"]
    for line in pipeline_log:
        md.append(f"- {line}")
    md.append("\n## LLM 호출 (input/output redacted)\n")
    md.append("| # | 함수 | 모델 | input (redacted) | output (redacted) | out chars | ms |")
    md.append("|---|---|---|---|---|---|---|")
    for r in records:
        md.append(f"| {r['step']} | `{r['fn']}` | {r['model']} | `{r['input_redacted']}` | "
                  f"`{r['output_redacted']}` | {r['output_chars']:,} | {r['ms']:,} |")
    md.append("\n> 재현: `CPX_TRACE_ACK=1 PYTHONPATH=src .venv/bin/python scripts/sample_trace.py`. "
              "redaction 규칙 = `src/cpx/tracing.py` `_mask`. 같은 본문 → 같은 sha256(변조 검증 가능).")
    (DOCS / "sample-trace-redacted.md").write_text("\n".join(md), encoding="utf-8")

    # ── 스샷용 html ──
    esc = _html.escape
    rows = "\n".join(
        f"<tr><td>{r['step']}</td><td><code>{esc(r['fn'])}</code></td><td>{esc(r['model'])}</td>"
        f"<td class=r>{esc(r['input_redacted'])}</td><td class=r>{esc(r['output_redacted'])}</td>"
        f"<td>{r['output_chars']:,}</td><td>{r['ms']:,}</td></tr>" for r in records)
    logs = "".join(f"<li>{esc(l)}</li>" for l in pipeline_log)
    html = f"""<!doctype html><meta charset=utf-8><style>
    body{{font:14px/1.5 -apple-system,Segoe UI,Malgun Gothic,sans-serif;max-width:1000px;margin:24px auto;color:#1b1b1f}}
    h1{{font-size:20px}} .sub{{color:#555}} code{{background:#f2f0ff;padding:1px 4px;border-radius:4px}}
    .r{{color:#7a3df0;font-family:ui-monospace,monospace;font-size:12px}}
    table{{border-collapse:collapse;width:100%;margin-top:8px}} td,th{{border:1px solid #e3e0f0;padding:6px 8px;text-align:left;font-size:12px}}
    th{{background:#7EE787;color:#063}} .badge{{display:inline-block;background:#bfb6fc;border-radius:6px;padding:2px 8px;margin:2px}}
    ul{{background:#faf9ff;border:1px solid #eee;border-radius:8px;padding:12px 28px}}</style>
    <h1>🔒 공개 샘플 트레이스 — redaction 적용 (CPX-AI)</h1>
    <p class=sub>실제 LangGraph 사례개발 1회 실행 · 모델 <code>{llm.DEFAULT_MODEL}</code> · 총 {total_ms:,} ms ·
    사례·교과서(RAG) 본문은 마스킹(길이+sha256), 흐름·verdict 는 공개</p>
    <p><span class=badge>주증상 {symptom}</span><span class=badge>진단 {diagnosis}</span>
    <span class=badge>②B 임상 on</span><span class=badge>LLM {len(records)}회</span></p>
    <h3>파이프라인 로그 (비민감)</h3><ul>{logs}</ul>
    <h3>LLM 호출 (input/output redacted)</h3>
    <table><tr><th>#</th><th>함수</th><th>모델</th><th>input (redacted)</th><th>output (redacted)</th><th>chars</th><th>ms</th></tr>
    {rows}</table>"""
    (DOCS / "sample-trace-redacted.html").write_text(html, encoding="utf-8")

    print(f"\n파이프라인: {' → '.join(pipeline_log)}")
    print(f"LLM 호출 {len(records)}회, 모두 redaction 적용. 산출물: docs/sample-trace-redacted.{{json,md,html}}")


if __name__ == "__main__":
    main()
