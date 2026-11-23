import json
sp=json.load(open('shots_play.json'))
base=[s for s in sp['shots'] if s['name']=='S3'][0]
def V(name, setup, per):
    return dict(name=name, frames=90, pre=0, keys=[], setup=setup, per="H.hpKeep(); L.P.yaw=-Math.PI/2; "+per+" const r=L.ropes[1]; if(f%3===0) H.log+=' '+f+':'+H.pos(L)+(r.hooked?'H'+r.L.toFixed(0):'-')+'|a'+r.anchor.toArray().map(v=>v.toFixed(0)).join(',');")
shots=[
 V('A',"H.reset(); H.place(B,300,2.2,0); H.place(L,20,27.2,0,-Math.PI/2);",
   "H.aim(46,38,0,false); if(f===2) I.jumpQueued=true; if(f===6) H.hook(46,38,0); I.hookR=f>=6;"),
 V('B',"H.reset(); H.place(B,300,2.2,0); H.place(L,20,27.2,0,-Math.PI/2);",
   "H.aim(46,38,0,false); if(f===2) I.jumpQueued=true; if(f===4) H.vel(L,10,6,0); if(f===6) H.hook(46,38,0); I.hookR=f>=6; I.stickZ=(f>=12&&f<30)?1:0;"),
 V('C',"H.reset(); H.place(B,300,2.2,0); H.place(L,22,27.2,0,-Math.PI/2);",
   "if(f<13) H.aim(60,30,0); else H.aim(48,42,0,false); if(f===4) I.jumpQueued=true; if(f===13) H.hook(48,42,0); I.hookR=(f>=13); I.stickZ=(f>=25)?1:0;"),
]
sp['shots']=shots; json.dump(sp,open('probe3.json','w'))
