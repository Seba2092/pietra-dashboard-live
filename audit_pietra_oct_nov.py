"""Auditoría profunda de Meta Ads (Octubre vs. Noviembre 2026) para Joyería Pietra."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
AD_ACCOUNT_ID = "act_2169549460223989"


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


def sf(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def act(actions: list | None, types: tuple[str, ...]) -> float:
    if not actions:
        return 0.0
    for t in types:
        for item in actions:
            if item.get("action_type") == t:
                return sf(item.get("value"))
    return 0.0


def norm(row: dict) -> dict:
    spend = sf(row.get("spend"))
    impr = int(sf(row.get("impressions")))
    reach = int(sf(row.get("reach")))
    freq = sf(row.get("frequency"))
    cpm = sf(row.get("cpm"))
    lclicks = int(sf(row.get("inline_link_clicks")))
    actions = row.get("actions") or []
    avals = row.get("action_values") or []

    purch = act(actions, ("purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"))
    lpv = act(actions, ("landing_page_view", "omni_landing_page_view"))
    atc = act(actions, ("add_to_cart", "omni_add_to_cart", "offsite_conversion.fb_pixel_add_to_cart"))
    ic = act(actions, ("initiate_checkout", "omni_initiated_checkout", "offsite_conversion.fb_pixel_initiate_checkout"))
    igv = act(actions, ("instagram_profile_visit",))
    v3s = act(actions, ("video_view",))
    thru = act(row.get("video_thruplay_watched_actions") or [], ("video_view",))
    rev = act(avals, ("purchase", "omni_purchase", "offsite_conversion.fb_pixel_purchase"))

    out = {
        "spend": round(spend, 2),
        "impr": impr,
        "reach": reach,
        "freq": round(freq, 2),
        "cpm": round(cpm, 2),
        "lclicks": lclicks,
        "ctr_link": round((lclicks / impr * 100) if impr else 0.0, 2),
        "cpc_link": round((spend / lclicks) if lclicks else 0.0, 2),
        "lpv": int(lpv),
        "atc": int(atc),
        "ic": int(ic),
        "purch": int(purch) if purch == int(purch) else round(purch, 2),
        "igv": int(igv),
        "v3s": int(v3s),
        "thru": int(thru),
        "hook_rate": round((v3s / impr * 100) if (impr and v3s) else 0.0, 1),
        "hold_rate": round((thru / v3s * 100) if (v3s and thru) else 0.0, 1),
        "rev": round(rev, 2),
        "roas": round((rev / spend) if spend else 0.0, 2),
        "cpa": round((spend / purch) if purch else 0.0, 2),
        "aov": round((rev / purch) if purch else 0.0, 2),
    }
    for k in (
        "campaign_id", "campaign_name", "adset_id", "adset_name",
        "ad_id", "ad_name", "publisher_platform", "platform_position",
        "age", "region", "date_start", "date_stop",
    ):
        if k in row:
            out[k] = row[k]
    return out


def fetch_period(token: str, version: str, since: str, until: str, full: bool = True) -> dict:
    fields = "spend,impressions,reach,frequency,cpm,inline_link_clicks,actions,action_values,video_thruplay_watched_actions"
    tr = json.dumps({"since": since, "until": until})

    acct = graph_get(f"{AD_ACCOUNT_ID}/insights", token, version, {"time_range": tr, "fields": fields}).get("data", [])
    camps = graph_get_all(
        f"{AD_ACCOUNT_ID}/insights", token, version,
        {"time_range": tr, "level": "campaign", "fields": f"campaign_id,campaign_name,{fields}", "limit": 100},
    )
    res = {
        "since": since, "until": until,
        "account": norm(acct[0]) if acct else {},
        "campaigns": sorted([norm(r) for r in camps], key=lambda x: x["spend"], reverse=True),
    }
    if not full:
        return res

    adsets = graph_get_all(
        f"{AD_ACCOUNT_ID}/insights", token, version,
        {"time_range": tr, "level": "adset", "fields": f"campaign_name,adset_id,adset_name,{fields}", "limit": 200},
    )
    ads = graph_get_all(
        f"{AD_ACCOUNT_ID}/insights", token, version,
        {"time_range": tr, "level": "ad", "fields": f"campaign_name,adset_name,ad_id,ad_name,{fields}", "limit": 300},
    )
    placements = graph_get_all(
        f"{AD_ACCOUNT_ID}/insights", token, version,
        {"time_range": tr, "breakdowns": "publisher_platform,platform_position", "fields": fields, "limit": 200},
    )
    ages = graph_get_all(
        f"{AD_ACCOUNT_ID}/insights", token, version,
        {"time_range": tr, "breakdowns": "age", "fields": fields, "limit": 100},
    )
    res["adsets"] = sorted([norm(r) for r in adsets], key=lambda x: x["spend"], reverse=True)
    res["ads"] = sorted([norm(r) for r in ads], key=lambda x: x["spend"], reverse=True)
    res["placements"] = sorted([norm(r) for r in placements], key=lambda x: x["spend"], reverse=True)
    res["ages"] = sorted([norm(r) for r in ages], key=lambda x: x["spend"], reverse=True)
    return res


def main() -> None:
    load_env(BASE_DIR / ".env")
    token = os.environ.get("META_ACCESS_TOKEN", "").strip()
    version = os.environ.get("META_API_VERSION", "v21.0").strip() or "v21.0"
    if not token:
        raise SystemExit("Falta META_ACCESS_TOKEN")

    print("Consultando Octubre (01-31 oct)...")
    oct_data = fetch_period(token, version, "2026-10-01", "2026-10-31", full=True)
    print("Consultando Noviembre completo (01-21 nov)...")
    nov_data = fetch_period(token, version, "2026-11-01", "2026-11-21", full=True)
    print("Consultando Noviembre tramo inicial (01-10 nov) vs reciente (11-21 nov)...")
    nov_early = fetch_period(token, version, "2026-11-01", "2026-11-10", full=False)
    nov_late = fetch_period(token, version, "2026-11-11", "2026-11-21", full=False)

    print("Consultando configuración de anuncios activos y adsets (UTMs, presupuestos, status)...")
    active_ads = graph_get_all(
        f"{AD_ACCOUNT_ID}/ads", token, version,
        {"filtering": json.dumps([{"field": "effective_status", "operator": "IN", "value": ["ACTIVE"]}]),
         "fields": "id,name,effective_status,campaign{name,daily_budget,objective},adset{id,name,daily_budget,optimization_goal,bid_strategy},creative{url_tags}",
         "limit": 100},
    )

    out = {
        "oct": oct_data,
        "nov": nov_data,
        "nov_early": nov_early,
        "nov_late": nov_late,
        "active_ads_config": active_ads,
    }
    out_path = BASE_DIR / "data" / "audit_oct_nov21.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Auditoría guardada en {out_path}")


if __name__ == "__main__":
    main()
