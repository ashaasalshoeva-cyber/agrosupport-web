# AgroSupport 0.2.1 — implementation and verification

## Basis and constraints

The uploaded AgroSupport 0.1.3 archive was used as the base. Only the requested calculators were taken from 0.1.5, and the science engine, verified dataset snapshots and validation assets from 0.2.0. No JS framework or build system was introduced. The existing navigation, layout, crop catalog and GIS map remain in place. Original source archives were not modified.

## Step 1 — three crop tabs

`js/portal.js`: main tabs `about`, `calc`, `nasa`; secondary tabs `npk/wheat/rates` and `land/irrigation/forecast`; preserves older plant content and old land/water planners; collapses agrotechnology and source/methodology and AAIAP assistant. Deep links in the form `#/crop/corn/nasa/forecast` and browser back/forward are handled. The selected sub-tab is horizontally scrollable; keyboard left/right navigation and ARIA tabs added. `js/i18n.js` includes EN/RU/TJ labels. The baseline look is preserved; limited CSS is appended. Same-origin embedding enabled in security headers.

## Step 2 — calculators

Transferred the donor's `tools/` six files, `agro_lab.py`, `agro_nasa.py`, and `agro_ai.py`. The three calculators are embedded via same-origin `iframe` with `?embed=1`, hiding their standalone navigation. The original calculator inputs, rate coefficients and formulas are not altered. The server exposes `/api/agro/weather`, `/api/agro/balance`, `/api/agro/advice`. The AI response is checked against numerical input; a deterministic template is returned if no key, provider error, or unsupported numbers. The numerical calculation itself is performed in Python. No API key is exposed in JS. [нужен агроном] The reference rates and Kc coefficients require domain review.

## Step 3 — NASA evidence

Transferred donor `science.py`, the 0.2.0 `agro_calc.py`, 17 original JSON snapshots, `data/crop_thresholds.json`, the validation report and its JSON, scripts and GIBS layer registry. The server provides `/api/science/sites`, `/api/science/evidence`, `/api/science/twin` and `/api/science/modis`, without removing `/api/data/*`. Evidence includes last completed calendar year and previous ten-year monthly climate baselines, with nulls for incomplete months. MODIS shows a QA-aware table, line chart and CSV export, and labels it as a mixed ~250 m pixel, not a plot-scale measurement. A historical weekly frost frequency is separate from the current US NWS forecast. Source status, retrieval date, resolution and units are labelled. The original POWER monthly endpoint can fall back to the real bundled Nebraska source if remote requests fail. No synthetic NASA figures were added.

## Verification performed

- `python -m unittest discover -s tests -q`: **41 tests OK** (the baseline 25, donor tests, v0.2.1 regression tests). The donor test of a textual mode was aligned to the explicit `template` mode requirement.
- `node --check js/portal.js`, `js/i18n.js`, `js/research-demo.js`: passed.
- `node --experimental-default-type=module tests/nasa_client_browser_test.mjs`: **8 checks passed**.
- Local Python HTTP tests: `/api/health`, science endpoints, three calculator documents, metadata and validation data returned HTTP 200; CSP returned `SAMEORIGIN` with `frame-ancestors 'self'`. A valid NASA snapshot from the Tajikistan regional reference was parsed offline.

## Remaining checks / limits

- [проверить онлайн] A live remote request to NASA POWER, CORS in the end user's browser, MODIS network availability and GIBS GetCapabilities were not verified. The bundle works offline for specific documented reference sites; arbitrary coordinates need an active remote API.
- [проверить онлайн] Chromium browser automation was blocked by the environment's administrator network policy. Pixel-perfect layout, iframe height, mobile scroll behaviour and browser history should be validated on widths 360, 768 and 1366 px before publication.
- [проверить носителем] Newly added Tajik UI translations need native-speaker proofreading. Some inherited standalone donor tools still have Russian-only text; their source content was deliberately not rewritten under the minimal-change constraint.
- [нужен агроном] Crop-specific NPK offtake and FAO-56 Kc values and irrigation recommendations require agronomic approval.
- Image licences and use of images.unsplash.com need review. Ground-station validation for Tajikistan is not provided; Nebraska validation has limitations and is shown without inflating correlations.
- NASA GIBS layer definitions were retained but no unverified GIBS map layer was enabled.

## Start

`python server.py`, then visit `http://127.0.0.1:8000` and click `NASA DEMO / Corn` or use `#/crop/corn/nasa/forecast` directly. Local development server is not suitable for direct exposure to the public internet; deploy on a supported host with the cloud-demo mode.
