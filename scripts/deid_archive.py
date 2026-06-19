"""
CPX 사례개발자료 아카이브 전체 비식별 → 안전 텍스트로 변환.
실행: PYTHONPATH=src .venv/bin/python scripts/deid_archive.py
입력: data/raw_private/2026-06-18_pusan/extracted/**/*.hwp (170개)
출력: /tmp/cpx_deid_archive/CPX사례개발자료(21-26)_비식별/  (폴더구조 유지, .txt)
처리: hwp→텍스트 추출 → deid(이메일·전화·주민번호 마스킹 + 개발자 메타블록 제거) + 아카이브 강화 스크럽 → 잔여 PII 스캔.
⚠️ .hwp 원본은 바이너리라 안전 편집 불가 → 비식별 '텍스트'로 변환. 자동 비식별은 best-effort(이름 100% 보장 X) → 플래그된 파일은 사람 점검 권장.
"""
import sys, re, glob
sys.path.insert(0, "scripts")
from pathlib import Path
from ingest import extract_text, deid

SRC = Path("data/raw_private/2026-06-18_pusan/extracted")
OUT = Path("/tmp/cpx_deid_archive/CPX사례개발자료(21-26)_비식별")
OUT.mkdir(parents=True, exist_ok=True)

_CONTENT = r"영역|기능|장기|상황|수험생|표준화환자|병력|증상|주\s*증상|채점|진료"


def scrub(t: str) -> str:
    """기본 deid + 아카이브 강화(트레일링 PII 없는 개발자 블록도 콘텐츠 경계까지 제거)."""
    t = deid(t)
    t = re.sub(r"(개발자?|작성자)[\s\S]{0,40}?(이름|성명|소속|전공|휴대폰|연락처)[\s\S]{0,220}?(?=" + _CONTENT + r"|\Z)",
               " [개발자정보 비공개] ", t)
    return t


def residual(t: str):
    f = []
    if re.search(r"[\w.+-]+@[\w.\-]", t): f.append("이메일")
    if re.search(r"01[016-9][-\s.]*\d{3,4}[-\s.]*\d{4}", t): f.append("전화")
    if re.search(r"\d{6}[-\s]?[1-4]\d{6}", t): f.append("주민번호")
    if re.search(r"(휴대폰|연락처|전화)\s*[:：]?\s*\d", t): f.append("연락처라벨+숫자")
    return f


files = sorted(glob.glob(f"{SRC}/**/*.hwp", recursive=True))
flagged, done = [], 0
for fp in files:
    p = Path(fp)
    rel = p.relative_to(SRC).with_suffix(".txt")
    try:
        t = scrub(extract_text(p))
    except Exception as e:
        flagged.append((str(rel), [f"추출실패:{str(e)[:30]}"])); continue
    out = OUT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(t, encoding="utf-8")
    done += 1
    r = residual(t)
    if r:
        flagged.append((str(rel), r))

(OUT / "_README.txt").write_text(
    "CPX 사례개발자료(21-26) — 비식별(de-identified) 텍스트 변환본\n"
    "- 원본 .hwp에서 텍스트 추출 후 이메일·전화·주민번호 마스킹, 개발자(작성자) 이름·소속·연락처 블록 제거.\n"
    "- .hwp 원본은 안전 편집이 불가해 텍스트(.txt)로 변환했습니다(표는 줄글로 펼쳐짐).\n"
    "- 자동 비식별은 best-effort입니다. 외부 공유 전, 아래 '점검 권장' 파일은 사람이 한 번 확인하세요.\n", encoding="utf-8")

print(f"✅ 변환 {done}/{len(files)} → {OUT}")
print(f"⚠️ 잔여 PII 점검 권장 {len(flagged)}개:")
for rel, r in flagged[:40]:
    print(f"   - {rel}: {','.join(r)}")
if len(flagged) > 40:
    print(f"   … 외 {len(flagged)-40}개")
