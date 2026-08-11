# 자료 지형 — 온톨로지 근거화(evidence-grounding)용 소스 맵

> **목적:** 온톨로지(YAML)를 *실제 자료 근거*로 보강할 때, "무엇을 읽을 수 있고 / 무엇이 어디에 있고 / 무엇을 조심해야 하나"를 한 번에. **매번 재조사 반복 방지.**
> 작성 2026-07-06 · 조사자 Claude · 상위 자료 목차 = `materials/INDEX.md`(로컬) · 데이터 지도 = `docs/data-inventory.md`
> ⚠️ **이 문서는 git 추적(공개)** — 개인정보·사례원문 **미포함**(경로·커버리지·함정만). 실원문은 로컬 `materials/`·`data/` 참조.

---

## 0. 거버넌스 — 공개 vs 비공개 (제일 먼저)

| 위치 | git | 읽기 | 공개 YAML에 원문 삽입 |
|---|---|---|---|
| `ontology/*.yaml` | **추적(공개)** | ✅ | — (이게 산출물) |
| `materials/` (원본 재료 전부) | **제외** | ✅ 로컬 | ❌ 원문·개인정보 금지 |
| `data/raw/`·`data/raw_private/`·`data/working/` | **제외** | ✅ 로컬 | ❌ |
| `*.hwp *.pdf *.docx *.xlsx` (전역) | **제외** | ✅ 로컬(추출후) | ❌ |

**하드룰:** 원자료는 **로컬에서 읽어 근거로 삼되**, 공개 추적 파일(`ontology/*.yaml`, `docs/*`)엔 **① 출처 포인터(파일·위치) + ② 비식별·교과서 수준 사실**만 넣는다. **실사례 원문·개인정보(이름·연락처·SP 페르소나 실명)는 절대 커밋 금지.**
→ 상세 근거값이 필요하면 gitignore 위치(`data/working/…`)에 두고 YAML은 `source_id` 포인터만.

---

## 1. 읽을 수 있는 실제 소스 (근거 재료)

### A. 실제 부산대 CPX 사례 — 가장 강한 근거(단, 좁음)
- `materials/05_사례/급성복통_2024_요로결석.hwp` (+ 추출 `materials/_extracted/05_사례__급성복통_2024_요로결석.hwp.txt`, 9.3KB)
  - 실 시험 사례 = **요로결석(ureteral_stone) 1개만** 직접 근거. CPX 워크시트 형식(병력·진찰·채점표) 포함.
  - ⚠️ **개인정보 포함**(개발자 이름·전화·이메일, SP 실명) → **비식별 필수**, 공개 커밋 금지.
  - `data/raw_private/2026-06-18_pusan/…/급성복통_2024_초안.hwp`·`…/최종/…요로결석.hwp` 도 동일 사례(초안/최종).
- 그 외 부산대 실사례 hwp 다수(182개, 다른 주증상) — 필요 주증상 있으면 여기서.

### B. 교과서 청크 — 5질환 다 커버(단, 얇음)
- `data/working/rag_index/textbooks.json` = **Harrison 1권 샘플 1200청크**(rag.py 기준). **직접 읽기 가능**(임베딩·API 불필요, `json.load`).
- 복통 5질환 커버리지(grep 실측, 2026-07-06):

  | term | 청크 히트 | term | 히트 |
  |---|---|---|---|
  | appendicitis | 4 | ectopic | 4 |
  | peptic ulcer | 4 | ureter | 5 |
  | cholecystit | 1 | renal colic | 2 |
  | gallstone | 8 | Murphy / rebound(징후) | **0 / 0** |

  → 각 질환 몇 문장씩은 근거 확보 가능. **진찰징후(Murphy·반발통)는 이 샘플에 없음.**

### B′. 교과서 **전권** 코퍼스 — 2026-08-11 발견 (B의 상위호환)
- 위치: `~/ghq/github.com/click6067-ship-it/cpx-agent/data/raw/textbook/` (**별개 repo·로컬·git 제외**, 182MB / 진료과별 분류)
  - 내과: `harrison/PART1~PART13*.md`(파트별 분권) · `InternalMed_Harrison.txt`(22MB 통본) · `해리슨 내과학 19판 1~3.md`(한국어판)
  - 그 외: Sabiston(외과) · Schwartz · Rosen·Tintinalli(응급) · Williams·Novak(산부인과) · Nelson(소아) · Adams(신경) · Robbins · Bates · Katzung · DSM-5 등
- **B(1200청크 샘플)와의 차이**: 샘플은 변비 2히트·celiac 0·laxative 0으로 사실상 못 씀. 전권 코퍼스는 **챕터 통째로 직독** 가능하고 `[[pN]]` 원문 페이지마커가 있어 **페이지 단위 인용**이 된다 → 기억 기반 인용(금지) 없이 근거화 가능.
- 실사용 예: 설사·변비 온톨로지 = Harrison Ch.49 'Diarrhea and Constipation'(Table 49-2/49-3/49-5) 직독으로 근거화.
- ⚠️ **판(edition) 미표기** — 파일 헤더에 판 정보 없음(인용 참고문헌 최신 2023년). 논문·대외 인용 전 **원본 PDF로 판 확정 필요**.
- ⚠️ **저작권**: 교과서 원문이므로 이 repo로 복사·커밋 금지. 읽어서 근거로 쓰되 YAML엔 **출처 포인터 + 요지**만.

### C. 지침·교재(published) — 읽을 수 있는 추출본
- `materials/_extracted/06_지침_교재__CPX 총론_…txt` · `…교재-기본임상술기지침_…txt` · `…기본진료수행지침_…txt`
  - ⚠️ `기본진료수행지침`(798p) = **스캔본**(INDEX 기준 텍스트 없음/OCR 필요) → 추출 txt 유효성 **사용 전 확인**.
  - 성격 = CPX 시험 방법·술기 일반. 질환별 감별 리스트라기보단 수행·채점 프레임.

### D. 전문가 피드백 — ②심사 정답지(감별 근거 아님)
- `materials/_extracted/04_사례개발피드백__사례개발피드백_2021~2026.hwp.txt` — 실초안→전문가 피드백. 연도별 다른 사례(가슴통증·객혈·변비 등), 복통 직접 아님. **②심사(reviewer) gold** 용도.

---

## 2. 도구 (재추출·직독)
- **hwp 재추출:** `~/.local/bin/hwp5txt <file.hwp>` / `hwp5html`. (추출 txt가 비면 원본 .hwp에서 재추출.)
- **교과서 직독:** `json.load('data/working/rag_index/textbooks.json')` → 청크 리스트(문자열). RAG 파이프라인/임베딩 불필요.
- **RAG 검색(선택):** `src/cpx/rag.py`의 `retrieve_hybrid`/`grounding` — dense(Gemini 임베딩 API키 필요)+BM25. 근거 *자동*검색용. "직접 읽고 인용"과는 별개 경로.

---

## 3. 함정 (같은 실수 반복 방지)
- **hwp→txt 추출본이 개행 0** → `wc -l`이 **0으로 오인**(내용은 있음). `wc -c`/`head -c`로 확인. (예: 요로결석 사례 9294바이트인데 `wc -l`=0.)
- 교과서 인덱스 = **Harrison 1권 샘플뿐**(전체 아님). 얇고, 진찰징후·한국지침 미포함.
- **복통 station의 실 시험 사례는 요로결석만** — 나머지 질환(충수염·궤양·담낭염·자궁외임신 등)은 교과서/일반지식 수준. 커버리지 불균형.
  ⚠️ **2026-08-11 갱신**: 이 문장은 *복통 한정*이다. 주증상 전체로 보면 흉통 2건(기흉·심막염) · **설사 1건(과민성대장증후군)** · **변비 2건(기능성변비·직장류)**의 station 직접 실사례가 있다 — §5 표가 정본. (이전 판에서 "실사례는 요로결석뿐"이 문서 전역 주장처럼 읽혀 §5 표와 충돌했음 — Codex 검수 지적 반영.)
- 실사례엔 **개인정보** → 읽되 공개물엔 비식별.

---

## 4. 정직한 한계 (근거화가 *할 수 있는 것 / 못 하는 것*)
- ✅ 가능: 각 항목을 **실재 파일(교과서 청크·요로결석 사례·지침)에서 읽어 `source_id` 인용** + 미근거 항목은 정직하게 표기.
- ❌ 불가(과장 금지): "완전 검증" — (a) 실사례는 요로결석뿐, (b) 교과서 샘플 얇음, (c) **의학적 최종 정확성은 교수 검증 몫**. 산출 = "출처 달린 초안"이지 "검증 완료" 아님.
- 기억 기반 인용(페이지·장절 지어내기) = **금지**(가짜 인용 = 프로젝트 제1원칙 위반).

---

## 5. 근거화 매핑 (실사례 → 온톨로지 질환) — 2026-07-06 확정

> 추출 도구 = **`hwp5html`**(hwp5txt는 불완전 → hwp5html 써야 전체 추출). 추출물은 스크래치(gitignored)에만, **개인정보 커밋 금지.**
> 실사례는 각 사례 채점표의 **진단 교육항목 '근거'** 에서 discriminating feature를 확인해 grounding.

| 온톨로지 질환 | 실사례(로컬·비공개) | 주증상 station | 참고문헌(사례 기재) | evidence level |
|---|---|---|---|---|
| `ureteral_stone`(복통) | 급성복통_2024_요로결석 | **복통(직접)** | 비뇨의학 6판 Ch.17 | real_case_direct |
| `bowel_obstruction`(복통) | 구토_2026_장폐색 | 구토 | Sabiston Textbook of Surgery | real_case_related |
| `peptic_ulcer_disease`(복통) | 구토_2024_소화성궤양협착 | 구토 | (미기재) | real_case_related |
| `acute_cholecystitis`(복통) | 황달_2024_급성담관염 | 황달 | (미기재) | real_case_related |
| `pyelonephritis`(복통) | 발열_2023_신우신염 | 발열 | (미기재) | real_case_related |
| `pneumothorax`(흉통) | 가슴통증_2023_기흉 | **흉통(직접)** | Sabiston & Spencer, Surgery of the Chest 9e 2015 | real_case_direct |
| `pericarditis`(흉통) | 가슴통증_2022_심막염 | **흉통(직접)** | Harrison IM | real_case_direct |
| `ibs_diarrhea`(설사) | 설사_2022_과민성대장증후군 | **설사(직접)** | (미기재) | real_case_direct |
| `functional_constipation`(변비) | 변비_Hyb_2026_기능성변비 | **변비(직접)** | (미기재) | real_case_direct |
| `rectocele`(변비) | 변비_Hyb_2024_직장류 | **변비(직접)** | (미기재) | real_case_direct |

**2026-08-11 추가 — 새 근거등급 `station_differential_listed`:** 해당 station 실사례 **채점표에 감별진단·문진·검사로 명시**되었으나 그 사례의 확정진단은 아닌 질환(예: 변비 사례의 대장암·IBS-C·직장탈출증, 설사 사례의 갑상선기능항진증·여행자설사·담즙산설사). `real_case_direct`(확정진단)로 올리면 근거 강도를 과장하고, `standard_textbook`(사례 언급 없음)으로 내리면 과소평가라 4번째 등급을 신설. 렌더 반영 = `scripts/ontology_report.py`·`yaml_to_evidence_html.py`.

**실사례 없음(표준 교과서 초안·미검증):** 충수염·췌장염·위장관염·게실염·자궁외임신·골반염(복통) · ACS·대동맥박리·폐색전·GERD·근골격·공황(흉통).

**추가 근거화 후보(미사용 실사례):** 소화불량_위식도역류(GERD) · 설사_과민성대장(위장관염 인접) · 월경통_자궁내막증·배뇨이상_자궁근종(부인과 복통) · 토혈_소화성궤양출혈(궤양) · 호흡곤란_심부전(흉통 인접).

**막힌 것:** ① 기본진료수행지침 = 스캔·**OCR 도구 없음**(tesseract/pdftotext 부재) → 공식 감별목록 미확보 · ② 참고문헌 미기재 사례 다수(사례 자체가 출처).

---
*연결: `materials/INDEX.md`(전체 자료 목차·로컬) · `docs/data-inventory.md`(데이터 지도) · `docs/transparency.md`(모델·데이터 정본) · `docs/ontology-plan.md`(온톨로지 설계).*
