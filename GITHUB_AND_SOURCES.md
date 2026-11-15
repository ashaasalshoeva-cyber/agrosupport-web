# AgroSupport v0.1.3 — Github deployment and source status

## 1. Images (three independent slots)

Crop images can now be changed independently: **catalog card**, **large detail image**, **detail page wallpaper**.

### Fastest way to add an image before GitHub publication

Run in the unzipped project folder:

```
python scripts/add_crop_images.py corn --card my-corn.webp --detail my-corn-closeup.webp --background my-field.webp
```

You may specify only one or two flags; other images remain unchanged. Repeat for another crop (`wheat`, `cotton`, `soybean`, etc.). Script validates genuine JPG/PNG/WebP and size/dimensions, copies into `assets/crops/<crop>/`, and updates `js/crop-images.js`. Then commit the `assets/crops/` directory and `js/crop-images.js` to GitHub. After GitHub redeploy, all users see the new public pictures. For manual edits see `assets/crops/README.md`.

**GitHub Pages is static hosting:** it cannot receive public file uploads or run this project's Python API. A browser's File input alone cannot store images permanently for everyone. On GitHub Pages add files using GitHub's repository uploader/commit, then redeploy. If site files are on GitHub but the app is hosted on a separate Python-capable platform, the current local admin photo editor can work **only** when cloud-demo read-only mode is off **and** the storage is persistent; this is a different deployment model. Do not expose the included stdlib development server directly on the public Internet.

Current crop card/large/detail photo support uses `js/crop-images.js`. The old server-managed uploaded *card* photo still overrides the Git catalog card when available. Git-managed *detail* and *background* stay independent.

Image quality: prefer square 800×800 WebP for card, 1400×1000 for detail and 1920×1080 for background. Use legally licensed imagery; don't commit EXIF/location-sensitive media.

## 2. New crop data pages

- Vegetation: Landsat spectral indices, MODIS NDVI, USDA NAIP (US only).
- Soil: SSURGO (US only), NASA SRTM, ISRIC SoilGrids, FAO/IIASA GAEZ.
- Water: NASA POWER, NASA SMAP, SRTM terrain, Nebraska Mesonet ground verification.
- Agrotechnology: field preparation, crop rotation, sowing, laboratory soil testing, NPK, irrigation, monitoring, harvest; extension/FAO/NASS references.
- Additional research: cross-source registry with intended usage and deployment status.

**Source availability is explicitly distinguished**. NASA POWER and MODIS have existing backend API handlers, but live access still needs an Internet-connected runtime. USDA NRCS soil response is available only for the US pilot point. Everything else in the new tabs is an **official documentation link**, not a completed backend integration; there are no invented values or fictitious NASA readings.

NAIP is USDA aerial imagery of the US (not NASA). FAO/IIASA GAEZ, USDA NASS, Nebraska Mesonet, ISRIC SoilGrids are not NASA databases; Landsat is a NASA/USGS mission with USGS distribution. SRTM and SMAP are NASA missions. USDA NAIP and SSURGO will not provide Tajikistan farm coverage.

## 3. Static GitHub Pages compatibility

The crop catalogue can now open with a specifically identified static Nebraska demo research site when the Python `/api/sites` endpoint is missing. All scientific data APIs remain unavailable on GitHub Pages alone; the existing UI must display unavailable/error, not invent data. For **stable live data**, deploy a Python backend separately, or export verified dated scientific JSON snapshots in a future static-data workflow. Repo upload alone is not a NASA data API.

## 4. Tests

Run `python -m unittest discover -s tests -v` and, if installed, `node --check js/portal.js` etc. No successful real NASA connection was established from this offline editing environment.
