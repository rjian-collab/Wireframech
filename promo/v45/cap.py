import os, sys, json, asyncio, subprocess, time
from playwright.async_api import async_playwright
# usage: cap.py spec.json OUTDIR EVERY [only,comma] ; spec: {mode:'play'|'menu', init, shots:[{name,setup,per,frames,pre,keys}]}
PORT = os.environ.get('PORT', '8771'); SPEC, OUT, EVERY = sys.argv[1], sys.argv[2], int(sys.argv[3])
ONLY = set(sys.argv[4].split(',')) if len(sys.argv) > 4 and sys.argv[4] else None
W, H = 1280, 720
srv = subprocess.Popen([sys.executable, '-m', 'http.server', PORT, '--directory', os.environ.get('GAMEDIR', '/home/claude/wf-promo')], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
G = '/home/claude/game/node_modules'
FAKE_TIMERS = """()=>{ const Q = new Map(); let id = 1e6; window.__timerQ = Q;
  window.setTimeout = (fn, ms, ...a) => { const i = ++id; Q.set(i, { fn, at: __fakeNow + (+ms || 0), a }); return i; };
  window.setInterval = (fn, ms, ...a) => { const i = ++id; Q.set(i, { fn, at: __fakeNow + (+ms || 0), iv: Math.max(1, +ms || 1), a }); return i; };
  window.clearTimeout = window.clearInterval = i => { Q.delete(i); };
  const st = window.__step; window.__step = ms => { st(ms); for (const [i, t] of [...Q]) if (t.at <= __fakeNow && Q.has(i)){ if (t.iv) t.at += t.iv; else Q.delete(i); try { typeof t.fn === 'function' ? t.fn(...t.a) : 0; } catch (e) { console.error(e); } } };
}"""
CSS_SYNC = """()=>{ for (const a of document.getAnimations()){ if (a.__t0 == null) a.__t0 = __fakeNow; a.pause(); a.currentTime = Math.max(0, (__fakeNow - a.__t0) * (window.__cssRate || 1)); } }"""
async def main():
    spec = json.load(open(SPEC))
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        pg = await b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=1)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append('console ' + m.text) if m.type == 'error' else None)
        async def route(r):
            u = r.request.url
            if 'three.module.js' in u: return await r.fulfill(path=G+'/three/build/three.module.js', content_type='application/javascript')
            if 'three.core.js' in u: return await r.fulfill(path=G+'/three/build/three.core.js', content_type='application/javascript')
            if 'rapier.mjs' in u: return await r.fulfill(path=G+'/@dimforge/rapier3d-compat/dist/rapier.mjs', content_type='application/javascript')
            if '/examples/jsm/' in u: return await r.fulfill(path=G+'/three/examples/jsm/'+u.split('/examples/jsm/')[1], content_type='application/javascript')
            if u.startswith('http://localhost:'+PORT): return await r.continue_()
            return await r.abort()
        await pg.route('**/*', route)
        await pg.add_init_script(("""
          window.__fakeNow = 1000; performance.now = () => window.__fakeNow;
          window.__rafQ = []; window.requestAnimationFrame = cb => { window.__rafQ.push(cb); return 1; };
          window.__step = (ms) => { window.__fakeNow += ms; const q = window.__rafQ; window.__rafQ = []; for (const cb of q) cb(window.__fakeNow); };
          localStorage.setItem('wfm.tutDone','1'); localStorage.setItem('wfm.name','VOLT'); localStorage.setItem('wfm.s2','blade'); localStorage.setItem('wfm.fcs','1'); if (window.__extraLS === undefined){ const X = %s; for (const k in X) localStorage.setItem(k, X[k]); }
        """).replace("%s", json.dumps(spec.get("ls", {}))))
        await pg.goto('http://localhost:'+PORT+'/index.html?promo=1')
        await pg.wait_for_function("window.__game", timeout=90000)
        await pg.evaluate("()=>{ for(let i=0;i<3;i++) __step(33); }")
        for i in range(400):
            st = await pg.evaluate("()=>{ for(let k=0;k<2;k++) __step(33); const g=window.__game; return [!!(g.mech&&g.mech.loaded), !!window.__composer]; }")
            if all(st): break
            await pg.wait_for_timeout(300)
        if spec['mode'] == 'play':
            await pg.evaluate("()=>{ const b=__game.ensureBot(); }")
            for i in range(400):
                st = await pg.evaluate("()=>{ __step(33); const g=window.__game; return [!!(g.bot&&g.bot.mech&&g.bot.mech.loaded)]; }")
                if all(st): break
                await pg.wait_for_timeout(300)
            await pg.evaluate("()=>document.getElementById('goAI').click()")
            for i in range(60):
                st = await pg.evaluate("()=>{ __step(33); return !!(__game.match && __game.match.state!=='idle'); }")
                if st: break
                await pg.wait_for_timeout(200)
            await pg.evaluate("()=>{ for(let i=0;i<10;i++) __step(33); }")
        print('loaded', i, flush=True)
        await pg.add_style_tag(content=spec.get('css', ''))
        if not spec.get('hud'): await pg.evaluate("()=>{ document.querySelectorAll('canvas').forEach(c=>{ if(c!==__game.renderer.domElement) c.style.display='none'; }); }")
        await pg.evaluate(FAKE_TIMERS)
        await pg.evaluate("()=>{ window.__cssSync = " + CSS_SYNC + "; }")
        await pg.evaluate(spec['init'])
        await pg.evaluate("()=>{ for(let i=0;i<30;i++) __step(33.333); }")
        t0 = time.time()
        for sc in spec['shots']:
            name = sc['name']
            if ONLY and name not in ONLY: continue
            d = f'{OUT}/{name}'; os.makedirs(d, exist_ok=True)
            await pg.evaluate(f"()=>{{ const {{g,L,I,B,M}}=H; H.log=''; H.dt=33.333; {sc['setup']} }}")
            pre = sc.get('pre', 0)
            for f in range(-pre, sc['frames']):
                shoot = f >= 0 and (f % EVERY == 0 or f in sc.get('keys', []))
                await pg.evaluate(f"()=>{{ window.__noRender={'false' if shoot else 'true'}; const {{g,L,I,B,M}}=H; const f={f}; H.f=f; H.dt=33.333; {sc['per']} __step(H.dt); H.post&&H.post(f); __cssSync(); }}")
                if shoot:
                    await pg.screenshot(path=f'{d}/{f:04d}.jpg', type='jpeg', quality=92)
            info = await pg.evaluate("()=>H.log||''")
            print(name, 'done %.0fs' % (time.time() - t0), info[:3000], flush=True)
        print('errs', errs[:8]); await b.close()
asyncio.run(main()); srv.terminate()
