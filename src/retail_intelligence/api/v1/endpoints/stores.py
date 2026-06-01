from datetime import datetime, timezone
import json
from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from retail_intelligence.api.deps import get_db
from retail_intelligence.application.use_cases.get_anomalies import GetStoreAnomaliesUseCase
from retail_intelligence.application.use_cases.get_funnel import GetStoreFunnelUseCase
from retail_intelligence.application.use_cases.get_heatmap import GetStoreHeatmapUseCase
from retail_intelligence.application.use_cases.get_store_metrics import GetStoreMetricsUseCase
from retail_intelligence.schemas.analytics import AnomalyResponse, FunnelResponse, HeatmapResponse
from retail_intelligence.schemas.metrics import StoreMetricsResponse

router = APIRouter(prefix="/stores/{store_id}", tags=["stores"])
PROJECT_ROOT = Path(__file__).resolve().parents[5]
ANALYTICS_DIR = PROJECT_ROOT / "outputs" / "analytics"
EVENTS_DIR = PROJECT_ROOT / "outputs" / "events"


def _load_json(path: Path) -> dict | list:
    with path.open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def _fallback_metrics(store_id: int) -> StoreMetricsResponse:
    store_metrics = _load_json(ANALYTICS_DIR / "store_metrics.json")
    funnel = _load_json(ANALYTICS_DIR / "funnel.json")
    conversion_report = _load_json(ANALYTICS_DIR / "conversion_report.json")

    billing_queue = int(funnel.get("billing_zone_visits", 0))
    purchases = int(conversion_report.get("transactions", 0))
    abandonment_rate = round(((billing_queue - purchases) / billing_queue) * 100.0, 2) if billing_queue > 0 else 0.0

    return StoreMetricsResponse(
        store_id=store_id,
        unique_visitors=int(store_metrics.get("unique_visitors", 0)),
        conversion_rate=float(conversion_report.get("conversion_rate", 0.0)),
        avg_dwell_time=float(store_metrics.get("avg_visit_duration", 0.0)),
        queue_depth=billing_queue,
        abandonment_rate=abandonment_rate,
    )


def _fallback_funnel(store_id: int) -> FunnelResponse:
    funnel = _load_json(ANALYTICS_DIR / "funnel.json")
    entry = int(funnel.get("entries", 0))
    zone_visit = int(funnel.get("zone_visits", 0))
    billing_queue = int(funnel.get("billing_zone_visits", 0))
    purchase = int(_load_json(ANALYTICS_DIR / "conversion_report.json").get("transactions", 0))

    def _dropoff(source: int, next_stage: int) -> float:
        if source <= 0:
            return 0.0
        return round(((source - next_stage) / source) * 100.0, 2)

    return FunnelResponse(
        store_id=store_id,
        entry=entry,
        zone_visit=zone_visit,
        billing_queue=billing_queue,
        purchase=purchase,
        dropoff_percentages={
            "entry_to_zone": _dropoff(entry, zone_visit),
            "zone_to_queue": _dropoff(zone_visit, billing_queue),
            "queue_to_purchase": _dropoff(billing_queue, purchase),
        },
    )


def _fallback_heatmap(store_id: int) -> HeatmapResponse:
    zone_summary = _load_json(EVENTS_DIR / "zone_summary.json")
    max_visits = max((int(zone.get("visits", 0)) for zone in zone_summary), default=0)

    zones = []
    for zone in zone_summary:
        visits = int(zone.get("visits", 0))
        normalized = int(round((visits / max_visits) * 100)) if max_visits > 0 else 0
        zones.append(
            {
                "zone_id": str(zone.get("zone_id", "UNKNOWN")),
                "visits": visits,
                "avg_dwell": round(float(zone.get("avg_dwell_ms", 0)) / 1000.0, 2),
                "normalized_score": normalized,
            }
        )

    zones.sort(key=lambda item: (-item["visits"], item["zone_id"]))
    return HeatmapResponse(store_id=store_id, zones=zones, data_confidence="LOW")


def _fallback_anomalies(store_id: int) -> AnomalyResponse:
    conversion_report = _load_json(ANALYTICS_DIR / "conversion_report.json")
    funnel = _load_json(ANALYTICS_DIR / "funnel.json")
    now_iso = datetime.now(timezone.utc).isoformat()

    anomalies = []
    conversion_rate = float(conversion_report.get("conversion_rate", 0.0))
    billing_zone_visits = int(funnel.get("billing_zone_visits", 0))

    if billing_zone_visits == 0:
        anomalies.append(
            {
                "type": "BILLING_FLOW_GAP",
                "severity": "WARN",
                "message": "No billing-zone visits observed in generated analytics output",
                "suggested_action": "Verify billing-zone mapping calibration and camera-to-layout alignment",
                "detected_at": now_iso,
            }
        )

    if conversion_rate < 30.0:
        anomalies.append(
            {
                "type": "LOW_CONVERSION",
                "severity": "CRITICAL",
                "message": f"Conversion rate is low at {conversion_rate:.2f}%",
                "suggested_action": "Review checkout flow and zone placement for product discoverability",
                "detected_at": now_iso,
            }
        )

    return AnomalyResponse(store_id=str(store_id), anomalies=anomalies)


@router.get("/metrics", response_model=StoreMetricsResponse)
def get_metrics(store_id: int, db: Session = Depends(get_db)) -> StoreMetricsResponse:
    try:
        return GetStoreMetricsUseCase(db=db).execute(store_id)
    except SQLAlchemyError:
        return _fallback_metrics(store_id)


@router.get("/funnel", response_model=FunnelResponse)
def get_funnel(store_id: int, db: Session = Depends(get_db)) -> FunnelResponse:
    try:
        return GetStoreFunnelUseCase(db=db).execute(store_id)
    except SQLAlchemyError:
        return _fallback_funnel(store_id)


@router.get("/heatmap", response_model=HeatmapResponse)
def get_heatmap(store_id: int, db: Session = Depends(get_db)) -> HeatmapResponse:
    try:
        return GetStoreHeatmapUseCase(db=db).execute(store_id)
    except SQLAlchemyError:
        return _fallback_heatmap(store_id)


@router.get("/anomalies", response_model=AnomalyResponse)
def get_anomalies(store_id: int, db: Session = Depends(get_db)) -> AnomalyResponse:
    try:
        return GetStoreAnomaliesUseCase(db=db).execute(store_id)
    except SQLAlchemyError:
        return _fallback_anomalies(store_id)
