// shared page config for capture + lab runs
module.exports = { fps: 60, ls: { 'wfm.device': 'pc', 'wfm.lang': 'zh-TW', 'wfm.name': 'VOLT', 'wfm.s2': 'blade', 'wfm.fcs': '1' },
  init: `()=>{ (${require('./h_init.js')})(); (${require('./fp_helpers.js')})(); }`,
  css: '#lockHint,#tut,#tutHand,#tutRing,#tutAim,#result,#fullLink,#rotate,#start,#swapHint,#vs{display:none!important}' };
