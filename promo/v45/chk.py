import asyncio, subprocess, sys, time
from playwright.async_api import async_playwright
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8779', '--directory', '/home/claude/wf-promo'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(0.8)
G='/home/claude/game/node_modules'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist'])
        pg = await b.new_page(viewport={'width':1280,'height':720})
        pg.on('pageerror', lambda e: print('ERR', e)); pg.on('console', lambda m: print('C', m.type, m.text[:200]) if m.type in ('error','warning') else None)
        async def route(r):
            u=r.request.url
            if 'three.module.js' in u: return await r.fulfill(path=G+'/three/build/three.module.js', content_type='application/javascript')
            if 'three.core.js' in u: return await r.fulfill(path=G+'/three/build/three.core.js', content_type='application/javascript')
            if 'rapier.mjs' in u: return await r.fulfill(path=G+'/@dimforge/rapier3d-compat/dist/rapier.mjs', content_type='application/javascript')
            if '/examples/jsm/' in u: return await r.fulfill(path=G+'/three/examples/jsm/'+u.split('/examples/jsm/')[1], content_type='application/javascript')
            if u.startswith('http://localhost:8779'): return await r.continue_()
            print('abort', u[:100]); return await r.abort()
        await pg.route('**/*', route)
        await pg.goto('http://localhost:8779/index.html?promo=1'); await pg.wait_for_timeout(20000)
        print('game?', await pg.evaluate("()=>!!window.__game"))
        await b.close()
asyncio.run(main()); srv.terminate()
