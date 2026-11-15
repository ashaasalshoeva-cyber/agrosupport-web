# AgroSupport v0.2.1

Three crop tabs: About / Calculators / NASA Data. Baseline design preserved from v0.2.1.

# AgroSupport / AAIAP — v0.1.1-demo

A judge-friendly, no-account agronomic research demo built from the **available v0.0.6 project**. The prompt targeted v0.0.8, but its archive was not included with the input. The v0.0.6 baseline preserves the latest accessible design, multilingual UI, NASA/NOAA/NRCS endpoints, crop catalogue and calculator tools.

## Quick test on Windows (Python 3.11+)

Unzip the entire archive; `server.py` must be in the current folder.

```powershell
py -3 server.py
```

Then visit <http://127.0.0.1:8000>. Press **NASA DEMO / Corn** on the welcome page. A **Science & AI** nav link contains methodology and disclosure. The **NASA data** tab loads calculated season data, MODIS exploratory NDVI and Climate Twin (only if the official services respond).

If Leaflet or external map tiles fail, the site displays a research-site navigation fallback instead of crashing. A satellite layer may not render without working remote NASA GIBS tiles. The layer identification and time interval should be verified against current `GetCapabilities`.

## Cloud demo (no registration and no upload)

The application includes an isolated cloud mode:

```powershell
$env:AAIAP_MODE='cloud-demo'
$env:HOST='0.0.0.0'
$env:PORT='10000'
py -3 server.py
```

`cloud-demo` disables administrator sessions, admin editing, community photo uploads, and access to local upload storage (HTTP 403/404); no user login exists. It uses environment `PORT`/`HOST`, JSON response limits, headers, rate limits, and a cached API. `/api/health` exposes the deployment version and cache / snapshot status. Keep HTTPS termination on the hosting platform.

**Deploy via Render Blueprint (example only):**
1. Push the project to a private or public Git repository **excluding** `.env`, `data/admin.json`, and `uploads/`.
2. In Render choose **New → Blueprint**, connect the repo and confirm `render.yaml`.
3. Check whether the selected `free` plan still exists and its inactivity/cold-start limits before publishing to judges.
4. Wait for a successful health check (`/api/health`), then open the generated HTTPS address from an unrelated mobile device.
5. At the domain registrar for `agrosupport.earth`, configure the domain records **exactly as Render displays**; verify certificate issuance. No Cloudflare or access gate is required for viewers.
6. Ensure the app is awake and externally accessible during judging; free instances can cold-start or be unavailable. This project is a research demo, **not a hardened production host**.

A `Dockerfile`, `Procfile`, and `.dockerignore` are included. The demo uses Python stdlib only (no pip install). Persistent file uploads are intentionally disabled in the cloud because free hosts may have ephemeral file systems.

## Scientific integrity

- **Real sources when connected:** NASA POWER (daily), NASA ORNL MODIS (experimental), NASA GIBS true-colour layer (historical tiles), NOAA/NWS forecast, USDA NRCS SSURGO map units. External availability is **not verified from this offline build environment**. An API error shows an unavailable state.
- **No fabricated NASA responses:** `data_snapshots/` initially contains no data JSON. After verifying outbound access, run `py -3 scripts/refresh_snapshots.py`, inspect source URLs and dates, and commit only authenticated successful output. At an API outage the site can display a **dated real saved snapshot**.
- **Calculation:** `agro_calc.py` includes documented corn GDD using 10–30 °C clamping, summer precipitation, heat days and freeze markers. `data/crop_thresholds.json` records the source and leaves other crop GDD thresholds unspecified.
- **Climate Twin:** an **uncalibrated** multifeature similarity between a Nebraska research station reference point and an approximate Tajik regional location, *not proof of comparable soil or farming practices*. Network-dependent: no generated percentage before actual POWER data.
- **NDVI:** MOD13Q1 subset service; pixel scale about 250m, quality flags are not fully handled yet. Do not interpret as a single farm's NDVI.
- **Validation:** ground station validation is pending. `docs/validation_report.md` and `scripts/validate_power.py` explain how to reproduce it with actual NASA/ground CSV observations.
- **AI:** `POST /api/assistant/summary` currently offers **deterministic template mode only**, explicitly labelled; no LLM claims or secret keys in browser. The PDF/slide claim must match this fact. AI-assisted development occurred. See `docs/presentation_slides.md`.
- **Photos:** legacy online Unsplash illustrations may not load on restricted networks. No licence is represented as verified. Replace before public deployment with sourced licensed visuals; the original local logo/backgrounds are retained. PT Sans falls back to available fonts if Google Fonts is blocked; font binaries are not included.

## Tests

```powershell
py -3 -m unittest discover -s tests -v
```

On Linux/macOS: `sh scripts/check_all.sh` (also checks JS syntax if Node is available).

## Files of interest

- `server.py` / `Dockerfile` / `render.yaml`: demo service and API.
- `agro_calc.py`, `assistant_template.py`, `snapshots.py`: transparent calculations, deterministic response, real saved data fallback.
- `js/research-demo.js`: NASA data, Climate Twin, labelled template assistant, method/validation disclosure.
- `js/map-fallback.js`: non-crashing navigation when Leaflet fails.
- `docs/presentation_slides.md`: slide drafts and evidence/caveats.
- `docs/validation_report.md`: validation pending, reproducible comparison guide.

## Known work still required before judging

- Test all remote NASA endpoints and GIBS exact tile layers against current official capabilities on an Internet-connected device.
- Obtain and retain real NASA/NOAA/NRCS snapshots; assess licensing of image sources.
- Perform ground-station comparison for validity; correct Tajik translations with a native reviewer.
- Test public HTTPS link, responsive UI and service cold starts; if externally distributed, do not rely on the stdlib development HTTP server alone.
- Make data NASA-centric in more crop-specific outputs. Missing is better than invented.
