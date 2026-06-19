const { items, PW, IS_DEMO } = require('../lib/data');
// 암호 맞으면 문항 반환 (게이트). 틀리면 403 → 문항 노출 안 됨.
module.exports = (req, res) => {
  if ((req.query.pw || '') !== PW) return res.status(403).json({ error: '비밀번호가 올바르지 않습니다' });
  res.json({ items, demo: IS_DEMO });
};
