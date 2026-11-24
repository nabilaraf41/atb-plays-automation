"""Cloud runner: posts every queued Reel whose time (BDT) has come, to FB + IG + YouTube.
content/queue.json: [{"id": "...", "at": "2026-11-25 07:00", "video": "queue/x.mp4", "title": "...", "caption": "..."}]
Cover = same name + _cover.jpg. Each platform is recorded in content/posted.json once done, so a failed platform
is retried next run and a done one is never posted twice. Items older than 6 h are skipped (no night dumps).
    python -m atb.run          (cloud)        python -m atb.run --dry   (shows what would post, posts nothing)"""
import json, sys, time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE, POSTED = ROOT / "content" / "queue.json", ROOT / "content" / "posted.json"
BDT = timezone(timedelta(hours=6))


def due(queue, posted, now):
    for it in queue:
        at = datetime.strptime(it["at"], "%Y-%m-%d %H:%M").replace(tzinfo=BDT)
        left = [p for p in ("facebook", "instagram", "youtube") if p not in posted.get(it["id"], {})]
        if left and at <= now <= at + timedelta(hours=6):
            yield it, left


def main(dry=False):
    queue = json.loads(QUEUE.read_text(encoding="utf-8")) if QUEUE.exists() else []
    posted = json.loads(POSTED.read_text(encoding="utf-8")) if POSTED.exists() else {}
    now = datetime.now(BDT)
    for it, left in due(queue, posted, now):
        video = ROOT / it["video"]
        cover = video.with_name(video.stem + "_cover.jpg")
        cover = cover if cover.exists() else None
        print(f"{it['id']} ({it['at']}): {', '.join(left)}{'  [dry run]' if dry else ''}")
        if dry:
            continue
        from atb import poster
        jobs = {"facebook": lambda: poster.fb_reel(video, it["caption"], cover),
                "instagram": lambda: poster.ig_reel(video, it["caption"], cover),
                "youtube": lambda: poster.yt_short(video, it["title"], it["caption"], cover)}
        for p in left:
            try:
                posted.setdefault(it["id"], {})[p] = jobs[p]()
                print(" ", p, "ok")
            except Exception as ex:  # keep going; retried next run
                print(" ", p, "FAILED:", str(ex)[:200])
            POSTED.write_text(json.dumps(posted, indent=1), encoding="utf-8")


def _selftest():
    now = datetime(2026, 11, 25, 8, 0, tzinfo=BDT)
    q = [{"id": "a", "at": "2026-11-25 07:00"}, {"id": "b", "at": "2026-11-25 09:00"}, {"id": "c", "at": "2026-11-24 21:00"}]
    got = [(i["id"], l) for i, l in due(q, {"a": {"facebook": "1"}}, now)]
    assert got == [("a", ["instagram", "youtube"])], got  # due + partial retry; future and stale items skipped


if __name__ == "__main__":
    _selftest()
    main(dry="--dry" in sys.argv)
