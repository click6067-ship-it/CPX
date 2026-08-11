# 시연 절차서 — 온톨로지 → CPX 사례 → 결정론 검증

> **목적**: 교수님께 **돌아가는 것**을 보여준다. 검수 이력이 아니라 파이프라인.
> 산출물은 `data/working/demo/`(gitignored) — 교재 인용을 포함할 수 있어 공개 저장소에 올리지 않는다.

## 한 줄 요약

**질환 카드(온톨로지)가 사례 생성을 제약하고, 같은 카드로 생성 결과를 기계 검증한다.**
검증은 LLM 판단이 아니라 **규칙 기반**이라 같은 입력이면 항상 같은 결과가 나온다.

---

## 시연 1 — 온톨로지 제약이 만드는 차이 (**메인, 키 불필요**)

같은 모델·같은 설정으로 두 번 생성한 결과를 같은 잣대로 검증한다.

```bash
PYTHONPATH=src .venv/bin/python demo_ontology_case.py \
  --ontology ontology/chest_pain.yaml --disease acute_coronary_syndrome \
  --compare data/working/ontology_pipeline/baseline_case.json \
            data/working/ontology_pipeline/scaffolded_case.json
```

→ `data/working/demo/chest_pain_acute_coronary_syndrome_compare.html`

**보여줄 지점**

| 검사 | 제약 없음 | 온톨로지 제약 |
|---|---|---|
| 공개 규칙(과공개 금지) | 실패 | **통과** |
| 채점표 항목 수 | 25 | **42** |
| 종합 | 실패 | 검토 필요 |

- **과공개 금지**가 핵심이다. 제약 없이 만들면 환자가 묻지도 않은 감별 단서를 먼저 말해 버려
  학생의 병력청취 능력을 평가할 수 없다. 카드의 `disclosure` 규칙이 그걸 막는다.
- 필수증상·감별단서는 양쪽 100%다 — **제약이 없어도 LLM이 흔한 것은 잘 만든다.**
  차이는 "흔한 것"이 아니라 **구조·규칙**에서 난다. 이 점을 정직하게 말할 것.

---

## 시연 2 — 카드 한 장을 열어 보이기 (키 불필요)

```bash
# 이 온톨로지에 어떤 질환이 있는지
PYTHONPATH=src .venv/bin/python demo_ontology_case.py --ontology ontology/diarrhea.yaml --list

# 카드 + 기존 사례 + 6검사 + 교재 근거를 한 장으로
PYTHONPATH=src .venv/bin/python demo_ontology_case.py \
  --ontology ontology/diarrhea.yaml --disease ibs_diarrhea --case data/cases/diarrhea_kim.json
```

**보여줄 지점** — ④ 교재 근거 표. 각 소견이 어느 교재 문장에 근거하는지 **원문 인용과 페이지**가 붙는다.
인용은 `scripts/findings_review.py`가 교재 원문과 기계 대조를 통과시킨 것만 실린다(현재 315/315).

> ⚠️ 이 조합은 카드(IBS)와 사례(급성 감염성 장염)가 **서로 다른 질환**이라 검사 결과가 낮게 나온다.
> 시연에서는 "손으로 쓴 기존 사례는 온톨로지가 요구하는 요소를 갖추지 않는다"는 대비로 쓰거나,
> 아래 시연 3으로 **설사 카드에서 생성한 사례**를 만들어 쓰는 편이 낫다.

---

## 시연 3 — 설사·변비 온톨로지로 실제 생성 (**API 키 필요**)

```bash
set -a; source ~/.secrets/api-keys.env; set +a     # 사용자가 직접 실행
PYTHONPATH=src .venv/bin/python demo_ontology_case.py \
  --ontology ontology/diarrhea.yaml --disease ibs_diarrhea --generate
```

생성 → 자동 검증 → HTML까지 한 번에 나온다. 다른 질환은 `--list`의 id를 쓰면 된다.
변비는 `--ontology ontology/constipation.yaml`.

**이걸 한 번 돌려 두면** 시연 1을 설사로도 할 수 있다(생성본 vs 기존 사례).

---

## 함께 보여줄 것

| 무엇 | 파일 |
|---|---|
| 지식그래프 전체 모습 | `docs/diarrhea-graph.png` · `docs/constipation-graph.png` |
| 근거화 현황·검수 이력 | `docs/ontology-grounding-report.html` |
| 발현소견 교재근거 검토표 | `data/working/findings/*.html` (로컬만) |

---

## 시연 전 점검 (2분)

```bash
.venv/bin/python scripts/ontology_lint.py                                   # yaml 정합성
.venv/bin/python scripts/findings_review.py data/working/findings/diarrhea_findings.json    # 인용·구조
PYTHONPATH=src .venv/bin/python demo_ontology_case.py --ontology ontology/diarrhea.yaml --list
```

세 개가 모두 통과하면 시연 준비 완료다.

---

## 말하지 말아야 할 것 (중요)

이 시스템은 **작동을 보이는 단계**이지 검증된 단계가 아니다. 다음은 주장하지 않는다:

- ❌ "임상적으로 정확하다" — 온톨로지·검토표 모두 `review_status: draft`, 교수 검증 전
- ❌ "온톨로지가 품질을 개선한다" — n=1 일화적 기계 데모다. 통계적 개선 주장 불가
- ❌ "출제범위다" — 공식 감별목록(기본진료수행지침) 미확보. 임시 teaching set
- ❌ "GraphRAG보다 낫다" — 비교 실험 없음

말할 수 있는 것:
- ✅ 온톨로지 카드가 생성을 제약하고, **같은 카드로 결정론 검증**까지 닫힌 루프가 돈다
- ✅ 소견마다 **교재 원문 인용**이 붙고, 인용은 기계 대조를 통과한 것만 실린다
- ✅ Codex 적대검수를 12회 돌렸고 **모든 지적과 미해결 항목이 `docs/verification-log.yaml`에 기록**돼 있다

> 검수 이력을 숨기지 않는 것이 이 프로젝트의 강점이다. 물어보시면 그대로 보여드리면 된다.
