// CPX adjudication 설문 데이터.
// ⚠️ 현재 = 토이(가상) 데이터. 실제 부산대 사례 아님. PI(교수) 동의 후 실데이터로 교체.
// 실데이터 교체 = 이 파일만 재생성(CSV→items) 후 재배포. 암호는 SURVEY_PW 환경변수.
const items = [
  {id:'E1',type:'EXPERT',pair:'흉통_가상',item:'현병력에 흡연력(갑년)을 정량적으로 기술해야 함',cat:'CLINICAL_CONTENT',cand:'흡연력 정량화 누락',tent:'caught'},
  {id:'E2',type:'EXPERT',pair:'흉통_가상',item:'감별진단에 급성관상동맥증후군 외 대동맥박리 추가 필요',cat:'CLINICAL_CONTENT',cand:'',tent:'missed'},
  {id:'E3',type:'EXPERT',pair:'흉통_가상',item:'활력징후가 상황지침과 신체진찰에 중복 기재됨',cat:'INTERNAL_LOGIC',cand:'활력징후 중복 측정',tent:'caught'},
  {id:'E4',type:'EXPERT',pair:'두통_가상',item:'병력청취에 두통의 발생 양상(돌발 여부) 질문 추가',cat:'CLINICAL_CONTENT',cand:'돌발성 두통 확인 항목 누락',tent:'caught'},
  {id:'E5',type:'EXPERT',pair:'두통_가상',item:'표준화환자 답변이 현병력과 상충(발열 유무 불일치)',cat:'STRUCTURAL',cand:'',tent:'missed'},
  {id:'E6',type:'EXPERT',pair:'두통_가상',item:'채점표 배점 합이 100점이 되도록 조정 필요',cat:'SCORING_VALIDITY',cand:'배점 합 불일치',tent:'caught'},
  {id:'E7',type:'EXPERT',pair:'복통_가상',item:'신체진찰에 반발통/근성방어(복막자극징후) 항목 추가',cat:'CLINICAL_CONTENT',cand:'복막자극징후 항목 누락',tent:'caught'},
  {id:'E8',type:'EXPERT',pair:'복통_가상',item:'환자교육에서 진통제 자가복용 권고는 부적절(과잉)',cat:'SAFETY_OVERCLAIM',cand:'',tent:'missed'},
  {id:'E9',type:'EXPERT',pair:'복통_가상',item:'가임기 여성의 임신 가능성 확인 질문 추가',cat:'CLINICAL_CONTENT',cand:'임신력 확인 누락',tent:'caught'},
];
module.exports = { items, PW: process.env.SURVEY_PW || 'cpx-demo', ADMIN_PW: process.env.ADMIN_PW || process.env.SURVEY_PW || 'cpx-demo', IS_DEMO: !process.env.SURVEY_PW };
