const { cases, PW, IS_DEMO, MODEL } = require('../lib/data');
// 암호 맞으면 사례 전체(전문 포함) 반환. 틀리면 403 → 내용 노출 0.
module.exports = (req, res) => {
  if ((req.query.pw || '') !== PW) return res.status(403).json({ error: '비밀번호가 올바르지 않습니다' });
  res.json({ cases, demo: IS_DEMO, model: MODEL || null });
};
