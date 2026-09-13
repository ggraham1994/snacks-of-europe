# Product image coverage

74 unique WebP cutouts cover 77 of the 88 catalogue entries on both All Products and Build a Box. Duplicate EAN entries share their image file.

Sources: linked Amazon packshots and front-facing Airtable Product Image attachments. Warehouse contact sheets were cropped to the front pack, with background masks corrected where automatic segmentation removed wrapper artwork. Existing approved source packshots were reused where available, including the heart-free LU Bastogne cutout. No new packaging was invented. Each output preserves its source proportions, is 480px on its longest side, has transparency and is below 60KB.

Run `python3 tools/check_product_images.py` to validate the exported files.

## Awaiting usable front-facing photos

These entries retain the existing placeholder because the available photos were obscured, showed labels/side panels, were cropped, or showed a different selling unit:

| EAN | Product |
| --- | --- |
| 4009267003089 | Fonzies cheese corn snacks |
| 4008400121321 | Giotto hazelnut mini sticks |
| 4033500101768 | Ahoj-Brause fizzy sherbet sweets |
| 4014400930054 | nimm2 Lolly fruit lollipops |
| 4009300016953 | Teekanne Italian cherry tea |
| 4009300005865 | Teekanne fennel tea |
| 8076809583039 | Mulino Bianco Baiocchi pistachio (large) |
| 40084176 | Kinder Country cereal chocolate bar |
| 8017139101531 | Agrisicilia pistachio cream 45% |
| 8718500445024 | K&H Muntendrop mint liquorice |
| 8714600003041 | King Extra Strong peppermints |

Add each approved replacement at `images/products/<EAN>.webp`; both pages will use it automatically. Do not substitute a different flavour or pack size to fill a gap.
