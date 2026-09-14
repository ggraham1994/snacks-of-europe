#!/usr/bin/env python3
"""Export approved, local studio packshots without altering their printed artwork.

Usage: python3 tools/export_product_packshots.py manifest.json --out images/products
Manifest: [{"ean": "...", "path": "local photo", "polygon": [[x,y], ...]}]
Polygon coordinates, when needed, are normalized to the source image. Without a
polygon, only the largest solid silhouette on a near-white studio backdrop is kept.
Always visually review the result. Never use this automatic mask for warehouse photos.
"""
import argparse,json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageOps,ImageDraw,ImageFilter

def export(row, destination):
    source=ImageOps.exif_transpose(Image.open(row['path'])).convert('RGBA')
    if row.get('crop'):
        source=source.crop(tuple(round(v*s) for v,s in zip(row['crop'],[source.width,source.height,source.width,source.height])))
    if row.get('polygon'):
        alpha=Image.new('L',source.size)
        ImageDraw.Draw(alpha).polygon([(round(x*source.width),round(y*source.height)) for x,y in row['polygon']],fill=255)
    elif source.getchannel('A').getextrema()[0] < 255:
        alpha=source.getchannel('A')
    else:
        rgb=np.asarray(source.convert('RGB'))
        foreground=(rgb.min(axis=2)<row.get('threshold',242)).astype('uint8')*255
        foreground=cv2.morphologyEx(foreground,cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
        contours,_=cv2.findContours(foreground,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        if not contours:raise ValueError(f"No pack silhouette: {row['ean']}")
        filled=np.zeros_like(foreground);cv2.drawContours(filled,[max(contours,key=cv2.contourArea)],-1,255,cv2.FILLED)
        alpha=Image.fromarray(filled)
    source.putalpha(alpha.filter(ImageFilter.GaussianBlur(.35)))
    bounds=source.getchannel('A').point(lambda a:255 if a>32 else 0).getbbox()
    if not bounds:raise ValueError(f"Empty image: {row['ean']}")
    source=source.crop(bounds)
    source=source.resize(tuple(max(1,round(v*478/max(source.size))) for v in source.size),Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',(source.width+2,source.height+2));canvas.alpha_composite(source,(1,1))
    destination.mkdir(parents=True,exist_ok=True)
    path=destination/(row['ean']+'.webp');canvas.save(path,'WEBP',quality=84,method=6)
    if path.stat().st_size>=60000:raise ValueError(f'{path}: exceeds 60KB; review the source')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest',type=Path);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    for row in json.loads(args.manifest.read_text()):
        export(row,args.out);print(row['ean'],flush=True)
