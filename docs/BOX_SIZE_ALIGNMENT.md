# Standard box sizes

Approved reference: `images/eu-22.webp` at commit ff22307. The reference remains
unchanged. Ten other box scene exports are aligned to its front-panel width,
height, curved rim and baseline. Hero packs and country/collection tiles are unchanged.

The built-in image model was tested with Europe as a geometry reference and each
country image as the edit target. Those drafts were not published: the model
retained varying geometry and sometimes changed packaging. Final exports instead
use the original artwork with a uniform scale/translation (no product stretching)
and the local box-rendering approach allowed by the image brief. They reuse the
Europe panel's material, draw a fixed lettering grid and retain country stamps.

`tools/align_box_sizes.py` records all source landmarks and the common target.
To rerun, supply an unmodified directory of these WebP files from commit ff22307
as `--source`, and the website images directory as `--out`. Do not use already
aligned exports as inputs. Requires Pillow, numpy, OpenCV and scipy, plus the
macOS Impact/Arial Bold fonts used by this project.

All changed files remain opaque 1200×900 WebP, quality 84 and below 150,000 bytes.
The cache version in index.html ensures browsers fetch the new exports.
