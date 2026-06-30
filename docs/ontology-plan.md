# CPX 온톨로지·지식그래프 설계 계획서 — 흉통 좁게 시작

> **정본 설계 계획.** 2026-06-30 작성(김용하+Claude+Codex). 박정빈 교수 비전(7/2 미팅) 실행 계획.
> 이전 `ontology-meeting-prep.md`(v1 본문 + 교정 레이어가 겹쳐 혼란)를 **대체·통합**. 가치 내용(개념·미팅 Q&A·리스크) 전부 흡수.
> 프로젝트 본질·아키텍처 정본 = `AGENTS.md`·`architecture.md`. 모델·데이터 정본 = `transparency.md`.

---

## 0. 목표 · 대원칙

👑 **박정빈 교수 안 = 정본·목표.** 우리 일 = 그 뜻을 **정확히 해석해 충실히 실행**. 대안을 밀거나 반박하는 게 아니다. **최대 리스크 = 그의 의도를 오해하는 것.** "작게 시작(흉통·YAML)"은 *그 비전에 가장 빠르고 정확히 도달하는 수단*이지 다른 안이 아니다. 시점·범위가 갈리면 우리가 정하지 말고 **교수님께 확인**(§7).

- **목표:** 의학 지식을 **온톨로지로 설계 → 지식그래프**로 만들고, 그 그래프가 **CPX 사례 생성의 뼈대**(반드시 포함할 요소를 강제)가 되어 **누락·날조를 줄인 사례**를 만든다. 정제지식은 wiki로 담는다.
- **학술 엄밀성(프로젝트 핵심):** 과대주장 금지. "근거 기반 생성"이라 주장하려면 *측정*(필수요소 누락률·모순율·교수 accept율) 먼저.
- **좁게 시작:** 48주증상 전체 ❌ → **흉통 1개 주증상**부터(§4). Neo4j/풀 GraphRAG는 그다음, 시점은 교수님 결정.

---

## 1. 개념 좌표 (참조용 — 헷갈리면 여기로)

- **온톨로지(설계) ⊂ 지식그래프(설계+데이터) ⊂ Neo4j(그릇).** 온톨로지=타입·관계 스키마, 지식그래프=그걸 채운 점·선 전체, Neo4j=그걸 저장·질의하는 DB 제품. → **설계는 지금, Neo4j는 교수 결정 시점.**
- **지식 전달 역할분담:** 교과서 18권 = **RAG**(현행) / CPX 형식·루브릭 등 정제지식 = **LLM wiki·롱컨텍스트** / 원인-증상-질환 **관계·감별·생성뼈대 = 지식그래프**. 셋은 경쟁 아니라 보완(크기·안정성·관계여부로 라우팅).
  - **RAG = 조연(축소 중).** 정제·안정 지식은 wiki/그래프가 거의 다 먹는다. RAG는 *"통째로 못 올릴 만큼 큰 교과서"* 라는 한 군데에만 남는다 — ① 거대 교과서 깊은 임상사실, ② **그래프 빌드 재료**(트리플의 `source_id` 근거를 교과서에서 찾음), ③ 그래프 빈 구간 임시 보조. 흉통 그래프가 교수 검증으로 차오를수록 RAG 비중은 더 준다.
- **"근거 갖고 생성" = 그래프가 사례 필수요소를 *강제*** (검색해서 참고로 보여주는 RAG와 다름). 미팅에선 "Pattern A/B" 같은 내부 용어 대신 *"그래프가 필수요소를 강제한다"*로 말한다.
- **지식그래프(구조, 작아도 가치) ≠ GraphRAG(큰 코퍼스 검색 시스템).** 우리가 원하는 건 **앞엣것**(작은 흉통 그래프를 생성 뼈대로). GraphRAG의 무거운 검색 파이프라인은 코퍼스가 거대해질 때까지 불필요.
- **LangGraph(우리 코드의 흐름제어) ≠ 지식그래프(교수님 Neo4j).** 둘 다 'graph'라 헷갈림 — 문서·미팅에서 구분.

---

## 2. 전체 설계 구조

### 2.1 엔티티 (주증상-중심 — 질환명이 아니라 주증상·수행항목이 축)

| 계층 | 엔티티 | 표준 재사용 | 자체 구축 |
|---|---|---|---|
| 입구 | `ChiefComplaint`(주호소) · `CpxStationMeta`(48주증상·시간·난이도·task·PPI) | 표준 없음 | CPX 출제 구조 |
| 질환 | `Disease` | MONDO · SNOMED CT | 주증상별 출제범위·부산대 case id |
| 표현형 | `Symptom`(주관·환자호소) · `Sign`(객관·진찰소견) | SNOMED CT · HPO | 한국어 환자표현·학생질문 트리거 |
| 위험 | `RiskFactor` · `RedFlag`(단순사례 금기) | SNOMED CT | CPX red flag 목록 |
| 감별 | `DifferentialDiagnosis` | SNOMED/MONDO | "혼동 유발 감별" 우선순위 |
| 검사 | `Test` · `Finding` | LOINC · SNOMED CT | "시행해야 할 진찰/검사" |
| 관리 | `Treatment` · `Medication` · `EducationItem` | RxNorm · SNOMED CT | 학생에 요구되는 설명 문구 |
| 채점 | `ChecklistItem`(1 행동 단위) · `PpiRubric` | **표준 없음** | 부산대 체크리스트·PPI 루브릭 |

### 2.2 관계
`Disease -has_symptom→ Symptom` · `-has_sign→ Sign` · `-has_risk_factor→ RiskFactor` · `-has_red_flag→ RedFlag` · `-differential_of→ Disease` · `-indicated_test→ Test` · `-treated_by→ Treatment` · `Symptom -discriminates_between→ Disease/Disease` · `ChecklistItem -assesses→ Symptom/Action`

### 2.3 엣지 속성 (3종 — 단순 `has_symptom`만이면 "기침=폐렴" 얕은 그래프)
- **임상:** `frequency` · `sensitivity` · `specificity` · `pathognomonic`(있으면 거의 확진) · `is_discriminating`(감별을 가르나) · `severity` · `onset` · `typical_age/sex`
- **CPX 전용:** `cpx_required`(필수 포함) · `student_visible` · **`disclose_if_asked`**(물어야만 답) · `spontaneous_disclosure_allowed`(과공개 방지)
- **거버넌스(재현성):** `source_id`(근거 출처) · `evidence_level` · `review_status` · `professor_approved`

### 2.4 표준 재사용 + 한국어 로컬레이어
- **재사용(바퀴 재발명 금지):** 질환=MONDO · 증상/징후=HPO+SNOMED CT · 검사=LOINC · 약=RxNorm. (LLM이 표준용어를 알아 추출 정확↑)
- **한국 SNOMED 현실:** 한국은 **2020년 SNOMED International 39번째 회원국**. 국내 기관은 **한국보건의료정보원(NRC) 통해 추가비용 없이** 활용 안내 → "라이선스 비용" 질문에 답 가능.
- **자체(표준에 없음):** 한국어 환자표현(`ko_patient_phrase`)·학생질문 동의어 · CPX 채점항목 · 과공개 규칙 · 오답유도 감별.

### 2.5 저장: **YAML = 정본(master) + Neo4j = 시각화 뷰 (한 방향 렌더)**
- **`ontology/chest_pain.yaml` = 단일 정본.** 편집·검증·버전관리는 전부 여기서 — 교수가 텍스트로 직접 고침 · git diff로 변경추적(재현성) · `validator`가 `required_symptoms` 등을 기계 검사 · 인프라 0.
- **Neo4j = 보여주는 거울(바로 사용, 시각화 목적).** 스크립트가 `YAML → Neo4j` 한 방향으로 렌더 → Neo4j Browser로 교수님께 *살아있는 흉통 그래프*를 띄움. **Neo4j에서 손으로 편집 안 함**(동기화 깨짐 방지). 산출: `scripts/yaml_to_cypher.py`(→ cypher-shell 로드) + 서버 없이 여는 `scripts/yaml_to_html.py`(→ vis-network 인터랙티브 HTML).
- *각자 잘하는 것만: YAML이 진실(검증가능), Neo4j가 거울(시각화). "Neo4j 조기 도입" 운영·동기화 리스크는 한 방향 렌더로 회피.* (교수님이 Neo4j를 *정본*으로 원하시면 §7 확인 포인트.)

---

## 3. 생성 파이프라인 (그래프-스캐폴드 + validator)

그래프가 "문학적 생성"을 하는 게 아니라 **포함해야 할 의학·CPX 요소를 제약**한다.

1. **질환 노드 선택** — 흉통 → 대표진단 1 + 주요감별 4
2. **서브그래프 추출** — 그 질환의 required_symptoms·discriminators·red_flags·checklist·education 순회
3. **제약 걸어 LLM에 명령** — "이 시나리오를 쓰되 **반드시 포함**: [필수증상·감별단서·red flag]. **과공개 금지**: [disclose_if_asked 항목은 물어야만]"
4. **LLM 서사화(살 채움)** — 환자 나이·배경·말투로 자연스러운 사례 텍스트
5. **validator(코드) 검사** — 필수요소 다 들었나·과공개 어겼나·모순 없나 → 통과/실패 리포트

**기존 시스템과의 관계:** 현재 멀티에이전트(①생성→②심사→③가상환자→④채점) + LangGraph(흐름제어)는 유지. 온톨로지/그래프는 **①생성의 입력 제약 + 사후 validator**로 들어간다. RAG(교과서)는 그대로 보조 근거. → *추가 레이어이지 교체 아님.*

---

## 4. 흉통 좁은 시작 — 구체 설계

### 4.1 `ontology/chest_pain.yaml` (질환 5개 — ⚠️ 교수 검증 전 초안)

> `review_status: draft` · `professor_approved: false` — 임상 내용은 **임선주/박정빈 교수 검증 후** 확정. 아래는 *구조를 보이는 스켈레톤*.

```yaml
chief_complaint: chest_pain          # 흉통
meta:
  station_minutes: 10
  ppi_assessed: true
  review_status: draft
  professor_approved: false
diseases:
  # ── 대표진단 ──────────────────────────────
  - id: acute_coronary_syndrome      # 급성 관상동맥 증후군
    role: primary
    required_symptoms:               # 반드시 포함(cpx_required)
      - chest_pressure               # 쥐어짜는/압박감
      - exertional_or_rest_onset
    discriminators:                  # 감별을 가르는 단서(is_discriminating)
      - radiation_to_left_arm_or_jaw
      - diaphoresis
      - dyspnea
    red_flags:                       # 응급 — 단순사례 금기
      - hypotension
      - syncope
    risk_factors: [hypertension, diabetes, smoking, dyslipidemia, family_history]
    checklist_items:                 # 채점(1 행동 단위)
      - ask_onset_duration
      - ask_character
      - ask_radiation
      - ask_aggravating_relieving
      - ask_associated_sx            # 호흡곤란/발한/오심
      - ask_cardiac_risk_factors
    physical_exam: [vital_signs, heart_auscultation, lung_auscultation]
    tests: [ecg_12lead, cardiac_troponin]
    education_items: [explain_need_for_ecg_troponin, explain_emergency_nature]
    disclosure:
      spontaneous: [chest_pressure]               # 환자가 먼저 말함
      disclose_if_asked: [radiation_to_left_arm_or_jaw, diaphoresis, risk_factors]
    source_id: TODO_harrison_or_kr_guideline

  # ── 주요 감별 4 (구조만, 임상은 교수 검증) ──
  - id: gerd                          # 역류성식도염
    role: differential
    required_symptoms: [retrosternal_burning, relation_to_meals_or_lying_down]
    discriminators: [acid_regurgitation, relieved_by_antacid, no_exertional_relation]
    red_flags: [dysphagia, weight_loss, gi_bleeding]   # alarm features
    checklist_items: [ask_relation_to_meals, ask_regurgitation, ask_antacid_response, ask_alarm_features]

  - id: musculoskeletal_chest_pain    # 근골격계 흉통 (배제적)
    role: differential
    required_symptoms: [localized_pain, reproducible_on_movement]
    discriminators: [pain_on_chest_wall_palpation, worse_with_breathing_or_motion, strain_history]
    red_flags: []
    checklist_items: [ask_palpation_reproducibility, ask_movement_relation, ask_trauma_hx, exam_chest_wall]

  - id: panic_anxiety                 # 공황/불안
    role: differential
    required_symptoms: [chest_tightness, palpitations]
    discriminators: [hyperventilation, paresthesia, situational_trigger, young_low_risk]
    red_flags: [must_exclude_cardiac_first]
    checklist_items: [ask_anxiety_sx, ask_triggers, ask_pattern, exclude_red_flags]

  - id: aortic_dissection             # 대동맥박리 (can't-miss)
    role: differential
    required_symptoms: [sudden_tearing_pain, maximal_at_onset]
    discriminators: [radiation_to_back, bp_differential_between_arms, hypertension_hx]
    red_flags: [bp_differential, neurologic_deficit, syncope, hypotension]
    checklist_items: [ask_onset_abruptness, ask_tearing_quality, ask_radiation_to_back, measure_bp_both_arms]
    tests: [ct_angiography]
```

### 4.2 validator 검사 항목 (생성 사례 → 통과/실패)
1. **required coverage** — 선택 질환의 `required_symptoms` 가 사례 텍스트에 다 있나?
2. **red-flag presence** — 의도한 red flag 가 (있어야 할 사례면) 들어갔나?
3. **discriminator presence** — 감별 단서가 최소 N개 포함됐나?
4. **disclosure 규칙** — `disclose_if_asked` 항목이 *환자가 먼저* 누설되지 않았나(과공개 위반)?
5. **contradiction** — 같은 사실의 모순 진술 없나?
6. **checklist mapping** — 사례가 채점 체크리스트와 매핑되나?
→ 출력 = 항목별 pass/fail + 누락 목록 리포트.

---

## 5. 2주 MVP 계획 (7/2 미팅 후, 교수 확인 후 착수)

### ✅ 지금 만든 것 (시각화 데모 — 미팅에 바로)
- `ontology/chest_pain.yaml` — 정본(질환5, draft) · `ontology/chest_pain.cypher` — 자동생성
- `docs/chest_pain-graph.html` — **서버 0, 브라우저로 바로 여는 인터랙티브 그래프** · `docs/chest_pain-graph.png` — 스샷(임베드용)
- 스크립트: `scripts/{ontology_graph,yaml_to_cypher,yaml_to_html}.py` + `graph_shot.js`
- **Neo4j 라이브 검증 완료**: docker neo4j → 65노드·70엣지 로드 → 타입 쿼리("ACS 감별질환", "red flag 있는 질환") 동작 확인.

```bash
# 재현: YAML 고치면 그래프 자동 갱신 (한 방향 렌더)
.venv/bin/python scripts/yaml_to_html.py        # → docs/chest_pain-graph.html (그냥 열기)
.venv/bin/python scripts/yaml_to_cypher.py      # → ontology/chest_pain.cypher
# Neo4j 시각화(인터랙티브, 교수 데모용):
docker run -d --name cpx-neo4j -p7474:7474 -p7687:7687 -e NEO4J_AUTH=neo4j/cpxneo4j2026 neo4j:5
cat ontology/chest_pain.cypher | docker exec -i cpx-neo4j cypher-shell -u neo4j -p cpxneo4j2026
# → http://localhost:7474 (neo4j / cpxneo4j2026) 에서 그래프 탐색
```

### 남은 산출물 (교수 확인 후):
**산출물 4개면 충분:**
1. `ontology/chest_pain.yaml` (위 §4.1, 교수 검증 반영)
2. 질환 5개(대표 1 + 감별 4) 완성 카드
3. validator (`src/cpx/ontology_validator.py` 등) — §4.2 검사
4. 그 카드로 생성한 **사례 3개 + validator 리포트**

**2주 목표 = 그래프DB가 아니라** "교수가 볼 수 있는 구조화된 CPX 지식 카드 + 그 카드로 생성한 사례 + validator 리포트". (시작 방식만 제안 — Neo4j 전환 시점은 교수님 결정.)

**평가지표:** required coverage · red-flag omission rate · differential plausibility · contradiction rate · 과공개율 · 교수 accept/minor/major/reject · (확대 시 kappa/ICC).

---

## 6. 리스크 · kill 조건 (Codex 적대 레드팀)

| 무엇이 문제 | 왜 위험 | kill 조건 |
|---|---|---|
| Neo4j 조기 도입 | 그래프DB 운영이 연구질문보다 커짐 | 2주 내 교수승인 사례 3개 못 만들면 Neo4j 보류 |
| "근거 기반 생성" 과대주장 | 틀린 triple = 근거 아닌 오류 전파 | **source 없는 triple 사용 금지** |
| 환각 트리플 (LLM 자동추출) | 없는 질환-증상 관계 날조 → 하류 전파 | **무작위 50 triple precision <0.9면 자동추출 폐기**, 전 트리플 교수 검증 |
| 표준만 가져오면 CPX 해결 착각 | SNOMED/HPO는 채점·과공개·PPI 모름 | CPX 체크리스트 커버리지 <80%면 자체계층 우선 |
| 질환-중심 그래프 | CPX는 주증상·수행항목 중심 | Disease-only schema면 중단 |
| 평가 없는 그래프 데모 | 예쁜 그래프가 품질개선 증거로 오해 | **정량 before/after 없으면 "연구 성과" 주장 금지** |
| 로컬 35B 조기 주력화 | 모델품질·긴context·KV비용이 연구 삼킴 | kappa CI가 API 대비 열등하면 로컬은 후속 |

---

## 7. 미팅 메모 (7/2)

**자세 = 박정빈 교수 안을 정확히 해석해 실행** (반박·대안 아님). 갈리는 지점은 우리가 정하지 말고 교수님께 물어 의도 확정.

**A. 교수님께 확인할 해석 포인트 (오해 방지):**
1. **"근거 갖고 생성"** = 그래프가 필수요소(증상·감별·red flag)를 강제해 누락·날조를 막는 것 — 맞습니까?
2. **Neo4j 바로** vs **흉통 1개를 YAML 카드로 먼저 검증 뒤 이전** — 어느 쪽으로 할까요? (둘 다 교수님 결정대로)
3. **엔티티 범위** = 질환만이 아니라 주증상·체크리스트·감별·과공개 규칙까지 — 맞습니까?
4. 온톨로지 인스턴스(트리플)는 **LLM 추출 후 교수 검증**으로 채우는 방식 OK입니까?

**B. 예상질문 → 답 (약점 명시):**
- "엔티티 뭘로?" → 주증상-질환-증상/징후-감별-체크리스트-교육/PPI (§2.1). *약점: 48주증상 전체 매핑 아직.*
- "SNOMED 쓰면 한국어 해결?" → 아니다, 한국어는 별도 로컬레이어. *약점: synonym 구축 비용.*
- "Neo4j 꼭?" → 2주 MVP엔 불필요, 카드로 시작 후 이전(시점=교수님). 
- "근거 기반 입증?" → source-linked coverage·모순율·교수 accept율 측정 후. *약점: gold data 부족.*
- "GraphRAG가 RAG보다 낫다는 증거?" → 일반 근거는 있으나 CPX 직접근거 없음, ablation으로 검증.
- "환자 과공개하면?" → `disclose_if_asked`·`spontaneous_disclosure_allowed`로 제어.
- "논문 주장 범위?" → "온톨로지+validator가 필수요소 누락·모순을 줄였는가"까지. "AI=교수 동등"은 주장 안 함.

**C. 차별점(어필):** CPX/OSCE를 지식그래프로 **생성**한 논문 아직 없음 + 부산대 실데이터 → 그래프가 필수요소를 강제하는 생성 = 신규 기여.

**D. 멘트:**
> "교수님 말씀대로 온톨로지 지식그래프로 사례를 근거 있게 생성하는 방향으로 가겠습니다. SNOMED 같은 표준을 참조하되 핵심은 한국 CPX 수행항목과 환자 응답정책으로 잡고, 먼저 흉통 1개에 대해 질환-증상-감별-체크리스트 카드를 만들어 생성 사례의 누락·모순이 줄어드는지 검증하겠습니다. Neo4j 전환 시점은 교수님 원하시는 대로 정해 주시면 그대로 따르겠습니다."

---

## 8. 핵심 출처 (2024-2026)
- GraphRAG: MS arXiv:2404.16130(2024-04) · LazyGraphRAG · Neo4j GraphRAG Python docs
- LLM wiki: Karpathy gist(2026-04) · DeepWiki/Cognition(2025-04) · vector-RAG vs wiki arXiv:2605.18490(2026-05, ~21x 비용)
- 임상 KG 생성: CLINGEN(ACL2024) · MedKGEval(arXiv:2510.12224) · ICD-10+SNOMED-CoT(arXiv:2512.05256) · MedKGI(arXiv:2512.24181)
- 온톨로지: SNOMED CT(한국 2020 39번째 회원국, NRC) · HPO · MONDO · LOINC · RxNorm · AutoRD(JMIR 2024) · KG construction survey(arXiv:2510.20345)
- 모델: Qwen3-30B-A3B(256k MoE) · TurboQuant(Google 2025, KV캐시 압축)
