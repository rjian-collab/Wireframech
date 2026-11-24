// (copied from promo_v5_tp/tp_helpers.js; probe also logs the enemy's cables) Third-person (and first-person) helpers added on top of H (promo helper). All of these only set the same inputs a player would
// (look yaw/pitch, WASD stick, Shift boost, Space jump, Q/E cable, mouse fire). Posing helpers are marked POSE.
module.exports = String.raw`()=>{ const H=window.H, g=H.g, L=H.L, I=H.I, B=H.B; const DEG=Math.PI/180;
H.yp=(x,y,z,off=0)=>{ const p=L.P.currPos, ex=p.x, ey=p.y+1.1, ez=p.z, dx=x-ex, dy=y-ey, dz=z-ez; return [Math.atan2(-dx,-dz)-off, Math.atan2(dy,Math.hypot(dx,dz))]; };
H.wrap=a=>Math.atan2(Math.sin(a),Math.cos(a));
// mouse look: move view toward (yaw,pitch) with exponential smoothing k (0..1 per frame) — like a player flicking the mouse
H.look=(yaw,pitch,k=1)=>{ const P=L.P; P.yaw+=H.wrap(yaw-P.yaw)*k; P.pitch+=(pitch-P.pitch)*k; P.pitch=Math.max(-85*DEG,Math.min(85*DEG,P.pitch)); };
H.lookAt=(x,y,z,k=1,off=0)=>{ const [a,b]=H.yp(x,y,z,off); H.look(a,b,k); };
H.keys=(o)=>{ Object.assign(I,{stickX:0,stickZ:0,boost:false,fire:false,hookL:false,hookR:false},o||{}); };
H.botQ=[]; // bot aims at where the player WAS (lag) — same idea as the game AI (aims at your position ~1 s ago)
H.botFireAt=(lagF,trail=2.5,oy=0.3)=>{ const p=L.P.currPos, v=L.P.vel; H.botQ.push([p.x,p.y,p.z]); while(H.botQ.length>120) H.botQ.shift(); const q=H.botQ[Math.max(0,H.botQ.length-1-lagF)];
  // aim where the player WAS, plus a little more behind the player's motion (the stream trails the dodge and misses)
  const hv=Math.hypot(v.x,v.z); let tx=0,tz=0; if(hv>1){ tx=-v.x/hv*trail; tz=-v.z/hv*trail; } else { const b=B.P.currPos, dx=p.x-b.x, dz=p.z-b.z, d=Math.hypot(dx,dz)||1; tx=-dz/d*trail; tz=dx/d*trail; }
  H.botAim(q[0]+tx,q[1]+oy,q[2]+tz); };
H.los=()=>{ const p=L.P.currPos, q=B.P.currPos; const o={x:p.x,y:p.y+1.1,z:p.z}, d={x:q.x-o.x,y:q.y+0.8-o.y,z:q.z-o.z}, n=Math.hypot(d.x,d.y,d.z); const h=g.castRay(o,{x:d.x/n,y:d.y/n,z:d.z/n},n); return !h || h.toi>n-2.5 ? 1 : 0; };
H.probe=f=>({ f, los:H.los(), p:H.pos(L), v:+L.P.vel.length().toFixed(1), vy:+L.P.vel.y.toFixed(1), g:L.P.grounded?1:0, yaw:+(L.P.yaw/DEG).toFixed(0), pit:+(L.P.pitch/DEG).toFixed(0), rL:L.ropes[0].hooked?L.ropes[0].anchor.toArray().map(v=>+v.toFixed(1)):0, rR:L.ropes[1].hooked?L.ropes[1].anchor.toArray().map(v=>+v.toFixed(1)):0, fuel:+L.P.fuel.toFixed(2), bhp:Math.round(B.hp), lhp:Math.round(L.hp), b:H.pos(B), bv:+B.P.vel.length().toFixed(1), bR:B.ropes.map(r=>r.hooked?r.anchor.toArray().map(v=>+v.toFixed(1)):0), wa:L.weapon.active, mgf:L.weapon.fired, trc:H.trcCollect(), log:H.log });
// ---- third-person: the game's chase camera sits T.dist behind a pivot T.height above the feet, looking along (yaw,pitch);
// the crosshair is the screen centre, i.e. the ray from that camera. These helpers mirror the game's own camera math
// (index.html "v2.1 第三人稱鏡頭" + aim3P) so the script can move the MOUSE until the CROSSHAIR is on a point — exactly what a 3P player does.
H.V=(x,y,z)=>new L.P.currPos.constructor(x,y,z);
H.fwd=(yaw,pit)=>H.V(-Math.sin(yaw)*Math.cos(pit),Math.sin(pit),-Math.cos(yaw)*Math.cos(pit));
H.tpCamAt=(yaw,pit)=>{ const T=g.CONFIG.tp, p=L.P.currPos, piv=H.V(p.x,p.y+T.height,p.z), f=H.fwd(yaw,pit), back=f.clone().negate(); const hb=g.castRay(piv,back,T.dist+0.5); const d=hb?Math.max(T.minDist,hb.toi-0.5):T.dist; return { cam: piv.clone().addScaledVector(back,d), piv, f, d }; };
// where the game's aim3P would send shells / cables for a given view (eye -> crosshair hit point)
H.aimOf=(yaw,pit)=>{ const c=H.tpCamAt(yaw,pit), p=L.P.currPos, eye=H.V(p.x,p.y+1.1,p.z); const s0=Math.max(0,eye.clone().sub(c.cam).dot(c.f)), o2=c.cam.clone().addScaledVector(c.f,s0); const h=g.castRay(o2,c.f,700); const aim=h?H.V(h.point.x,h.point.y,h.point.z):o2.clone().addScaledVector(c.f,700); const d=aim.sub(eye).normalize(); return [Math.atan2(-d.x,-d.z), Math.asin(Math.max(-1,Math.min(1,d.y)))]; };
// view (yaw,pitch) that puts the crosshair ray from the 3P camera through world point X (pivot-based, 3 refinement passes)
H.ypTP=(x,y,z)=>{ const T=g.CONFIG.tp, p=L.P.currPos; let yaw=L.P.yaw, pit=L.P.pitch; for(let i=0;i<3;i++){ const c=H.tpCamAt(yaw,pit), dx=x-c.cam.x, dy=y-c.cam.y, dz=z-c.cam.z; yaw=Math.atan2(-dx,-dz); pit=Math.atan2(dy,Math.hypot(dx,dz)); } return [yaw,pit]; };
// view such that the game's aim direction (aim3P, + cable side offset off) points at X: iterate on the aim error
H.ypAim=(x,y,z,off=0)=>{ const [ty,tp]=H.yp(x,y,z,off); let [yaw,pit]=H.ypTP(x,y,z); yaw-=off; for(let i=0;i<4;i++){ const [ay,ap]=H.aimOf(yaw,pit); yaw+=H.wrap(ty-ay); pit+=tp-ap; } return [yaw,pit]; };
H.lookTP=(x,y,z,k=1)=>{ const [a,b]=H.ypTP(x,y,z); H.look(a,b,k); };
H.lookAim=(x,y,z,k=1,off=0)=>{ const [a,b]=H.ypAim(x,y,z,off); H.look(a,b,k); };
// keep the game's tpCam (used by aim3P) in sync with this frame's view even on frames that are not rendered (dry runs)
H.syncTP=()=>{ if(!g.opts.view3P) return; const c=H.tpCamAt(L.P.yaw,L.P.pitch); g.tpCam.pos.copy(c.cam); g.tpCam.valid=true; H.camD=c.d; };
// ---- promo-only POST-PROCESSING data: screen-space positions of the game's own MG tracer lines (0xffe08a Line objects),
// recorded per frame so post_tp.py can draw a glow over them. Nothing here changes the game image itself.
H.trcInit=()=>{ const R=g.renderer; if(R.__wrapped) return; const r0=R.render.bind(R); R.render=(s,c)=>{ if(s===g.scene) window.__cam=c; return r0(s,c); }; R.__wrapped=true; };
H.trcCollect=()=>{ const c=window.__cam, out=[]; if(!c) return out; const W=innerWidth, Hh=innerHeight; c.updateMatrixWorld();
  g.scene.traverse(o=>{ if(!o.isLine||!o.visible||!o.material||!o.material.color||o.material.color.getHex()!==0xffe08a) return; const a=o.geometry.attributes.position; if(!a||a.count!==2) return;
    const p0=H.V(a.getX(0),a.getY(0),a.getZ(0)), p1=H.V(a.getX(1),a.getY(1),a.getZ(1)), pts=[];
    for(let i=0;i<=24;i++){ const q=p0.clone().lerp(p1,i/24); const cs=q.clone().applyMatrix4(c.matrixWorldInverse); if(cs.z>-0.5){ if(pts.length) break; else continue; } q.project(c); pts.push([Math.round((q.x+1)/2*W), Math.round((1-q.y)/2*Hh)]); }
    if(pts.length>1) out.push({o:+(o.material.opacity??1).toFixed(2), p:pts}); });
  return out; };
}`;
