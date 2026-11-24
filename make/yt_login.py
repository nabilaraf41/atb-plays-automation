"""One-time YouTube/Drive sign-in for ATB Plays -> secrets/youtube_token.json (own token, FMM untouched).
Run: .venv/Scripts/python make/yt_login.py   (opens the browser; sign in as atbplayss@gmail.com)"""
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

S = Path(__file__).resolve().parent.parent / "secrets"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly",
          "https://www.googleapis.com/auth/drive.readonly"]
c = InstalledAppFlow.from_client_secrets_file(str(S / "google_client.json"), SCOPES).run_local_server(
    port=0, prompt="consent select_account", access_type="offline")
ch = build("youtube", "v3", credentials=c).channels().list(part="snippet", mine=True).execute()["items"][0]
assert ch["id"] == "UCPwVdzsav766yAJ9PXu3pxg", f"wrong channel: {ch['snippet']['title']} - sign in as atbplayss"
(S / "youtube_token.json").write_text(c.to_json(), encoding="utf-8")
print("OK: token saved for", ch["snippet"]["title"])
