"""교재 원문 인용 채굴기 — 검색어 → (책·페이지·원문 문장) 후보 출력.

발현소견(Finding) 교재근거 검토표를 만들 때 **인용문을 손으로 옮겨 적지 않기 위한** 도구.
손으로 옮기면 오타·오페이지가 반드시 생기고, 그건 이 프로젝트에서 가장 무거운 결함(가짜 인용)이다.

- 페이지는 인용문 **직전의 `[[pN]]` 마커**를 그대로 딴다(교재 파일 규약).
- 출력된 `quote`는 원문에서 잘라낸 문자열이라 그대로 JSON에 넣으면 대조를 통과한다.
- 교재 본체는 저작권 자료라 이 repo에 없다. 로컬 코퍼스 경로만 참조한다(TEXTBOOK_ROOT).

사용:
  python scripts/textbook_mine.py "rebound tenderness"                # 전 교재
  python scripts/textbook_mine.py "Rome IV" --book PART10 --n 8
  python scripts/textbook_mine.py "senna|bisacodyl" --book PART2 --width 260
"""
from __future__ import annotations
import argparse
import os
import re
import sys
import unicodedata
from pathlib import Path

TEXTBOOK_ROOT = Path(os.environ.get(
    "TEXTBOOK_ROOT",
    Path.home() / "ghq/github.com/click6067-ship-it/cpx-agent/data/raw/textbook",
))

# 자주 쓰는 축약 이름 → 실제 파일 경로 조각
BOOK_ALIAS = {
    "PART2":  "harrison/PART2_Cardinal_Manifestations",
    "PART10": "harrison/PART10_Disorders_of_the_Gastrointestinal_System",
    "PART9":  "harrison/PART9_Disorders_of_the_Kidney",
    "PART5":  "harrison/PART5_Infectious_Diseases",
    "sabiston": "Sabiston - Textbook of Surgery",
    "schwartz": "Surgery_Schwartz",
    "rosen":    "Rosen_8th_Full",
    "tintinalli": "Tintinalli",
    "bates":    "Bates_PhysicalExam",
    "robbins":  "Pathology_Robbins",
}

# 인용에 쓸 책 표기(검토표 `book` 필드) — 파일 조각 → 표기
BOOK_LABEL = [
    ("harrison/PART2",  "Harrison (PART2)"),
    ("harrison/PART10", "Harrison (PART10)"),
    ("harrison/PART9",  "Harrison (PART9)"),
    ("harrison/PART5",  "Harrison (PART5)"),
    ("Sabiston",        "Sabiston 19th"),
    ("Schwartz",        "Schwartz"),
    ("Rosen",           "Rosen 8th"),
    ("Tintinalli",      "Tintinalli 8th"),
    ("Bates",           "Bates"),
    ("Robbins",         "Robbins"),
]


def label_for(rel: str) -> str:
    for frag, lab in BOOK_LABEL:
        if frag in rel:
            return lab
    return Path(rel).stem[:28]


def clean(s: str) -> str:
    """표시·인용용 정리 — 소프트하이픈/제로폭 제거, 줄바꿈·이중공백 흡수, 행말 절음 복원."""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"[­​-‍﻿]", "", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"(\w)- (\w)", r"\1\2", s)   # 'abdomi- nal' → 'abdominal'
    return s.strip()


def iter_files(book: str | None):
    frag = BOOK_ALIAS.get(book, book) if book else None
    for p in sorted(TEXTBOOK_ROOT.rglob("*")):
        if p.suffix.lower() not in (".md", ".txt"):
            continue
        rel = str(p.relative_to(TEXTBOOK_ROOT))
        if frag and frag.lower() not in rel.lower():
            continue
        yield rel, p


def mine(pattern: str, book: str | None, n: int, width: int, ctx: int):
    rx = re.compile(pattern, re.I)
    hits = 0
    for rel, path in iter_files(book):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        # 페이지 마커 위치 인덱스
        marks = [(m.start(), m.group(1)) for m in re.finditer(r"\[\[p(\d+)\]\]", text)]
        for m in rx.finditer(text):
            # 직전 페이지 마커
            page = "?"
            for pos, num in marks:
                if pos <= m.start():
                    page = num
                else:
                    break
            seg = text[max(0, m.start() - ctx): m.start() + width]
            seg = clean(re.sub(r"\[\[p\d+\]\]", " ", seg))
            print(f"\n[{label_for(rel)} p{page}]  ({rel})")
            print(f"  {seg}")
            hits += 1
            if hits >= n:
                print(f"\n— {hits}건 출력(상한 도달). --n 으로 더 볼 수 있음.")
                return
    print(f"\n— 총 {hits}건." + ("" if hits else "  ⚠ 검색어를 못 찾음 — 표현을 바꿔 다시."))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern", help="정규식(대소문자 무시)")
    ap.add_argument("--book", help="PART2·PART10·sabiston·rosen 등 별칭 또는 경로 조각")
    ap.add_argument("--n", type=int, default=6, help="출력 개수 상한")
    ap.add_argument("--width", type=int, default=320, help="매치 이후 표시 길이")
    ap.add_argument("--ctx", type=int, default=80, help="매치 이전 표시 길이")
    a = ap.parse_args()
    if not TEXTBOOK_ROOT.exists():
        sys.exit(f"교재 코퍼스를 찾을 수 없음: {TEXTBOOK_ROOT}  (TEXTBOOK_ROOT 환경변수로 지정)")
    mine(a.pattern, a.book, a.n, a.width, a.ctx)


if __name__ == "__main__":
    main()
