# Design Document

## 1. System Architecture

The system is designed as a modular analytics pipeline with optional API/dashboard surfaces.

Data flow:
1. CCTV video files are ingested.
2. Detection + tracking produce per-frame visitor trajectories.
3. Session manager emits ENTRY/EXIT lifecycle events.
4. Zone mapper and zone event generator emit ZONE_ENTER/ZONE_EXIT/ZONE_DWELL.
5. Analytics modules generate journeys, funnel, and store metrics.
6. POS parser and product analytics compute transaction/business KPIs.
7. Streamlit dashboard renders operational + business metrics.

## 2. Detection Pipeline

- Detector: YOLO-based person detection.
- Output per frame includes bounding boxes and confidence scores.
- Frame metadata includes frame index and derived timestamp.

## 3. Tracking Pipeline

- Tracks person identities across frames using track IDs.
- Produces `outputs/tracking/tracking_results.json` and annotated frame images.
- Enables downstream session/event analytics.

## 4. Event Generation

- Session manager tracks per-visitor/per-camera state.
- ENTRY event emitted when a new session is observed.
- EXIT event emitted when session timeout/absence threshold is reached.
- Output: `outputs/events/events.jsonl`.

## 5. Zone Analytics

- Layout parser extracts zone polygons from store layout artifacts.
- Zone mapper maps bbox center to polygon membership.
- Zone event generator emits:
  - `ZONE_ENTER`
  - `ZONE_EXIT`
  - `ZONE_DWELL` (threshold-based)
- Outputs:
  - `outputs/events/zone_events.jsonl`
  - `outputs/events/zone_summary.json`

## 6. POS Correlation and Business Analytics

- POS parser reads transaction CSV and standardizes fields:
  - transaction id, timestamp, amount, quantity, product, brand
- Product analytics computes top products/brands and revenue breakdowns.
- Conversion analytics combines POS transactions with visitor counts:
  - `conversion_rate = transactions / unique_visitors * 100`
- Outputs:
  - `outputs/analytics/pos_summary.json`
  - `outputs/analytics/product_metrics.json`
  - `outputs/analytics/conversion_report.json`
  - `outputs/analytics/final_pos_analytics_report.json`

## 7. Dashboard

- Streamlit dashboard file: `dashboard/app.py`
- Reads analytics JSON files and displays:
  - visitor metrics
  - entries/exits
  - revenue and AOV
  - conversion rate
  - top products/brands
  - funnel chart
  - zone statistics
