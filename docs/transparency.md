# 투명성 — 어디에 어떤 모델·데이터를 썼나 (단일 정본)

> **이 문서가 "무엇을 어디에 썼나"의 단일 출처.** 헷갈리면 여기를 본다. (오픈소스·논문 투명성 + 재현성)
> 최종 갱신: 2026-07-01

## 1. 모델 사용 현황 (컴포넌트별)
| 컴포넌트 | 모델 | 제공사 | API/로컬 | 상태 | 메모 |
|---|---|---|---|---|---|
| **① 사례 생성** | gpt-5.5 (의도) | OpenAI | API | 프로토타입 | 계획서=Claude. Claude 결제 막혀 **gpt-5.5로 대체**(어댑터 1줄 교체) |
| **② 사례 심사**(검증 대상) | **gpt-5.5** | OpenAI | API | **검증 진행** | 최상위. ②A 구조+②B 임상 |
| **③ 가상환자 대화** | GPT-4o | OpenAI | API(음성 STT/TTS) | **미구현** | 계획서대로 |
| **④ 자동채점** | GPT-4o | OpenAI | API | **미구현(나=다음)** | 계획서=GPT-4o |
| **RAG 임베딩(dense)** | **gemini-embedding-001** | Google | API | 사용중 | **임베딩 전용 모델(글→벡터, 생성 LLM 아님)**. 다국어(한↔영). Claude=임베딩 없음, OpenAI도 가능하나 다국어로 Gemini 택. cf. EmbeddingGemma=같은 계열 오픈웨이트 |
| **RAG 검색(sparse)** | **BM25** (rank_bm25) | — | **로컬(모델·API 없음)** | 사용중 | 정확 용어 매칭. dense와 RRF 병합 |
| **보조**(피드백 분해·근거 추출·발췌) | gemini-2.5-flash | Google | API | 사용중 | 빠름·저렴. ②리뷰와 분리 |
| **사례 변환(ingest)** | gemini-2.5-flash | Google | API | 사용중 | hwp→CpxCase. flash-lite는 과소추출이라 flash |
| **적대 검수** | Codex (codex exec) | OpenAI/Codex | CLI | 사용중 | 설계·코드 red-team(메타만, raw 미전송) |
| **로컬 LLM** (교수 비전·계획) | 35B Q4(예: Qwen3-30B-A3B) · 256k · TurboQuant | 로컬 | 로컬 | **계획(미도입)** | 지도교수 숙제 — LLM wiki 롱컨텍스트·근거 생성용. 초기엔 API 병행 비교(`ontology-plan §5.5`) |

- **모델 교체 지점 = `src/cpx/llm.py`** (모델명 prefix로 Claude/GPT/Gemini 자동 라우팅). 결제 풀리면 ①②를 Claude로 1줄 교체 가능.
- 기본값(`GEMINI_MODEL` env)=`gemini-flash-lite-latest` — 명시 모델 안 주면 이게 쓰임. 검증/생성은 위 표대로 명시 지정.
- **⚠️ 온톨로지 validator = 모델 아님(LLM 0회).** `src/cpx/ontology_validator.py`는 **결정론 코드**(키워드·동의어·부정문 매칭)로 생성 사례를 온톨로지 카드와 대조 — API 호출·비용 0. 그래서 위 모델표에 없음. (온톨로지 상세 = `ontology-plan.md`.)

## 2. 계획서(연구책임자) vs 현재 — 정직 비교
- 계획서: **Claude=①생성·②심사, GPT-4o=③대화·④채점.** 임베딩/RAG 모델은 계획서에 **명시 없음**.
- 현재: Claude API 결제가 막혀(한국카드/백엔드) **Claude 자리를 최상위 GPT(gpt-5.5)로 대체.** 결제 풀리면 Claude로 복귀(어댑터). 임베딩=Gemini는 **우리 선택**(다국어).
- 계획서 ⑤ 준수: 외부 API엔 **비식별 데이터만** 입력, **재학습(파인튜닝) 안 함**(프롬프트+RAG 방식).

## 3. 데이터·코퍼스 출처
| 용도 | 파일/위치 | 출처 | 공개 |
|---|---|---|---|
| **RAG 교과서 코퍼스** | `data_clean.zip` → `data_clean/textbooks/en/*.txt` | **MedQA**(jind11) 영어 의학교과서 18권(Harrison·Robbins·Schwartz·Janeway·Williams·Novak 등) | 저작권상 비공개(gitignore) |
| RAG 인덱스(현재) | `data/working/rag_index/textbooks.{npy,json}` | 위 중 **Harrison 1권 샘플 1200청크** | gitignore |
| **CPX 실제 사례** | `data/raw_private/2026-06-18_pusan/` (hwp 170건) | 부산대 양산병원(PI) — 최종85·초안80·피드백5 | **학교자산·비식별·gitignore** |
| 점검표/양식 | `실기문항저자점검표.hwp`·`[붙임2] CPX 개발 양식.hwp` | 부산대 제공 | repo 내 |
| 계획서/연구문제 | `2026년...PI...hwp`·`CPX AI agent 연구문제.hwp` | 연구책임자 | repo 내 |
| 검증 빌드(중간) | `data/working/validation_build/` (data.js·cases_meta) | 위 사례서 생성 | 학교자산·gitignore |

⚠️ 학교자산(사례·피드백)·교과서(저작권)는 **git 커밋 금지**. Codex/외부엔 **메타만**.

**임베딩에 무엇이 들어가나(정확히):** 현재 RAG 임베딩 코퍼스 = **교과서뿐**. CPX 사례는 ②리뷰의 *입력*이라 임베딩 안 함(프롬프트로 통째 전달). **단 ①생성(미구현) 때는 "유사 사례 검색"을 위해 사례도 임베딩 예정**(비식별). 사례는 ②리뷰 시 LLM API엔 비식별로 전달됨(임베딩 API 아님).

## 4. RAG 작동방식 (서버 없음)
**오픈북 시험** 구조 — LLM이 교과서 근거를 보고 ②심사. `src/cpx/rag.py`.
1. **색인(1회)**: 교과서 청크 → 임베딩 API(Gemini) → 벡터 **로컬 파일**(.npy) + 청크(.json)
2. **검색(질의시·하이브리드)**:
   - dense: 질의→임베딩(Gemini API) → 코사인 top-n
   - sparse: BM25(rank_bm25, **로컬 계산**) → 단어 매칭 top-n
   - **RRF 병합**(순위 역수 합) → top-k
3. **주입+생성**: top-k를 ② 프롬프트에 넣어 gpt-5.5가 근거 기반 심사
- **API는 임베딩 1회뿐**(+생성). 저장=파일, BM25·병합=메모리. 그래서 **서버 불필요**(코퍼스 작음). 수백만 청크면 벡터DB(서버) 필요 — 우리 규모는 아님.
- ⚠️ 현재 한계: 영어 교과서만 색인 → 한국어 질의엔 dense(다국어)가 주력, BM25 효과는 **한국 코퍼스 색인 시** 큼. Korean 형태소 토크나이저·전체 코퍼스·리랭커는 후속.

## 5. 키·보안
- 키는 `.env`(gitignore): `GOOGLE_API_KEY`·`OPENAI_API_KEY`(있음), `ANTHROPIC_API_KEY`(결제 보류). 코드/로그에 하드코딩 금지.
- 배포 설문(`web/adjudication/`)은 비식별 검증항목만, 암호게이트+noindex, CPX repo와 분리 배포.

## 6. 관찰·추적 (트레이싱) — 기본 OFF, redaction 필수
파이프라인 재현·감사를 위해 실행 트레이스를 남길 수 있으나, **거버넌스상 기본 OFF**이고 켤 때도 **본문은 마스킹**한다(`src/cpx/tracing.py`).
- **2종:** **LangSmith**(langgraph 네이티브 노드 트리; `LANGSMITH_HIDE_INPUTS/OUTPUTS=true`로 내용 전체 비공개) + **셀프호스트 Langfuse**(데이터가 이 머신 밖으로 안 나감; `Langfuse(mask=_mask)`).
- **egress 게이트:** `CPX_TRACE_ACK` 미동의 시 langgraph-native 추적까지 OFF(SaaS 전송 0).
- **redaction(`_mask`):** 긴/민감 문자열·cpx 도메인모델 → `<redacted:Nc sha256:…>`(해시 보존=재현·감사). 짧은 비민감(role·verdict·log)·수치는 통과. → 부산대 사례·저작권 교과서 본문 **SaaS 비유출** (라이브 검증: LangSmith 업로드분 `inputs={}`, Langfuse observation 전부 마스킹).
- **범위:** 현재 dev 그래프(합성/사례개발)만. **③·④ 실제 학생 상호작용은 추적 제외**(민감·IRB). 공개 트레이스 예시 = `docs/sample-trace-redacted.*` · 셀프호스트 셋업 = `docs/langfuse-selfhost.md`.
