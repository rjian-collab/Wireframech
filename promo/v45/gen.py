import json
INIT = r"""()=>{ window.H = (()=>{ const g=__game, L=g.local, I=g.input, B=g.ensureBot(), M=g.mech;
const H = { g, L, I, B, M, f:0, log:'', bc:{}, dt:33.333 };
H.place=(a,x,y,z,yaw)=>{ a.body.setTranslation({x,y,z},true); a.body.setLinvel({x:0,y:0,z:0},true); a.P.prevPos.set(x,y,z); a.P.currPos.set(x,y,z); a.P.vel.set(0,0,0); if(yaw!=null) a.P.yaw=yaw; a.P.pitch=0; a.P.pinned=null; for(const r of a.ropes){ r.hooked=false; r.wasHeld=false; } if(a.tgt) a.tgt.mesh.position.set(x,y,z); };
H.vel=(a,x,y,z)=>{ a.body.setLinvel({x,y,z},true); a.P.vel.set(x,y,z); };
H.aim=(tx,ty,tz,turn=true)=>{ const p=L.P.currPos, dx=tx-p.x, dy=ty-(p.y+1.1), dz=tz-p.z, y=Math.atan2(-dx,-dz), pt=Math.atan2(dy,Math.hypot(dx,dz)); window.__aimOverride=[y,pt]; if(turn){ L.P.yaw=y; L.P.pitch=Math.max(-0.3,Math.min(0.5,pt)); } };
H.aimBot=(lead=false)=>{ const q=B.P.currPos; let x=q.x,y=q.y+0.3,z=q.z; if(lead){ const d=Math.hypot(x-L.P.currPos.x,z-L.P.currPos.z), t=d/700; x+=B.P.vel.x*t; z+=B.P.vel.z*t; } H.aim(x,y,z); };
H.botAim=(tx,ty,tz)=>{ const p=B.P.currPos, dx=tx-p.x, dy=ty-(p.y+1.1), dz=tz-p.z, y=Math.atan2(-dx,-dz), pt=Math.atan2(dy,Math.hypot(dx,dz)); Object.assign(H.bc,{yaw:y,pitch:pt,gunYaw:y,gunPitch:pt,aimYaw:y,aimPitch:pt}); };
H.botAimL=(ox=0,oz=0)=>{ const p=L.P.currPos; H.botAim(p.x+ox,p.y+0.3,p.z+oz); };
window.__botCmd=(dt,b)=>{ const c={ seq:0, tick:0, moveX:0, moveZ:0, yaw:b.P.yaw, pitch:b.P.pitch, fire:false, hookL:false, hookR:false, hookMain:false, smart:false, autoFire:false, swap:false, swapTo:null, gunYaw:null, gunPitch:null, jump:false, jumpPow:1, jumpX:0, jumpZ:0, boost:false, thrust:false, reload:false };
  Object.assign(c,H.bc); H.bc.jump=false; H.bc.swapTo=null; return c; };
H.cam=(x,y,z,lx,ly,lz,fov)=>{ window.__camOverride={x,y,z,lx,ly,lz,fov}; };
H.free=()=>{ window.__camOverride=null; };
H.lerp=(a,b,t)=>a+(b-a)*t; H.cl=t=>Math.max(0,Math.min(1,t)); H.eo=t=>1-Math.pow(1-H.cl(t),3); H.eio=t=>{t=H.cl(t); return t*t*(3-2*t);};
H.p=()=>L.P.currPos; H.q=()=>B.P.currPos;
H.edge=k=>{ const e=M.paintMats&&M.paintMats.edge&&M.paintMats.edge[0]; if(!e) return; if(!H.e0) H.e0=e.color.clone(); e.color.copy(H.e0).multiplyScalar(k); };
H.wreset=a=>{ const w=a.weapon; w.active='main'; w.s2='blade'; w.cannon.ammo=6; w.cannon.reserve=99; w.cannon.reloading=0; w.cannon.cool=0; w.shells.length=0; w.melee={cd:0,t:0,ph:0,prev:false,vis:null}; w.prevFire=false; w.ammo=999; w.reloading=0; w.cooldown=0; a.hp=1e9; a.P.fuel=999; };
H.reset=()=>{ Object.assign(I,{fire:false,hookR:false,hookL:false,hookMain:false,stickX:0,stickZ:0,jumpQueued:false,jumpX:0,jumpZ:0,ropeLatch:false,swapTo:null}); window.__aimOverride=null; H.wreset(L); H.wreset(B); H.bc={}; g.match.state='live'; g.match.timeLeft=999; B.active=true; B.body.setEnabled(true); B.kind='bot'; B.name='Kestrel_09'; if(window.__promoSeverReset) __promoSeverReset(); H.edge(1); H.cut=null; H.post=null; window.__promoBoomK=0.35; window.__promoSparkS=1; window.__promoCutSparks=1; };
H.melee=a=>{ const ml=a.weapon.melee; ml.ph=0; ml.cd=0; ml.prev=false; };
H.hook=(x,y,z)=>{ const r=L.ropes[1]; const o=L.P.currPos.clone(); o.y+=1.2; const d=new o.constructor(x,y,z).sub(o).normalize(); const h=g.castRay(o,d,120); r.hooked=true; r.wasHeld=true; r.smart=true; r.bufT=0; if(h) r.anchor.copy(h.point); else r.anchor.set(x,y,z); r.L=Math.min(60, L.P.currPos.distanceTo(r.anchor)); I.hookR=true; };
H.pos=a=>a.P.currPos.toArray().map(v=>v.toFixed(1)).join('/');
H.hpKeep=()=>{ L.hp=1e9; B.hp=1e9; g.match.timeLeft=999; };
return H; })(); }"""

def S(name, frames, setup, per, pre=0, keys=()):
    return dict(name=name, frames=frames, setup=setup, per=per, pre=pre, keys=list(keys))
PI2 = 'Math.PI/2'
shots = []

# ---- S1 versus intro: vs opens at f12; orbit like the game's intro + push-in near the end
shots.append(S('S1', 90,
  f"H.reset(); g.match.state='idle'; H.place(L,6,27.2,0,-{PI2}); H.place(B,394,27.2,0,{PI2});",
  "H.hpKeep(); if(f===12){ g.match.start('ai'); B.weapon.s2='blade'; B.name='Kestrel_09'; H.bc={}; document.getElementById('vsMode').textContent='ONLINE 1v1'; document.getElementById('vsOpName').textContent='Kestrel_09'; }"
  " const t=(f+40)/30, a=0.6+t*0.22, k=1-0.16*H.eio((f-55)/35); H.cam(200+Math.cos(a)*230*k, 95-t*6-(1-k)*40, Math.sin(a)*170*k, 200,4+(1-k)*8,0, 70);",
  pre=4, keys=[0, 12, 20, 30, 45, 60, 75, 89]))

# ---- S2 X slash close-up (swing in the air)
shots.append(S('S2', 30,
  f"H.reset(); H.place(L,150,2.2,-46,-{PI2}); H.place(B,230,2.2,-60,{PI2}); L.weapon.active='mg';",
  "H.hpKeep(); L.P.yaw=-Math.PI/2; if(f===2) H.melee(L); I.fire=(f>=-8&&f<-6)||(f>=2&&f<4); const p=H.p(), t=H.eo((f+8)/38);"
  " H.cam(p.x+H.lerp(9.5,7.5,t), p.y+1.0, p.z+H.lerp(5.5,4.2,t), p.x+3.2, p.y+1.3, p.z, 52);",
  pre=24, keys=[0, 4, 8, 10, 12, 14, 16, 20, 29]))


# ---- S2 fix: frontal 3/4 so the X reads
shots[-1] = S('S2', 30,
  f"H.reset(); H.place(L,150,2.2,-46,-{PI2}); H.place(B,230,2.2,-60,{PI2}); L.weapon.active='mg';",
  "H.hpKeep(); L.P.yaw=-Math.PI/2; if(f===2) H.melee(L); I.fire=(f>=-8&&f<-6)||(f>=2&&f<4); const p=H.p(), t=H.eo((f+8)/38);"
  " H.cam(p.x+H.lerp(15,12.5,t), p.y+H.lerp(3.4,2.8,t), p.z+H.lerp(6.5,5.2,t), p.x+2.4, p.y+1.3, p.z, 44);",
  pre=24, keys=[0, 4, 8, 10, 12, 14, 16, 20, 29])

# ---- S3 swing: hatch close-up -> hop + push off the edge -> hook rock underside -> reel -> pendulum; 0.3x at the top of the arc, release
shots.append(S('S3', 105,
  f"H.reset(); H.place(B,300,2.2,0); H.place(L,20,27.2,0,-{PI2});",
  "H.hpKeep(); L.P.yaw=-Math.PI/2; H.aim(46,38,0,false); if(f===2) I.jumpQueued=true; if(f===4) H.vel(L,10,6,0); if(f===6) H.hook(46,38,0);"
  " I.hookR=(f>=6&&f<84); I.stickZ=(f>=12&&f<30)?1:0; const s=f-64;"
  " if(s>=0&&s<33) H.dt=33.333*0.3; else if(s>=33) H.dt=33.333*H.lerp(0.3,1,(s-33)/7);"
  " const p=H.p(), a=H.eio((f-5)/14), b=H.eio(s/24);"
  " H.cam(p.x+H.lerp(-4.5,-9,a)+H.lerp(0,-5,b), p.y+H.lerp(3.4,-0.5,a)+H.lerp(0,1.5,b), p.z+H.lerp(-2.4,-11,a)+H.lerp(0,-12,b), p.x+H.lerp(0.5,5,a)+H.lerp(0,-4,b), p.y+H.lerp(1.5,2.5,a), p.z, H.lerp(50,62,a));"
  " if(f%6===0) H.log+=' '+f+':'+H.pos(L)+(L.ropes[1].hooked?'H':'-');",
  pre=2, keys=[]))

# ---- S4 over-shoulder FCS lead shot; impact logged for the freeze
shots.append(S('S4', 66,
  f"H.reset(); H.place(L,150,2.2,-46,-{PI2}); H.place(B,195,2.2,-8,{PI2}); H.ns=0; window.__promoBoomK=0.5;",
  "H.hpKeep(); H.bc.moveX=1; H.botAimL(); H.aimBot(true); I.fire=(f>=45&&f<47); const p=H.p(), q=H.q();"
  " const tl=Math.hypot(q.x-p.x,q.z-p.z)/700, gx=q.x+B.P.vel.x*tl, gz=q.z+B.P.vel.z*tl, z=H.eio((f-20)/8); H.cam(p.x-5.5, p.y+4.4, p.z+4.0, H.lerp(H.lerp(p.x,q.x,0.5),(gx+q.x)/2,z), H.lerp(p.y+1.0,q.y+1.2,z), H.lerp(H.lerp(p.z,q.z,0.5),(gz+q.z)/2,z), H.lerp(40,11,z));"
  " const n=L.weapon.shells.length; if(n<H.ns) H.log+=' imp:'+f; H.ns=n; if(f%10===0) H.log+=' '+f+':B'+H.pos(B);",
  pre=25, keys=[]))

# ---- S5 blade snap close-up (slow-mo, edge lights up)
shots.append(S('S5', 75,
  f"H.reset(); H.place(B,230,2.2,-60,{PI2}); H.place(L,150,2.2,-46,-{PI2});",
  "H.hpKeep(); L.P.yaw=-Math.PI/2; L.P.pitch=0.05; window.__aimOverride=null; if(f===10) I.swapTo='mg'; H.dt=33.333*(f<10?0.5:f<14?1:0.35);"
  " H.edge(f<28?0.35:H.lerp(0.35,3.2,H.eo((f-28)/12))); const p=H.p(), t=H.eio(f/75);"
  " H.cam(p.x+H.lerp(12,10.5,t), p.y+H.lerp(1.8,1.5,t), p.z+H.lerp(7.5,6.5,t), p.x+4.2, p.y+0.5, p.z, 36);",
  pre=20, keys=[]))

# ---- S6 sever: swing hits the side-on opponent, cut leg flies; 2nd swing for the X
shots.append(S('S6', 66,
  f"H.reset(); H.place(L,150,2.2,-46,-{PI2}); H.place(B,156.6,2.2,-46,Math.PI); L.weapon.active='mg'; H.cut=null; window.__promoBoomK=0.12;",
  "H.hpKeep(); L.P.yaw=-Math.PI/2; B.P.yaw=Math.PI; I.fire=(f>=0&&f<2); const ml=L.weapon.melee;"
  " if(H.cut==null && ml.hit){ const kp=H.p().clone(), lp=H.p(); let bi=0,bd=1e9; B.mech.legs.forEach((lg,i)=>{ lg.kneeG.getWorldPosition(kp); const d=kp.distanceTo(lp); if(d<bd){bd=d;bi=i;} }); __promoSever('bot',bi,1,0.5); H.cut=f; H.log+=' cut:'+f+' leg'+bi; }"
  " const c=H.cut==null?-99:f-H.cut; if(c>=0&&c<20) H.dt=33.333*0.5; if(c===16) H.melee(L); I.fire=I.fire||(c>=16&&c<18);"
  " const m={x:153.3,y:2.2,z:-46}, t=H.eio(f/66); H.cam(m.x+H.lerp(2.6,3.0,t), m.y+H.lerp(1.9,2.3,t), m.z+H.lerp(11.5,12.8,t), m.x+2.4, m.y+1.0, m.z, 40);",
  pre=20, keys=[]))

# ---- S7 online duel: red laser locks on, side hop (0.6x), fire back
shots.append(S('S7', 120,
  f"H.reset(); H.place(L,150,2.2,-46,-{PI2}); H.place(B,172,2.2,-42,{PI2}); H.p0=H.p().clone();",
  "H.hpKeep(); const k=H.eo(f/24); if(f<44) H.botAim(H.p0.x, H.p0.y+0.3, H.p0.z+H.lerp(11,0,k)); else H.botAimL(0,H.lerp(-4,0,H.eio((f-44)/30)));"
  " H.bc.fire=(f>=40&&f<42); if(f<60) H.aim(H.q().x,H.q().y+0.3,H.q().z,false); else H.aimBot(); if(f===36){ I.jumpQueued=true; I.jumpX=1; I.jumpZ=0; }"
  " if(f>=36&&f<60) H.dt=33.333*0.6; I.fire=(f>=90&&f<92); const p=H.p(), q=H.q();"
  " const t=H.eio(f/120); H.cam(161+H.lerp(-1,1,t), 5.2, -46-H.lerp(18,15,t), 161, 2.6, -43, 50);"
  " if(f%6===0) H.log+=' '+f+':'+H.pos(L);",
  pre=20, keys=[]))

# ---- S8 guard blocks shell; teleport; opponent's blade parried -> both knocked apart (0.5x) -> counter
shots.append(S('S8', 88,
  f"H.reset(); H.place(L,150,2.2,-46,-{PI2}); H.place(B,176,2.2,-46,{PI2}); L.weapon.active='mg'; H.parry=null; H.bph=0; window.__promoBoomK=0.12;",
  "H.hpKeep(); L.P.yaw=-Math.PI/2; window.__aimOverride=null; if(f<35){ H.botAimL(); H.bc.fire=(f>=10&&f<12); }"
  " if(f===35){ H.place(B,157,2.2,-46,Math.PI/2); B.weapon.active='mg'; H.bc={}; } if(f<35&&L.weapon.shells) 0; if(f===12) H.log+=' blk?';"
  " if(f>=35){ H.botAimL(); H.bc.fire=(f>=40&&f<42); const ph=B.weapon.melee.ph; if(H.bph===1&&ph===2&&H.parry==null){ H.vel(L,-9,5,0); H.vel(B,14,6,0); H.parry=f; H.log+=' parry:'+f; } H.bph=ph; } if(f>=46&&f<88) H.dt=33.333*0.5; if(f===64) H.melee(L); I.fire=(f>=64&&f<66);"
  " const p=H.p(), q=H.q();"
  " if(f<35) H.cam(p.x+6.8, p.y+1.6, p.z+5.2, p.x+2.6, p.y+1.1, p.z, 45); else { const t=H.eio((f-44)/40), mx=(p.x+q.x)/2; H.cam(mx+H.lerp(0,0.5,t), p.y+H.lerp(1.4,2.2,t), -46+H.lerp(10,14,t), mx, p.y+0.9, -46, 50); }"
  " if(f%4===0) H.log+=' '+f+':'+H.pos(L)+'~'+H.pos(B);",
  pre=20, keys=[]))

# ---- S10 skin stills (identical pose, dt=0 between paints)
shots.append(S('S10', 4,
  f"H.reset(); H.place(B,230,2.2,-60,{PI2}); H.place(L,150,2.2,-46,-{PI2}); L.weapon.active='mg';",
  "H.hpKeep(); L.P.yaw=-Math.PI/2+0.3; L.P.pitch=0.12; window.__aimOverride=null; if(f>=0){ H.dt=0; M.applyPaint(['steel','gold','crimson','olive'][f]); } const p=H.p(); H.cam(p.x+36, p.y+4.6, p.z+6.0, p.x, p.y+0.6, p.z, 17);",
  pre=24, keys=[]))

json.dump(dict(mode='play', init=INIT, css="#touch,#topbar,#toast,#tut,#tutHand,#tutRing,#tutAim,#swapHint,.wslot,#result,#fullLink,#rotate,#start,#lockHint{display:none!important} .vs-card::before{content:'YOU'!important} .vs-card.op::before{content:'OPPONENT'!important} .vs-count span{font-size:0!important} .vs-count span::after{content:'STARTS IN';font-size:clamp(12px,3vmin,16px)}",
               shots=shots), open('/home/claude/promo/v45/shots_play.json', 'w'))

MENU_INIT = r"""()=>{ window.H={ f:0, log:'' }; }"""
menu = [S('S9', 91, "document.getElementById('mHangar').click(); window.__MENU.rot=0;",
  "const ch={0:'steel',16:'night',31:'desert',46:'white',61:'gold',69:'crimson',76:'olive'}; window.__MENU.rot=0.5-f*0.045; window.__MENU.rotV=0;"
  " if(ch[f]){ const s=document.getElementById('optPaint'); s.value=ch[f]; s.dispatchEvent(new Event('change')); }", pre=0, keys=[])]
json.dump(dict(mode='menu', init=MENU_INIT, css="#touch,#topbar,#toast,#tut,#tutHand,#tutRing,#tutAim,#swapHint,.wslot,#result,#fullLink,#rotate,#lockHint{display:none!important}", shots=menu), open('/home/claude/promo/v45/shots_menu.json','w'))
print(sum(s['frames'] + s['pre'] for s in shots), 'sim frames')
