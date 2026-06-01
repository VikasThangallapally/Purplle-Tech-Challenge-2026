def classify_anomaly(queue_length: int, dwell_seconds: float) -> str | None:
    if queue_length >= 10:
        return "queue_spike"
    if dwell_seconds >= 900:
        return "long_dwell"
    return None
