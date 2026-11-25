"""Descarga en vivo la planilla de Rentabilidad por Producto de Joyería Pietra."""

import csv
import io
import json
import os
import re
import unicodedata
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PROFIT_SHEET_ID = "12lJn3u08VZYBtZPTv3mdyj5ikAyRyqNDe6MZFvic9uw"


def norm_text(s: str) -> str:
    s = unicodedata.normalize("NFKD", (s or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def parse_ar_num(v: str) -> float:
    if not v:
        return 0.0
    s = str(v).strip().replace("$", "").replace("%", "").replace("x", "").replace(" ", "")
    # Formato argentino: 1.234,56 -> 1234.56
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    elif s.count(".") == 1 and len(s.split(".")[1]) == 3:
        s = s.replace(".", "")
    elif s.count(".") > 1:
        s = s.replace(".", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def main() -> None:
    sheet_id = os.environ.get("PROFIT_SHEET_ID", DEFAULT_PROFIT_SHEET_ID).strip()
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
    print(f"Descargando planilla de Rentabilidad ({sheet_id})...")
    req = urllib.request.Request(url, headers={"User-Agent": "PietraDashboard/2.0"})
    with urllib.request.urlopen(req, timeout=25) as resp:
        text = resp.read().decode("utf-8-sig")

    lines = list(csv.reader(io.StringIO(text)))
    # Buscar fila de encabezados ("Código" y "Producto")
    hdr_idx = -1
    for i, row in enumerate(lines[:15]):
        if len(row) >= 4 and "producto" in (row[1] or "").lower() and "categor" in (row[2] or "").lower():
            hdr_idx = i
            break
    if hdr_idx < 0:
        raise RuntimeError("No se encontró el encabezado de Rentabilidad en la planilla.")

    completed_count = 0
    total_catalog = 0
    for row in lines[:hdr_idx]:
        if len(row) >= 5 and "productos completos" in (row[0] or "").lower():
            completed_count = int(parse_ar_num(row[2]))
            total_catalog = int(parse_ar_num(row[4]))

    products = []
    margins = []
    be_list = []

    for row in lines[hdr_idx + 1 :]:
        if len(row) < 12 or not row[1].strip():
            continue
        code = (row[0] or "").strip()
        name = (row[1] or "").strip()
        cat = (row[2] or "").strip()
        grp = (row[3] or "").strip()
        price = parse_ar_num(row[4])
        contrib = parse_ar_num(row[5])
        margin = parse_ar_num(row[6])
        be = parse_ar_num(row[7])
        vel = parse_ar_num(row[11])
        stock_raw = (row[13] if len(row) > 13 else "").strip()
        stock = int(parse_ar_num(stock_raw)) if stock_raw != "" else None
        status = (row[14] if len(row) > 14 else "").strip()

        if margin > 0:
            margins.append(margin)
        if be > 0:
            be_list.append(be)

        products.append({
            "code": code,
            "name": name,
            "norm": norm_text(name),
            "cat": cat,
            "grp": grp,
            "price": round(price, 2),
            "contrib": round(contrib, 2),
            "margin": round(margin, 2),
            "be_roas": round(be, 2),
            "vel": round(vel, 1),
            "stock": stock,
            "status": status,
        })

    avg_margin = round(sum(margins) / len(margins), 2) if margins else 0.0
    avg_be = round(sum(be_list) / len(be_list), 2) if be_list else 0.0
    low_stock = sorted(
        [p for p in products if p["vel"] >= 3 and p["stock"] is not None and p["stock"] <= 10],
        key=lambda x: (-x["vel"], x["stock"]),
    )

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "sheet_id": sheet_id,
        "completed_count": completed_count or len(products),
        "total_catalog": total_catalog,
        "avg_margin": avg_margin,
        "avg_be_roas": avg_be,
        "low_stock_alerts": low_stock[:12],
        "products": products,
    }

    data_dir = BASE_DIR / "data"
    data_dir.mkdir(exist_ok=True)
    out_file = data_dir / "profitability.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(
        f"Guardado {out_file} | productos={len(products)} | margen_prom={avg_margin}% | roas_eq={avg_be}x | alertas_stock={len(low_stock)}"
    )


if __name__ == "__main__":
    main()
