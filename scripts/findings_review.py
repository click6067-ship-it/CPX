"""발현소견(Finding)·조건(Condition) 교재근거 검토표 — 인용 기계대조 + HTML 렌더.

입력  : data/working/findings/<name>.json   (gitignored — 교재 원문 인용 포함, 저작권상 커밋 금지)
출력  : data/working/findings/<name>.html   (동일 사유로 gitignored)

핵심은 **인용 기계대조**다. quote가 교재 원문에 실제로 없으면 `_quote_verified=false`로 찍혀
표에 ✗로 뜨고, 채택 전 확인 대상이 된다. 사람이 옮겨 적은 인용을 믿지 않기 위한 장치.

대조 규칙(복통판 merge_findings.py 로직 이식):
  - `[[pN]]` 페이지 마커가 문장 중간에 끼므로 제거
  - PDF 추출물의 **소프트하이픈(U+00AD)**·제로폭 문자 제거
  - 행말 절음('abdomi- nal')과 **행 바꿈 지점의 단어 중간 공백**('com monly') 때문에
    공백·하이픈을 전부 지운 키로 비교한다(100자 인용에서 우연 일치는 사실상 없음)

사용:  python scripts/findings_review.py data/working/findings/diarrhea_findings.json
"""
from __future__ import annotations
import html
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

TB = Path(os.environ.get(
    "TEXTBOOK_ROOT",
    Path.home() / "ghq/github.com/click6067-ship-it/cpx-agent/data/raw/textbook",
))

ROLE_KO = {"required": "필수", "discriminator": "구별", "supporting": "동반", "red_flag": "경고"}
ROLE_DESC = {"required": "그 질환이면 거의 항상 있는 핵심 소견",
             "discriminator": "경쟁 질환과 구별해 주는 소견",
             "supporting": "흔히 동반되나 비특이적",
             "red_flag": "응급·중증을 시사"}
ROLE_COLOR = {"required": "#8c2f1f", "discriminator": "#1f5c8c",
              "supporting": "#5c5c56", "red_flag": "#a8330a"}

COND_KO = {"age_group": "연령대", "sex_group": "성별", "occupation": "직업",
           "exposure": "노출", "lifestyle_factor": "생활습관", "risk_factor": "위험인자",
           "past_history": "과거력", "medication_history": "복용약", "family_history": "가족력",
           "social_history": "사회력", "trauma_history": "외상력",
           "menstrual_history": "월경력", "obstetric_history": "임신·출산력"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    s = re.sub(r"[­​-‍﻿]", "", s)
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = re.sub(r"[‐-―]", "-", s)
    s = re.sub(r"\[\[p\d+\]\]", " ", s)
    s = re.sub(r"\s+", " ", s).strip().lower()
    return re.sub(r"- ", "", s)


def squash(s: str) -> str:
    return re.sub(r"[\s-]+", "", norm(s))


_corpus: dict[str, str] = {}


def corpus() -> dict[str, str]:
    if not _corpus:
        if not TB.exists():
            sys.exit(f"교재 코퍼스 없음: {TB} (TEXTBOOK_ROOT로 지정)")
        for p in sorted(TB.rglob("*")):
            if p.suffix.lower() in (".md", ".txt"):
                _corpus[str(p.relative_to(TB))] = squash(p.read_text(encoding="utf-8", errors="ignore"))
    return _corpus


def verify(quote: str) -> tuple[bool, str]:
    key = squash(quote)
    if len(key) < 25:
        return False, "인용이 너무 짧아 대조 불가(25자 미만)"
    for rel, body in corpus().items():
        if key in body:
            return True, f"일치 @{rel}"
    return False, "교재에서 못 찾음"


BOOK_LABEL = [("harrison/PART2", "Harrison (PART2)"), ("harrison/PART10", "Harrison (PART10)"),
              ("harrison/PART9", "Harrison (PART9)"), ("harrison/PART5", "Harrison (PART5)"),
              ("harrison/PART4", "Harrison (PART4)"), ("harrison/PART12", "Harrison (PART12)"),
              ("harrison/PART13", "Harrison (PART13)"), ("Sabiston", "Sabiston 19th"),
              ("Schwartz", "Schwartz"), ("Rosen", "Rosen 8th"), ("Tintinalli", "Tintinalli 8th"),
              ("Bates", "Bates"), ("Robbins", "Robbins"), ("InternalMed_Harrison", "Harrison IM")]

_raw: dict[str, str] = {}


def resolve(quote: str):
    """인용문이 실제로 있는 파일과 **직전 `[[pN]]` 마커**를 찾아 (book, page) 반환.

    사람이 페이지를 옮겨 적으면 반드시 틀린다 → 기계가 원문 위치에서 직접 딴다.
    페이지 마커가 없는 교재(txt)는 page=""로 둔다.
    """
    if not _raw:
        for p in sorted(TB.rglob("*")):
            if p.suffix.lower() in (".md", ".txt"):
                _raw[str(p.relative_to(TB))] = p.read_text(encoding="utf-8", errors="ignore")
    key = squash(quote)
    # 페이지 마커가 있는 파일을 먼저 본다. 통본(InternalMed_Harrison.txt)은 마커가 없어
    # 먼저 매칭되면 page가 빈 채로 확정돼 인용의 재현성이 떨어진다.
    order = sorted(corpus(), key=lambda r: (0 if "[[p" in _raw.get(r, "") else 1, r))
    for rel in order:
        body = corpus()[rel]
        i = body.find(key)
        if i < 0:
            continue
        label = next((lab for frag, lab in BOOK_LABEL if frag in rel), Path(rel).stem[:24])
        # squash 인덱스 → 원문 인덱스 복원: 앞에서부터 비공백 문자 i개 지점
        raw = _raw[rel]
        cnt, pos = 0, 0
        for pos, ch in enumerate(raw):
            if not re.match(r"[\s-]", ch):
                cnt += 1
            if cnt > i:
                break
        page = ""
        for m in re.finditer(r"\[\[p(\d+)\]\]", raw[:pos]):
            page = "p" + m.group(1)
        return label, page
    return "", ""


def esc(s) -> str:
    return html.escape(str(s or ""))


CSS = """
:root{--line:#d8d8d2;--ink:#1a1a18;--mute:#6b6b66;--bg:#faf9f6}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.65 "Noto Serif KR","Malgun Gothic",serif}
.wrap{max-width:1180px;margin:0 auto;padding:44px 26px 80px}
h1{font-size:1.85rem;margin:0 0 6px;letter-spacing:-.02em}
.sub{color:var(--mute);font-size:.9rem;margin-bottom:6px}
.warn{background:#fff4f4;border:1px solid #e7b7b7;color:#8c2f1f;padding:10px 14px;font-size:.84rem;margin:14px 0}
.legend{display:flex;gap:16px;flex-wrap:wrap;margin:20px 0 30px;padding:13px 15px;background:#fff;
 border:1px solid var(--line);font-size:.82rem}
.legend div{display:flex;align-items:center;gap:6px}
.dot{width:9px;height:9px;border-radius:50%;display:inline-block}
h2{font-size:1.18rem;margin:40px 0 4px;padding-bottom:6px;border-bottom:2px solid var(--ink)}
h3{font-size:.9rem;margin:20px 0 5px;color:var(--mute);letter-spacing:.03em}
.meta{color:var(--mute);font-size:.79rem;margin-bottom:10px}
table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line);font-size:.85rem}
th{text-align:left;background:#f2f1ec;padding:8px 10px;font-weight:600;font-size:.77rem;
 border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:8px 10px;border-bottom:1px solid #eeede8;vertical-align:top}
.ax{color:var(--mute);font-family:ui-monospace,monospace;font-size:.75rem;white-space:nowrap}
.role{font-weight:600;font-size:.78rem;white-space:nowrap}
.q{font-family:Georgia,serif;font-style:italic;color:#333;font-size:.83rem}
.src{color:var(--mute);font-size:.76rem;white-space:nowrap}
.ok{color:#15803d;font-weight:700}.no{color:#b91c1c;font-weight:700}
.na{background:#fff;border:1px solid var(--line);padding:9px 12px;font-size:.8rem;color:var(--mute);margin-top:6px}
"""


def rows_html(items, kind):
    out = []
    for it in items:
        ref = it.get("reference", {})
        ok = it.get("_quote_verified")
        if kind == "finding":
            ax, nm = it.get("feature", ""), it.get("name", "")
        else:
            ax, nm = COND_KO.get(it.get("condition", ""), it.get("condition", "")), it.get("value", "")
        role = it.get("role", "")
        out.append(
            f'<tr><td class="ax">{esc(ax)}</td><td>{esc(nm)}</td>'
            f'<td class="role" style="color:{ROLE_COLOR.get(role,"#555")}">{esc(ROLE_KO.get(role, role))}</td>'
            f'<td class="q">{esc(ref.get("quote",""))}</td>'
            f'<td class="src">{esc(ref.get("book",""))} {esc(ref.get("page",""))}</td>'
            f'<td class="{"ok" if ok else "no"}">{"✓" if ok else "✗"}</td></tr>'
        )
    return "".join(out)


def build(data: dict) -> str:
    secs = []
    nf = nfv = nc = ncv = 0
    for d in data["질환목록"]:
        fs, cs = d.get("findings", []), d.get("conditions", [])
        nf += len(fs); nfv += sum(1 for f in fs if f.get("_quote_verified"))
        nc += len(cs); ncv += sum(1 for c in cs if c.get("_quote_verified"))
        na = d.get("해당없음", []) + d.get("해당없음_condition", [])
        na_html = ""
        if na:
            lis = "".join(f'<li><b>{esc(x.get("feature") or x.get("condition"))}</b> — {esc(x.get("이유"))}</li>'
                          for x in na)
            na_html = f'<div class="na"><b>해당없음(근거 못 찾음 — 추측으로 채우지 않음)</b><ul>{lis}</ul></div>'
        secs.append(
            f'<h2>{esc(d["질환"])}</h2>'
            f'<div class="meta">소견 {len(fs)}개 · 조건 {len(cs)}개 · 출처 {esc(", ".join(d.get("출처파일", [])))}</div>'
            f'<h3>발현소견 (Finding)</h3>'
            f'<table><thead><tr><th>축</th><th>소견</th><th>role</th><th>교재 인용 원문</th><th>출처</th><th>대조</th></tr></thead>'
            f'<tbody>{rows_html(fs, "finding")}</tbody></table>'
            + (f'<h3>조건 (Enabling Condition)</h3>'
               f'<table><thead><tr><th>축</th><th>조건</th><th>role</th><th>교재 인용 원문</th><th>출처</th><th>대조</th></tr></thead>'
               f'<tbody>{rows_html(cs, "condition")}</tbody></table>' if cs else "")
            + na_html
        )
    legend = "".join(
        f'<div><span class="dot" style="background:{ROLE_COLOR[k]}"></span><b>{v}</b> {ROLE_DESC[k]}</div>'
        for k, v in ROLE_KO.items())
    pct = lambda a, b: f"{a}/{b}" + (f" ({round(a/b*100)}%)" if b else "")
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(data.get("제목","발현소견 교재근거 검토표"))}</title><style>{CSS}</style></head><body><div class="wrap">
<h1>{esc(data.get("제목","발현소견(Finding)·조건(Condition) 교재 근거 검토표"))}</h1>
<div class="sub">질환 {len(data["질환목록"])}개 · 소견 {nf}개(인용대조 {pct(nfv,nf)}) · 조건 {nc}개(인용대조 {pct(ncv,nc)}) · 생성 {esc(data.get("생성일",""))}</div>
<div class="sub">각 항목이 <b>교재 원문에 실제로 있는 문장</b>에 근거하는지 기계 대조한 결과를 함께 표시합니다.
<b>✗</b>는 근거를 확인하지 못한 것이므로 채택 전 확인이 필요합니다.</div>
<div class="warn">⚠ review_status: draft — 임상 내용은 교수 검증 전 초안. 교재 원문 인용을 포함하므로 <b>공개 저장소 커밋 금지</b>(저작권).</div>
<div class="legend">{legend}</div>
{"".join(secs)}
</div></body></html>"""


def main():
    src = Path(sys.argv[1])
    data = json.loads(src.read_text(encoding="utf-8"))
    for d in data["질환목록"]:
        for it in d.get("findings", []) + d.get("conditions", []):
            ref = it.setdefault("reference", {})
            ok, note = verify(ref.get("quote", ""))
            it["_quote_verified"] = ok
            it["_quote_note"] = note
            if ok:  # book·page는 항상 기계가 원문 위치에서 다시 딴다(사람 입력 신뢰 안 함)
                book, page = resolve(ref["quote"])
                ref["book"], ref["page"] = book, page
    nf = sum(len(d.get("findings", [])) for d in data["질환목록"])
    nfv = sum(1 for d in data["질환목록"] for f in d.get("findings", []) if f["_quote_verified"])
    nc = sum(len(d.get("conditions", [])) for d in data["질환목록"])
    ncv = sum(1 for d in data["질환목록"] for c in d.get("conditions", []) if c["_quote_verified"])
    src.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    out = src.with_suffix(".html")
    out.write_text(build(data), encoding="utf-8")
    print(f"소견 {nfv}/{nf} · 조건 {ncv}/{nc} 인용대조 통과 → {out}")
    for d in data["질환목록"]:
        for it in d.get("findings", []) + d.get("conditions", []):
            if not it["_quote_verified"]:
                print(f"  ✗ {d['질환']} | {it.get('name') or it.get('value')} | {it['_quote_note']}")


if __name__ == "__main__":
    main()
