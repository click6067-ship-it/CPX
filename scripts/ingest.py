"""
[붙임2] CPX 양식(hwp/txt) → CpxCase JSON 변환 (LLM 구조화출력 보조).

사용: PYTHONPATH=src .venv/bin/python scripts/ingest.py <입력파일> [출력디렉토리] [case_id]
  예: ... scripts/ingest.py "[붙임2] CPX 개발 양식.hwp" data/working/dev_tune diarrhea_kim_v2

hwp는 표까지 뽑으려 hwp5html→텍스트, 그 텍스트를 LLM이 CpxCase 스키마로 구조화.
⚠️ 실제 사례는 **비식별 작업본**에만 쓰고(원본 X), no-training API로. (docs/data-governance.md)
"""
import sys
import re
import html
import glob
import subprocess
import tempfile
from pathlib import Path

from cpx.models import CpxCase
from cpx import llm


_PII = [
    (re.compile(r"[\w.+-]+@[\w.-]+\.\w+"), "[이메일]"),
    (re.compile(r"01[016-9][-\s.]?\d{3,4}[-\s.]?\d{4}"), "[전화]"),
    (re.compile(r"0\d{1,2}[-\s.]\d{3,4}[-\s.]\d{4}"), "[전화]"),
    (re.compile(r"\d{6}[-\s]?[1-4]\d{6}"), "[주민번호]"),
]


def deid(text: str) -> str:
    """API 전송 전 PII 제거(이메일·전화·주민번호). 이름은 CpxCase에 필드가 없어 미전파 + 프롬프트로도 제외."""
    for pat, repl in _PII:
        text = pat.sub(repl, text)
    return text


def extract_text(path: Path) -> str:
    if path.suffix.lower() == ".hwp":
        with tempfile.TemporaryDirectory() as td:
            subprocess.run(["hwp5html", "--output", td, str(path)], capture_output=True)
            xs = glob.glob(f"{td}/*.xhtml") + glob.glob(f"{td}/*.html")
            if xs:
                t = Path(xs[0]).read_text(encoding="utf-8", errors="replace")
                t = re.sub(r"<[^>]+>", " ", t)
                t = html.unescape(t)
                t = re.sub(r"[ \t]+", " ", t)
                t = re.sub(r"(\n\s*){2,}", "\n", t)
                return t.strip()
            r = subprocess.run(["hwp5txt", str(path)], capture_output=True, text=True)
            return r.stdout
    return path.read_text(encoding="utf-8", errors="replace")


PROMPT = """다음은 한국 의과대학 CPX 사례 워크시트([붙임2] 양식) 원문이다. 이를 CpxCase 스키마로 정확히 구조화하라.

규칙:
- 환자 인적사항·상황지침·활력징후·현병력(시간순)·가족력/사회력/산부인과력/과거력을 원문에서 채운다.
- checklist(채점항목): 원문 채점표/대화스크립트의 항목을 추출. 각 항목에:
  · scoring_rule = 관찰가능·행동위주의 채점 기준 한 문장
  · keywords = 그 질문을 인정할 동의어/표현 3~6개(v0 결정론 채점용)
  · is_binary = true (병력/진찰)
  · domain 분류 규칙(중요): '의사질문-환자답변' 쌍은 그 증상의 **병력청취**(또는 신체진찰)로 분류한다. **환자의사관계(PPI)는 공감·라포·면담구조화 등 소수(보통 2~5개)만** — 일반 문진 질문을 PPI로 넣지 마라.
  · ⚠️ **한 행=한 항목. 중복 금지. 전체 항목은 보통 30개 안팎**(과도하게 쪼개지 말 것).
- 원문에 없는 값은 빈 문자열/빈 리스트. 추측으로 의학정보를 지어내지 말 것.
- ⚠️ 개발자·평가자·기관 직원의 이름·연락처·소속은 출력에 포함하지 마라(임상 사례 내용만 추출).

[원문]
{text}
"""


def to_cpxcase(text: str, case_id: str, model: str | None = None) -> CpxCase:
    # ingest=품질 작업 → 기본 강한 모델(flash-latest), 전문(잘림 최소). 채점표 표를 빠짐없이.
    case = llm.complete_json(PROMPT.format(text=deid(text)[:40000]), CpxCase,
                             model=model or "gemini-2.5-flash")
    return case.model_copy(update={"case_id": case_id})


def main():
    if len(sys.argv) < 2:
        print("사용: scripts/ingest.py <입력파일> [출력디렉토리] [case_id]")
        return
    src = Path(sys.argv[1])
    outdir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/working/dev_tune")
    case_id = sys.argv[3] if len(sys.argv) > 3 else src.stem

    text = extract_text(src)
    print(f"추출 텍스트 {len(text)}자 → LLM 구조화…")
    case = to_cpxcase(text, case_id)

    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{case_id}.json"
    out.write_text(case.model_dump_json(indent=2), encoding="utf-8")
    print(f"✅ {out}")
    print(f"  제목: {case.title} · 주증상: {case.chief_complaint} · 진단: {case.diagnosis}")
    print(f"  환자: {case.patient.age}세 {case.patient.sex} · 체크리스트 {len(case.checklist)}항목")
    for it in case.checklist[:6]:
        print(f"    - [{it.domain}] {it.id}: {it.scoring_rule[:30]}… kw={it.keywords[:3]}")


if __name__ == "__main__":
    main()
