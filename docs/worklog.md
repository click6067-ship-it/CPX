# 작업 로그 (worklog) — Codex 검수용

> 용도(1석3조): **① Codex 적대 검수** · ② 김용하 본인 이해 · ③ 교수님 설명.
> 원칙: 정제·요약(원문 나열 X). 기획 단계부터 기록.

---

## Phase 0 (정의·설계) — 2026-06-17 ~ 06-18

### 진행 요약 (요청 → 한 일 → 결과)

1. **자료 파악 요청** → 임선주 사업계획서(.hwp) + MedQA 레포 정독 → CPX 문제정의·MedQA 구조 파악.
2. **"aristo-mini/MedQA 접목, 거시 구조화"** → aristo-mini 6개 솔버 분석. 결론: **코드 복붙 X, 설계 골격만 오마주**(2017년 코드라 낡음). MedQA의 "텍스트 A↔B 부합도 점수화" 구조 = CPX 채점/사례평가 뼈대와 동일(핵심 통찰).
3. **범위 리프레임** → "MVP" → **"90% 완성품"**(교수 깐깐). 역할 = 팀분담 명목상, **전체 end-to-end 김용하 단독**.
4. **기술 방향 확정** (2026 최신 검색): 새 레포 · 하이브리드 RAG(임베딩+BM25) · 상위모델(Claude/GPT, 결제) · LangGraph · Gemini Live API(음성) · LangSmith · GraphRAG는 고도화 이관.
5. **파일 전체 정독** → `[붙임2]`(사례 스키마, 설사/김선미 예시 완전체), `실기문항저자점검표`(루브릭), `사례개발피드백`×5(정답지·~90사례), `연구문제`(4 Agent별 RQ + 하네스 정의), 회의록×2(역할·결정·리스크), data_clean.zip(교과서18권+문제) → **`context-map.md`** 작성.
6. **deep-research**(110 agent, 27소스, 22 confirmed/3 killed) → **`research-llm-cpx-sota.md`** 작성.
7. **아키텍처 확정** → **`architecture.md`** 작성.

### 핵심 결정 (근거)
- 생성 = **멀티에이전트 + checklist-as-seed** (연구: 사용가능 88% vs 단일 31%).
- 생성에 **인구통계 다양성 제어** (실측: LLM 남성 79~84% 과대).
- 근거 = **하이브리드 RAG + 4단계 self-check** (오류 3.3%).
- 채점 = **이분법**(팀 D1) + **오픈모델 옵션**(연구: GPT-4o와 동급, 비용↓).
- 검증 = 전문가 간 일치도 먼저 → AI-전문가(ICC/kappa), `사례개발피드백` silver-label 부트스트랩.
- ⚠️ 논문: **"AI=인간 동등" 주장 금지**(적대검증 탈락).

### 산출물
- `docs/context-map.md` · `docs/research-llm-cpx-sota.md` · `docs/architecture.md` · `docs/worklog.md`(본 파일)

### 열린 항목
- 부산대 샘플 사례 2~3건 확보(단톡 요청 중) — 생성 few-shot·CPX 이해.
- `사례개발피드백` 표 본문 추출(hwp5html) — H2 정답지.
- 진료수행지침(798p 스캔본) OCR — 분류 근거.
- 프로젝트용 CLAUDE.md/AGENT.md/MEMORY.md — 맥락 파악 완료, 생성 시점 도래.

### 다음
- Codex 적대 검수(architecture) → 구현(데이터준비 → models.py → RAG → ①생성 …).

---
<!-- 이후 구현 단계 로그는 이 아래에 날짜별 append -->

---

## 구현 — 2026-06-18

### 카운슬(Codex 적대검수) 후 첫 vertical slice = ④ 채점 v0
- **Codex 2라운드** 적대검수 → architecture v1→v3 (그래더-first 역순·데이터 게이트 2단계·한국어 주코퍼스·과대주장 강등·VP 유한상태정책·하네스 임계 사전등록·개인정보/비용). 기록: `~/main/council/2026-06-18_cpx-ai-architecture/`.
- **스캐폴드:** venv(pydantic 2.13.4) · `src/cpx/` · `data/{cases,transcripts}` · `.gitignore`(민감/대용량 제외).
- **`models.py`:** `CpxCase` 계약(= [붙임2]). Pydantic=구조만, 의미검증은 별도(명시).
- **`agents/grader.py`:** ④ v0 = aristo-mini `score→판정` 오마주. 결정론 키워드 이분법(의존성·API 0 = 엔지니어링 게이트). LLM 의미매칭은 다음 단계(인터페이스 동일).
- **gold 사례 1건**(설사/김선미, [붙임2]서 손 작성) + **데모 transcript** → `demo_grade.py`.
- **실행 결과:** 6/8 도달, 누락(hx_form·hx_fever) 구체 피드백 정상 출력. ✅
- ⚠️ v0 점수 = smoke/단위테스트용. kappa 타당성은 실제 학생 transcript+인간라벨 후(H4-real).

### 다음
- LLM 의미매칭 grader(`llm.py` 어댑터 + `grade_item` 교체) — 키워드 한계 극복
- gold 사례·fixture 추가 + H4-smoke 하네스
- 최소 교수 리뷰 UI (v1 thin-vertical 완성)

### ④ grader LLM 의미매칭 (A 진행) — 2026-06-18
- `.env`(gitignore) + `llm.py`(Gemini 어댑터, 모델 교체 지점) + `grade_llm`(구조화출력 이분법 판정).
- Gemini 모델 API로 확인 → `gemini-flash-lite-latest`(최저가) 사용.
- **데모: v0 6/8 vs LLM 7/8.** LLM이 의역("변이 물처럼 줄줄 나오나요"=변 형태질문) 캐치, v0 키워드는 놓침. → 7-a "심장마비=심근경색" 의미문제 해결 입증.
- ⚠️ 노출 API키 rotate 필요. 모델 교체(Claude/GPT)는 `.env`/`llm.py` 1줄.

### B) H4-smoke 하네스 + gold 사례 추가 — 2026-06-18
- gold 사례 +2 (두통/긴장성두통, 흉통/심근경색=red flag) + transcript + `data/fixtures.json`(손 라벨).
- `harness/metrics.py`(Cohen's kappa 직접 구현) + `harness/runner.py` + `harness_smoke.py`.
- **결과(20항목): v0 정확도 0.90·kappa 0.69 vs LLM 1.00·kappa 1.00. LLM 일관성 3회 1.00.** → LLM이 의역(변형태·두통위치·방사통) 전부 캐치. (⚠️ SMOKE: 손라벨·소표본)

### A) ③ 텍스트 가상환자 (루프 닫힘) — 2026-06-18
- `agents/patient.py`: 환자 페르소나 + **과공개 제어**(허용사실 + 강한 정책 프롬프트). 완전 FSM 항목별 정책은 다음 단계.
- `demo_loop.py`: 사례 → 스크립트 학생↔가상환자 대화 → ④ 채점. **= thin-vertical 심장(텍스트).**
- **결과(흉통 사례): 환자 구어체 연기 OK · 과공개 제어 준수(위험인자 누출 0) · ④가 hx_risk 누락 정확 포착(5/6).**
- 미세: 환자가 첫 인사서 증상 일부 자연 언급 — FSM 정책으로 더 조일 여지(후속).

### v1 thin-vertical 현황
- ✅ 스키마(models) · ③가상환자 · ④채점 · H4-smoke 하네스 · gold 3건
- ⬜ 남음: 최소 교수 리뷰 UI · ①생성(타당성 게이트 후) · 실제 부산대 사례 교체

### 가) F1·precision 하네스 추가 + 나) Codex 학술검수 + 데이터 거버넌스 — 2026-06-18
- 하네스에 **precision/recall/F1** 추가 → v0: P1.00·R0.88·F1.94·κ0.69 / LLM: 전부 1.00(smoke).
- **Codex 학술-프레임 검수**(AGENTS.md 읽고 비즈니스 X, 검증·재현·안전 축): VERDICT REVISE(아직 smoke). 핵심 = 누수 통제·gold 신뢰성·검증 프로토콜 명문화·재현성 패키지·안전경계. 기록 `~/main/council/2026-06-18_completeness-academic/`.
- **데이터 거버넌스 구축**(사례 도착 前): `docs/data-governance.md`(누수 방화벽·격리절차·안전경계·검증 스켈레톤) · `.gitignore`(raw_private/working) · `scripts/quarantine.py`(해시·인벤토리) · `data/{raw_private,working/{train_prompt,dev_tune,locked_eval},toy}/`.
- ★ 오늘 밤 사례 도착 시: **생성부터 ❌ → 격리·인벤토리·분할 먼저**(누수=연구 무효화 1순위).

### 사례 도착 전 prep (#1·#2) — 2026-06-18
- **#1 Ingestion 변환기** (`scripts/ingest.py`): hwp(hwp5html)→텍스트→LLM 구조화출력→CpxCase JSON. [붙임2] 테스트: 제목·진단(LLM "항생제 연관 설사" 정확 추론)·**19 체크리스트(scoring_rule+keywords) 자동생성**. models.py: function_weights·demographics를 dict→**타입모델**(Gemini 구조화출력 호환 + 엄격). 기존 케이스 회귀 OK. **오늘밤 사례용 준비완료.**
- **#2 ④ 디브리핑 확장** (`agents/debrief.py`): 학생 발화별 **유도성질문·전문용어·개방형/폐쇄형·리라이트**. 데모: "방사되는 느낌? 왼팔이?"를 유도성+전문용어로 잡고 리라이트 — 메튜 간판기능을 투명하게 재현. (⚠️ 이 판정도 추후 하네스 검증 필요)
- 남은 prep: #3 적대 transcript팩+오류taxonomy · #4 VP검증 probe · #5 toy데이터셋+재현성 템플릿.

### 사례 도착 전 prep (#3·#4·#5) — 2026-06-18
- **#3 적대 transcript 팩** (`data/adversarial.json` + `adversarial_smoke.py`): 동의어·헛공감·유도성+전문용어 3종. **18/18 일치, FP/FN 0** — 채점 강건(헛공감 과대평가 안 함, 유도성이어도 내용 인정). 오류 surfacing(FP=헛점/FN=놓침) 틀 마련.
- **#4 VP probe** (`vp_probe.py`): 과공개("구토?"에 '속불편' 흘림 ⚠️ 포착=FSM 필요 근거) + 일관성(3회 동일 ✅).
- **#5 재현성 패키지**: `README.md`(실행법·한계 명시) · `data/toy/`(가상 사례 공개 복사) · `data/DATASET_VERSION.md`(템플릿) · `docs/validation-registry.md`(주장↔재현좌표 템플릿).

### 파이프라인 완성 — ②심사 + ①생성 + 전체 루프 — 2026-06-18
- **② 심사** (agents/reviewer.py): 실기문항저자점검표 13항목 루브릭 → 통과/지적 + verdict(Accept/Minor/Major/Reject) + 수정안. 데모(설사 손사례): 10/13, Major, 정확한 지적(생각/걱정 빔·항목 8개뿐·교육 약함).
- **① 생성** (agents/generator.py): 멀티에이전트 생성→②비평→수정. 연구반영(checklist-as-seed·진단조건부 인구통계·self-check).
- **전체 파이프라인** (demo_pipeline.py): 발열/급성신우신염 → ①생성(**28세 여성**=진단조건부, '65세 남성 흡연자' 편향 회피 ✅; draft→Major→수정) → ②심사 **Accept 13/13**(루프가 Major→Accept 개선) → ③가상환자 → ④채점. **①→②→③→④ 작동.**
- ⚠️ toy/가설. 실제 검증은 부산대 사례+전문가 라벨 후.

### 나) RAG 근거층 — 2026-06-18
- `llm.embed()`(gemini-embedding-001, 다국어 3072d) + `src/cpx/rag.py`(청크→임베딩→코사인 top-k).
- `scripts/build_rag_index.py`: Harrison 내과 1200청크 인덱스 → `data/working/rag_index/`(gitignore, 저작권).
- `demo_rag.py`: **한국어 질의→영어 교과서 의미검색 작동**(신우신염→cystitis/uropathogen, 흉통→cardiac risk, 설사→diarrhea workup, 코사인 0.66~0.72).
- ① 생성에 **근거 주입**(generator._draft): parametric 아닌 교과서 grounding 위에서 생성. (폐렴 생성 시 PCP 근거 940자 주입 확인)
- ⚠️ 프로토타입: 코퍼스 일부(1책 샘플). 하이브리드(BM25)·전체코퍼스·리랭커·한국 자료 주코퍼스 = 후속.

### 다) LangGraph 오케스트레이션 — 2026-06-18
- `src/cpx/graph.py`: StateGraph로 **①생성→②심사→(조건부)수정→재심사 루프**. demo_graph.py: 생성→Minor→수정→Minor→수정→**Accept** 자동 루프 작동. 함수호출 대비 상태·분기·루프·(추후 LangSmith 추적·중단재개).
- ⚠️ ③④(학생 상호작용 런타임)는 이 개발그래프와 별도.

### 라) 검증 인프라 — 2026-06-18
- `docs/ppi-rubric.md`: PPI 미시행동 0/1/2 루브릭(이분법 불가 영역, 진정성=인간 최종). debrief 플래그 연결.
- `data/labeling_workbook_template.csv`: H4-real 임상교원 2인 블라인드 라벨→불일치 합의→AI 비교 (논문 methods 산출물).

### 실제 사례 도착 + 누수안전 분할 — 2026-06-18
- 임선주 교수 → `CPX사례개발자료(21-26).zip`(170 hwp). → `data/raw_private/2026-06-18_pusan`(격리·gitignore·해시 인벤토리).
- 구조: **최종 85**(증상_연도_진단) · **초안 80** · **피드백 5**(연도별). 초안↔최종 **페어 71**. 48증상, 2021-2026(2025 없음, hybrid 소수).
- **Codex 데이터전략 검수**(메타만 전송, raw는 레포 밖으로 빼고): 누수안전 분할 · 첫실험 **H2(②심사가 전문가 피드백 재현?)** · 점진변환 · 비식별 · locked 봉인. 기록 `~/main/council/2026-06-18_realdata-plan/`.
- `scripts/split_cases.py`: 파일명 메타만으로 케이스패밀리 층화분할 → `data/working/splits.json`. **train25/dev45/locked17**(연도층화). 내용 안 열고 분할 = 방화벽.
- 다음: 비식별 + dev 3건 변환→검수→배치 / **H2 실험**(70페어).

### dev 변환 검증 + 추출 품질 튜닝 + 결제 판단 — 2026-06-18
- `ingest.py`: **비식별**(이메일·전화·주민번호 제거, 개발자정보 제외) + 모델 **gemini-2.5-flash**(flash-lite는 과소추출) + 한도 40k + **도메인분류/중복금지/~30개** 프롬프트 규칙.
- dev 3건(객혈 22/23/24): flash-lite **22/6/4** → 2.5-flash+규칙 **32/39/35**항목. PII 0. 타당성 검증기가 PPI>6 1건 플래그.
- **결제 판단: Gemini 2.5-flash로 ingest 충분 → Claude/GPT 결제 보류**(생성·심사 품질 부족/음성/모델비교 때 재검토).
- 다음: dev 배치 변환(검증기로 outlier 표시) → **H2 실험**(②심사 vs 전문가 피드백, 70페어).

### H2 파일럿 (②심사 vs 전문가 피드백) — 2026-06-19
- scripts/h2_pilot.py: dev 페어 3건(객혈 22/23/24) 초안→①변환→②심사 → 연도 피드백서 해당사례 발췌 → LLM judge로 카테고리 비교.
- **결과: ② recall 5/22 = 23%.** 구조적 지적(복합질문·항목수)은 잡고, 사례특이 임상 정교화(흡연력·직업일관성·현병력상세)는 대부분 누락.
- 해석: 일반 점검표 ② vs 사례특이 전문가 피드백 = 결 다름(부분 아티팩트) + ②의 진짜 한계 동시. → Codex 검수.
- 상세: docs/h2-pilot-result.md

### H2 Codex 적대검수 — 2026-06-19
- 판정: 파일럿=진단 smoke로 유효, ②"23% 성능" 증거로는 무효(구성 불일치: 일반 구조 ② vs 사례특이 임상 피드백). 23%=아티팩트+부분 실제갭 혼합.
- 처방(둘 다): ② **2층 분리(②A 구조/②B 임상)** + 출력 taxonomy. 실험 **재설계**(atomic label·카테고리별 P/R/F1·인간 adjudication·CI). 논문 과대주장 금지.
- ⚠️ 큰 재설계는 권고로 보류(인간 adjudication=교수 필요). 정직 프레임만 반영. 기록 ~/main/council/2026-06-19_h2-review/.

### ②B 임상 리뷰어 추가 + H2 비교 — 2026-06-19 (용하 ㄱㄱ 승인)
- `reviewer.py`: **②B review_clinical**(RAG 근거 임상심사, taxonomy: CLINICAL_CONTENT/INTERNAL_LOGIC/SP_FEASIBILITY/…). `llm.py`: 503/429 재시도 백오프. `ingest.py`: 모델 폴백 체인(2.5-flash→lite). `h2_compare.py`: 공정비교(전문가 지적 1회 고정 + draft 캐시).
- 결과: ②A **19%** → ②A+②B **26%** (+6%p). ②B 방향 맞으나 갭 잔존, 자동 judge 노이즈. → **인간 adjudication 필요(교수)**.
