"""Align photographed box surfaces to the approved Europe box landmarks.

Uses original pack artwork, not generated replacement packaging. The piecewise
coordinate map aligns the rim and base, and preserves texture and panel lettering.
Inputs are kept separately so repeated exports never compound resampling.
"""
import argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Left/right front-panel edges, rim at left/centre/right, and bottom edge.
LANDMARKS = {
    'eu-22': (110,1090,605,650,605,850),
    'pl-15': (126,1065,568,568,568,825),
    'de-20': (85,1110,653,656,653,855),
    'nl-18': (110,1088,611,616,611,850),
    'be-16': (110,1090,590,611,590,834),
    'it-16': (94,1100,530,530,530,830),
    'fr-15': (130,1068,610,617,610,835),
    'es-16': (152,1050,606,613,606,842),
    'se-18': (140,1055,585,605,585,835),
    'uk-classic': (108,1090,610,617,610,855),
    'sub-italy': (148,1053,553,555,553,818),
}

def render(src, dest, spec):
    import cv2
    import json
    l,r,tl,tc,tr,b=spec
    recipes=json.loads((Path(__file__).parent/'boxes.json').read_text())
    recipe=next(v for v in recipes if v['id']==src.stem)
    color=np.array(list(bytes.fromhex(recipe['color'][1:])),dtype=float)
    original=Image.open(src).convert('RGB')
    # Uniform scale and translation retain the product packs' aspect ratios.
    scale=980/(r-l)
    dx=110-l*scale
    dy=650-min(tl,tc,tr)*scale
    bg=tuple(np.rint(color*.14+255*.86).astype(int))
    transformed=cv2.warpAffine(np.array(original),np.float32([[scale,0,dx],[0,scale,dy]]),(1200,900),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE)
    im=Image.fromarray(transformed)
    # Shared front silhouette; replace the entire lower area so old boxes cannot leak.
    yy,xx=np.indices((900,1200))
    t=np.clip((xx-110)/980,0,1)
    rim=605+180*t*(1-t)
    lower=Image.fromarray(np.uint8(yy>=rim)*255)
    # Continue the existing pale studio background without rectangular seams.
    left=np.median(transformed[:,:5,:],axis=1)[:,None,:]
    right=np.median(transformed[:,-5:,:],axis=1)[:,None,:]
    mix=np.linspace(0,1,1200)[None,:,None]
    backdrop=Image.fromarray(np.uint8(left*(1-mix)+right*mix))
    im.paste(backdrop,(0,0),lower)
    shadow=Image.new('RGBA',im.size)
    ImageDraw.Draw(shadow).ellipse((100,829,1110,878),fill=(20,15,10,65))
    im=Image.alpha_composite(im.convert('RGBA'),shadow.filter(ImageFilter.GaussianBlur(14)))
    # Reuse the Europe panel's photographed material and lighting, without its printing.
    template=np.array(Image.open(src.parent/'eu-22.webp').convert('RGB'))
    erase=np.zeros((900,1200),np.uint8)
    erase[670:835,190:1060]=255
    blank=cv2.inpaint(template,erase,15,cv2.INPAINT_TELEA).astype(float)
    # Template blue channel carries its fabric-free cardboard luminance.
    shade=np.clip(blank[:,:,2]/168,.65,1.35)
    panel=np.uint8(np.clip(shade[:,:,None]*color,0,255))
    mask=Image.fromarray(np.uint8((xx>=110)&(xx<=1090)&(yy>=rim)&(yy<=850))*255)
    im.paste(Image.fromarray(panel).convert('RGBA'),(0,0),mask)
    d=ImageDraw.Draw(im)
    d.line([(110,605),(110,845),(115,850),(1085,850),(1090,845),(1090,605)],fill=tuple(np.uint8(color*.72))+(255,),width=2)
    # A straight shared typography grid avoids curved or stretched country lettering.
    title=recipe['country'].upper()+' EDITION'
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Impact.ttf',100)
    box=font.getbbox(title)
    text=Image.new('RGBA',(box[2]+4,box[3]-box[1]+4))
    ImageDraw.Draw(text).text((0,-box[1]),title,font=font,fill='white')
    text=text.resize((min(700,round(text.width*80/text.height)),80),Image.Resampling.LANCZOS)
    im.alpha_composite(text,(round(565-text.width/2),685))
    d.line((215,780,915,780),fill='white',width=4)
    f=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',31)
    brand='SNACKS OF EUROPE'
    widths=[d.textlength(c,font=f) for c in brand]
    x=565-(sum(widths)+4*(len(brand)-1))/2
    for ch,width in zip(brand,widths):
        d.text((x,795),ch,font=f,fill='white');x+=width+4
    # Keep each existing postage illustration, isolating its red silhouette.
    stamps={'pl-15':(875,615,1015,790),'de-20':(935,680,1090,837),'nl-18':(940,670,1070,803),'be-16':(935,635,1068,790),'it-16':(928,580,1070,740),'fr-15':(880,640,1015,795),'es-16':(880,645,1015,800),'se-18':(880,640,1015,795),'uk-classic':(900,645,1070,830),'sub-italy':(890,580,1035,765)}
    stamp=original.crop(stamps[src.stem]).convert('RGBA')
    a=np.array(stamp)
    red=((a[:,:,0].astype(float)>a[:,:,1]*1.35)&(a[:,:,0].astype(float)>a[:,:,2]*1.3)&(a[:,:,0]>100)).astype(np.uint8)*255
    from scipy.ndimage import binary_fill_holes
    red=np.uint8(binary_fill_holes(red))*255
    red=cv2.dilate(red,np.ones((9,9),np.uint8))
    stamp.putalpha(Image.fromarray(red))
    stamp.thumbnail((135,145),Image.Resampling.LANCZOS)
    im.alpha_composite(stamp,(round(985-stamp.width/2),680))
    im=im.convert('RGB')
    im.save(dest,'WEBP',quality=84,method=6)
    assert dest.stat().st_size<150000, dest

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    for name,spec in LANDMARKS.items():
        if name=='eu-22':
            continue  # The approved reference stays byte-for-byte unchanged.
        dest=args.out/(name+'.webp')
        render(args.source/(name+'.webp'),dest,spec)
        print(name,dest.stat().st_size)
