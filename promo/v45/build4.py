import os, sys, subprocess
from PIL import Image, ImageDraw, ImageFont
import build as B1, build2 as B2
from build import W, H, cap, noise_layer, over, flash, zoom, ease
ROOT = B1.ROOT; OUT = ROOT + '/edit4'; os.makedirs(OUT, exist_ok=True); SY = B2.SY
CAPS = [(16, 80, 'Two pilots. One duel.'), (190, 236, 'Their laser finds you first.'), (246, 320, 'Lead the shot. Land it.'),
        (330, 416, 'Hook the rocks. Ride the arc.'), (426, 488, 'Mantis Blade. One hit. Done.'), (570, 670, 'Online 1v1 is here.'),
        (680, 738, 'Keyboard and mouse? Ready.'), (748, 836, 'Parry. Counter. Strike back.'), (846, 922, 'Repaint anytime in the Hangar.'),
        (928, 978, 'Three new skins.'), (988, 1048, 'Your record, on your card.'), (1054, 1104, 'Now in four languages.'), (1122, 1200, 'Brand-new look.')]
def add_caption(im, gi):
    for a, b, t in CAPS:
        if a <= gi < b:
            k = min(1, (gi - a) / 4, (b - gi) / 4); L = B1.caption_layer(t)
            if k < 1: L = L.copy(); L.putalpha(L.getchannel('A').point(lambda v: int(v * k)))
            return over(im, L)
    return im
def sc_blade():
    fr = []
    for i, ci in enumerate(range(14, 112)):
        im = cap('B2', ci)
        if i < 4: im = over(Image.blend(cap('S1', 83), im, i / 4), noise_layer(1 - i / 5, 900 + i))
        if 44 <= ci < 47: im = flash(im, [0.55, 0.3, 0.12][ci - 44], (255, 200, 170))
        if ci >= 96: im = B2.red_bloom(zoom(im, 1 + 0.25 * ease((ci - 96) / 16)), ease((ci - 98) / 14))
        fr.append(im)
    return fr
def sc_aim():
    imp = SY['A4_imp']; seq = list(range(6, imp + 1)) + [imp] * 9 + list(range(imp + 1, 81)); fr = []
    for k, ci in enumerate(seq):
        im = cap('A4', ci); j = k - (imp - 6)
        if 0 <= j < 10: im = zoom(im, 1.0 + 0.12 * ease((j + 1) / 3), cx=SY['A4_cx'], cy=SY['A4_cy'])
        if j in (0, 1): im = flash(im, 0.35 if j == 0 else 0.15, (255, 240, 220))
        fr.append(im)
    return fr
def sc_duel():
    fx = ImageFont.truetype(B1.FX, 30); fm = ImageFont.truetype(B1.FM, 20); M = B1.MINT
    lines = [(20, 16, 'VOLT', fx, (255, 255, 255, 255)), (122, 24, 'VS', fm, M + (255,)), (164, 16, 'Kestrel_09', fx, (255, 200, 205, 255)), (20, 66, 'LIVE  /  ONLINE DUEL', fm, M + (230,))]
    fr = []
    for i in range(112):
        im = cap('S7', 4 + i); t = (i - 2) / 30
        if t >= 0: im = over(im, B1.window_layer((44, 60, 444, 166), 'ONLINE 1v1', lines, t))
        fr.append(im)
    return fr
def sc_end():
    f = B2.sc_end(); return f[:82] + f[100:116]
from PIL import ImageFilter
MINT = B1.MINT; INK = B1.INK
def key_layer(i):
    fK = ImageFont.truetype(B1.FX, 22); fS = ImageFont.truetype(B1.FX, 15)
    on = {'W': i < 10, 'A': 46 <= i < 62, 'S': False, 'D': 16 <= i < 34, 'Q': False, 'E': False, 'SPACE': 28 <= i < 33, 'SHIFT': 50 <= i < 60, 'LMB': 42 <= i < 47, 'RMB': False}
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L); x0, y0, u = 846, 360, 54
    def key(lab, x, y, w=1, k=None):
        a = on.get(k or lab); r = (x, y, x + u * w - 6, y + u - 6)
        d.rectangle(r, fill=MINT + (235,) if a else (6, 20, 22, 150), outline=MINT + (220,), width=1)
        d.text(((r[0] + r[2]) // 2, (r[1] + r[3]) // 2), lab, font=fK if len(lab) < 3 else fS, fill=INK if a else (235, 250, 246), anchor='mm')
    key('Q', x0, y0); key('W', x0 + u, y0); key('E', x0 + 2 * u, y0)
    key('A', x0, y0 + u); key('S', x0 + u, y0 + u); key('D', x0 + 2 * u, y0 + u)
    key('SHIFT', x0 - u - 10, y0 + 2 * u, 1.6, 'SHIFT'); key('SPACE', x0 + u * 0.7, y0 + 2 * u, 2.6, 'SPACE')
    mx, my = x0 + 3 * u + 22, y0 + 6   # mouse
    d.rounded_rectangle((mx, my, mx + 76, my + 118), 34, fill=(6, 20, 22, 150), outline=MINT + (220,), width=1)
    d.line((mx + 38, my, mx + 38, my + 46), fill=MINT + (200,), width=1); d.line((mx, my + 46, mx + 76, my + 46), fill=MINT + (200,), width=1)
    if on['LMB']: d.pieslice((mx + 1, my + 1, mx + 75, my + 90), 180, 270, fill=MINT + (235,))
    d.text((mx + 38, my + 82), 'AIM', font=fS, fill=(235, 250, 246), anchor='mm')
    d.rectangle((x0 - u - 10, y0 - 34, x0 - u + 190, y0 - 10), fill=MINT + (255,)); d.text((x0 - u, y0 - 22), 'PC  KEYBOARD + MOUSE', font=fS, fill=INK, anchor='lm')
    return L
def sc_pc():
    fr = []
    for i in range(70):
        im = cap('P1', i)
        if i < 3: im = over(im, noise_layer(0.8 - i * 0.25, 1700 + i))
        sx, sy = B1.wo_open((i - 2) / 30, 0.5)
        if sx > 0:
            K = key_layer(i); bb = (700, 310, 1260, 560); P = K.crop(bb); nw, nh = max(1, int(P.width * sx)), max(2, int(P.height * sy))
            P = P.resize((nw, nh)) if sy > 0.02 else Image.new('RGBA', (nw, 2), MINT + (255,))
            Q = Image.new('RGBA', (W, H), (0, 0, 0, 0)); Q.alpha_composite(P, ((bb[0] + bb[2]) // 2 - nw // 2, (bb[1] + bb[3]) // 2 - nh // 2)); im = over(im, Q)
        fr.append(im)
    return fr
def sc_profile():
    fr = []
    for i in range(70):
        im = cap('PF', i + 1)
        if i < 14: im = zoom(im, 2.1 - 0.15 * i / 14, cx=230, cy=110)
        else: im = zoom(im, 1.15 + 0.12 * ease((i - 14) / 8) + 0.03 * (i - 14) / 56, cx=642, cy=420)
        if i == 14: im = flash(im, 0.3, B1.MINT)
        fr.append(im)
    return fr
LN = ['繁體中文', '日本語', '한국어', 'English']
def sc_lang():
    fN = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 40, index=0); fr = []
    for i in range(56):
        im = zoom(cap('LG', i + 1), 1.18, cx=640, cy=430); k = i // 14; j = i % 14
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L); tw = d.textbbox((0, 0), LN[k], font=fN)[2]
        cx = W // 2; d.rectangle((cx - tw // 2 - 26, 22, cx + tw // 2 + 26, 84), fill=(6, 20, 22, 200), outline=MINT + (230,), width=2)
        d.text((cx, 52), LN[k], font=fN, fill=(255, 255, 255), anchor='mm')
        for q in range(4): d.rectangle((cx - 45 + q * 24, 92, cx - 27 + q * 24, 97), fill=MINT + (255 if q == k else 70,))
        if j < 3: im = over(im, noise_layer(0.6 - j * 0.2, 1900 + i))
        fr.append(over(im, L))
    return fr
SCENES = [('w01', lambda: B1.sc1()[:84], 84), ('w02', sc_blade, 98), ('w03', lambda: B2.sc_laser()[:56], 56), ('w04', sc_aim, 84),
          ('w05', lambda: [cap('S3', i) for i in range(98)], 98), ('w06', lambda: [cap('S5', i) for i in range(70)], 70), ('w07', B2.sc_sever, 70),
          ('w08', sc_duel, 112), ('n09', sc_pc, 70), ('w09', lambda: B1.sc8()[:98], 98), ('w10', lambda: B1.sc9()[:84], 84), ('w11', B2.sc_skins, 56),
          ('n13', sc_profile, 70), ('n14', sc_lang, 56), ('w12', sc_end, 98)]
ONLY = sys.argv[1].split(',') if len(sys.argv) > 1 else None
G0 = {}; g = 0
for n, _, L in SCENES: G0[n] = g; g += L
assert g == 1204
def encode(name, frames):
    d = f'{OUT}/{name}_f'; os.makedirs(d, exist_ok=True)
    for i, im in enumerate(frames): im.save(f'{d}/{i:04d}.jpg', quality=94)
    tmp, dst = f'{OUT}/{name}.tmp.mp4', f'{OUT}/{name}.mp4'
    r = subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', f'{d}/%04d.jpg', '-frames:v', str(len(frames)), '-vf', B1.VF + ',format=yuv420p',
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '30', tmp])
    if r.returncode: raise SystemExit('encode failed ' + name)
    os.replace(tmp, dst); print('encoded', name, len(frames), flush=True)
for n, fn, L in SCENES:
    if ONLY and n not in ONLY: continue
    fr = fn(); assert len(fr) == L, (n, len(fr)); encode(n, [add_caption(im, G0[n] + i) for i, im in enumerate(fr)])
open(f'{OUT}/list.txt', 'w').write(''.join(f"file '{n}.mp4'\n" for n, _, _ in SCENES))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/list.txt', '-c', 'copy', f'{OUT}/video.tmp.mp4'], check=True); os.replace(f'{OUT}/video.tmp.mp4', f'{OUT}/video.mp4')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{OUT}/video.mp4', '-i', f'{ROOT}/music4.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', f'{ROOT}/wireframech_v45_promo_v4.tmp.mp4'], check=True)
os.replace(f'{ROOT}/wireframech_v45_promo_v4.tmp.mp4', f'{ROOT}/wireframech_v45_promo_v4.mp4'); print('final ok')
