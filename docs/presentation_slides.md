# Presentation-ready, verified-claim-safe slide notes

## Use of AI
- AI coding assistance has been used during development; all generated code and translations need team review.
- The site reads NASA POWER/ORNL data through documented APIs; satellite measurements **are not** AI-generated.
- Growing-degree-days and climate similarity are deterministic calculations, not AI forecasts.
- Current assistant is **template mode** and labels itself accordingly. No LLM provider is configured; do NOT describe it as an autonomous AI advisor.
- AI imagery and stock imagery must be identified per image after team licence verification.

## NASA data used
- NASA POWER Daily Point API: historical daily T2M, Tmax/Tmin, precipitation; derived GDD and frost indicators. Requires live network.
- NASA GIBS: MODIS Terra true-colour historical tile overlay, accessible when CDN/maps are available; not an NDVI value.
- NASA ORNL DAAC MODIS MOD13Q1: experimental point NDVI series; 250m mixed pixels and QA flags have not been validated.

## Validity
- GDD: clamp Tmax/Tmin to 10–30 °C and sum max(0, (Tmax+Tmin)/2 − 10) for corn.
- Frost indicator: daily minimum ≤0 °C; spatial grid versus actual field conditions must be checked.
- Ground-station bias/MAE/RMSE **not measured yet**. Source comparison remains pending.

## Creativity
- Climate Twin compares transparent scaled features from real NASA model estimates at an official US research station and a labelled Tajik regional reference point. It is an **uncalibrated heuristic**, not crop suitability.

## Impact
- Accessible, public agronomic data exploration with no login and transparent limitations.
- Pilot: South Central Agricultural Laboratory reference point in Nebraska.
- Never claim improved yield, verified farm-scale NDVI or calculated fertilizer application rates.
