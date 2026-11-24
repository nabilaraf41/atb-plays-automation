"""Turn the short Graph-Explorer user token in .env into a never-expiring Page token + IG id, saved back to .env.
.env needs: META_APP_ID, META_APP_SECRET, META_USER_TOKEN (from Graph API Explorer).
Run: .venv/Scripts/python make/meta_token.py   -- prints only names/ids, never token values."""
from pathlib import Path
import requests

ENV = Path(__file__).resolve().parent.parent / ".env"
G = "https://graph.facebook.com/v21.0"
PAGE_ID = "61596235157826"  # ATB Plays


def load():
    d = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.strip().startswith("#"):
            k, v = line.split("=", 1)
            d[k.strip()] = v.strip()
    return d


def get(url, **p):
    r = requests.get(url, params=p, timeout=30).json()
    if "error" in r:
        raise SystemExit("Meta error: " + r["error"].get("message", "unknown"))
    return r


e = load()
for k in ("META_APP_ID", "META_APP_SECRET", "META_USER_TOKEN"):
    assert e.get(k), f"{k} is missing in .env"
long_user = get(f"{G}/oauth/access_token", grant_type="fb_exchange_token", client_id=e["META_APP_ID"],
                client_secret=e["META_APP_SECRET"], fb_exchange_token=e["META_USER_TOKEN"])["access_token"]
pages = get(f"{G}/me/accounts", access_token=long_user, fields="id,name,access_token")["data"]
page = next((p for p in pages if p["name"] == "ATB Plays"), None)
PAGE_ID = page["id"] if page else PAGE_ID
if not page:
    raise SystemExit("ATB Plays Page not in this token. Pages seen: " + ", ".join(p["name"] for p in pages))
ig = get(f"{G}/{PAGE_ID}", fields="instagram_business_account{id,username}", access_token=page["access_token"])
ig = ig.get("instagram_business_account") or {}
assert ig.get("id"), "Instagram is not linked to the Page"
dbg = get(f"{G}/debug_token", input_token=page["access_token"], access_token=f'{e["META_APP_ID"]}|{e["META_APP_SECRET"]}')["data"]

e.pop("META_USER_TOKEN")  # short token no longer needed
e.update(META_PAGE_ID=PAGE_ID, META_PAGE_TOKEN=page["access_token"], IG_USER_ID=ig["id"])
ENV.write_text("".join(f"{k}={v}\n" for k, v in e.items()), encoding="utf-8")
print(f"OK: Page '{page['name']}' + Instagram @{ig.get('username')} (id {ig['id']}) saved to .env")
print("Page token expires:", "never" if dbg.get("expires_at") == 0 else dbg.get("expires_at"))
