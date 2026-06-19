const { ADMIN_PW } = require('../lib/data');
let list; try { list = require('@vercel/blob').list; } catch (e) {}
// 관리자 전용(ADMIN_PW, 판정자 암호와 분리) → 모든 제출 취합. 판정자는 남 답 못 봄(독립성).
module.exports = async (req, res) => {
  if ((req.query.pw || '') !== ADMIN_PW) return res.status(403).json({ error: '인증 실패' });
  if (!list || !process.env.BLOB_READ_WRITE_TOKEN) return res.json({ count: 0, submissions: [], note: 'blob 미설정' });
  try {
    const { blobs } = await list({ prefix: 'submissions/' });
    const out = [];
    for (const b of blobs) { const r = await fetch(b.url); out.push(await r.json()); }
    res.json({ count: out.length, submissions: out });
  } catch (e) { res.status(500).json({ error: e.message }); }
};
