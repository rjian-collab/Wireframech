import sys, os
from PIL import Image, ImageDraw
# sheet.py out.jpg cols scale dir1 [dir2..]
out, cols, sc = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]); fs = []
for d in sys.argv[4:]: fs += [os.path.join(d, f) for f in sorted(os.listdir(d)) if f.endswith('.jpg')]
w, h = int(1280*sc), int(720*sc); rows = (len(fs)+cols-1)//cols
S = Image.new('RGB', (w*cols, h*rows))
for i, f in enumerate(fs):
    im = Image.open(f).resize((w, h)); ImageDraw.Draw(im).text((4, 2), f.split('/')[-2]+f.split('/')[-1][:4], fill=(255,255,0)); S.paste(im, ((i%cols)*w, (i//cols)*h))
S.save(out, quality=85); print(len(fs))
