# 데이터 인벤토리 (전체) — CPX-AI

> **전체 데이터 지도** — gitignore된 것 포함 모든 데이터를 한 곳에. (커밋됨: 공개레포 목록용.)
> 상세 로컬 목차·실내용 = `materials/INDEX.md`(로컬) · 거버넌스 = `docs/data-governance.md` · 맥락 = `docs/context-map.md`.
>
> ⚠️ **거버넌스:** 실 사례·저작권 자료는 **원본 파일만 gitignore**(커밋 금지). 이 문서는 *구조·목록*이며, **민감 원본(부산대 실사례 ~170건)은 개별 나열하지 않고 요약**한다(파일명에 이름·질환 특정 포함 → 공개레포 누수 방지). 전체 나열이 필요하면 로컬에서 `find data/raw_private`.
>
> 🔑 **자료 2종:** **참고자료**(`materials/` = 사람이 읽는 원본) ↔ **파이프라인 데이터**(`data/` = 코드가 처리·생성). = **재료 vs 가공품.**

---

## A. 참고자료 — `materials/`  🔒 gitignore(로컬 전용)
> ★ 시스템 직접 재료 · ☆ 도메인 근거(검색) · ⭐ 2026-07-01 신규. 실내용 = `materials/_extracted/`.

| 카테고리 | 파일 | 무엇 → 어디 쓸지 |
|---|---|---|
| **01_기획연구** | 사업계획서(임선주) | 연구지원사업 신청서 → 목표·일정·IRB 근거 |
| | ★ CPX AI agent 연구문제 | 4 Agent 연구문제(신뢰도·타당도…) → 평가 하네스·논문 RQ |
| **02_CPX양식_점검표** | ★ [붙임2] CPX 개발 양식 | 표준양식+예시(설사 김선미) → ①생성 스키마(CpxCase) 정본 |
| | [붙임3]·실기문항저자점검표 (≈동일) | 저자 자가점검(30항목 기준) → ②심사 루브릭 |
| | ⭐ 실기시험 사례개발 점검표 | 개발자 1차 점검(적절/보완) → ②심사·QC |
| **03_채점_PPI루브릭** | ⭐ new PPI 채점표 | PPI **4단계(3·2·1·0)** 원본 → ④채점 PPI |
| | ⭐ PPI_체크리스트_피드백 | PPI **1-0** 34항목+피드백멘트 → ④채점 PPI+debrief(완성형) |
| | ⭐ 환자의사관계 채점표(수정중) | 위 1-0 이전 버전 → 참고 |
| | ⭐ 신체진찰평가_2018.xlsx | 진찰별 단계기준+SP훈련 → ④채점 신체진찰(D3)·③SP |
| **04_사례개발피드백** | ★ 사례개발피드백_2021~2026 (5) | 실 초안→전문가 피드백 → ②심사 정답지(D6)·few-shot |
| **05_사례** | ★⭐ 급성복통_2024_요로결석 | 실 CPX 사례 → ①생성 few-shot ⚠️**PII·비식별 필요** |
| **06_지침_교재** | ☆ CPX총론(412p)·기본임상술기지침(546p)·기본진료수행지침(798p) | 도메인 근거(RAG) · ⚠️진료수행지침=스캔본(OCR) |
| **07_회의_공지** | ☆ 에듀테크 회의 260603·260611 | 결정·역할 맥락 |
| | ⭐ 국시 실기 변경 2차 공지 | 국시 구조(임상표현48·술기9) → 설계 제약 |
| **08_논문** | ☆ Challenges…(임선주·이혜윤 PI 논문)·Agent Hospital | 설계 근거·개념 |
| **09_수업자료** | ☆ 260416 PPI 수업(임선주 35p) | PPI·실기 개요 근거 |
| **_archive** | data_clean.zip | 교과서en 18권+문제(US/중국/대만) → RAG 코퍼스 |

**계: 문서 26개** (+ `INDEX.md`·`_extracted/` 로컬).

---

## B. 파이프라인 데이터 — `data/`

### 공개 (커밋 OK)
| 경로 | 내용 |
|---|---|
| `cases/` | 손작성 gold 사례 JSON 3: `chestpain_lee`·`diarrhea_kim`·`headache_park` |
| `toy/` | 공개 재현용 toy 데이터셋(사례·fixtures·adversarial 복사본) |
| `transcripts/` | 데모 학생↔가상환자 대화 3건 |
| `fixtures.json` | 하네스 손라벨 fixture · `adversarial.json` 적대 transcript 팩 |
| `labeling_workbook_template.csv` | H4-real 임상교원 블라인드 라벨 템플릿 |
| `README.md`·`DATASET_VERSION.md` | 구조·버전 메모 |

### 🔒 비공개 (gitignore — 절대 커밋 금지)
| 경로 | 내용 |
|---|---|
| `raw_private/2026-06-18_pusan/` | **실 부산대 사례 원본 ~170건** = `초안/`·`최종본`·`피드백` × 증상(48주증상 일부) × **2021~2026** + 원본 zip. (예: 가슴통증·객혈·급성복통·두통·발열…) *개별 파일명 나열 생략(이름·질환 특정 → 누수 방지).* 총 172 파일. |
| `working/` | 비식별 작업본·**연도층화 분할(train25/dev45/locked17)**·`rag_index/`·`dev_tune/`·`dev_drafts/`·`gen_sample.json`·`survey_build/`·`validation_build/`·`adjudication/` |

> ※ `materials/04_사례개발피드백`·`05_사례`(사람용 원본 hwp) ↔ `data/raw_private`(파이프라인 격리본)은 **별개 사본**. 전자는 참고용, 후자는 비식별·분할 대상.

---

## C. 온톨로지 — `ontology/` (커밋 OK)
- `chest_pain.yaml` — 흉통 온톨로지 정본(질환5, `review_status: draft`) → validator 대조 카드.
- `chest_pain.cypher` — Neo4j 렌더(YAML→자동생성).
- *(예정)* **흉통 LLM wiki**(마크다운 정제지식·롱컨텍스트) + **markdown 변환 사례** — 교수 숙제 4·6(`ontology-plan §5.5`), 다음 스텝 산출물. 위치 = `ontology/wiki/` 또는 `docs/wiki/`(착수 시 확정).

---

## gitignore 요약 (무엇이 커밋 안 되나)
`.gitignore`: `materials/`(참고자료 전체) · `data/raw/`·`data/raw_private/`·`data/working/`(민감 파이프라인) · `*.hwp`·`*.pdf`·`*.docx`·`*.xlsx`·`*.zip`(오피스/압축 원본) · `.env`·`flowise/.cookies`(비밀).
→ **커밋되는 데이터** = `data/cases`·`data/toy`·`data/transcripts`·`data/*.json/csv`·`ontology/`·이 인벤토리 문서들.
