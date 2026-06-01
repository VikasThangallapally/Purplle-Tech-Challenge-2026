import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List


def build_product_metrics(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    product_qty = defaultdict(int)
    product_rev = defaultdict(float)
    brand_qty = defaultdict(int)
    brand_rev = defaultdict(float)

    for r in rows:
        product = r.get("product") or "UNKNOWN"
        brand = r.get("brand") or "UNKNOWN"
        qty = int(r.get("quantity") or 0)
        amount = float(r.get("amount") or 0.0)
        product_qty[product] += qty
        product_rev[product] += amount
        brand_qty[brand] += qty
        brand_rev[brand] += amount

    top_products = [
        {"product": k, "quantity": v}
        for k, v in sorted(product_qty.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
    top_brands = [
        {"brand": k, "quantity": v}
        for k, v in sorted(brand_qty.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
    revenue_by_product = [
        {"product": k, "revenue": v}
        for k, v in sorted(product_rev.items(), key=lambda x: x[1], reverse=True)[:10]
    ]
    revenue_by_brand = [
        {"brand": k, "revenue": v}
        for k, v in sorted(brand_rev.items(), key=lambda x: x[1], reverse=True)[:10]
    ]

    return {
        "top_10_products": top_products,
        "top_10_brands": top_brands,
        "revenue_by_product": revenue_by_product,
        "revenue_by_brand": revenue_by_brand,
    }


def write_product_metrics(metrics: Dict[str, Any], out_path: str = "outputs/analytics/product_metrics.json") -> None:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
