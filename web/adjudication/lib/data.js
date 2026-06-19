// 토이(가상) 데이터 — 실제 부산대 사례 아님. 구조 예시 + 데모 배포용.
// 실데이터는 build_validation_data.py로 생성해 /tmp 배포폴더에만 두고 git 커밋 금지(학교자산).
const cases = [{
  case_id: "흉통_가상", symptom: "흉통", dx: "가상(시연용)", year: "0000",
  draft: "[가상 사례 — 실제 아님]\n■ 상황지침: 52세 남성이 2시간 전 시작된 가슴 통증으로 응급실에 왔다.\n■ 현병력(환자 말투): \"가슴 가운데가 짓누르듯 아파요. 식은땀도 나고요. 담배는 좀 핍니다.\"\n■ 과거력: 고혈압. ■ 활력징후: 150/95, 맥 92, 호흡 20, 체온 36.7 (상황지침과 신체진찰에 중복 기재)\n■ 신체진찰 / 체크리스트(병력청취·신체진찰·환자교육·환자의사관계) 항목들…",
  expert_review: "현병력에 흡연력을 갑년(pack-year)으로 정량화해야 함. 감별진단에 급성관상동맥증후군 외 대동맥박리를 추가할 것. 활력징후가 상황지침과 신체진찰에 중복 기재되어 있어 정리 필요.",
  ai_findings: [
    { id: "F0", text: "흡연력이 정량적으로 기술되지 않음(갑년 명시 권장)" },
    { id: "F1", text: "활력징후가 두 곳에 중복 기재됨" }],
  expert_points: [
    { id: "P0", text: "흡연력을 갑년으로 정량화", category: "CLINICAL_CONTENT" },
    { id: "P1", text: "감별진단에 대동맥박리 추가", category: "CLINICAL_CONTENT" },
    { id: "P2", text: "활력징후 중복 기재 정리", category: "INTERNAL_LOGIC" }],
  blind: { A: "expert", B: "ai" }
}];
module.exports = {
  cases,
  PW: process.env.SURVEY_PW || 'cpx-demo',
  ADMIN_PW: process.env.ADMIN_PW || process.env.SURVEY_PW || 'cpx-demo',
  IS_DEMO: !process.env.SURVEY_PW,
  MODEL: process.env.REVIEW_MODEL || 'toy'
};
