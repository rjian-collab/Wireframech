import sys, glob, os
from PIL import Image, ImageDraw
import os; TD=os.environ.get('TD','test'); names = sys.argv[2:]; out = sys.argv[1]; tiles=[]
for n in names:
    fs = sorted(glob.glob(f'{TD}/{n}/*.jpg'))
    for f in fs: tiles.append((n+' '+os.path.basename(f)[:4], f))
cols=4; w,h=320,180; rows=(len(tiles)+cols-1)//cols
S=Image.new('RGB',(cols*w,rows*h))
for i,(lab,f) in enumerate(tiles):
    im=Image.open(f).resize((w,h)); d=ImageDraw.Draw(im); d.text((4,4),lab,fill=(255,255,0)); S.paste(im,((i%cols)*w,(i//cols)*h))
S.save(out,quality=85); print(len(tiles))
