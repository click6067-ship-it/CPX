> ⚠️ **[예전 버전 — v1, 현재 사용 안 함]** per-point CSV 방식 옛 설계. 현 정본: **`validation-design.md`**(설계)·**`handoff.md`**(교수 전달)·웹 설문(`web/adjudication/`). 혼동 방지용으로만 보존.

# 교수 adjudication 가이드 (H2 검증)

> 목적: **②AI 심사가 전문가 피드백을 얼마나 재현하나(H2)** 를 검증. 판정자 3명이 **독립** 판정 → Fleiss kappa(일치도) + 다수결 합의(gold).
> 시트: `adjudication_batch1_J1/J2/J3.csv` (각자 자기 것만, 서로 보지 말 것). 배치1 = 10사례.

## 시트 읽는 법
AI가 **전문가 지적 분해 + ②의 후보매칭 + 잠정판정**까지 미리 채워둠. 교수님은 **`PROF_verdict`만 확인·수정**(빈칸 채우기 아님).

| 열 | 의미 |
|---|---|
| pair | 사례 (증상_연도) |
| row_type | **EXPERT_POINT**(전문가 지적) / **AI_FINDING**(②가 든 지적) |
| item | 그 지적 내용 |
| category | 분류 (CLINICAL_CONTENT·STRUCTURAL·INTERNAL_LOGIC·SP_FEASIBILITY·SP_LOGISTICS 등) |
| case_quality | ②가 잡아야 할 사례품질 사항? (N=SP섭외·일정 등 운영) |
| ai_candidate | ②의 대응 지적 (AI 잠정) |
| ai_tentative | AI 잠정판정 (caught/missed) |
| **PROF_verdict** | ⬅ **교수님이 채울 칸** |
| PROF_note | 자유 메모(선택) |

## PROF_verdict 입력값
**EXPERT_POINT 행** (= ②가 이 전문가 지적을 재현했나):
- `caught` — ②가 제대로 잡음
- `partial` — 부분적으로만
- `missed` — 못 잡음
- `excluded` — 이건 사례품질이 아님(SP 섭외·일정 등) → 분석서 제외

**AI_FINDING 행** (= ②가 든 지적이 타당한가):
- `in_expert` — 전문가 피드백에도 있는 것
- `valid_extra` — 전문가는 안 썼지만 **타당한 결함**(②가 추가로 잘 잡음)
- `invalid` — 틀렸거나 환각

## 원칙
- **독립 판정**: 다른 판정자 시트 보지 말고 각자.
- AI 잠정판정은 *참고*일 뿐, 동의 안 하면 바꿔 주세요 (그게 이 작업의 핵심).
- 애매하면 `PROF_note`에 한 줄.

## 이후
3명 결과 → AI가 **Fleiss kappa(일치도) + 다수결 합의(gold) + 카테고리별 recall/precision/F1 + CI** 산출. 배치1로 기준 고정 후 배치2~3(총 30사례)로 확대. *(파일럿/개발단계 — 과대주장 없이 보고)*
