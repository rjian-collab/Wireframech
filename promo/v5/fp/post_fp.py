#!/usr/bin/env python3
"""Post for the FP high-mobility shot: trim, hit-stop + punch-in + shake on the cannon kill, optional caption, H.264 encode.
usage: python3 post_fp.py FRAMES_DIR OUT.mp4 [--caption] [--impact N] [--end N]
The in-engine speed ramp (game clock slowed to 0.25x only around the shot) is already baked into the captured frames."""
import sys, json, glob, os, subprocess, random, argparse
from PIL import Image, ImageDraw, ImageFont
ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--caption', action='store_true')
ap.add_argument('--impact', type=int, default=None); ap.add_argument('--end', type=int, default=None); ap.add_argument('--start', type=int, default=0)
ap.add_argument('--hold', type=int, default=6); ap.add_argument('--punch', type=float, default=0.09); ap.add_argument('--shake', type=float, default=16)
ap.add_argument('--fps', type=int, default=60); ap.add_argument('--vertical', action='store_true', help='9:16 centre-crop test (608x1080 -> 1080x1920)')
a = ap.parse_args()
frames = sorted(glob.glob(os.path.join(a.src, '[0-9]*.png')))
probe = json.load(open(os.path.join(a.src, 'probe.json')))
def logv(k):
    for r in probe:
        v = r['log'].split(k + ':')[1].split(' ')[0]
        if v: return int(v)
dead = logv('dead'); fired = logv('fire')
hitf = next((r['f'] for r in probe if r['f'] > (fired or 0) and r['bhp'] != probe[0]['bhp']), dead)   # first frame after the shell hit (HP reset = kill)
impact = a.impact if a.impact is not None else hitf          # first frame that shows the explosion
end = a.end if a.end is not None else min(len(frames), dead + 165)
W, H = Image.open(frames[0]).size
seq = []   # (frame index, punch scale, dx, dy)
random.seed(7)
for i in range(a.start, end):
    if i == impact:
        for h in range(a.hold): seq.append((i, 1 + a.punch, 0, 0))     # hit-stop: hold the impact frame, already punched-in
    k = i - impact
    if 0 <= k < 16:
        e = (1 - k / 16) ** 2
        s = 1 + a.punch * e; amp = a.shake * (1 - k / 12) if k < 12 else 0
        seq.append((i, s, random.uniform(-amp, amp), random.uniform(-amp, amp)))
    else: seq.append((i, 1.0, 0, 0))
if a.hold:   # add a little shake to the held frames too (first 2 held frames still, then jitter)
    j = [n for n, x in enumerate(seq) if x[0] == impact][:a.hold]
    for m, n in enumerate(j):
        amp = a.shake * (0.6 if m >= 2 else 0); seq[n] = (seq[n][0], seq[n][1], random.uniform(-amp, amp), random.uniform(-amp, amp))
FONT_EN = '/home/user/font/WireframechLine-Regular.otf'; FONT_ZH = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
def caption(img, t):
    # small lower-left caption test: fades in 0.3-0.6 s; English in the custom font, CJK in WenQuanYi Zen Hei
    al = max(0.0, min(1.0, (t - 0.3) / 0.3))
    if al <= 0: return img
    ov = Image.new('RGBA', img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    fe = ImageFont.truetype(FONT_EN, 46); fz = ImageFont.truetype(FONT_ZH, 40)
    x, y = 96, H - 210
    txt1, txt2 = 'HIGH-MOBILITY COMBAT', ' / 高機動戰鬥'
    w1 = d.textlength(txt1, font=fe)
    d.rectangle([x - 18, y - 12, x + w1 + d.textlength(txt2, font=fz) + 22, y + 62], fill=(4, 18, 20, int(150 * al)))
    d.rectangle([x - 18, y - 12, x - 12, y + 62], fill=(127, 245, 224, int(255 * al)))
    for ox, oy in ((2, 2),): d.text((x + ox, y + oy), txt1, font=fe, fill=(0, 0, 0, int(160 * al)))
    d.text((x, y), txt1, font=fe, fill=(127, 245, 224, int(255 * al)))
    d.text((x + w1 + 2, y + 6), txt2, font=fz, fill=(235, 255, 250, int(255 * al)))
    return Image.alpha_composite(img.convert('RGBA'), ov).convert('RGB')
ow, oh = (1080, 1920) if a.vertical else (W, H)
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{ow}x{oh}', '-r', str(a.fps), '-i', '-',
                       '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', a.out], stdin=subprocess.PIPE)
cache = {}
for n, (i, s, dx, dy) in enumerate(seq):
    im = Image.open(frames[i]).convert('RGB')
    if s != 1.0 or dx or dy:
        cw, ch = W / s, H / s; cx, cy = W / 2 - dx / s, H / 2 - dy / s
        im = im.transform((W, H), Image.EXTENT, (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2), Image.BICUBIC)
    if a.caption: im = caption(im, n / a.fps)
    if a.vertical:
        cw = round(H * 9 / 16); x0 = (W - cw) // 2; im = im.crop((x0, 0, x0 + cw, H)).resize((ow, oh), Image.LANCZOS)
    ff.stdin.write(im.tobytes())
ff.stdin.close(); ff.wait()
print(json.dumps({'out': a.out, 'frames_out': len(seq), 'seconds': round(len(seq) / a.fps, 2), 'fired': fired, 'dead': dead, 'impact': impact, 'end': end}))
