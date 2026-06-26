// 셀프호스트 Langfuse 대시보드(마스킹된 트레이스) 헤드리스 스샷
const FLOWISE = '/home/click/.nvm/versions/node/v20.20.2/lib/node_modules/flowise/node_modules';
const puppeteer = require(FLOWISE + '/puppeteer');

const PORT = process.argv[2] || '3100';
const PID = process.argv[3] || 'cpx-ai';
const TID = process.argv[4];
const EMAIL = process.env.LF_EMAIL || 'admin@cpx.local';
const PW = process.env.LF_PW || '';
const base = `http://localhost:${PORT}`;

const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const b = await puppeteer.launch({ headless: 'new', executablePath: puppeteer.executablePath(),
    args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  const pg = await b.newPage();
  await pg.setViewport({ width: 1500, height: 1000, deviceScaleFactor: 2 });

  // 로그인
  await pg.goto(`${base}/auth/sign-in`, { waitUntil: 'networkidle2', timeout: 60000 });
  await pg.waitForSelector('input', { timeout: 15000 });
  const inputs = await pg.$$('input');
  // email + password 채우기
  for (const el of inputs) {
    const t = await (await el.getProperty('type')).jsonValue();
    if (t === 'email' || t === 'text') await el.type(EMAIL);
    else if (t === 'password') await el.type(PW);
  }
  await Promise.all([
    pg.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 }).catch(() => {}),
    pg.evaluate(() => { const btn = [...document.querySelectorAll('button')].find(x => /sign in|로그인|continue/i.test(x.textContent)); if (btn) btn.click(); }),
  ]);
  await sleep(2000);
  console.log('after login url:', pg.url());

  // 트레이스 목록
  await pg.goto(`${base}/project/${PID}/traces`, { waitUntil: 'networkidle2', timeout: 60000 }).catch(() => {});
  await sleep(3500);
  await pg.screenshot({ path: 'docs/langfuse-traces-list.png', fullPage: false });
  console.log('saved docs/langfuse-traces-list.png');

  // 트레이스 상세 (마스킹된 observation)
  if (TID) {
    await pg.goto(`${base}/project/${PID}/traces/${TID}`, { waitUntil: 'networkidle2', timeout: 60000 }).catch(() => {});
    await sleep(4000);
    await pg.screenshot({ path: 'docs/langfuse-trace-detail.png', fullPage: false });
    console.log('saved docs/langfuse-trace-detail.png');
  }
  await b.close();
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });
