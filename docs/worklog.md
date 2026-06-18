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
