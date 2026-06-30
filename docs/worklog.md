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

### 교수 adjudication 인프라 — 배포형 설문 + 집계 파이프라인 — 2026-06-19 (용하 지시)
- **배포 설문 웹앱**(`web/adjudication/`, Vercel): 교수가 **주소+암호만** 받아 한 문항씩 클릭(AI 잠정판정 미리선택) → **중앙 자동수집**(Blob). 3명→N명 확장. 암호 게이트+noindex+URL추측불가, CPX repo와 **분리 배포**(사례데이터 안 올라감). Live: cpx-adj-web.vercel.app. **현재 토이데이터** — 실데이터는 PI 동의 후 전환(SURVEY_PW+CSV교체+재배포, 판정자/관리자 암호 분리 예정).
- 스크립트: `build_adjudication_sheets.py`(CSV 생성, 배치1=9페어·전문가지적84·②지적76) · `build_adjudication_html.py`(오프라인 단일HTML 대안) · `build_survey_data.py`(CSV→data.js+items_meta.json, 실데이터 검증: 73지적/카테고리분포) · `aggregate_adjudication.py`(**Fleiss kappa+다수결 합의+카테고리별 recall/precision/F1+페어부트스트랩 CI**, `--demo`/`--url` 지원, 데모+live e2e 검증 완료).
- excluded(사례품질 아님) 다수결은 분모 제외 = Codex 지적 구성불일치를 사람판정으로 교정. tie는 재검토 플래그.
- 다음: PI 동의 → 실데이터 전환 → 교수 판정 → 집계(첫 진짜 H2 결과). 배치2~3로 30페어 확대. locked15 봉인 유지.

### H2 검증 v3 — Codex 3라운드 적대검수 후 전면 재설계·재배포 — 2026-06-19 (용하 지시: "codex랑 끝까지 완벽하게")
- **Codex 적대검수 3회**(메타만): R1(v1 설계)·R2(v2 설계) **둘 다 REVISE** → R3(v3 구현) **PILOT-OK**. 상세 `docs/validation-design.md`.
- v1(per-point 분해→LLM매칭→인간 caught) 결함: 순환측정·앵커링·정보부족·약한주지표·precision누락·pseudoreplication. → **v3 전면 재설계**.
- **v3 = case 중심·전체맥락(생략0)·블라인드 비교**: 사례별 [초안 전문 + 교수 피드백 vs AI 리뷰 블라인드 루브릭(완전성/정확성/유용성/안전성 1~5, BARS앵커, 블라인드성공 점검) + 공개후 per-point recall + AI지적 precision]. 라디오·모드분리(blind/recall 코호트)·읽음확인.
- ② 모델 **flash-lite→gemini-2.5-flash 격상**(harness 모델-agnostic, pro/Claude는 본검증 freeze). 사례 전체 심사(truncation 30k).
- 집계 `aggregate_validation.py`: blind 차이+**case-cluster CI**·**ICC(2,k)**·**블라인드 성공률**·recall+Fleiss+LOO·precision+**harmful 안전게이트**·(judge,mode) dedup. e2e(제출→--url) 검증 완료.
- Live 6사례(객혈·고혈압·관절통증·구토·기분변화·기억력저하) 배포. 판정자/관리자 암호 분리.
- ⚠️ Codex 강조 = **feasibility/파일럿**(확정주장 금지: "AI가 전문가에 필적/대체" ❌). 본검증엔 사전등록·δ·코호트분리·표본확대 필요. 스크립트: `build_validation_data.py`·`aggregate_validation.py`·`web/adjudication/`.

### v3 마감 — PII 강화·온보딩·Codex 최종QA 수정·목차 — 2026-06-19
- **PII 긴급수정**: 배포 초안에 개발자 실명·전화·이메일·CSS 노출 발견 → ingest deid 강화(개발자 블록 제거·공백/도메인깨진 이메일·전화 마스킹·style/CSS/페이지머리말 제거). 전수 재검 0. `deid_archive.py`로 170파일 안전텍스트본 바탕화면 zip.
- **온보딩**: 콜드 교수용 안내(연구주체·목적·점수·자발성·한계). 개발자=**조호영·채원우·김용하**. IRB·동의서·기입칸 미사용(용하 결정).
- **Codex 최종 QA(R5, FIX-FIRST) 6개 수정**: ①블라인드 길이격차 극단(고혈압 78x) **제외**→기침 대체 ②집계 `--mode` 코호트필터(혼용오염) ③submit 서버 스키마검증+집계 결측경고 ④집계가 meta의 blind만 신뢰(클라조작 차단) ⑤성함 공백정규화 ⑥백업다운로드 pw 제거. +모드화이트리스트·메모칸·초안전체보기·예외처리. 전부 e2e 검증.
- **목차 기능**(조호영 제안): 초안 섹션(상황지침·현병력·신체진찰…) 목차칩 → 클릭시 해당 섹션 점프(지적↔본문 대조 편의).
- 가독성: 초안·검토의견 섹션/○/N번 줄바꿈+들여쓰기(fmtDraft/fmtReview). 6사례 라이브.

### gpt-5.5 ② + 3사 어댑터 + RAG 하이브리드 + 좌우비교·근거하이라이트 + 교수 파일럿 준비완료 — 2026-06-19
- **모델**: Claude 결제 막힘(한국카드/백엔드) → 계획서 Claude자리 = 최상위 GPT(**gpt-5.5**). `llm.py` 3사 라우팅 어댑터(claude/gpt/gemini, 추론모델 temperature 패치). 결제 풀리면 1줄 교체. 임베딩=Gemini 유지.
- **② 간결튜닝**(verbosity↓)+16상한 → 사례당 16지적, 블라인드 길이격차 **1.3~2.3x**(was 5~9). 근거 하이라이트(finding별 quote)·**좌우비교 레이아웃**·목차 점프(조호영 제안).
- **RAG 하이브리드** 구현: dense(Gemini 임베딩)+sparse(BM25, 로컬)+RRF. 코퍼스=MedQA 교과서(Harrison 샘플 1200청크). 사례는 ②입력이라 임베딩X(①생성 때 비식별 임베딩 예정).
- 문서: `docs/transparency.md`(모델·데이터·RAG 정본)·`docs/validation-design.md`(Codex 5R)·`docs/handoff.md`(교수 전달).
- **교수 파일럿 준비완료**: 6사례 gpt-5.5 라이브, PII0, 수집함 클린. 다음 = 교수 응답 → `aggregate_validation` 집계(첫 실결과).

### 설문 A1~A6 + 하이브리드 모드 + 다이어그램 + README/문서 정리 — 2026-06-19~20 (용하 지시)
- **설문 A1~A6**(조호영 피드백): A1 생성/채점 경계 안내(상단 고정), A2 영어약자 `abbr`(Hx/PE/Edu/PPI 자동·중복방지), A3 의견 A/B별 주관식, A4 `?mode=browse` 자유열람(블라인드·판정 없음), A5 browse 사례별 자유메모, A6 검증데이터 오분류 스캔(clean). 배포·검증.
- **하이브리드 모드**(`?mode=hybrid`): 교수가 사례별 "블라인드 평가(eval)" 또는 "열람만(browse)" 선택 → eval만 정량·browse 정성. 블라인드 무결성 유지+부담↓. 집계에 hybrid 추가(pick=eval 필터·선택편향 진단). Codex review 반영.
- **작동방식 다이어그램**: mermaid(README·`cpx-flow.md` 자동렌더) + excalidraw 2버전(Claude 직접좌표 vs Codex 병렬생성, 둘 다 겹침0) → **용하 Claude 버전 확정** = `docs/cpx-flow.excalidraw` 정본 + 온라인편집 링크. `scripts/build_excali.py`(좌표 그리드)·`preview_excali.py`(PNG 검증). README 이미지화. Napkin용 텍스트(`diagram-text-for-napkin.md`).
- **README 전면 개편**: 데이터·코퍼스·모델 표 명확화 + 작동방식 이미지. **"MedQA처럼/식" 비유 전부 삭제**(README·roadmap·AGENTS — 추후 분쟁 방지, 데이터 출처 인용만 유지).
- **암호 진단**: 설문 진입=응시암호(`cpx-pnu-2026`), 결과취합=관리자암호(`cpx-adm-2026-x7k`, `/api/results` 전용). 혼동 해소(설문에 관리자암호 넣어 403났던 것).

### 기술보고서 PDF (교수 디펜스용) — Codex 2라운드 적대검수 — 2026-06-20 (용하 지시)
- **`docs/techreport-cpx.md`/.pdf** (14p, 바탕화면): 배경·전체구조·작동방식·아키텍처·데이터/코퍼스·모델·H2검증설계·RAG·SOTA근거·한계·로드맵 + **예상질문 디펜스 Q&A 11개**. 일반인 이해 목표. pandoc+weasyprint(한글 Malgun), 다이어그램 이미지 임베드.
- **Codex 적대검수 2R**(REVISE→REVISE 둘 다 반영): 과대주장 톤다운("필적"→재현정도 측정·"학원"→연구용 시뮬레이터·"교수 대행"→보조·"오류3.3%"→외부문헌수치 우리 미측정), 사실정확화(임베딩=색인+질의+생성·RAG=Harrison샘플·FSM=설계안), 모델ID 일관화(설문 README gemini→gpt-5.5), IRB 상태 분리.

### 남은작업 안전순서 (Codex 적대 계획) + A1·C1·거버넌스 — 2026-06-20 (용하: "전부 다 세심하게")
- **Codex 적대 계획검수**(REVISE): "전부 동시"는 순환검증(H2 전 생성강화)·저작권(seed변형)·가짜지표 위험 → **안전순서 확정**: H2(교수대기)→C1→A1→거버넌스→B2. A2·A3·B1·B3 연기. (용하 결정: 비식별·로컬전용이면 B2/A2 가능)
- **A1** ②B 임상리뷰어를 ①생성 루프 연결(`generator`/`graph`): ②A 구조+②B 임상(RAG), 종료조건 ②A∈{Accept,Minor} AND ②B must_fix=0. Codex review 2R: 재심사 루프 통일·종료상태 플래그·optional 보존·②B 스위치. ⚠️ H2 안전성 확인 후 프로덕션(현재 프로토타입).
- **C1** 근사 pseudo-F1 + `docs/f1-codebook.md`: 교수point↔AI finding 매칭규칙·TP/FP/FN·완전 adjudication SOP(데이터 오면 적용). Codex review 2R: "진짜 F1"→"근사 pseudo-F1"(매칭 미adjudication·1:1가정 명시)·동률=ambiguous 제외·finding 결측검사. ⚠️ 코드+demo만, 수치주장 없음.
- **거버넌스** `src/cpx/governance.py`: near-copy(char-ngram containment+sliding window, 부분복제 탐지)·provenance(generator 연결)·버전freeze·단가(gpt-5.5 $5/$30). `data-governance §7` provider data-use 표(Google free-quota=학습→유료tier 필수·feedback제출금지·의료제한). Codex review 1R 반영(4gram자카드→containment, 단가 웹확인).
- **다음 = B2**: 가용 한국자료(점검표·양식) 색인 + RAG 평가셋 + `build_validation_data` near-copy 통합 + 진료수행지침 PI 요청. (연기: A2·A3·B1·B3 / 대기: 교수 파일럿 응답·README excalidraw export)

### LangGraph 네이티브 렌더 (코드-정본 시각화) — 2026-06-26 (용하 지시)
- **요청="flowise로 랭그래프 시각화"** → 함정 지적: Flowise는 기존 LangGraph 코드를 불러와 렌더하지 못함(자체 포맷·노드, 캔버스 수동 재구성=실제 코드와 분리된 mock). 학술 투명성엔 부적합. → 용하 결정: **LangGraph 네이티브 렌더** 채택.
- **`scripts/render_langgraph.py`**: `graph.build().get_graph().draw_mermaid()`/`draw_mermaid_png()` 로 *실제 컴파일된* 그래프를 그대로 출력. 손그림 `cpx-flow.*`(전체 시스템 아키텍처)와 달리 코드 100% 일치·재현가능. 키 불필요(렌더는 구조만, 실행 아님).
- 산출물: `docs/cpx-langgraph.mmd`(mermaid, 네트워크불필요) + `docs/cpx-langgraph.png`(mermaid.ink). 구조: `start→generate→review`, `review⇢end`(조건), `review⇢revise`(조건), `revise→review`(수정 루프). graph.py와 일치 확인.

### 관찰·추적(Langfuse + LangSmith) + Flowise 캔버스 — 2026-06-26 (용하 지시: "지금바로")
- **트레이싱 2종 연결** (`src/cpx/tracing.py`, no-op safe·env-gated): 이 레포는 langgraph+raw SDK(LangChain 래퍼 X)라 2층으로 붙임 — ① 노드 트리: LangSmith=langgraph 네이티브(env), Langfuse=CallbackHandler를 `graph.invoke(config)`로 전달 ② LLM generation(raw SDK 사각지대): `llm.complete/complete_json`을 `@traced(run_type="llm")`로 감싸 LangSmith span+Langfuse generation 생성. `graph.develop_case`에 run_config+flush 배선.
- **거버넌스 존중**: `.env` "추적 기본 OFF(민감데이터 SaaS 전송 주의, architecture §7)" 명시 → 임의로 켜지 않음. 키만 채우고 `LANGSMITH_TRACING=true` 1회 토글로 활성. `.env`/`.env.example`에 LANGFUSE_*·LANGSMITH_PROJECT 추가. requirements에 langfuse+langchain(=langfuse CallbackHandler 요구). 검증: off-path(둘 다 off=무영향)·on-path(더미키로 콜백주입·observe적용, LLM호출 0=무비용) 둘 다 PASS. ⚠️ 대시보드 실트레이스는 유효키+라이브런 필요(용하 몫). dev 그래프는 합성사례라 PII위험 낮음·③④ 학생런타임 추적 시 거버넌스 재검토.
- **Flowise 캔버스**(원래 요청): Flowise는 LangGraph 코드를 자동렌더 못함 → 자체 빌더 캔버스에 수동 재구성. `flowise/cpx-case-loop.agentflow.json`(Agentflow V2, 7노드·7엣지) = graph.py와 구조 동일(종료조건 ②B must_fix 세부는 graph.py 정본·Flowise route 단순화)(Start formInput→generate→review→Condition[Accept/Minor→확정·Else→수정]→revise→loop(maxLoopCount=2)→review). `flowise/build_agentflow.py`가 Flowise 내장 템플릿의 검증된 노드 블록을 추출·재조립(id/앵커 일괄치환). 구조검증 통과(엣지 핸들·앵커·loopBackToNode·targetHandle 규약 0에러). flowise 전역설치+서버 :3100 기동. API import는 3.x 인증(401) 막힘 → UI Load로 import(README 절차). `docs/cpx-langgraph.png`(네이티브 렌더)와 별개 산출물.
- **(후속) Flowise import 실제 완료 + 캔버스 스크린샷**: 401은 `x-request-from: internal` 헤더 누락이었음 → OSS 첫 계정은 즉시 ACTIVE(account/register, 이메일인증 불필요) → 로컬관리자(admin@cpx.local) 생성 → 로그인 → `/api/v1/chatflows`(type=AGENTFLOW) POST 로 플로우 import 성공(id 065caee8, 7노드·7엣지 보존 확인). puppeteer(번들 chromium) 폼로그인 → `/v2/agentcanvas/<id>` 헤드리스 렌더 캡처 = `flowise/cpx-flowise-canvas.png`(7노드·7엣지, graph.py와 구조 동일(종료조건 ②B must_fix 세부는 graph.py 정본·Flowise route 단순화)). `flowise/shot.js` 재현용.
- **(후속) README 차별점 (예정) 섹션 추가** (용하: "트레이스 공개로 ㄱㄱ, 전부 (예정)"): 3축 — A 임상전문가 검증루프(expert-in-the-loop, H2 대기) · B 재현성·투명성(시스템프롬프트+실행트레이스 공개+Pydantic 스키마강제) · C 비전공자 이해가능성(Flowise 설명캔버스+LangGraph 네이티브렌더). 전부 (예정) 태그·과대주장 금지 톤·"Flowise는 엔진 아닌 설명용" 명시. Codex 적대검수는 미실행(권장).
- **(후속) Codex 적대검수 반영 (4건)**: [BLOCKER] flowise 로컬 admin 비번 커밋 → 제거·env화(shot.js `FLOWISE_EMAIL/PASSWORD`) · [BLOCKER] 추적 전역계측이 사례+저작권RAG를 SaaS 업로드 → `CPX_TRACE_ACK` egress 게이트 추가(미동의 시 langgraph-native까지 OFF, tracing.py가 LANGSMITH_TRACING 자동관리) · [MAJOR] Flowise route가 must_fix=0 게이트 누락 → "1:1" 주장 완화+단순화 명시(graph.py 정본) · [MINOR] Pydantic이 hallucination 차단 과대주장 → "형식·스키마 차단; 임상 사실성은 별도검증"으로 완화. `flowise/.cookies`(세션JWT) gitignore.
- **(후속2) Redaction 레이어 + README 정리** (용하 지시): 트레이스 egress 직전 사례·RAG 본문 마스킹(`tracing._mask`) — 긴/민감 문자열→`<redacted:Nc sha256:…>`(해시 보존=재현·감사), cpx 도메인모델→`<Type redacted>`, 짧은 비민감(role·verdict·log)·수치는 통과. LangSmith=내용 전체 비공개(`LANGSMITH_HIDE_INPUTS/OUTPUTS=true`), Langfuse=`Langfuse(mask=_mask)`(CallbackHandler+@observe 모두 거침, 모듈로드 시 마스킹 싱글톤 선초기화). → 부산대 사례·저작권 교과서 본문 SaaS 비유출. README 차별점: **Pydantic 불릿 삭제**(과대주장 소지·축 혼란), B 트레이스 공개를 "자동 마스킹하여 공개"로 안전화, **C "비전공자"→"일반인"**. .env/.env.example redaction 자동 명시.
- **(후속3) 라이브 redaction 검증 + 공개 트레이스 산출물** (용하: "라이브 확인하고 로그 전체 공개"): `scripts/sample_trace.py` 로 graph 1회 실행(gemini-flash-lite, LLM 6회: 생성→②A→②B→수정→②A→②B). `tracing._mask` 로 사례·RAG 본문 마스킹 → `docs/sample-trace-redacted.{json,md,html,png}`. **LangSmith 라이브 업로드분 API로 확인 = `inputs={}`·outputs 없음(내용 0)** → redaction이 SaaS에서 실제 작동. 공개 권장 = 텍스트 정본(md, 검색·재현·해시검증) + 스샷(README 임베드). README 차별점에 "공개 트레이스 예시" 섹션 추가.
- **(후속4) 셀프호스트 Langfuse 라이브 검증** (용하 결정: self-host, sudo 제공): docker 설치(v29.6) → langfuse 공식 compose 기동(web 포트 3000 충돌 → 3100 `!override`) → **헤드리스 init**(`LANGFUSE_INIT_*`)으로 org·project(`cpx-ai`)·API키·admin 자동생성(브라우저 수동작업 0) → CPX `.env` 연동(`CPX_TRACE_ACK=1`). 라이브 트레이스 1회(**Langfuse만·LangSmith off = egress 0**) → API 검증: observation 13개 전부 마스킹(LLM input `<redacted:sha256>`, output/노드 state `<CpxCase/ReviewOut/ClinicalReview redacted>`), **누출 0**. 대시보드 스샷 `docs/langfuse-trace-detail.png`. 가이드 `docs/langfuse-selfhost.md`, 스샷 스크립트 `scripts/langfuse_shot.js`. README 공개 트레이스 섹션 = 셀프호스트 대시보드 스샷. (langfuse 스택은 `~/langfuse` 외부폴더, 키·비번은 gitignore된 .env들에만.)

### 7/2 온톨로지·지식그래프 미팅 준비 문서 + Codex 적대 리서치·레드팀 통합 — 2026-06-30 (중단 세션 복구)
- **배경**: 박정빈 교수 미팅 제안("온톨로지+Neo4j 지식그래프로 LLM이 근거 갖고 사례 생성") + 채원우 제안("로컬 35B Q4 256k + LLM wiki + 키워드 온톨로지"). 용하 질문 "GraphRAG랑 LLM wiki 다른 거 아냐?" → 리서처+적대검증으로 정밀구분 확정.
- **`docs/ontology-meeting-prep.md` (v2)**: §0 두 제안=다른 층(박정빈=관계구조/채원우=지식포맷·모델) · §1 개념(온톨로지=의미설계/Neo4j=그릇/LangGraph≠지식그래프) · §2 **GraphRAG vs LLM wiki 정밀구분**(둘 다 선택적검색, 진짜 차이=기계지향그래프 vs 인간가독산문 + 자동추출 vs LLM큐레이션, Karpathy 본인 "RAG 대체 아님") · §3 결정프레임워크 · §4 엔티티/관계/엣지속성 + 표준재사용(MONDO/HPO/SNOMED/LOINC/RxNorm) · §5 SKOS · §6 Qwen3-30B-A3B/TurboQuant · §7 리스크·kill · §8 미팅정렬 · §9 출처.
- **중단·복구**: 직전 세션이 deep-research Workflow + Codex 백그라운드 리서치 띄운 직후 종료 → 둘 다 산출 전 사망. **Codex(gpt-5.5) 세션을 `codex exec resume`로 복구** = 웹검색 30여 건(완료분) 그대로 활용해 최종 리포트 생성. deep-research 재실행은 용하 결정으로 생략(v1 출처 충분).
- **§10 = Codex 독립 리서치·레드팀 통합** + 본문 v1 교정(⚠️ 포인터): **①질환-중심→주증상-중심**(ChecklistItem·RedFlag·CpxStationMeta·PPI 계층 필수) · **②온톨로지≠Neo4j**(YAML/JSON disease card+validator로 그래프-스캐폴드 70% 즉시 구현, 온톨로지는 v2+ 불필요) · **③한국 SNOMED 2020년 39번째 회원국**(NRC 통해 추가비용 없이) · 레드팀 결함 7+kill조건 · 교수 예상질문 7+약점 · **2주 MVP 최단순 스코프**(흉통 1개·질환 5개·validator·사례 3개, 그래프DB 아님) · 미팅 최종 권고 멘트("표준 참조하되 핵심은 한국 CPX 수행항목·환자 응답정책; 1주증상 카드부터; Neo4j는 다음 확장").
- **(후속) 해석 정정 — 박정빈 교수 = 결정권자(왕)** (용하 지시): 채원우 발언은 *박정빈 교수 안의 전달*이지 별개 의견 아님 → **미팅 입력 전부를 박정빈 교수의 단일 비전으로 해석.** 우리 자세 = 반박·대안 아니라 **그 뜻을 정확히 해석해 충실히 실행**(최대 리스크=의도 오해). 문서 §0(2인 정렬 프레이밍 폐기)·§8(→교수님께 확인할 해석 포인트 4개)·§10.6(멘트를 "우리가 Neo4j 미룬다"→"전환 시점은 교수님 결정대로")·§8C("Pattern A/B" 내부용어 미팅서 미사용) 톤 교정. *단계화(YAML 먼저)는 그 비전에 더 빨리·정확히 도달하는 수단이지 다른 안 아님 — 시점은 교수님께.*
- **(후속2) 단일 계획서로 통합 + 옛 문서 삭제** (용하 지시: "이전버전 헷갈리지않게 삭제, 전체 설계구조 계획서, 흉통 좁게 시작"): `ontology-meeting-prep.md`가 v1 본문+⚠️교정+§10 3겹이라 혼란 → **`docs/ontology-plan.md` 단일 정본 설계 계획서로 통합**(개념좌표·전체 설계구조(주증상-중심 엔티티/관계/3종 엣지속성/표준+한국어/YAML→Neo4j)·생성 파이프라인(그래프-스캐폴드+validator, 기존 멀티에이전트·LangGraph와 추가레이어 관계)·**흉통 chest_pain.yaml 질환5 초안(ACS+감별4, review_status:draft)**·validator 6검사·2주 MVP·리스크7·미팅메모). `ontology-meeting-prep.md` 삭제(가치내용 전부 흡수). 임상 YAML은 교수 검증 전 초안 명시.
- **(후속3) 흉통 온톨로지 실파일 + 시각화(YAML 정본 + Neo4j 거울) 구현·검증** (용하 "ㄱㄱ"): RAG 역할 = "큰 교과서 전용 조연(축소중)" 명확화(§1) · 저장 = **YAML 정본 + Neo4j/HTML 한 방향 렌더 뷰**(§2.5, Neo4j 조기 운영·동기화 리스크 회피). 산출: `ontology/chest_pain.yaml`(질환5=ACS+감별4, 한국어 라벨맵, **review_status:draft** 임상 교수검증 전) · `scripts/ontology_graph.py`(공통 빌더)·`yaml_to_cypher.py`·`yaml_to_html.py`·`graph_shot.js` · `docs/chest_pain-graph.html`(서버0 인터랙티브 vis-network)·`.png`(스샷). **검증**: 생성 65노드·70엣지 → docker neo4j:5 로드(cypher-shell, 새 py의존성0) → 타입쿼리("ACS 감별질환"·"red flag 질환") 동작 확인 → HTML headless chrome 스샷(흉통→ACS→감별4 색분류·타입엣지). = 옵시디언(무타입)이 못 하는 타입그래프 질의를 미팅서 시연 가능. (neo4j 컨테이너 cpx-neo4j 로컬 :7474, 비번 로컬용.)
- **다음**: 7/2 미팅 → 교수 확인(§7 해석포인트) → 흉통 chest_pain.yaml 교수검증 반영 + validator(`src/cpx/`) 구현 + 사례3 생성·리포트. (Neo4j 전환 시점은 교수님 결정대로.)
