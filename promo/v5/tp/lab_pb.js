// Dry-run choreo_pb.js for several CFG variants in one browser load (no rendering). Usage:
//   LAB=lab_pb.js VARS='[{...cfg...},...]' [EVERY=3] node cap_tp.js base.js x
const vars = JSON.parse(process.env.VARS || '[{}]');
module.exports = { fps: 60, every: +(process.env.EVERY || 6), variants: vars.map((c, i) => { process.env.CFG = JSON.stringify(c); delete require.cache[require.resolve('./choreo_pb.js')]; const ch = require('./choreo_pb.js');
  return { name: 'v' + i + ' ' + JSON.stringify(c), frames: ch.frames, setup: ch.setup, per: ch.per }; }) };
