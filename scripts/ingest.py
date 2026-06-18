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
- checklist(채점항목): '의사질문-환자답변' 쌍을 domain별로(병력청취/신체진찰/환자교육/환자의사관계/사이시험). 각 항목에:
  · scoring_rule = 관찰가능·행동위주의 채점 기준 한 문장
  · keywords = 그 질문을 인정할 동의어/표현 3~6개(v0 결정론 채점용)
  · is_binary = true (병력/진찰), PPI는 별도 처리지만 일단 항목화
- 원문에 없는 값은 빈 문자열/빈 리스트. 추측으로 의학정보를 지어내지 말 것.

[원문]
{text}
"""


def to_cpxcase(text: str, case_id: str) -> CpxCase:
    case = llm.complete_json(PROMPT.format(text=text[:12000]), CpxCase)
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
