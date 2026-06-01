Outputs demo index
==================

This folder lists curated demo artifacts that reviewers can inspect without downloading large CCTV datasets or model weights.

Included (references to files under `outputs/`):

- Detection samples:
  - `outputs/debug/CAM 1_detection.jpg`
  - `outputs/debug/CAM 2_detection.jpg`
  - `outputs/debug/CAM 3_detection.jpg`
  - `outputs/debug/CAM 4_detection.jpg`
  - `outputs/debug/CAM 5_detection.jpg`
  - `outputs/debug/first_detection.jpg`

- Tracking samples:
  - `outputs/tracking/CAM 1/frame_0001.jpg`
  - `outputs/tracking/CAM 1/frame_0050.jpg`
  - `outputs/tracking/CAM 1/frame_0100.jpg`

- Zone visualization:
  - `outputs/layout/zones_visualized.png`
  - `outputs/layout/zones_overlay.png`

- POS gallery samples:
  - `outputs/debug/pos_gallery/01_None_trk2_f1.png` (and related images)

- Dashboard screenshot:
  - `outputs/debug/dashboard_screenshot.png` (if present)

Notes:
- If any of the referenced files are missing, regenerate demo outputs by running the related scripts in `scripts/` (see project README for commands). The pipeline will process a small sample by default.
- We intentionally do not include raw CCTV videos, raw datasets, or model weights in the submission.
