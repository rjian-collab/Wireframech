// WIREFRAMECH 鋼弦機兵 — promo v5 "SWING COMBAT" (steel-cable swing combat among terrain), game's own 3P chase camera + HUD, 60 fps game clock.
// Everything the PLAYER does is a real input: mouse look (yaw/pitch; in 3P the crosshair = 3P camera centre ray), Space jump, W (reel while hooked),
// Shift boost, Q/E cables (fired along the game's own aim ray -> findHook), right mouse = 14.5mm MG (loadout s2 = mg), left mouse = 57mm.
// The enemy is driven through ?promo=1 __botCmd: the SAME command struct the game AI emits (move/aim/fire/hookR/reel). Posed parts are marked "POSE".
const base = require('./base.js');
const CFG = Object.assign({
  P0: [26, 27.2, -2], yaw0: -90,           // POSE: hero start on the east lip of sky island 基地 A, facing east (+x)
  R1: [48, 40, 0], c1: 'R',              // cable #1 (E): underside of the floating rock in front of 基地 A (bottom y 39.5)
  rel1: 52,                      // release cable #1 (frame)
  E0: [80, 24, 16], EA: [89.9, 40, 30],   // POSE: enemy start (mid-air) + its first cable target (top of the pine at 89.9/30.2)
  EV: [14, 0, 0], eHook: -6, eRel: 9999, eReel: 0, eBoost: 0, eAlt: 26, eTop: 2, eRange: 70, eAvoid: [[110.8]], trees: [[89.9,43.6,30.2],[92.3,36.9,46.6],[110.8,41.2,29.7],[107.2,41.1,51.2],[122.2,37.8,48.3],[141.1,34.9,21.1],[142.1,39.4,59],[155.6,31.5,39.2],[157.6,33.5,21.4],[167.7,45.3,49.5],[176.6,42.5,33]], eLag: 14, eTrail: 5.0, eFire0: 20,
  R2: [110.8, 39, 29.7], c2: 'L', h2: 76, rel2: 9999, reel2: [0, 50], b2: [0, 20],   // cable #2 (Q): top of the pine at (110.8, 29.7); cable #3 (E): top of the pine at (122.2, 48.3)
  mg: [206, 224], shots: [[100, 125], [160, 200], [244, 264]], stay: 16, yo: 10, yo2: 10, po: 0, flick: 18, postYaw: 0, postP: -10,                 // hero MG burst frames
  look1: -110, ehp: 3400, slowK: 0.3, slowIn: 6, slowHold: 20, slowOut: 30, h3: 184, R3: [122.2, 36, 48.3], c3: 'R', rel3: 9999,                    // yaw (deg) the hero looks at during the launch
}, process.env.CFG ? JSON.parse(process.env.CFG) : {});
module.exports = { ...base, frames: +(process.env.FRAMES || 365), pre: +(process.env.PRE || 6),
  setup: `H.reset(); g.setView(true); document.body.classList.remove('vsOn');
    H.cfg=${JSON.stringify(CFG)}; const C=H.cfg;
    H.place(L,...C.P0,C.yaw0*Math.PI/180); H.place(B,...C.E0,Math.PI); if(C.EV) H.vel(B,...C.EV);
    L.hp=4380; B.hp=C.ehp; L.P.fuel=6; L.weapon.s2='mg'; L.weapon.active='main'; L.weapon.cannon.ammo=4; L.weapon.cannon.reserve=12; L.weapon.cannon.cool=0;
    B.weapon.s2='mg'; B.weapon.active='mg'; B.weapon.ammo=200; B.weapon.reserve=600; B.name='Kestrel_09';
    g.match.score=[2,1]; g.match.timeLeft=131; H.keys(); H.botQ=[]; H.log=''; H.st={}; H.ts=1; H.hits=0; window.__promoBoomK=1.0; window.__promoSparkS=1.4; H.trcInit();
    L.P.pitch=0.3;`,
  per: `
  const S=H.st, C=H.cfg, p=L.P.currPos, q=B.P.currPos, P=L.P, D=Math.PI/180; H.keys(); H.mark=false;
  if (L.hp<4380){ H.hits=(H.hits||0)+1; } L.hp=4380; g.match.timeLeft=Math.max(0,131-f/60);
  const ec=[q.x,q.y+0.6,q.z];
  // ---------------- enemy (scripted AI command) ----------------
  // The enemy pilot does what the game AI does to travel: right cable (hookR) to a pine top, reel (moveZ) to keep height; when a cable
  // breaks (the game cuts it when terrain blocks the line) it fires a new one at the next pine top within reach.
  { const bc=H.bc, e=B.P.currPos, r=B.ropes[1]; bc.moveX=0; bc.moveZ=0; bc.boost=false;
    if (!S.dead && f>=C.eHook){
      if (!r.hooked){ if (S.eWas){ S.eWas=false; S.eLast=S.eT; S.eT=null; }
        if (!S.eT){ let best=null, bd=1e9; for (const t of C.trees){ if (S.eLast && t===S.eLast) continue; if (C.eAvoid.some(a=>a[0]===t[0])) continue; const d=Math.hypot(t[0]-e.x,t[2]-e.z); const dd=Math.hypot(d,t[1]-2-e.y); if (dd<C.eRange && t[1]-2>e.y && d<bd && d>4){ bd=d; best=t; } } S.eT=best||C.EA; S.eTf=f; }
        const a=S.eT===C.EA?C.EA:[S.eT[0],S.eT[1]-C.eTop,S.eT[2]], dx=a[0]-e.x, dy=a[1]-(e.y+1.1), dz=a[2]-e.z;
        bc.ropeYaw=Math.atan2(-dx,-dz)+8*D; bc.ropePitch=Math.atan2(dy,Math.hypot(dx,dz)); bc.hookR = (f-S.eTf)%4!==0;   // tap E until it catches
      } else { S.eWas=true; bc.hookR=true; bc.moveZ = e.y<C.eAlt ? 1 : 0; bc.boost = e.y<C.eAlt-6; }
    } else bc.hookR=false;
    if(!S.dead){ H.botFireAt(C.eLag, C.eTrail, 0.6); bc.fire = f>=C.eFire0; } }
  // ---------------- hero ----------------
  const gone = S.fired && B.hp>=6000;                      // game already respawned the bot at its base after the kill
  const ecL = gone && H.lastE ? [H.lastE[0],H.lastE[1]+0.6,H.lastE[2]] : ec;
  const o1=C.c1==='L'?0.1396:-0.1396, o2=C.c2==='L'?0.1396:-0.1396;
  if (f===-4){ I.jumpQueued=true; I.jumpZ=1; }              // Space + W: hop off the sky-island lip
  if (f<4) H.lookAim(...C.R1, 0.35, o1);                    // look up at the floating rock
  if (f>=2 && f<C.rel1){ I[C.c1==='L'?'hookL':'hookR']=true; I.stickZ=1; }   // cable #1 + W reel (zip under the rock)
  const [ey,ep]=H.ypTP(...ecL);
  if (f>=4 && f<C.h2-C.flick) H.look(ey+C.yo*D, ep+C.po*D, f<C.rel1?0.06:0.16);      // look at the enemy (kept a little right of the reticle)
  else if (f>=C.h2-C.flick && f<C.h2+2) H.lookAim(...C.R2, f>=C.h2-2?1:0.3, o2);            // flick to the next pine top
  else if (f>=C.h2+2 && !S.fired && !(S.sh||[]).some(s=>s&&f<s.f+C.stay) && !C.shots.some((w,i)=>f>=w[0]&&f<w[1]&&!(S.sh||[])[i])) H.look(ey+C.yo2*D, ep+C.po*D, 0.2);
  if (f>=C.h2 && f<C.rel2){ I[C.c2==='L'?'hookL':'hookR']=true; const k=f-C.h2; I.stickZ=(k>=C.reel2[0]&&k<C.reel2[1])?1:0; I.boost=(k>=C.b2[0]&&k<C.b2[1]); }
  if (f>=C.mg[0]-6 && f<C.mg[1]){ const [a3,b3]=H.ypTP(...ec); H.look(a3,b3,0.45); }
  if (f>=C.mg[0] && f<C.mg[1]){ I.swapTo='mg'; I.fire=true; }   // right mouse: 14.5mm MG
  if (f===C.mg[1]) I.swapTo='main';
  // 57mm (left mouse): inside each window, put the crosshair on the enemy and fire once the game's aim ray is within 1.5 deg (fire control does the rest)
  S.sh=S.sh||[]; const sw=C.shots.findIndex(w=>f>=w[0]&&f<w[1]);
  if (sw>=0 && !S.sh[sw] && !gone){ const [a2,b2]=H.ypTP(...ec); H.look(a2,b2,f-C.shots[sw][0]<4?0.35:f-C.shots[sw][0]<8?0.75:1); I.swapTo='main';
    const to=new p.constructor(ec[0]-p.x,ec[1]-p.y-1.1,ec[2]-p.z).normalize(), am=H.aimOf(P.yaw,P.pitch), fw=H.fwd(am[0],am[1]);
    S.ae=Math.acos(Math.min(1,fw.dot(to)))/D;
    if (fw.dot(to)>Math.cos(1.8*D) && H.los() && !(L.weapon.cannon.cool>0)){ S.sh[sw]={f, n:L.weapon.cannon.ammo}; H.mark=true; if(sw===C.shots.length-1) S.fired=f; } }
  for (const s of S.sh) if (s && L.weapon.cannon.ammo===s.n && f<s.f+20 && f>=s.f) I.fire=true;   // hold the trigger until the game actually fires the shell
  for (const s of S.sh) if (s && f>s.f && f<s.f+C.stay){ const [a2,b2]=H.ypTP(...ecL); H.look(a2+C.yo*D*0.5,b2,0.25); }
  if (S.fired && f>S.fired){ if(!S.dead){ const [a2,b2]=H.ypTP(...ecL); H.look(a2,b2,0.3); } else { if(S.hd==null) S.hd=P.yaw; H.look(S.hd+C.postYaw*D, C.postP*D, 0.05); } }
  if (S.fired && !S.dead && gone){ S.dead=f; H.mark=true; }
  if (S.dead===f){ H.bc.fire=false; S.boomAt=[...H.lastE]; B.mech.root.visible=false; if(window.__promoBurst) __promoBurst(new p.constructor(...S.boomAt), 60, 22, 6); }
  if (S.dead && f===S.dead+3 && window.__promoBurst) __promoBurst(new p.constructor(S.boomAt[0],S.boomAt[1]+1.5,S.boomAt[2]), 50, 16, 8);
  if (S.dead){ H.bc.fire=false; H.bc.hookR=false; B.mech.root.visible=false; }
  if (!S.dead && B.hp<6000) H.lastE=[q.x,q.y,q.z];
  if (C.h3 && f>=C.h3-C.flick && f<C.h3+2 && !C.shots.some((w,i)=>f>=w[0]&&f<w[1]&&!(S.sh||[])[i])) H.lookAim(...C.R3, 0.32, C.c3==='L'?0.1396:-0.1396);
  if (C.h3 && f>=C.h3 && f<C.rel3){ I[C.c3==='L'?'hookL':'hookR']=true; I.stickZ=1; }
  // in-engine speed ramp (promo only): game clock eases to slowK during the last cannon window, back to 1.0 after the kill
  { const w=C.shots[C.shots.length-1]; if (S.slow==null && f>=w[0]) S.slow=f;
    let k=1; if (S.slow!=null) k=Math.max(C.slowK, 1-(f-S.slow)/C.slowIn*(1-C.slowK));
    if (S.dead) k=Math.min(1, C.slowK+Math.max(0,f-S.dead-C.slowHold)/C.slowOut*(1-C.slowK));
    H.ts = (S.slow!=null) ? k : 1; }
  H.syncTP();
  const to=[q.x-p.x,q.y-p.y,q.z-p.z], dist=Math.hypot(...to), byaw=Math.atan2(-to[0],-to[2])/D;
    H.log='d:'+dist.toFixed(0)+' brg:'+(H.wrap(byaw*D-P.yaw)/D).toFixed(0)+' hits:'+(H.hits||0)+' sh:'+(S.sh||[]).map(s=>s&&s.f).join('/')+' ae:'+(S.ae||0).toFixed(1)+' cool:'+L.weapon.cannon.cool+' ts:'+(H.ts||1).toFixed(2)+' fire:'+(S.fired||'')+' dead:'+(S.dead||'');
  `,
  keys: (process.env.KEYS || '').split(',').filter(Boolean).map(Number) };
