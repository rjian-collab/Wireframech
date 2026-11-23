import json
exec(open('gen.py').read().split("def S(")[0])   # INIT
def S(name, frames, setup, per, pre=0, keys=()): return dict(name=name, frames=frames, setup=setup, per=per, pre=pre, keys=list(keys))
PI2 = 'Math.PI/2'
CSS = json.load(open('shots_play.json'))['css']
shots = []
# ---- B2: blade raise -> swing (slow) -> extreme close-up, red-hot cut line on the hull -> push into the red glow
shots.append(S('B2', 112,
  f"H.reset(); H.place(L,150,2.2,-46,-{PI2}); H.place(B,157.6,2.2,-46,{PI2}); L.weapon.active='mg'; H.cut=null; H.ph=0; window.__promoBoomK=0.04; window.__promoSparkS=0.3; window.__promoCutSparks=0.5;",
  "H.hpKeep(); L.P.yaw=-Math.PI/2; B.P.yaw=Math.PI/2; window.__aimOverride=null; H.bc={}; I.fire=(f>=4&&f<6); const ml=L.weapon.melee; const V3=H.p().constructor;"
  " if(H.ph===0 && ml.ph===1 && ml.t<0.07) { H.ph=1; H.pf=f; H.log+=' B:'+f; }"
  " if(H.cut==null && ml.ph===2){ H.cut=f; const ok=__promoCutLine('bot', new V3(155.0,4.0,-46.6), new V3(156.8,2.5,-46.6), new V3(155.6,3.3,-51.0), 0.1); H.log+=' cut:'+f+(ok?'ok':'FAIL'); }"
  " const c=H.cut==null?-1:f-H.cut; H.dt=33.333*(H.ph===0?0.25:(c<0||c<34)?0.12:0.3);"
  " if(H.ph===0){ const t=H.eio(f/30); H.cam(H.lerp(146.0,147.0,t), H.lerp(5.4,5.0,t), H.lerp(-43.4,-44.0,t), 156.5, 3.0, -46.4, 46); }"
  " else { const e=c<40?0:H.eio((c-40)/30); const cx=H.lerp(154.2,155.5,e), cy=H.lerp(3.0,3.2,e), cz=H.lerp(-50.4,-48.6,e); H.cam(cx,cy,cz, 155.9, 3.2, -46.6, H.lerp(30,14,e)); }",
  pre=20, keys=[]))
# ---- L3: red IR laser crawls over the blue hull and locks on
shots.append(S('L3', 70,
  f"H.reset(); H.place(L,150,2.2,-46,-{PI2}); H.place(B,182,2.2,-46,{PI2}); window.__promoBoomK=0.3; L.weapon.active='mg';",
  "H.hpKeep(); H.aimBot(); const p=H.p(), k=H.eio(f/30); H.botAim(p.x+H.lerp(0.4,1.1,k), p.y+H.lerp(2.3,0.7,k), p.z+H.lerp(-2.6,0,k)+(f>=30?0:0.15*Math.sin(f*0.7)));"
  " const t=H.eio(f/70); H.cam(H.lerp(156.8,156.0,t), H.lerp(4.1,3.8,t), H.lerp(-50.8,-49.8,t), 153.0, 3.0, -46.2, H.lerp(40,32,t));",
  pre=20, keys=[]))
# ---- A4: aim assist vs a target flying across at long range (ghost leads it visibly)
shots.append(S('A4', 98,
  f"H.reset(); H.place(L,150,2.2,-46,-{PI2}); H.place(B,265,36,58,{PI2}); H.ns=0; window.__promoBoomK=0.6;",
  "H.hpKeep(); H.vel(B,0,6-(f+10)*0.12,-36); H.botAimL(); H.aimBot(true); I.fire=(f>=56&&f<58); const p=H.p(), q=H.q();"
  " const tl=Math.hypot(q.x-p.x,q.z-p.z,q.y-p.y)/700, gx=q.x+B.P.vel.x*tl, gy=q.y+B.P.vel.y*tl, gz=q.z+B.P.vel.z*tl, z=H.eio((f-22)/9);"
  " H.cam(144.6, 6.2, -42.4, H.lerp(H.lerp(p.x,q.x,0.45),(gx+q.x)/2,z), H.lerp(p.y+4,(gy+q.y)/2+0.6,z), H.lerp(H.lerp(p.z,q.z,0.45),(gz+q.z)/2,z), H.lerp(42,7.5,z));"
  " const n=L.weapon.shells.length; if(n<H.ns) H.log+=' imp:'+f; H.ns=n; if(f%14===0) H.log+=' '+f+':B'+H.pos(B)+' lead'+(Math.hypot(gx-q.x,gz-q.z)).toFixed(1);",
  pre=10, keys=[]))
json.dump(dict(mode='play', init=INIT, css=CSS, shots=shots), open('shots_v2.json', 'w'))
menu = [S('H9', 85, "window.__composer.passes[1].strength=0.3; document.getElementById('mHangar').click(); window.__MENU.rot=0;",
  "const ch={0:'steel',15:'night',29:'desert',43:'white',57:'gold',64:'crimson',71:'olive'}; window.__MENU.rot=0.5-f*0.05; window.__MENU.rotV=0;"
  " if(ch[f]){ const s=document.getElementById('optPaint'); s.value=ch[f]; s.dispatchEvent(new Event('change')); }")]
m0 = json.load(open('shots_menu.json')); m0['shots'] = menu; json.dump(m0, open('shots_menu2.json', 'w'))
print('ok')
