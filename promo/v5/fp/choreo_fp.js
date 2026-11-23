// WIREFRAMECH 鋼弦機兵 — promo v5 first-person high-mobility shot (60 fps game clock).
// Everything the PLAYER does here is a real input (mouse look yaw/pitch, A/D strafe, Shift boost, Space side-hop,
// Q/E cables via the game's own findHook ray, W reel, left-click 57mm cannon). Posed parts are marked "POSE".
const base = require('./base.js');
// tunables (cable anchors are points on two real, hookable pine trees; E = enemy ground position, POSE: chosen under the swing path)
const CFG = Object.assign({ E: [268, -10], A1: [258.5, 30, 21], A2: [288.5, 37, 30], b1: [136, 999], b2: 17, dhFire: 3.5, dhSlow: 10, r2min: 196, relL: 5 }, process.env.CFG ? JSON.parse(process.env.CFG) : {});
const E = CFG.E, A1 = CFG.A1, A2 = CFG.A2;
module.exports = { ...base, frames: +(process.env.FRAMES || 350), pre: 8,
  setup: `H.reset(); g.setView(false); document.body.classList.remove('vsOn');
    // POSE: start positions. Player on open ground south of the pine row, enemy ~31 m ahead.
    H.place(L,278,2.2,-22,Math.PI); H.place(B,${E[0]},2.2,${E[1]},0);
    // POSE: HP. Enemy already damaged to 1500/6000 (= three earlier 57mm hits, 1500 each) so one direct hit is lethal.
    L.hp=4380; B.hp=1500; L.P.fuel=6; L.weapon.active='main'; L.weapon.cannon.ammo=4; L.weapon.cannon.reserve=12; L.weapon.cannon.cool=0;
    B.weapon.s2='mg'; B.weapon.active='mg'; B.weapon.ammo=200; B.weapon.reserve=600; B.name='Kestrel_09';
    g.match.score=[2,1]; g.match.timeLeft=131; H.keys(); H.botQ=[]; H.log=''; H.st={}; H.ts=1; window.__promoBoomK=1.0; window.__promoSparkS=1.4;
    H.cfg=${JSON.stringify(CFG)};
    H.E=H.cfg.E; H.A1=H.cfg.A1; H.A2=H.cfg.A2;`,
  per: `
  const S=H.st, p=L.P.currPos, q=B.P.currPos, P=L.P; H.keys(); H.mark=false;
  const gone = S.fired && B.hp>=6000;                       // game already respawned the bot at its base after the kill
  const ec = gone && H.lastE ? [H.lastE[0],H.lastE[1]+0.6,H.lastE[2]] : [q.x,q.y+0.6,q.z];   // enemy chest
  if (L.hp<4380){ H.hits=(H.hits||0)+1; } L.hp=4380;   // player HP is held (any MG hit would be counted in H.hits and shows as a red hurt flash) g.match.timeLeft=Math.max(0,131-f/60);
  // ---------------- enemy: real 14.5mm MG, aims where the player WAS (lagged) ----------------
  const burst = (f>=4&&f<70)||(f>=82&&f<140)||(f>=165&&f<235);
  if(!S.dead){ H.botFireAt(f<150?16:10, f<150?2.6:3.5, f<150?1.2:0.5); H.bc.fire = burst; H.bc.moveX=0; }
  // ---------------- player ----------------
  if (f<142){                                              // BEAT 1: dodge the MG streams
    if(f===10){ I.jumpQueued=true; I.jumpX=1; }            //   side-hop right (Space + D)
    if(f>=45&&f<72){ I.stickX=-1; I.boost=true; }          //   boost-strafe left (Shift + A)
    if(f===118){ I.jumpQueued=true; I.jumpX=1; }           //   side-hop right again
    if(f===136){ I.jumpQueued=true; }                      //   hop up, about to cable
    H.lookAt(...ec, 0.18);
  } else if (f<150){ H.lookAt(...H.A1, 0.4, 0.1396); I.boost=f>=136; }
  else if (!S.r2){                                         // BEAT 2: cable #1 (left, Q) → reel (W)
    if(f===150) H.lookAt(...H.A1, 1, 0.1396);
    I.hookL = true; I.stickZ = 1; I.boost = f>=H.cfg.b1[0] && f<H.cfg.b1[1];
    if (f>=186){ H.lookAt(...H.A2, f>=H.cfg.r2min?1:0.35, -0.1396);
      if (f>=H.cfg.r2min && p.distanceTo({x:H.A2[0],y:H.A2[1],z:H.A2[2]})<58.5){ I.hookR=true; if(L.ropes[1].hooked){ S.r2=f; H.mark=true; } } }
    else H.lookAt(...ec, 0.12);
  } else if (!S.fired){                                    // cable #2 (right, E) → swing up and over
    I.hookR=true; I.hookL = f < S.r2+H.cfg.relL; I.stickZ = 1; I.boost = f < S.r2+H.cfg.b2;
    const dh=Math.hypot(p.x-q.x,p.z-q.z);
    if (f < S.r2+12) H.lookAt(...H.A2, 0.3, -0.1396); else H.lookAt(...ec, f<S.r2+20?0.22:0.35);
    if(!S.slow && dh<H.cfg.dhSlow && p.y>q.y+6) S.slow=f;
    const to=new p.constructor(ec[0]-p.x,ec[1]-p.y-1.1,ec[2]-p.z).normalize(), fw=new p.constructor(-Math.sin(P.yaw)*Math.cos(P.pitch),Math.sin(P.pitch),-Math.cos(P.yaw)*Math.cos(P.pitch));
    if (S.slow && dh<H.cfg.dhFire && fw.dot(to)>Math.cos(1.5*Math.PI/180) && p.y>q.y+7){ S.fired=f; S.shots0=L.weapon.fired; H.mark=true; }   // BEAT 3: 57mm straight down
  }
  if (S.fired && f>=S.fired && L.weapon.fired===S.shots0) I.fire=true;   // hold the trigger until the game has actually fired the shell
  if (S.fired && f>S.fired) {
    I.hookR = f < S.fired+40; I.stickZ = 0;
    if(!S.dead) H.lookAt(...ec, 0.3);
    else if (f < S.dead+40) H.lookAt(S.boomAt[0],S.boomAt[1]+1,S.boomAt[2], 0.25);
    else { if(!S.hd){ const v=L.P.vel, hv=Math.hypot(v.x,v.z)||1; S.hd=[v.x/hv, v.z/hv]; } H.lookAt(p.x+S.hd[0]*120, p.y-24, p.z+S.hd[1]*120, 0.05); }   // ease the view up to the horizon ahead
    if(!S.dead && gone) { S.dead=f; H.mark=true; }
  }
  if(S.dead===f){ /* enemy just died (game reset its HP and teleported it to its base) */
    H.bc.fire=false; S.boomAt=[...H.lastE]; B.mech.root.visible=false;   // POSE: hide the respawned bot so it doesn't pop up far away
    if(window.__promoBurst) __promoBurst(new p.constructor(...S.boomAt), 60, 22, 6);   // promo-mode spark burst
  }
  if(S.dead && f===S.dead+3 && window.__promoBurst) __promoBurst(new p.constructor(S.boomAt[0],S.boomAt[1]+1.5,S.boomAt[2]), 50, 16, 8);
  if(S.dead){ H.bc.fire=false; B.mech.root.visible=false; }
  if(!S.dead && B.hp<6000) H.lastE=[q.x,q.y,q.z];   // last position before the game respawned the bot
  // in-engine speed ramp around the cannon shot only
  const sl=S.slow||1e9, fr=S.fired||1e9, k=S.dead? Math.min(1,0.25+(f-S.dead)/30*0.75) : (f>=sl? Math.max(0.25,1-(f-sl)/10*0.75) : 1);
  H.ts = (S.dead && f-S.dead>=30) ? 1 : k;
  H.log = 'r2:'+(S.r2||'')+' slow:'+(S.slow||'')+' fire:'+(S.fired||'')+' dead:'+(S.dead||'')+' ts:'+H.ts.toFixed(2)+' hits:'+(H.hits||0);
  `,
  keys: [] };
