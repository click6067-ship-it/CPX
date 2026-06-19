# H2 F1 codebook — 근사 pseudo-F1(현 집계) + 완전 매칭 F1 SOP(본검증) (C1)

> 목적: recall·precision을 **동일 confusion matrix**로 묶는 매칭 규칙을 *고정*한다. Codex 검수(2026-06-20) 반영 — "표준 F1은 교수·AI 지적 union을 인간이 adjudication한 동일 universe에서만 허용".
> 현 집계(`aggregate_validation.py`)는 설문의 recall(교수 point view) + precision(finding view)을 결합한 **근사**다. 완전 매칭 adjudication SOP는 본검증.

## Universe (분석 대상 집합)
**교수 지적(gold points) ∪ AI 지적(findings).** 둘이 같은 결함을 가리키면 하나의 매칭으로 본다.

## 매칭(TP) 판정 — 다음 셋을 모두 만족할 때만
1. **같은 결함 범주**(category: CLINICAL_CONTENT·STRUCTURAL·INTERNAL_LOGIC 등)
2. **같은 수정 행동**(suggested edit의 방향이 실질적으로 동일)
3. **같은 임상 중요도**(severity 등급 일치)

## 설문 라벨 → confusion matrix 매핑
| 설문 라벨 | confusion | 의미 |
|---|---|---|
| 교수 point = `caught` | **TP** | AI가 교수 지적을 잡음 |
| 교수 point = `missed` | **FN** | AI가 놓침 |
| 교수 point = `partial` | **FN**(보수적) | 부분만 → 미달로 처리 |
| 교수 point = `excluded` | 분석 제외 | 사례품질 아님(SP 섭외·일정 등 운영) |
| AI finding = `wrong`/`harmful` | **FP** | AI가 틀린/유해한 지적을 함 |
| AI finding = `valid_major`/`valid_minor` | **추가기여**(별도 축) | 교수엔 없지만 타당 — FP 아님, AI 보너스로 별도 보고 |
| AI finding = `redundant` | TP의 AI측 뷰 | 교수와 중복 → 이중계산 방지 위해 따로 세지 않음 |

## 지표
- **precision** = TP / (TP + FP)
- **recall** = TP / (TP + FN)
- **F1** = 2·TP / (2·TP + FP + FN)
- **추가기여율(별도)** = valid_extra / (전체 AI finding) — "AI가 교수보다 더 잡았나" (F1과 다른 축)

## 한계 (정직) — 현 집계는 "근사 pseudo-F1"이다 (Codex 검수 반영)
- **매칭 미adjudication**: 설문은 교수 point(caught/missed)와 AI finding(validity)을 *별도로* 받고, 집계는 둘을 매칭하지 않는다. TP는 교수 point 뷰, FP는 finding 뷰 → **같은 매칭쌍 기준이 아님**. 그래서 출력 명칭도 "근사 pseudo-F1"(진짜 F1 아님).
- **1:1 bijection 가정(미검증)**: caught 1 ↔ redundant 1을 암묵 가정. broad finding 하나가 여러 point를 잡거나 중복 finding이 많으면 왜곡. 본검증 adjudication이 해결.
- **reproduction 관점**: 이 F1은 "AI가 교수 지적을 재현했나"(recall 중심) 근사다. `valid_extra`(교수엔 없는 타당 지적)는 reproduction이 아니라 **AI 추가기여**라 F1에서 제외(별도 축). union F1(valid_extra 포함)은 본검증에서.
- **완전 F1 SOP(본검증)**: 교수·AI 지적 union을 **인간 2인이 독립 매칭→합의(adjudication)** + 매칭 입력을 받는 설문. LLM 단독 매칭 금지(순환).
- 동률 consensus는 `ambiguous`로 제외(임의 확정 안 함). `partial`=FN(보수적). 파일럿 소표본 → **exploratory**.

## 적용 시점
교수 평가 데이터(`/api/results`) 수신 후 `aggregate_validation.py`가 위 매핑대로 자동 산출. 현재는 codebook(정의)·집계 코드·demo 검증만 완료(수치 주장 없음).
