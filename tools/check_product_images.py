#!/usr/bin/env python3
"""Validate published catalogue cutouts; missing source photos are allowed by the brief."""
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
catalogue = json.loads((ROOT / 'tools/products.json').read_text())
paths = {row['image'] for row in catalogue}
available = 0
for relative in sorted(paths):
    path = ROOT / relative
    if not path.exists():
        continue
    with Image.open(path) as image:
        assert image.format == 'WEBP', relative
        assert image.mode == 'RGBA', f'{relative}: missing alpha channel'
        assert max(image.size) == 480, f'{relative}: {image.size}'
        assert image.getchannel('A').getextrema()[0] == 0, relative
        assert path.stat().st_size < 60000, f'{relative}: too large'
    available += 1
covered = sum((ROOT / row['image']).exists() for row in catalogue)
print(f'{available}/{len(paths)} unique images; {covered}/{len(catalogue)} catalogue entries covered')
print('All available images pass format, dimensions, transparency and file-size checks.')
