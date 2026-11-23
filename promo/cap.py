import os
import asyncio, subprocess, sys, time
from playwright.async_api import async_playwright
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8765', '--directory', '/home/claude/wireframech'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
        pg=await b.new_page(viewport={'width':1280,'height':720}, device_scale_factor=1)
        logs=[]; pg.on('pageerror', lambda e: logs.append('ERR '+str(e))); pg.on('console', lambda m: logs.append(m.type+' '+m.text) if m.type in ('warning','error') else None)
        G='/home/claude/game/node_modules'
        async def route(r):
            u=r.request.url
            if 'three.module.js' in u: return await r.fulfill(path=G+'/three/build/three.module.js', content_type='application/javascript')
            if 'three.core.js' in u: return await r.fulfill(path=G+'/three/build/three.core.js', content_type='application/javascript')
            if 'rapier.mjs' in u: return await r.fulfill(path=G+'/@dimforge/rapier3d-compat/dist/rapier.mjs', content_type='application/javascript')
            if '/examples/jsm/' in u: return await r.fulfill(path=G+'/three/examples/jsm/'+u.split('/examples/jsm/')[1], content_type='application/javascript')
            if u.startswith('http://localhost:8765'): return await r.continue_()
            return await r.abort()
        await pg.route('**/*', route)
        await pg.add_init_script("""
          window.__fakeNow = 1000; performance.now = () => window.__fakeNow;
          window.__rafQ = []; window.requestAnimationFrame = cb => { window.__rafQ.push(cb); return 1; };
          window.__step = (ms) => { window.__fakeNow += ms; const q = window.__rafQ; window.__rafQ = []; for (const cb of q) cb(window.__fakeNow); };
          localStorage.setItem('wfm.tutDone','1');
        """)
        await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_function("window.__game", timeout=60000)
        await pg.evaluate("()=>{ for(let i=0;i<3;i++) __step(33); }")
        await pg.evaluate("()=>document.getElementById('goAI').click()")
        for i in range(240):
            st = await pg.evaluate("()=>{ for(let k=0;k<3;k++) __step(33); const g=window.__game; return [!!(g.mech&&g.mech.loaded), !!(g.bot&&g.bot.mech&&g.bot.mech.loaded), g.match&&g.match.state]; }")
            if st[0] and st[1]: break
            await pg.wait_for_timeout(500)
        print('load', i, st, flush=True)
        await pg.evaluate("()=>{ for(let i=0;i<40;i++) __step(33); }")   # let pines/shadows load
        await pg.add_style_tag(content="#touch,#topbar,#toast,#tut,#tutHand,#tutRing,#tutAim,#swapHint,.wslot,#result,#fullLink,#rotate{display:none!important}")
        import json
        SC = json.load(open(sys.argv[1]))
        for sc in SC:
            name = sc['name']; os.makedirs(name, exist_ok=True)
            if sc.get('setup'): await pg.evaluate(sc['setup'])
            for f in range(sc['frames']):
                await pg.evaluate(f"()=>{{ const f={f}; {sc.get('per','')} __step(33.333); }}")
                await pg.screenshot(path=f'{name}/{f:04d}.jpg', type='jpeg', quality=92)
            print(name, 'done', flush=True)
        print('\\n'.join(l for l in logs if 'ERR' in l)); await b.close()
import os
asyncio.run(main()); srv.terminate()
