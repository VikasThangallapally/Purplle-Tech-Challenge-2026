import json
from pathlib import Path

from analytics.pos_parser import parse_pos_csv, write_pos_summary
from analytics.product_metrics import build_product_metrics, write_product_metrics


def load_unique_visitors(path: str = "outputs/analytics/store_metrics.json") -> int:
    p = Path(path)
    if not p.exists():
        return 0
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return int(data.get("unique_visitors", 0))


def build_conversion_report(pos_summary: dict, unique_visitors: int) -> dict:
    transactions = int(pos_summary.get("total_transactions", 0))
    total_revenue = float(pos_summary.get("total_revenue", 0.0))
    average_order_value = float(pos_summary.get("average_order_value", 0.0))
    conversion_rate = (transactions / unique_visitors) * 100.0 if unique_visitors > 0 else 0.0
    return {
        "unique_visitors": unique_visitors,
        "transactions": transactions,
        "conversion_rate": conversion_rate,
        "total_revenue": total_revenue,
        "average_order_value": average_order_value,
    }


def validate_report(parsed: dict, conversion_report: dict) -> dict:
    summary = parsed["summary"]
    revenue_ok = summary.get("total_revenue", 0) > 0
    transactions_ok = summary.get("total_transactions", 0) > 0

    uv = conversion_report.get("unique_visitors", 0)
    tx = conversion_report.get("transactions", 0)
    expected_rate = (tx / uv) * 100.0 if uv > 0 else 0.0
    conversion_ok = abs(expected_rate - conversion_report.get("conversion_rate", 0.0)) < 1e-9

    no_duplicate_transactions = summary.get("duplicate_line_count", 0) == 0

    return {
        "revenue_gt_zero": revenue_ok,
        "transactions_gt_zero": transactions_ok,
        "conversion_rate_valid": conversion_ok,
        "no_duplicate_transactions": no_duplicate_transactions,
        "duplicate_line_count": summary.get("duplicate_line_count", 0),
    }


def main():
    parsed = parse_pos_csv()
    write_pos_summary(parsed)

    product_metrics = build_product_metrics(parsed["rows"])
    write_product_metrics(product_metrics)

    unique_visitors = load_unique_visitors()
    conversion_report = build_conversion_report(parsed["summary"], unique_visitors)

    out_conversion = Path("outputs/analytics/conversion_report.json")
    out_conversion.parent.mkdir(parents=True, exist_ok=True)
    with out_conversion.open("w", encoding="utf-8") as f:
        json.dump(conversion_report, f, indent=2)

    validation = validate_report(parsed, conversion_report)
    final_report = {
        "pos_summary": parsed["summary"],
        "conversion_report": conversion_report,
        "validation": validation,
    }
    out_final = Path("outputs/analytics/final_pos_analytics_report.json")
    with out_final.open("w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2)

    # Print summary
    print("Visitors:", conversion_report["unique_visitors"])
    print("Transactions:", conversion_report["transactions"])
    print("Revenue:", round(conversion_report["total_revenue"], 2))
    print("Conversion Rate:", round(conversion_report["conversion_rate"], 2))
    print("Average Order Value:", round(conversion_report["average_order_value"], 2))
    print("Validation:", validation)


if __name__ == "__main__":
    main()
