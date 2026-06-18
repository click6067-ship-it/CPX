# H2 파일럿 결과 — ②AI심사 vs 전문가 피드백

2026-06-19. dev_tune 페어 3건(객혈 2022/23/24), 자동 LLM 판정. ⚠️ **파일럿(소표본·자동판정), locked 미사용.**

## 결과: ② recall 5/22 = 23%
- **② 포착(구조적):** 복합질문 분리, 채점표 항목 수 부족, 신체진찰·환자교육 구체화.
- **② 누락(사례특이 임상):** 흡연력 구체화, 직업-건강검진 논리 일관성, 현병력 상세화(가래 양상·체중감소), SP 연령/성별 다양성, 가족 흡연력 등.
- **② 추가지적:** 항목수 부족 등 타당한 점도 일부(전문가 피드백엔 없던).

## 해석 (잠정 — Codex 검수 대상)
- 전문가 피드백은 **사례특이 임상 정교화**인데, 현재 ②는 **일반 점검표 구조 검수**라 결이 다름 → 23%는 *부분적으로 실험 설계 아티팩트* 가능.
- 동시에 ②가 사례특이 임상 지적을 거의 못 하는 **진짜 한계**도 시사.
- → 다음: Codex 검수 판정 반영(실험 재설계 vs ② 강화).

## Codex 검수 판정 (2026-06-19)
**판정: 진단용 smoke로는 유효(구성 불일치 + 임상비평 갭 드러냄). ②의 "진짜 23% 성능" 증거로는 무효.**
- 23% = 혼합 신호: 구성 불일치 아티팩트(일반 구조 점검표 ② vs 사례특이 임상/SP로지스틱스 전문가 피드백; n=3; 자동 judge; 전문가 피드백이 순수 case-quality gold 아님) + ②의 실제 한계(사례특이 임상 비평 약함) 둘 다.
- **고칠 것 = 둘 다:**
  - **② 2층 분리:** `②A 구조 리뷰어`(체크리스트 구조·항목수·복합항목·채점명료·진찰/교육) + `②B 임상 리뷰어`(임상타당성·핵심병력 누락·red flag·위험인자·내적논리·SP 현실성·인구통계·사례특이 체크리스트). 출력 taxonomy(STRUCTURAL/CLINICAL_CONTENT/INTERNAL_LOGIC/SP_FEASIBILITY/SCORING_VALIDITY/EDUCATIONAL_ALIGNMENT/SAFETY_OVERCLAIM) + 각 지적에 evidence·edit·severity·must-fix.
  - **실험 재설계:** 전문가 피드백→atomic label 분해→카테고리화→non-case-quality(SP로지스틱스) 분리→**인간 adjudication**(자동judge=pre-screen만)→per-category recall/precision/F1+valid-extra+bootstrap CI+인간-인간 일치도 먼저.
- **논문 주장 경계:** "AI가 전문가 피드백 재현" ❌ / "교수 검토 대체" ❌. 가능(재설계 후): "개발단계 소규모 평가서 ②가 일부 구조결함 식별, 사례특이 임상 정교화 recall은 제한적; 카테고리별 상이 → 2층 리뷰어 + 인간 adjudication 지지."
- **다음 1수:** 22개 전문가 지적을 adjudicated taxonomy로 relabel → 카테고리별 structural-only ② vs clinical-enhanced ② 재실행.
