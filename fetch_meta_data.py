"""Extractor diario de Meta Marketing API + IG/FB Graph API (desde 2026-09-01 hasta hoy)."""

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AD_ACCOUNT_ID = "act_2169549460223989"
FB_PAGE_ID = "102684522836714"
IG_USER_ID = "17841400783739438"


def load_env(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def graph_get(endpoint: str, token: str, version: str, params: dict | None = None) -> dict:
    query = dict(params or {})
    query["access_token"] = token
    url = f"https://graph.facebook.com/{version}/{endpoint.lstrip('/')}?{urllib.parse.urlencode(query)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} en {endpoint}: {body}") from exc


def graph_get_all(endpoint: str, token: str, version: str, params: dict | None = None, max_pages: int = 25) -> list:
    data: list = []
    res = graph_get(endpoint, token, version, params)
    data.extend(res.get("data", []))
    pages = 1
    next_url = (res.get("paging") or {}).get("next")
    while next_url and pages < max_pages:
        req = urllib.request.Request(next_url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            res = json.loads(resp.read().decode("utf-8"))
        data.extend(res.get("data", []))
        next_url = (res.get("paging") or {}).get("next")
        pages += 1
    return data


def sf(val) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


def extract_action(actions: list | None, types: tuple[str, ...]) -> float:
    if not actions:
        return 0.0
    for target in types:
        for item in actions:
            if item.get("action_type") == target:
                return sf(item.get("value"))
    return 0.0


def compact_row(row: dict, extra_key: str | None = None) -> dict:
    actions = row.get("actions") or []
    avals = row.get("action_values") or []
    purch = extract_action(actions, ("purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"))
    rev = extract_action(avals, ("purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"))
    out = {
        "d": row.get("date_start", ""),
        "sp": round(sf(row.get("spend")), 2),
        "im": int(sf(row.get("impressions"))),
        "lc": int(sf(row.get("inline_link_clicks"))),
        "lp": int(extract_action(actions, ("landing_page_view", "omni_landing_page_view"))),
        "ac": int(extract_action(actions, ("add_to_cart", "omni_add_to_cart", "offsite_conversion.fb_pixel_add_to_cart"))),
        "ic": int(extract_action(actions, ("initiate_checkout", "omni_initiated_checkout", "offsite_conversion.fb_pixel_initiate_checkout"))),
        "p": int(purch) if purch == int(purch) else round(purch, 2),
        "rv": round(rev, 2),
    }
    if extra_key:
        out["k"] = row.get(extra_key, "")
    if "ad_id" in row:
        out["id"] = row["ad_id"]
    return out


def fetch_daily_series(token: str, version: str, since: str, until: str) -> dict:
    tr = json.dumps({"since": since, "until": until})
    f_full = "spend,impressions,inline_link_clicks,actions,action_values"

    print(f"  - Cuenta diaria ({since}..{until})...")
    acct_rows = graph_get_all(
        f"{AD_ACCOUNT_ID}/insights", token, version,
        {"time_range": tr, "time_increment": 1, "fields": f_full, "limit": 200},
    )
    daily_account = sorted([compact_row(r) for r in acct_rows], key=lambda x: x["d"])

    print("  - Campañas diarias...")
    camp_rows = graph_get_all(
        f"{AD_ACCOUNT_ID}/insights", token, version,
        {"time_range": tr, "time_increment": 1, "level": "campaign", "fields": f"campaign_name,{f_full}", "limit": 500},
    )
    daily_campaigns = [compact_row(r, "campaign_name") for r in camp_rows if sf(r.get("spend")) > 0]

    print("  - Anuncios diarios...")
    ad_rows = graph_get_all(
        f"{AD_ACCOUNT_ID}/insights", token, version,
        {"time_range": tr, "time_increment": 1, "level": "ad", "fields": f"ad_id,ad_name,{f_full}", "limit": 500},
    )
    daily_ads = [compact_row(r, "ad_name") for r in ad_rows if sf(r.get("spend")) > 0]

    print("  - Edad diaria...")
    age_rows = graph_get_all(
        f"{AD_ACCOUNT_ID}/insights", token, version,
        {"time_range": tr, "time_increment": 1, "breakdowns": "age", "fields": f_full, "limit": 500},
    )
    daily_age = [compact_row(r, "age") for r in age_rows if sf(r.get("spend")) > 0]

    print("  - Regiones (resumen período)...")
    reg_rows = graph_get_all(
        f"{AD_ACCOUNT_ID}/insights", token, version,
        {"time_range": tr, "breakdowns": "region", "fields": "spend,impressions,inline_link_clicks", "limit": 100},
    )
    regions = sorted(
        [{"region": r.get("region", ""), "spend": round(sf(r.get("spend")), 2), "clicks": int(sf(r.get("inline_link_clicks")))} for r in reg_rows],
        key=lambda x: x["spend"], reverse=True,
    )[:15]

    print("  - Miniaturas de anuncios...")
    ad_objs = graph_get_all(
        f"{AD_ACCOUNT_ID}/ads", token, version,
        {"fields": "id,creative{thumbnail_url,image_url}", "limit": 100},
        max_pages=3,
    )
    ad_thumbs = {}
    for obj in ad_objs:
        cr = obj.get("creative") or {}
        u = cr.get("thumbnail_url") or cr.get("image_url") or ""
        if u:
            ad_thumbs[obj["id"]] = u

    return {
        "since": since,
        "until": until,
        "daily_account": daily_account,
        "daily_campaigns": daily_campaigns,
        "daily_ads": daily_ads,
        "daily_age": daily_age,
        "regions": regions,
        "ad_thumbs": ad_thumbs,
    }


def fetch_instagram_organic(token: str, version: str, start: str, end: str) -> dict:
    profile = graph_get(IG_USER_ID, token, version, {"fields": "id,username,followers_count,follows_count,media_count"})
    dt_start = datetime.strptime(start, "%Y-%m-%d")
    dt_end = datetime.strptime(end, "%Y-%m-%d")
    chunks = []
    cur = dt_start
    while cur <= dt_end:
        nxt = min(dt_end, cur + timedelta(days=27))
        chunks.append((int(cur.timestamp()), int(nxt.timestamp()) + 86399))
        cur = nxt + timedelta(days=1)

    insights_summary = {}
    for metric in ("reach", "views", "accounts_engaged", "total_interactions"):
        try:
            total = 0
            for since_ts, until_ts in chunks:
                res = graph_get(
                    f"{IG_USER_ID}/insights", token, version,
                    {"metric": metric, "period": "day", "metric_type": "total_value", "since": since_ts, "until": until_ts},
                )
                data = res.get("data", [])
                if data:
                    total += int((data[0].get("total_value") or {}).get("value") or 0)
            insights_summary[metric] = total
        except Exception as exc:
            insights_summary[f"{metric}_error"] = str(exc)

    media_list = graph_get_all(
        f"{IG_USER_ID}/media", token, version,
        {"fields": "id,caption,media_type,media_product_type,timestamp,like_count,comments_count,permalink", "limit": 50},
        max_pages=2,
    )
    return {"profile": profile, "insights_summary": insights_summary, "media": media_list[:30]}


def fetch_facebook_organic(token: str, version: str) -> dict:
    page = graph_get(FB_PAGE_ID, token, version, {"fields": "id,name,fan_count,followers_count"})
    return {"page": page}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default="2026-09-01")
    parser.add_argument("--until", default=date.today().isoformat())
    args = parser.parse_args()

    load_env(BASE_DIR / ".env")
    token = os.environ.get("META_ACCESS_TOKEN", "").strip()
    version = os.environ.get("META_API_VERSION", "v21.0").strip() or "v21.0"
    if not token:
        raise SystemExit("Falta META_ACCESS_TOKEN")

    print(f"Extrayendo Meta Ads diario desde {args.since} hasta {args.until}...")
    meta_daily = fetch_daily_series(token, version, args.since, args.until)

    # Orgánico últimos 30 días
    org_start = (datetime.strptime(args.until, "%Y-%m-%d") - timedelta(days=29)).strftime("%Y-%m-%d")
    print(f"Extrayendo Orgánico IG/FB ({org_start}..{args.until})...")
    ig = fetch_instagram_organic(token, version, org_start, args.until)
    fb = fetch_facebook_organic(token, version)

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "meta_daily": meta_daily,
        "organic": {"instagram": ig, "facebook": fb, "period": {"since": org_start, "until": args.until}},
    }
    data_dir = BASE_DIR / "data"
    data_dir.mkdir(exist_ok=True)
    out_file = data_dir / "meta_daily.json"
    out_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"Guardado {out_file} ({round(out_file.stat().st_size/1024, 1)} KB) | días={len(meta_daily['daily_account'])}")


if __name__ == "__main__":
    main()
