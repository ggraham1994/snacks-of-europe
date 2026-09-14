# Product image coverage

85 unique WebP cutouts cover all 88 catalogue entries on All Products and Build a Box. Duplicate EAN entries share the same image.

The studio-photo refresh replaces 39 existing images and fills 11 missing images. Of these 50 photos, 44 come from linked Amazon listings and six from manufacturer or retailer sources. Public source URLs and crop/mask coordinates are recorded in `tools/product_image_sources.json`. No packaging artwork was generated or rewritten. Existing approved images, including heart-free LU Bastogne, remain unchanged.

Every file is 480px on its longest side, preserves source proportions, contains transparency and is below 60KB. Outputs use WebP quality 84. White wrappers and multipack source crops require visual review; automatic background removal alone is not sufficient.

Rejected alternatives included De Ruijter Kleintjes photos showing a different weight and a Perugina photo with loose sweets obscuring the wrapper. Their previous images remain unchanged; image coverage does not mean all sources are equally high quality.

Run `python3 tools/check_product_images.py` to validate the assets. To reproduce a cutout, download its recorded source, add a local `path` to that manifest entry, and run `python3 tools/export_product_packshots.py manifest.json --out images/products` (Pillow, numpy and OpenCV required). Review each result before publishing.
