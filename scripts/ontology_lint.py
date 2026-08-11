"""온톨로지 YAML 정합성 검사 — 커밋 전 게이트.

질환 카드를 쪼개거나 라벨을 추가할 때 **조용히 깨지는 것들**을 잡는다.
그래프 렌더(yaml_to_cypher/html)는 이런 오류를 에러 없이 통과시키므로, 눈으로는 발견하기 어렵다.

검사 항목
  1. 질환 id에 라벨이 있는가
  2. required/discriminator/red_flag/checklist/tests/education이 가리키는 id에 라벨이 있는가
  3. evidence.sources가 sources 레지스트리에 등록돼 있는가
  4. 질환 id 중복
  5. **질환 id ↔ 증상 라벨 id 충돌** ← 2026-08-11 5라운드에서 실제로 터질 뻔한 것.
     `hypercalcemia`(증상 라벨)와 같은 id로 질환 카드를 만들면 **그래프에서 한 노드로 병합**되어
     "고칼슘혈증이 고칼슘혈증의 감별점"인 자기참조 엣지가 생긴다. 렌더는 정상 종료한다.
  6. 아무 카드도 참조하지 않는 고아 라벨 (경고만)

사용:
  .venv/bin/python scripts/ontology_lint.py                 # ontology/*.yaml 전부
  .venv/bin/python scripts/ontology_lint.py ontology/diarrhea.yaml
종료코드: 0 = 통과, 1 = 오류 있음
"""
from __future__ import annotations
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
REF_KEYS = ("required_symptoms", "discriminators", "red_flags",
            "checklist_items", "tests", "education_items")


def lint(path: Path) -> list[str]:
    d = yaml.safe_load(path.read_text(encoding="utf-8"))
    labels = set(d.get("labels", {}) or {})
    sources = set(d.get("sources", {}) or {})
    diseases = d.get("diseases", []) or []
    ids = [x["id"] for x in diseases]
    errs: list[str] = []

    for dis in diseases:
        if dis["id"] not in labels:
            errs.append(f"질환 id에 라벨 없음: {dis['id']}")
        for k in REF_KEYS:
            for v in dis.get(k) or []:
                if v not in labels:
                    errs.append(f"[{dis['id']}] {k} → 라벨 없는 id: {v}")
        for v in (dis.get("disclosure") or {}).values():
            for x in v:
                if x not in labels:
                    errs.append(f"[{dis['id']}] disclosure → 라벨 없는 id: {x}")
        for s in (dis.get("evidence") or {}).get("sources") or []:
            if s not in sources:
                errs.append(f"[{dis['id']}] 등록되지 않은 source: {s}")

    for i in sorted({x for x in ids if ids.count(x) > 1}):
        errs.append(f"질환 id 중복: {i}")

    # ── 5. 질환 id ↔ 증상 라벨 충돌 ──
    referenced = set()
    for dis in diseases:
        for k in REF_KEYS:
            referenced |= set(dis.get(k) or [])
        for v in (dis.get("disclosure") or {}).values():
            referenced |= set(v)
    for i in sorted(set(ids) & referenced):
        errs.append(f"질환 id가 증상·검사 라벨로도 쓰임(그래프에서 노드 병합됨): {i}")

    orphans = sorted(labels - set(ids) - referenced - {d.get("chief_complaint")})
    warn = [f"⚠ 어떤 카드도 쓰지 않는 라벨: {', '.join(orphans)}"] if orphans else []

    print(f"\n## {path.relative_to(ROOT) if path.is_relative_to(ROOT) else path}"
          f" — 질환 {len(ids)}개 · 라벨 {len(labels)} · 출처 {len(sources)}")
    for e in errs:
        print(f"   ❌ {e}")
    for w in warn:
        print(f"   {w}")
    if not errs:
        print("   ✅ 통과")
    return errs


def main() -> int:
    args = sys.argv[1:]
    paths = [Path(a) for a in args] if args else sorted((ROOT / "ontology").glob("*.yaml"))
    bad = sum(len(lint(p)) for p in paths)
    print(f"\n{'❌ 오류 ' + str(bad) + '건' if bad else '✅ 전부 통과'}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
