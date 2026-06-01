import pandas as pd
import pdfplumber
import io
import json
from typing import Union


def parse_csv(file_bytes: bytes) -> dict:
    df = pd.read_csv(io.BytesIO(file_bytes))
    df.columns = df.columns.str.strip()

    summary = {
        "total_records": len(df),
        "columns": list(df.columns),
        "date_range": "",
        "products": [],
        "categories": [],
        "regions": [],
        "total_revenue": 0.0,
        "total_profit": 0.0,
        "total_units": 0,
        "avg_rating": 0.0,
        "total_returns": 0,
        "product_performance": [],
        "regional_performance": [],
        "category_performance": [],
        "reviews": [],
        "raw_preview": df.head(10).to_string(),
    }

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        summary["date_range"] = f"{df['Date'].min().date()} to {df['Date'].max().date()}"

    numeric_map = {
        "Revenue_USD": "total_revenue",
        "Profit_USD": "total_profit",
        "Units_Sold": "total_units",
        "Returns": "total_returns",
    }
    for col, key in numeric_map.items():
        if col in df.columns:
            summary[key] = round(float(df[col].sum()), 2)

    if "Customer_Rating" in df.columns:
        summary["avg_rating"] = round(float(df["Customer_Rating"].mean()), 2)

    for col, key in [("Product_Name", "products"), ("Category", "categories"), ("Region", "regions")]:
        if col in df.columns:
            summary[key] = sorted(df[col].dropna().unique().tolist())

    if "Product_Name" in df.columns:
        grp_cols = ["Product_Name"]
        agg = {}
        for c in ["Revenue_USD", "Profit_USD", "Units_Sold", "Marketing_Spend_USD", "Returns", "Customer_Rating"]:
            if c in df.columns:
                agg[c] = "sum" if c != "Customer_Rating" else "mean"
        prod_perf = df.groupby(grp_cols).agg(agg).reset_index()
        prod_perf = prod_perf.sort_values("Revenue_USD", ascending=False) if "Revenue_USD" in prod_perf else prod_perf
        summary["product_performance"] = json.loads(prod_perf.round(2).to_json(orient="records"))

    if "Region" in df.columns:
        agg_r = {}
        for c in ["Revenue_USD", "Profit_USD", "Units_Sold"]:
            if c in df.columns:
                agg_r[c] = "sum"
        reg_perf = df.groupby("Region").agg(agg_r).reset_index()
        summary["regional_performance"] = json.loads(reg_perf.round(2).to_json(orient="records"))

    if "Category" in df.columns:
        agg_c = {}
        for c in ["Revenue_USD", "Profit_USD", "Units_Sold"]:
            if c in df.columns:
                agg_c[c] = "sum"
        cat_perf = df.groupby("Category").agg(agg_c).reset_index()
        summary["category_performance"] = json.loads(cat_perf.round(2).to_json(orient="records"))

    if "Review" in df.columns:
        reviews = df["Review"].dropna().tolist()
        if "Product_Name" in df.columns:
            summary["reviews"] = [
                {"product": row["Product_Name"], "review": row["Review"], "rating": row.get("Customer_Rating", "")}
                for _, row in df[["Product_Name", "Review", "Customer_Rating"]].dropna().iterrows()
            ]
        else:
            summary["reviews"] = [{"review": r} for r in reviews]

    summary["dataframe_json"] = df.to_json(orient="records", date_format="iso")
    return summary


def parse_pdf(file_bytes: bytes) -> dict:
    text_chunks = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_chunks.append(text.strip())
    full_text = "\n\n".join(text_chunks)
    return {
        "type": "pdf",
        "pages": len(text_chunks),
        "full_text": full_text,
        "preview": full_text[:2000],
    }


def parse_text(file_bytes: bytes) -> dict:
    text = file_bytes.decode("utf-8", errors="ignore")
    return {
        "type": "text",
        "full_text": text,
        "preview": text[:2000],
    }


def parse_uploaded_file(filename: str, file_bytes: bytes) -> dict:
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext == "csv":
        result = parse_csv(file_bytes)
        result["type"] = "csv"
        result["filename"] = filename
    elif ext == "pdf":
        result = parse_pdf(file_bytes)
        result["filename"] = filename
    else:
        result = parse_text(file_bytes)
        result["filename"] = filename
    return result


def build_context_string(parsed_data: list[dict]) -> str:
    parts = []
    for d in parsed_data:
        fname = d.get("filename", "unknown")
        dtype = d.get("type", "unknown")
        if dtype == "csv":
            parts.append(
                f"=== FILE: {fname} (Sales Data CSV) ===\n"
                f"Records: {d.get('total_records', 0)} | Date Range: {d.get('date_range', 'N/A')}\n"
                f"Products: {', '.join(d.get('products', []))}\n"
                f"Categories: {', '.join(d.get('categories', []))}\n"
                f"Regions: {', '.join(d.get('regions', []))}\n"
                f"Total Revenue: ${d.get('total_revenue', 0):,.2f}\n"
                f"Total Profit: ${d.get('total_profit', 0):,.2f}\n"
                f"Total Units Sold: {d.get('total_units', 0):,}\n"
                f"Avg Customer Rating: {d.get('avg_rating', 0)}/5\n"
                f"Total Returns: {d.get('total_returns', 0)}\n\n"
                f"Product Performance (by Revenue):\n"
                + "\n".join(
                    f"  - {p.get('Product_Name')}: Revenue=${p.get('Revenue_USD', 0):,.0f}, "
                    f"Profit=${p.get('Profit_USD', 0):,.0f}, Units={p.get('Units_Sold', 0)}, "
                    f"Rating={round(p.get('Customer_Rating', 0), 2)}"
                    for p in d.get("product_performance", [])
                )
                + f"\n\nSample Reviews:\n"
                + "\n".join(
                    f"  [{r.get('product', '')}] {r.get('review', '')} (Rating: {r.get('rating', '')})"
                    for r in d.get("reviews", [])[:20]
                )
            )
        else:
            parts.append(
                f"=== FILE: {fname} ({dtype.upper()}) ===\n"
                f"{d.get('preview', d.get('full_text', ''))[:3000]}"
            )
    return "\n\n".join(parts)
