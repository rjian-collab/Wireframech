// WIREFRAMECH 鋼弦機兵 — promo v5 THIRD-PERSON "POINT-BLANK" finish (零距離貼臉), game's own 3P chase camera (60 fps game clock).
// Beats 1-2 (MG dodge, cable 1 + cable 2 swing up) are the same as choreo_tp.js. New finish:
//   cable 3 (Q) fired DOWN at the ground right beside the enemy + full reel (W) = grapple-dive → the hero slams in at the enemy's feet,
//   the enemy tries to hop away (bot jump), the hero fires the 57mm into it from ~3 m (capsules almost touching) → kill,
//   hero pounces forward (Space+W) + boost over the blast, then WHIPS the view back ~180° onto the fireball (look-back) and drifts away.
// Everything the PLAYER does is a real input (mouse yaw/pitch, WASD, Shift, Space, Q/E cables via the game's own findHook, W reel, left click).
// Posed parts are marked "POSE".
const base = require('./base.js');
const CFG = Object.assign({ E: [261, 2], A1: [258.5, 30, 21], A2: [288.5, 37, 30], b1: [136, 999], b2: 17, r2min: 196, relL: 5, yo1: 11, po1: 2,
  yo: 28, showP: -30,        // over-the-top look (as before, but no slow-mo here)
  dive: 14,                  // frames after cable 2 hooks: release it and fire cable 3 down at the ground
  G: [264.6, 0, -0.6],       // cable-3 ground point (beside the enemy, on the hero's side)
  ET: [261.5, 15], rt: 160,  // enemy backs off (real bot movement) from E to ET while the hero is on cable 1/2
  hopY: 15,                  // enemy hops straight up (bot jump) when the diving hero is below this height
  relY: 3.6,                 // hero lets go of cable 3 just before touching down
  fireD: 5.2, fireY: 2.6, dyMin: 2.2,   // point-blank shot: hero on the ground, enemy (mid-hop) above it, centres < fireD apart
  // camD/camY/camPost: POSE promo-only camera assist (<=0.5 s of video incl. the 8-frame hit-stop): chase distance 15 m -> camD around the shot
  esc: 4, turn: 12, turnF: 16, whip: 36, whipF: 17, holdTs: 0.3, postTs: 0.5, escRot: -40, slowY: 6.5,
  camD: 8, camY: 2.4, camPost: 2 }, process.env.CFG ? JSON.parse(process.env.CFG) : {});
const E = CFG.E;
module.exports = { ...base, frames: +(process.env.FRAMES || 470), pre: +(process.env.PRE || 24),
  setup: `H.reset(); g.setView(true); document.body.classList.remove('vsOn');
    // POSE: start positions (same as choreo_tp.js).
    H.place(L,278,2.2,-22,Math.PI); H.place(B,${E[0]},2.2,${E[1]},0);
    // POSE: HP. Enemy already damaged to 1500/6000 (= three earlier 57mm hits, 1500 each) so one direct hit is lethal.
    L.hp=4380; B.hp=1500; L.P.fuel=6; L.weapon.active='main'; L.weapon.cannon.ammo=4; L.weapon.cannon.reserve=12; L.weapon.cannon.cool=0;
    B.weapon.s2='mg'; B.weapon.active='mg'; B.weapon.ammo=200; B.weapon.reserve=600; B.name='Kestrel_09';
    g.match.score=[2,1]; g.match.timeLeft=131; H.keys(); H.botQ=[]; H.log=''; H.st={}; H.ts=1; window.__promoBoomK=1.0; window.__promoSparkS=1.4;
    H.cfg=${JSON.stringify(CFG)}; H.trcInit();
    H.E=H.cfg.E; H.A1=H.cfg.A1; H.A2=H.cfg.A2;`,
  per: `
  const S=H.st, C=H.cfg, p=L.P.currPos, q=B.P.currPos, P=L.P, D=Math.PI/180; H.keys(); H.mark=false;
  const gone = S.fired && B.hp>=6000;                       // game already respawned the bot at its base after the kill
  const ec = gone && H.lastE ? [H.lastE[0],H.lastE[1]+0.6,H.lastE[2]] : [q.x,q.y+0.6,q.z];   // enemy chest
  if (L.hp<4380){ H.hits=(H.hits||0)+1; } L.hp=4380;   // player HP is held at 4380 (HUD only); MG hits would be counted in H.hits
  g.match.timeLeft=Math.max(0,131-f/60);
  const dE=Math.hypot(p.x-q.x,p.y-q.y,p.z-q.z);
  // ---------------- enemy: real 14.5mm MG, aims where the player WAS (lagged) ----------------
  const burst = (f>=4&&f<70)||(f>=82&&f<140)||(f>=165&&f<235)||(S.c3 && !S.fired);
  if(!S.dead){ H.botFireAt(f<150?16:10, f<150?2.6:3.5, f<150?1.2:0.5); H.bc.fire = burst; H.bc.moveX=0; H.bc.moveZ=0;
    if (f>=C.rt && !S.hop){ const dx=C.ET[0]-q.x, dz=C.ET[1]-q.z, dl=Math.hypot(dx,dz), yw=H.bc.yaw??B.P.yaw;   // enemy backs off while the hero is up on the cables (real bot movement)
      if (dl>0.6){ const ux=dx/dl, uz=dz/dl, k=Math.min(1,dl/2); H.bc.moveZ=k*(ux*-Math.sin(yw)+uz*-Math.cos(yw)); H.bc.moveX=k*(ux*Math.cos(yw)+uz*-Math.sin(yw)); } } }
  if(S.c3 && !S.hop && !S.fired && p.y<C.hopY){ S.hop=f; H.bc.jump=true; H.bc.jumpX=0; H.bc.jumpZ=0; H.mark=true; }   // enemy panics and hops straight up (real bot jump)
  // ---------------- player ----------------
  if (f<142){                                              // BEAT 1: dodge the MG streams (same as choreo_tp.js)
    if(f===10){ I.jumpQueued=true; I.jumpX=1; }
    if(f>=45&&f<72){ I.stickX=-1; I.boost=true; }
    if(f===118){ I.jumpQueued=true; I.jumpX=1; }
    if(f===136){ I.jumpQueued=true; }
    { const [a,b]=H.ypTP(...ec); H.look(a+C.yo1*D, b+C.po1*D, 0.18); }
  } else if (f<150){ H.lookAim(...H.A1, 0.4, 0.1396); I.boost=f>=136; }
  else if (!S.r2){                                         // BEAT 2: cable #1 (left, Q) → reel (W)
    if(f===150) H.lookAim(...H.A1, 1, 0.1396);
    I.hookL = true; I.stickZ = 1; I.boost = f>=C.b1[0] && f<C.b1[1];
    if (f>=186){ H.lookAim(...H.A2, f>=C.r2min?1:0.35, -0.1396);
      if (f>=C.r2min && p.distanceTo({x:H.A2[0],y:H.A2[1],z:H.A2[2]})<58.5){ I.hookR=true; if(L.ropes[1].hooked){ S.r2=f; H.mark=true; } } }
    else H.lookTP(...ec, 0.12);
  } else if (!S.c3){                                       // cable #2 (right, E) → swing up and over the enemy
    I.hookR=true; I.hookL = f < S.r2+C.relL; I.stickZ = 1; I.boost = f < S.r2+C.b2;
    if (f < S.r2+8) H.lookAim(...H.A2, 0.3, -0.1396);
    else if (f < S.r2+C.dive){ const [ey]=H.ypTP(...ec); H.look(ey+C.yo*D, C.showP*D, 0.25); }   // over the top: hero up top, enemy lower-right
    else { I.hookR=false; I.stickZ=0;                     // BEAT 3: let go of cable 2, flick the crosshair down beside the enemy and fire cable 3 (Q) into the ground
      H.lookAim(...C.G, f < S.r2+C.dive+3 ? 0.5 : 1, 0.1396); if (f >= S.r2+C.dive+2){ I.hookL=true; if (L.ropes[0].hooked){ S.c3=f; H.mark=true; } } }
  } else if (!S.fired){                                    // grapple-dive: full reel on cable 3, crosshair onto the enemy's face
    if (!S.rel && p.y<C.relY) S.rel=f;
    I.hookL=!S.rel; I.stickZ=S.rel?0:1;
    H.lookTP(...ec, f < S.c3+6 ? 0.25 : 0.5);
    const am=H.aimOf(P.yaw,P.pitch), fw=H.fwd(am[0],am[1]);
    const ah=g.castRay(H.V(p.x,p.y+1.1,p.z),fw,12), onE=ah && Math.hypot(ah.point.x-q.x,ah.point.y-q.y,ah.point.z-q.z)<2.4;   // the shell's line (game aim3P) actually meets the enemy's body
    if (p.y<C.fireY && q.y-p.y>C.dyMin && dE < C.fireD && onE){ S.fired=f; S.shots0=L.weapon.fired; H.mark=true; }   // POINT-BLANK 57mm
  }
  if (S.fired && f>=S.fired && L.weapon.fired===S.shots0) I.fire=true;   // hold the trigger until the game has actually fired the shell
  if (S.fired && f>S.fired){
    if(!S.dead){ H.lookTP(...ec, 0.3); }
    if(!S.dead && gone){ S.dead=f; H.mark=true; }
  }
  if (S.dead && f>S.dead){
    const k=f-S.dead; if(S.hd==null) S.hd=P.yaw;
    if(!S.ed){ const dx=p.x-S.boomAt[0], dz=p.z-S.boomAt[2], dl=Math.hypot(dx,dz)||1, r=C.escRot*D; S.ed=[(dx*Math.cos(r)-dz*Math.sin(r))/dl,(dx*Math.sin(r)+dz*Math.cos(r))/dl]; S.ey=Math.atan2(-S.ed[0],-S.ed[1]); }   // escape heading: away from the blast
    const stickTo=(ux,uz)=>{ const y=P.yaw; I.stickZ=ux*-Math.sin(y)+uz*-Math.cos(y); I.stickX=ux*Math.cos(y)+uz*-Math.sin(y); };
    if (k===C.esc) { I.jumpQueued=true; I.jumpZ=-1; }                 // back-hop off the ground (Space + S), away from the blast
    if (k>C.esc) { stickTo(...S.ed); I.boost=k<C.whip+40; }          // boost away
    if (k < C.turn) H.look(S.hd, P.pitch, 0.2);                       // eyes still on the blast while blown back
    else if (k < C.whip){ const u=Math.min(1,(k-C.turn)/C.turnF), e=u*u*(3-2*u); if(S.ty0==null){ S.ty0=P.yaw; S.tp0=P.pitch; }
      P.yaw=S.ty0+H.wrap(S.ey-S.ty0)*e; P.pitch=S.tp0+(-6*D-S.tp0)*e; }   // spin round and boost off (player turns the mouse ~180°)
    else { if(S.wy==null){ S.wy=P.yaw; S.wp=P.pitch; }               // WHIP-PAN: player snaps the mouse back ~180° onto the fireball behind
      const [ty,tp]=H.ypTP(S.boomAt[0],S.boomAt[1]+1,S.boomAt[2]); const u=Math.min(1,(k-C.whip)/C.whipF), e=u<0.5?2*u*u:1-Math.pow(-2*u+2,2)/2;
      if (u<1){ P.yaw=S.wy+H.wrap(ty-S.wy)*e; P.pitch=S.wp+(tp-S.wp)*e; } else H.look(ty,tp,0.3); }
  }
  if(S.dead===f){ /* enemy just died (game reset its HP and teleported it to its base) */
    H.bc.fire=false; S.boomAt=[...H.lastE]; B.mech.root.visible=false;   // POSE: hide the respawned bot so it doesn't pop up far away
    if(window.__promoBurst) __promoBurst(new p.constructor(...S.boomAt), 70, 24, 6);   // promo-mode spark burst
  }
  if(S.dead && (f===S.dead+3 || f===S.dead+C.whip+C.whipF-4 || f===S.dead+C.whip+C.whipF+14) && window.__promoBurst) __promoBurst(new p.constructor(S.boomAt[0],S.boomAt[1]+1.5,S.boomAt[2]), 50, 16, 8);
  if(S.dead){ H.bc.fire=false; B.mech.root.visible=false; }
  if(!S.dead && B.hp<6000) H.lastE=[q.x,q.y,q.z];
  // in-engine speed ramp: only around the point-blank contact, and a slight slow-down during the look-back hold
  let ts=1;
  if (S.c3 && !S.dead && (S.sl || p.y<C.slowY)){ if(!S.sl) S.sl=f; ts=Math.max(0.25,1-(f-S.sl)/6*0.75); }   // 0.25x only around the contact
  if (S.dead){ const k=f-S.dead; ts = k<10 ? 0.25 : Math.min(C.postTs, 0.25+(k-10)/8*(C.postTs-0.25));
    if (k>=C.whip) ts = Math.max(C.holdTs, C.postTs-(k-C.whip)/C.whipF*(C.postTs-C.holdTs)); }
  H.ts=ts;
  // POSE: promo-only camera assist. For a few frames around the point-blank shot the game's own chase camera is pulled in along the SAME
  // view ray (CONFIG.tp.dist 15 m -> camD). Direction, crosshair and aim (aim3P) are unchanged; only the camera distance is shortened.
  { const T=g.CONFIG.tp, a1=S.dead?S.dead+C.camPost:1e9; if(S.c3&&!S.fired&&p.y<C.camY&&S.cam0==null) S.cam0=f;   // starts at touchdown, ends camPost frames after the kill
    let w=0; if(S.cam0!=null && f>=S.cam0){ w=Math.min(1,(f-S.cam0+1)/3); if(f>a1) w=Math.max(0,1-(f-a1)/3); }
    T.dist=15+(C.camD-15)*w*w*(3-2*w); S.camW=w; }
  H.syncTP();
  H.log = 'cam:'+(H.camD||0).toFixed(1)+' r2:'+(S.r2||'')+' c3:'+(S.c3||'')+' hop:'+(S.hop||'')+' fire:'+(S.fired||'')+' dead:'+(S.dead||'')+' whip:'+(S.dead?S.dead+C.whip:'')+' ts:'+H.ts.toFixed(2)+' camW:'+(S.camW||0).toFixed(2)+' rel:'+(S.rel||'')+' dE:'+dE.toFixed(1)+' dy:'+(q.y-p.y).toFixed(1)+' hits:'+(H.hits||0);
  `,
  keys: (process.env.KEYS||"").split(",").filter(Boolean).map(Number) };
