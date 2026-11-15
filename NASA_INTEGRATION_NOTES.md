# AgroSupport 0.1.2 — NASA integration and fixes

## Changes
- Removed the top-right camera/admin-editor trigger from BOTH map and portal headers. The existing photo editing code is left intact but not accessible via the removed button.
- NASA tab includes monthly NASA POWER interactive charts for temperature (°C), precipitation (mm/month), daily mean solar irradiation (kWh/m²/day), and 2 m wind speed (m/s), plus accessible tabular data and month tooltips.
- Monthly POWER loads automatically on first visit to the NASA tab. Manual refresh buttons still work.
- Successful real NASA POWER, derived season, and MODIS API responses are saved in `data_snapshots/*.json` using the existing validated snapshot writer. If a subsequent remote call fails, the server can return the last authentic response with `snapshot: true` and retrieval time. Successful responses remain memory-cached with the original TTL.
- No fake NASA values are bundled. If there has never been a successful online request, offline data remains unavailable; the UI explains that.
- Kept NASA provenance and methodology/limitations on chart screens.
- Added a persistence regression test and updated the version-aware health endpoint test. 25 tests pass and JavaScript syntax checks pass.

## How to launch
1. On a computer connected to the Internet, run `python server.py` from this folder.
2. Open `http://127.0.0.1:8000/`.
3. Select **NASA DEMO / Corn** on the welcome page or select the corn crop and open the NASA tab. Monthly POWER is fetched once automatically; charts become visible when the response succeeds.
4. Click **Load verified data** next to season indicators and MODIS to warm additional snapshots. When you restart the server, verified snapshots can be used if NASA endpoints are temporarily unavailable.
5. For deployment, mount `data_snapshots` on persistent storage or periodically run `python scripts/refresh_snapshots.py` and redeploy the resulting verified snapshot files. Filesystems on many free hosting platforms are ephemeral; a successful fetch there does not guarantee durability across redeploys.

## Known limitations
- Source environment had no DNS/outbound Internet; NASA connectivity and output values could NOT be verified during this build. Production access to POWER and ORNL MODIS must be tested online.
- POWER monthly figures are aggregated from daily modeled/grid values for the Nebraska research reference point, NOT direct field sensor data. Currently configured site is Nebraska; arbitrary GPS/field selection is not implemented.
- NASA MODIS API is experimental and quality masking has not been validated. The MODIS endpoint may fail independently of POWER.
- No source-data snapshot is bundled because none was verified by a live NASA fetch.
- This is a development server; do not publicly expose in local mode without a security review.

Official reference: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
