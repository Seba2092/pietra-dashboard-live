"""Lee las 4 pestañas del Google Sheet de Google Ads y genera data/google_ads.json."""

import argparse
import csv
import io
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_SHEET_ID = "1nRWkUGnENJzFJDowZQDinW1aMvCT7rbFYKKEJ_ud9fw"

AGE_MAP = {
    "AGE_RANGE_18_24": "18-24",
    "AGE_RANGE_25_34": "25-34",
    "AGE_RANGE_35_44": "35-44",
    "AGE_RANGE_45_54": "45-54",
    "AGE_RANGE_55_64": "55-64",
    "AGE_RANGE_65_UP": "65+",
    "AGE_RANGE_UNDETERMINED": "Desconocido",
}


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
    url = (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?"
        + urllib.parse.urlencode({"tqx": "out:csv", "sheet": tab_name})
    )
    req = urllib.request.Request(url, headers={"User-Agent": "PietraDashboard/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            text = resp.read().decode("utf-8-sig")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(
            f"No se pudo leer la pestaña '{tab_name}' (HTTP {exc.code}). "
            "Verificá que el Google Sheet tenga acceso de 'Cualquier usuario con el vínculo: Lector'."
        ) from exc
    if text.lstrip().startswith("<!DOCTYPE html") or "<html" in text[:300].lower():
        raise RuntimeError(
            f"Google devolvió una página de login al pedir '{tab_name}'. "
            "Cambiá el acceso general del Sheet a 'Cualquier usuario que tenga el vínculo: Lector'."
        )
    return list(csv.DictReader(io.StringIO(text)))


def sf(v) -> float:
    if v is None:
        return 0.0
    s = str(v).strip().replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_cost(row: dict) -> float:
    if "metrics.cost_micros" in row:
        return sf(row["metrics.cost_micros"]) / 1_000_000.0
    return sf(row.get("cost"))


def summarize_bucket(rows: list[dict]) -> dict:
    spend = sum(parse_cost(r) for r in rows)
    impr = int(sum(sf(r.get("metrics.impressions")) for r in rows))
    clicks = int(sum(sf(r.get("metrics.clicks")) for r in rows))
    conv = sum(sf(r.get("metrics.conversions")) for r in rows)
    rev = sum(sf(r.get("metrics.conversions_value")) for r in rows)
    return {
        "spend": round(spend, 2),
        "impressions": impr,
        "clicks": clicks,
        "ctr": round((clicks / impr * 100) if impr else 0.0, 2),
        "cpc": round((spend / clicks) if clicks else 0.0, 2),
        "conversions": round(conv, 2),
        "cpa": round((spend / conv) if conv else 0.0, 2),
        "revenue": round(rev, 2),
        "roas": round((rev / spend) if spend else 0.0, 2),
    }


def filter_dates(rows: list[dict], start: str, end: str) -> list[dict]:
    return [r for r in rows if start <= (r.get("segments.date") or "")[:10] <= end]


def group_sum(rows: list[dict], key_fn, include_rev: bool = True) -> list[dict]:
    buckets: dict = defaultdict(list)
    for r in rows:
        buckets[key_fn(r)].append(r)
    out = []
    for k, grp in buckets.items():
        s = summarize_bucket(grp)
        if not include_rev:
            s.pop("revenue", None)
            s.pop("roas", None)
        out.append({"key": k, **s})
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cur-start", default="2026-10-01")
    parser.add_argument("--cur-end", default="2026-10-31")
    parser.add_argument("--prev-start", default="2026-09-20")
    parser.add_argument("--prev-end", default="2026-09-30")
    args = parser.parse_args()

    load_env(BASE_DIR / ".env")
    sheet_id = os.environ.get("GOOGLE_SHEET_ID", DEFAULT_SHEET_ID).strip()

    print(f"Descargando 4 pestañas desde Google Sheet ({sheet_id})...")
    camps_raw = fetch_sheet_csv(sheet_id, "Campañas_Diario")
    kw_raw = fetch_sheet_csv(sheet_id, "Keywords")
    age_raw = fetch_sheet_csv(sheet_id, "Edad")
    prod_raw = fetch_sheet_csv(sheet_id, "Productos_PMax")

    camps_cur = filter_dates(camps_raw, args.cur_start, args.cur_end)
    camps_prev = filter_dates(camps_raw, args.prev_start, args.prev_end)
    kw_cur = filter_dates(kw_raw, args.cur_start, args.cur_end)
    age_cur = filter_dates(age_raw, args.cur_start, args.cur_end)
    prod_cur = filter_dates(prod_raw, args.cur_start, args.cur_end)

    cur_campaigns = sorted(
        group_sum(camps_cur, lambda r: r.get("campaign.name", "")),
        key=lambda x: x["spend"],
        reverse=True,
    )
    prev_campaigns = sorted(
        group_sum(camps_prev, lambda r: r.get("campaign.name", "")),
        key=lambda x: x["spend"],
        reverse=True,
    )

    def fmt_kw(r: dict) -> str:
        txt = r.get("ad_group_criterion.keyword.text", "")
        mt = (r.get("ad_group_criterion.keyword.match_type") or "").upper()
        if mt == "EXACT":
            return f"[{txt}]"
        if mt == "PHRASE":
            return f'"{txt}"'
        return txt

    keywords = sorted(
        group_sum(kw_cur, fmt_kw),
        key=lambda x: x["spend"],
        reverse=True,
    )[:20]

    ages = sorted(
        group_sum(age_cur, lambda r: AGE_MAP.get(r.get("ad_group_criterion.age_range.type", ""), r.get("ad_group_criterion.age_range.type", "")), include_rev=False),
        key=lambda x: x["key"],
    )

    products = sorted(
        group_sum(prod_cur, lambda r: r.get("segments.product_title", "(Sin título)")),
        key=lambda x: (x["revenue"], x["conversions"]),
        reverse=True,
    )[:15]

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "sheet_id": sheet_id,
        "current": {
            "period": {"since": args.cur_start, "until": args.cur_end},
            "account": summarize_bucket(camps_cur),
            "campaigns": cur_campaigns,
            "keywords": keywords,
            "age": ages,
            "products": products,
        },
        "previous": {
            "period": {"since": args.prev_start, "until": args.prev_end},
            "account": summarize_bucket(camps_prev),
            "campaigns": prev_campaigns,
        },
    }

    data_dir = BASE_DIR / "data"
    data_dir.mkdir(exist_ok=True)
    out_file = data_dir / "google_ads.json"
    out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    ac = payload["current"]["account"]
    print("\n--- RESUMEN GOOGLE ADS DESDE SHEET ---")
    print(f"Filas leídas -> Campañas:{len(camps_raw)} | Keywords:{len(kw_raw)} | Edad:{len(age_raw)} | Productos:{len(prod_raw)}")
    print(f"Actual ({args.cur_start}..{args.cur_end}): Spend=${ac['spend']:,.2f} | Clicks={ac['clicks']} | Conv={ac['conversions']} | Rev=${ac['revenue']:,.2f} | ROAS={ac['roas']}x")
    print(f"Archivo guardado: {out_file}")


if __name__ == "__main__":
    main()
