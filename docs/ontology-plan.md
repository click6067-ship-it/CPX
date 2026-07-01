# CPX 온톨로지·지식그래프 설계 계획서 — 흉통 좁게 시작

> **정본 설계 계획.** 2026-06-30 초안 · **2026-07-01 교수 원문 반영·갱신**(개발 담당+Claude+Codex). 지도교수 비전 실행 계획.
> 이전 `ontology-meeting-prep.md`(v1 본문 + 교정 레이어가 겹쳐 혼란)를 **대체·통합**. 가치 내용(개념·미팅 Q&A·리스크) 전부 흡수.
> 프로젝트 본질·아키텍처 정본 = `AGENTS.md`·`architecture.md`. 모델·데이터 정본 = `transparency.md`.

---

## 0. 목표 · 대원칙

👑 **지도교수 안 = 정본·목표.** 우리 일 = 그 뜻을 **정확히 해석해 충실히 실행**. 대안을 밀거나 반박하는 게 아니다. **최대 리스크 = 그의 의도를 오해하는 것.** "작게 시작(흉통·YAML)"은 *그 비전에 가장 빠르고 정확히 도달하는 수단*이지 다른 안이 아니다. 시점·범위가 갈리면 우리가 정하지 말고 **교수님께 확인**(§7).

> **설계 지시 (정본, 2026-07-01):** 온톨로지를 적용 — **Neo4j 지식그래프로 구조화된 지식 내에서 LLM이 근거를 갖고 사례를 생성**(아무렇게나 X). 기술 요지 = 아래 목표 + 숙제 7항목 표. 이 지시를 충실히 실행하고 결과를 측정한다(반박·대체 아님, 보강 가능).

**해석 (오해 방지):** 원문의 **LLM wiki(마크다운 정제지식) · 지식그래프(Neo4j 타입관계) · RAG(큰 교과서) · 로컬 35B 롱컨텍스트** 는 모두 **지도교수의 단일 비전**이다 — 팀원·팀 발언은 그 *전달*이지 별개 의견이 아니다. 우리 자세 = 이 스택을 **충실히 실행**하고, 그 결과(필수요소 누락·모순·교수 accept율)를 **측정**한다. *(측정은 우리 산출물의 학술 정직성을 위한 것 — 교수님 기술선택에 대한 저항이 아니다. 비전 실행과 측정은 양립한다.)*

- **목표:** 의학 지식을 **온톨로지(원인–증상–질환 의미구조)로 설계 → 지식그래프**로 만들고, 그 그래프가 **CPX 사례 생성의 뼈대**(반드시 포함할 요소를 강제)가 되어 **근거 있는(누락·날조 줄인) 사례**를 만든다. 정제지식은 **LLM wiki(마크다운·롱컨텍스트)** 로 담는다.
- **교수님 숙제 (원문 7항목 — 정본 체크리스트, "각자 생각해올 것"):** blueprint·AGENTS도 이 표를 참조 — 부분집합 축약 금지.

| # | 교수 원문 | 우리 해석 | 대응 | 상태 |
|---|---|---|---|---|
| 1 | "엔티티를 뭘로" | CPX 엔티티 설계(주증상-중심) | §2.1 | 초안, §7 확인 |
| 2 | "Keyword 기반 ontology 디자인" | 키워드-앵커(한국어 환자표현·질문 트리거) | §2.4 | 반영 |
| 3 | "Graph 연결이 아닌 온톨로지 — 원인·증상·질환" | 의미 온톨로지(단순 링크 아님) | §2.1·§2.2 | 반영, 원인축 §7 |
| 4 | "Markdown으로 CPX 사례 변환" | **(a) 사례→markdown 변환**(ingest 연계) + **(b) 정제지식 wiki** — 별개 산출물 | §1·ingest | 갈래 분리, §7 확인 |
| 5 | "35B Q4 · 256k↑ · TurboQuant" | 로컬 서빙·양자화·롱컨텍스트 | §5.5 | 실행계획 착수 |
| 6 | "LLM wiki 처럼" | 마크다운 정제지식·롱컨텍스트 | §1·§5.5 | 반영 |
| 7 | "Skill.MD" | CPX 생성 절차를 재사용 Skill 지시파일(.md)로 | §5.5 | 미해석 → §7 확인 |

- **학술 엄밀성(프로젝트 핵심):** 과대주장 금지. "근거 기반 생성"이라 *주장*하려면 *측정*(필수요소 누락률·모순율·교수 accept율)이 먼저.
- **좁게 시작:** 48주증상 전체 ❌ → **흉통 1개 주증상**부터(§4). Neo4j 전환·풀 스택 주력화 **시점은 교수님 결정**(우리가 정하지 않음, §7).

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

> **의미 축 = 원인–증상–질환 (교수님 원문 "Graph 연결이 아닌 온톨로지 — 원인·증상·질환").** 아래 계층이 그 축을 CPX용으로 구체화한 것: **원인**=`RiskFactor`/병태생리(etiology) → **증상·징후**=`Symptom`/`Sign` → **질환**=`Disease`, 이를 **주증상(`ChiefComplaint`)** 입구로 묶는다. *단순 `has_symptom` 링크 그래프가 아니라 감별·강제·과공개 규칙을 담은 의미 온톨로지*(→ §2.3 엣지속성). *(원문 "원인"을 `RiskFactor`와 별개의 `Cause/Etiology` 엔티티로 세분할지는 §7 교수 확인 포인트.)*

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
> **원인축 — ⚠️ 아래는 내가 제안하는 것(교수 확정·채택 아님, §7):** 원문 "원인·증상·질환" 강조를 반영해 관계 `-caused_by→ Cause/Etiology` · `RiskFactor -predisposes_to→ Disease` 추가를 **제안**. `RiskFactor`(소인·위험인자)와 `Cause/Etiology`(병태생리 원인)는 임상적으로 다르므로, 원인을 `RiskFactor` 하나로 볼지 별도 엔티티+관계로 세분할지 **§7 교수 확인**(관계명·채택 여부 미정).

### 2.3 엣지 속성 (3종 — 단순 `has_symptom`만이면 "기침=폐렴" 얕은 그래프)
- **임상:** `frequency` · `sensitivity` · `specificity` · `pathognomonic`(있으면 거의 확진) · `is_discriminating`(감별을 가르나) · `severity` · `onset` · `typical_age/sex`
- **CPX 전용:** `cpx_required`(필수 포함) · `student_visible` · **`disclose_if_asked`**(물어야만 답) · `spontaneous_disclosure_allowed`(과공개 방지)
- **거버넌스(재현성):** `source_id`(근거 출처) · `evidence_level` · `review_status` · `professor_approved`

### 2.4 표준 재사용 + 한국어 로컬레이어
- **재사용(바퀴 재발명 금지):** 질환=MONDO · 증상/징후=HPO+SNOMED CT · 검사=LOINC · 약=RxNorm. (LLM이 표준용어를 알아 추출 정확↑)
- **한국 SNOMED 현실:** 한국은 **2020년 SNOMED International 39번째 회원국**. 국내 기관은 **한국보건의료정보원(NRC) 통해 추가비용 없이** 활용 안내 → "라이선스 비용" 질문에 답 가능.
- **자체(표준에 없음):** 한국어 환자표현(`ko_patient_phrase`)·학생질문 동의어 · CPX 채점항목 · 과공개 규칙 · 오답유도 감별.
- **keyword 기반 설계 (교수님 숙제②):** 온톨로지 노드를 **키워드-앵커**로 — 각 엔티티가 *한국어 환자표현·학생질문 트리거 키워드 집합*을 갖고, validator가 생성 사례 자유텍스트에서 그 키워드/동의어를 매칭(현행 `ontology_validator`가 이미 이 방식). 표준 코드(SNOMED 등)=*기계 상호운용* 축, keyword 레이어=*한국어 CPX 매칭* 축 — **두 축 병행**(어느 쪽을 정본으로 볼지는 §7 확인).

### 2.5 저장: **YAML = 정본(master) + Neo4j = 시각화 뷰 (한 방향 렌더)**
- **`ontology/chest_pain.yaml` = 단일 정본.** 편집·검증·버전관리는 전부 여기서 — 교수가 텍스트로 직접 고침 · git diff로 변경추적(재현성) · `validator`가 `required_symptoms` 등을 기계 검사 · 인프라 0.
- **Neo4j = 보여주는 거울(바로 사용, 시각화 목적).** 스크립트가 `YAML → Neo4j` 한 방향으로 렌더 → Neo4j Browser로 교수님께 *살아있는 흉통 그래프*를 띄움. **Neo4j에서 손으로 편집 안 함**(동기화 깨짐 방지). 산출: `scripts/yaml_to_cypher.py`(→ cypher-shell 로드) + 서버 없이 여는 `scripts/yaml_to_html.py`(→ vis-network 인터랙티브 HTML).
- **교수님 지시대로 Neo4j로 그래프를 그린다.** 다만 *편집·검증의 정본*을 YAML로 두면 git diff·기계검증·재현성이 쉬워, **한 방향 렌더(YAML→Neo4j)로 시작**해 운영·동기화 부담을 줄인다. *각자 잘하는 것: YAML=진실(검증가능), Neo4j=그 렌더(시각화·탐색).* **Neo4j를 정본(직접 편집)으로 두는 것도 교수님이 원하시면 그 방향으로** — §7 확인 포인트.

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

> `review_status: draft` · `professor_approved: false` — 임상 내용은 **PI/지도교수 검증 후** 확정. 아래는 *구조를 보이는 스켈레톤*.

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

## 5. 2주 MVP 계획 (설계 리뷰 후, 교수 확인 후 착수)

### ✅ 지금 만든 것 (시각화 데모 — 미팅에 바로)
- `ontology/chest_pain.yaml` — 정본(질환5, draft) · `ontology/chest_pain.cypher` — 자동생성
- `docs/chest_pain-graph.html` — **서버 0, 브라우저로 바로 여는 인터랙티브 그래프** · `docs/chest_pain-graph.png` — 스샷(임베드용)
- 스크립트: `scripts/{ontology_graph,yaml_to_cypher,yaml_to_html}.py` + `graph_shot.js`
- **Neo4j 라이브 검증 완료**: docker neo4j → 65노드·70엣지 로드 → 타입 쿼리("ACS 감별질환", "red flag 있는 질환") 동작 확인.

```bash
# 재현: YAML 고치면 그래프 자동 갱신 (한 방향 렌더)
.venv/bin/python scripts/yaml_to_html.py        # → docs/chest_pain-graph.html (그냥 열기)
.venv/bin/python scripts/yaml_to_cypher.py      # → ontology/chest_pain.cypher
# Neo4j 시각화(인터랙티브, 교수 데모용): IPv4 loopback 바인딩(아래 ⚠️ 참조)
docker run -d --name cpx-neo4j -p127.0.0.1:7474:7474 -p127.0.0.1:7687:7687 \
  -e NEO4J_AUTH=neo4j/cpxneo4j2026 \
  -e NEO4J_server_default__advertised__address=127.0.0.1 \
  -e NEO4J_server_bolt_advertised__address=127.0.0.1:7687 neo4j:5
cat ontology/chest_pain.cypher | docker exec -i cpx-neo4j cypher-shell -u neo4j -p cpxneo4j2026
# → http://127.0.0.1:7474 (neo4j / cpxneo4j2026) 에서 탐색  ← localhost 말고 127.0.0.1!
```
> ⚠️ **WSL mirrored 모드 함정: `localhost`(→IPv6 `::1`) 안 됨, `127.0.0.1`(IPv4) 써야 됨.** mirrored 모드가 IPv6 loopback SYN을 블랙홀해서 `localhost:7474`는 "TCP는 붙는데 데이터 timeout". 위처럼 IPv4 loopback에 바인딩 + advertised=127.0.0.1로 고정하면 Neo4j Browser가 bolt도 자동으로 127.0.0.1로 붙음. (검증: Windows `Invoke-WebRequest 127.0.0.1:7474`=200, `localhost`=timeout.)

### 남은 산출물 (교수 확인 후):
**산출물 4개면 충분:**
1. `ontology/chest_pain.yaml` (위 §4.1, 교수 검증 반영)
2. 질환 5개(대표 1 + 감별 4) 완성 카드
3. validator (`src/cpx/ontology_validator.py` 등) — §4.2 검사
4. 그 카드로 생성한 **사례 3개 + validator 리포트**

**2주 목표 = 그래프DB가 아니라** "교수가 볼 수 있는 구조화된 CPX 지식 카드 + 그 카드로 생성한 사례 + validator 리포트". (시작 방식만 제안 — Neo4j 전환 시점은 교수님 결정.)

**평가지표:** required coverage · red-flag omission rate · differential plausibility · contradiction rate · 과공개율 · 교수 accept/minor/major/reject · (확대 시 kappa/ICC).

### 5.5 로컬 모델 스택 · Skill.MD (교수 숙제 4·5·6·7 — 서지 아닌 실행 계획)
교수님이 명시한 모델·형식 축을 §8 서지에 두지 않고 실행 계획으로 둔다:
- **로컬 35B Q4 · 256k · TurboQuant (숙제 5):** 후보 `Qwen3-30B-A3B`(256k MoE) 등 → **Q4 양자화 로컬 서빙** · **256k+ 컨텍스트 실측 확인**(교수 "256k 이상 최대로 확인") · **TurboQuant**(KV캐시 압축)으로 롱컨텍스트 메모리 절감. 착수 = 서빙 PoC + 컨텍스트 한계 실측.
- **LLM wiki (숙제 6):** CPX 형식·루브릭·흉통 임상을 **마크다운 위키**로 정제 → 로컬 35B가 **롱컨텍스트로 통째로** 읽음(RAG 조각검색 아님). 흉통 wiki부터(다음 스텝 ①).
- **markdown CPX 사례 변환 (숙제 4):** 실제 CPX 사례를 **markdown으로 변환**(기존 `scripts/ingest.py` hwp→구조화 연계) → wiki·롱컨텍스트 입력. ⚠️ *지식 wiki(6)와 사례 변환(4)은 별개 산출물 — 혼동 금지.*
- **Skill.MD (숙제 7):** CPX 사례 생성 절차(온톨로지 제약·과공개 규칙·형식)를 **재사용 가능한 Skill 지시파일(.md)** 로 규정 — 에이전트가 매번 읽어 일관 생성. *해석 미확정 → §7 교수 확인.*
- **초기 검증 = API 병행:** 로컬 품질을 API(gpt-5.5 등)와 **동일 프롬프트로 비교 측정**(누락률·모순율). 로컬 주력화 시점 = 교수님 결정. *(측정은 정직성용 — 로컬 방향 저항 아님.)*

---

## 6. 리스크 · kill 조건 (Codex 적대 레드팀)

| 무엇이 문제 | 왜 위험 | kill 조건 |
|---|---|---|
| Neo4j **운영·동기화**가 연구질문을 삼킴 | 교수 지시대로 Neo4j는 도입 — 단 DB 운영이 본질(근거 생성)보다 커지면 곁길 | **YAML 정본 + 한 방향 렌더로 운영부담 최소화**(Neo4j 시각화부터, 정본화 시점=교수님). *폐기 대상은 Neo4j가 아니라 동기화 과부하* |
| "근거 기반 생성" 과대주장 | 틀린 triple = 근거 아닌 오류 전파 | **source 없는 triple 사용 금지.** ⚠️ 현재 `chest_pain.yaml`은 `source_id: TODO`(draft) → **source 채우기 전엔 "근거 기반" 주장 안 함**; 데모는 "필수요소 강제" 효과까지만 |
| 환각 트리플 (LLM 자동추출) | 없는 질환-증상 관계 날조 → 하류 전파 | **무작위 50 triple precision <0.9면 자동추출 폐기**, 전 트리플 교수 검증 |
| 표준만 가져오면 CPX 해결 착각 | SNOMED/HPO는 채점·과공개·PPI 모름 | CPX 체크리스트 커버리지 <80%면 자체계층 우선 |
| 질환-중심 그래프 | CPX는 주증상·수행항목 중심 | Disease-only schema면 중단 |
| 평가 없는 그래프 데모 | 예쁜 그래프가 품질개선 증거로 오해 | **정량 before/after 없으면 "연구 성과" 주장 금지** |
| 로컬 35B 품질을 **측정 없이** 주장 | 모델품질·긴 context가 결과를 좌우하는데 미검증 | **측정 전 "로컬로 됐다" 주장 금지** — 로컬 35B는 교수 비전대로 진행하되 초기엔 API 병행 비교로 품질 확인(주력화 시점=교수님). *(kill 대상 = 미측정 주장이지 로컬 방향이 아님)* |

---

## 7. 설계 리뷰 메모

**자세 = 지도교수 안을 정확히 해석해 실행** (반박·대안 아님). 갈리는 지점은 우리가 정하지 말고 교수님께 물어 의도 확정.

**A. 교수님께 확인할 해석 포인트 (오해 방지):**
1. **"근거 갖고 생성"** = 그래프가 필수요소(증상·감별·red flag)를 강제해 누락·날조를 막는 것 — 맞습니까?
2. **Neo4j 바로** vs **흉통 1개를 YAML 카드로 먼저 검증 뒤 이전** — 어느 쪽으로 할까요? (둘 다 교수님 결정대로)
3. **엔티티 범위** = 질환만이 아니라 주증상·체크리스트·감별·과공개 규칙까지 — 맞습니까? (**"원인"을 `RiskFactor`로 볼지 별도 `Cause` 엔티티+관계로 세분할지** 포함 — 교수님 "원인·증상·질환" 강조 반영)
4. 온톨로지 인스턴스(트리플)는 **LLM 추출 후 교수 검증**으로 채우는 방식 OK입니까?
5. **"Markdown으로 CPX 사례 변환"** = (a) *사례 자체를 markdown으로* 변환하는 것인지, (b) *형식·루브릭 정제지식 wiki*를 뜻하는지, 아니면 둘 다인지? (우리는 두 갈래로 준비 — §5.5)
6. **"Skill.MD"** = CPX 생성 절차를 재사용 Skill 지시파일(.md)로 두는 것으로 해석했는데(§5.5), 교수님 의도가 맞습니까?

**B. 예상질문 → 답 (약점 명시):**
- "엔티티 뭘로?" → 주증상-질환-증상/징후-감별-체크리스트-교육/PPI (§2.1). *약점: 48주증상 전체 매핑 아직.*
- "SNOMED 쓰면 한국어 해결?" → 아니다, 한국어는 별도 로컬레이어. *약점: synonym 구축 비용.*
- "Neo4j 꼭?" → **네, 교수님 말씀대로 Neo4j로 그립니다**(이미 65노드 렌더해 봄). 다만 흉통 카드를 **YAML로 먼저 검증**하면 같은 목표에 더 빠름(편집·git추적 쉬움) — YAML 먼저 vs Neo4j 바로는 **교수님 결정대로.**
- "근거 기반 입증?" → source-linked coverage·모순율·교수 accept율 측정 후. *약점: gold data 부족.*
- "GraphRAG가 RAG보다 낫다는 증거?" → 일반 근거는 있으나 CPX 직접근거 없음, ablation으로 검증.
- "환자 과공개하면?" → `disclose_if_asked`·`spontaneous_disclosure_allowed`로 제어.
- "논문 주장 범위?" → "온톨로지+validator가 필수요소 누락·모순을 줄였는가"까지. "AI=교수 동등"은 주장 안 함.

**C. 차별점(어필):** **확인된 범위에선** CPX/OSCE를 지식그래프로 **생성**한 선행연구를 찾지 못함 + 부산대 실데이터 → 그래프가 필수요소를 강제하는 생성 = **신규 기여 가능성**. *(체계적 prior-art 검색은 논문 단계에서 — 단정 회피.)*

**D. 멘트:**
> "교수님 말씀대로 온톨로지 지식그래프로 사례를 근거 있게 생성하는 방향으로 가겠습니다. SNOMED 같은 표준을 참조하되 핵심은 한국 CPX 수행항목과 환자 응답정책으로 잡고, 먼저 흉통 1개에 대해 질환-증상-감별-체크리스트 카드를 만들어 생성 사례의 누락·모순이 줄어드는지 검증하겠습니다. Neo4j 전환 시점은 교수님 원하시는 대로 정해 주시면 그대로 따르겠습니다."

**E. 리허설 보강 (2026-06-30 — validator 구현 + Codex 5R 적대검수 반영):**
- **A 질문 다듬기**(Q1·Q2가 "맞습니까?" yes/no라 동의편향 → *열고 대비*):
  - Q1 → *"'근거 갖고 생성'을 (A) 필수요소 강제(누락·날조 차단) / (B) 각 임상사실에 교과서 출처 부착 — 어느 쪽에 가깝습니까? 둘 다일 수도."* (B 비중 크면 source-linked provenance = 큰 추가작업 → 빌드 갈림.)
  - Q2 → *"Neo4j 바로 vs 카드 먼저, 어느 쪽이든 따릅니다. 권고만 30초: 카드 먼저가 같은 목표에 더 빠름 — 교수가 텍스트로 직접 수정·git 추적·DB운영 0, Neo4j엔 이미 65노드 올려봄."*
- **Q5 추가(검증 노동)**: *"임상 검증은 누가(교수/PI/공동)·시간 얼마나? 그에 맞춰 흉통 검증 분량을 잡겠습니다."* — "교수-검증 그래프" 주장의 실현가능성 핵심.
- **가드레일**: 내부용어(Pattern A/B·스캐폴드·validator) 대신 평이하게 · 반박조 금지 · "AI=교수 필적" 절대 금지(→ "누락·모순 줄이는지 측정"까지) · LangGraph↔지식그래프 혼동 금지 · 모르면 "측정해 말씀드리겠습니다".
- **당일 데모 점검**: 오프라인 HTML(인터넷 불필요·vendored 인라인) · Neo4j는 Windows크롬이면 프록시(127.0.0.1:17474) 1회 확인 · validator는 **합성 clean↔결함** 사례로 시연(실 gold가 fail로 떠 실사례 비판처럼 보이는 것 회피).

**C 보강 — validator 차별점 (구현·Codex 검증됨):** validator가 결정론(LLM 0회)으로 **"환자가 *가졌나*(positive)" vs "학생이 *선별했나*(asked)"를 분리** 측정 + **과공개**(물어야 답할 정보를 환자가 자발 노출)·**필수요소 누락**을 검출. 한국어 부정문("실신은 없었어요"=미보유)·관계부정도 처리. *표준 온톨로지(SNOMED 등)가 못 하는 CPX 고유 규칙.* (임상 내용은 draft — 교수 검증 대상.)
→ 새 확인질문 **Q6**: *"coverage를 '환자가 가졌나' vs '학생이 선별했나' 중 어느 의미로 보십니까?"* (우리 설계는 둘 다 분리 보고 — 교수 의도에 정책만 맞추면 됨.)

---

## 8. 핵심 출처 (2024-2026)
- GraphRAG: MS arXiv:2404.16130(2024-04) · LazyGraphRAG · Neo4j GraphRAG Python docs
- LLM wiki: Karpathy gist(2026-04) · DeepWiki/Cognition(2025-04) · vector-RAG vs wiki arXiv:2605.18490(2026-05, ~21x 비용)
- 임상 KG 생성: CLINGEN(ACL2024) · MedKGEval(arXiv:2510.12224) · ICD-10+SNOMED-CoT(arXiv:2512.05256) · MedKGI(arXiv:2512.24181)
- 온톨로지: SNOMED CT(한국 2020 39번째 회원국, NRC) · HPO · MONDO · LOINC · RxNorm · AutoRD(JMIR 2024) · KG construction survey(arXiv:2510.20345)
- 모델: Qwen3-30B-A3B(256k MoE) · TurboQuant(Google 2025, KV캐시 압축)
