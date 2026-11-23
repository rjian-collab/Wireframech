import os, subprocess, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from build import SHOTS, cap_index, fx_frame, glow_text, FB2, FM, CYAN
CAP = 'full'; OUT = 'reels'; os.makedirs(OUT, exist_ok=True)
W, H = 1080, 1920
CJK = lambda sz, b=False: ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-' + ('Bold' if b else 'Black') + '.ttc', sz, index=3)
VY = 560                     # top of the 16:9 video band (1080x608)
# top captions (global frame ranges)
CAPS = [(0, 129, '我自己做了一款\n機甲遊戲'), (129, 309, '用鋼索\n在空中甩來甩去'), (309, 412, '擺盪・飛越・開火'),
        (412, 566, '跳起來開砲'), (566, 720, '一砲炸裂'), (720, 771, '手機點開就能玩')]
def caption_for(g):
    for a, b, t in CAPS:
        if a <= g < b: return t, g - a, b - g
    return None, 0, 0

def compose(frame, g):
    bg = frame.resize((W // 8, H // 8)).filter(ImageFilter.GaussianBlur(3))
    s = max(W / frame.width, H / frame.height); bw, bh = int(frame.width * s), int(frame.height * s)
    bg = frame.resize((bw // 10, bh // 10)).filter(ImageFilter.GaussianBlur(2)).resize((bw, bh), Image.BILINEAR)
    x = (bw - W) // 2; bg = bg.crop((x, 0, x + W, H)); bg = ImageEnhance.Brightness(bg).enhance(0.42).convert('RGBA')
    fg = frame.resize((1422, 800), Image.LANCZOS).crop((171, 0, 171 + W, 800)); bg.paste(fg, (0, VY))
    d = ImageDraw.Draw(bg)
    d.rectangle((0, VY - 4, W, VY - 1), fill=CYAN + (255,)); d.rectangle((0, VY + 800, W, VY + 803), fill=CYAN + (255,))
    # header
    d.text((W // 2, 215), 'WIREFRAMECH 鋼弦機兵', font=CJK(44, True), fill=(160, 235, 222, 255), anchor='mm')
    t, since, left = caption_for(g)
    if t:
        k = min(1, since / 5); k = 1 - (1 - k) ** 3; a = int(255 * min(1, left / 3) * k)
        f = CJK(92); y0 = 418 + int((1 - k) * 25)
        L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); dl = ImageDraw.Draw(L)
        dl.multiline_text((W // 2 + 4, y0 + 6), t, font=f, fill=(0, 0, 0, int(a * 0.6)), anchor='mm', align='center', spacing=14)
        L = L.filter(ImageFilter.GaussianBlur(6)); ImageDraw.Draw(L).multiline_text((W // 2, y0), t, font=f, fill=(255, 255, 255, a), anchor='mm', align='center', spacing=14)
        bg.alpha_composite(L)
    # footer
    d = ImageDraw.Draw(bg)
    d.text((W // 2, 1425), '免費・免安裝・手機就能玩', font=CJK(48, True), fill=(255, 255, 255, 235), anchor='mm')
    d.text((W // 2, 1490), 'wireframech.vercel.app', font=ImageFont.truetype(FM, 40), fill=(160, 235, 222, 235), anchor='mm')
    return bg.convert('RGB')

def encode(name, d, n):
    tmp = f'{OUT}/{name}.tmp.mp4'
    r = subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', '30', '-i', f'{d}/%04d.jpg', '-frames:v', str(n),
                        '-vf', 'eq=contrast=1.05:saturation=1.12', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', '30', tmp])
    assert r.returncode == 0; os.replace(tmp, f'{OUT}/{name}.mp4')

g = 0
for name, n, segs, eff, text in SHOTS:
    d = f'{OUT}/{name}_f'; os.makedirs(d, exist_ok=True)
    for i in range(n):
        im = Image.open(f'{CAP}/{name}/{cap_index(i, segs):04d}.jpg').convert('RGB')
        compose(fx_frame(im, i, eff, None), g + i).save(f'{d}/{i:04d}.jpg', quality=90)
    encode(name, d, n); g += n; print(name, flush=True)

# vertical cards
last = sorted(os.listdir(f'{CAP}/S8'))[-1]
src = Image.open(f'{CAP}/S8/{last}').convert('RGB')
s = H / src.height; bgc = src.resize((int(src.width * s), H)); x = (bgc.width - W) // 2; bgc = bgc.crop((x, 0, x + W, H))
bgc = Image.blend(ImageEnhance.Brightness(bgc.filter(ImageFilter.GaussianBlur(16))).enhance(0.38), Image.new('RGB', (W, H), (8, 20, 30)), 0.35)
d = f'{OUT}/logo_f'; os.makedirs(d, exist_ok=True)
for i in range(39):
    sc = 1.25 - 0.25 * min(1, i / 4) ** 0.7
    C = bgc.convert('RGBA'); glow_text(C, (W // 2, 860), 'WIREFRAMECH', ImageFont.truetype(FB2, int(124 * sc)), r=14)
    k = min(1, max(0, (i - 5) / 8))
    if k: ImageDraw.Draw(C).text((W // 2, 1000), '鋼弦機兵', font=CJK(96), fill=(255, 255, 255, int(255 * k)), anchor='mm')
    fx_frame(C.convert('RGB'), i, dict(flash=[0], shake=[0]), None).save(f'{d}/{i:04d}.jpg', quality=90)
encode('logo', d, 39)
d = f'{OUT}/end_f'; os.makedirs(d, exist_ok=True)
for i in range(28):
    k = min(1, i / 6); k = 1 - (1 - k) ** 3; a = int(255 * k)
    C = bgc.convert('RGBA'); glow_text(C, (W // 2, 560), 'WIREFRAMECH', ImageFont.truetype(FB2, 110), r=12)
    dr = ImageDraw.Draw(C)
    dr.text((W // 2, 690), '鋼弦機兵', font=CJK(80), fill=(255, 255, 255, 255), anchor='mm')
    dr.text((W // 2, 900 + int((1 - k) * 30)), '免費・免安裝', font=CJK(100), fill=(255, 255, 255, a), anchor='mm')
    dr.text((W // 2, 1020), '手機・平板・電腦都能玩', font=CJK(52, True), fill=(205, 238, 232, a), anchor='mm')
    dr.rectangle((W // 2 - int(260 * k), 1090, W // 2 + int(260 * k), 1098), fill=CYAN + (255,))
    dr.text((W // 2, 1180), 'wireframech.vercel.app', font=ImageFont.truetype(FM, 56), fill=(255, 255, 255, a), anchor='mm')
    dr.text((W // 2, 1290), '網址在頻道首頁', font=CJK(46, True), fill=CYAN + (a,), anchor='mm')
    C.convert('RGB').save(f'{d}/{i:04d}.jpg', quality=90)
encode('end', d, 28)
order = [s[0] for s in SHOTS] + ['logo', 'end']
open(f'{OUT}/list.txt', 'w').write(''.join(f"file '{n}.mp4'\n" for n in order))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', f'{OUT}/list.txt', '-c', 'copy', f'{OUT}/v.tmp.mp4'], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f'{OUT}/v.tmp.mp4', '-i', 'music.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-shortest', 'reels.tmp.mp4'], check=True)
os.replace('reels.tmp.mp4', 'wireframech_shorts.mp4'); print('ok')
