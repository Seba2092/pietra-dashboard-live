"""Verifica el token de Meta Graph API, permisos y descubre IDs de Pietra."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def load_env(env_path: Path) -> None:
    """Carga variables simples KEY=VALUE desde .env si existe."""
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        os.environ.setdefault(key.strip(), val.strip().strip('"').strip("'"))


def graph_get(endpoint: str, token: str, version: str, params: dict | None = None) -> dict:
    """Ejecuta un GET a Meta Graph API sin dependencias externas."""
    query = dict(params or {})
    query["access_token"] = token
    url = f"https://graph.facebook.com/{version}/{endpoint.lstrip('/')}?{urllib.parse.urlencode(query)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Error HTTP {exc.code} en {endpoint}: {body}") from exc


def main() -> None:
    load_env(BASE_DIR / ".env")
    token = os.environ.get("META_ACCESS_TOKEN", "").strip()
    version = os.environ.get("META_API_VERSION", "v21.0").strip() or "v21.0"

    if not token or token == "tu_token_aqui":
        print("Falta META_ACCESS_TOKEN en .env. Pega tu token en:")
        print(f"  {BASE_DIR / '.env'}")
        return

    print(f"Probando conexión con Meta Graph API ({version})...\n")

    me = graph_get("me", token, version, {"fields": "id,name"})
    print(f"Usuario / System User: {me.get('name')} (ID: {me.get('id')})")

    perms = graph_get("me/permissions", token, version)
    granted = sorted(
        p["permission"] for p in perms.get("data", []) if p.get("status") == "granted"
    )
    required = {
        "ads_read",
        "read_insights",
        "pages_show_list",
        "pages_read_engagement",
        "instagram_basic",
        "instagram_manage_insights",
    }
    missing = sorted(required - set(granted))
    print(f"Permisos otorgados ({len(granted)}): {', '.join(granted)}")
    if missing:
        print(f"ATENCION - Permisos recomendados faltantes: {', '.join(missing)}")

    ad_accounts = graph_get(
        "me/adaccounts",
        token,
        version,
        {"fields": "id,name,account_status,currency,timezone_name"},
    ).get("data", [])
    print(f"\nCuentas publicitarias encontradas ({len(ad_accounts)}):")
    for acc in ad_accounts:
        print(
            f"  - {acc.get('name')} | {acc.get('id')} | {acc.get('currency')} | status={acc.get('account_status')}"
        )

    pages = graph_get(
        "me/accounts",
        token,
        version,
        {"fields": "id,name,instagram_business_account{id,username,followers_count}"},
    ).get("data", [])
    print(f"\nPáginas de Facebook encontradas ({len(pages)}):")
    for pg in pages:
        ig = pg.get("instagram_business_account") or {}
        ig_txt = (
            f"IG: @{ig.get('username')} (ID: {ig.get('id')}, seg: {ig.get('followers_count')})"
            if ig
            else "Sin IG vinculado"
        )
        print(f"  - {pg.get('name')} (Page ID: {pg.get('id')}) | {ig_txt}")

    config = {
        "api_version": version,
        "ad_accounts": ad_accounts,
        "pages": pages,
        "granted_permissions": granted,
    }
    out_cfg = BASE_DIR / "config.json"
    out_cfg.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nConfiguración guardada en: {out_cfg}")


if __name__ == "__main__":
    main()
