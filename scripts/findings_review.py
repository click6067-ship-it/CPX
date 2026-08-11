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

# ── 발현소견이 *아닌* 항목의 구분 ──
# Codex 임상타당성 검수(2026-08-11, MAJOR 94건)의 뿌리 = 검사·치료·감별진단·역학 문장이
# findings의 required/discriminator로 섞여 들어가 role 체계가 무너진 것. 지우지 않고
# **별도 축으로 분리**한다 — 교재 근거로서는 가치가 있으나 '발현소견'은 아니기 때문.
KIND_KO = {"workup": "진단검사", "management": "치료·관리", "differential": "감별진단",
           "epidemiology": "역학·빈도", "definition": "용어 정의", "mechanism": "기전 설명",
           "sequela": "후유증", "normal_finding": "정상 대조소견", "history_taking": "병력청취"}

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


def search_order() -> list[str]:
    """페이지 마커가 있는 파일 우선. verify()·resolve()가 **같은 파일**을 고르게 하는 단일 순서.

    (예전엔 verify()는 알파벳순, resolve()는 마커 우선이라 대조 note와 인용 출처가
     서로 다른 파일을 가리킬 수 있었다 — 같은 문장이 통본과 분책에 모두 실려 있기 때문.)
    """
    load_raw()
    return sorted(corpus(), key=lambda r: (0 if "[[p" in _raw.get(r, "") else 1, r))


def verify(quote: str) -> tuple[bool, str]:
    key = squash(quote)
    if len(key) < 25:
        return False, "인용이 너무 짧아 대조 불가(25자 미만)"
    for rel in search_order():
        if key in corpus()[rel]:
            return True, f"일치 @{rel}"
    return False, "교재에서 못 찾음"


BOOK_LABEL = [("harrison/PART2", "Harrison (PART2)"), ("harrison/PART10", "Harrison (PART10)"),
              ("harrison/PART9", "Harrison (PART9)"), ("harrison/PART5", "Harrison (PART5)"),
              ("harrison/PART4", "Harrison (PART4)"), ("harrison/PART12", "Harrison (PART12)"),
              ("harrison/PART13", "Harrison (PART13)"), ("Sabiston", "Sabiston 19th"),
              ("Schwartz", "Schwartz"), ("Rosen", "Rosen 8th"), ("Tintinalli", "Tintinalli 8th"),
              ("Bates", "Bates"), ("Robbins", "Robbins"), ("InternalMed_Harrison", "Harrison IM")]

_raw: dict[str, str] = {}
_pageidx: dict[str, list[tuple[int, str]]] = {}


def load_raw() -> dict[str, str]:
    if not _raw:
        for p in sorted(TB.rglob("*")):
            if p.suffix.lower() in (".md", ".txt"):
                _raw[str(p.relative_to(TB))] = p.read_text(encoding="utf-8", errors="ignore")
    return _raw


def page_index(rel: str) -> list[tuple[int, str]]:
    """파일별 `[[pN]]` 마커의 **squash 좌표** 목록 [(squash상 위치, 페이지번호)].

    squash()는 공백·하이픈·페이지마커를 전부 지우므로 `squash(a+b) == squash(a)+squash(b)`가
    성립한다(문자 단위 변환만 남음). 그래서 마커 사이 구간을 순서대로 squash해 길이를 누적하면
    각 마커가 squash 코퍼스의 어느 좌표에 놓이는지 **오차 없이** 얻는다.

    ⚠️ 예전 구현은 squash 인덱스를 원문 인덱스로 되돌릴 때 `[[pN]]` 마커의 글자까지 세었다.
       마커는 squash 코퍼스엔 없으므로 마커 1개당 약 7자씩 오차가 누적됐고(Tintinalli 1124번째
       마커에서 약 7,900자 ≈ 2페이지), 뒤쪽 페이지일수록 **인용 페이지가 앞으로 밀려 찍혔다.**
    """
    if rel not in _pageidx:
        raw = _raw[rel]
        idx, prev, cum = [], 0, 0
        for m in re.finditer(r"\[\[p(\d+)\]\]", raw):
            cum += len(squash(raw[prev:m.start()]))
            idx.append((cum, m.group(1)))
            prev = m.start()
        _pageidx[rel] = idx
    return _pageidx[rel]


def resolve(quote: str):
    """인용문이 실제로 있는 파일과 **직전 `[[pN]]` 마커**를 찾아 (book, page) 반환.

    사람이 페이지를 옮겨 적으면 반드시 틀린다 → 기계가 원문 위치에서 직접 딴다.
    페이지 마커가 없는 교재(txt)는 page=""로 둔다.
    """
    key = squash(quote)
    # 페이지 마커가 있는 파일을 먼저 본다. 통본(InternalMed_Harrison.txt)은 마커가 없어
    # 먼저 매칭되면 page가 빈 채로 확정돼 인용의 재현성이 떨어진다.
    for rel in search_order():
        body = corpus()[rel]
        i = body.find(key)
        if i < 0:
            continue
        label = next((lab for frag, lab in BOOK_LABEL if frag in rel), Path(rel).stem[:24])
        page = ""
        for cum, num in page_index(rel):
            if cum > i:
                break
            page = "p" + num
        return label, page
    return "", ""


SENT_END = re.compile(r"[.!?](?=\s|$)")
HEAD_CAP = 90   # 머리쪽 문장 확장 허용 폭(자). 넘으면 단어 경계까지만 — 앞 문단 끌어오기 방지


def locate_raw(quote: str, rel: str):
    """원문(raw) 안에서 인용의 (시작, 끝) 오프셋. 공백·행말 절음·페이지마커를 건너뛰며 맞춘다."""
    chars = [c for c in norm(quote) if not re.match(r"[\s-]", c)]
    if len(chars) < 20:
        return None
    gap = r"(?:\s|-|\[\[p\d+\]\]|­)*"
    rx = re.compile(gap.join(re.escape(c) for c in chars), re.I)
    m = rx.search(_raw[rel])
    return (m.start(), m.end()) if m else None


def snap_to_sentence(quote: str, window: int = 220) -> str:
    """**단어 중간에서 잘린** 인용만 온전한 경계까지 되돌린다.

    'ience a sudden onset…'(=experience), 'ld be formally evaluated'(=should) 처럼 잘린 인용은
    기계 대조는 통과해도 교수가 읽을 표에서는 깨져 보이고 그대로 재인용할 수도 없다.

    ⚠️ **멀쩡한 인용은 절대 건드리지 않는다.** 처음에 모든 인용을 문장 경계로 넓혔더니,
    표(table)에서 딴 인용이 바로 앞 본문 문장을 끌어와 오히려 더 나빠졌다
    (예: Shigella 표 인용 앞에 "The World Health Organization recommends…"가 붙음).
    그래서 '원문에서 앞/뒤 글자가 실제로 이어지는가'로만 판단하고, 문장부호가 window 안에
    없으면 **단어 경계까지만** 넓힌다.
    """
    rel = next((r for r in search_order() if squash(quote) in corpus()[r]), None)
    if not rel:
        return quote
    pos = locate_raw(quote, rel)
    if not pos:
        return quote
    raw, (s, e) = _raw[rel], pos
    cut_head = s > 0 and raw[s - 1].isalnum()          # 앞 글자가 이어짐 = 단어 중간 절단
    cut_tail = e < len(raw) and raw[e].isalnum()
    if not (cut_head or cut_tail):
        return quote
    if cut_head:
        left = raw[max(0, s - window):s]
        m = list(SENT_END.finditer(left))
        # 문장 시작까지가 너무 멀면(제목·앞 문장을 통째로 끌어옴) 단어 경계까지만 되살린다.
        if m and len(left) - m[-1].end() <= HEAD_CAP:
            s -= len(left) - m[-1].end()
        else:
            while s > 0 and raw[s - 1].isalnum():
                s -= 1
    if cut_tail:
        right = raw[e:e + window]
        if (m := SENT_END.search(right)):
            e += m.end()
        else:
            while e < len(raw) and raw[e].isalnum():
                e += 1
    out = re.sub(r"\[\[p\d+\]\]", " ", raw[s:e])
    out = unicodedata.normalize("NFKC", out)
    out = re.sub(r"[­​-‍﻿]", "", out)
    out = re.sub(r"(\w)- (\w)", r"\1\2", out)          # 행말 절음 복원
    return re.sub(r"\s+", " ", out).strip()


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
.kind{color:#4a5a3f;font-size:.76rem;white-space:nowrap;font-weight:600}
.cav{color:#8c2f1f;font-size:.76rem;margin-top:3px}
h3.sep{color:#4a5a3f}
"""


def ref_rows(items):
    """참고항목(발현소견이 아닌 것) 표의 행."""
    out = []
    for it in items:
        ref = it.get("reference", {})
        ok = it.get("_quote_verified")
        note = f'<div class="cav">⚠ {esc(it["주의"])}</div>' if it.get("주의") else ""
        out.append(
            f'<tr><td class="kind">{esc(KIND_KO.get(it.get("kind"), it.get("kind")))}</td>'
            f'<td>{esc(it.get("name", ""))}{note}</td>'
            f'<td class="q">{esc(ref.get("quote", ""))}</td>'
            f'<td class="src">{esc(ref.get("book", ""))} {esc(ref.get("page", ""))}</td>'
            f'<td class="{"ok" if ok else "no"}">{"✓" if ok else "✗"}</td></tr>'
        )
    return "".join(out)


def rows_html(items, kind):
    out = []
    for it in items:
        ref = it.get("reference", {})
        ok = it.get("_quote_verified")
        if kind == "finding":
            ax, nm = it.get("feature", ""), it.get("name", "")
        else:
            cid = it.get("condition", "")
            ax, nm = f'{COND_KO.get(cid, cid)} <span style="opacity:.55">{cid}</span>', it.get("value", "")
        role = it.get("role", "")
        note = f'<div class="cav">⚠ {esc(it["주의"])}</div>' if it.get("주의") else ""
        out.append(
            f'<tr><td class="ax">{ax if kind=="condition" else esc(ax)}</td><td>{esc(nm)}{note}</td>'
            f'<td class="role" style="color:{ROLE_COLOR.get(role,"#555")}">{esc(ROLE_KO.get(role, role))}</td>'
            f'<td class="q">{esc(ref.get("quote",""))}</td>'
            f'<td class="src">{esc(ref.get("book",""))} {esc(ref.get("page",""))}</td>'
            f'<td class="{"ok" if ok else "no"}">{"✓" if ok else "✗"}</td></tr>'
        )
    return "".join(out)


def build(data: dict) -> str:
    secs = []
    nf = nfv = nc = ncv = nr = nrv = 0
    for d in data["질환목록"]:
        fs, cs, rs = d.get("findings", []), d.get("conditions", []), d.get("참고항목", [])
        nf += len(fs); nfv += sum(1 for f in fs if f.get("_quote_verified"))
        nc += len(cs); ncv += sum(1 for c in cs if c.get("_quote_verified"))
        nr += len(rs); nrv += sum(1 for r in rs if r.get("_quote_verified"))
        na = d.get("해당없음", []) + d.get("해당없음_condition", [])
        na_html = ""
        if na:
            lis = "".join(f'<li><b>{esc(x.get("feature") or x.get("condition"))}</b> — {esc(x.get("이유"))}</li>'
                          for x in na)
            na_html = f'<div class="na"><b>해당없음(근거 못 찾음 — 추측으로 채우지 않음)</b><ul>{lis}</ul></div>'
        cnt = {}
        for f in fs:
            k = ROLE_KO.get(f.get("role"), f.get("role"))
            cnt[k] = cnt.get(k, 0) + 1
        books = sorted({x.get("reference", {}).get("book", "") for x in fs + cs + rs if x.get("reference", {}).get("book")})
        meta = (f'발현소견 {len(fs)}개 · ' + " · ".join(f"{k} {v}" for k, v in sorted(cnt.items()))
                + f' · 배경조건 {len(cs)}개 · 참고항목 {len(rs)}개 · 근거 교재: {esc(", ".join(books))}')
        cond_tbl = (f'<h3>배경조건 — 어떤 배경의 환자인가 (환자 페르소나 근거)</h3>'
                    f'<table><thead><tr><th>조건</th><th>값</th><th>role</th><th>교재 인용 원문</th><th>출처</th><th>대조</th></tr></thead>'
                    f'<tbody>{rows_html(cs, "condition")}</tbody></table>') if cs else ""
        ref_tbl = (f'<h3 class="sep">참고항목 — 발현소견이 <b>아닌</b> 것 (검사·치료·감별진단·역학)</h3>'
                   f'<table><thead><tr><th>구분</th><th>내용</th><th>교재 인용 원문</th><th>출처</th><th>대조</th></tr></thead>'
                   f'<tbody>{ref_rows(rs)}</tbody></table>') if rs else ""
        # required가 없는 카드는 '빠뜨린 것'이 아니라 **의도된 판단**임을 표에 남긴다.
        noreq = (f'<div class="na"><b>필수(required) 소견을 두지 않은 이유</b> — {esc(d["required_없음_사유"])}</div>'
                 if d.get("required_없음_사유") else "")
        secs.append(
            f'<h2>{esc(d["질환"])}</h2><div class="meta">{meta}</div>' + noreq
            + cond_tbl
            + f'<h3>발현소견 — 어떤 증상·징후가 나오는가</h3>'
            f'<table><thead><tr><th>축</th><th>소견</th><th>role</th><th>교재 인용 원문</th><th>출처</th><th>대조</th></tr></thead>'
            f'<tbody>{rows_html(fs, "finding")}</tbody></table>'
            + na_html + ref_tbl
        )
    legend = "".join(
        f'<div><span class="dot" style="background:{ROLE_COLOR[k]}"></span><b>{v}</b> {ROLE_DESC[k]}</div>'
        for k, v in ROLE_KO.items())
    tot, totv = nf + nc + nr, nfv + ncv + nrv
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(data.get("제목","발현소견 · 배경조건 교재 근거 검토표"))}</title><style>{CSS}</style></head><body><div class="wrap">
<h1>{esc(data.get("제목","발현소견 · 배경조건 교재 근거 검토표"))}</h1>
<div class="sub">질환 {len(data["질환목록"])}개 · 발현소견 {nf}개 · 배경조건 {nc}개 · 참고항목 {nr}개 ·
교재 인용 원문대조 {totv}/{tot} 통과 ({round(totv/max(1,tot)*100)}%) · 생성 {esc(data.get("생성일",""))}</div>
<div class="warn"><b>⚠ 인용 대조 {round(totv/max(1,tot)*100)}%는 “임상적으로 맞다”는 뜻이 <u>아닙니다</u>.</b>
기계 대조가 확인하는 것은 <b>그 문장이 교재 원문에 실제로 존재하는가</b> 하나뿐입니다.
<b>그 인용이 이 소견의·이 role의 근거로 타당한가는 대조가 보지 못합니다.</b>
실제로 2026-08-11 임상타당성 검수에서, 인용 대조를 100% 통과한 상태에서 환자 안전 BLOCKER 2건
(혈변만으로 경험적 항생제 · 배변협조장애에서 회장루)이 이 틈으로 통과했습니다.
<b>대조 통과 = 채택 가능이 아닙니다.</b> 임상 채택은 교수 검증을 거쳐야 합니다.
{"" if totv==tot else " <b>✗</b> 표시는 원문에서 문장을 찾지 못한 것으로, 채택 전 확인이 필요합니다."}</div>
<div class="warn">⚠ review_status: draft — 임상 내용은 교수 검증 전 초안. 교재 원문 인용을 포함하므로 <b>공개 저장소 커밋 금지</b>(저작권).</div>
<div class="legend">{legend}</div>
{"".join(secs)}
</div></body></html>"""


def all_items(d: dict) -> list:
    return d.get("findings", []) + d.get("conditions", []) + d.get("참고항목", [])


def structural_warnings(data: dict) -> list[str]:
    """렌더는 통과하지만 표를 **모순되게** 만드는 것들.

    2026-08-11 실제로 터진 것들만 검사한다 —
      ① 같은 인용이 한 카드에 두 번(수정 스크립트가 한쪽만 고쳐 role이 갈린다. 실제 발생)
      ② `required_없음_사유`를 써 놓고 required가 남아 있음
      ③ `해당없음`으로 선언한 축에 소견이 존재
      ④ required가 없는데 사유도 없음
    """
    warn = []
    for d in data["질환목록"]:
        nm = d["질환"]
        fs, cs = d.get("findings", []), d.get("conditions", [])
        # ⚠️ 중복 판정은 **같은 축 안에서만.** 한 문장이 증상과 노출을 함께 담는 일은 흔해서
        #    (예: "Campylobacter 설사·혈변… 가금류 접촉") 소견과 배경조건이 같은 인용을 쓰는 건 정상이다.
        #    (2026-08-11: 축을 안 가리고 지웠다가 배경조건 6건을 잃고 복구했다.)
        for axis, items in (("발현소견", fs), ("배경조건", cs)):
            seen: dict[str, str] = {}
            for it in items:
                q = it["reference"].get("quote", "")
                if q in seen:
                    warn.append(f"{nm}: {axis} 안에서 같은 인용이 중복 — [{seen[q]}] / [{it.get('role')}] "
                                f"❝{q[:45]}…❞")
                seen[q] = it.get("role", "")
        reqs = [x for x in fs + cs if x.get("role") == "required"]
        if d.get("required_없음_사유") and reqs:
            warn.append(f"{nm}: 'required 없음' 사유를 명시했는데 required {len(reqs)}건이 남아 있음")
        if not reqs and not d.get("required_없음_사유"):
            warn.append(f"{nm}: required가 없는데 사유도 없음")
        na = {x.get("feature") for x in d.get("해당없음", [])}
        clash = na & {x.get("feature") for x in fs}
        if clash:
            warn.append(f"{nm}: '해당없음'으로 선언한 축에 소견이 있음 — {sorted(clash)}")
    return warn


def main():
    src = Path(sys.argv[1])
    snap = "--snap" in sys.argv          # 인용을 문장 경계까지 넓혀 저장(1회성 정비)
    data = json.loads(src.read_text(encoding="utf-8"))
    snapped = 0
    for d in data["질환목록"]:
        for it in all_items(d):
            ref = it.setdefault("reference", {})
            if snap and ref.get("quote"):
                load_raw()
                new = snap_to_sentence(ref["quote"])
                if new != ref["quote"] and verify(new)[0]:
                    ref["quote"], snapped = new, snapped + 1
            ok, note = verify(ref.get("quote", ""))
            it["_quote_verified"] = ok
            it["_quote_note"] = note
            if ok:  # book·page는 항상 기계가 원문 위치에서 다시 딴다(사람 입력 신뢰 안 함)
                book, page = resolve(ref["quote"])
                ref["book"], ref["page"] = book, page
    cnt = lambda key: sum(len(d.get(key, [])) for d in data["질환목록"])
    okc = lambda key: sum(1 for d in data["질환목록"] for x in d.get(key, []) if x["_quote_verified"])
    src.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    out = src.with_suffix(".html")
    out.write_text(build(data), encoding="utf-8")
    if snap:
        print(f"인용 {snapped}건을 문장 경계까지 확장(단어 중간 절단 제거)")
    print(f"질환 {len(data['질환목록'])}개 · 소견 {okc('findings')}/{cnt('findings')}"
          f" · 조건 {okc('conditions')}/{cnt('conditions')}"
          f" · 참고항목 {okc('참고항목')}/{cnt('참고항목')} 인용대조 통과 → {out}")
    for d in data["질환목록"]:
        for it in all_items(d):
            if not it["_quote_verified"]:
                print(f"  ✗ {d['질환']} | {it.get('name') or it.get('value')} | {it['_quote_note']}")
    if (warn := structural_warnings(data)):
        print(f"\n⚠ 구조 경고 {len(warn)}건 (인용 대조는 통과하지만 표가 모순된다)")
        for w in warn:
            print(f"  ⚠ {w}")


if __name__ == "__main__":
    main()
