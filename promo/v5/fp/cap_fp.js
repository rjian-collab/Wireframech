// WIREFRAMECH promo v5 — first-person (real player view) capture harness.
// Usage: node cap_fp.js <choreo.js> <outDir> [every=1] [width=1920] [height=1080] [maxFrames]
// Game files are served by request interception (no local server). CDN modules are cached to CDN_CACHE via curl.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const GAME = process.env.GAMEDIR || '/tmp/claude-0/-home-user/13092d8d-a146-5b13-b847-caff4ba5d91c/scratchpad/fp/game';
const CDN = process.env.CDN_CACHE || '/tmp/claude-0/-home-user/13092d8d-a146-5b13-b847-caff4ba5d91c/scratchpad/fp/cdn';
const [CHO, OUT, EVERY = '1', W = '1920', HH = '1080', MAXF] = process.argv.slice(2);
const MT = f => ({ html: 'text/html', js: 'text/javascript', mjs: 'text/javascript', json: 'application/json', png: 'image/png', jpg: 'image/jpeg', glb: 'model/gltf-binary', css: 'text/css', wasm: 'application/wasm' })[f.split('.').pop()] || 'application/octet-stream';
const cho = require(path.resolve(CHO));
const FPS = cho.fps || 60, STEP = 1000 / FPS;
function cdnFile(u){ const f = path.join(CDN, u.replace(/^https?:\/\//, '').replace(/[?#].*$/, '')); if (!fs.existsSync(f)){ fs.mkdirSync(path.dirname(f), { recursive: true }); execFileSync('curl', ['-sSfL', '-o', f, u]); } return f; }
(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--autoplay-policy=no-user-gesture-required'] });
  const ctx = await browser.newContext({ viewport: { width: +W, height: +HH }, deviceScaleFactor: 1 });
  await ctx.route('**/*', async r => { const u = r.request().url();
    try {
      if (u.startsWith('http://wf.local/')){ const f = path.join(GAME, decodeURIComponent(new URL(u).pathname)); return await r.fulfill({ body: fs.readFileSync(f), contentType: MT(f) }); }
      if (u.includes('cdn.jsdelivr.net')){ const f = cdnFile(u); return await r.fulfill({ body: fs.readFileSync(f), contentType: MT(f) }); }
      if (u.startsWith('data:') || u.startsWith('blob:')) return await r.continue();
      if (u.includes('fonts.g')) return await r.abort();
      return await r.abort();
    } catch (e) { console.error('route fail', u, e.message); return await r.fulfill({ status: 404, body: '' }); } });
  const page = await ctx.newPage();
  const errs = []; page.on('pageerror', e => errs.push('pageerror ' + e.message)); page.on('console', m => { if (m.type() === 'error') errs.push('console ' + m.text()); if (m.text().startsWith('[cho]')) console.log(m.text()); });
  await page.addInitScript(ls => {
    { let a = 12345; Math.random = () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
    window.__fakeNow = 1000; performance.now = () => window.__fakeNow; Date.now = (d => () => d + window.__fakeNow)(Date.now());
    window.__rafQ = []; window.requestAnimationFrame = cb => { window.__rafQ.push(cb); return 1; };
    window.__step = ms => { window.__fakeNow += ms; const q = window.__rafQ; window.__rafQ = []; for (const cb of q) cb(window.__fakeNow); };
    try { localStorage.setItem('wfm.tutDone', '1'); for (const k in ls) localStorage.setItem(k, ls[k]); } catch (_) {}
  }, cho.ls || {});
  await page.goto('http://wf.local/index.html?promo=1', { waitUntil: 'load' });
  await page.waitForFunction(() => window.__game, null, { timeout: 400000 });
  for (let i = 0; i < 600; i++){ const ok = await page.evaluate(() => { for (let k = 0; k < 2; k++) __step(33); const g = __game; return !!(g.mech && g.mech.loaded); }); if (ok) break; await page.waitForTimeout(200); }
  await page.evaluate(() => __game.ensureBot());
  for (let i = 0; i < 600; i++){ const ok = await page.evaluate(() => { __step(33); const g = __game; return !!(g.bot && g.bot.mech && g.bot.mech.loaded); }); if (ok) break; await page.waitForTimeout(200); }
  await page.evaluate(() => document.getElementById('goAI').click());
  for (let i = 0; i < 100; i++){ const ok = await page.evaluate(() => { __step(33); return !!(__game.match && __game.match.state !== 'idle'); }); if (ok) break; await page.waitForTimeout(100); }
  await page.evaluate(() => { for (let i = 0; i < 20; i++) __step(33); });
  // fake timers (toasts, CSS) so DOM HUD timing follows the fixed clock
  await page.evaluate(() => { const Q = new Map(); let id = 1e6;
    window.setTimeout = (fn, ms, ...a) => { const i = ++id; Q.set(i, { fn, at: __fakeNow + (+ms || 0), a }); return i; };
    window.setInterval = (fn, ms, ...a) => { const i = ++id; Q.set(i, { fn, at: __fakeNow + (+ms || 0), iv: Math.max(1, +ms || 1), a }); return i; };
    window.clearTimeout = window.clearInterval = i => { Q.delete(i); };
    const st = window.__step; window.__step = ms => { st(ms); for (const [i, t] of [...Q]) if (t.at <= __fakeNow && Q.has(i)){ if (t.iv) t.at += t.iv; else Q.delete(i); try { typeof t.fn === 'function' ? t.fn(...t.a) : 0; } catch (e) { console.error(e); } } };
    window.__cssSync = () => { for (const a of document.getAnimations()){ if (a.__t0 == null) a.__t0 = __fakeNow; a.pause(); a.currentTime = Math.max(0, (__fakeNow - a.__t0)); } }; });
  if (cho.css) await page.addStyleTag({ content: cho.css });
  await page.evaluate(`(${cho.init})()`);
  if (process.env.LAB){ const lab = require(path.resolve(process.env.LAB));
    for (const v of lab.variants){ await page.evaluate(`(()=>{ const {g,L,I,B,M}=H; ${v.setup} })()`); const rows = [];
      for (let f = 0; f < v.frames; f++){ const r = await page.evaluate(`(()=>{ window.__noRender=true; const {g,L,I,B,M}=H; const f=${f}; H.f=f; ${v.per} __step(${1000/(lab.fps||60)}*(H.ts??1)); return (f % ${lab.every||10} === 0 || H.mark) ? (H.probe? H.probe(f) : null) : null; })()`); if (r) rows.push(r); }
      console.log('VARIANT', v.name); for (const r of rows) console.log(JSON.stringify(r)); }
    console.log('errs', errs.slice(0, 10).join('\n')); await browser.close(); return; }
  await page.evaluate(`(()=>{ const {g,L,I,B,M}=H; ${cho.setup} })()`);
  const pre = cho.pre || 0, N = Math.min(cho.frames, MAXF ? +MAXF : 1e9), ev = +EVERY, keys = new Set(cho.keys || []);
  const log = [];
  const t0 = Date.now();
  for (let f = -pre; f < N; f++){
    const shoot = f >= 0 && (f % ev === 0 || keys.has(f));
    const info = await page.evaluate(`(()=>{ window.__noRender=${!shoot}; const {g,L,I,B,M}=H; const f=${f}; H.f=f; ${cho.per} __step(${STEP}*(H.ts??1)); H.post&&H.post(f); __cssSync(); return H.probe? H.probe(f):null; })()`);
    if (info) log.push(info);
    if (shoot) await page.screenshot({ path: `${OUT}/${String(f).padStart(4, '0')}.png` });
    if (f % 30 === 0 || (info && info.log && false)) console.log('frame', f, ((Date.now() - t0) / 1000).toFixed(0) + 's', info ? JSON.stringify(info) : '');
  }
  fs.writeFileSync(`${OUT}/probe.json`, JSON.stringify(log));
  console.log('errs', errs.slice(0, 10).join('\n'));
  await browser.close();
})();
