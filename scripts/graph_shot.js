// 주증상 온톨로지 인터랙티브 HTML 그래프 → PNG 스샷 (미팅/README 임베드용)
// 사용: node scripts/graph_shot.js [주증상]   # 기본 chest_pain, 예: node scripts/graph_shot.js diarrhea
//
// 2026-08-11: 브라우저 백엔드 교체 — 기존의 flowise 번들 puppeteer 경로가 사라져(MODULE_NOT_FOUND)
// 렌더가 깨져 있었다. 전역 headless 번들(~/.claude/tools/headless)의 playwright로 전환.
const os = require('os');
const path = require('path');

const HEADLESS = process.env.HEADLESS_BUNDLE
  || path.join(os.homedir(), '.claude', 'tools', 'headless', 'node_modules');

let chromium;
try {
  ({ chromium } = require(path.join(HEADLESS, 'playwright')));
} catch (e) {
  console.error(
    `playwright를 찾을 수 없습니다: ${HEADLESS}\n` +
    `HEADLESS_BUNDLE 환경변수로 node_modules 경로를 지정하거나 해당 번들을 설치하세요.`
  );
  process.exit(1);
}

const SYMPTOM = process.argv[2] || 'chest_pain';
const HTML = 'file://' + path.resolve(__dirname, `../docs/${SYMPTOM}-graph.html`);
const OUT = path.resolve(__dirname, `../docs/${SYMPTOM}-graph.png`);

(async () => {
  const b = await chromium.launch({ args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  try {
    const pg = await b.newPage({ viewport: { width: 1600, height: 1000 }, deviceScaleFactor: 2 });
    await pg.goto(HTML, { waitUntil: 'networkidle', timeout: 60000 });
    // vis-network physics 안정화 — 고정 대기 대신 stabilized 이벤트를 기다리고, 못 받으면 타임아웃 폴백.
    await pg.evaluate(() => new Promise(res => {
      const done = () => res();
      if (window.__netStabilized) return done();
      const t = setTimeout(done, 8000);
      document.addEventListener('vis-stabilized', () => { clearTimeout(t); done(); }, { once: true });
    })).catch(() => {});
    await pg.waitForTimeout(1500);
    await pg.screenshot({ path: OUT });
    console.log('wrote', OUT);
  } finally {
    await b.close();   // 실패해도 브라우저를 남기지 않는다
  }
})().catch(e => { console.error(e.message); process.exit(1); });
