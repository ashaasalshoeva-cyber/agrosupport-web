# AAIAP 0.1.1-demo — acceptance status (November 15, 2026)

**Base:** latest available archive v0.0.6. Requested v0.0.8 was not attached.

| Judging criterion | Status | Reviewer note | Non-guaranteed expected score after connected tests |
|---|---|---|---|
| No login | Implemented | Farmer catalogue without account; cloud mode has no editor / public uploads | 9/10 |
| Usability | Partial | One-click corn demo, responsive adjustments and fallback map; browser rendering not fully tested | 7/10 |
| Cloud access | Partial | Dockerfile, Render Blueprint, health endpoint; NOT actually deployed; free service cold starts | 4/10 |
| Disclosure of AI | Partial | Transparent deterministic template; no LLM provider integration or live generative claims | 6/10 |
| Impact | Partial | Crop catalogue and research station pilot; Tajik pilots remain unverified | 6/10 |
| Creativity | Partial | Climate Twin heuristic from actual POWER data on demand; online check pending | 6/10 |
| Validity | Partial | Tested GDD/frost/heat math; no ground-station bias/MAE/RMSE established | 7/10 |
| Relevance / NASA | Partial | POWER, experimental ORNL MODIS endpoint, GIBS true-colour overlay; live services NOT verified here | 6/10 |

These are **internal planning estimates**, not official NASA Space Apps scores. No category is guaranteed to earn any particular score; successful judging depends on real deploy, evidence and demonstration quality.

## Implemented in code

- Cloud config (`AAIAP_MODE=cloud-demo`), no public uploads/admin, environment port and host, API request throttling and security response headers.
- Daily NASA POWER-based calculated season indicators, explicit source/date/scale/limitations; dynamic last completed year.
- NASA ORNL MODIS experimental NDVI subset endpoint, honest approximate spatial resolution and absent QA limitation.
- NASA GIBS MODIS Terra historical true-colour layer button; external layers require real Internet and correct service capabilities.
- Climate Twin from POWER daily data of two labeled *reference points*, with disclosed heuristic scales; **not a crop suitability score**.
- Evidence Meter, deterministic multilingual summary and methodology page; template explicitly states when no AI model has run.
- Safe map fallback when Leaflet CDN fails, invalidation after hidden map becomes visible, OSM tile-error warning.
- Removal of fake soil/water/NDVI/temperature values from Tajik demo sites.
- Real-only dated snapshot writer and reader; no fabricated responses distributed.
- 24 passing Python tests and Node JS syntax checks.

## Partial or not completed

- The actual v0.0.8 source wasn't provided; the implementation builds on v0.0.6.
- No public HTTPS URL has been provisioned: `agrosupport.earth` remains unlinked to this build.
- **No real NASA/NOAA/USDA snapshots shipped** because outbound connections from the coding environment are unavailable.
- NDVI endpoint/parameters and NASA GIBS WMTS layer/time must be tested online against current `GetCapabilities`; GIBS is a true-colour layer, not the requested NDVI overlay yet.
- No full historical normal / calibrated seasonal window / real ground-station validation.
- No full LLM integration: template mode only, labelled honestly. Numbers are never AI-generated.
- External Leaflet and Google Fonts not packaged locally; fallback prevents a hard map crash, but complete offline geographic map requires licensed vendor files. No font binaries included.
- Crop photos are still partly remote Unsplash links: licensing and local attribution require review by the team.
- Browser's local network is blocked in the build environment, so pixel-level interface verification could not be performed; human should test at 360/768/1366/1920 px.
- Prompted 3-language interface updates are largely implemented for new NASA views; technical labels and some legacy screens still require native Tajik review.
- Cloud Python stdlib server still needs production security review before a high-traffic public launch. No cloud uptime SLA on free tier.
- Owner must decide repo licence and image re-distribution rights before publication.

## Practical pre-jury action list

1. Run `py -3 server.py`, check welcome/demo/Science & AI and GIS fallback with network disabled.
2. On an Internet-connected machine execute `py -3 scripts/refresh_snapshots.py`, inspect all real JSON responses and dates.
3. Validate POWER vs a real Nebraska Mesonet/NOAA station; fill `docs/validation_report.md` with actual results.
4. Verify GIBS layer/tile date and MODIS subset outputs, ground pixels and QA; do not show false conclusions.
5. Replace external illustrations with licensed sourced photos and review all Tajik text.
6. Deploy using `render.yaml` or another host; verify external URL, HTTPS and mobile loading. Free Render spins down after inactivity; plan for a judge-safe available deployment.
7. Test AI claims with slide deck: label template as template, do not call it LLM when no LLM was used.
