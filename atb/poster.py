"""Post a Reel to the ATB Plays Facebook Page, Instagram @atb.plays and YouTube Shorts.
Adapted from FMM's fmm/poster.py + fmm/youtube.py (copied, FMM untouched). Secrets: .env + secrets/ locally,
environment variables in the cloud (GitHub Secrets)."""
import json, os, time
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parent.parent
G = "https://graph.facebook.com/v21.0"


def env():
    keys = ("META_PAGE_TOKEN", "META_PAGE_ID", "IG_USER_ID", "YOUTUBE_TOKEN_JSON")
    e = {k: os.environ[k] for k in keys if os.environ.get(k)}
    f = ROOT / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                e.setdefault(k.strip(), v.strip())
    yt = ROOT / "secrets" / "youtube_token.json"
    if "YOUTUBE_TOKEN_JSON" not in e and yt.exists():
        e["YOUTUBE_TOKEN_JSON"] = yt.read_text(encoding="utf-8")
    return e


E = env()


def call(method, path, **kw):
    kw.setdefault("params", {})["access_token"] = E["META_PAGE_TOKEN"]
    j = requests.request(method, f"{G}/{path}", timeout=300, **kw).json()
    if "error" in j:
        raise RuntimeError(f"{path}: {j['error'].get('message')}")
    return j


def _upload(url, path):
    with open(path, "rb") as f:
        r = requests.post(url, data=f, timeout=600, headers={
            "Authorization": f"OAuth {E['META_PAGE_TOKEN']}", "offset": "0", "file_size": str(os.path.getsize(path))})
    if not r.ok:
        raise RuntimeError(f"upload failed: {r.text[:300]}")
    return r


def fb_reel(path, caption, cover=None):
    page = E["META_PAGE_ID"]
    start = call("POST", f"{page}/video_reels", data={"upload_phase": "start"})
    _upload(start["upload_url"], path)
    call("POST", f"{page}/video_reels", data={"upload_phase": "finish", "video_id": start["video_id"],
                                              "video_state": "PUBLISHED", "description": caption})
    if cover:
        for _ in range(6):  # the video must finish processing before a thumbnail is accepted
            try:
                with open(cover, "rb") as f:
                    call("POST", f"{start['video_id']}/thumbnails", files={"source": f}, data={"is_preferred": "true"})
                break
            except Exception:
                time.sleep(30)
    return start["video_id"]


def _public_url(path):
    """Instagram fetches covers from a URL: host it as an unpublished FB photo (same trick as FMM)."""
    with open(path, "rb") as f:
        pid = call("POST", f"{E['META_PAGE_ID']}/photos", files={"source": f}, data={"published": "false"})["id"]
    return call("GET", pid, params={"fields": "images"})["images"][0]["source"]


def ig_reel(path, caption, cover=None):
    ig = E["IG_USER_ID"]
    data = {"media_type": "REELS", "upload_type": "resumable", "caption": caption, "share_to_feed": "true"}
    if cover:
        data["cover_url"] = _public_url(cover)
    j = call("POST", f"{ig}/media", data=data)
    _upload(j["uri"], path)
    for _ in range(60):
        st = call("GET", j["id"], params={"fields": "status_code"}).get("status_code")
        if st == "FINISHED":
            break
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"IG processing failed: {st}")
        time.sleep(5)
    for i in range(5):  # IG sometimes says "not available" right after FINISHED (seen on FMM)
        try:
            return call("POST", f"{ig}/media_publish", data={"creation_id": j["id"]})["id"]
        except RuntimeError as ex:
            if i == 4 or "not" not in str(ex).lower():
                raise
            time.sleep(20)


def yt_short(path, title, caption, cover=None):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    c = Credentials.from_authorized_user_info(json.loads(E["YOUTUBE_TOKEN_JSON"]))
    if not c.valid:
        c.refresh(Request())
    yt = build("youtube", "v3", credentials=c, cache_discovery=False)
    body = {"snippet": {"title": title[:100], "description": caption + "\n\n#Shorts", "categoryId": "20",
                        "tags": ["GTA 6", "GTA VI", "GTA 6 shorts", "ATB Plays"]},
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False}}
    req = yt.videos().insert(part="snippet,status", body=body,
                             media_body=MediaFileUpload(str(path), chunksize=-1, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    if cover:
        try:
            yt.thumbnails().set(videoId=resp["id"], media_body=MediaFileUpload(str(cover))).execute()
        except Exception as ex:
            print("yt thumbnail skipped:", str(ex)[:150])
    return resp["id"]


def check():
    """Read-only access check: posts nothing."""
    page = call("GET", E["META_PAGE_ID"], params={"fields": "name"})["name"]
    ig = call("GET", E["IG_USER_ID"], params={"fields": "username"})["username"]
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    c = Credentials.from_authorized_user_info(json.loads(E["YOUTUBE_TOKEN_JSON"]))
    c.refresh(Request())
    ch = build("youtube", "v3", credentials=c, cache_discovery=False).channels().list(part="snippet", mine=True).execute()
    return page, ig, ch["items"][0]["snippet"]["title"]


if __name__ == "__main__":
    print("FB Page / Instagram / YouTube:", check())
