import pytest

pytest.importorskip("sqlalchemy")

from retail_intelligence.application.services.analytics_service import AnalyticsService


def test_analytics_service_metrics_shape() -> None:
    service = AnalyticsService(db=object())
    metrics = service.metrics(store_id=1)
    assert metrics.store_id == 1
    assert metrics.conversion_rate == 0.0
