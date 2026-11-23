// Dry-run the full choreography for several CFG variants in one browser load (no rendering). Usage:
//   LAB=lab_fp.js VARS='[{...cfg...},...]' node cap_fp.js base.js x
const fs = require('fs');
const vars = JSON.parse(process.env.VARS || '[{}]');
module.exports = { fps: 60, every: 6, variants: vars.map((c, i) => { process.env.CFG = JSON.stringify(c); delete require.cache[require.resolve('./choreo_fp.js')]; const ch = require('./choreo_fp.js');
  return { name: 'v' + i + ' ' + JSON.stringify(c), frames: ch.frames, setup: ch.setup, per: ch.per }; }) };
