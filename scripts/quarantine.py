"""
실제 사례 격리·인벤토리 (도착 시 첫 실행 — docs/data-governance.md §3).
사용: PYTHONPATH=src .venv/bin/python scripts/quarantine.py data/raw_private/2026-06-18_pusan

해시 + 인벤토리만 만든다. 원본은 읽기만(수정 X). 비식별·분할은 다음 단계(별도).
누수 방화벽의 첫 단추: 무엇이 들어왔는지 불변 기록.
"""
import sys
import json
import hashlib
from pathlib import Path


def sha256_16(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()[:16]


def main(target: str):
    d = Path(target)
    if not d.exists():
        print(f"❌ 경로 없음: {d}  (먼저 원본을 여기 넣으세요)")
        return
    files = [p for p in d.rglob("*") if p.is_file() and p.name != "inventory.json"]
    inv = [{
        "file": str(p.relative_to(d)),
        "bytes": p.stat().st_size,
        "sha256_16": sha256_16(p),
        "ext": p.suffix.lower(),
    } for p in sorted(files)]

    out = d / "inventory.json"
    out.write_text(json.dumps({"dir": str(d), "count": len(inv), "files": inv},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 인벤토리: {len(inv)}개 파일 → {out}\n")
    for i in inv:
        print(f"  {i['sha256_16']}  {i['bytes']:>9,}  {i['file']}")
    print("\n⚠️ 다음 (docs/data-governance.md §3):")
    print("  1) 비식별 작업본 생성(원본 불변)  2) 분할 train_prompt/dev_tune/locked_eval")
    print("  3) data/DATASET_VERSION.md  4) 그 다음 ingestion → CpxCase JSON")
    print("  ⛔ 원본을 LLM 채팅에 붙여넣거나 SaaS 업로드 금지. locked_eval은 평가날까지 잠금.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data/raw_private")
