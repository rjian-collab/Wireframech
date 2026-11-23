import json, math
INIT = r"""()=>{ window.H = (()=>{ const g=__game, L=g.local, I=g.input; let B=null;
const H = { g, L, I, f:0, log:'' };
H.bot = (on=true)=>{ if(!B) B=g.ensureBot(); B.active=on; B.body.setEnabled(on); return B; };
H.place=(a,x,y,z,yaw)=>{ a.body.setTranslation({x,y,z},true); a.body.setLinvel({x:0,y:0,z:0},true); a.P.prevPos.set(x,y,z); a.P.currPos.set(x,y,z); a.P.vel.set(0,0,0); if(yaw!=null) a.P.yaw=yaw; a.P.pitch=0; a.P.pinned=null; for(const r of a.ropes){ r.hooked=false; r.wasHeld=false; } if(a.tgt) a.tgt.mesh.position.set(x,y,z); };
H.vel=(a,x,y,z)=>{ a.body.setLinvel({x,y,z},true); a.P.vel.set(x,y,z); };
H.aim=(tx,ty,tz,turn=true)=>{ const p=L.P.currPos, dx=tx-p.x, dy=ty-(p.y+1.4), dz=tz-p.z, y=Math.atan2(-dx,-dz), pt=Math.atan2(dy,Math.hypot(dx,dz)); window.__aimOverride=[y,pt]; if(turn){ L.P.yaw=y; L.P.pitch=Math.max(-0.3,Math.min(0.5,pt)); } };
H.aimBot=()=>{ const q=B.P.currPos; H.aim(q.x,q.y+0.6,q.z); };
H.cam=(x,y,z,lx,ly,lz)=>{ window.__camOverride={x,y,z,lx,ly,lz}; };
H.camRel=(dx,dy,dz,lx=0,ly=0.6,lz=0)=>{ const p=L.P.currPos; H.cam(p.x+dx,p.y+dy,p.z+dz,p.x+lx,p.y+ly,p.z+lz); };
H.orbit=(cx,cy,cz,r,h,a,ly=0.6)=>{ H.cam(cx+Math.cos(a)*r, cy+h, cz+Math.sin(a)*r, cx, cy+ly, cz); };
H.free=()=>{ window.__camOverride=null; };
H.lerp=(a,b,t)=>a+(b-a)*t; H.cl=t=>Math.max(0,Math.min(1,t)); H.eo=t=>1-Math.pow(1-H.cl(t),3); H.eio=t=>{t=H.cl(t); return t*t*(3-2*t);};
H.reset=()=>{ Object.assign(I,{fire:false,hookR:false,hookL:false,hookMain:false,stickX:0,stickZ:0,jumpQueued:false,ropeLatch:false,swapTo:'main'}); window.__aimOverride=null; const w=L.weapon; w.cannon.ammo=6; w.cannon.reloading=0; w.cannon.cool=0; w.ammo=999; w.reloading=0; w.cooldown=0; L.P.fuel=999; };
H.p=()=>L.P.currPos;
H.hook=(x,y,z)=>{ const r=L.ropes[1]; const o=L.P.currPos.clone(); o.y+=1.2; const d=new o.constructor(x,y,z).sub(o).normalize(); const h=g.castRay(o,d,120); r.hooked=true; r.wasHeld=true; r.smart=true; r.bufT=0; if(h) r.anchor.copy(h.point); else r.anchor.set(x,y,z); H.log=(H.log||'')+' hook:'+(h?h.point.toArray().map(v=>v.toFixed(1)).join(','):'none'); r.L=Math.min(60, L.P.currPos.distanceTo(r.anchor)); I.hookR=true; };
H.post=null;
return H; })(); }"""

def S(name, frames, setup, per, pre=0, keys=()):
    return dict(name=name, frames=frames, setup=setup, per=per, pre=pre, keys=list(keys))

BOTLANE = "H.place(H.bot(),186,2.2,-50,Math.PI/2);"
shots = []

# S2 epic drop: crane from high above down to mech on base A; cannon fires at cap 65
shots.append(S('S2', 91,
  "H.reset(); H.bot(); H.place(H.bot(),118,2.2,-24,Math.PI/2); H.place(H.L,8,27.2,4,-Math.PI/2); H.free();",
  "const t=H.eo(f/66); H.cam(H.lerp(40,-1,t),H.lerp(115,30,t),H.lerp(-45,-5,t), H.lerp(150,14,t),H.lerp(0,27.4,t),H.lerp(10,2,t)); H.aim(118,2.8,-24); H.I.fire=(f>=65&&f<67);",
  pre=4, keys=[0,30,60,66,70,90]))

# hook launch: mech at base A edge, jump f4, hook rock (48,42,0) f13, reel from f25
def launch(name, frames, cam, start=0):
    return S(name, frames,
      "H.reset(); H.place(H.bot(),300,2.2,0); H.place(H.L,22,27.2,0,-Math.PI/2); H.free();",
      "const F=f+"+str(start)+"; H.L.P.yaw=-Math.PI/2; if(F<13) H.aim(60,30,0); else H.aim(48,42,0,false); if(F===4) H.I.jumpQueued=true; if(F===13) H.hook(48,42,0); H.I.hookR=(F>=13); H.I.stickZ=(F>=25)?1:0; if(f%10===0) H.log+=' '+F+':'+H.p().toArray().map(v=>v.toFixed(0)).join('/'); " + cam.replace('(f-','(F-'),
      pre=2+start, keys=[0,frames//2,frames-1])
CAM_L1 = "const p=H.p(), t=H.eio((f-25)/15); H.cam(p.x-9,p.y+H.lerp(0.4,4,t),p.z-6, p.x+H.lerp(0,10,t),p.y+H.lerp(0.8,8,t),p.z);"
shots.append(launch('S1A', 77, CAM_L1))
CAM_L2 = "const p=H.p(); H.cam(40,30+f*0.15,-14, p.x,p.y+0.5,p.z);"           # from ahead: mech launches toward camera
shots.append(launch('S1B', 26, CAM_L2.replace('f*0.15','(F+13)*0.15'), start=8))
CAM_L3 = "const p=H.p(); H.cam(p.x+2,p.y-3,p.z+11, p.x+4,p.y+2,p.z);"         # low worm's-eye side
shots.append(launch('S1C', 25, CAM_L3, start=10))

# swing arc: hooked to rock (48,42,0), pushed off the plateau, reel from 39, release at 90
def swing(name, frames, cam, start=0):
    return S(name, frames,
      "H.reset(); H.place(H.bot(),300,2.2,0); H.place(H.L,27,28.5,0,-Math.PI/2); H.free(); H.sw=0;",
      f"const F=f+{start}; H.L.P.yaw=-Math.PI/2; H.aim(48,42,0,false); if(F===-3) H.hook(48,42,0); H.I.hookR=(F>=-3 && F<90); if(F===-2) H.vel(H.L,13,5,0); H.I.stickZ=(F>=39&&F<90)?1:0; if(f%10===0) H.log+=' '+F+':'+H.p().toArray().map(v=>v.toFixed(0)).join('/'); " + cam,
      pre=4 + start, keys=[0, frames//2, frames-1])
CAM_S1 = "const p=H.p(), t=H.eio(F/97); H.cam(p.x+H.lerp(-7,3,t),p.y-2.5,p.z-12.5, p.x+2,p.y+1.2,p.z);"
shots.append(swing('S3A', 97, CAM_S1))
CAM_S2 = "const p=H.p(); H.cam(p.x-3,p.y+7,p.z+9, p.x+3,p.y,p.z);"
shots.append(swing('S3B', 26, CAM_S2, start=78))

# jump-shot over boulder (138,-10): run-up, jump, cannon at apex at bot (185,-10)
def jumpshot(name, frames, cam, jf, ff):
    return S(name, frames,
      "H.reset(); H.place(H.bot(),186,2.2,-10,Math.PI/2); H.place(H.L,127,2.2,-10,-Math.PI/2); H.free();",
      f"H.aimBot(); H.I.stickZ=(f<{jf})?1:0; if(f==={jf}) H.I.jumpQueued=true; H.I.fire=(f>={ff}&&f<{ff+2}); " + cam,
      pre=3, keys=[0,jf,ff,ff+3,frames-1])
CAM_J1 = "const p=H.p(), t=H.eio(f/30); H.cam(H.lerp(129,134,t),H.lerp(2.6,4.2,t),-23, H.lerp(135,p.x+3,t),H.lerp(3,p.y+0.8,t),-10);"
shots.append(jumpshot('S4A', 36, CAM_J1, 6, 20))
CAM_J2 = "const p=H.p(); H.cam(p.x-8,p.y+1.6,p.z+5, p.x+12,p.y+1,p.z-1);"
shots.append(jumpshot('S4B', 25, CAM_J2, 0, 13))

# MG orbit: mech on ground firing MG at bot 45 m away
def mg(name, frames, a0, a1, f0, f1):
    return S(name, frames,
      "H.reset(); H.I.swapTo='mg'; H.place(H.bot(),196,2.2,-46,Math.PI/2); H.place(H.L,150,2.2,-46,-Math.PI/2); H.free();",
      f"H.I.swapTo='mg'; H.aimBot(); H.I.fire=(f>={f0}&&f<{f1}); const p=H.p(), a=({a0})+(({a1})-({a0}))*H.eio(f/{frames}); H.cam(p.x+Math.cos(a)*8,p.y+2.2,p.z+Math.sin(a)*8, p.x+6,p.y+0.6,p.z);",
      pre=14, keys=[0,f0+4,(f0+f1)//2,frames-1])
shots.append(mg('S5A', 52, 2.3, 3.5, 13, 39))
shots.append(mg('S5B', 52, -1.2, 0.4, 0, 39))

# cannon hit snap: low push-in on bot; mech 45 m back fires so shell lands at f13
def snap(name, frames, side):
    return S(name, frames,
      "H.reset(); " + BOTLANE + " H.place(H.L,146,2.2,-50,-Math.PI/2); H.free();",
      f"H.aimBot(); H.I.fire=(f>=12&&f<14); const q=H.B||__game.bot.P.currPos, t=H.eo(f/13); H.cam(H.lerp(158,173,t),H.lerp(1.6,2.6,t),-50+{side}*H.lerp(12,5,t), 186,2.8,-50);",
      pre=3, keys=[0,12,13,14,16,frames-1])
shots.append(snap('S6A', 19, 1))
shots.append(snap('S6B', 20, -1))

# air shots: mech flying over the island after a release, cannon down at bot
def air(name, frames, cam, ff):
    return S(name, frames,
      "H.reset(); " + BOTLANE + " H.place(H.L,122,38,-44,-Math.PI/2); H.vel(H.L,20,12,-1); H.free();",
      f"H.aimBot(); H.I.fire=(f>={ff}&&f<{ff+2}); " + cam,
      pre=0, keys=[0,ff,ff+2,ff+5,frames-1])
CAM_A1 = "const p=H.p(), lx=H.lerp(p.x,186,0.4), ly=H.lerp(p.y,2,0.4), lz=H.lerp(p.z,-50,0.4), a=1.57+H.eio((f-10)/36)*1.35; H.cam(p.x+Math.cos(a)*13,p.y+1.5+H.eio((f-10)/36)*1.5,p.z+Math.sin(a)*13, H.lerp(p.x+2,lx,H.eio((f-10)/36)),H.lerp(p.y,ly,H.eio((f-10)/36)),H.lerp(p.z,lz,H.eio((f-10)/36)));"
shots.append(air('S7A', 51, CAM_A1, 0))
CAM_A2 = "const p=H.p(); H.cam(p.x-11,p.y+2.5,p.z+3, H.lerp(p.x,186,0.3),H.lerp(p.y,2,0.3),H.lerp(p.z,-50,0.3));"
shots.append(air('S7B', 26, CAM_A2, 13))
CAM_A3 = "const p=H.p(); H.cam(p.x+6,p.y-2.5,p.z+12, p.x,p.y+0.5,p.z);"
shots.append(air('S7C', 20, CAM_A3, 0))

# hero beauty: mech on base B plateau edge, slow low orbit, floating rock behind
shots.append(S('S8', 26,
  "H.reset(); H.bot(false); H.place(H.L,374,27.2,6,Math.PI/2); H.free();",
  "H.L.P.yaw=Math.PI/2; H.L.P.pitch=0.05; window.__aimOverride=null; const a=3.3+f/26*0.75; H.cam(374+Math.cos(a)*12.5, 27.0, 6+Math.sin(a)*12.5, 373,27.8,6);",
  pre=30, keys=[0,13,25]))

json.dump(dict(init=INIT, shots=shots), open('/home/claude/promo/shots.json','w'))
print(sum(s['frames'] for s in shots), 'capture frames')
