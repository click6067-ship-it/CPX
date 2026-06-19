const { PW } = require('../lib/data');
let put; try { put = require('@vercel/blob').put; } catch (e) {}
// 판정자 제출 → Vercel Blob에 judge별 1파일(재제출=덮어쓰기). 토큰 없으면 데모(미저장).
module.exports = async (req, res) => {
  if (req.method !== 'POST') return res.status(405).json({ error: 'POST only' });
  let body = req.body;
  if (typeof body === 'string') { try { body = JSON.parse(body || '{}'); } catch (e) { body = {}; } }
  if (!body || body.pw !== PW) return res.status(403).json({ error: '인증 실패' });
  const safe = (body.judge || 'anon').replace(/[^0-9A-Za-z가-힣]/g, '_').slice(0, 40) || 'anon';
  const { pw: _pw, ...rec } = body;   // pw만 제외하고 전부 저장(cases/verdicts 등 스키마 무관)
  try {
    if (put && process.env.BLOB_READ_WRITE_TOKEN) {
      await put(`submissions/${safe}.json`, JSON.stringify(rec), {
        access: 'public', addRandomSuffix: true, contentType: 'application/json' });
      return res.json({ ok: true, stored: 'blob' });
    }
  } catch (e) { return res.status(500).json({ error: '저장 실패: ' + e.message }); }
  return res.json({ ok: true, stored: 'none' });
};
