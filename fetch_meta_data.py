"""Extractor de Meta Marketing API + Instagram/Facebook Graph API para Joyería Pietra."""

import argparse
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AD_ACCOUNT_ID = "act_2169549460223989"  # Joyería Pietra CP Nueva
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


def graph_get_all(endpoint: str, token: str, version: str, params: dict | None = None, max_pages: int = 10) -> list:
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


def safe_float(val, default=0.0) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def extract_action(actions: list | None, action_types: tuple[str, ...]) -> float:
    if not actions:
        return 0.0
    for target in action_types:
        for item in actions:
            if item.get("action_type") == target:
                return safe_float(item.get("value"))
    return 0.0


def normalize_insight_row(row: dict) -> dict:
    spend = safe_float(row.get("spend"))
    impr = int(safe_float(row.get("impressions")))
    reach = int(safe_float(row.get("reach")))
    link_clicks = int(safe_float(row.get("inline_link_clicks")))
    actions = row.get("actions") or []
    action_values = row.get("action_values") or []

    purchases = extract_action(actions, ("purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"))
    landing_views = extract_action(actions, ("landing_page_view", "omni_landing_page_view"))
    add_to_cart = extract_action(actions, ("add_to_cart", "omni_add_to_cart", "offsite_conversion.fb_pixel_add_to_cart"))
    checkout = extract_action(actions, ("initiate_checkout", "omni_initiated_checkout", "offsite_conversion.fb_pixel_initiate_checkout"))
    ig_visits = extract_action(actions, ("instagram_profile_visit",))
    revenue = extract_action(action_values, ("purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"))

    roas = (revenue / spend) if spend > 0 else 0.0
    cpa = (spend / purchases) if purchases > 0 else 0.0
    aov = (revenue / purchases) if purchases > 0 else 0.0
    ctr_link = (link_clicks / impr * 100) if impr > 0 else 0.0

    out = {
        "spend": round(spend, 2),
        "impressions": impr,
        "reach": reach,
        "frequency": round(safe_float(row.get("frequency")), 2),
        "link_clicks": link_clicks,
        "ctr_link": round(ctr_link, 2),
        "landing_views": int(landing_views),
        "add_to_cart": int(add_to_cart),
        "initiate_checkout": int(checkout),
        "purchases": int(purchases) if purchases == int(purchases) else round(purchases, 2),
        "ig_profile_visits": int(ig_visits),
        "revenue": round(revenue, 2),
        "roas": round(roas, 2),
        "cpa": round(cpa, 2),
        "aov": round(aov, 2),
    }
    for k in ("campaign_name", "campaign_id", "objective", "ad_name", "ad_id", "region", "age", "publisher_platform", "date_start", "date_stop"):
        if k in row:
            out[k] = row[k]
    return out


def fetch_ads_period(token: str, version: str, start: str, end: str, include_breakdowns: bool = True) -> dict:
    base_fields = "spend,impressions,reach,frequency,inline_link_clicks,actions,action_values"
    tr = json.dumps({"since": start, "until": end})

    acct_rows = graph_get(
        f"{AD_ACCOUNT_ID}/insights",
        token,
        version,
        {"time_range": tr, "fields": base_fields},
    ).get("data", [])
    account = normalize_insight_row(acct_rows[0]) if acct_rows else {}

    camp_rows = graph_get_all(
        f"{AD_ACCOUNT_ID}/insights",
        token,
        version,
        {"time_range": tr, "level": "campaign", "fields": f"campaign_id,campaign_name,objective,{base_fields}", "limit": 100},
    )
    campaigns = sorted([normalize_insight_row(r) for r in camp_rows], key=lambda x: x["spend"], reverse=True)

    result = {"period": {"since": start, "until": end}, "account": account, "campaigns": campaigns}

    if include_breakdowns:
        weekly_rows = graph_get_all(
            f"{AD_ACCOUNT_ID}/insights",
            token,
            version,
            {"time_range": tr, "time_increment": 7, "fields": base_fields, "limit": 50},
        )
        result["weekly"] = [normalize_insight_row(r) for r in weekly_rows]

        for b_key, b_name in (("region", "region"), ("age", "age"), ("publisher_platform", "platform")):
            b_rows = graph_get_all(
                f"{AD_ACCOUNT_ID}/insights",
                token,
                version,
                {"time_range": tr, "breakdowns": b_key, "fields": base_fields, "limit": 200},
            )
            result[b_name] = sorted([normalize_insight_row(r) for r in b_rows], key=lambda x: x["spend"], reverse=True)

        ad_rows = graph_get_all(
            f"{AD_ACCOUNT_ID}/insights",
            token,
            version,
            {"time_range": tr, "level": "ad", "fields": f"ad_id,ad_name,{base_fields}", "limit": 200},
        )
        ads = sorted([normalize_insight_row(r) for r in ad_rows], key=lambda x: (x["purchases"], x["spend"]), reverse=True)

        # Miniaturas de los top 15 anuncios
        top_ids = {a["ad_id"] for a in ads[:15] if a.get("ad_id")}
        thumbs: dict[str, str] = {}
        if top_ids:
            ad_objs = graph_get_all(
                f"{AD_ACCOUNT_ID}/ads",
                token,
                version,
                {"fields": "id,name,creative{thumbnail_url,image_url}", "limit": 100},
            )
            for obj in ad_objs:
                if obj.get("id") in top_ids:
                    cr = obj.get("creative") or {}
                    thumbs[obj["id"]] = cr.get("image_url") or cr.get("thumbnail_url") or ""
        for a in ads:
            if a.get("ad_id") in thumbs:
                a["thumbnail_url"] = thumbs[a["ad_id"]]

        result["top_ads"] = ads[:25]

    return result


def fetch_instagram_organic(token: str, version: str, start: str, end: str) -> dict:
    profile = graph_get(
        IG_USER_ID,
        token,
        version,
        {"fields": "id,username,followers_count,follows_count,media_count"},
    )
    dt_start = datetime.strptime(start, "%Y-%m-%d")
    dt_end = datetime.strptime(end, "%Y-%m-%d")

    # Meta IG Insights permite máx 30 días (2592000s) por consulta; partimos en tramos de <= 28 días
    chunks = []
    cur = dt_start
    while cur <= dt_end:
        nxt = min(dt_end, cur + __import__("datetime").timedelta(days=27))
        chunks.append((int(cur.timestamp()), int(nxt.timestamp()) + 86399))
        cur = nxt + __import__("datetime").timedelta(days=1)

    insights_summary = {}
    for metric in ("reach", "views", "accounts_engaged", "total_interactions"):
        try:
            total = 0
            for since_ts, until_ts in chunks:
                res = graph_get(
                    f"{IG_USER_ID}/insights",
                    token,
                    version,
                    {"metric": metric, "period": "day", "metric_type": "total_value", "since": since_ts, "until": until_ts},
                )
                data = res.get("data", [])
                if data:
                    total += int((data[0].get("total_value") or {}).get("value") or 0)
            insights_summary[metric] = total
        except Exception as exc:
            insights_summary[f"{metric}_error"] = str(exc)

    media_list = graph_get_all(
        f"{IG_USER_ID}/media",
        token,
        version,
        {"fields": "id,caption,media_type,media_product_type,timestamp,like_count,comments_count,permalink,thumbnail_url,media_url", "limit": 50},
        max_pages=3,
    )
    period_media = [m for m in media_list if start <= (m.get("timestamp") or "")[:10] <= end]

    return {
        "profile": profile,
        "insights_summary": insights_summary,
        "media_count_in_period": len(period_media),
        "media": period_media[:25],
    }


def fetch_facebook_organic(token: str, version: str) -> dict:
    page = graph_get(
        FB_PAGE_ID,
        token,
        version,
        {"fields": "id,name,fan_count,followers_count"},
    )
    return {"page": page}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cur-start", default="2026-10-01")
    parser.add_argument("--cur-end", default="2026-10-31")
    parser.add_argument("--prev-start", default="2026-09-01")
    parser.add_argument("--prev-end", default="2026-09-30")
    args = parser.parse_args()

    load_env(BASE_DIR / ".env")
    token = os.environ.get("META_ACCESS_TOKEN", "").strip()
    version = os.environ.get("META_API_VERSION", "v21.0").strip() or "v21.0"
    if not token:
        raise SystemExit("Falta META_ACCESS_TOKEN en .env")

    print(f"Extrayendo Meta Ads ({args.cur_start}..{args.cur_end} vs {args.prev_start}..{args.prev_end})...")
    ads_cur = fetch_ads_period(token, version, args.cur_start, args.cur_end, include_breakdowns=True)
    ads_prev = fetch_ads_period(token, version, args.prev_start, args.prev_end, include_breakdowns=False)

    print("Extrayendo Instagram y Facebook Orgánico...")
    ig_cur = fetch_instagram_organic(token, version, args.cur_start, args.cur_end)
    fb_cur = fetch_facebook_organic(token, version)

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "meta_ads": {"current": ads_cur, "previous": ads_prev},
        "organic": {"instagram": ig_cur, "facebook": fb_cur},
    }

    data_dir = BASE_DIR / "data"
    data_dir.mkdir(exist_ok=True)
    out_file = data_dir / f"meta_{args.cur_start}_to_{args.cur_end}.json"
    out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    c = ads_cur["account"]
    p = ads_prev["account"]
    print("\n--- RESUMEN EXTRAÍDO VIA API ---")
    print(f"Meta Ads Actual ({args.cur_start}..{args.cur_end}): Spend=${c.get('spend'):,.2f} | Compras={c.get('purchases')} | Rev=${c.get('revenue'):,.2f} | ROAS={c.get('roas')}x | Semanas={len(ads_cur.get('weekly',[]))} | Regiones={len(ads_cur.get('region',[]))}")
    print(f"Meta Ads Anterior ({args.prev_start}..{args.prev_end}): Spend=${p.get('spend'):,.2f} | Compras={p.get('purchases')} | Rev=${p.get('revenue'):,.2f} | ROAS={p.get('roas')}x")
    print(f"IG @{ig_cur['profile'].get('username')}: {ig_cur['profile'].get('followers_count')} seg | Posts/Reels en período: {ig_cur['media_count_in_period']} | Insights: {ig_cur['insights_summary']}")
    print(f"FB {fb_cur['page'].get('name')}: {fb_cur['page'].get('followers_count')} seg")
    print(f"Archivo guardado: {out_file}")


if __name__ == "__main__":
    main()
