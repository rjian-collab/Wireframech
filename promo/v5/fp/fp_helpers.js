// First-person helpers added on top of H (promo helper). All of these only set the same inputs a player would
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
H.probe=f=>({ f, los:H.los(), p:H.pos(L), v:+L.P.vel.length().toFixed(1), vy:+L.P.vel.y.toFixed(1), g:L.P.grounded?1:0, yaw:+(L.P.yaw/DEG).toFixed(0), pit:+(L.P.pitch/DEG).toFixed(0), rL:L.ropes[0].hooked?L.ropes[0].anchor.toArray().map(v=>+v.toFixed(1)):0, rR:L.ropes[1].hooked?L.ropes[1].anchor.toArray().map(v=>+v.toFixed(1)):0, fuel:+L.P.fuel.toFixed(2), bhp:Math.round(B.hp), lhp:Math.round(L.hp), b:H.pos(B), log:H.log });
}`;
