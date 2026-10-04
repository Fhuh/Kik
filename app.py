"""Semi-auto YouTube Shorts bot.
Trend dhundho -> script (Claude) -> voice (edge-tts) -> 1080x1920 HD video (ffmpeg + Pexels)
-> Telegram pe tumhari approval -> YouTube pe upload -> "upload ho gaya" message.
"""
import os, json, subprocess, textwrap, time, random, asyncio, pathlib
import requests, anthropic, edge_tts
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

load_dotenv()
E = os.environ.get
NICHE = E("NICHE", "amazing science and tech facts")
ANGLE = E("MY_ANGLE", "friendly, curious, gives a clear personal opinion")
LANG = E("SCRIPT_LANGUAGE", "simple Indian English")
VOICE = E("VOICE", "en-IN-PrabhatNeural")
REGION = E("REGION", "IN")
PRIVACY = E("PRIVACY", "public")
MODEL = E("CLAUDE_MODEL", "claude-sonnet-5-5")
FONT = E("FONT_FILE", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
OUT = pathlib.Path("output"); OUT.mkdir(exist_ok=True)
TG = f"https://api.telegram.org/bot{E('TELEGRAM_BOT_TOKEN')}"
CHAT = E("TELEGRAM_CHAT_ID")


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)


def tg(method, **kw):
    return requests.post(f"{TG}/{method}", timeout=300, **kw).json()


def trending():
    r = requests.get("https://www.googleapis.com/youtube/v3/videos", timeout=30, params={
        "part": "snippet", "chart": "mostPopular", "regionCode": REGION,
        "maxResults": 25, "key": E("YT_API_KEY")}).json()
    return [i["snippet"]["title"] for i in r.get("items", [])]


def make_idea(titles):
    p = f"""You write YouTube Shorts for a channel about: {NICHE}. Channel voice: {ANGLE}. Language: {LANG}.
Trending video titles today: {json.dumps(titles, ensure_ascii=False)}
Pick ONE trend that fits the niche (or a close angle) and write an ORIGINAL Short with a clear personal
opinion or insight, not a generic list of facts. Rules: strong hook in the first 2 seconds, 6-8 short lines,
40-50 seconds when spoken, last line asks viewers a question to comment, no false claims, nothing copyrighted.
Return ONLY JSON: {{"title":"max 70 chars, curiosity but honest","description":"2-3 lines + 3 hashtags incl #Shorts",
"tags":["..."],"lines":[{{"text":"spoken line","stock_query":"2-3 English words for stock footage"}}]}}"""
    m = anthropic.Anthropic().messages.create(model=MODEL, max_tokens=1500,
                                              messages=[{"role": "user", "content": p}])
    t = m.content[0].text
    return json.loads(t[t.index("{"): t.rindex("}") + 1])


def stock(query, i):
    r = requests.get("https://api.pexels.com/videos/search", timeout=30,
                     headers={"Authorization": E("PEXELS_API_KEY")},
                     params={"query": query, "orientation": "portrait", "size": "large", "per_page": 6}).json()
    vids = r.get("videos") or []
    if not vids:
        raise RuntimeError(f"Stock footage nahi mila: {query}")
    f = max(random.choice(vids)["video_files"], key=lambda x: x.get("height") or 0)
    path = OUT / f"clip{i}.mp4"
    path.write_bytes(requests.get(f["link"], timeout=120).content)
    return path


def duration(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", str(p)]).decode())


def scene(i, line):
    a = OUT / f"a{i}.mp3"
    asyncio.run(edge_tts.Communicate(line["text"], VOICE, rate="+5%").save(str(a)))
    d = duration(a) + 0.25
    clip = stock(line["stock_query"], i)
    txt = OUT / f"t{i}.txt"
    txt.write_text("\n".join(textwrap.wrap(line["text"], 22)), encoding="utf-8")
    vf = ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,"
          f"drawtext=fontfile='{FONT}':textfile='{txt.as_posix()}':fontsize=64:fontcolor=white:"
          "borderw=6:bordercolor=black:x=(w-text_w)/2:y=h*0.62:line_spacing=12")
    o = OUT / f"s{i}.mp4"
    run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(clip), "-i", str(a), "-t", f"{d:.2f}",
         "-vf", vf, "-af", "apad", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "slow",
         "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", str(o)])
    return o, d


def ask_ok(preview, idea):
    with open(preview, "rb") as f:
        tg("sendVideo", data={"chat_id": CHAT, "caption": f"{idea['title']}\n\nUpload karu? Reply: YES ya NO"},
           files={"video": f})
    res = tg("getUpdates", data={"timeout": 0}).get("result") or []
    off = res[-1]["update_id"] + 1 if res else 0
    end = time.time() + 6 * 3600
    while time.time() < end:
        for u in tg("getUpdates", data={"offset": off, "timeout": 30}).get("result", []):
            off = u["update_id"] + 1
            m = u.get("message", {})
            if str(m.get("chat", {}).get("id")) == str(CHAT):
                t = m.get("text", "").strip().lower()
                if t in ("yes", "y", "ha", "haan"):
                    return True
                if t in ("no", "n", "nahi"):
                    return False
    return False


def youtube():
    sc = ["https://www.googleapis.com/auth/youtube.upload"]
    cred = Credentials.from_authorized_user_file("token.json", sc) if os.path.exists("token.json") else None
    if not cred or not cred.valid:
        if cred and cred.expired and cred.refresh_token:
            cred.refresh(Request())
        else:
            cred = InstalledAppFlow.from_client_secrets_file("client_secret.json", sc).run_local_server(port=0)
        open("token.json", "w").write(cred.to_json())
    return build("youtube", "v3", credentials=cred)


def upload(video, idea):
    body = {"snippet": {"title": idea["title"][:100], "description": idea["description"],
                        "tags": idea["tags"], "categoryId": E("CATEGORY_ID", "28")},
            "status": {"privacyStatus": PRIVACY, "selfDeclaredMadeForKids": False,
                       "containsSyntheticMedia": True}}  # AI voice hai, isliye honest label
    req = youtube().videos().insert(part="snippet,status", body=body,
                                    media_body=MediaFileUpload(str(video), chunksize=-1, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp["id"]


def main():
    idea = make_idea(trending())
    (OUT / "idea.json").write_text(json.dumps(idea, ensure_ascii=False, indent=2), encoding="utf-8")
    scenes, total = [], 0
    for i, l in enumerate(idea["lines"]):
        s, d = scene(i, l); scenes.append(s); total += d
    if total > 59:
        print(f"Dhyan do: video {total:.0f}s ka hai, Shorts ke liye chhota karo (script kam lines ka).")
    lst = OUT / "list.txt"
    lst.write_text("".join(f"file '{s.resolve().as_posix()}'\n" for s in scenes))
    final, prev = OUT / "short.mp4", OUT / "preview.mp4"
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(final)])
    run(["ffmpeg", "-y", "-i", str(final), "-vf", "scale=540:-2", "-c:v", "libx264", "-crf", "28",
         "-c:a", "aac", str(prev)])
    if ask_ok(prev, idea):
        vid = upload(final, idea)
        msg = f"✅ Video upload ho gaya: https://youtube.com/shorts/{vid}"
    else:
        msg = "⏭️ Theek hai, ye video upload nahi kiya."
    tg("sendMessage", data={"chat_id": CHAT, "text": msg})
    print(msg)


if __name__ == "__main__":
    main()
