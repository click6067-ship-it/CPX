const { PW } = require('../lib/data');
let list; try { list = require('@vercel/blob').list; } catch (e) {}
// 관리자(같은 암호) → 모든 제출 취합 JSON. 집계 스크립트가 이걸 받아 Fleiss kappa/recall 계산.
module.exports = async (req, res) => {
  if ((req.query.pw || '') !== PW) return res.status(403).json({ error: '인증 실패' });
  if (!list || !process.env.BLOB_READ_WRITE_TOKEN) return res.json({ count: 0, submissions: [], note: 'blob 미설정' });
  try {
    const { blobs } = await list({ prefix: 'submissions/' });
    const out = [];
    for (const b of blobs) { const r = await fetch(b.url); out.push(await r.json()); }
    res.json({ count: out.length, submissions: out });
  } catch (e) { res.status(500).json({ error: e.message }); }
};
