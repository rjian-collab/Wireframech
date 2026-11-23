#!/usr/bin/env python3
"""產生預覽圖：python make_preview.py  (需先執行 generate_font.py)"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
BG = (8, 12, 20)
CYAN = (90, 235, 255)
WHITE = (240, 248, 255)
DIM = (70, 100, 120)

SAMPLES = ["WIREFRAMECH", "ONLINE 1V1 PVP NOW LIVE", "MANTIS SCYTHE",
           "PLAY FREE IN YOUR BROWSER", "V4.5", "WIREFRAMECH.VERCEL.APP"]
CHARSET = ["ABCDEFGHIJKLM", "NOPQRSTUVWXYZ", "0123456789 °", ".,:;!?'\"`-_/\\|",
           "()[]{}+=&#@%*<>~^$", "× · • ● – — → ← ↑ ↓ ▶"]
CONFUSE = "0O 1I 5S 8B 2Z 6G"


def font(w, size):
    return ImageFont.truetype(os.path.join(HERE, f"WireframechLine-{w}.ttf"), size)


def text(d, xy, s, f, fill, spacing=0):
    if spacing == 0:
        d.text(xy, s, font=f, fill=fill)
        return
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=f, fill=fill)
        x += f.getlength(ch) + spacing


def sheet(path):
    W, H = 1800, 1740
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    lab = font("Regular", 22)
    y = 30
    for w, col in (("Thin", WHITE), ("Regular", CYAN)):
        text(d, (40, y), f"WIREFRAMECH LINE {w.upper()} — GLYPH SET", lab, DIM)
        y += 50
        f = font(w, 76)
        for row in CHARSET:
            text(d, (40, y), row, f, col, spacing=18)
            y += 104
        text(d, (40, y), "lowercase -> " + "abcdefghijklm", font(w, 44), DIM)
        y += 70
        text(d, (40, y), "CONFUSABLES  " + CONFUSE, font(w, 60), col)
        y += 110
    im.save(path)


def samples(path):
    W, H = 1800, 1740
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    lab = font("Regular", 20)
    y = 30
    for w, col in (("Regular", WHITE), ("Thin", CYAN)):
        text(d, (40, y), f"{w.upper()} — LARGE", lab, DIM)
        y += 40
        for s, sz in zip(SAMPLES, (120, 64, 80, 58, 110, 60)):
            text(d, (40, y), s, font(w, sz), col)
            y += int(sz * 1.25)
        y += 20
    # phone-like small sizes, both weights
    for w, col in (("Regular", WHITE), ("Thin", CYAN)):
        text(d, (40, y), f"{w.upper()} — 24px / 18px (PHONE)", lab, DIM)
        y += 34
        for sz in (24, 18):
            x = 40
            for s in SAMPLES:
                text(d, (x, y), s, font(w, sz), col)
                x += font(w, sz).getlength(s) + 40
                if x > W - 400:
                    x = 40
                    y += int(sz * 1.6)
            y += int(sz * 1.8)
    im.save(path)


def glow_layer(size, draw_fn, color, radius_list=((22, 0.9), (8, 1.0), (2, 0.8))):
    mask = Image.new("L", size, 0)
    draw_fn(ImageDraw.Draw(mask))
    out = Image.new("RGB", size, (0, 0, 0))
    for r, a in radius_list:
        b = mask.filter(ImageFilter.GaussianBlur(r)).point(lambda v: min(255, int(v * a * 1.6)))
        out = ImageChops.add(out, Image.merge("RGB", [b.point(lambda v, c=c: v * c // 255) for c in color]))
    core = Image.merge("RGB", [mask.point(lambda v, c=c: v * c // 255) for c in (255, 255, 255)])
    return ImageChops.lighter(out, core)


def trailer(path):
    W, H = 1920, 1080
    im = Image.new("RGB", (W, H), (4, 7, 14))
    d = ImageDraw.Draw(im)
    # 背景網格 (HUD)
    for x in range(0, W, 60):
        d.line([(x, 0), (x, H)], fill=(12, 22, 34), width=1)
    for y in range(0, H, 60):
        d.line([(0, y), (W, y)], fill=(12, 22, 34), width=1)

    def fn(dd):
        f1 = font("Regular", 190)
        s = "WIREFRAMECH"
        w = f1.getlength(s)
        dd.text(((W - w) / 2, 150), s, font=f1, fill=255)
        f2 = font("Thin", 70)
        s = "ONLINE 1V1 PVP NOW LIVE"
        dd.text(((W - f2.getlength(s)) / 2, 420), s, font=f2, fill=255)
        f3 = font("Regular", 96)
        s = "MANTIS SCYTHE"
        dd.text(((W - f3.getlength(s)) / 2, 560), s, font=f3, fill=255)
        f4 = font("Thin", 54)
        s = "▶ PLAY FREE IN YOUR BROWSER  ·  V4.5"
        dd.text(((W - f4.getlength(s)) / 2, 760), s, font=f4, fill=255)
        f5 = font("Regular", 46)
        s = "WIREFRAMECH.VERCEL.APP →"
        dd.text(((W - f5.getlength(s)) / 2, 900), s, font=f5, fill=255)
    g = glow_layer((W, H), fn, (40, 200, 255))
    im = ImageChops.add(im, g)
    im.save(path)


def phone(path):
    """手機直式 (9:16) 縮圖模擬：1080x1920 縮到 360 寬。"""
    W, H = 1080, 1920
    im = Image.new("RGB", (W, H), (4, 7, 14))

    def fn(dd):
        y = 300
        for s, sz, w in (("WIREFRAMECH", 120, "Regular"), ("ONLINE 1V1 PVP", 80, "Regular"),
                         ("NOW LIVE", 110, "Regular"), ("MANTIS SCYTHE", 72, "Thin"),
                         ("PLAY FREE IN", 64, "Thin"), ("YOUR BROWSER", 64, "Thin"), ("V4.5", 120, "Regular"),
                         ("WIREFRAMECH.VERCEL.APP", 52, "Regular")):
            f = font(w, sz)
            dd.text(((W - f.getlength(s)) / 2, y), s, font=f, fill=255)
            y += int(sz * 1.55)
    g = glow_layer((W, H), fn, (40, 200, 255), ((16, 0.9), (5, 1.0)))
    im = ImageChops.add(im, g).resize((360, 640), Image.LANCZOS)
    im.save(path)


if __name__ == "__main__":
    out = os.path.join(HERE, "preview")
    os.makedirs(out, exist_ok=True)
    sheet(os.path.join(out, "preview_glyphs.png"))
    samples(os.path.join(out, "preview_samples.png"))
    trailer(os.path.join(out, "preview_trailer_glow.png"))
    phone(os.path.join(out, "preview_phone_360px.png"))
    print("saved to", out)
