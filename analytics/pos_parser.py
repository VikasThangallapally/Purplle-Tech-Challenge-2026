import csv
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def _to_float(value: Any) -> float:
    try:
        if value is None or value == "":
            return 0.0
        return float(str(value).replace(",", ""))
    except Exception:
        return 0.0


def _to_int(value: Any) -> int:
    try:
        if value is None or value == "":
            return 0
        return int(float(str(value).replace(",", "")))
    except Exception:
        return 0


def _parse_timestamp(order_date: str, order_time: str) -> Optional[str]:
    if not order_date and not order_time:
        return None
    raw = f"{order_date} {order_time}".strip()
    for fmt in ["%d-%m-%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"]:
        try:
            return datetime.strptime(raw, fmt).isoformat()
        except Exception:
            continue
    return raw


def resolve_pos_csv_path(explicit_path: Optional[str] = None) -> Path:
    if explicit_path:
        p = Path(explicit_path)
        if p.exists():
            return p
    candidates = sorted(Path(".").glob("Brigade_Bangalore_10_April_26*.csv"))
    if candidates:
        return candidates[0]
    raise FileNotFoundError("Could not find POS CSV matching Brigade_Bangalore_10_April_26*.csv")


def parse_pos_csv(csv_path: Optional[str] = None) -> Dict[str, Any]:
    path = resolve_pos_csv_path(csv_path)
    rows: List[Dict[str, Any]] = []

    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            transaction_id = (r.get("invoice_number") or r.get("order_id") or "").strip()
            timestamp = _parse_timestamp(r.get("order_date", "").strip(), r.get("order_time", "").strip())
            qty = _to_int(r.get("qty"))
            amount = _to_float(r.get("total_amount"))
            product = (r.get("product_name") or "").strip()
            brand = (r.get("brand_name") or "").strip()
            rows.append(
                {
                    "transaction_id": transaction_id,
                    "timestamp": timestamp,
                    "amount": amount,
                    "quantity": qty,
                    "product": product,
                    "brand": brand,
                }
            )

    transaction_ids = [r["transaction_id"] for r in rows if r["transaction_id"]]
    unique_transaction_ids = set(transaction_ids)
    total_transactions = len(unique_transaction_ids)
    total_revenue = sum(r["amount"] for r in rows)
    total_items_sold = sum(r["quantity"] for r in rows)
    average_order_value = (total_revenue / total_transactions) if total_transactions else 0.0

    exact_row_keys = [
        (r["transaction_id"], r["timestamp"], r["product"], r["brand"], r["quantity"], r["amount"])
        for r in rows
    ]
    duplicate_line_count = len(exact_row_keys) - len(set(exact_row_keys))

    parsed = {
        "csv_path": str(path),
        "rows": rows,
        "summary": {
            "total_transactions": total_transactions,
            "total_revenue": total_revenue,
            "average_order_value": average_order_value,
            "total_items_sold": total_items_sold,
            "duplicate_line_count": duplicate_line_count,
        },
    }
    return parsed


def write_pos_summary(parsed: Dict[str, Any], out_path: str = "outputs/analytics/pos_summary.json") -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(parsed["summary"], f, indent=2)
