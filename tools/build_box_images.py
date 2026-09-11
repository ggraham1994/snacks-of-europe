#!/usr/bin/env python3
"""Compose box hero images from real packshots.

    python3 build_box_images.py --catalog catalog.json --boxes boxes.json --out box-images

boxes.json is a list of boxes:
  {"id":"de-20", "country":"Germany", "color":"#F4B400",
   "products":[{"match":"Haribo Quaxi", "image":0, "pick":"left"}, ...]}

  style  "box" (default: packs standing in the open Snacks of Europe box),
         "cluster" (packs fanned on the tinted background with no box or text,
         used for the country tiles) or "cutouts" (no composition: each pack is
         written as its own transparent WebP, <id>-<slug>.webp, for the hero)
  slug   file name for a cutout in a "cutouts" recipe (default: its index)

  match  substring of the Airtable SKU Name (or give "ean")
  image  which attachment to use (index into the product's images, default 0)
  pick   which pack to keep when several are in frame: largest | left | right | top | bottom
  crop   optional [x0,y0,x1,y1] fractions applied before background removal
  white_thresh  brightness (0-255) above which a border-connected pixel counts as
         background for the "white" method; default 232, use ~250 for packs with white
         packaging on Amazon's pure-white background (per product or per box)
  method "rembg" (default, for phone/warehouse photos) or "white" for studio packshots
         on a plain white background, where the segmentation model tends to keep only
         the printed food photo
  rotate optional degrees to turn the cutout (e.g. 90 to stand a tube upright)
  image_url  use this picture instead of the Airtable attachment (e.g. an Amazon
             catalogue image); defaults to method "white"
  asin       fetch the Amazon main image for this ASIN (add "marketplace": "co.uk",
             "de", ... ; default "com"); best effort, falls back to an error that
             tells you to paste an image_url

Background removal uses rembg (pip install "rembg[cpu]"); --no-rembg falls back to
treating near-white pixels as background, which only suits studio packshots.
Output per box: <id>.png and <id>.webp at 1200x900, plus manifest.json.
"""
import argparse, hashlib, json, os, re, sys, urllib.request
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H, S = 1200, 900, 3.75          # canvas and the scale from the site's 320x240 drawing
FONT_BLACK = ['/System/Library/Fonts/Supplemental/Arial Black.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']
FONT_BOLD = ['/System/Library/Fonts/Supplemental/Arial Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']

def font(paths, size):
    for p in paths:
        if os.path.exists(p): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def hex2rgb(h): h = h.lstrip('#'); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def shade(rgb, p):
    t = 0 if p < 0 else 255; a = abs(p)
    return tuple(round(c + (t - c) * a) for c in rgb)

# ---------------- catalogue ----------------
def find_product(cat, spec):
    if spec.get('ean'):
        for r in cat:
            if r.get('ean') == spec['ean'] and r.get('images'): return r
    q = spec['match'].lower()
    for r in cat:
        if r.get('name') and q in r['name'].lower() and r.get('images'): return r
    sys.exit(f"no catalogue match for {spec.get('match') or spec.get('ean')!r}")

def fetch(att, cache):
    os.makedirs(cache, exist_ok=True)
    fn = os.path.join(cache, att['id'] + '.img')
    if not os.path.exists(fn):
        urllib.request.urlretrieve(att.get('full') or att['url'], fn)
    return fn

AMZ_PATTERNS = [r'"hiRes":"(https://m\.media-amazon\.com/images/I/[^"]+)"',
                r'data-old-hires="(https://m\.media-amazon\.com/images/I/[^"]+)"',
                r'"large":"(https://m\.media-amazon\.com/images/I/[^"]+)"']
def amazon_main_image(asin, tld='com'):
    """Best-effort scrape of the main catalogue image for an ASIN."""
    req = urllib.request.Request(f'https://www.amazon.{tld}/dp/{asin}', headers={
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36',
        'Accept-Language': 'en-GB,en;q=0.8'})
    try:
        html = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'ignore')
    except Exception as e:
        sys.exit(f'could not fetch Amazon page for {asin}: {e}. Paste the picture URL as "image_url" instead.')
    for pat in AMZ_PATTERNS:
        m = re.search(pat, html)
        if m: return m.group(1)
    sys.exit(f'no main image found on the Amazon page for {asin}. Paste the picture URL as "image_url" instead.')

def source_for(spec, cat):
    """Resolve a recipe entry to (product, attachment-like dict, default method)."""
    prod = find_product(cat, spec) if (spec.get('match') or spec.get('ean')) else {'name': spec.get('name', spec.get('asin', 'product')), 'ean': spec.get('ean'), 'images': []}
    if spec.get('image_url') or spec.get('asin'):
        url = spec.get('image_url') or amazon_main_image(spec['asin'], spec.get('marketplace', 'com'))
        return prod, {'id': 'url-' + hashlib.md5(url.encode()).hexdigest()[:16], 'url': url, 'filename': url}, 'white'
    return prod, prod['images'][spec.get('image', 0)], 'rembg'

# ---------------- cutout ----------------
_session = None
def white_cutout(im, thresh=232):
    """Background = near-white pixels connected to the image border."""
    arr = np.asarray(im); near = arr.min(axis=2) > thresh
    scale = max(1.0, max(near.shape) / 350)
    size = (max(1, int(near.shape[1] / scale)), max(1, int(near.shape[0] / scale)))
    small = np.asarray(Image.fromarray(near.astype('uint8') * 255).resize(size, Image.BILINEAR)) > 128
    h, w = small.shape; bg = np.zeros_like(small); q = deque()
    for x in range(w):
        for y in (0, h - 1):
            if small[y, x] and not bg[y, x]: bg[y, x] = True; q.append((y, x))
    for y in range(h):
        for x in (0, w - 1):
            if small[y, x] and not bg[y, x]: bg[y, x] = True; q.append((y, x))
    while q:
        cy, cx = q.popleft()
        for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
            if 0 <= ny < h and 0 <= nx < w and small[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True; q.append((ny, nx))
    bgfull = np.asarray(Image.fromarray(bg.astype('uint8') * 255).resize(im.size, Image.BILINEAR)) > 40
    alpha = np.where(bgfull & near, 0, 255).astype('uint8')
    out = im.convert('RGBA'); out.putalpha(Image.fromarray(alpha).filter(ImageFilter.GaussianBlur(1))); return out

def cutout(im, use_rembg=True, method='rembg', white_thresh=232):
    im = ImageOps.exif_transpose(im).convert('RGB')
    im.thumbnail((1400, 1400))
    if method == 'white': return white_cutout(im, white_thresh)
    if use_rembg:
        global _session
        from rembg import remove, new_session
        if _session is None: _session = new_session('u2net')
        return remove(im, session=_session).convert('RGBA')
    arr = np.asarray(im).astype(int)
    alpha = np.where(arr.min(axis=2) > 225, 0, 255).astype('uint8')
    out = im.convert('RGBA'); out.putalpha(Image.fromarray(alpha)); return out

def components(mask, min_frac=0.02):
    h, w = mask.shape; labels = np.zeros((h, w), dtype=np.int32); comps = []
    for y in range(h):
        for x in range(w):
            if mask[y, x] and labels[y, x] == 0:
                n = len(comps) + 1; labels[y, x] = n; q = deque([(y, x)])
                area = sx = sy = 0; x0 = x1 = x; y0 = y1 = y
                while q:
                    cy, cx = q.popleft(); area += 1; sx += cx; sy += cy
                    x0, x1, y0, y1 = min(x0, cx), max(x1, cx), min(y0, cy), max(y1, cy)
                    for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                        if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and labels[ny, nx] == 0:
                            labels[ny, nx] = n; q.append((ny, nx))
                comps.append({'label': n, 'area': area, 'cx': sx / area, 'cy': sy / area, 'bbox': (x0, y0, x1, y1)})
    big = [c for c in comps if c['area'] >= min_frac * h * w]
    return labels, (big or comps)

def select_pack(rgba, pick='largest'):
    a = np.asarray(rgba.split()[-1])
    scale = max(1.0, max(a.shape) / 240)
    small_size = (max(1, int(a.shape[1] / scale)), max(1, int(a.shape[0] / scale)))
    small = np.asarray(Image.fromarray(a).resize(small_size, Image.BILINEAR)) > 128
    labels, comps = components(small)
    if not comps: return rgba
    key = {'largest': lambda c: -c['area'], 'left': lambda c: c['cx'], 'right': lambda c: -c['cx'],
           'top': lambda c: c['cy'], 'bottom': lambda c: -c['cy']}[pick]
    c = sorted(comps, key=key)[0]
    x0, y0, x1, y1 = c['bbox']
    single = len(comps) == 1
    if single and pick in ('left', 'right'):
        mid = (x0 + x1) // 2; x0, x1 = (x0, mid) if pick == 'left' else (mid, x1)
    if single and pick in ('top', 'bottom'):
        mid = (y0 + y1) // 2; y0, y1 = (y0, mid) if pick == 'top' else (mid, y1)
    keep = np.asarray(Image.fromarray((labels == c['label']).astype('uint8') * 255).resize(rgba.size, Image.NEAREST)) > 0
    out = rgba.copy(); out.putalpha(Image.fromarray(np.where(keep, a, 0).astype('uint8')))
    out = out.crop((int(x0 * scale), int(y0 * scale), int((x1 + 1) * scale), int((y1 + 1) * scale)))
    bb = out.split()[-1].getbbox()
    return out.crop(bb) if bb else out

# ---------------- composition ----------------
def fan(n, style='box'):
    """Pack centres in the site's 320x240 units: (cx, cy, rotation, height)."""
    if style == 'cluster':
        xs = [160] if n == 1 else [72 + i * (176 / (n - 1)) for i in range(n)]
        return [(x, 124 + 6 * abs((x - 160) / 88), -((x - 160) / 88) * 14, 150 - 28 * abs((x - 160) / 88)) for x in xs]
    xs = [160] if n == 1 else [92 + i * (136 / (n - 1)) for i in range(n)]
    out = []
    for x in xs:
        t = (x - 160) / 68
        out.append((x, 78 + 18 * abs(t) ** 1.2, -t * 20, 128 - 12 * abs(t)))
    return out

def draw_tracked(d, text, cx, y, fnt, fill, spacing):
    widths = [d.textlength(ch, font=fnt) for ch in text]
    total = sum(widths) + spacing * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        d.text((x, y), ch, font=fnt, fill=fill, anchor='ls'); x += w + spacing

def compose(box, packs):
    style = box.get('style', 'box')
    c = hex2rgb(box['color']); cd = shade(c, -.3); cl = shade(c, .14); tint = shade(c, .86)
    img = Image.new('RGBA', (W, H), tint + (255,))
    glow = Image.new('RGBA', (W, H), (255, 255, 255, 0))
    ImageDraw.Draw(glow).ellipse((200, 40, 1000, 640), fill=(255, 255, 255, 120))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(120)))
    P = lambda pts: [(x * S, y * S) for x, y in pts]
    if style == 'box':
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(sh).ellipse((105, 799, 1095, 881), fill=cd + (70,))
        img = Image.alpha_composite(img, sh.filter(ImageFilter.GaussianBlur(14)))
        ImageDraw.Draw(img).polygon(P([(58, 98), (262, 98), (256, 158), (64, 158)]), fill=cd)
    layout = fan(len(packs), style)
    for i in sorted(range(len(packs)), key=lambda i: -abs(layout[i][0] - 160)):
        cx, cy, rot, ph = layout[i]; pk = packs[i]
        r = ph * S / pk.height; pk2 = pk.resize((max(1, round(pk.width * r)), round(ph * S)), Image.LANCZOS)
        cap = 480 if style == 'cluster' else 420
        if pk2.width > cap:
            r = cap / pk2.width; pk2 = pk2.resize((cap, max(1, round(pk2.height * r))), Image.LANCZOS)
        rot_im = pk2.rotate(rot, expand=True, resample=Image.BICUBIC)
        shd = Image.new('RGBA', rot_im.size, (0, 0, 0, 0))
        shd.putalpha(rot_im.split()[-1].point(lambda v: int(v * .45)))
        pos = (round(cx * S - rot_im.width / 2), round(cy * S - rot_im.height / 2))
        img.alpha_composite(shd.filter(ImageFilter.GaussianBlur(16)), (pos[0] + 6, pos[1] + 24))
        img.alpha_composite(rot_im, pos)
    if style != 'box':
        return img.convert('RGB')
    d = ImageDraw.Draw(img)
    d.polygon(P([(46, 128), (274, 128), (262, 220), (58, 220)]), fill=c)
    d.polygon(P([(46, 128), (22, 114), (30, 204), (58, 220)]), fill=cl)
    d.polygon(P([(274, 128), (298, 114), (290, 204), (262, 220)]), fill=cl)
    title = f"{box['country'].upper()} EDITION"
    title_size = 56
    while title_size > 20 and sum(d.textlength(ch, font=font(FONT_BLACK, title_size)) for ch in title) + 2 * (len(title) - 1) > 700:
        title_size -= 1
    draw_tracked(d, title, 600, 672, font(FONT_BLACK, title_size), (255, 255, 255, 255), 2)
    d.line((250, 709, 950, 709), fill=(255, 255, 255, 255), width=4)
    draw_tracked(d, 'SNACKS OF EUROPE', 600, 743, font(FONT_BOLD, max(16, title_size // 2)), (255, 255, 255, 255), 3)
    stamp = Image.new('RGBA', (150, 120), (0, 0, 0, 0)); sd = ImageDraw.Draw(stamp)
    sd.rectangle((0, 0, 127, 97), fill=(255, 255, 255, 255)); sd.rectangle((11, 11, 116, 86), fill=(216, 35, 42, 255))
    sd.ellipse((45, 30, 82, 67), fill=(255, 255, 255, 255)); sd.ellipse((72, -14, 140, 54), outline=(255, 255, 255, 190), width=4)
    img.alpha_composite(stamp.rotate(-8, expand=True, resample=Image.BICUBIC), (866, 486))
    return img.convert('RGB')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--catalog', required=True); ap.add_argument('--boxes', required=True)
    ap.add_argument('--out', default='box-images'); ap.add_argument('--cache', default='.packshot-cache')
    ap.add_argument('--no-rembg', action='store_true'); ap.add_argument('--only', help='comma-separated box ids')
    a = ap.parse_args()
    cat = json.load(open(a.catalog)); boxes = json.load(open(a.boxes)); os.makedirs(a.out, exist_ok=True)
    manifest = {}
    for box in boxes:
        if a.only and box['id'] not in a.only.split(','): continue
        packs, used = [], []
        for spec in box['products']:
            prod, att, default_method = source_for(spec, cat)
            im = Image.open(fetch(att, a.cache))
            if spec.get('crop'):
                x0, y0, x1, y1 = spec['crop']; im = im.crop((int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height)))
            pk = select_pack(cutout(im, not a.no_rembg, spec.get('method', default_method), spec.get('white_thresh', box.get('white_thresh', 232))), spec.get('pick', 'largest'))
            if spec.get('rotate'): pk = pk.rotate(spec['rotate'], expand=True, resample=Image.BICUBIC)
            pk.save(os.path.join(a.cache, f"{box['id']}-{len(packs)}-cutout.png"))
            packs.append(pk); used.append({'ean': prod.get('ean'), 'name': prod.get('name'), 'attachment': att['id'], 'pick': spec.get('pick', 'largest')})
            print(f"  {box['id']}: {(prod.get('name') or '')[:50]} ({att.get('filename', '')[:40]}) -> {pk.size}")
        if box.get('style') == 'cutouts':
            files = []
            for i, (pk, spec) in enumerate(zip(packs, box['products'])):
                pk = pk.copy(); pk.thumbnail((900, 720))
                fn = os.path.join(a.out, f"{box['id']}-{spec.get('slug', i)}.webp")
                pk.save(fn, quality=86, method=6); files.append(fn)
                print(f"wrote {fn} ({os.path.getsize(fn) // 1024} KB, {pk.size[0]}x{pk.size[1]})")
            manifest[box['id']] = {'style': 'cutouts', 'files': files, 'products': used}
            continue
        out = compose(box, packs)
        png, webp = os.path.join(a.out, box['id'] + '.png'), os.path.join(a.out, box['id'] + '.webp')
        out.save(png, optimize=True); out.save(webp, quality=84, method=6)
        manifest[box['id']] = {'country': box.get('country'), 'png': png, 'webp': webp, 'products': used}
        print(f"wrote {webp} ({os.path.getsize(webp) // 1024} KB)")
    json.dump(manifest, open(os.path.join(a.out, 'manifest.json'), 'w'), indent=1)

if __name__ == '__main__':
    main()
