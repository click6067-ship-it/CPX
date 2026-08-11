"""온톨로지 근거화 현황 리포트 → 자체완결 HTML (로컬 전용, 브라우저로 바로 열기).

각 주증상 YAML의 diseases[].evidence 를 읽어 **출처·근거수준**을 표로, 그리고
**못 한 것/안 한 것(정직한 미완)** 을 별도 섹션으로 렌더. 서버·인터넷 불필요.

사용:  .venv/bin/python scripts/ontology_report.py   # → docs/ontology-grounding-report.html
"""
from __future__ import annotations
import html
import os
import re
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYMS = ["abdominal_pain", "chest_pain", "diarrhea", "constipation"]
OUT = os.path.join(ROOT, "docs", "ontology-grounding-report.html")

LEVEL = {
    "real_case_direct":  ("실사례 (직접)",  "#15803d", "#dcfce7", "해당 주증상 station의 실제 부산대 CPX 사례로 근거"),
    "real_case_related": ("실사례 (연관)",  "#1d4ed8", "#dbeafe", "동일 질환이 다른 주증상 station 실사례에 존재 → 그 사례로 근거"),
    "station_differential_listed": ("사례 감별목록 명시", "#0e7490", "#cffafe",
                                    "해당 station 실사례 채점표에 감별진단·문진·검사로 명시(확정진단은 아님) + 교과서 근거"),
    "standard_textbook": ("표준 초안 · 미검증", "#b45309", "#fef3c7", "실 CPX 사례 없음 — 표준 교과서 수준 초안(교수 검증 필요)"),
}


def esc(s) -> str:
    return html.escape(str(s))


def load(sym):
    with open(os.path.join(ROOT, "ontology", f"{sym}.yaml"), encoding="utf-8") as f:
        return yaml.safe_load(f)


def disease_rows(data):
    labels = data.get("labels", {})
    srcs = data.get("sources", {})
    rows = []
    for d in data["diseases"]:
        ev = d.get("evidence", {})
        lvl = ev.get("level", "standard_textbook")
        src_refs = [srcs.get(s, {}).get("ref", s) for s in ev.get("sources", [])]
        # YAML 본문은 반드시 esc 경유(md_lite) — 원문에 <,&가 있으면 렌더가 깨진다.
        basis = md_lite(ev.get("basis") or ev.get("note") or "")
        unsourced = ev.get("unsourced", [])
        if unsourced:
            basis += f'  <span class="uns">⚠ 미근거 항목(정직표기): {esc(", ".join(labels.get(u, u) for u in unsourced))}</span>'
        rows.append({
            "label": labels.get(d["id"], d["id"]),
            "role": d.get("role", "differential"),
            "level": lvl,
            "refs": src_refs,
            "basis": basis,
        })
    return rows


def sym_section(sym, data):
    ko = data.get("labels", {}).get(sym, sym)
    rows = disease_rows(data)
    counts = {}
    for r in rows:
        counts[r["level"]] = counts.get(r["level"], 0) + 1
    chips = " ".join(
        f'<span class="chip" style="background:{LEVEL[k][2]};color:{LEVEL[k][1]}">{LEVEL[k][0]}: {v}</span>'
        for k, v in sorted(counts.items())
    )
    trs = ""
    for r in rows:
        nm, col, bg, _ = LEVEL[r["level"]]
        badge = f'<span class="badge" style="background:{bg};color:{col}">{nm}</span>'
        role = '<span class="prim">대표</span> ' if r["role"] == "primary" else ""
        refs = "<br>".join(f"• {md_lite(x)}" for x in r["refs"]) if r["refs"] else '<span class="dash">— (출처 없음)</span>'
        trs += (
            f'<tr><td class="dz">{role}{esc(r["label"])}</td>'
            f'<td>{badge}</td><td class="ref">{refs}</td>'
            f'<td class="basis">{r["basis"]}</td></tr>'
        )
    return f"""
    <h2>{esc(ko)} <span class="cc">({esc(sym)})</span> — 질환 {len(rows)}개</h2>
    <div class="chips">{chips}</div>
    <table>
      <thead><tr><th>질환</th><th>근거 수준</th><th>출처</th><th>근거 / 비고</th></tr></thead>
      <tbody>{trs}</tbody>
    </table>"""


def honest_gaps(datas):
    # 데이터 기반: 표준교과서(미근거) 질환 목록
    unsourced = {}
    for sym, data in datas.items():
        labs = data.get("labels", {})
        us = [labs.get(d["id"], d["id"]) for d in data["diseases"]
              if d.get("evidence", {}).get("level") == "standard_textbook"]
        if us:
            unsourced[labs.get(sym, sym)] = us
    lines = "".join(
        f"<li><b>{esc(k)}</b>: {esc(', '.join(v))}</li>" for k, v in unsourced.items()
    )
    return f"""
    <h2 class="gap">⚠️ 정직한 미완 · 못 한 것 (숨기지 않음)</h2>
    <div class="gapbox">
      <h3>1. 못 함 (막힘)</h3>
      <ul>
        <li><b>공식 감별목록 미확보</b> — <code>기본진료수행지침</code>이 스캔본인데 이 환경에 <b>OCR 도구가 없음</b>(tesseract·pdftotext 부재). → 현재 질환 목록은 <b>제(AI) 판단(표준 교과서 기준)</b>이지 교수/지침의 공식 출제범위가 아님. 확정하려면 지침 OCR 또는 교수 확인 필요.</li>
      </ul>
      <h3>2. 안 함 · 미완</h3>
      <ul>
        <li><b>실 CPX 사례가 없는 질환 (= <code>standard_textbook</code> 등급):</b>
          <ul>{lines}</ul>
          ⚠️ <b>"출처 없음"이 아니라 "실사례 없음"입니다</b> — 이들 다수는 교과서(Harrison 등) 출처가 붙어 있으나,
          <b>부산대 CPX 실사례로는 검증되지 않았습니다.</b> 사례 출처가 아예 없는 항목은 위 질환표에서
          <code>— (출처 없음)</code>으로 따로 표시됩니다. (source-landscape §5에 미사용 후보 사례 목록 있음)</li>
        <li><b>적대검수·검증 현황은 하드코딩하지 않습니다</b> — 위 <b>검수·검증 기록</b> 표가
          <code>docs/verification-log.yaml</code>을 그대로 렌더한 것이며, 그것이 정본입니다.</li>
      </ul>
      <h3>3. 근본 한계 (과대주장 방지)</h3>
      <ul>
        <li>전체가 <b><code>review_status: draft</code></b> — <b>임상 정확성 주장 안 함.</b> 최종 의학 검증 = PI·지도교수 몫.</li>
        <li><b>주증상별 근거 두께가 다름</b> — 복통은 station 직접 실사례가 요로결석뿐이고 나머지는 다른 station(발열·구토 등)에서 끌어옴. 반면 <b>설사 1건·변비 2건</b>은 해당 station 직접 실사례라 상대적으로 두꺼움.</li>
        <li>인용은 <b>실제로 읽은 것</b>만 — 사례가 기재한 참고문헌 + 로컬 Harrison 코퍼스 직독. <b>기억으로 지어낸 인용 없음.</b> 단 Harrison <b>판(edition)이 원본에 미표기</b>라 대외 인용 전 원본 PDF 대조 필요.</li>
      </ul>
    </div>"""


VERIFY_STATUS = {
    "PASS":    ("통과", "#15803d", "#dcfce7"),
    "PARTIAL": ("부분", "#0e7490", "#cffafe"),
    "FAIL":    ("실패", "#b91c1c", "#fee2e2"),
    "BLOCKED": ("막힘 · 미실시", "#b45309", "#fef3c7"),
    "NOT_RUN": ("미실시", "#6b7280", "#f3f4f6"),
}


def md_lite(s) -> str:
    """검수기록 본문용 최소 마크업: esc 후 **굵게** · `코드`만 허용(임의 HTML 주입 차단)."""
    t = esc(s)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t, flags=re.S)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    return t


def verification_section() -> str:
    """docs/verification-log.yaml(정본) → 검수기록 표. 파일 없으면 섹션 자체를 생략."""
    path = os.path.join(ROOT, "docs", "verification-log.yaml")
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as f:
        log = yaml.safe_load(f) or {}

    out = ['<h2>🧪 검수·검증 기록 <span class="cc">정본 = docs/verification-log.yaml (실측한 것만 기재)</span></h2>']
    for run in log.get("runs", []):
        counts = {}
        for c in run.get("checks", []):
            counts[c["status"]] = counts.get(c["status"], 0) + 1
        chips = " ".join(
            f'<span class="chip" style="background:{VERIFY_STATUS[k][2]};color:{VERIFY_STATUS[k][1]}">'
            f'{VERIFY_STATUS[k][0]}: {v}</span>'
            for k, v in counts.items() if k in VERIFY_STATUS
        )
        out.append(
            f'<h3>{esc(run.get("date",""))} · {esc(run.get("scope",""))} '
            f'<span class="cc">— {esc(run.get("by",""))}</span></h3>'
            f'<div class="chips">{chips}</div>'
            '<table><thead><tr><th style="width:22%">검사</th><th style="width:10%">결과</th>'
            '<th style="width:26%">방법</th><th>실측 내용</th></tr></thead><tbody>'
        )
        for c in run.get("checks", []):
            nm, col, bg = VERIFY_STATUS.get(c["status"], (c["status"], "#6b7280", "#f3f4f6"))
            out.append(
                f'<tr><td class="dz">{esc(c.get("name",""))}</td>'
                f'<td><span class="badge" style="background:{bg};color:{col}">{nm}</span></td>'
                f'<td class="ref">{md_lite(c.get("method",""))}</td>'
                f'<td class="basis">{md_lite(c.get("detail",""))}</td></tr>'
            )
        out.append("</tbody></table>")
    return "\n".join(out)


def build():
    datas = {s: load(s) for s in SYMS}
    body = "\n".join(sym_section(s, datas[s]) for s in SYMS)
    # 출처 레지스트리(합본)
    srclines = ""
    for s in SYMS:
        for sid, meta in datas[s].get("sources", {}).items():
            tag = "실사례" if meta.get("type") == "real_cpx_case" else "교과서"
            srclines += f'<li><span class="stag">{tag}</span> <code>{esc(sid)}</code> — {md_lite(meta.get("ref",""))}</li>'
    gaps = honest_gaps(datas)
    legend = " ".join(
        f'<span class="chip" style="background:{bg};color:{col}">{nm}</span> <small>{esc(desc)}</small>'
        for nm, col, bg, desc in LEVEL.values()
    )
    return TEMPLATE.format(body=body, gaps=gaps, sources=srclines, legend=legend,
                           verification=verification_section(),
                           graphlinks="".join(
                               f'<a href="{s}-graph.html">{datas[s].get("labels", {}).get(s, s)} '
                               f'온톨로지 그래프 →</a>' for s in SYMS))


TEMPLATE = """<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CPX 온톨로지 — 근거화 현황 리포트</title>
<style>
  :root{{--fg:#1f2937;--mut:#6b7280;--line:#e5e7eb;--bg:#ffffff;--card:#fafafa}}
  @media(prefers-color-scheme:dark){{:root{{--fg:#e5e7eb;--mut:#9ca3af;--line:#374151;--bg:#0f1420;--card:#161c28}}}}
  *{{box-sizing:border-box}}
  body{{margin:0;font-family:'Malgun Gothic',system-ui,sans-serif;color:var(--fg);background:var(--bg);line-height:1.6}}
  .wrap{{max-width:980px;margin:0 auto;padding:24px 18px 60px}}
  h1{{font-size:22px;margin:0 0 4px}}
  .sub{{color:var(--mut);font-size:13px;margin-bottom:10px}}
  .warn{{background:#fef2f2;border:1px solid #fecaca;color:#b91c1c;padding:10px 14px;border-radius:8px;font-size:13px;font-weight:bold;margin:12px 0 24px}}
  @media(prefers-color-scheme:dark){{.warn{{background:#2a1414;border-color:#7f1d1d;color:#fca5a5}}}}
  h2{{font-size:17px;margin:30px 0 8px;padding-bottom:6px;border-bottom:2px solid var(--line)}}
  h2 .cc{{color:var(--mut);font-weight:normal;font-size:13px}}
  h2.gap{{color:#b45309;border-color:#f59e0b}}
  h3{{font-size:14px;margin:16px 0 6px}}
  .chips{{margin:8px 0 12px}} .chip{{display:inline-block;padding:2px 9px;border-radius:11px;font-size:12px;font-weight:bold;margin:2px 6px 2px 0}}
  table{{width:100%;border-collapse:collapse;font-size:13px;margin:6px 0}}
  th,td{{text-align:left;padding:7px 9px;border-bottom:1px solid var(--line);vertical-align:top}}
  th{{color:var(--mut);font-size:12px;font-weight:600}}
  td.dz{{font-weight:bold;white-space:nowrap}} .prim{{color:#dc2626;font-size:11px;border:1px solid #dc2626;border-radius:4px;padding:0 3px}}
  .badge{{display:inline-block;padding:2px 8px;border-radius:6px;font-size:11px;font-weight:bold;white-space:nowrap}}
  td.ref{{font-size:12px;color:var(--mut);min-width:220px}} td.basis{{font-size:12px}}
  .uns{{display:inline-block;color:#b45309;font-size:11px;margin-top:3px}}
  .dash{{color:var(--mut)}}
  .gapbox{{background:var(--card);border:1px solid #f59e0b;border-radius:10px;padding:6px 18px 14px}}
  ul{{margin:6px 0;padding-left:20px}} li{{margin:4px 0;font-size:13px}}
  code{{background:var(--card);padding:1px 5px;border-radius:4px;font-size:12px;border:1px solid var(--line)}}
  .stag{{display:inline-block;background:var(--card);border:1px solid var(--line);border-radius:5px;padding:0 6px;font-size:11px;color:var(--mut)}}
  .links a{{color:#2563eb;margin-right:16px;font-size:13px}}
  .legend{{font-size:12px;color:var(--mut);margin:8px 0 20px}}
</style></head>
<body><div class="wrap">
  <h1>CPX 온톨로지 — 근거화 현황 리포트</h1>
  <div class="sub">주증상별 감별 온톨로지의 <b>출처·근거</b> + <b>정직한 미완 항목</b> · 생성 = <code>scripts/ontology_report.py</code>(YAML 직독)</div>
  <div class="warn">⚠ review_status: draft — 임상 내용은 교수 검증 전 초안. 의학적 정확성을 주장하지 않음.</div>
  <div class="legend"><b>근거 수준:</b><br>{legend}</div>
  {body}
  <h2>출처 목록 (사례·문헌 — 공개물엔 포인터만, 원문·개인정보 미수록)</h2>
  <ul>{sources}</ul>
  {verification}
  {gaps}
  <h2>그래프 (인터랙티브)</h2>
  <div class="links">{graphlinks}</div>
  <p class="sub" style="margin-top:24px">정본 = <code>ontology/*.yaml</code> · 자료 지형 = <code>docs/source-landscape.md</code> · 설계 = <code>docs/ontology-plan.md</code></p>
</div></body></html>
"""


def main():
    html_out = build()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html_out)
    print(f"wrote {OUT}  ({len(html_out)} bytes)")


if __name__ == "__main__":
    main()
