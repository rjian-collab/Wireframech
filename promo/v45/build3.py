import os, sys, subprocess
from PIL import Image, ImageDraw, ImageFont
import build as B1, build2 as B2
from build import W, H, cap, noise_layer, over, flash, zoom, ease
ROOT = B1.ROOT; OUT = ROOT + '/edit3'; os.makedirs(OUT, exist_ok=True); SY = B2.SY
CAPS = [(16, 80, 'Two pilots. One duel.'), (190, 236, 'Their laser finds you first.'), (246, 320, 'Lead the shot. Land it.'),
        (330, 416, 'Hook the rocks. Ride the arc.'), (426, 488, 'Mantis Blade. One hit. Done.'), (570, 670, 'Online 1v1 is here.'),
        (678, 766, 'Parry. Counter. Strike back.'), (776, 852, 'Repaint anytime in the Hangar.'), (858, 908, 'Three new skins.'), (926, 1004, 'Brand-new look.')]
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
SCENES = [('w01', lambda: B1.sc1()[:84], 84), ('w02', sc_blade, 98), ('w03', lambda: B2.sc_laser()[:56], 56), ('w04', sc_aim, 84),
          ('w05', lambda: [cap('S3', i) for i in range(98)], 98), ('w06', lambda: [cap('S5', i) for i in range(70)], 70), ('w07', B2.sc_sever, 70),
          ('w08', sc_duel, 112), ('w09', lambda: B1.sc8()[:98], 98), ('w10', lambda: B1.sc9()[:84], 84), ('w11', B2.sc_skins, 56), ('w12', sc_end, 98)]
G0 = {}; g = 0
for n, _, L in SCENES: G0[n] = g; g += L
assert g == 1008
def encode(name, frames):
    d = f'{OUT}/{name}_f'; os.makedirs(d, exist_ok=True)
    for i, im in enumerate(frames): im.save(f'{d}/{i:04d}.jpg', quality=94)
    tmp, dst = f'{OUT}/{name}.tmp.mp4', f'{OUT}/{name}.mp4'
    r = subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', f'{d}/%04d.jpg', '-frames:v', str(len(frames)), '-vf', B1.VF + ',format=yuv420p',
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', '30', tmp])
    if r.returncode: raise SystemExit('encode failed ' + name)
    os.replace(tmp, dst); print('encoded', name, len(frames), flush=True)
for n, fn, L in SCENES:
    fr = fn(); assert len(fr) == L, (n, len(fr)); encode(n, [add_caption(im, G0[n] + i) for i, im in enumerate(fr)])
open(f'{OUT}/list.txt', 'w').write(''.join(f"file '{n}.mp4'\n" for n, _, _ in SCENES))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/list.txt', '-c', 'copy', f'{OUT}/video.tmp.mp4'], check=True); os.replace(f'{OUT}/video.tmp.mp4', f'{OUT}/video.mp4')
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{OUT}/video.mp4', '-i', f'{ROOT}/music3.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', f'{ROOT}/wireframech_v45_promo_v3.tmp.mp4'], check=True)
os.replace(f'{ROOT}/wireframech_v45_promo_v3.tmp.mp4', f'{ROOT}/wireframech_v45_promo_v3.mp4'); print('final ok')
