from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]


def _load_json(path: Path) -> Dict[str, Any] | List[Dict[str, Any]]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _as_currency(value: float) -> str:
    return f"{value:,.2f}"


def _as_percent(value: float) -> str:
    return f"{value:.2f}%"


def main() -> None:
    st.set_page_config(page_title="Retail Business Dashboard", layout="wide")
    st.title("Retail Store Intelligence Dashboard")

    store_metrics_path = BASE_DIR / "outputs" / "analytics" / "store_metrics.json"
    funnel_path = BASE_DIR / "outputs" / "analytics" / "funnel.json"
    conversion_path = BASE_DIR / "outputs" / "analytics" / "conversion_report.json"
    product_metrics_path = BASE_DIR / "outputs" / "analytics" / "product_metrics.json"
    zone_summary_path = BASE_DIR / "outputs" / "events" / "zone_summary.json"

    store_metrics = _load_json(store_metrics_path)
    funnel = _load_json(funnel_path)
    conversion = _load_json(conversion_path)
    product_metrics = _load_json(product_metrics_path)
    zone_summary = _load_json(zone_summary_path)

    if not store_metrics or not funnel or not conversion or not product_metrics:
        st.error(
            "One or more analytics files are missing. Run scripts/run_analytics.py and scripts/run_pos_analytics.py first."
        )
        st.stop()

    st.subheader("1) Visitor Metrics")
    c1, c2, c3 = st.columns(3)
    c1.metric("Unique Visitors", int(store_metrics.get("unique_visitors", 0)))
    c2.metric("Avg Visit Duration", f"{store_metrics.get('avg_visit_duration', 0):.2f}")
    c3.metric("Avg Zone Count", f"{store_metrics.get('avg_zone_count', 0):.2f}")

    st.subheader("2) Entries / Exits")
    c4, c5 = st.columns(2)
    c4.metric("Entries", int(funnel.get("entries", 0)))
    c5.metric("Exits", int(funnel.get("exits", 0)))

    st.subheader("3) Revenue")
    c6, c7 = st.columns(2)
    c6.metric("Total Revenue", _as_currency(float(conversion.get("total_revenue", 0.0))))
    c7.metric("Average Order Value", _as_currency(float(conversion.get("average_order_value", 0.0))))

    st.subheader("4) Conversion Rate")
    c8, c9, c10 = st.columns(3)
    c8.metric("Transactions", int(conversion.get("transactions", 0)))
    c9.metric("Unique Visitors", int(conversion.get("unique_visitors", 0)))
    c10.metric("Conversion Rate", _as_percent(float(conversion.get("conversion_rate", 0.0))))

    st.subheader("5) Top Products")
    top_products = pd.DataFrame(product_metrics.get("top_10_products", []))
    if not top_products.empty:
        st.dataframe(top_products, use_container_width=True)
    else:
        st.info("No product metrics available.")

    st.subheader("6) Top Brands")
    top_brands = pd.DataFrame(product_metrics.get("top_10_brands", []))
    if not top_brands.empty:
        st.dataframe(top_brands, use_container_width=True)
    else:
        st.info("No brand metrics available.")

    st.subheader("7) Funnel Visualization")
    funnel_df = pd.DataFrame(
        [
            {"stage": "Entries", "value": int(funnel.get("entries", 0))},
            {"stage": "Zone Visits", "value": int(funnel.get("zone_visits", 0))},
            {"stage": "Billing Zone Visits", "value": int(funnel.get("billing_zone_visits", 0))},
            {"stage": "Exits", "value": int(funnel.get("exits", 0))},
        ]
    )
    st.bar_chart(funnel_df.set_index("stage"))
    st.dataframe(funnel_df, use_container_width=True)

    st.subheader("8) Zone Statistics")
    col_a, col_b = st.columns(2)
    most_zone = store_metrics.get("most_visited_zone") or {}
    least_zone = store_metrics.get("least_visited_zone") or {}
    col_a.metric(
        "Most Visited Zone",
        f"{most_zone.get('zone_id', 'N/A')} ({most_zone.get('visits', 0)})",
    )
    col_b.metric(
        "Least Visited Zone",
        f"{least_zone.get('zone_id', 'N/A')} ({least_zone.get('visits', 0)})",
    )

    if isinstance(zone_summary, list) and zone_summary:
        zone_df = pd.DataFrame(zone_summary)
        st.write("Detailed Zone Summary")
        st.dataframe(zone_df, use_container_width=True)
        if "visits" in zone_df.columns:
            st.bar_chart(zone_df.set_index("zone_id")["visits"])
    else:
        st.info("Detailed zone summary file not found at outputs/events/zone_summary.json.")


if __name__ == "__main__":
    main()
