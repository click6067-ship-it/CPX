# 작업 로그 (worklog) — Codex 검수용

> 용도(1석3조): **① Codex 적대 검수** · ② 개발 담당 본인 이해 · ③ 교수님 설명.
> 원칙: 정제·요약(원문 나열 X). 기획 단계부터 기록.

---

## Phase 0 (정의·설계) — 2026-06-17 ~ 06-18

### 진행 요약 (요청 → 한 일 → 결과)

1. **자료 파악 요청** → PI 사업계획서(.hwp) + MedQA 레포 정독 → CPX 문제정의·MedQA 구조 파악.
2. **"aristo-mini/MedQA 접목, 거시 구조화"** → aristo-mini 6개 솔버 분석. 결론: **코드 복붙 X, 설계 골격만 오마주**(2017년 코드라 낡음). MedQA의 "텍스트 A↔B 부합도 점수화" 구조 = CPX 채점/사례평가 뼈대와 동일(핵심 통찰). *(⚠️ 이후 2026-06-20 결정: "MedQA처럼/오마주" 비유는 공개문서에서 전부 삭제 — MedQA는 RAG 교과서 데이터 출처로만 인용. 이 줄은 당시 연대기 기록.)*
3. **범위 리프레임** → "MVP" → **"90% 완성품"**(교수 깐깐). 역할 = 팀분담 명목상, **전체 end-to-end 개발 담당 단독**.
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
- 연구책임자 → `CPX사례개발자료(21-26).zip`(170 hwp). → `data/raw_private/2026-06-18_pusan`(격리·gitignore·해시 인벤토리).
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

### ②B 임상 리뷰어 추가 + H2 비교 — 2026-06-19 (개발 담당 ㄱㄱ 승인)
- `reviewer.py`: **②B review_clinical**(RAG 근거 임상심사, taxonomy: CLINICAL_CONTENT/INTERNAL_LOGIC/SP_FEASIBILITY/…). `llm.py`: 503/429 재시도 백오프. `ingest.py`: 모델 폴백 체인(2.5-flash→lite). `h2_compare.py`: 공정비교(전문가 지적 1회 고정 + draft 캐시).
- 결과: ②A **19%** → ②A+②B **26%** (+6%p). ②B 방향 맞으나 갭 잔존, 자동 judge 노이즈. → **인간 adjudication 필요(교수)**.

### 교수 adjudication 인프라 — 배포형 설문 + 집계 파이프라인 — 2026-06-19 (개발 담당 지시)
- **배포 설문 웹앱**(`web/adjudication/`, Vercel): 교수가 **주소+암호만** 받아 한 문항씩 클릭(AI 잠정판정 미리선택) → **중앙 자동수집**(Blob). 3명→N명 확장. 암호 게이트+noindex+URL추측불가, CPX repo와 **분리 배포**(사례데이터 안 올라감). Live: cpx-adj-web.vercel.app. **현재 토이데이터** — 실데이터는 PI 동의 후 전환(SURVEY_PW+CSV교체+재배포, 판정자/관리자 암호 분리 예정).
- 스크립트: `build_adjudication_sheets.py`(CSV 생성, 배치1=9페어·전문가지적84·②지적76) · `build_adjudication_html.py`(오프라인 단일HTML 대안) · `build_survey_data.py`(CSV→data.js+items_meta.json, 실데이터 검증: 73지적/카테고리분포) · `aggregate_adjudication.py`(**Fleiss kappa+다수결 합의+카테고리별 recall/precision/F1+페어부트스트랩 CI**, `--demo`/`--url` 지원, 데모+live e2e 검증 완료).
- excluded(사례품질 아님) 다수결은 분모 제외 = Codex 지적 구성불일치를 사람판정으로 교정. tie는 재검토 플래그.
- 다음: PI 동의 → 실데이터 전환 → 교수 판정 → 집계(첫 진짜 H2 결과). 배치2~3로 30페어 확대. locked17 봉인 유지.

### H2 검증 v3 — Codex 3라운드 적대검수 후 전면 재설계·재배포 — 2026-06-19 (개발 담당 지시: "codex랑 끝까지 완벽하게")
- **Codex 적대검수 3회**(메타만): R1(v1 설계)·R2(v2 설계) **둘 다 REVISE** → R3(v3 구현) **PILOT-OK**. 상세 `docs/validation-design.md`.
- v1(per-point 분해→LLM매칭→인간 caught) 결함: 순환측정·앵커링·정보부족·약한주지표·precision누락·pseudoreplication. → **v3 전면 재설계**.
- **v3 = case 중심·전체맥락(생략0)·블라인드 비교**: 사례별 [초안 전문 + 교수 피드백 vs AI 리뷰 블라인드 루브릭(완전성/정확성/유용성/안전성 1~5, BARS앵커, 블라인드성공 점검) + 공개후 per-point recall + AI지적 precision]. 라디오·모드분리(blind/recall 코호트)·읽음확인.
- ② 모델 **flash-lite→gemini-2.5-flash 격상**(harness 모델-agnostic, pro/Claude는 본검증 freeze). 사례 전체 심사(truncation 30k).
- 집계 `aggregate_validation.py`: blind 차이+**case-cluster CI**·**ICC(2,k)**·**블라인드 성공률**·recall+Fleiss+LOO·precision+**harmful 안전게이트**·(judge,mode) dedup. e2e(제출→--url) 검증 완료.
- Live 6사례(객혈·고혈압·관절통증·구토·기분변화·기억력저하) 배포. 판정자/관리자 암호 분리.
- ⚠️ Codex 강조 = **feasibility/파일럿**(확정주장 금지: "AI가 전문가에 필적/대체" ❌). 본검증엔 사전등록·δ·코호트분리·표본확대 필요. 스크립트: `build_validation_data.py`·`aggregate_validation.py`·`web/adjudication/`.

### v3 마감 — PII 강화·온보딩·Codex 최종QA 수정·목차 — 2026-06-19
- **PII 긴급수정**: 배포 초안에 개발자 실명·전화·이메일·CSS 노출 발견 → ingest deid 강화(개발자 블록 제거·공백/도메인깨진 이메일·전화 마스킹·style/CSS/페이지머리말 제거). 전수 재검 0. `deid_archive.py`로 170파일 안전텍스트본 바탕화면 zip.
- **온보딩**: 콜드 교수용 안내(연구주체·목적·점수·자발성·한계). 개발자=**팀원·팀원·개발 담당**. IRB·동의서·기입칸 미사용(개발 담당 결정).
- **Codex 최종 QA(R5, FIX-FIRST) 6개 수정**: ①블라인드 길이격차 극단(고혈압 78x) **제외**→기침 대체 ②집계 `--mode` 코호트필터(혼용오염) ③submit 서버 스키마검증+집계 결측경고 ④집계가 meta의 blind만 신뢰(클라조작 차단) ⑤성함 공백정규화 ⑥백업다운로드 pw 제거. +모드화이트리스트·메모칸·초안전체보기·예외처리. 전부 e2e 검증.
- **목차 기능**(팀원 제안): 초안 섹션(상황지침·현병력·신체진찰…) 목차칩 → 클릭시 해당 섹션 점프(지적↔본문 대조 편의).
- 가독성: 초안·검토의견 섹션/○/N번 줄바꿈+들여쓰기(fmtDraft/fmtReview). 6사례 라이브.

### gpt-5.5 ② + 3사 어댑터 + RAG 하이브리드 + 좌우비교·근거하이라이트 + 교수 파일럿 준비완료 — 2026-06-19
- **모델**: Claude 결제 막힘(한국카드/백엔드) → 계획서 Claude자리 = 최상위 GPT(**gpt-5.5**). `llm.py` 3사 라우팅 어댑터(claude/gpt/gemini, 추론모델 temperature 패치). 결제 풀리면 1줄 교체. 임베딩=Gemini 유지.
- **② 간결튜닝**(verbosity↓)+16상한 → 사례당 16지적, 블라인드 길이격차 **1.3~2.3x**(was 5~9). 근거 하이라이트(finding별 quote)·**좌우비교 레이아웃**·목차 점프(팀원 제안).
- **RAG 하이브리드** 구현: dense(Gemini 임베딩)+sparse(BM25, 로컬)+RRF. 코퍼스=MedQA 교과서(Harrison 샘플 1200청크). 사례는 ②입력이라 임베딩X(①생성 때 비식별 임베딩 예정).
- 문서: `docs/transparency.md`(모델·데이터·RAG 정본)·`docs/validation-design.md`(Codex 5R)·`docs/handoff.md`(교수 전달).
- **교수 파일럿 준비완료**: 6사례 gpt-5.5 라이브, PII0, 수집함 클린. 다음 = 교수 응답 → `aggregate_validation` 집계(첫 실결과).

### 설문 A1~A6 + 하이브리드 모드 + 다이어그램 + README/문서 정리 — 2026-06-19~20 (개발 담당 지시)
- **설문 A1~A6**(팀원 피드백): A1 생성/채점 경계 안내(상단 고정), A2 영어약자 `abbr`(Hx/PE/Edu/PPI 자동·중복방지), A3 의견 A/B별 주관식, A4 `?mode=browse` 자유열람(블라인드·판정 없음), A5 browse 사례별 자유메모, A6 검증데이터 오분류 스캔(clean). 배포·검증.
- **하이브리드 모드**(`?mode=hybrid`): 교수가 사례별 "블라인드 평가(eval)" 또는 "열람만(browse)" 선택 → eval만 정량·browse 정성. 블라인드 무결성 유지+부담↓. 집계에 hybrid 추가(pick=eval 필터·선택편향 진단). Codex review 반영.
- **작동방식 다이어그램**: mermaid(README·`cpx-flow.md` 자동렌더) + excalidraw 2버전(Claude 직접좌표 vs Codex 병렬생성, 둘 다 겹침0) → **개발 담당 Claude 버전 확정** = `docs/cpx-flow.excalidraw` 정본 + 온라인편집 링크. `scripts/build_excali.py`(좌표 그리드)·`preview_excali.py`(PNG 검증). README 이미지화. Napkin용 텍스트(`diagram-text-for-napkin.md`).
- **README 전면 개편**: 데이터·코퍼스·모델 표 명확화 + 작동방식 이미지. **"MedQA처럼/식" 비유 전부 삭제**(README·roadmap·AGENTS — 추후 분쟁 방지, 데이터 출처 인용만 유지).
- **암호 진단**: 설문 진입=응시암호(`cpx-pnu-2026`), 결과취합=관리자암호(`cpx-adm-2026-x7k`, `/api/results` 전용). 혼동 해소(설문에 관리자암호 넣어 403났던 것).

### 기술보고서 PDF (교수 디펜스용) — Codex 2라운드 적대검수 — 2026-06-20 (개발 담당 지시)
- **`docs/techreport-cpx.md`/.pdf** (14p, 바탕화면): 배경·전체구조·작동방식·아키텍처·데이터/코퍼스·모델·H2검증설계·RAG·SOTA근거·한계·로드맵 + **예상질문 디펜스 Q&A 11개**. 일반인 이해 목표. pandoc+weasyprint(한글 Malgun), 다이어그램 이미지 임베드.
- **Codex 적대검수 2R**(REVISE→REVISE 둘 다 반영): 과대주장 톤다운("필적"→재현정도 측정·"학원"→연구용 시뮬레이터·"교수 대행"→보조·"오류3.3%"→외부문헌수치 우리 미측정), 사실정확화(임베딩=색인+질의+생성·RAG=Harrison샘플·FSM=설계안), 모델ID 일관화(설문 README gemini→gpt-5.5), IRB 상태 분리.

### 남은작업 안전순서 (Codex 적대 계획) + A1·C1·거버넌스 — 2026-06-20 (개발 담당: "전부 다 세심하게")
- **Codex 적대 계획검수**(REVISE): "전부 동시"는 순환검증(H2 전 생성강화)·저작권(seed변형)·가짜지표 위험 → **안전순서 확정**: H2(교수대기)→C1→A1→거버넌스→B2. A2·A3·B1·B3 연기. (개발 담당 결정: 비식별·로컬전용이면 B2/A2 가능)
- **A1** ②B 임상리뷰어를 ①생성 루프 연결(`generator`/`graph`): ②A 구조+②B 임상(RAG), 종료조건 ②A∈{Accept,Minor} AND ②B must_fix=0. Codex review 2R: 재심사 루프 통일·종료상태 플래그·optional 보존·②B 스위치. ⚠️ H2 안전성 확인 후 프로덕션(현재 프로토타입).
- **C1** 근사 pseudo-F1 + `docs/f1-codebook.md`: 교수point↔AI finding 매칭규칙·TP/FP/FN·완전 adjudication SOP(데이터 오면 적용). Codex review 2R: "진짜 F1"→"근사 pseudo-F1"(매칭 미adjudication·1:1가정 명시)·동률=ambiguous 제외·finding 결측검사. ⚠️ 코드+demo만, 수치주장 없음.
- **거버넌스** `src/cpx/governance.py`: near-copy(char-ngram containment+sliding window, 부분복제 탐지)·provenance(generator 연결)·버전freeze·단가(gpt-5.5 $5/$30). `data-governance §7` provider data-use 표(Google free-quota=학습→유료tier 필수·feedback제출금지·의료제한). Codex review 1R 반영(4gram자카드→containment, 단가 웹확인).
- **다음 = B2**: 가용 한국자료(점검표·양식) 색인 + RAG 평가셋 + `build_validation_data` near-copy 통합 + 진료수행지침 PI 요청. (연기: A2·A3·B1·B3 / 대기: 교수 파일럿 응답·README excalidraw export)

### LangGraph 네이티브 렌더 (코드-정본 시각화) — 2026-06-26 (개발 담당 지시)
- **요청="flowise로 랭그래프 시각화"** → 함정 지적: Flowise는 기존 LangGraph 코드를 불러와 렌더하지 못함(자체 포맷·노드, 캔버스 수동 재구성=실제 코드와 분리된 mock). 학술 투명성엔 부적합. → 개발 담당 결정: **LangGraph 네이티브 렌더** 채택.
- **`scripts/render_langgraph.py`**: `graph.build().get_graph().draw_mermaid()`/`draw_mermaid_png()` 로 *실제 컴파일된* 그래프를 그대로 출력. 손그림 `cpx-flow.*`(전체 시스템 아키텍처)와 달리 코드 100% 일치·재현가능. 키 불필요(렌더는 구조만, 실행 아님).
- 산출물: `docs/cpx-langgraph.mmd`(mermaid, 네트워크불필요) + `docs/cpx-langgraph.png`(mermaid.ink). 구조: `start→generate→review`, `review⇢end`(조건), `review⇢revise`(조건), `revise→review`(수정 루프). graph.py와 일치 확인.

### 관찰·추적(Langfuse + LangSmith) + Flowise 캔버스 — 2026-06-26 (개발 담당 지시: "지금바로")
- **트레이싱 2종 연결** (`src/cpx/tracing.py`, no-op safe·env-gated): 이 레포는 langgraph+raw SDK(LangChain 래퍼 X)라 2층으로 붙임 — ① 노드 트리: LangSmith=langgraph 네이티브(env), Langfuse=CallbackHandler를 `graph.invoke(config)`로 전달 ② LLM generation(raw SDK 사각지대): `llm.complete/complete_json`을 `@traced(run_type="llm")`로 감싸 LangSmith span+Langfuse generation 생성. `graph.develop_case`에 run_config+flush 배선.
- **거버넌스 존중**: `.env` "추적 기본 OFF(민감데이터 SaaS 전송 주의, architecture §7)" 명시 → 임의로 켜지 않음. 키만 채우고 `LANGSMITH_TRACING=true` 1회 토글로 활성. `.env`/`.env.example`에 LANGFUSE_*·LANGSMITH_PROJECT 추가. requirements에 langfuse+langchain(=langfuse CallbackHandler 요구). 검증: off-path(둘 다 off=무영향)·on-path(더미키로 콜백주입·observe적용, LLM호출 0=무비용) 둘 다 PASS. ⚠️ 대시보드 실트레이스는 유효키+라이브런 필요(개발 담당 몫). dev 그래프는 합성사례라 PII위험 낮음·③④ 학생런타임 추적 시 거버넌스 재검토.
- **Flowise 캔버스**(원래 요청): Flowise는 LangGraph 코드를 자동렌더 못함 → 자체 빌더 캔버스에 수동 재구성. `flowise/cpx-case-loop.agentflow.json`(Agentflow V2, 7노드·7엣지) = graph.py와 구조 동일(종료조건 ②B must_fix 세부는 graph.py 정본·Flowise route 단순화)(Start formInput→generate→review→Condition[Accept/Minor→확정·Else→수정]→revise→loop(maxLoopCount=2)→review). `flowise/build_agentflow.py`가 Flowise 내장 템플릿의 검증된 노드 블록을 추출·재조립(id/앵커 일괄치환). 구조검증 통과(엣지 핸들·앵커·loopBackToNode·targetHandle 규약 0에러). flowise 전역설치+서버 :3100 기동. API import는 3.x 인증(401) 막힘 → UI Load로 import(README 절차). `docs/cpx-langgraph.png`(네이티브 렌더)와 별개 산출물.
- **(후속) Flowise import 실제 완료 + 캔버스 스크린샷**: 401은 `x-request-from: internal` 헤더 누락이었음 → OSS 첫 계정은 즉시 ACTIVE(account/register, 이메일인증 불필요) → 로컬관리자(admin@cpx.local) 생성 → 로그인 → `/api/v1/chatflows`(type=AGENTFLOW) POST 로 플로우 import 성공(id 065caee8, 7노드·7엣지 보존 확인). puppeteer(번들 chromium) 폼로그인 → `/v2/agentcanvas/<id>` 헤드리스 렌더 캡처 = `flowise/cpx-flowise-canvas.png`(7노드·7엣지, graph.py와 구조 동일(종료조건 ②B must_fix 세부는 graph.py 정본·Flowise route 단순화)). `flowise/shot.js` 재현용.
- **(후속) README 차별점 (예정) 섹션 추가** (개발 담당: "트레이스 공개로 ㄱㄱ, 전부 (예정)"): 3축 — A 임상전문가 검증루프(expert-in-the-loop, H2 대기) · B 재현성·투명성(시스템프롬프트+실행트레이스 공개+Pydantic 스키마강제) · C 비전공자 이해가능성(Flowise 설명캔버스+LangGraph 네이티브렌더). 전부 (예정) 태그·과대주장 금지 톤·"Flowise는 엔진 아닌 설명용" 명시. Codex 적대검수는 미실행(권장).
- **(후속) Codex 적대검수 반영 (4건)**: [BLOCKER] flowise 로컬 admin 비번 커밋 → 제거·env화(shot.js `FLOWISE_EMAIL/PASSWORD`) · [BLOCKER] 추적 전역계측이 사례+저작권RAG를 SaaS 업로드 → `CPX_TRACE_ACK` egress 게이트 추가(미동의 시 langgraph-native까지 OFF, tracing.py가 LANGSMITH_TRACING 자동관리) · [MAJOR] Flowise route가 must_fix=0 게이트 누락 → "1:1" 주장 완화+단순화 명시(graph.py 정본) · [MINOR] Pydantic이 hallucination 차단 과대주장 → "형식·스키마 차단; 임상 사실성은 별도검증"으로 완화. `flowise/.cookies`(세션JWT) gitignore.
- **(후속2) Redaction 레이어 + README 정리** (개발 담당 지시): 트레이스 egress 직전 사례·RAG 본문 마스킹(`tracing._mask`) — 긴/민감 문자열→`<redacted:Nc sha256:…>`(해시 보존=재현·감사), cpx 도메인모델→`<Type redacted>`, 짧은 비민감(role·verdict·log)·수치는 통과. LangSmith=내용 전체 비공개(`LANGSMITH_HIDE_INPUTS/OUTPUTS=true`), Langfuse=`Langfuse(mask=_mask)`(CallbackHandler+@observe 모두 거침, 모듈로드 시 마스킹 싱글톤 선초기화). → 부산대 사례·저작권 교과서 본문 SaaS 비유출. README 차별점: **Pydantic 불릿 삭제**(과대주장 소지·축 혼란), B 트레이스 공개를 "자동 마스킹하여 공개"로 안전화, **C "비전공자"→"일반인"**. .env/.env.example redaction 자동 명시.
- **(후속3) 라이브 redaction 검증 + 공개 트레이스 산출물** (개발 담당: "라이브 확인하고 로그 전체 공개"): `scripts/sample_trace.py` 로 graph 1회 실행(gemini-flash-lite, LLM 6회: 생성→②A→②B→수정→②A→②B). `tracing._mask` 로 사례·RAG 본문 마스킹 → `docs/sample-trace-redacted.{json,md,html,png}`. **LangSmith 라이브 업로드분 API로 확인 = `inputs={}`·outputs 없음(내용 0)** → redaction이 SaaS에서 실제 작동. 공개 권장 = 텍스트 정본(md, 검색·재현·해시검증) + 스샷(README 임베드). README 차별점에 "공개 트레이스 예시" 섹션 추가.
- **(후속4) 셀프호스트 Langfuse 라이브 검증** (개발 담당 결정: self-host, sudo 제공): docker 설치(v29.6) → langfuse 공식 compose 기동(web 포트 3000 충돌 → 3100 `!override`) → **헤드리스 init**(`LANGFUSE_INIT_*`)으로 org·project(`cpx-ai`)·API키·admin 자동생성(브라우저 수동작업 0) → CPX `.env` 연동(`CPX_TRACE_ACK=1`). 라이브 트레이스 1회(**Langfuse만·LangSmith off = egress 0**) → API 검증: observation 13개 전부 마스킹(LLM input `<redacted:sha256>`, output/노드 state `<CpxCase/ReviewOut/ClinicalReview redacted>`), **누출 0**. 대시보드 스샷 `docs/langfuse-trace-detail.png`. 가이드 `docs/langfuse-selfhost.md`, 스샷 스크립트 `scripts/langfuse_shot.js`. README 공개 트레이스 섹션 = 셀프호스트 대시보드 스샷. (langfuse 스택은 `~/langfuse` 외부폴더, 키·비번은 gitignore된 .env들에만.)

### 온톨로지·지식그래프 설계 리뷰 준비 문서 + Codex 적대 리서치·레드팀 통합 — 2026-06-30 (중단 세션 복구)
- **배경**: 지도교수 미팅 제안("온톨로지+Neo4j 지식그래프로 LLM이 근거 갖고 사례 생성") + 팀원 제안("로컬 35B Q4 256k + LLM wiki + 키워드 온톨로지"). 개발 담당 질문 "GraphRAG랑 LLM wiki 다른 거 아냐?" → 리서처+적대검증으로 정밀구분 확정.
- **`docs/ontology-meeting-prep.md` (v2)**: §0 두 제안=다른 층(지도교수=관계구조/팀원=지식포맷·모델) · §1 개념(온톨로지=의미설계/Neo4j=그릇/LangGraph≠지식그래프) · §2 **GraphRAG vs LLM wiki 정밀구분**(둘 다 선택적검색, 진짜 차이=기계지향그래프 vs 인간가독산문 + 자동추출 vs LLM큐레이션, Karpathy 본인 "RAG 대체 아님") · §3 결정프레임워크 · §4 엔티티/관계/엣지속성 + 표준재사용(MONDO/HPO/SNOMED/LOINC/RxNorm) · §5 SKOS · §6 Qwen3-30B-A3B/TurboQuant · §7 리스크·kill · §8 미팅정렬 · §9 출처.
- **중단·복구**: 직전 세션이 deep-research Workflow + Codex 백그라운드 리서치 띄운 직후 종료 → 둘 다 산출 전 사망. **Codex(gpt-5.5) 세션을 `codex exec resume`로 복구** = 웹검색 30여 건(완료분) 그대로 활용해 최종 리포트 생성. deep-research 재실행은 개발 담당 결정으로 생략(v1 출처 충분).
- **§10 = Codex 독립 리서치·레드팀 통합** + 본문 v1 교정(⚠️ 포인터): **①질환-중심→주증상-중심**(ChecklistItem·RedFlag·CpxStationMeta·PPI 계층 필수) · **②온톨로지≠Neo4j**(YAML/JSON disease card+validator로 그래프-스캐폴드 70% 즉시 구현, 온톨로지는 v2+ 불필요) · **③한국 SNOMED 2020년 39번째 회원국**(NRC 통해 추가비용 없이) · 레드팀 결함 7+kill조건 · 교수 예상질문 7+약점 · **2주 MVP 최단순 스코프**(흉통 1개·질환 5개·validator·사례 3개, 그래프DB 아님) · 미팅 최종 권고 멘트("표준 참조하되 핵심은 한국 CPX 수행항목·환자 응답정책; 1주증상 카드부터; Neo4j는 다음 확장").
- **(후속) 해석 정정 — 지도교수 = 결정권자(왕)** (개발 담당 지시): 팀원 발언은 *지도교수 안의 전달*이지 별개 의견 아님 → **미팅 입력 전부를 지도교수의 단일 비전으로 해석.** 우리 자세 = 반박·대안 아니라 **그 뜻을 정확히 해석해 충실히 실행**(최대 리스크=의도 오해). 문서 §0(2인 정렬 프레이밍 폐기)·§8(→교수님께 확인할 해석 포인트 4개)·§10.6(멘트를 "우리가 Neo4j 미룬다"→"전환 시점은 교수님 결정대로")·§8C("Pattern A/B" 내부용어 미팅서 미사용) 톤 교정. *단계화(YAML 먼저)는 그 비전에 더 빨리·정확히 도달하는 수단이지 다른 안 아님 — 시점은 교수님께.*
- **(후속2) 단일 계획서로 통합 + 옛 문서 삭제** (개발 담당 지시: "이전버전 헷갈리지않게 삭제, 전체 설계구조 계획서, 흉통 좁게 시작"): `ontology-meeting-prep.md`가 v1 본문+⚠️교정+§10 3겹이라 혼란 → **`docs/ontology-plan.md` 단일 정본 설계 계획서로 통합**(개념좌표·전체 설계구조(주증상-중심 엔티티/관계/3종 엣지속성/표준+한국어/YAML→Neo4j)·생성 파이프라인(그래프-스캐폴드+validator, 기존 멀티에이전트·LangGraph와 추가레이어 관계)·**흉통 chest_pain.yaml 질환5 초안(ACS+감별4, review_status:draft)**·validator 6검사·2주 MVP·리스크7·미팅메모). `ontology-meeting-prep.md` 삭제(가치내용 전부 흡수). 임상 YAML은 교수 검증 전 초안 명시.
- **(후속3) 흉통 온톨로지 실파일 + 시각화(YAML 정본 + Neo4j 거울) 구현·검증** (개발 담당 "ㄱㄱ"): RAG 역할 = "큰 교과서 전용 조연(축소중)" 명확화(§1) · 저장 = **YAML 정본 + Neo4j/HTML 한 방향 렌더 뷰**(§2.5, Neo4j 조기 운영·동기화 리스크 회피). 산출: `ontology/chest_pain.yaml`(질환5=ACS+감별4, 한국어 라벨맵, **review_status:draft** 임상 교수검증 전) · `scripts/ontology_graph.py`(공통 빌더)·`yaml_to_cypher.py`·`yaml_to_html.py`·`graph_shot.js` · `docs/chest_pain-graph.html`(서버0 인터랙티브 vis-network)·`.png`(스샷). **검증**: 생성 65노드·70엣지 → docker neo4j:5 로드(cypher-shell, 새 py의존성0) → 타입쿼리("ACS 감별질환"·"red flag 질환") 동작 확인 → HTML headless chrome 스샷(흉통→ACS→감별4 색분류·타입엣지). = 옵시디언(무타입)이 못 하는 타입그래프 질의를 미팅서 시연 가능. (neo4j 컨테이너 cpx-neo4j 로컬 :7474, 비번 로컬용.)
- **(후속4) 외부 Chrome→WSL Neo4j localhost 안 뜸 = mirrored 모드 함정 해결** (개발 담당 "기어이 ㄱㄱ", ultracode→max): 증상=브라우저 스피너→오류, WSL 내부·PowerShell은 다 정상. systematic-debugging으로 Windows쪽 interop 검증해 **용의자 전부 배제**(IPv6 ::1 / 프록시 ProxyEnable=0 / Tailscale 꺼도 안됨 / Chrome 프로필·확장·샌드박스 / 방화벽 / chrome115). **근본원인=mirrored 모드가 브라우저 연결만 WSL loopback으로 안 넘김**(데스크톱앱·Windows-local 리스너는 됨—Windows TcpListener로 결정 입증). **해법(비관리자·검증)**: Windows-side TCP 프록시(`C:\Users\click\tcpproxy.ps1`, 런스페이스풀 duplex) 17474→7474·17687→7687 + Neo4j `bolt_advertised=127.0.0.1:17687` 재설정 → Chrome `127.0.0.1:17474` 작동. 런처 바탕화면 `Neo4j프록시.bat`. 메모리 `wsl-mirrored-ipv6-localhost` 갱신. (그래프 보기용 완전오프라인 HTML도 바탕화면 배포.)
- **(후속5) 온톨로지 정합 validator 구현·커밋** (multi-agent workflow): `src/cpx/ontology_validator.py`+`tests/`(19통과). 결정론 6검사(required/red-flag/discriminator coverage·disclosure 자발vs질문시 채널 위반·상호배타 모순·checklist 매핑), 영문id→labels→case 자유텍스트 토큰/동의어 매칭. 실 gold `data/cases/chestpain_lee.json`로 핀고정(진단→ACS카드 해석 검증). workflow=explore→설계패널3(winner=구조체우선 결정론)→구현→적대리뷰3. ⚠️draft 면책 내장. **후속: Codex 적대검수 + nit(freetext disease_id docstring) + graph.py 종료조건 연결 검토.**
- **다음**: 설계 리뷰 → 교수 확인(§7 해석포인트) → 흉통 chest_pain.yaml 교수검증 반영 + validator 실사례 적용 + 사례3 생성·리포트. (Neo4j 전환 시점은 교수님 결정대로.)

### validator 적대검수 반영 + 2-렌즈 재설계 + 미팅 데모 오프라인화 — 2026-06-30 (이어서)
- **(브리핑)** 세션 복귀 — 후보 3건(브리핑·validator Codex검수·미팅점검) **전부 병렬** 진행(개발 담당 "병렬 ㄱㄱ").
- **(미팅 데모 견고화)** ⚠️ `docs/chest_pain-graph.html`이 vis-network를 unpkg **CDN 의존**(인터넷 필요) 발견 → **vendored 핀고정(9.1.9)·인라인**으로 완전 오프라인 + 재현성(부유 CDN 제거). `scripts/yaml_to_html.py`가 `scripts/vendor/vis-network.min.js`(688KB) 인라인. **함정**: 첫 인라인이 템플릿 `<script>__VISJS__</script>` + 함수도 `<script>` 래핑 → **태그 중첩**으로 헤더만 렌더(빈 그래프). 바이트 무결성 + chrome 렌더(35KB깨짐→332KB정상)로 검출·수정. (graph_shot.js의 옛 flowise puppeteer 경로 깨짐은 별도 — chrome cache 바이너리 CLI로 우회 검증.)
- **(미팅 데모 스크립트)** `demo_ontology_validator.py`: 합성 ①정상→pass ②과공개→disclosure fail ③필수누락→required/red_flags fail. 실 gold(`fail`)가 실사례 비판처럼 보일 위험 회피 — 합성 clean↔결함이 "강제·과공개방지"를 안전 시연.
- **(미팅 리허설)** §7 확인질문 4개 적대적 재구성(Q1·Q2 yes/no 동의편향 → 열고-대비; Q5 "검증 주체·노동량" 추가), 예상Q&A 구두화, 가드레일(내부용어·반박조·과대주장 금지), 당일 체크리스트(오프라인HTML·Neo4j접속·합성데모).
- **(Codex 적대검수 #1)** `ontology_validator.py` → **VERDICT REVISE**(gpt-5.5, effort high). 함정: `codex exec`가 비대화형 stdin EOF 대기로 hang + 백그라운드 스크립트 맨앞 `cd` 권한프롬프트로 실패 → **foreground · `< /dev/null` · no-cd**로 해결. 기록 `~/main/council/2026-06-30_ontology-validator-review/`.
- **(즉시 수정 5건)** R4 채널제한(저혈압 "물었다"≠단언) · 성별 토큰추출("남성(58세)") · checklist LOW→flagged 증거보존 · `flag_threshold` 죽은 config 제거 · freetext docstring 보강. 전부 타겟 검증 + 회귀 통과.
- **(2-렌즈 재설계 — 개발 담당 "전면 분리" 결정)** Codex Blocker = validator가 "증상 *있다* / *물었다* / *부정했다*"를 한 바구니로 셈. → **positive 렌즈(환자가 가짐, 부정 제외)** vs **asked 렌즈(학생이 선별)** 분리. `_negated`(한국어 후치부정 "실신은 없었어요" 검출) + `Hit.polarity`, 채널 재배치(present_illness/past/family/social → **history**; disclosure 누설 과플래그 해소), 각 검사 `positive_coverage`/`asked_coverage` 병기. 정책(draft): required=positive 필수 / red_flags=선별(asked)∪제시(positive) / discriminators=positive 우선 비-strict. **테스트 19→24**(negation·선별-부인·present_illness·asked_only·직렬화 핀고정). 데모 정직화 핵심: `red_flags pass · positive=0.00 · asked=1.00`(환자 무·전부 선별 = 두 의미 분리).
- **(Codex 2-렌즈 재검수 R2 → 반영)** R2 = **REVISE**(Blocker 0, 직전 8건 중 6해결·2부분). 5건 반영: R3 `_appears_for_contradiction` **polarity 제외**(부정 출현은 모순 신호 아님) · R4 **polarity=affirmed** 추가("저혈압 없음"은 모순 아님) · **required 강화**(선별만/부정=screened→**fail**; "필수=환자 *제시*") · **`screened` 버킷 신설**(`_categorize` 4분류 present/weak/screened/missing → red_flags pass에 검토 flagged 안 섞임, R2 Minor 해소) · `_negated` 보강(`않`/`못`/이중부정 가드). **위치인자 버그**(screened 삽입이 `_check_contradiction`/`_check_checklist`의 notes 위치인자를 밀어냄)도 테스트가 검출 → notes= 키워드로 수정. **테스트 24→26.**
- **(Codex R3 → 반영)** R3 = **REVISE**(Blocker 0 · 수렴 R1:8→R2:5→R3:3). 3건 반영: `_locate` **긍정 우선**(전체 scope 스캔 — 한 필드 부정·다른 필드 긍정이면 긍정 채택; first-field masking 해소) · `_NEG_CUES`에 **관계부정**(`무관하`·`관련없` — "운동과 무관"이 exertional "운동" 부분매칭→거짓 모순 내던 것 차단) · red_flags `weak`→flag. **테스트 26→28.**
- **(Codex R4 → 반영)** R4 = **REVISE**(Major 1). R3 3건 중 2 완전해결 확인(운동무관·weak red flag), first-field masking은 surface 내부는 해결됐으나 **동의어 간** masking 잔존(label "실신 없음" + synonym "기절함" → false negative). 수정: `_match` HIGH-tier 후보(라벨+동의어) **수집 → 긍정 우선** 선택. **테스트 28→29.**
- **(Codex R5 → 반영)** R5 = **REVISE**(Major 1). R4 synonym 수정 확인 + 회귀 전부 통과(결정론·R4·운동무관·required). 새 Major = **contradiction R3/R4가 아직 `union`(probe 포함)** → "운동 연관을 물었다"(keyword 운동)가 exertional×no_exertional 거짓모순. 휴리스틱 한계 아닌 **2-렌즈 미전파**(R1 채널혼합 클래스 잔재)라 수정: contradiction을 **`fact_scope` 로 제한**(probe 제외) + 죽은 `union` 제거. **테스트 29→30.** → **R1 채널혼합 클래스가 6검사 전체에서 닫힘(수렴점).** Codex 추이 R1:8→R2:5→R3:3→R4:1→R5:1 전부 반영. 남은 건 휴리스틱·draft = 교수 임상검증 영역.
- **(Codex R6 → APPROVED ✅)** R6 = **APPROVED**(6라운드 만에 승인 — R1~R5 REVISE → R6). contradiction fact_scope 수정 확인(운동 keyword→pass; 진짜 모순=성별·산부인과력·fact채널 상호배타 "계단통증+운동무관"→fail 유지) + 결정론. validator 적대검수 종료. **테스트 30.**
- **(미팅 §7 보강)** 리허설 반영: A질문 열고-대비(Q1 근거=강제 vs 출처, Q2 권고-후-위임), **Q5 검증노동**·**Q6 coverage 의미론**, 2-렌즈 차별점(C 보강), 가드레일, 당일 데모점검.
- **다음**: 설계 리뷰 → 교수 §7 확인 → 교수검증 반영·validator 실사례 적용·사례3 생성.

### 자료 폴더 정리 + 전 문서 실내용 파악 — 2026-07-01
- **새 데이터 8개 확인**(붙임3·급성복통 사례·국시공지·new PPI채점표·신체진찰평가·PPI피드백·환자의사관계채점표·사례개발점검표) — 전부 루트에 흩어져 있던 것.
- **루트 정리**: 문서 26개 → `materials/<01~09_카테고리>/`(gitignored). 코드 `.py`는 루트 유지(import 리스크 회피). `.gitignore`에 `*.docx`·`*.xlsx`·`materials/` 추가(민감 docx/xlsx 커밋 gap 해결). **참고자료(materials/=재료) vs 파이프라인 데이터(data/=가공품)** 구분 명문화(context-map §2 + materials/INDEX.md).
- **전 문서(26) 실내용 추출**(hwp5html 표 + PyMuPDF pdf → `materials/_extracted/`). 핵심 파악: 붙임3≈저자점검표(동일) · **PPI 2방식**(new=4단계 원본 vs 변환=1-0) · 사례개발피드백5=②심사 정답지(D6) · 급성복통=실사례(**PII·비식별 필요**) · Challenges=우리 PI 논문 · 진료수행지침=스캔본(OCR).
- **목차** = `materials/INDEX.md`(로컬·실내용 기반). 커밋 = `.gitignore`·`context-map`·`worklog`만(문서 원본·INDEX·_extracted는 gitignore).

### 흉통 온톨로지 스캐폴드 생성 '전체과정' + Codex 3라운드 협업(설계·출력·최종) — 2026-07-01
- **README 차별점 D축 추가·푸시**: 근거 기반 생성(온톨로지 지식그래프 + LLM wiki + Neo4j + 2-렌즈 validator). (예정)·draft 정직 표기.
- **온톨로지 제약 생성**(`generator.py` `_ontology_constraint` + `generate(ontology=)`): `chest_pain.yaml` ACS 카드의 필수요소(required·감별·red flag·checklist·과공개)를 생성/수정 프롬프트에 주입(누락·과공개 방지). `demo_ontology_pipeline.py`: **baseline(자유) vs scaffolded(제약)** — 동일 model/temp/rounds, 각각 ①생성→②심사→ontology_validator 검증→비교.
- **Codex 설계검수(REVISE)**: 순환성(같은 온톨로지로 검증)·**라벨 누수**(평가라벨 verbatim→trivial coverage↑)·n=1 프레이밍 지적 → 반영: scaffold에 *환자 구어 표현* 지시(verbatim 금지), `matched_by` 분해(trivial/의미), '기계적 스모크·통계 아님·임상 미검증' 주장 상한.
- **Codex 출력검수(REVISE) — 실데이터가 validator FP 4종 적발**(합성테스트가 못 잡은 것): ①diaphoresis `발한`⊂`활발한` ②hypotension keyword `혈압`⊂`저혈압` ③syncope 걱정 "쓰러질까 봐"를 긍정 오인 ④"한 번도 없"의 `없`이 negation window 밖. + 내 발표가 과대주장(red_flags/disclosure 개선이 FP 오염)이던 것도 적발.
- **FP 4종 수정**: diaphoresis 동의어 발한·땀 제거 · keyword-anchor 겹침 min≥3자 · negation cue `까봐`(걱정)·`번도`(한번도 없) · patient 메타필드(thoughts_concerns 등) 자발채널 제외. **회귀테스트 3 추가(30→33 통과).**
- **fresh paired 재실행(고친 validator)**: baseline overall=fail(red_flags fail·disclosure viol2), scaffolded=flag(disclosure **pass**·red_flags asked0.5). **정직한 개선 = 과공개·모순 위반 2→0**, red_flags 선별 0→0.5. required는 n=1 변이(둘 다 pass). 라벨누수 1/13(낮음).
- **정직한 주장 상한**(Codex): "스캐폴드가 draft 카드 요소를 표면화 강제 → 과공개 제거·red flag 선별 일부 개선"까지. 임상타당·통계·논문효과·GraphRAG 우월 주장 **불가**. 산출 `data/working/ontology_pipeline/`(gitignore).
- nit: 데모가 트레이스 export 시도(`LANGSMITH_TRACING=false`인데도) — export 실패(egress 0)나 게이트 손봐야.
- **다음**: Codex 최종검수 → 커밋 → (2주 MVP) 사례3·교수검증.

### (이어서) follow-up 커밋 + LLM wiki 개념정리 + 지도교수 미팅 확정 — 2026-07-01
- **follow-up 커밋·푸시**(2dae15c): 트레이스 게이트(traceable=langsmith_on 시만 적용·데모는 `CPX_TRACE_ACK=0` opt-out) · validator FP/FN trade-off 문서화 · **README 차별점 C(Flowise) 삭제** → A/B/C(C=근거 기반 생성). ⚠️ 원인=`.env` `CPX_TRACE_ACK=1`(tracing 전역 ON) 잔존 — 끌지(=0) 개발 담당 판단 대기.
- **LLM wiki 개념정리**(개발 담당 질문 "llm wiki가 뭐야? 옵시디언 아냐?"): LLM wiki=지식을 **마크다운 위키로 정제**해 LLM이 **롱컨텍스트로 통째로 읽는** 방식(RAG 조각검색 아님; 256k+·turboquant로 가능). **옵시디언≠LLM wiki**(옵시디언=마크다운 에디터·무타입 링크그래프 / 교수님 온톨로지=Neo4j **타입** 그래프). 3층=지식그래프(관계·생성뼈대)·LLM wiki(형식·루브릭)·RAG(큰 교과서)=보완.
- **✅ 온톨로지 방향 확정**(2026-07-01): 온톨로지 적용 결정 — Neo4j 그래프로 구조화 지식 내 LLM 근거 생성. 숙제="CPX 엔티티 뭘로"(→§2.1). **LLM wiki·그래프·RAG 모두 지도교수 단일 비전**(팀 발언=전달). ontology-plan §0 반영.
- **▶ 다음 세션 시작점(개발 담당 계획, /clear 후)**:
  - **⓪ 문서 정합성 검수 먼저** — 모든 컨텍스트 문서가 온톨로지 대전환 이전이라 **stale**(context-map[06-18]·architecture·roadmap·transparency·memory 등). 검수 → stale 갱신 → **단일 총괄 `docs/blueprint.md` 작성(B안: 새 슬림 진입점, 30초→5분→딥다이브 + 상세문서 링크, "이거만 보면 전부").** *(개발 담당: "작업 시작 전 검수 필요, 현재 정보 업뎃 안됨")*
  - ① **흉통 LLM wiki 만들기**(마크다운 정제지식 — CPX 형식·흉통 임상·루브릭)
  - ② **chestpain Neo4j + validator 구현·진행**
  - ③ 설계 리뷰(예정)
  - (준비완료: 흉통 온톨로지·Neo4j·HTML·validator[33테스트, Codex 6R]·스캐폴드 생성 데모[과공개2→0]·§7 리허설.)

### ⓪ 실행 — 문서 정합성 검수 + blueprint(B안) + 3자 블라인드 감사 — 2026-07-01 (이어서)
- **지도교수 원문(verbatim) 정본화**: 미팅 메시지 원문(온톨로지·Neo4j 근거생성 / 숙제=엔티티·keyword 온톨로지·**원인-증상-질환**·**markdown CPX 사례변환**·로컬35B/256k/TurboQuant·LLM wiki·**Skill.MD** / 설계 리뷰(예정))을 `ontology-plan §0`·`AGENTS.md`·memory에 앵커로 박음. **개발 담당 지시 "위 의견대로 따라야 해"** → 로컬35B·LLM wiki·keyword 온톨로지를 *"측정하며 실행할 비전"*으로 전면화, 기존 *"리스크라 미루자"* 저항톤 제거(측정≠저항).
- **stale 5문서 전면 재작성**(개발 담당 "전면 재작성" 결정): context-map(D10/D11 온톨로지 결정·옛 TODO 해소·데이터는 data-inventory 위임) · architecture(**v2→v3** + §4.5 온톨로지 레이어 + §0 다이어그램 3층지식화) · roadmap(07-01 현황·온톨로지 마일스톤) · transparency(validator LLM0·트레이싱·로컬LLM 트랙) · memory("MedQA처럼" 삭제·pivot 반영).
- **`docs/blueprint.md` 신규 = 단일 진입점**(B안: 30초→5분→딥다이브 + 링크). AGENTS·CLAUDE·README·context-map·roadmap 문서지도가 blueprint·ontology-plan 가리키게 배선.
- **Codex + Claude×2 독립·병렬·블라인드 감사**(개발 담당 지시): 축=지도교수 비전 정합·stale·모순·과대주장. **29건 전부 반영**:
  - [BLOCKER] ontology-plan 고아 코드펜스(§5 이후 통째 코드블록 렌더) 삭제.
  - [정합] roadmap ② 모델 gemini→**gpt-5.5**(`build_validation_data.py`로 확정; gemini=보조 발췌) · `locked15`→**17**(`splits.json` 실측) · "저녁 도착" stale 제거 · H2 완료vsTODO 모순 해소.
  - [숙제 정본화] 교수 숙제 **7항목 정본표**(Skill.MD·markdown 사례변환·LLM wiki 포함) — 문서별 부분집합 상이 해소 · **§5.5 로컬 모델·Skill.MD 실행계획 신설**(서지 1줄→실행 홈) · markdown "사례 변환" vs "wiki 정제지식" 갈래 분리.
  - [de-hedge] architecture §1 "오픈모델 후순위"·§0 RAG-only 다이어그램 · ontology-plan §6/§7 "Neo4j 조기도입 위험" → 교수 비전 실행톤.
  - [정직성] README 온톨로지 efficacy caveat 추가·"줄인다"→"줄이는 것을 목표(측정 전)" · ontology-plan 신규성 "논문 없음"→"확인된 범위에선 못 찾음" · `source_id:TODO` caveat.
  - [기타] 원인축 관계(`caused_by`/`predisposes_to`)+§7 · D11 "제안(교수 확인)" 강등 · ④모델 GPT-4o 통일 · ontology-plan 작성일 07-01 · README/data-inventory doc-list·wiki 위치.
- **검증**: 코드펜스 균형·stale 제거·내부링크 broken 0. 11파일 +219/−136 + blueprint 신규. (feedback-todo "팀원 제안"=pre-pivot RAG 역사적 귀속이라 의도적 유지.)
- **§7 교수 확인 포인트(미팅용)**: 원인 엔티티 세분 · markdown 해석(사례변환 vs wiki) · Skill.MD 의도 · Neo4j 정본 여부 · 검증 노동.
- **다음**: 설계 리뷰 → 교수 확인 → 흉통 LLM wiki(다음스텝①)·validator 실사례·사례3.

### 온톨로지 심화 — 형식(YAML 하이브리드)·엔티티 확정 (Claude+Codex 블라인드) — 2026-07-01 (이어서)
- **개념 정리**(개발 담당 요청): 엔티티=그래프 노드(도메인 명사) · 온톨로지=명시적 개념+관계+규칙 스키마(LLM "맥락이해"가 아니라 LLM을 *잡아주는* 구조) · keyword 온톨로지=노드에 한국어 환자표현·질문 트리거 키워드 부착 · **옵시디언≠LLM wiki**(옵시디언=무타입 링크그래프+md에디터 / LLM wiki=산문을 롱컨텍스트로 통째 읽는 *방법*). 3축 분리(표현/도구/형식).
- **로컬 35B "왜?"**: API로 불가능한 게 아님(256k는 API도 됨) — 로컬 선호 이유=거버넌스(저작권·실사례 SaaS 금지)·비용(롱컨텍스트×대량)·재현성/오픈소스/학생무료. trade-off=로컬 품질 약함→API 병행 측정. "왜 로컬인지"는 §7 교수 확인.
- **형식 결정 (Claude+Codex 블라인드 수렴, Codex 85%):** "md vs yaml" 아니라 **YAML=규칙(validator·Neo4j) / MD=위키·사례 / Neo4j=투영.** 근거·공격방어 = `ontology-plan §2.5`. 스플릿뷰 시연 `docs/format-comparison.html`. ⚠️ 전제=결정론 검증이 요구사항(§7).
- **엔티티 설계 (Claude 초안 → Codex 블라인드 보강):** 내 초안(주증상-중심 지식노드)이 **CPX 실행 노드를 놓침** → Codex가 Station/Case·PatientProfile·ClinicalFact·StudentIntent·ExamManeuver·ScoreRule·Provenance 추가 · 과노드화(감별·RedFlag·Education)→관계/역할 축소 · ChecklistItem/DisclosureRule 스키마 보강 · 원인축=별도 Cause노드 X→**RiskFactor+관계타입**(흡연이 여러 질환 위험인자라 "원인" 고정 시 오분류). `§2.1`(엔티티표+MVP단계)·`§2.2`(관계) 정본화.
- **⏸ 파킹 = 구현(용하 결정 B: 설계 커밋·구현 별도):** `chest_pain.yaml` + validator 반영 — 키워드 **코드→yaml** 이동(교수 편집·재현성) + validator 리팩터(33테스트 유지) + Differential 관계화 + DisclosureRule fact단위. MVP-now 범위(Station 등 정식노드=v2).
