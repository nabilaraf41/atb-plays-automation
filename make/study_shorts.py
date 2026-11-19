"""Collect ~100 GTA 6 YouTube Shorts (metadata only, nothing downloaded) -> out/study/shorts.json
Run: PYTHONUTF8=1 .venv/Scripts/python make/study_shorts.py"""
import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "out" / "study"
YTDLP = str(Path(sys.executable).with_name("yt-dlp.exe"))
QUERIES = ["gta6", "gtavi", "gta6shorts", "gta6gameplay", "gta6funny", "gta6tips", "grandtheftauto6", "gta"]


def search(q):
    # the search Shorts filter returns nothing; the hashtag Shorts feed works
    r = subprocess.run([YTDLP, "--flat-playlist", "--playlist-end", "60", "-J", f"https://www.youtube.com/hashtag/{q}/shorts"],
                       capture_output=True, text=True, encoding="utf-8")
    try:
        return [e["id"] for e in json.loads(r.stdout).get("entries", []) if e.get("id")]
    except json.JSONDecodeError:
        return []


def meta(vid):
    r = subprocess.run([YTDLP, "-J", "--skip-download", f"https://www.youtube.com/shorts/{vid}"],
                       capture_output=True, text=True, encoding="utf-8")
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None
    keep = ("id", "title", "channel", "channel_follower_count", "view_count", "like_count", "comment_count",
            "duration", "upload_date", "description", "tags")
    return {k: d.get(k) for k in keep}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ids = []
    with ThreadPoolExecutor(6) as ex:
        for found in ex.map(search, QUERIES):
            ids += [i for i in found if i not in ids]
    print("found", len(ids))
    with ThreadPoolExecutor(8) as ex:
        rows = [m for m in ex.map(meta, ids[:180]) if m and m.get("duration") and m["duration"] <= 180]
    rows.sort(key=lambda m: m.get("view_count") or 0, reverse=True)
    (OUT / "shorts.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("saved", len(rows))


if __name__ == "__main__":
    main()
