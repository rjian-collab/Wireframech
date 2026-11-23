#!/usr/bin/env python3
"""Contact sheet: python3 sheet_fp.py FRAMES_DIR OUT.jpg f1,f2,... [cols] [labels]"""
import sys
from PIL import Image, ImageDraw, ImageFont
src, out, fl = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(',')]
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 4
labels = sys.argv[5].split('|') if len(sys.argv) > 5 else None
W, H = 640, 360; rows = (len(fl) + cols - 1) // cols
im = Image.new('RGB', (cols * W, rows * H), (10, 12, 14)); fnt = ImageFont.truetype('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 20)
for i, f in enumerate(fl):
    t = Image.open(f'{src}/{f:04d}.png').convert('RGB').resize((W, H), Image.LANCZOS); d = ImageDraw.Draw(t)
    lab = f'f{f}' + (f'  {labels[i]}' if labels and i < len(labels) else '')
    d.rectangle([0, 0, d.textlength(lab, font=fnt) + 12, 28], fill=(0, 0, 0)); d.text((6, 3), lab, font=fnt, fill=(127, 245, 224))
    im.paste(t, ((i % cols) * W, (i // cols) * H))
im.save(out, quality=88)
