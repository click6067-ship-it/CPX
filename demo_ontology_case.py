"""온톨로지 → CPX 사례 → 결정론 검증 — **한 장으로 보는 시연**.

무엇을 보여주는가
  ① 온톨로지 카드(질환 1개)가 강제하는 **생성 제약**(필수증상·감별단서·위험징후·체크리스트·공개규칙)
  ② 그 제약으로 만든(또는 기존) **CPX 사례** — SP 대본·현병력·채점표
  ③ `ontology_validator` 의 **6검사 결정론 리포트**(카드가 요구한 것이 사례에 실제로 있는가)
  ④ 각 요소의 **교재 근거**(발현소견 검토표의 인용 — 있으면 연결)

왜 이렇게 만드나
  교수 시연에서 필요한 건 "검수 이력"이 아니라 **한 화면에서 도는 것**이다.
  그래서 LLM 없이도 즉시 돌아가도록 `--case`(기존 사례)를 기본으로 두고,
  키가 있을 때만 `--generate` 로 실제 생성까지 간다.

실행
  # LLM 없이 (즉시 실행 가능)
  PYTHONPATH=src .venv/bin/python demo_ontology_case.py \
      --ontology ontology/diarrhea.yaml --disease ibs_diarrhea --case data/cases/diarrhea_kim.json

  # 생성까지 (GOOGLE_API_KEY 등 필요)
  set -a; source ~/.secrets/api-keys.env; set +a
  PYTHONPATH=src .venv/bin/python demo_ontology_case.py \
      --ontology ontology/diarrhea.yaml --disease ibs_diarrhea --generate

⚠️ 산출물은 `data/working/`(gitignored) — 교재 인용을 포함할 수 있어 공개 저장소에 올리지 않는다.
⚠️ 온톨로지·검토표 모두 `review_status: draft` — 교수 검증 전이며 의학적 정확성을 주장하지 않는다.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("CPX_TRACE_ACK", "0")      # 데모는 외부 트레이싱 안 함

from cpx.models import CpxCase                                    # noqa: E402
from cpx.ontology_validator import load_cards, validate           # noqa: E402

OUT = ROOT / "data" / "working" / "demo"

CHECK_KO = {
    "required_coverage": "필수 증상이 사례에 있는가",
    "red_flags": "위험징후를 체크리스트가 선별하는가",
    "discriminators": "감별 단서가 드러나는가",
    "disclosure": "공개 규칙(과공개 금지)을 지키는가",
    "contradiction": "카드와 모순되는 서술이 없는가",
    "checklist_mapping": "체크리스트가 카드 항목에 대응되는가",
}
STATUS_KO = {"pass": ("통과", "#15803d", "#dcfce7"), "flag": ("검토 필요", "#b45309", "#fef3c7"),
             "fail": ("실패", "#b91c1c", "#fee2e2"), "skip": ("건너뜀", "#6b6b66", "#f1f0ec")}


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


# ── 교재 근거 연결 ────────────────────────────────────────────────────────────
def load_evidence(symptom: str) -> dict[str, list[dict]]:
    """발현소견 검토표(gitignored)에서 질환별 인용을 읽어 온다. 없으면 빈 dict."""
    p = ROOT / "data" / "working" / "findings" / f"{symptom}_findings.json"
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    out = {}
    for card in data["질환목록"]:
        rows = []
        for it in card.get("findings", []) + card.get("conditions", []):
            rows.append({"role": it.get("role", ""), "name": it.get("name") or it.get("value", ""),
                         "quote": it["reference"].get("quote", ""),
                         "src": f"{it['reference'].get('book','')} {it['reference'].get('page','')}".strip()})
        out[card["질환"]] = rows
    return out


def constraint_block(card: dict, labels: dict) -> list[tuple[str, str]]:
    """카드가 강제하는 것 — generator._ontology_constraint 와 같은 소스를 사람이 읽게 편 것."""
    def lab(ids):
        return ", ".join(labels.get(i, i) for i in (ids or []))
    disc = card.get("disclosure") or {}
    rows = [
        ("필수 증상 (환자가 실제로 가지고 있어야)", lab(card.get("required_symptoms"))),
        ("감별 단서 (환자 응답으로 드러나야)", lab(card.get("discriminators"))),
        ("위험징후 (체크리스트가 반드시 물어 선별)", lab(card.get("red_flags"))),
        ("체크리스트 필수 질문", lab(card.get("checklist_items"))),
        ("검사 계획", lab(card.get("tests"))),
        ("환자 교육", lab(card.get("education_items"))),
        ("자발 노출 허용", lab(disc.get("spontaneous"))),
        ("과공개 금지 (물어봐야만 답)", lab(disc.get("disclose_if_asked"))),
    ]
    return [(k, v) for k, v in rows if v]


# ── 렌더 ─────────────────────────────────────────────────────────────────────
CSS = """
:root{--line:#d8d8d2;--ink:#1a1a18;--mute:#6b6b66;--bg:#faf9f6}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 "Noto Serif KR","Malgun Gothic",serif}
.wrap{max-width:1120px;margin:0 auto;padding:40px 26px 80px}
h1{font-size:1.8rem;margin:0 0 6px;letter-spacing:-.02em}
h2{font-size:1.1rem;margin:38px 0 8px;padding-bottom:6px;border-bottom:2px solid var(--ink)}
h3{font-size:.88rem;margin:18px 0 5px;color:var(--mute);letter-spacing:.03em}
.sub{color:var(--mute);font-size:.9rem}
.warn{background:#fff4f4;border:1px solid #e7b7b7;color:#8c2f1f;padding:10px 14px;font-size:.84rem;margin:14px 0}
.flow{display:flex;gap:8px;flex-wrap:wrap;margin:18px 0 6px}
.step{flex:1;min-width:170px;background:#fff;border:1px solid var(--line);padding:11px 13px}
.step b{display:block;font-size:.82rem;margin-bottom:3px}
.step span{font-size:.78rem;color:var(--mute)}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);font-size:.85rem;margin-top:6px}
th{text-align:left;background:#f2f1ec;padding:8px 10px;font-weight:600;font-size:.77rem;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:8px 10px;border-bottom:1px solid #eeede8;vertical-align:top}
.k{color:var(--mute);font-size:.79rem;white-space:nowrap;width:230px}
.q{font-family:Georgia,serif;font-style:italic;color:#333;font-size:.82rem}
.src{color:var(--mute);font-size:.75rem;white-space:nowrap}
.pill{display:inline-block;padding:1px 8px;border-radius:10px;font-size:.75rem;font-weight:700}
.dlg{background:#fff;border:1px solid var(--line);padding:12px 14px;font-size:.86rem}
.dlg .qq{color:#1f5c8c;font-weight:600}
.dlg .aa{margin:2px 0 10px}
.mini{font-size:.78rem;color:var(--mute)}
.ok{color:#15803d;font-weight:700}.no{color:#b91c1c;font-weight:700}
"""


def render(card, labels, case: CpxCase, report, evidence_rows, meta) -> str:
    rep = report.to_dict() if hasattr(report, "to_dict") else report
    checks = rep["checks"]
    ov = STATUS_KO.get(rep["overall"], ("?", "#000", "#eee"))

    # ① 제약
    cons = "".join(f'<tr><td class="k">{esc(k)}</td><td>{esc(v)}</td></tr>' for k, v in constraint_block(card, labels))

    # ② 사례
    dem = case.demographics
    who = f"{getattr(dem,'age','')}세 {getattr(dem,'sex','')}" if dem else ""
    hpi = "".join(f'<tr><td class="k">{esc(h.time_point)}</td><td>{esc(h.detail)}</td></tr>'
                  for h in (case.present_illness or []))
    chk = "".join(f'<tr><td>{i+1}</td>'
                  f'<td class="qq">{esc(c.question_open or c.question_closed or "")}</td>'
                  f'<td>{esc(c.patient_answer)}</td>'
                  f'<td class="mini">{esc(getattr(c.domain, "value", c.domain))}</td></tr>'
                  for i, c in enumerate(case.checklist or []))

    # ③ 6검사
    rows = []
    for key, ck in checks.items():
        st = STATUS_KO.get(ck["status"], ("?", "#000", "#eee"))
        cov = ck.get("positive_coverage")
        covs = f"{cov*100:.0f}%" if isinstance(cov, (int, float)) else "—"
        miss = ", ".join(h.get("label", h.get("id", "")) for h in (ck.get("missing") or [])[:6]) or "—"
        rows.append(f'<tr><td>{esc(CHECK_KO.get(key,key))}</td>'
                    f'<td><span class="pill" style="color:{st[1]};background:{st[2]}">{st[0]}</span></td>'
                    f'<td>{covs}</td><td class="mini">{esc(miss)}</td></tr>')
    checks_html = "".join(rows)

    # ④ 교재 근거
    ev = "".join(f'<tr><td class="k">{esc(r["role"])}</td><td>{esc(r["name"])}</td>'
                 f'<td class="q">{esc(r["quote"][:180])}</td><td class="src">{esc(r["src"])}</td></tr>'
                 for r in evidence_rows[:14])
    ev_html = (f'<table><thead><tr><th>role</th><th>소견</th><th>교재 인용 원문</th><th>출처</th></tr></thead>'
               f'<tbody>{ev}</tbody></table>'
               f'<div class="mini">※ 검토표 전체는 별도 파일. 여기서는 상위 {min(14,len(evidence_rows))}건만 표시.</div>'
               if ev else '<div class="mini">교재 근거 검토표를 찾지 못했습니다(gitignored — 로컬에만 존재).</div>')

    warn = "".join(f"<li>{esc(w)}</li>" for w in rep.get("warnings", []))
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>온톨로지 기반 CPX 사례 생성·검증 시연</title><style>{CSS}</style></head><body><div class="wrap">
<h1>온톨로지 기반 CPX 사례 생성·검증</h1>
<div class="sub">주증상 <b>{esc(meta['symptom_ko'])}</b> · 질환 <b>{esc(rep['disease_label'])}</b>
 · 사례 {esc(case.case_id)} · 생성 {esc(meta['mode'])} · {esc(meta['stamp'])}</div>

<div class="flow">
  <div class="step"><b>① 온톨로지 카드</b><span>질환이 요구하는 필수증상·감별단서·위험징후·공개규칙</span></div>
  <div class="step"><b>② 사례</b><span>카드 제약을 반영한 SP 대본·현병력·채점표</span></div>
  <div class="step"><b>③ 결정론 검증</b><span>카드가 요구한 것이 사례에 실제로 있는지 6검사</span></div>
  <div class="step"><b>④ 교재 근거</b><span>각 소견이 어느 교재 문장에 근거하는지</span></div>
</div>

<div class="warn">⚠️ <b>review_status: {esc(rep['review_status'])} · 지도교수 승인: {'예' if rep['professor_approved'] else '아니오'}</b>
 — 온톨로지와 검토표 모두 교수 검증 전 초안입니다. 이 화면은 <b>파이프라인이 도는 것</b>을 보이기 위한 것이며
 의학적 정확성을 주장하지 않습니다. {esc(rep.get('disclaimer',''))}</div>

<h2>① 온톨로지 카드가 강제하는 것</h2>
<div class="mini">이 표의 항목들이 생성 프롬프트에 제약으로 주입되고, ③에서 같은 항목으로 검증됩니다.</div>
<table><tbody>{cons}</tbody></table>

<h2>② 사례</h2>
<h3>환자</h3>
<table><tbody>
<tr><td class="k">제목</td><td>{esc(case.title)}</td></tr>
<tr><td class="k">주증상 / 진단</td><td>{esc(case.chief_complaint)} / {esc(case.diagnosis)}</td></tr>
<tr><td class="k">인적사항</td><td>{esc(who)}</td></tr>
<tr><td class="k">수험생 과제</td><td>{esc(case.examinee_task)}</td></tr>
</tbody></table>
<h3>현병력 (SP 대본 근거)</h3>
<table><tbody>{hpi or '<tr><td class="mini">항목 없음</td></tr>'}</tbody></table>
<h3>채점표 ({len(case.checklist or [])}항목)</h3>
<table><thead><tr><th>#</th><th>의사 질문</th><th>환자 답변</th><th>영역</th></tr></thead><tbody>{chk}</tbody></table>

<h2>③ 결정론 검증 — 종합 <span class="pill" style="color:{ov[1]};background:{ov[2]}">{ov[0]}</span></h2>
<div class="mini">LLM 판단이 아니라 <b>규칙 기반</b>입니다. 같은 입력이면 항상 같은 결과가 나옵니다.</div>
<table><thead><tr><th>검사</th><th>결과</th><th>충족률</th><th>빠진 항목</th></tr></thead><tbody>{checks_html}</tbody></table>
{f'<h3>경고</h3><div class="dlg"><ul>{warn}</ul></div>' if warn else ''}

<h2>④ 교재 근거</h2>
<div class="mini">이 질환의 소견들이 어느 교재 문장에 근거하는지 — 인용은 기계 대조를 통과한 것만 실립니다.</div>
{ev_html}
</div></body></html>"""


def render_compare(card, labels, pairs, meta) -> str:
    """온톨로지 제약 유무 비교 — 이 시스템이 왜 필요한지 한 화면에 보이는 것."""
    cons = "".join(f'<tr><td class="k">{esc(k)}</td><td>{esc(v)}</td></tr>'
                   for k, v in constraint_block(card, labels))
    head = "".join(f"<th>{esc(t)}</th>" for t, _, _ in pairs)
    rows = []
    for key, ko in CHECK_KO.items():
        tds = []
        for _, _, rep in pairs:
            ck = rep["checks"].get(key, {})
            st = STATUS_KO.get(ck.get("status"), ("—", "#000", "#eee"))
            cov = ck.get("positive_coverage")
            covs = f' <b>{cov*100:.0f}%</b>' if isinstance(cov, (int, float)) else ""
            tds.append(f'<td><span class="pill" style="color:{st[1]};background:{st[2]}">{st[0]}</span>{covs}</td>')
        rows.append(f"<tr><td>{esc(ko)}</td>{''.join(tds)}</tr>")
    ovs = "".join(f'<td><span class="pill" style="color:{STATUS_KO[r["overall"]][1]};'
                  f'background:{STATUS_KO[r["overall"]][2]}">{STATUS_KO[r["overall"]][0]}</span></td>'
                  for _, _, r in pairs)
    cases = "".join(
        f'<h3>{esc(t)} — {esc(c.title)}</h3><table><tbody>'
        f'<tr><td class="k">진단</td><td>{esc(c.diagnosis)}</td></tr>'
        f'<tr><td class="k">현병력 항목수</td><td>{len(c.present_illness or [])}</td></tr>'
        f'<tr><td class="k">채점표 항목수</td><td>{len(c.checklist or [])}</td></tr>'
        + "".join(f'<tr><td class="k">{esc(h.time_point)}</td><td>{esc(h.detail)}</td></tr>'
                  for h in (c.present_illness or [])[:8])
        + '</tbody></table>' for t, c, _ in pairs)
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>온톨로지 제약이 사례 생성에 주는 차이</title><style>{CSS}</style></head><body><div class="wrap">
<h1>온톨로지 제약이 사례 생성에 주는 차이</h1>
<div class="sub">주증상 <b>{esc(meta['symptom_ko'])}</b> · 질환 <b>{esc(labels.get(card['id'],card['id']))}</b> · {esc(meta['stamp'])}</div>

<div class="flow">
  <div class="step"><b>① 온톨로지 카드</b><span>질환이 요구하는 필수증상·감별단서·위험징후</span></div>
  <div class="step"><b>② 두 가지로 생성</b><span>제약 없이(baseline) vs 카드 제약으로(scaffolded)</span></div>
  <div class="step"><b>③ 같은 잣대로 검증</b><span>카드가 요구한 것이 실제로 들어갔는가 — 규칙 기반</span></div>
</div>

<div class="warn">⚠️ <b>n=1 일화적 기계 데모입니다.</b> 통계적 개선·임상 타당성·교수 수준 품질을 주장하지 않습니다.
 온톨로지는 <b>review_status: draft</b>(교수 검증 전)이며, 이 화면은 <b>파이프라인이 실제로 도는 것</b>을 보이기 위한 것입니다.</div>

<h2>① 온톨로지 카드가 강제하는 것</h2>
<table><tbody>{cons}</tbody></table>

<h2>③ 검증 결과 — 같은 잣대, 다른 결과</h2>
<div class="mini">LLM 판단이 아니라 <b>규칙 기반</b>입니다. 같은 입력이면 항상 같은 결과가 나옵니다.</div>
<table><thead><tr><th>검사</th>{head}</tr></thead><tbody>
{''.join(rows)}
<tr><td><b>종합</b></td>{ovs}</tr>
</tbody></table>

<h2>② 생성된 사례</h2>
{cases}
</div></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ontology", default="ontology/diarrhea.yaml")
    ap.add_argument("--disease", default="ibs_diarrhea")
    ap.add_argument("--case", help="기존 사례 JSON (LLM 없이 즉시 실행)")
    ap.add_argument("--generate", action="store_true", help="LLM으로 새로 생성 (API 키 필요)")
    ap.add_argument("--compare", nargs=2, metavar=("BASELINE","SCAFFOLDED"),
                    help="온톨로지 제약 유무 두 사례를 나란히 검증(핵심 시연)")
    ap.add_argument("--model", default=os.environ.get("GEN_MODEL", "gemini-2.5-flash"))
    ap.add_argument("--list", action="store_true", help="이 온톨로지의 질환 목록만 출력")
    a = ap.parse_args()

    diseases, labels = load_cards(a.ontology)
    if a.list:
        print(f"{a.ontology} — 질환 {len(diseases)}개")
        for d in diseases:
            print(f"   {d['id']:38s} {labels.get(d['id'],'')}")
        return 0
    try:
        card = next(d for d in diseases if d["id"] == a.disease)
    except StopIteration:
        print(f"질환 id '{a.disease}' 없음. 가능한 값:")
        for d in diseases:
            print(f"   {d['id']:38s} {labels.get(d['id'],'')}")
        return 1

    symptom = Path(a.ontology).stem
    symptom_ko = {"diarrhea": "설사", "constipation": "변비",
                  "chest_pain": "흉통", "abdominal_pain": "복통"}.get(symptom, symptom)
    label = labels.get(card["id"], card["id"])

    if a.compare:
        from datetime import datetime
        pairs = []
        for tag, path in zip(("제약 없음 (baseline)", "온톨로지 제약 (scaffolded)"), a.compare):
            c = CpxCase(**json.loads(Path(path).read_text(encoding="utf-8")))
            rep = validate(c, a.ontology, disease_id=card["id"]).to_dict()
            pairs.append((tag, c, rep))
            print(f"{tag}: {rep['overall']}")
            for k, v in rep["checks"].items():
                cov = v.get("positive_coverage")
                print(f"   {CHECK_KO.get(k,k):32s} {v['status']:5s} {'' if cov is None else f'{cov*100:.0f}%'}")
        meta = {"symptom_ko": symptom_ko, "stamp": datetime.now().strftime("%Y-%m-%d %H:%M")}
        OUT.mkdir(parents=True, exist_ok=True)
        out = OUT / f"{symptom}_{card['id']}_compare.html"
        out.write_text(render_compare(card, labels, pairs, meta), encoding="utf-8")
        print(f"\n→ {out}")
        return 0

    if a.generate:
        need = {"gemini": "GOOGLE_API_KEY", "gpt": "OPENAI_API_KEY", "claude": "ANTHROPIC_API_KEY"}
        key = next((v for k, v in need.items() if a.model.startswith(k)), "GOOGLE_API_KEY")
        if not os.environ.get(key):
            print(f"❌ {key} 가 없습니다. 키를 주입한 뒤 다시 실행하세요:\n"
                  f"   set -a; source ~/.secrets/api-keys.env; set +a\n"
                  f"   PYTHONPATH=src .venv/bin/python demo_ontology_case.py "
                  f"--ontology {a.ontology} --disease {a.disease} --generate\n"
                  f"(키 없이 볼 수 있는 것: --list · --case · --compare)")
            return 2
        from cpx.agents import generator
        print(f"① 생성 중 — {symptom_ko} / {label} (model={a.model}) …")
        case, log = generator.generate(symptom_ko, label, model=a.model, rounds=1,
                                       clinical=True, ontology=(card, labels))
        for l in log:
            print("   ", l)
        mode = f"LLM 생성 ({a.model})"
    else:
        src = a.case or f"data/cases/{symptom}_kim.json"
        if not Path(src).exists():
            print(f"사례 파일 없음: {src}\n  --case 로 지정하거나 --generate 로 생성하세요.")
            return 1
        case = CpxCase(**json.loads(Path(src).read_text(encoding="utf-8")))
        mode = f"기존 사례 ({Path(src).name})"

    print(f"③ 검증 중 — {label}")
    report = validate(case, a.ontology, disease_id=card["id"])
    rep = report.to_dict()
    for k, v in rep["checks"].items():
        cov = v.get("positive_coverage")
        print(f"   {CHECK_KO.get(k,k):32s} {v['status']:5s} "
              f"{'' if cov is None else f'{cov*100:.0f}%'}")
    print(f"   → 종합: {rep['overall']}")

    evidence = load_evidence(symptom)
    ev_rows = evidence.get(label, [])
    if not ev_rows:                     # 라벨이 다르면 앞부분 일치로 재시도
        ev_rows = next((v for k, v in evidence.items() if k.startswith(label[:8])), [])

    from datetime import datetime
    meta = {"symptom_ko": symptom_ko, "mode": mode,
            "stamp": datetime.now().strftime("%Y-%m-%d %H:%M")}
    OUT.mkdir(parents=True, exist_ok=True)
    out = OUT / f"{symptom}_{card['id']}.html"
    out.write_text(render(card, labels, case, report, ev_rows, meta), encoding="utf-8")
    (OUT / f"{symptom}_{card['id']}_report.json").write_text(
        json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n④ 산출 → {out}")
    print(f"   교재 근거 {len(ev_rows)}건 연결")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
