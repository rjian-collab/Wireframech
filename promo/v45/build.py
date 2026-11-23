import os, sys, json, subprocess, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
# usage: build.py [scene,scene..|all] [--still N]  (global frame N -> still_N.jpg, no encode)
ROOT = '/home/claude/promo/v45'; CAP = ROOT + '/cap'; OUT = ROOT + '/edit'; os.makedirs(OUT, exist_ok=True)
W, H = 1280, 720
FB = '/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf'
FBK = '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'
FM = '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'
FX = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
MINT = (142, 243, 218); ALERT = (255, 84, 102); INK = (6, 18, 22)
SY = json.load(open(ROOT + '/edit_sync.json'))   # capture-derived frame numbers
rng = np.random.default_rng(3)

def cap(shot, i): return Image.open(f'{CAP}/{shot}/{i:04d}.jpg').convert('RGB')

# ---------- shared FX ----------
def noise_layer(alpha, seed, streak=True):
    r = np.random.default_rng(seed); v = r.random((H // 2, W // 2))
    a = np.clip(v * v * 255 * alpha * (1.8 if streak else 1), 0, 255)
    if streak:
        rows = r.random(H // 2) < 0.07; a[rows] = np.clip(a[rows] * 2.2, 0, 255)
    col = (225 + v * 30).astype(np.uint8); A = Image.fromarray(a.astype(np.uint8)).resize((W, H), Image.NEAREST)
    C = Image.fromarray(col).resize((W, H), Image.NEAREST); L = Image.merge('RGBA', (C, C, C, A))
    sl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(sl)
    for y in range(0, H, 3): d.line((0, y, W, y), fill=(0, 0, 0, int(90 * alpha)))
    L.alpha_composite(sl); return L

def over(im, L): im = im.convert('RGBA'); im.alpha_composite(L); return im.convert('RGB')
def flash(im, k, col=(255, 252, 245)): return Image.blend(im, Image.new('RGB', (W, H), col), max(0, min(1, k)))
def zoom(im, z, cx=W / 2, cy=H / 2, dx=0, dy=0):
    if z <= 1.0001 and not dx and not dy: return im
    cw, ch = W / z, H / z; x0 = min(max(cx - cw / 2 + dx, 0), W - cw); y0 = min(max(cy - ch / 2 + dy, 0), H - ch)
    return im.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BICUBIC)
def shake(im, i, a, amp=10):
    if not (a <= i < a + 8): return im
    q = 1 - (i - a) / 8; return zoom(im, 1.04, dx=amp * math.sin(i * 2.9) * q, dy=amp * 0.7 * math.cos(i * 3.7) * q)
def ease(t): t = max(0, min(1, t)); return 1 - (1 - t) ** 3

def wo_open(t, dur=0.55):
    """game's window-open: returns (sx, sy) scale of window at time t seconds (line 0->32%, expand ->100%)."""
    u = t / dur
    if u <= 0: return 0, 0.006
    if u < 0.32: return ease(u / 0.32), 0.006
    if u < 1: return 1, 0.006 + 0.994 * ease((u - 0.32) / 0.68)
    return 1, 1
def wo_noise(t, dur=0.55):
    u = t / (dur * 1.6)
    if u < 0: return 0, 0
    if u < 0.3: return 1, 1
    if u < 0.42: return 0.9, 0.22
    if u < 0.65: return 0.6, 0.08
    if u < 1: return 0.6 * (1 - (u - 0.65) / 0.35), 0.08 * (1 - (u - 0.65) / 0.35)
    return 0, 0

def screen_open(im, i, start=0, dur=0.75):
    """full-frame version of the window-open effect: black -> glowing mint line -> expands vertically, with static."""
    t = (i - start) / 30
    if t >= dur * 1.6: return im
    sx, sy = wo_open(t, dur); nz, bg = wo_noise(t, dur)
    base = Image.new('RGB', (W, H), (0, 0, 0))
    w, h = int(W * sx), max(2, int(H * sy)); x0, y0 = (W - w) // 2, (H - h) // 2
    if w > 0:
        reg = im.crop((x0, y0, x0 + w, y0 + h))
        if bg > 0: reg = Image.blend(reg, Image.new('RGB', reg.size, MINT), min(1, bg * 0.9))
        base.paste(reg, (x0, y0))
        G = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(G)
        for yy in (y0, y0 + h - 1): d.line((x0, yy, x0 + w, yy), fill=MINT + (255,), width=3)
        Gb = G.filter(ImageFilter.GaussianBlur(6)); base = over(base, Gb); base = over(base, Gb); base = over(base, G)
    if nz > 0:
        Nl = noise_layer(nz, 100 + i); m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rectangle((x0, y0, x0 + w, y0 + h), fill=255)
        Nl.putalpha(Image.fromarray(np.minimum(np.array(Nl.getchannel('A')), np.array(m)))); base = over(base, Nl)
    if 0.44 * dur * 1.5 < t < 0.66 * dur * 1.5 and int(t * 60) % 2: base = ImageEnhance.Brightness(base).enhance(0.6)
    return base

# ---------- captions ----------
CAPS = [(16, 86, 'Two pilots. One duel.'), (128, 218, 'Swing. Aim. Strike.'), (306, 370, 'Mantis Blade. One hit. Done.'),
        (462, 566, 'Online 1v1 is here.'), (576, 668, 'Parry. Counter. Strike back.'), (681, 760, 'Repaint anytime in the Hangar.'),
        (769, 822, 'Three new skins.'), (845, 895, 'Brand-new look. Play free.')]
_capcache = {}
def caption_layer(text):
    if text in _capcache: return _capcache[text]
    size = 64
    while True:
        f = ImageFont.truetype(FB, size); bb = f.getbbox(text)
        if bb[2] - bb[0] <= 1120 or size <= 60: break
        size -= 2
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    cy = int(H * 0.835)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).text((W // 2, cy + 3), text, font=f, anchor='mm', fill=(0, 0, 0, 150), stroke_width=7, stroke_fill=(0, 0, 0, 150))
    L.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    d.text((W // 2, cy), text, font=f, anchor='mm', fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=(8, 16, 20, 255))
    _capcache[text] = L; return L
def add_caption(im, g):
    for a, b, text in CAPS:
        if a <= g < b:
            k = min(1, (g - a) / 4, (b - g) / 4); L = caption_layer(text)
            if k < 1: L = L.copy(); L.putalpha(L.getchannel('A').point(lambda v: int(v * k)))
            if a <= g < a + 4: L = L.transform(L.size, Image.AFFINE, (1, 0, 0, 0, 1, -int((1 - k) * 14)))
            return over(im, L)
    return im

# ---------- thin-line window (game style) ----------
def window_layer(box, tag, lines, t, col=MINT, dur=0.55):
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0; sx, sy = wo_open(t, dur); nz, bg = wo_noise(t, dur)
    P = Image.new('RGBA', (w + 2, h + 2), (0, 0, 0, 0)); d = ImageDraw.Draw(P)
    d.rectangle((0, 0, w, h), fill=(6, 20, 22, 120), outline=col + (200,), width=1)
    for lx, ly, s, font, c in lines: d.text((lx, ly), s, font=font, fill=c)
    if bg > 0: P = Image.alpha_composite(P, Image.new('RGBA', P.size, col + (int(255 * bg),)))
    if nz > 0:
        Nl = noise_layer(nz, 500 + int(t * 30), False).crop((0, 0, w + 2, h + 2)); P = Image.alpha_composite(P, Nl)
    if sx <= 0: return Image.new('RGBA', (W, H), (0, 0, 0, 0))
    nw, nh = max(1, int((w + 2) * sx)), max(2, int((h + 2) * sy))
    if sy < 0.02: P = Image.new('RGBA', (nw, 2), col + (255,))
    else: P = P.resize((nw, nh), Image.BILINEAR)
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    L.alpha_composite(P, (cx - nw // 2, cy - nh // 2))
    if tag and sy > 0.5:
        f = ImageFont.truetype(FX, 18); tb = f.getbbox(tag); tw = tb[2] - tb[0] + 24
        d2 = ImageDraw.Draw(L); d2.rectangle((x0, y0 - 26, x0 + tw, y0), fill=col + (255,)); d2.text((x0 + 12, y0 - 13), tag, font=f, fill=INK, anchor='lm')
    glow = L.filter(ImageFilter.GaussianBlur(3)); out = Image.new('RGBA', (W, H), (0, 0, 0, 0)); out.alpha_composite(glow); out.alpha_composite(L); return out

# ---------- grade + encode ----------
VF = "eq=contrast=1.05:saturation=1.12,vignette=PI/5.5"
def encode(name, frames):
    d = f'{OUT}/{name}_f'; os.makedirs(d, exist_ok=True)
    for i, im in enumerate(frames): im.save(f'{d}/{i:04d}.jpg', quality=94)
    tmp, dst = f'{OUT}/{name}.tmp.mp4', f'{OUT}/{name}.mp4'
    r = subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', f'{d}/%04d.jpg', '-frames:v', str(len(frames)), '-vf', VF + ',format=yuv420p',
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '30', tmp])
    if r.returncode != 0: raise SystemExit('encode failed ' + name)
    os.replace(tmp, dst); print('encoded', name, len(frames), flush=True)

# ---------- scenes: each returns list of frames (without captions); g0 = global start frame ----------
def sc1():
    fr = []
    for i in range(90):
        im = cap('S1', i); im = screen_open(im, i, 0, 0.6); fr.append(im)
    return fr
def sc2():
    fr = []; xf = SY['S2_x']
    for i in range(30):
        im = zoom(cap('S2', i), 1.12 + 0.06 * i / 30, cx=690, cy=400)
        if i < 4: im = over(Image.blend(cap('S1', 89), im, i / 4), noise_layer(1 - i / 5, 900 + i))
        if xf <= i < xf + 4: im = flash(im, [0.85, 0.55, 0.3, 0.12][i - xf])
        im = shake(im, i, xf, 12); fr.append(im)
    return fr
def sc3(): return [cap('S3', i) for i in range(105)]
def sc4():
    fr = []; imp = SY['S4_imp']   # capture frame where the shell lands (boom first visible)
    seq = list(range(0, imp + 1)) + [imp] * 9 + list(range(imp + 1, 66))
    for k, ci in enumerate(seq):
        im = cap('S4', ci)
        if imp <= k < imp + 10: im = zoom(im, 1.0 + 0.10 * ease((k - imp + 1) / 3), cx=SY['S4_cx'], cy=SY['S4_cy'])
        if k in (imp, imp + 1): im = flash(im, 0.35 if k == imp else 0.15, (255, 240, 220))
        fr.append(im)
    return fr[:75]
def sc5(): return [cap('S5', i) for i in range(75)]
def sc6():
    fr = []; c = SY['S6_cut'] + 1
    seq = list(range(0, c + 1)) + [c] * 9 + list(range(c + 1, 66))
    for k, ci in enumerate(seq):
        im = cap('S6', ci)
        if c <= k < c + 10: im = zoom(im, 1.06, cx=SY['S6_cx'], cy=SY['S6_cy'])
        if k == c: im = flash(im, 0.45)
        fr.append(shake(im, k, c + 9, 9))
    return fr[:75]
def sc7():
    fr = []; fx = ImageFont.truetype(FX, 30); fm = ImageFont.truetype(FM, 20)
    lines = [(20, 16, 'VOLT', fx, (255, 255, 255, 255)), (122, 24, 'VS', fm, MINT + (255,)), (164, 16, 'Kestrel_09', fx, (255, 200, 205, 255)),
             (20, 66, 'LIVE  ·  ONLINE DUEL', fm, MINT + (230,))]
    for i in range(120):
        im = cap('S7', i); t = (i - 2) / 30
        if t >= 0: im = over(im, window_layer((44, 60, 444, 166), 'ONLINE 1v1', lines, t))
        fr.append(im)
    return fr
def sc8():
    fr = []; fz = SY['S8_freeze']; cutf = 35
    seq = list(range(0, fz + 1)) + [fz] * (105 - fz - 1)
    for k, ci in enumerate(seq):
        im = cap('S8', ci)
        if cutf <= k < cutf + 3: im = flash(im, [0.9, 0.5, 0.2][k - cutf])
        if k == SY['S8_block']: im = flash(im, 0.25, (255, 230, 200))
        if k >= fz:
            u = min(1, (k - fz) / 4); im = zoom(im, 1 + 0.05 * ease(u)); im = ImageEnhance.Color(im).enhance(1 - 0.35 * u)
            if k == fz: im = flash(im, 0.5)
        fr.append(shake(im, k, SY['S8_parry'], 10))
    return fr
def sc9():
    fr = []; last = cap('S8', SY['S8_freeze']); last = ImageEnhance.Color(zoom(last, 1.05)).enhance(0.65)
    Z = SY['S9_zoom']   # [(start, end, cx, cy)]
    for i in range(90):
        im = cap('S9', i + 1)
        if i < 7:
            u = ease(i / 7); prev = ImageEnhance.Brightness(last).enhance(1 - 0.6 * u)
            m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rectangle((int(W * (1 - u)), 0, W, H), fill=255); prev.paste(im, (0, 0), m)
            prev = over(prev, Image.new('RGBA', (W, H), MINT + (0,))); im = prev
            if i < 6: ImageDraw.Draw(im).line((int(W * (1 - u)), 0, int(W * (1 - u)), H), fill=MINT, width=3)
        for a, b, cx, cy in Z:
            if a <= i < b:
                u = min(ease((i - a) / 3), ease((b - i) / 3)); im = zoom(im, 1 + 0.38 * u, cx=cx, cy=cy)
        fr.append(im)
    return fr
def sc10():
    names = ['GOLD  ×  BLACK', 'CRIMSON  ×  INDIGO', 'OLIVE  ×  PALE GREEN']; cols = [(255, 194, 74), (150, 110, 255), (200, 240, 168)]
    cx = SY['S10_cx']; sw = W // 3; ims = [cap('S10', k) for k in (1, 2, 3)]
    f = ImageFont.truetype(FX, 20); fr = []
    for i in range(60):
        base = Image.new('RGB', (W, H), (4, 10, 14)); z = 1 + 0.06 * i / 60
        for k in range(3):
            src = zoom(ims[k], z * SY['S10_z'], cx=cx, cy=SY['S10_cy'])
            strip = src.crop(((W - sw) // 2, 0, (W - sw) // 2 + sw, H))
            on = i >= k * 15; t = (i - k * 15) / 30
            if not on: strip = ImageEnhance.Brightness(ImageEnhance.Color(strip).enhance(0.2)).enhance(0.3)
            elif t < 0.25: strip = ImageEnhance.Brightness(strip).enhance(1 + 0.6 * (1 - t / 0.25))
            if on and i >= 45: pass
            elif on and k * 15 + 15 <= i < 45: strip = ImageEnhance.Brightness(strip).enhance(0.75)
            base.paste(strip, (k * sw + (2 if k else 0), 0))
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        for k in range(3):
            on = i >= k * 15; c = cols[k] if on else (90, 100, 105)
            x0 = k * sw + 30; d.rectangle((x0, 34, x0 + f.getbbox(names[k])[2] + 24, 62), fill=c + (255,) if on else (30, 36, 40, 220))
            d.text((x0 + 12, 48), names[k], font=f, fill=INK if on else (150, 160, 165), anchor='lm')
            if k: d.line((k * sw, 0, k * sw, H), fill=MINT + (160,), width=2)
            if on and (i - k * 15) < 8:
                a = int(255 * (1 - (i - k * 15) / 8)); d.rectangle((k * sw + 3, 3, (k + 1) * sw - 4, H - 4), outline=c + (a,), width=4)
        fr.append(over(base, L))
    return fr
def draw_icon(d, kind, cx, cy, c, wdt=3):
    if kind == 'tablet': d.rounded_rectangle((cx - 26, cy - 34, cx + 26, cy + 34), 6, outline=c, width=wdt); d.ellipse((cx - 3, cy + 25, cx + 3, cy + 31), outline=c, width=2)
    if kind == 'phone': d.rounded_rectangle((cx - 16, cy - 30, cx + 16, cy + 30), 6, outline=c, width=wdt); d.line((cx - 5, cy - 24, cx + 5, cy - 24), fill=c, width=2)
    if kind == 'pc': d.rectangle((cx - 40, cy - 30, cx + 40, cy + 18), outline=c, width=wdt); d.line((cx, cy + 18, cx, cy + 30), fill=c, width=wdt); d.line((cx - 18, cy + 31, cx + 18, cy + 31), fill=c, width=wdt)
def sc11():
    bg = cap('S10', 0).filter(ImageFilter.GaussianBlur(9)); bg = ImageEnhance.Brightness(bg).enhance(0.32)
    bg = Image.blend(bg, Image.new('RGB', (W, H), (4, 14, 18)), 0.35)
    fL = ImageFont.truetype(FBK, 104); fS = ImageFont.truetype(FM, 30); fI = ImageFont.truetype(FM, 17)
    fr = []
    for i in range(75):
        t = i / 30 * 1.35; im = bg.copy()
        logo = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(logo)
        dl.text((W // 2, 228), 'WIREFRAMECH', font=fL, anchor='mm', fill=(255, 255, 255, 255))
        gl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).text((W // 2, 228), 'WIREFRAMECH', font=fL, anchor='mm', fill=MINT + (255,))
        gl = gl.filter(ImageFilter.GaussianBlur(14))
        sx, sy = wo_open(t, 0.6); nz, bgk = wo_noise(t, 0.6)
        box = (W // 2 - 420, 150, W // 2 + 420, 306)
        if sx > 0:
            P = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dp = ImageDraw.Draw(P)
            dp.rectangle(box, fill=(6, 20, 22, 110), outline=MINT + (220,), width=2)
            for (ax, ay, bx, by) in [(box[0] + 8, box[1] + 8, 1, 1), (box[2] - 8, box[3] - 8, -1, -1)]:
                dp.line((ax, ay, ax + 22 * bx, ay), fill=MINT + (255,), width=2); dp.line((ax, ay, ax, ay + 22 * by), fill=MINT + (255,), width=2)
            P.alpha_composite(gl); P.alpha_composite(logo)
            if bgk > 0: tint = Image.new('RGBA', (W, H), MINT + (int(255 * bgk),)); m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rectangle(box, fill=255); P.paste(tint, (0, 0), m)
            if nz > 0:
                Nl = noise_layer(nz, 700 + i); m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rectangle(box, fill=255)
                Nl.putalpha(Image.fromarray(np.minimum(np.array(Nl.getchannel('A')), np.array(m)))); P.alpha_composite(Nl)
            cy0 = (box[1] + box[3]) // 2; bw, bh = box[2] - box[0], box[3] - box[1]
            nw, nh = max(1, int(bw * sx)), max(3, int(bh * sy))
            crop = P.crop((box[0] - 2, box[1] - 2, box[2] + 3, box[3] + 3)).resize((nw + 5, nh + 5), Image.BILINEAR)
            if sy < 0.02: crop = Image.new('RGBA', (nw, 3), MINT + (255,))
            Q = Image.new('RGBA', (W, H), (0, 0, 0, 0)); Q.alpha_composite(crop, (W // 2 - crop.width // 2, cy0 - crop.height // 2))
            Q.alpha_composite(Q.filter(ImageFilter.GaussianBlur(4)) if sy < 0.05 else Image.new('RGBA', (W, H), (0, 0, 0, 0)))
            im = over(im, Q)
        k = ease((i - 16) / 8)
        if k > 0:
            L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L); a = int(255 * k)
            d.tag = 'v4.5'
            d.rectangle((box[0], box[1] - 24, box[0] + 92, box[1]), fill=MINT + (a,)); d.text((box[0] + 46, box[1] - 12), 'v4.5', font=fI, fill=INK + (a,), anchor='mm')
            d.text((W // 2, 352 + int((1 - k) * 12)), 'itch.io   |   wireframech.vercel.app', font=fS, fill=(235, 250, 246, a), anchor='mm')
            k2 = ease((i - 22) / 8); a2 = int(255 * k2)
            for j, (kind, lab) in enumerate([('tablet', 'iPad'), ('phone', 'Phone'), ('pc', 'PC')]):
                cx = W // 2 + (j - 1) * 130; draw_icon(d, kind, cx, 432, MINT + (a2,)); d.text((cx, 485), lab, font=fI, fill=(200, 230, 225, a2), anchor='mm')
            im = over(im, L)
        if i == 0: im = flash(im, 0.7)
        if i >= 60:
            u = (i - 60) / 14; im = over(im, noise_layer(min(1, u * 1.1), 1300 + i)); im = ImageEnhance.Brightness(im).enhance(1 - 0.92 * u ** 1.3)
        fr.append(im)
    return fr

SCENES = [('s01', sc1, 0), ('s02', sc2, 90), ('s03', sc3, 120), ('s04', sc4, 225), ('s05', sc5, 300), ('s06', sc6, 375), ('s07', sc7, 450),
          ('s08', sc8, 570), ('s09', sc9, 675), ('s10', sc10, 765), ('s11', sc11, 825)]
LEN = {'s01': 90, 's02': 30, 's03': 105, 's04': 75, 's05': 75, 's06': 75, 's07': 120, 's08': 105, 's09': 90, 's10': 60, 's11': 75}

def scene_frames(name):
    fn, g0 = [(f, g) for n, f, g in SCENES if n == name][0]
    fr = fn(); assert len(fr) == LEN[name], (name, len(fr))
    return [add_caption(im, g0 + i) for i, im in enumerate(fr)]

if __name__ == '__main__':
    if '--still' in sys.argv:
        for gs in sys.argv[sys.argv.index('--still') + 1].split(','):
            g = int(gs); name, fn, g0 = [s for s in SCENES if s[2] <= g][-1]
            fr = fn(); add_caption(fr[g - g0], g).save(f'{ROOT}/still_{g}.jpg', quality=92); print('still', g)
        sys.exit()
    sel = sys.argv[1] if len(sys.argv) > 1 else 'all'
    names = [n for n, _, _ in SCENES] if sel == 'all' else sel.split(',')
    for n in names: encode(n, scene_frames(n))
    order = [n for n, _, _ in SCENES]
    if all(os.path.exists(f'{OUT}/{n}.mp4') for n in order) and sel == 'all':
        open(f'{OUT}/list.txt', 'w').write(''.join(f"file '{n}.mp4'\n" for n in order))
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/list.txt', '-c', 'copy', f'{OUT}/video.tmp.mp4'], check=True)
        os.replace(f'{OUT}/video.tmp.mp4', f'{OUT}/video.mp4')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{OUT}/video.mp4', '-i', f'{ROOT}/music.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', f'{ROOT}/wireframech_v45_promo.tmp.mp4'], check=True)
        os.replace(f'{ROOT}/wireframech_v45_promo.tmp.mp4', f'{ROOT}/wireframech_v45_promo.mp4'); print('final ok')
