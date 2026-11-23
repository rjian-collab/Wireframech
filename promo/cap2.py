import os, sys, json, asyncio, subprocess, time
from playwright.async_api import async_playwright
# usage: cap2.py shots.json OUTDIR W H EVERY [only_shot_names,comma]
PORT = os.environ.get('PORT','8765'); SPEC, OUT, W, H, EVERY = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
ONLY = set(sys.argv[6].split(',')) if len(sys.argv) > 6 and sys.argv[6] else None
srv = subprocess.Popen([sys.executable, '-m', 'http.server', PORT, '--directory', '/home/claude/wireframech'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
G = '/home/claude/game/node_modules'
async def main():
    spec = json.load(open(SPEC))
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist'])
        pg = await b.new_page(viewport={'width': W, 'height': H}, device_scale_factor=1)
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        async def route(r):
            u = r.request.url
            if 'three.module.js' in u: return await r.fulfill(path=G+'/three/build/three.module.js', content_type='application/javascript')
            if 'three.core.js' in u: return await r.fulfill(path=G+'/three/build/three.core.js', content_type='application/javascript')
            if 'rapier.mjs' in u: return await r.fulfill(path=G+'/@dimforge/rapier3d-compat/dist/rapier.mjs', content_type='application/javascript')
            if '/examples/jsm/' in u: return await r.fulfill(path=G+'/three/examples/jsm/'+u.split('/examples/jsm/')[1], content_type='application/javascript')
            if u.startswith('http://localhost:'+PORT+''): return await r.continue_()
            return await r.abort()
        await pg.route('**/*', route)
        await pg.add_init_script("""
          window.__fakeNow = 1000; performance.now = () => window.__fakeNow;
          window.__rafQ = []; window.requestAnimationFrame = cb => { window.__rafQ.push(cb); return 1; };
          window.__step = (ms) => { window.__fakeNow += ms; const q = window.__rafQ; window.__rafQ = []; for (const cb of q) cb(window.__fakeNow); };
          localStorage.setItem('wfm.tutDone','1');
        """)
        await pg.goto('http://localhost:'+PORT+'/index.html?promo=1')
        await pg.wait_for_function("window.__game", timeout=90000)
        await pg.evaluate("()=>{ for(let i=0;i<3;i++) __step(33); }")
        await pg.evaluate("()=>document.getElementById('goAI').click()")
        for i in range(400):
            st = await pg.evaluate("()=>{ for(let k=0;k<2;k++) __step(33); const g=window.__game; return [!!(g.mech&&g.mech.loaded), !!(g.bot&&g.bot.mech&&g.bot.mech.loaded), !!window.__composer]; }")
            if all(st): break
            await pg.wait_for_timeout(300)
        print('loaded', i, st, flush=True)
        await pg.add_style_tag(content="#touch,#topbar,#toast,#tut,#tutHand,#tutRing,#tutAim,#swapHint,.wslot,#result,#fullLink,#rotate,#start{display:none!important}")
        await pg.evaluate("()=>{ document.querySelectorAll('canvas').forEach(c=>{ if(c!==__game.renderer.domElement) c.style.display='none'; }); __game.match.state='idle'; }")
        await pg.evaluate(spec['init'])
        await pg.evaluate("()=>{ for(let i=0;i<30;i++) __step(33.333); }")
        for sc in spec['shots']:
            name = sc['name']
            if ONLY and name not in ONLY: continue
            d = f'{OUT}/{name}'; os.makedirs(d, exist_ok=True)
            await pg.evaluate(f"()=>{{ {sc['setup']} }}")
            pre = sc.get('pre', 0)
            for f in range(-pre, sc['frames']):
                await pg.evaluate(f"()=>{{ const f={f}; H.f=f; {sc['per']} __step(33.333); H.post&&H.post(); }}")
                if f >= 0 and (f % EVERY == 0 or f in sc.get('keys', [])):
                    await pg.screenshot(path=f'{d}/{f:04d}.jpg', type='jpeg', quality=92)
            info = await pg.evaluate("()=>H.log||''")
            print(name, 'done', info, flush=True)
        print('errs', errs[:5]); await b.close()
asyncio.run(main()); srv.terminate()
