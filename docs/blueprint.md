# CPX-AI — 블루프린트 (단일 진입점)

> **"이거만 보면 전부."** 이 프로젝트의 현재 상태를 한 문서로 — **30초 → 5분 → 딥다이브 링크**. 상세는 각 정본 문서로 연결한다.
> **최종 갱신:** 2026-07-01 · 김용하 + Claude (+ Codex 적대검수) · 불변 규약·본질 = [`AGENTS.md`](../AGENTS.md)

---

## ⏱ 30초 — 무엇·왜·지금

- **무엇:** 의대 **CPX(임상수행평가)** 교육을 위해 AI가 사례를 **① 생성 → ② 심사 → ③ 가상환자 → ④ 자동채점**하는 4-에이전트 파이프라인 + 그 **검증 하네스**.
- **본질:** 양산부산대병원·**임선주 PI**와의 **학술 연구 프로젝트**(영리·사업 아님). 목적 = **논문·검증·투명성**(오픈소스·부산대 무료). 김용하 = 학부생 개발 담당(전체 end-to-end 단독 구현, 논문 저자 아님).
- **🔑 지금 최우선 (2026-07-01):** **온톨로지 지식그래프로 "근거 기반 생성"** — 박정빈 교수 비전. LLM이 아무렇게나가 아니라 **구조화된 지식(원인–증상–질환) 안에서 근거를 갖고** 사례를 만들게 한다. **미팅 = 7/2(목) 12시 시뮬레이션센터.**
- **정직성(가장 중요):** 현재는 **엔지니어링 smoke 단계**. "AI=전문가 동등"·"근거 기반 생성 효과" 같은 타당성 주장은 **측정한 뒤에만** 한다.

---

## ⏱ 5분 — 어떻게 돌아가나 (각 항목 → 딥다이브)

### 1. 4-에이전트 파이프라인 — [`architecture.md`](architecture.md)
기존 CPX 사례(씨앗) → **① 생성**(멀티에이전트·checklist-seed·진단조건부 인구통계) → **② 심사**(②A 구조 + ②B 임상·RAG → Accept/Minor/Major/Reject → 교수 확정) → **③ 가상환자**(텍스트·과공개 제어 답변정책) → **④ 채점**(병력·진찰 = 이분법, PPI = 별도 루브릭). LangGraph 루프(생성→심사→수정). **toy 데이터로 작동 검증**(타당성 주장 아님).

### 2. 🔑 온톨로지 레이어 — 근거 기반 생성 — [`ontology-plan.md`](ontology-plan.md)
**박정빈 교수 비전** (정본 = `ontology-plan §0`에 교수 원문 verbatim). 의학 지식을 **온톨로지(원인–증상–질환)로 설계 → 지식그래프**로 만들고, 그 그래프가 사례 **필수요소를 강제**(증상·감별·red flag·과공개 규칙) → 누락·날조를 줄인다. *4-에이전트를 교체하는 게 아니라 **① 생성의 입력 제약 + 사후 validator**로 얹는 레이어.*
- **지식 3층 (경쟁 아닌 보완):** 지식그래프(관계·감별·생성뼈대) / **LLM wiki·롱컨텍스트**(마크다운 정제지식: CPX 형식·루브릭, 256k+·로컬 35B) / RAG(큰 교과서 — 조연·축소 중).
- **저장:** YAML 정본(`ontology/chest_pain.yaml`) + **Neo4j 거울**(한 방향 렌더·시각화).
- **validator(결정론·LLM 0회):** **2-렌즈** — "환자가 *가졌나*(positive)" vs "학생이 *선별했나*(asked)"를 분리 측정 + 과공개·필수요소 누락 검출. 한국어 부정문 처리. 표준 온톨로지(SNOMED 등)가 못 하는 CPX 고유 규칙. **Codex 6R APPROVED · 33테스트.**
- **좁게 시작:** 흉통 1개 주증상(질환5 = ACS + 감별4, `review_status: draft`). Neo4j 전환·48주증상 확대·로컬 35B 주력화 **시점은 교수님 결정**(`ontology-plan §7`).

### 3. 검증 — [`validation-design.md`](validation-design.md) · [`roadmap.md`](roadmap.md)
- **H2 (현재 파일럿):** ②의 AI 심사가 교수의 과거 피드백을 얼마나 재현하나 → 교수 **블라인드 설문**(recall·precision·ICC). `cpx-adj-web.vercel.app`, 6건 feasibility. **교수 응답 대기 = 다음 게이트.**
- **하네스:** H1 사례품질 · H2 심사신뢰 · H3 가상환자 일관·과공개 · H4 채점타당. 임계 **사전등록** · 전문가간 floor 먼저 · silver-label = 스모크 only.

### 4. 데이터·모델 — [`transparency.md`](transparency.md) · [`data-inventory.md`](data-inventory.md)
- **데이터:** 부산대 실사례 **170 hwp 도착**(격리·누수안전 분할, 🔒비공개·학교자산) · RAG 교과서(MedQA 배포본 18권, 🔒저작권) · 공개 재현용 toy. **materials/(원본 재료) vs data/(파이프라인 산출).**
- **모델:** ①② = gpt-5.5, ③④ = GPT-4o(미구현), 임베딩 = gemini-embedding-001, sparse = BM25(로컬), 보조·ingest = gemini-2.5-flash. 어댑터(`llm.py`)로 교체. **no-training 유료 티어** · 외부엔 비식별만.
- **트레이싱:** LangSmith + **셀프호스트 Langfuse** + **redaction**(본문 마스킹·해시 보존, egress 게이트 `CPX_TRACE_ACK`) → 사례·저작권 본문 SaaS 비유출. ③·④ 실제 학생 상호작용은 추적 제외.

### 5. 지금 어디 · 다음 3스텝
1. 흉통 **LLM wiki**(마크다운 정제지식 — CPX 형식·흉통 임상·루브릭)
2. chest_pain **Neo4j + validator** 구현·진행
3. **7/2(목) 12시 온톨로지 미팅**(시뮬센터) → 교수 확인(`ontology-plan §7`) → 흉통 카드 교수검증·사례3 생성
- **교수 숙제 (7항목 · 정본표 = [`ontology-plan §0`](ontology-plan.md)):** ① 엔티티 설계 · ② keyword 온톨로지 · ③ 원인–증상–질환(단순 graph 링크 아님) · ④ markdown CPX 사례 변환 · ⑤ 로컬 35B Q4·256k·TurboQuant · ⑥ LLM wiki · ⑦ Skill.MD.

### 6. ⚠️ 정직성 경계 (과대주장 금지 — 논문 정직성)
- 현재 **엔지니어링 smoke**(손라벨·소표본) — kappa 타당성 주장 **아님.**
- H2 = feasibility 파일럿(6건) — "AI가 전문가에 필적/대체" **주장하지 않음.**
- 온톨로지 임상내용 = **draft**(교수 검증 전) · "근거 기반 생성 효과"는 **정량 측정**(필수요소 누락률·모순율·교수 accept율) 후에만.
- 실제 학생 transcript + 임상교원 라벨로 **본검증** 후에만 타당성을 논함.

---

## 📚 딥다이브 지도 (전부 2026-07-01 현행)

| 문서 | 무엇 | 역할 |
|---|---|---|
| [`AGENTS.md`](../AGENTS.md) | 불변 규약·본질·최우선 설계(박정빈 원문) | 정본 |
| [`ontology-plan.md`](ontology-plan.md) | 온톨로지 pivot 정본 + 교수 원문 + 미팅 §7 | 정본 |
| [`context-map.md`](context-map.md) | 결정(D1–D11)·팀·방향·열린 질문 | 현행 |
| [`architecture.md`](architecture.md) | 설계 v3 (4에이전트 + 온톨로지 §4.5) | 현행 |
| [`transparency.md`](transparency.md) | 모델·데이터·RAG·트레이싱 정본 | 현행 |
| [`data-inventory.md`](data-inventory.md) | 전체 데이터·자료 지도 | 현행 |
| [`roadmap.md`](roadmap.md) | 완성 체크·마일스톤 | 현행 |
| [`validation-design.md`](validation-design.md) | H2 검증 설계 | 현행 |
| [`worklog.md`](worklog.md) | 시간순 작업 기록(연대기 진실) | 상시 |
| [`research-llm-cpx-sota.md`](research-llm-cpx-sota.md) | 학술 SOTA 근거 | 참고 |
| [`competitor-meditutor.md`](competitor-meditutor.md) | 상용 참고(경쟁 아님) | 참고 |

**코드:** `src/cpx/`(models · llm 어댑터 · rag · agents/{reviewer,grader,patient,debrief} · **ontology_validator** · tracing · harness) · `ontology/chest_pain.yaml` · `scripts/`(ingest · yaml_to_cypher/html · aggregate_validation) · `web/adjudication/`. 실행 = `PYTHONPATH=src .venv/bin/python ...`.

**팀:** 임선주 PI · 이혜윤 공동PI · **박정빈(온톨로지 결정권자 👑)** · 채원우(① 생성·전처리) · 조호영(음성·UI·학사) · 민성(온톨로지) · **김용하(전체 구현)**. **미팅 = 7/2(목) 12시 의대 3층 시뮬레이션센터.**
