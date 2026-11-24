// Dry-run (no rendering) several variants in one browser load. Usage:
//   LAB=lab_sw.js VARS='[{...cfg...},...]' node cap_sw.js base.js x        (variants of choreo_sw.js CFG)
//   LAB=lab_sw.js RAW=experiment.js node cap_sw.js base.js x               (RAW module exports {variants:[{name,frames,setup,per}]})
const vars = JSON.parse(process.env.VARS || '[{}]');
module.exports = process.env.RAW ? { fps: 60, every: +(process.env.EVERY || 6), variants: require(require('path').resolve(process.env.RAW)).variants } :
 { fps: 60, every: +(process.env.EVERY || 6), variants: vars.map((c, i) => { process.env.CFG = JSON.stringify(c); delete require.cache[require.resolve('./choreo_sw.js')]; const ch = require('./choreo_sw.js');
  return { name: 'v' + i + ' ' + JSON.stringify(c), frames: ch.frames, pre: ch.pre, setup: ch.setup, per: ch.per }; }) };
