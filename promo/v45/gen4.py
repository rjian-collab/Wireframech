import json
exec(open('gen.py').read().split("def S(")[0])   # INIT
def S(name, frames, setup, per, pre=0): return dict(name=name, frames=frames, setup=setup, per=per, pre=pre, keys=[])
LS = {'wfm.device': 'pc', 'wfm.lang': 'en', 'wfm.rec': json.dumps({'ai': {'w': 8, 'l': 5, 'd': 0}, 'net': {'w': 4, 'l': 2, 'd': 0}})}
# PC HUD shot: third-person game camera, real HUD, mouse-mode (no touch buttons)
pc = [S('P1', 70, "H.reset(); H.free(); H.place(L,150,2.2,-46,-Math.PI/2); H.place(B,200,2.2,-46,Math.PI/2); L.hp=6000; B.hp=6000; g.match.timeLeft=166;",
  "g.match.timeLeft=166-f/30; B.hp=Math.max(B.hp,1600); H.bc.moveX=(f%40<20)?1:-1; H.botAimL(); const q=H.q(); H.aim(q.x,q.y+0.4,q.z);"
  " I.stickZ=(f<10)?1:0; const p=H.p(), dx=q.x-p.x, dz=q.z-p.z, dd=Math.hypot(dx,dz), fx=dx/dd, fz=dz/dd; H.cam(p.x-fx*10, p.y+3.6, p.z-fz*10, p.x+fx*25, p.y+1.2, p.z+fz*25, 62); I.stickX=(f>=16&&f<34)?1:(f>=46&&f<62)?-1:0; if(f===28) I.jumpQueued=true; I.fire=(f>=42&&f<44); I.boost=(f>=50&&f<60);", pre=20)]
json.dump(dict(mode='play', hud=True, ls=LS, init=INIT, css="#toast,#tut,#tutHand,#tutRing,#tutAim,#result,#fullLink,#rotate,#start,#lockHint,#swapHint{display:none!important}", shots=pc), open('shots_v4pc.json', 'w'))
# profile card + language flips (menu)
menu = [S('PF', 71, "window.__MENU.rot=0;", "window.__MENU.rot=0.4-f*0.01; if(f===15) document.getElementById('mProfile').click();"),
        S('LG', 57, "document.querySelector('#mModal').classList.remove('on'); setLang('zh-TW'); document.getElementById('mSet').click();",
          "window.__MENU.rot=-0.3+f*0.012; const LS4=['zh-TW','ja','ko','en']; if(f%14===1&&f<56) setLang(LS4[(f-1)/14]);")]
json.dump(dict(mode='menu', ls=LS, init="()=>{ window.H={ f:0, log:'' }; }", css="#touch,#topbar,#toast,#tut,#tutHand,#tutRing,#tutAim,#swapHint,.wslot,#result,#fullLink,#rotate,#lockHint{display:none!important}", shots=menu), open('shots_v4menu.json', 'w'))
print('ok')
