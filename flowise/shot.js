// 로그인된 Flowise Agentflow 캔버스를 헤드리스로 스크린샷 (실제 렌더 증명)
const fs = require('fs');
const FLOWISE = '/home/click/.nvm/versions/node/v20.20.2/lib/node_modules/flowise/node_modules';
const puppeteer = require(FLOWISE + '/puppeteer');

const ID = process.argv[2];
const PORT = process.argv[3] || '3100';
const OUT = process.argv[4] || 'flowise/cpx-flowise-canvas.png';

// 쿠키 jar(Netscape) 파싱
const cookies = fs.readFileSync('flowise/.cookies', 'utf8').split('\n')
  .map(l => l.replace('#HttpOnly_', '')).filter(l => l && !l.startsWith('#'))
  .map(l => l.split('\t')).filter(f => f.length >= 7)
  .map(f => ({ name: f[5], value: f[6].trim(), domain: 'localhost', path: '/', httpOnly: true }));

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new', executablePath: puppeteer.executablePath(),
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1680, height: 950, deviceScaleFactor: 2 });
  await page.setCookie(...cookies);
  // 폼 로그인 (쿠키만으론 SPA 통과 안 됨)
  await page.goto(`http://localhost:${PORT}/login`, { waitUntil: 'networkidle2', timeout: 60000 });
  try {
    await page.waitForSelector('input', { timeout: 10000 });
    const inputs = await page.$$('input');
    // 자격증명은 env 로 (소스에 비번 커밋 금지): FLOWISE_EMAIL / FLOWISE_PASSWORD
    await inputs[0].type(process.env.FLOWISE_EMAIL || 'admin@cpx.local');
    await inputs[1].type(process.env.FLOWISE_PASSWORD || '');
    await Promise.all([
      page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 30000 }).catch(() => {}),
      page.evaluate(() => { const b = [...document.querySelectorAll('button')].find(x => /login|sign in/i.test(x.textContent)); if (b) b.click(); }),
    ]);
    console.log('logged in, url now', page.url());
  } catch (err) { console.log('login step:', err.message); }
  const url = `http://localhost:${PORT}/v2/agentcanvas/${ID}`;
  console.log('goto', url);
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 60000 });
  try {
    await page.waitForSelector('.react-flow__node', { timeout: 30000 });
    const n = await page.$$eval('.react-flow__node', els => els.length);
    const e = await page.$$eval('.react-flow__edge', els => els.length);
    console.log('rendered nodes', n, 'edges', e);
    await new Promise(r => setTimeout(r, 2500)); // 레이아웃 안정화
  } catch (err) {
    console.log('node selector not found:', err.message);
  }
  await page.screenshot({ path: OUT });
  console.log('saved', OUT);
  await browser.close();
})().catch(e => { console.error('FAIL', e.message); process.exit(1); });
