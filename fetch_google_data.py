"""Descarga las 4 pestañas diarias del Google Sheet de Google Ads y guarda data/google_ads.json."""

import csv
import io
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SHEET_ID = "1nRWkUGnENJzFJDowZQDinW1aMvCT7rbFYKKEJ_ud9fw"


def load_env(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def fetch_sheet_csv(sheet_id: str, tab_name: str) -> list[dict]:
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?" + urllib.parse.urlencode({"tqx": "out:csv", "sheet": tab_name})
    req = urllib.request.Request(url, headers={"User-Agent": "PietraDashboard/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            text = resp.read().decode("utf-8-sig")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Error HTTP {exc.code} leyendo pestaña '{tab_name}'") from exc
    if text.lstrip().startswith("<!DOCTYPE html"):
        raise RuntimeError(f"El Sheet devolvió HTML de login en '{tab_name}'. Verificá acceso Lector.")
    return list(csv.DictReader(io.StringIO(text)))


def sf(v) -> float:
    if v is None:
        return 0.0
    try:
        return float(str(v).strip().replace(",", ""))
    except ValueError:
        return 0.0


def main() -> None:
    load_env(BASE_DIR / ".env")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID", DEFAULT_SHEET_ID).strip()

    print(f"Descargando Google Ads diario desde Sheet ({sheet_id})...")
    camps_raw = fetch_sheet_csv(sheet_id, "Campañas_Diario")
    kw_raw = fetch_sheet_csv(sheet_id, "Keywords")
    prod_raw = fetch_sheet_csv(sheet_id, "Productos_PMax")

    daily_campaigns = [
        {
            "d": (r.get("segments.date") or "")[:10],
            "k": r.get("campaign.name", ""),
            "sp": round(sf(r.get("metrics.cost_micros")) / 1e6, 2),
            "im": int(sf(r.get("metrics.impressions"))),
            "cl": int(sf(r.get("metrics.clicks"))),
            "cv": round(sf(r.get("metrics.conversions")), 2),
            "rv": round(sf(r.get("metrics.conversions_value")), 2),
        }
        for r in camps_raw
        if (r.get("segments.date") or "")[:10]
    ]

    def fmt_kw(r: dict) -> str:
        t = r.get("ad_group_criterion.keyword.text", "")
        mt = (r.get("ad_group_criterion.keyword.match_type") or "").upper()
        return f"[{t}]" if mt == "EXACT" else (f'"{t}"' if mt == "PHRASE" else t)

    daily_keywords = [
        {
            "d": (r.get("segments.date") or "")[:10],
            "k": fmt_kw(r),
            "sp": round(sf(r.get("metrics.cost_micros")) / 1e6, 2),
            "cl": int(sf(r.get("metrics.clicks"))),
            "cv": round(sf(r.get("metrics.conversions")), 2),
            "rv": round(sf(r.get("metrics.conversions_value")), 2),
        }
        for r in kw_raw
        if sf(r.get("metrics.clicks")) > 0
    ]

    daily_products = [
        {
            "d": (r.get("segments.date") or "")[:10],
            "k": r.get("segments.product_title", "(Sin título)"),
            "sp": round(sf(r.get("metrics.cost_micros")) / 1e6, 2),
            "cl": int(sf(r.get("metrics.clicks"))),
            "cv": round(sf(r.get("metrics.conversions")), 2),
            "rv": round(sf(r.get("metrics.conversions_value")), 2),
        }
        for r in prod_raw
        if sf(r.get("metrics.clicks")) > 0
    ]

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "sheet_id": sheet_id,
        "daily_campaigns": daily_campaigns,
        "daily_keywords": daily_keywords,
        "daily_products": daily_products,
    }
    data_dir = BASE_DIR / "data"
    data_dir.mkdir(exist_ok=True)
    out_file = data_dir / "google_ads.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    dates = sorted({x["d"] for x in daily_campaigns})
    print(f"Guardado {out_file} ({round(out_file.stat().st_size/1024, 1)} KB) | rango={dates[0] if dates else '-'}..{dates[-1] if dates else '-'}")


if __name__ == "__main__":
    main()
