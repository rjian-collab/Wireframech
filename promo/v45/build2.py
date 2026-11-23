import os, sys, json, subprocess, math
import numpy as np, qrcode
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import build as B1
from build import (W, H, MINT, ALERT, INK, FB, FBK, FM, FX, cap, noise_layer, over, flash, zoom, shake, ease, wo_open, wo_noise,
                   screen_open, window_layer, draw_icon, VF)
# v2 edit: 14 frames per beat (128.57 BPM). Section starts are multiples of 14.
ROOT = B1.ROOT; OUT = ROOT + '/edit2'; os.makedirs(OUT, exist_ok=True)
SY = json.load(open(ROOT + '/edit_sync.json'))

CAPS = [(14, 80, 'Two pilots. One duel.'), (88, 128, 'One cut is all it takes.'), (206, 264, 'Their laser finds you first.'),
        (276, 362, 'Lead the shot. Land it.'), (482, 558, 'Online 1v1 is here.'), (566, 640, 'Parry. Counter. Strike back.'),
        (650, 726, 'Repaint anytime in the Hangar.'), (732, 782, 'Three new skins.'), (800, 896, 'One scan to your next duel.')]
def add_caption(im, gi):
    for a, b, text in CAPS:
        if a <= gi < b:
            k = min(1, (gi - a) / 4, (b - gi) / 4); L = B1.caption_layer(text)
            if k < 1: L = L.copy(); L.putalpha(L.getchannel('A').point(lambda v: int(v * k)))
            return over(im, L)
    return im

def red_bloom(im, k):   # match-cut glue: push into the red glow
    if k <= 0: return im
    g = im.filter(ImageFilter.GaussianBlur(8 + 30 * k)); r = Image.new('RGB', (W, H), (255, 70, 40))
    return Image.blend(Image.blend(im, g, min(1, k)), r, 0.55 * k)

def sc_versus(): return [screen_open(cap('S1', i), i, 0, 0.6) for i in range(84)]
def sc_blade():
    fr = []
    for i in range(112):
        im = cap('B2', i)
        if i < 4: im = over(Image.blend(cap('S1', 83), im, i / 4), noise_layer(1 - i / 5, 900 + i))   # static burst match-cut
        if 44 <= i < 47: im = flash(im, [0.55, 0.3, 0.12][i - 44], (255, 200, 170))                     # blade touches the hull
        if i >= 96: im = red_bloom(zoom(im, 1 + 0.25 * ease((i - 96) / 16)), ease((i - 98) / 14))
        fr.append(im)
    return fr
def find_red(im):
    a = np.asarray(im).astype(int); m = (a[..., 0] > 200) & (a[..., 1] < 140) & (a[..., 2] < 120)
    if m.sum() < 6: return None
    ys, xs = np.nonzero(m); return int(np.median(xs)), int(np.median(ys))
def sc_laser():
    fr = []; f = ImageFont.truetype(FX, 18); last = None
    for i in range(70):
        im = cap('L3', i)
        if i < 8: im = red_bloom(im, 1 - ease(i / 8))
        p = find_red(im) or last; last = p
        if p and i >= 6:
            L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L); locked = i >= 32
            s = 70 if locked else 70 + int(40 * abs(math.sin(i * 0.5))); x, y = p; c = ALERT + (230,)
            for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                d.line((x + sx * s, y + sy * s, x + sx * (s - 22), y + sy * s), fill=c, width=3); d.line((x + sx * s, y + sy * s, x + sx * s, y + sy * (s - 22)), fill=c, width=3)
            if locked and (i - 32) % 6 < 4:
                tx = x - s; ty = y - s - 30; d.rectangle((tx, ty, tx + 130, ty + 24), fill=ALERT + (255,)); d.text((tx + 10, ty + 12), 'LOCKED ON', font=f, fill=INK, anchor='lm')
            im = over(im, L.filter(ImageFilter.GaussianBlur(1)))
            im = over(im, L)
        fr.append(im)
    return fr
def sc_aim():
    fr = []; imp = SY['A4_imp']; seq = list(range(0, imp + 1)) + [imp] * 9 + list(range(imp + 1, 89))
    for k, ci in enumerate(seq[:98]):
        im = cap('A4', ci)
        if imp <= k < imp + 10: im = zoom(im, 1.0 + 0.12 * ease((k - imp + 1) / 3), cx=SY['A4_cx'], cy=SY['A4_cy'])
        if k in (imp, imp + 1): im = flash(im, 0.35 if k == imp else 0.15, (255, 240, 220))
        fr.append(im)
    return fr
def sc_swing(): return [cap('S3', 46 + i) for i in range(42)]
def sc_sever():
    fr = []; c = SY['S6_cut'] + 1; seq = list(range(0, c + 1)) + [c] * 9 + list(range(c + 1, 66))
    for k, ci in enumerate(seq[:70]):
        im = cap('S6', ci)
        if c <= k < c + 10: im = zoom(im, 1.06, cx=SY['S6_cx'], cy=SY['S6_cy'])
        if k == c: im = flash(im, 0.45)
        fr.append(shake(im, k, c + 9, 9))
    return fr
def sc_duel():
    fr = []; fx = ImageFont.truetype(FX, 30); fm = ImageFont.truetype(FM, 20)
    lines = [(20, 16, 'VOLT', fx, (255, 255, 255, 255)), (122, 24, 'VS', fm, MINT + (255,)), (164, 16, 'Kestrel_09', fx, (255, 200, 205, 255)), (20, 66, 'LIVE  /  ONLINE DUEL', fm, MINT + (230,))]
    for i in range(84):
        im = cap('S7', 24 + i)
        if i < 3: im = over(im, noise_layer(0.8 - i * 0.25, 1500 + i))
        t = (i - 2) / 30
        if t >= 0: im = over(im, window_layer((44, 60, 444, 166), 'ONLINE 1v1', lines, t))
        fr.append(im)
    return fr
def sc_parry():
    fr = []; fz = SY['S8_freeze']; seq = list(range(10, fz + 1)) + [fz] * (84 - (fz - 10 + 1))
    for k, ci in enumerate(seq):
        im = cap('S8', ci)
        if 35 <= ci < 38 and seq[k - 1] != ci: im = flash(im, [0.9, 0.5, 0.2][ci - 35])
        if ci == SY['S8_block']: im = flash(im, 0.3, (255, 230, 200))
        if ci == fz:
            u = min(1, (k - (fz - 10)) / 4); im = zoom(im, 1 + 0.05 * ease(u)); im = ImageEnhance.Color(im).enhance(1 - 0.35 * u)
            if k == fz - 10: im = flash(im, 0.5)
        fr.append(shake(im, ci, SY['S8_parry'], 10))
    return fr
def sc_hangar():
    fr = []; last = ImageEnhance.Color(zoom(cap('S8', SY['S8_freeze']), 1.05)).enhance(0.65)
    for i in range(84):
        im = cap('H9', i + 1)
        if i < 7:
            u = ease(i / 7); prev = ImageEnhance.Brightness(last).enhance(1 - 0.6 * u)
            m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rectangle((int(W * (1 - u)), 0, W, H), fill=255); prev.paste(im, (0, 0), m); im = prev
            if i < 6: ImageDraw.Draw(im).line((int(W * (1 - u)), 0, int(W * (1 - u)), H), fill=MINT, width=3)
        for a, b, cx, cy in SY['H9_zoom']:
            if a <= i < b: u = min(ease((i - a) / 3), ease((b - i) / 3)); im = zoom(im, 1 + 0.38 * u, cx=cx, cy=cy)
        fr.append(im)
    return fr
def sc_skins():
    names = ['GOLD  ×  BLACK', 'CRIMSON  ×  INDIGO', 'OLIVE  ×  PALE GREEN']; cols = [(255, 194, 74), (150, 110, 255), (200, 240, 168)]
    sw = W // 3; ims = [cap('S10', k) for k in (1, 2, 3)]; f = ImageFont.truetype(FX, 21); fr = []
    for i in range(56):
        base = Image.new('RGB', (W, H), (4, 10, 14)); z = 1 + 0.06 * i / 56
        for k in range(3):
            strip = zoom(ims[k], z, cx=SY['S10_cx'], cy=SY['S10_cy']).crop(((W - sw) // 2, 0, (W - sw) // 2 + sw, H))
            on = i >= k * 14; t = (i - k * 14) / 30
            if not on: strip = ImageEnhance.Brightness(ImageEnhance.Color(strip).enhance(0.2)).enhance(0.3)
            elif t < 0.25: strip = ImageEnhance.Brightness(strip).enhance(1 + 0.5 * (1 - t / 0.25))
            elif i < 42 and i >= k * 14 + 14: strip = ImageEnhance.Brightness(strip).enhance(0.78)
            base.paste(strip, (k * sw + (2 if k else 0), 0))
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
        for k in range(3):
            on = i >= k * 14; c = cols[k] if on else (90, 100, 105); cx = k * sw + sw // 2; tw = f.getbbox(names[k])[2] + 28
            d.rectangle((cx - tw // 2, 92, cx + tw // 2, 124), fill=c + (255,) if on else (30, 36, 40, 230)); d.text((cx, 108), names[k], font=f, fill=INK if on else (150, 160, 165), anchor='mm')
            if k: d.line((k * sw, 0, k * sw, H), fill=MINT + (160,), width=2)
            if on and (i - k * 14) < 8: a = int(255 * (1 - (i - k * 14) / 8)); d.rectangle((k * sw + 3, 3, (k + 1) * sw - 4, H - 4), outline=c + (a,), width=4)
        fr.append(over(base, L))
    return fr
def qr_image(size):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=4); q.add_data('https://wireframech.vercel.app'); q.make(fit=True)
    im = q.make_image(fill_color='black', back_color='white').convert('RGB'); n = im.size[0]; bx = size // n   # integer module size: crisp modules
    out = Image.new('RGB', (size, size), (255, 255, 255)); out.paste(im.resize((n * bx, n * bx), Image.NEAREST), ((size - n * bx) // 2, (size - n * bx) // 2)); return out
def sc_end():
    bg = cap('S10', 0).filter(ImageFilter.GaussianBlur(9)); bg = ImageEnhance.Brightness(bg).enhance(0.32); bg = Image.blend(bg, Image.new('RGB', (W, H), (4, 14, 18)), 0.35)
    fL = ImageFont.truetype(FBK, 84); fS = ImageFont.truetype(FM, 26); fI = ImageFont.truetype(FM, 16); fQ = ImageFont.truetype(FX, 22)
    QS = 300; QR = qr_image(QS); qx, qy = 860, 92            # 300 px = 42% of frame height, quiet zone built in
    box = (70, 150, 760, 290); fr = []
    for i in range(116):
        t = i / 30 * 1.35; im = bg.copy()
        sx, sy = wo_open(t, 0.6); nz, bgk = wo_noise(t, 0.6)
        if sx > 0:
            P = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dp = ImageDraw.Draw(P)
            dp.rectangle(box, fill=(6, 20, 22, 110), outline=MINT + (220,), width=2)
            gl = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(gl).text(((box[0] + box[2]) // 2, (box[1] + box[3]) // 2), 'WIREFRAMECH', font=fL, anchor='mm', fill=MINT + (255,))
            P.alpha_composite(gl.filter(ImageFilter.GaussianBlur(12))); ImageDraw.Draw(P).text(((box[0] + box[2]) // 2, (box[1] + box[3]) // 2), 'WIREFRAMECH', font=fL, anchor='mm', fill=(255, 255, 255, 255))
            m = Image.new('L', (W, H), 0); ImageDraw.Draw(m).rectangle(box, fill=255)
            if bgk > 0: P.paste(Image.new('RGBA', (W, H), MINT + (int(255 * bgk),)), (0, 0), m)
            if nz > 0:
                Nl = noise_layer(nz, 700 + i); Nl.putalpha(Image.fromarray(np.minimum(np.array(Nl.getchannel('A')), np.array(m)))); P.alpha_composite(Nl)
            bw, bh = box[2] - box[0], box[3] - box[1]; nw, nh = max(1, int(bw * sx)), max(3, int(bh * sy))
            crop = P.crop((box[0] - 2, box[1] - 2, box[2] + 3, box[3] + 3)).resize((nw + 5, nh + 5), Image.BILINEAR)
            if sy < 0.02: crop = Image.new('RGBA', (nw, 3), MINT + (255,))
            Q = Image.new('RGBA', (W, H), (0, 0, 0, 0)); Q.alpha_composite(crop, ((box[0] + box[2]) // 2 - crop.width // 2, (box[1] + box[3]) // 2 - crop.height // 2)); im = over(im, Q)
        k = ease((i - 14) / 8)
        if k > 0:
            L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L); a = int(255 * k); cx = (box[0] + box[2]) // 2
            d.rectangle((box[0], box[1] - 24, box[0] + 70, box[1]), fill=MINT + (a,)); d.text((box[0] + 35, box[1] - 12), 'v4.5', font=fI, fill=INK + (a,), anchor='mm')
            d.text((cx, 336), 'itch.io   |   wireframech.vercel.app', font=fS, fill=(235, 250, 246, a), anchor='mm')
            k2 = ease((i - 20) / 8); a2 = int(255 * k2)
            for j, (kind, lab) in enumerate([('tablet', 'iPad'), ('phone', 'Phone'), ('pc', 'PC')]):
                ix = cx + (j - 1) * 120; draw_icon(d, kind, ix, 420, MINT + (a2,)); d.text((ix, 470), lab, font=fI, fill=(200, 230, 225, a2), anchor='mm')
            im = over(im, L)
        kq = ease((i - 10) / 10)
        if kq > 0:   # QR: white card (quiet zone included), dark modules, label
            card = Image.new('RGB', (QS + 24, QS + 64), (255, 255, 255)); card.paste(QR, (12, 12))
            ImageDraw.Draw(card).text(((QS + 24) // 2, QS + 38), 'Scan to play', font=fQ, fill=(6, 18, 22), anchor='mm')
            glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).rectangle((qx - 6, qy - 6, qx + QS + 30, qy + QS + 70), outline=MINT + (255,), width=3)
            im = over(im, glow.filter(ImageFilter.GaussianBlur(5))); im = over(im, glow)
            yy = qy + int((1 - kq) * 20); cm = Image.new('L', card.size, int(255 * kq)); im.paste(card, (qx, yy), cm)
        if i == 0: im = flash(im, 0.7)
        if i >= 100:
            u = (i - 100) / 15; im = over(im, noise_layer(min(1, u * 1.1) * 0.8, 1300 + i)); im = ImageEnhance.Brightness(im).enhance(1 - 0.92 * u ** 1.4)
        fr.append(im)
    return fr

SCENES = [('v01', sc_versus, 0, 84), ('v02', sc_blade, 84, 112), ('v03', sc_laser, 196, 70), ('v04', sc_aim, 266, 98), ('v05', sc_swing, 364, 42),
          ('v06', sc_sever, 406, 70), ('v07', sc_duel, 476, 84), ('v08', sc_parry, 560, 84), ('v09', sc_hangar, 644, 84), ('v10', sc_skins, 728, 56), ('v11', sc_end, 784, 116)]
assert sum(s[3] for s in SCENES) == 900 and all(SCENES[i][2] + SCENES[i][3] == SCENES[i + 1][2] for i in range(len(SCENES) - 1))
def encode(name, frames):
    d = f'{OUT}/{name}_f'; os.makedirs(d, exist_ok=True)
    for i, im in enumerate(frames): im.save(f'{d}/{i:04d}.jpg', quality=94)
    tmp, dst = f'{OUT}/{name}.tmp.mp4', f'{OUT}/{name}.mp4'
    r = subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', f'{d}/%04d.jpg', '-frames:v', str(len(frames)), '-vf', VF + ',format=yuv420p',
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '30', tmp])
    if r.returncode: raise SystemExit('encode failed ' + name)
    os.replace(tmp, dst); print('encoded', name, len(frames), flush=True)
def frames(name):
    _, fn, g0, n = [s for s in SCENES if s[0] == name][0]; fr = fn(); assert len(fr) == n, (name, len(fr)); return [add_caption(im, g0 + i) for i, im in enumerate(fr)]
if __name__ == '__main__':
    if '--still' in sys.argv:
        os.makedirs(ROOT + '/stills2', exist_ok=True)
        for gs in sys.argv[sys.argv.index('--still') + 1].split(','):
            gi = int(gs); name, fn, g0, n = [s for s in SCENES if s[2] <= gi][-1]; add_caption(fn()[gi - g0], gi).save(f'{ROOT}/stills2/{gi:03d}.jpg', quality=90)
        sys.exit()
    sel = sys.argv[1] if len(sys.argv) > 1 else 'all'; names = [s[0] for s in SCENES] if sel == 'all' else sel.split(',')
    for n in names: encode(n, frames(n))
    order = [s[0] for s in SCENES]
    if sel == 'all':
        open(f'{OUT}/list.txt', 'w').write(''.join(f"file '{n}.mp4'\n" for n in order))
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/list.txt', '-c', 'copy', f'{OUT}/video.tmp.mp4'], check=True); os.replace(f'{OUT}/video.tmp.mp4', f'{OUT}/video.mp4')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{OUT}/video.mp4', '-i', f'{ROOT}/music2.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', f'{ROOT}/wireframech_v45_promo_v2.tmp.mp4'], check=True)
        os.replace(f'{ROOT}/wireframech_v45_promo_v2.tmp.mp4', f'{ROOT}/wireframech_v45_promo_v2.mp4'); print('final ok')
