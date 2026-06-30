// 흉통 온톨로지 인터랙티브 HTML 그래프 → PNG 스샷 (미팅/README 임베드용)
// 사용: node scripts/graph_shot.js
const FLOWISE = '/home/click/.nvm/versions/node/v20.20.2/lib/node_modules/flowise/node_modules';
const puppeteer = require(FLOWISE + '/puppeteer');
const path = require('path');

const HTML = 'file://' + path.resolve(__dirname, '../docs/chest_pain-graph.html');
const OUT = path.resolve(__dirname, '../docs/chest_pain-graph.png');
const sleep = ms => new Promise(r => setTimeout(r, ms));

(async () => {
  const b = await puppeteer.launch({
    headless: 'new', executablePath: puppeteer.executablePath(),
    args: ['--no-sandbox', '--disable-dev-shm-usage'],
  });
  const pg = await b.newPage();
  await pg.setViewport({ width: 1600, height: 1000, deviceScaleFactor: 2 });
  await pg.goto(HTML, { waitUntil: 'networkidle2', timeout: 60000 });
  await sleep(6000); // vis-network physics 안정화 대기
  await pg.screenshot({ path: OUT });
  await b.close();
  console.log('wrote', OUT);
})().catch(e => { console.error(e.message); process.exit(1); });
