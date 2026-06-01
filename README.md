# Retail Store Intelligence

AI-powered retail analytics project that combines CCTV detection/tracking signals with POS transactions to produce store operations and business conversion insights.

## Project overview

The project processes recorded CCTV camera videos, tracks visitor motion, generates behavioral events (ENTRY/EXIT and zone transitions), and fuses this with POS data for business KPIs.

Main outcomes:
- visitor/session analytics
- zone behavior analytics
- POS revenue and product analytics
- conversion analytics
- Streamlit dashboard for review

## Architecture

High-level flow:
1. CCTV video input
2. Detection + tracking pipeline
3. Session/event generation (ENTRY/EXIT, zone events)
4. Store analytics and journey/funnel metrics
5. POS CSV parsing and product/conversion analytics
6. Streamlit dashboard visualization

## Folder structure

- `pipeline/`: detection/tracking/event/zone processing modules
- `analytics/`: journey, funnel, store, POS, and product analytics logic
- `scripts/`: executable scripts for pipeline runs, validations, and reports
- `outputs/tracking/`: tracking outputs and annotated frames
- `outputs/events/`: events and zone events outputs
- `outputs/analytics/`: analytics JSON artifacts
- `outputs/debug/`: debug galleries and diagnostics
- `dashboard/`: standalone business Streamlit dashboard (`app.py`)
- `src/retail_intelligence/`: package-based API/application/infrastructure/dashboard modules
- `tests/`: unit/integration/API/pipeline tests

## Installation

Requirements:
- Python 3.11+

Install dependencies:

```bash
pip install -e .
```

Optional developer dependencies:

```bash
pip install -e .[dev]
```

## Run commands

Run core analytics pipeline scripts:

```bash
# Zone events
python scripts/run_zone_events.py

# Visitor/funnel/store analytics
python scripts/run_analytics.py

# POS + conversion analytics
python scripts/run_pos_analytics.py

# Submission validation report
python scripts/validate_submission.py
```

## Dashboard instructions

Run the business dashboard:

```bash
streamlit run dashboard/app.py
```

Default Streamlit URL:
- `http://localhost:8501`

## Key generated files

- `outputs/events/events.jsonl`
- `outputs/events/zone_events.jsonl`
- `outputs/analytics/journeys.json`
- `outputs/analytics/funnel.json`
- `outputs/analytics/store_metrics.json`
- `outputs/analytics/product_metrics.json`
- `outputs/analytics/conversion_report.json`
- `outputs/final_validation_report.json`

## Results (demo outputs)

For a quick review, curated representative outputs are collected in `outputs_demo/`. These files are small, easy to view, and let reviewers evaluate detection, tracking, zoning, POS, and dashboard visuals without downloading raw CCTV footage or model weights.

- Detection samples: [outputs_demo/detection/CAM 1_detection.jpg](outputs_demo/detection/CAM 1_detection.jpg), [outputs_demo/detection/CAM 2_detection.jpg](outputs_demo/detection/CAM 2_detection.jpg), [outputs_demo/detection/first_detection.jpg](outputs_demo/detection/first_detection.jpg)
- Tracking samples: [outputs_demo/tracking/frame_0050.jpg](outputs_demo/tracking/frame_0050.jpg), [outputs_demo/tracking/frame_0100.jpg](outputs_demo/tracking/frame_0100.jpg)
- Zone visualization: [outputs_demo/zones/zones_visualized.png](outputs_demo/zones/zones_visualized.png)
- POS gallery sample: [outputs_demo/pos_gallery/01_None_trk2_f1.png](outputs_demo/pos_gallery/01_None_trk2_f1.png)
- Dashboard screenshot: [outputs_demo/dashboard/dashboard_screenshot.png](outputs_demo/dashboard/dashboard_screenshot.png)

See [outputs_demo/README.md](outputs_demo/README.md) for a short index and instructions to regenerate demo outputs locally.
