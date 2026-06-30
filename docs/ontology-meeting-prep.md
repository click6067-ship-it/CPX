# CPX 온톨로지·지식그래프 미팅 준비 (2026-07-02 시뮬레이션센터)

> 작성: 2026-06-30 · 김용하 + Claude(+Codex). 용도 = ① 용하 본인 이해 ② 교수님(박정빈/임선주) 설명 ③ 7/2 미팅 핸드아웃.
> 근거 = 최신(2025-2026) 웹검색 + 적대검증. 현 시스템 정본 = `architecture.md`·`rag.py`.
> ⚠️ 이 문서 v2 = 5개 리서치 스트림 종합 + **Codex(gpt-5.5) 독립 리서치·레드팀 통합(§10, 2026-06-30 완료)**. deep-research Workflow 재실행은 용하 결정으로 생략(v1 출처로 충분). §10이 v1 본문 일부를 교정 — 본문에 ⚠️ 포인터로 표시.

---

## 0. 한 장 요약 — 미팅에서 실제로 무슨 일이 일어났나

**미팅 입력 = 박정빈 교수의 일관된 비전 하나.** 채원우가 그 일부(로컬 모델·wiki·키워드 온톨로지)를 *전달*한 것이지 별개 제안이 아니다. → **전부 박정빈 교수 안으로 해석한다.**

> 👑 **대원칙: 박정빈 교수 안이 정본·목표다.** 우리 일 = 그 뜻을 **정확히 해석해 충실히 실행**하는 것. 대안을 밀거나 반박하는 게 아니다. **최대 리스크 = 그의 의도를 오해하는 것.** (아래의 "작게 시작·단계화"는 *그 비전을 가장 빠르고 정확히 구현하는 수단*이지, 다른 안이 아니다. 시점·범위가 갈리면 우리가 정하지 말고 §8에서 *교수님께 확인*한다.)

| 박정빈 교수 안 (한 비전) | 기술 정체 | 우리 실행(그의 뜻대로) |
|---|---|---|
| 온톨로지 + Neo4j 지식그래프로 LLM이 **근거 갖고** 사례 생성 | 지식그래프 기반 grounded generation | 온톨로지 설계 착수 → 지식그래프 → **Neo4j(그가 지목한 목표 그릇)** |
| (채원우 전달) 로컬 35B 256k + 마크다운 wiki + 키워드 온톨로지 | 로컬 LLM + LLM wiki + SKOS | 정제 CPX 지식을 wiki로, 로컬 롱컨텍스트로 실행 |

**핵심: 두 줄은 대립이 아니라 한 비전의 두 부분이다** — 온톨로지(설계)를 먼저 잡고, 지식그래프(Neo4j)로 담아 사례를 근거 있게 생성하며, 정제지식은 wiki로 로컬에 올린다. 미팅에서 우리가 할 일 = **"교수님 뜻을 이렇게 이해했는데 맞습니까?"를 확인**(§8). *공통 전제 = "온톨로지(원인·증상·질환 의미설계)를 먼저"는 교수 안의 출발점.*

---

## 1. 개념 바로잡기 (틀리면 미팅에서 꼬임)

### 1.1 온톨로지 vs 그래프 vs Neo4j
- **온톨로지** = "이 도메인에 어떤 **엔티티(종류)** 가 있고 **어떤 관계**로 엮이나"를 명시한 **의미 설계/스키마**. (예: `질환 —has_symptom→ 증상`, `질환 —caused_by→ 원인`)
- **Neo4j** = 그 온톨로지를 담는 **그릇**(그래프 DB). 도구일 뿐.
- 채원우 **"graph 연결이 아닌 온톨로지"** = *노드를 선으로 잇는 작업 자체가 가치가 아니라, 원인·증상·질환의 **의미 타입·관계를 설계**하는 게 핵심* 이라는 말 → **기술적으로 맞다.** 최신 연구도 일관: **스키마(엔티티·관계 타입)는 사람이 먼저 손으로 설계하고, 그래프는 그걸 채우는 그릇**(schema-based KG가 의료에서 schema-free보다 우수, *LLM-empowered KG Construction Survey* arXiv:2510.20345, 2025).

### 1.2 ⚠️ 이름 충돌 — `graph` 두 개
- 우리 레포 `src/cpx/graph.py` = **LangGraph**(개발 워크플로우 흐름제어: 생성→심사→수정 루프).
- 박정빈의 "Neo4j 그래프" = **지식그래프(knowledge graph)**.
- **완전히 다른 것.** 문서·미팅에서 "graph"를 구분해 표기할 것 (LangGraph=흐름 / Neo4j=지식).

### 1.3 "근거 갖고 생성" = 두 패턴 (CPX엔 B)
- **Pattern A — 검색해서 근거 주입**(대부분 GraphRAG 제품): 질문→그래프에서 서브그래프 검색→프롬프트에 *맥락으로* 붙임. 우리 현 RAG와 목적 유사(그래프 버전).
- **Pattern B — 그래프를 생성 뼈대(scaffold)로** ⭐: 그래프에서 **질환 노드 선택**→이웃(증상·병력·진찰·검사·감별) **순회**→"이 질환 시나리오를 만들되 **반드시 이 증상/진찰/감별 포함**"으로 LLM에 강제. 그래프가 *무엇을 포함할지*를 **제약** → 빠뜨림·날조 방지.
- **CPX 사례 생성엔 Pattern B가 정답.** 근접 선행: CLINGEN(ACL2024), MedKGEval(arXiv:2510.12224, WWW'26), ICD-10+SNOMED-CoT(arXiv:2512.05256, 2025.12). **OSCE/CPX를 지식그래프로 생성한 논문은 아직 없음 → 신규 기여 공간.**

---

## 2. ⭐ GraphRAG vs LLM wiki — 정확한 구분 (둘은 다른 것)

> 용하 지적대로 **둘은 다른 패턴**이다. 단, 흔한 오해("GraphRAG=검색 / LLM wiki=검색 없이 통째 로드")는 **부정확**하다(적대검증 결과). 정확한 차이는 아래.

**먼저 오해부터 정정 (적대검증 확인):**
- LLM wiki도 **선택적 검색을 한다.** Karpathy 원본(gist)은 *통째 로드*가 아니라 **`index.md`(목차)를 읽고 → 관련 페이지만 골라 읽는다.** 규모 커지면 인덱스도 안 들어가서 "결국 검색이 다시 필요"하다고 본인이 명시(작은 검색엔진까지 붙임).
- GraphRAG도 **빌드 시 대량 사전계산**(엔티티추출·커뮤니티탐지·요약 사전생성)을 한다. 쿼리 때는 *사전계산된 요약*에 접근.
- **Karpathy 본인:** "LLM wiki는 RAG를 **대체하지 않는다.** 사고의 방향을 바꿀 뿐." 대규모·동적·멀티유저는 여전히 RAG. → **보완재**.

**그래서 진짜 차이 (정확한 축):**

| 차원 | **GraphRAG** | **LLM wiki (Karpathy/DeepWiki)** |
|---|---|---|
| 최초 | MS Research, **2024-04**(arXiv:2404.16130), OSS 2024-07 | DeepWiki(Cognition) **2025-04**(코드레포) / Karpathy gist **2026-04** |
| 중간표현 | **기계지향** 엔티티-관계 그래프 + Leiden 커뮤니티 요약 | **인간가독** 마크다운 산문 + wikilinks + `index.md` |
| 쿼리 시 접근 | 그래프 순회(local) / 커뮤니티 요약 map-reduce(global) | `index.md` 탐색→관련 **페이지 통째**를 컨텍스트에 로드 |
| RAG인가? | **예**(그래프형 RAG 변종) | "Beyond RAG"로 포지셔닝(보완재, 대체 아님) |
| 빌드 | **자동 LLM 파이프라인**(엔티티추출→그래프→커뮤니티→요약). 비쌈(LazyGraphRAG로 ~0.1% 절감) | **LLM 큐레이션·사람 주도**(소스 추가→LLM이 페이지 통합·갱신·lint) |
| 추론 | **명시적 다중홉 관계 순회** + 전역 sensemaking | **산문 종합**(wikilink는 형식 엣지 아님) |
| 스케일 | 대규모 코퍼스(100만 토큰+) | ~수백 페이지(~100-300k토큰)까지 실용 |
| 비용 | 인덱싱 비쌈, 쿼리는 저렴 | 인프라 0, **쿼리 비쌈**(전체 페이지 읽음; vector RAG 대비 ~21x — arXiv:2605.18490, 2026-05) |
| 철학 | "관계 구조로 검색 정밀도↑" | "지식을 미리 컴파일해 매 쿼리 재검색 회피" |
| 인프라 | 그래프DB+벡터스토어+추출 파이프라인 | 파일시스템 + LLM 에이전트(벡터DB 0) |

**결론:** 같지 않다. 두 축에서 근본적으로 다름 — ① **기계지향 그래프 vs 인간가독 산문**, ② **자동추출 vs LLM큐레이션**. 표면 유사("naive chunk RAG를 넘어선다")가 혼동 원인. **혼동이 틀린 이유:** GraphRAG의 가치 = "그래프 검색이 벡터 검색보다 낫다", LLM wiki의 가치 = "미리 컴파일하면 검색을 줄인다" — 같은 질문("쿼리 때 지식을 어떻게?")에 대한 *다른 답*.

**조합 가능(우리에게 중요):**
1. **그래프로 빌드 → wiki로 쿼리**: GraphRAG 추출로 커뮤니티 요약 생성 → 마크다운 위키 페이지로 렌더 → 위키식으로 질의. (DeepWiki가 실제로 내부는 그래프, 표출은 위키 = 부분 하이브리드.)
2. **wiki + 경량 그래프 인덱스**: 마크다운 위키 + "어느 페이지가 어느 엔티티 언급" 그래프 인덱스 → 쿼리 시 그래프로 페이지 선택 후 로드.

---

## 3. RAG·GraphRAG·LLM wiki·롱컨텍스트 — CPX 결정 프레임워크

> 용하 질문 "RAG랑 LLM wiki 겹치나?"의 정확한 답: **목적 겹침(둘 다 외부지식 주입), 방식·적합영역 다름.** 한 지식 덩어리엔 택일, 지식을 크기·안정성·관계여부로 나누면 보완.

| 도구 | 적합 | CPX에서 담당 |
|---|---|---|
| **RAG(현재 우리 것: 임베딩+BM25 청크)** | 큰·동적 비구조 코퍼스, 단발 사실조회 | **교과서 18권** 등 대량 사실 보조(현행 유지) |
| **LLM wiki(마크다운 통째/페이지 로드)** | 작은·안정·정제 지식(~100-300k토큰) | **CPX 형식·루브릭·48주증상·진료수행지침** 등 정제·안정 지식 |
| **GraphRAG/온톨로지(Neo4j)** | 다중홉 관계추론, 생성 뼈대(B) | **원인-증상-질환 관계 + 사례 생성 뼈대 + 감별 추론** |
| **롱컨텍스트(통째 로드)** | KB가 컨텍스트에 다 들어갈 때 | 위 wiki를 256k 모델에 로드하는 *실행 방식* |

**핵심 판단:**
- **RAG vs wiki 겹침 지점** = "정제 가능한 안정 지식". CPX 형식·루브릭처럼 *작고 안정*이면 → **wiki(검색 불필요, 엉뚱한 청크 문제 제거)**. 교과서처럼 *크면* → **RAG**. → *지식을 크기/안정성으로 라우팅*.
- **KG는 둘과 안 겹침** — RAG도 wiki도 "A→B→C 관계추론"·"이 질환의 감별 3개"를 구조적으로 못 줌. 그건 그래프만의 영역.
- ⚠️ **교정(§10 Codex):** "온톨로지=Neo4j"가 아니다. **온톨로지(엔티티·관계 의미설계)는 v2+로 미룰 필요 없음** — Neo4j 없이 `YAML/JSON disease card + validator`만으로 "그래프-스캐폴드 생성"의 **~70%를 즉시 구현** 가능. *비용 사유로 v2+에 미룬 건 그래프DB/풀 GraphRAG지 온톨로지 자체가 아님.* → 2주 MVP는 파일+validator로 시작(§10.5).
- 근거: *LLM Wiki vs RAG 결정 프레임워크*(MindStudio 2026), *Knowledge Graphs vs RAG*(Atlan 2026), *Knowledge Base vs Knowledge Graph*(Kloia 2026: "GraphRAG=기계지향 중간구조, LLM wiki=인간가독 중간구조 — 적이 아니라 가까운 친척"). 셋은 redundant 아닌 complementary.

---

## 4. ⭐ 미팅 숙제 답 — "CPX 온톨로지 엔티티를 뭘로?"

임선주 숙제. SNOMED CT/HPO/MONDO + 임상 KG 논문 기반 추천.

**핵심 엔티티(지금 만들 것):**
- `질환 Disease` · `증상 Symptom`(주관·환자호소) · `징후 Sign`(객관·진찰소견) · `원인/병인 Etiology` · `위험인자 RiskFactor`
- 병력: `주호소 ChiefComplaint` · `현병력 HPI`(OLDCARTS/OPQRST 차원) · 과거력/가족력/사회력/약물/알레르기
- 진찰: `활력징후 VitalSign` · `진찰소견 PhysicalExamFinding` · `특수수기 SpecialManeuver`(예: Murphy 징후)
- 검사: `검사 Lab/Imaging` · `결과값 FindingValue`
- 추론: `감별진단 DifferentialDiagnosis` · `진단기준 DiagnosticCriterion` · `병리특이소견 Pathognomonic`
- 관리: `치료 Treatment` · `환자교육 PatientEducation`
- **CPX 메타(표준에 없음 → 직접 구축):** `CaseStation`(난이도·학습목표·루브릭 매핑) · `Demographics` · `CommunicationChallenge`(PPI용)

**관계 + ⭐엣지 속성(가장 중요):**
- `질환 -has_symptom→ 증상`, `-has_sign→ 징후`, `-caused_by→ 원인`, `-has_risk_factor→ 위험인자`, `-confirmed_by→ 검사`, **`-differentiated_from→ 질환`**(자주 헷갈리는 쌍 = CPX 교육 핵심)
- **엣지에 저장:** `frequency`(빈도) · `sensitivity`/`specificity` · `is_pathognomonic`(있으면 거의 확진) · `is_discriminating`(감별을 가르나) → **감별진단 랭킹 알고리즘의 연료.**

**표준 재사용(바퀴 재발명 금지):** 질환ID=**MONDO**, 증상/징후=**HPO + SNOMED CT**, 검사명=**LOINC**, 약=**RxNorm** (LLM이 표준용어를 알아 추출정확↑; *AutoRD* JMIR 2024: 온톨로지 그라운딩 +14.4%). **단 한국어 환자언어·CPX 교육메타는 직접 구축.**

> ⚠️ **§10 Codex 교정 (중요) — "질환-중심"이 아니라 "주증상-중심":** CPX는 진단명이 아니라 **주증상(ChiefComplaint)→감별→체크리스트·수행항목** 중심이다. 그래서 위 표준 엔티티에 **CPX 시험-수행 계층을 반드시 섞어야** 한다: `ChecklistItem`(병력/진찰 이분법 채점 1행동 단위) · `RedFlag`(단순사례 금기) · `CpxStationMeta`(48주증상·시간·난이도·task) · `PpiRubric`/`MicroBehavior`(이분법 부적합). **추가 엣지속성:** `cpx_required`·`student_visible`·**`patient_should_disclose_if_asked`**·`spontaneous_disclosure_allowed`(가상환자 과공개 방지) · `source_id`·`evidence_level`·`review_status`·`professor_approved`(교수 HITL·재현성). → 표준은 "코드·상호운용", *시험 성패를 가르는 채점항목·과공개 규칙·오답유도 감별은 자체 스키마*.

---

## 5. "키워드 기반 온톨로지" = 실제로 뭘 하나 (채원우 질문)

= 무거운 형식논리(OWL) 말고 **가벼운 통제어휘(SKOS 택소노미)**:
```
흉통 (prefLabel) = chest pain (altLabel/동의어)
  ├ broader(상위):  통증
  ├ narrower(하위): 흉막성 흉통 · 협심통 · 근골격계 흉통
  └ related(연관):  호흡곤란 · 발한
```
- = **용어 + 계층 + 동의어**. 추론기 없음. **한국어 환자말→표준용어 정규화**에 딱(환자 "쥐어짜듯 아파요"→`협심통`). 스프레드시트/JSON으로 시작 = **가장 먼저 만들 층.**
- **3층 권장:** ① SKOS(키워드·동의어) → ② Neo4j property graph(관계+엣지속성) → ③ OWL(자동추론, *SNOMED 연동 필요할 때만 나중에*).
- **CPX 권장: Neo4j + SKOS층부터. OWL은 미루기**(설계 오버헤드가 진도 잡아먹음 — 연구 일치 조언).

---

## 6. 로컬 모델 인프라 (채원우: 35B Q4 256k / TurboQuant)

- **목적**: LLM-wiki를 로컬에서 돌리려면 **긴 컨텍스트(256k+)** 모델 필요(통째 로드용).
- **256k 되는 ~35B(2026)**: **Qwen3-30B-A3B (MoE, 256k 네이티브)** 가 1순위 — 30B인데 활성 ~3B만 계산해 가벼움. (Gemma 4 26B, GLM-4.x-Flash 등.)
- **Q4 양자화**: 35B dense 가중치 ~20GB. **진짜 병목은 256k KV 캐시**(35B dense FP16 ~16GB 추가) → 24GB 카드 빡빡.
- **TurboQuant** ⚠️ 정정: **모델 가중치 양자화가 아니라 KV 캐시 압축**(Google 2025-04, ICLR2026). KV 3~6배 압축. **단 2026 중반 llama.cpp 정식 병합 아직**(실험적). "turboquant 가능 버전"은 아직 미성숙.
- **우리 아키텍처와 충돌**: 결정 = "상위모델(Claude/GPT) 먼저, 로컬은 kappa 통과 후 distill". 채원우 로컬-우선과 충돌 → **"검증은 상위모델로, 로컬은 비용·프라이버시 옵션으로 병행 실험"** 으로 정렬 제안.

---

## 7. 리스크 & kill 조건 (학술 엄밀성 — 논문 신뢰성 직결)

| 리스크 | 내용 | 대응/kill |
|---|---|---|
| **LLM 엔티티추출 환각** ⚠️최대 | LLM이 교과서서 그래프 만들 때 **없는 질환-증상 관계 날조** → 하류 사례생성까지 전파 | 표준(SNOMED/HPO)으로 스키마 제약 + **모든 트리플 교수 검증** |
| **Text2Cypher 취약** | 자연어→그래프질의가 엉뚱한 서브그래프 반환 | 핵심 질의는 **고정 Cypher 템플릿** |
| **범위 조기확대** | GraphRAG를 비용 사유로 v2+ 미뤘었음. 앞당기면 타당성게이트(부산대 gold 10건+) 전 위험 | **작은 코어 온톨로지(흔한 CPX 질환 N개)부터** |
| **과대주장** | "근거 기반 생성"이라 주장하려면 측정 필요 | 그래프 커버리지·교수 수용률·환각율 *사전등록* 후 측정 |

> ⚠️ **§10.3에 Codex 독립 레드팀 결함표(7개·kill조건)** 추가 — 위 표와 일부 중복되나 *주증상-중심 누락·자동추출 triple precision<0.9 폐기·평가없는 GraphRAG 데모 금지* 등 신규 kill 조건 포함.

---

## 8. 미팅 정렬 포인트 + 교수께 던질/받을 질문

**A. 자세 = 박정빈 교수 안을 *정확히 해석해 실행*** (정렬할 두 사람이 있는 게 아님 — 채원우는 전달자). 미팅에서 우리 역할 = 반박·대안 제시가 아니라 **"교수님 뜻을 이렇게 이해했습니다, 맞습니까?" 확인.** 해석이 갈리는 지점은 우리가 정하지 말고 교수님께 물어 *의도를 확정*한다.
- ✅ **교수님께 직접 확인할 해석 포인트 (오해 방지):**
  1. **"근거 갖고 생성"** = 그래프가 사례에 들어갈 **필수요소(증상·감별·red flag)를 강제**해 누락·날조를 막는 것 — 이렇게 이해했는데 맞습니까?
  2. **Neo4j를 바로** 세울까요, 아니면 **1개 주증상을 작은 카드(YAML)로 먼저 검증한 뒤 Neo4j로 옮길까요?** (어느 쪽이든 교수님 결정대로 — 단계화는 *더 빨리·정확히* 그 그래프에 도달하려는 수단일 뿐)
  3. **엔티티 범위** = 질환만이 아니라 **주증상·체크리스트·감별·과공개 규칙**까지 잡는 게 맞습니까?
  4. 온톨로지 인스턴스(실제 트리플)는 **LLM 추출 후 교수 검증**으로 채우는 방식 OK입니까?

**B. 우리가 준비할 답 (예상 질문):**
- "엔티티 뭐로?" → §4 표 (이미 생각해온 안으로 제시 = 강력)
- "RAG 있는데 왜 그래프?" → §3 (관계추론·생성뼈대는 RAG가 못 함)
- "온톨로지 자동으로 만드나, 손으로?" → 스키마는 손(교수검증), 인스턴스는 LLM추출+검증(§7)
- "근거 기반이라 어떻게 증명?" → §7 사전등록 측정

**C. 차별점(교수 어필):** CPX/OSCE를 지식그래프로 **생성**하는 건 아직 논문 없음 + 부산대 실데이터 보유 → **그래프가 사례 필수요소를 강제하는 생성(그래프-스캐폴드) = 신규 기여.** (미팅에선 "Pattern A/B" 같은 내부 용어 대신 "그래프가 필수요소를 강제한다"로 말할 것.)

> ⚠️ **§10.4에 Codex가 뽑은 교수 예상질문 7개 + 우리 약점**(엔티티 정의·SNOMED로 한국어 해결되나·Neo4j 꼭 필요한가·"근거 기반" 입증·GraphRAG>RAG 증거·과공개·논문 주장범위) — 미팅 직전 리허설용.

---

## 9. 핵심 출처 (2024-2026)
- GraphRAG: MS arXiv:2404.16130(2024-04) · LazyGraphRAG(MS 2024) · Neo4j GraphRAG Python(2025) · LLM KG Builder(neosemantics OWL 임포트)
- LLM wiki: Karpathy gist(2026-04) · DeepWiki/Cognition(2025-04) · vector-RAG vs wiki 비교 arXiv:2605.18490(2026-05, ~21x 비용)
- 임상 KG 생성: CLINGEN(ACL2024) · MedKGEval(arXiv:2510.12224) · ICD-10+SNOMED-CoT(arXiv:2512.05256) · MedKGI(arXiv:2512.24181, 감별진단)
- 온톨로지: SNOMED CT · HPO · MONDO · LOINC · RxNorm · AutoRD(JMIR 2024) · KG construction survey(arXiv:2510.20345)
- 모델: Qwen3-30B-A3B(256k) · TurboQuant(Google 2025-04/ICLR2026)
- 결정 프레임워크: MindStudio · Atlan · Kloia(2026)

---

## 10. Codex(gpt-5.5) 독립 리서치·레드팀 종합 (2026-06-30)

> 출처 = Codex(gpt-5.5)가 read-only로 `architecture.md`·`AGENTS.md`·`transparency.md`·`rag.py` 정독 + 웹검색 30여 건(SNOMED CT 개념모델·HPO·MS GraphRAG·OSCE 사례생성·Karpathy LLM wiki·DeepWiki·Qwen3-30B-A3B·TurboQuant·Neo4j GraphRAG·한국 SNOMED 멤버십). **deep-research Workflow 재실행은 용하 결정으로 생략**(v1 §9 출처로 충분, 7/2까지 시간 여유 우선).

### 10.1 핵심 교정 (v1 → v2)
1. **질환-중심 ❌ → 주증상-중심 ✅**: CPX는 진단명이 아니라 **주증상→감별→체크리스트·수행항목**이 축. 온톨로지에 *시험-수행 계층*(ChecklistItem·RedFlag·CpxStationMeta·PpiRubric)을 섞어야 함 (→§4 교정).
2. **온톨로지 ≠ Neo4j**: 온톨로지(의미설계)는 v2+로 미룰 필요 없음. **Neo4j 없이 `YAML/JSON disease card + validator`로 그래프-스캐폴드 ~70% 즉시 구현.** 비용으로 미룬 건 그래프DB/풀 GraphRAG (→§3 교정).
3. **한국 SNOMED 현실**: 한국은 **2020년 SNOMED International 39번째 회원국** 가입. 국내 기관은 **한국보건의료정보원(NRC) 통해 별도 국제가입·추가비용 없이** 활용 안내 (한국보건의료정보원 https://www.khis.kr/menu.es?mid=a20203010000 · SNOMED https://www.snomed.org/membership, 접속 2026-06-30). → "SNOMED 라이선스 비용" 질문에 답 가능.

### 10.2 엔티티/엣지속성 보강 (§4 통합표)
| 계층 | CPX 엔티티 | 표준 재사용 | 자체 구축 |
|---|---|---|---|
| 질환 | `Disease` | MONDO, SNOMED CT | 주증상별 출제범위·부산대 case id |
| 증상/징후 | `Symptom`,`Sign` | SNOMED CT, HPO | 한국어 환자표현·학생질문 트리거 |
| 검사 | `Test`,`Finding` | LOINC, SNOMED CT | CPX서 "시행해야 할 진찰/검사" |
| 치료/교육 | `Treatment`,`Medication`,`Education` | RxNorm, SNOMED CT | 학생에 요구되는 설명문구 |
| 감별 | `DifferentialDiagnosis` | SNOMED/MONDO | "혼동 유발 감별" 우선순위 |
| **채점** | `ChecklistItem` | **표준 없음** | 부산대 체크리스트·PPI 루브릭 |
| **실기메타** | `CpxStationMeta`·`RedFlag` | **표준 없음** | 48주증상·시간·난이도·PPI·task |

**엣지속성(필수, 단순 `has_symptom`이면 "기침=폐렴" 얕은 그래프됨):** `frequency`·`sensitivity`·`specificity`·`pathognomonic`·`is_discriminating`·`severity`·`onset`·`typical_age/sex` + **CPX 전용** `cpx_required`·`student_visible`·`patient_should_disclose_if_asked`·`spontaneous_disclosure_allowed` + **거버넌스** `source_id`·`evidence_level`·`review_status`·`professor_approved`.

**그래프-스캐폴드 절차(Pattern B):** 질환노드 선택 → 주증상/위험인자/감별/검사/교육 서브그래프 추출 → 필수/금지 요소 체크 → LLM 서사화 → **그래프 validator**. *그래프는 "문학적 생성"이 아니라 포함해야 할 의학·CPX 요소를 제약.*
**평가지표:** schema coverage · required checklist coverage · red-flag omission rate · differential plausibility · contradiction rate · grounded fact precision · 교수 accept/minor/major/reject · kappa/ICC · 과공개율.
**직접근거 없음(명시):** "한국 CPX/OSCE를 온톨로지+Neo4j GraphRAG로 생성·검증"한 직접 선행연구 미확인(2024-2026). 가까운 건 OSCE 가상환자·LLM 평가·의료 GraphRAG = **전이 근거로만**. → 차별점이자 *과대주장 금지 경계*.

### 10.3 레드팀 — v1 계획 결함 7 + kill 조건
| 무엇이 문제 | 왜 위험 | kill 조건 |
|---|---|---|
| Neo4j 조기도입 | 그래프DB 운영이 연구질문보다 커짐 | 2주 내 교수승인 사례 3개 못 만들면 Neo4j 보류 |
| GraphRAG="근거 기반 생성" 과대주장 | 틀린 triple = 근거 아닌 오류 전파 | **source 없는 triple 사용 금지** |
| "표준 가져오면 CPX 해결" 착각 | SNOMED/HPO는 채점·과공개·PPI 모름 | CPX 체크리스트 커버리지 <80%면 자체계층 우선 |
| LLM 자동 wiki/ontology 생성 | 환각 triple이 구조화돼 더 위험 | **무작위 50 triple precision <0.9면 자동추출 폐기** |
| 로컬 35B 조기 주력화 | 모델품질·긴context·KV비용이 연구 삼킴 | kappa CI가 API 대비 열등하면 로컬은 후속 |
| 질환-중심 그래프 | CPX는 주증상·수행항목 중심 | Disease-only schema면 중단 |
| 평가 없는 GraphRAG 데모 | 예쁜 그래프가 품질개선 증거로 오해 | **정량 before/after 없으면 "연구 성과" 주장 금지** |

### 10.4 교수 예상질문 7 + 우리 약점 (미팅 리허설)
1. **"엔티티 정확히 뭘로?"** → 질환이 아니라 `주증상-질환-증상/징후-감별-체크리스트-교육/PPI`. *약점: 48주증상 전체 매핑 아직 없음.*
2. **"SNOMED 쓰면 한국 CPX 표현 해결?"** → 아니다. SNOMED=코드·관계 기준, 한국어 환자표현·학생질문 동의어는 별도 로컬레이어. *약점: 한국어 synonym 구축 비용.*
3. **"Neo4j 꼭 필요?"** → 2주 MVP엔 불필요. YAML/JSON graph card로 시작, 쿼리 복잡도 생기면 이전. *약점: Neo4j 데모 기대치와 다를 수 있음.*
4. **"근거 기반 생성이라 할 수 있나?"** → 지금은 "그래프 제약 생성". source-linked triple coverage·contradiction rate·교수 accept율 측정해야 "근거 기반". *약점: gold data 부족.*
5. **"GraphRAG가 RAG보다 낫다는 증거?"** → 일반 GraphRAG 근거는 있으나 CPX 직접근거 없음. ablation으로 검증. *약점: 선행연구 직접성 약함.*
6. **"환자가 과공개하면 시험 깨지지 않나?"** → symptom/checklist 엣지에 `disclose_if_asked`·`spontaneous_disclosure_allowed`. *약점: 실대화 검증 전엔 규칙품질 미확정.*
7. **"논문서 뭘 주장?"** → "온톨로지+validator가 CPX 사례의 필수요소 누락·모순을 줄였는가"까지만. "AI가 교수와 동등"은 주장 안 함.

### 10.5 최단순 버전 — 7/2 이후 2주 MVP (over-engineering 방지)
**스코프 = 48주증상 전체 ❌, 1개 주증상(예: 흉통 또는 복통)만.** 산출물 4개면 충분:
1. `ontology/chest_pain.yaml`
2. 질환 5개(대표진단 1 + 주요감별 4)
3. 노드: `Disease`·`Symptom`·`RedFlag`·`ChecklistItem`·`EducationItem`
4. validator: 생성 사례가 `필수증상`·`감별단서`·`red flag`·`체크리스트`·`과공개 규칙` 만족하는지 검사
```yaml
chief_complaint: chest_pain
diseases:
  - id: acute_coronary_syndrome
    required_symptoms: [chest_pressure, exertional_worsening]
    discriminators: [radiation_to_left_arm, diaphoresis]
    red_flags: [hypotension, syncope]
    checklist_items: [ask_onset, ask_radiation, ask_risk_factors]
    education_items: [explain_need_for_ecg]
```
**2주 목표 = 그래프DB ❌ →** "교수가 볼 수 있는 구조화된 CPX 지식카드 + 그 카드로 생성한 사례 3개 + validator 리포트".

### 10.6 미팅 최종 권고 멘트 (교수님 비전을 충실히 실행하는 톤)
> **"교수님 말씀대로 온톨로지 지식그래프로 사례를 근거 있게 생성하는 방향으로 가겠습니다. SNOMED 같은 표준을 참조하되 핵심은 한국 CPX 수행항목과 환자 응답정책으로 잡고, 먼저 1개 주증상에 대해 질환-증상-감별-체크리스트 카드를 만들어 생성 사례의 누락·모순이 줄어드는지 검증하겠습니다. Neo4j로의 전환 시점은 교수님 원하시는 대로 — 바로 세울지, 이 검증 뒤에 옮길지 정해 주시면 그대로 따르겠습니다."**

*(톤 주의: "우리가 Neo4j를 미루겠다"가 아니라 "교수님 비전이 목표이고, 시작 방식만 가장 빠른 경로를 제안드린다". 시점·범위 결정권은 교수님께.)*

### 10.7 (생략) deep-research Workflow
- [x] Codex 독립 리서치 + 레드팀 → 통합 완료(위 §10).
- [~] deep-research 하네스(5각도 fan-out) → **용하 결정으로 생략.** 필요 시 후속 세션에서 한국 CPX 특수성·임상 KG SOTA 심화로 재가동 가능.
