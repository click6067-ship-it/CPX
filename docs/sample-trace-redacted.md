# 공개 샘플 트레이스 (redaction 적용)

> 실제 LangGraph 사례개발 그래프 **1회 실행**. 사례·교과서(RAG) 본문은 `tracing._mask` 로 마스킹(길이+sha256). 흐름·verdict 같은 비민감 정보는 그대로 — *투명성은 유지, 본문은 비노출*.

- 입력: 주증상=`어지러움` · 진단=`양성돌발두위현훈(BPPV)` · max_rounds=1 · ②B(임상)=on
- 기본 모델: `gemini-flash-lite-latest` · 총 44,542 ms · LLM 호출 6회

## 파이프라인 로그 (비민감)

- ① 생성
- ② 심사: ②A=Minor·②B must_fix=3·optional=1
- ✏️ 수정 R1
- ② 심사: ②A=Minor·②B must_fix=1·optional=2
- 종료: ⚠️ 미충족 (max_rounds 1 소진)

## LLM 호출 (input/output redacted)

| # | 함수 | 모델 | input (redacted) | output (redacted) | out chars | ms |
|---|---|---|---|---|---|---|
| 1 | `complete_json` | gemini-flash-lite-latest | `<redacted:2309c sha256:b1df50096a07>` | `<CpxCase redacted>` | 3,891 | 5,850 |
| 2 | `complete_json` | gemini-flash-lite-latest | `<redacted:6365c sha256:d9c03bbb77db>` | `<ReviewOut redacted>` | 1,688 | 12,907 |
| 3 | `complete_json` | gemini-flash-lite-latest | `<redacted:8078c sha256:4de016ed7bac>` | `<ClinicalReview redacted>` | 1,169 | 3,363 |
| 4 | `complete_json` | gemini-flash-lite-latest | `<redacted:6575c sha256:881e2f49be2b>` | `<CpxCase redacted>` | 5,434 | 8,947 |
| 5 | `complete_json` | gemini-flash-lite-latest | `<redacted:8645c sha256:d48450a17231>` | `<ReviewOut redacted>` | 1,683 | 3,777 |
| 6 | `complete_json` | gemini-flash-lite-latest | `<redacted:10370c sha256:0b68872cd67b>` | `<ClinicalReview redacted>` | 976 | 6,090 |

> 재현: `CPX_TRACE_ACK=1 PYTHONPATH=src .venv/bin/python scripts/sample_trace.py`. redaction 규칙 = `src/cpx/tracing.py` `_mask`. 같은 본문 → 같은 sha256(변조 검증 가능).