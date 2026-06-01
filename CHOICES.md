## Billing Zone Approximation

- `BILLING` is currently mapped from `ZONE_6` as a pragmatic approximation.
- The choice was made using POS-region sample extraction, nearest-zone ranking, and visual inspection of zone overlays.

## Known Limitation: Coordinate Mismatch

- CCTV detection coordinates and layout-zone coordinates are not fully calibrated.
- This mismatch can produce weak or zero billing-zone intersections even when checkout behavior is visible in camera frames.

## Future Improvement: Homography Calibration


## Current Known Limitations (short)

- Camera-to-layout mapping is approximate; zones are defined in layout pixel space and mapped naively to camera pixel coordinates.
- `BILLING` zone is a pragmatic approximation (renamed from `ZONE_6`) used for funnel/billing analytics; this should be recomputed after calibration.
- No cross-camera re-identification: visitor identities are local per-camera which affects REENTRY and multi-camera journeys.

## Recommended Next Steps

- Add a small interactive calibration script to collect correspondence points and compute homographies per camera.
- Re-run zone assignment and recompute funnel/checkout metrics after calibration.
- Optionally add appearance-reid for cross-camera matching.

## Change Log

- `outputs/layout/zones.json`: renamed `ZONE_6` to `BILLING`.
- Re-ran pipeline outputs after mapping update:
	- `outputs/events/zone_events.jsonl`
	- `outputs/analytics/funnel.json`
	- `outputs/analytics/store_metrics.json`