import os, sys, json, subprocess, math, shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
CAP = sys.argv[1] if len(sys.argv) > 1 else 'full'
OUT = 'edit'; os.makedirs(OUT, exist_ok=True)
W, H = 1280, 720
FB = '/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf'
FB2 = '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'
FM = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
CYAN = (61, 224, 200)

# (name, out_frames, segments[(out_start, cap_start, factor)], effects, text)
SHOTS = [
 ('S2', 129, [(0, 0, 2), (77, 39, 1)], dict(zoom=[103], shake=[103]), None),
 ('S1A', 77, [(0, 0, 1)], {}, ('FOUR LEGS. STEEL WIRES.', 13, 74, 'top')),
 ('S4A', 51, [(0, 0, 1), (20, 20, 2)], dict(zoom=[20], flash=[24], shake=[24]), None),
 ('S5A', 52, [(0, 0, 1)], dict(shakeS=[13, 21, 29]), None),
 ('S3A', 103, [(0, 0, 1), (90, 90, 2)], {}, ('SWING. FLY. SHOOT.', 13, 86)),
 ('S7A', 51, [(0, 0, 1)], dict(zoom=[0], flash=[0, 2], shake=[2]), None),
 ('S1B', 26, [(0, 0, 1)], {}, None),
 ('S6A', 25, [(0, 0, 1), (13, 13, 2)], dict(flash=[13], shake=[13]), None),
 ('S5B', 52, [(0, 0, 1)], dict(shakeS=[0, 8, 16, 24, 32]), None),
 ('S4B', 25, [(0, 0, 1)], dict(zoom=[13], flash=[15], shake=[15]), None),
 ('S3B', 26, [(0, 0, 1)], {}, None),
 ('S7B', 26, [(0, 0, 1)], dict(zoom=[13], flash=[15], shake=[15]), None),
 ('S6B', 26, [(0, 0, 1), (13, 13, 2)], dict(flash=[13], shake=[13]), None),
 ('S1C', 25, [(0, 0, 1)], {}, None),
 ('S7C', 26, [(0, 0, 1), (13, 13, 2)], dict(zoom=[0], flash=[2], shake=[2]), None),
 ('S8', 51, [(0, 0, 2)], {}, ('NO INSTALL. JUST CLICK.', 3, 48)),
]
def cap_index(i, segs):
    seg = [s for s in segs if s[0] <= i][-1]
    return seg[1] + (i - seg[0]) // seg[2]

def text_layer(line, k, size=74, top=False):
    """k: 0..1 appear progress, fade handled by caller. Returns RGBA overlay."""
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    f = ImageFont.truetype(FB, size); bb = d.textbbox((0, 0), line, font=f); tw, th = bb[2] - bb[0], bb[3] - bb[1]
    x = (W - tw) // 2 + int((1 - k) * 60); y = int(H * (0.16 if top else 0.76)) - (0 if top else th)
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sh); ds.text((x + 4, y + 5), line, font=f, fill=(0, 0, 0, 170))
    sh = sh.filter(ImageFilter.GaussianBlur(5)); L.alpha_composite(sh)
    d.text((x, y), line, font=f, fill=(255, 255, 255, 255))
    bw = int(tw * min(1, k * 1.2)); d.rectangle((x, y + th + 26, x + bw, y + th + 34), fill=CYAN + (255,))
    return L

def fx_frame(im, i, eff, text):
    # crash zoom (hold to cut)
    z = 1.0
    for a in eff.get('zoom', []):
        if i >= a: z = max(z, 1 + 0.12 * min(1, (i - a) / 6) ** 0.6)
    # shakes
    dx = dy = 0.0
    for a in eff.get('shake', []):
        if a <= i < a + 8: q = 1 - (i - a) / 8; dx += 16 * math.sin(i * 2.9) * q; dy += 11 * math.cos(i * 3.7) * q
    for a in eff.get('shakeS', []):
        if a <= i < a + 6: q = 1 - (i - a) / 6; dx += 5 * math.sin(i * 3.3) * q; dy += 4 * math.cos(i * 4.1) * q
    if z > 1 or dx or dy:
        zz = max(z, 1.06 if (dx or dy) else 1)
        cw, ch = W / zz, H / zz; cx = W / 2 + dx; cy = H / 2 + dy
        im = im.crop((cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)).resize((W, H), Image.BICUBIC)
    for a in eff.get('flash', []):
        if a <= i < a + 3: im = Image.blend(im, Image.new('RGB', (W, H), (255, 252, 240)), [0.75, 0.45, 0.2][i - a])
    if text:
        line, t0, t1 = text[:3]; top = len(text) > 3
        if t0 <= i < t1:
            k = min(1, (i - t0) / 5); k = 1 - (1 - k) ** 3
            fade = min(1, (t1 - i) / 4)
            L = text_layer(line, k, top=top)
            if fade < 1: L.putalpha(L.getchannel('A').point(lambda v: int(v * fade)))
            im = im.convert('RGBA'); im.alpha_composite(L); im = im.convert('RGB')
    return im

VF = "eq=contrast=1.06:saturation=1.14:brightness=-0.01,colorbalance=bs=0.04:bm=0.02:rh=0.03,vignette=PI/5"
def encode(name, frames_dir, n):
    tmp = f'{OUT}/{name}.tmp.mp4'; dst = f'{OUT}/{name}.mp4'
    r = subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', f'{frames_dir}/%04d.jpg', '-frames:v', str(n), '-vf', VF,
                        '-c:v', 'libx264', '-crf', '18', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', '30', tmp])
    if r.returncode == 0: os.replace(tmp, dst)
    else: raise SystemExit('encode failed ' + name)

def build_shot(name, n, segs, eff, text):
    d = f'{OUT}/{name}_f'; os.makedirs(d, exist_ok=True)
    for i in range(n):
        ci = cap_index(i, segs); src = f'{CAP}/{name}/{ci:04d}.jpg'
        im = Image.open(src).convert('RGB')
        if im.size != (W, H): im = im.resize((W, H), Image.BICUBIC)
        fx_frame(im, i, eff, text).save(f'{d}/{i:04d}.jpg', quality=92)
    encode(name, d, n)

def card_bg():
    last = sorted(os.listdir(f'{CAP}/S8'))[-1]
    bg = Image.open(f'{CAP}/S8/{last}').convert('RGB').resize((W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(10)); bg = ImageEnhance.Brightness(bg).enhance(0.38)
    ov = Image.new('RGB', (W, H), (8, 20, 30)); return Image.blend(bg, ov, 0.35)

def glow_text(base, xy, s, font, fill=(255, 255, 255), glow=CYAN, r=14, anchor='mm'):
    L = Image.new('RGBA', base.size, (0, 0, 0, 0)); ImageDraw.Draw(L).text(xy, s, font=font, fill=glow + (255,), anchor=anchor)
    L = L.filter(ImageFilter.GaussianBlur(r)); base.alpha_composite(L); base.alpha_composite(L)
    ImageDraw.Draw(base).text(xy, s, font=font, fill=fill + (255,), anchor=anchor)

def build_cards():
    bg = card_bg()
    # logo slam: 39 frames
    d = f'{OUT}/logo_f'; os.makedirs(d, exist_ok=True)
    for i in range(39):
        s = 1.25 - 0.25 * min(1, i / 4) ** 0.7
        C = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        f = ImageFont.truetype(FB2, int(150 * s)); glow_text(C, (W // 2, H // 2 - 20), 'WIREFRAMECH', f)
        sub = ImageFont.truetype(FM, 30); k = min(1, max(0, (i - 6) / 8))
        if k > 0: ImageDraw.Draw(C).text((W // 2, H // 2 + 85), 'GRAPPLE-WIRE MECH COMBAT', font=sub, fill=(200, 235, 230, int(255 * k)), anchor='mm', spacing=4)
        im = bg.convert('RGBA'); im.alpha_composite(C); im = im.convert('RGB')
        fx_frame(im, i, dict(flash=[0], shake=[0]), None).save(f'{d}/{i:04d}.jpg', quality=92)
    encode('logo', d, 39)
    # end card: 28 frames
    d = f'{OUT}/end_f'; os.makedirs(d, exist_ok=True)
    for i in range(28):
        k = min(1, i / 6); k = 1 - (1 - k) ** 3
        C = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dr = ImageDraw.Draw(C)
        glow_text(C, (W // 2, 170), 'WIREFRAMECH', ImageFont.truetype(FB2, 84), r=10)
        a = int(255 * k)
        dr.text((W // 2, 330 + int((1 - k) * 30)), 'PLAY FREE IN YOUR BROWSER', font=ImageFont.truetype(FB, 64), fill=(255, 255, 255, a), anchor='mm')
        dr.rectangle((W // 2 - int(330 * k), 380, W // 2 + int(330 * k), 386), fill=CYAN + (255,))
        dr.text((W // 2, 450), 'chitanta-daisuki.itch.io/wireframech', font=ImageFont.truetype(FM, 34), fill=(225, 245, 240, a), anchor='mm')
        dr.text((W // 2, 500), 'wireframech.vercel.app', font=ImageFont.truetype(FM, 34), fill=(225, 245, 240, a), anchor='mm')
        k2 = min(1, max(0, (i - 3) / 6))
        dr.text((W // 2, 590), 'Phone, tablet, or PC.', font=ImageFont.truetype(FM, 28), fill=(160, 200, 195, int(255 * k2)), anchor='mm')
        im = bg.convert('RGBA'); im.alpha_composite(C); im.convert('RGB').save(f'{d}/{i:04d}.jpg', quality=92)
    encode('end', d, 28)

if __name__ == '__main__':
    only = sys.argv[2].split(',') if len(sys.argv) > 2 else None
    for name, n, segs, eff, text in SHOTS:
        if only and name not in only: continue
        build_shot(name, n, segs, eff, text); print('built', name, flush=True)
    if not only or 'cards' in only: build_cards(); print('cards', flush=True)
    order = [s[0] for s in SHOTS] + ['logo', 'end']
    if all(os.path.exists(f'{OUT}/{n}.mp4') for n in order):
        open(f'{OUT}/list.txt', 'w').write(''.join(f"file '{n}.mp4'\n" for n in order))
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/list.txt', '-c', 'copy', f'{OUT}/video.tmp.mp4'], check=True)
        os.replace(f'{OUT}/video.tmp.mp4', f'{OUT}/video.mp4')
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{OUT}/video.mp4', '-i', 'music.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', 'wireframech_promo.tmp.mp4'], check=True)
        os.replace('wireframech_promo.tmp.mp4', 'wireframech_promo.mp4'); print('final ok')
