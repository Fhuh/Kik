# Shorts Bot (semi-auto YouTube Shorts)

Flow: trend dhundho → script → voice → 1080x1920 HD video → Telegram pe approval → upload → "upload ho gaya" message.

## Setup (ek baar)
1. Python 3.10+ aur **ffmpeg** install karo (`ffmpeg -version` chalna chahiye).
2. `pip install anthropic edge-tts requests python-dotenv google-api-python-client google-auth-oauthlib`
3. `.env.example` ko `.env` naam se copy karo aur keys bharo:
   - **ANTHROPIC_API_KEY**: console.anthropic.com
   - **YT_API_KEY**: Google Cloud → naya project → "YouTube Data API v3" ON → API key
   - **PEXELS_API_KEY**: pexels.com/api (free, stock videos)
   - **Telegram**: @BotFather se bot banao (token), bot ko message bhejo, phir `https://api.telegram.org/bot<TOKEN>/getUpdates` kholke apna chat id lo
4. Google Cloud me **OAuth client (Desktop app)** banao, file ka naam `client_secret.json` rakho aur is folder me daalo.
5. `python app.py` chalao. Pehli baar browser khulega, apne channel se login karo.
6. Pehle `PRIVACY=private` rakho. 2-3 test ke baad `public` karo.

## Roz apne aap chalane ke liye
Windows Task Scheduler ya Linux cron me `python app.py` din me 1 baar lagao.

## Zaroori rules (channel bachane ke liye)
- Roz **1 video** se shuru karo, 10-20 nahi. Bahut zyada templated videos "inauthentic content" me aa sakte hain.
- Har video me **tumhara apna angle** ho. `MY_ANGLE` me apni style likho aur preview dekh ke hi YES bolo.
- AI voice hai, isliye app upload par "synthetic media" label lagata hai. Ise hatao mat.
- Sirf Pexels ke stock clips use hote hain, kisi aur ke video copy nahi hote.

## Views badhane ke liye
- Pehle 2 second me hook, aur aakhri line me sawal (comments badhte hain).
- Ek hi niche pe tike raho. Jo video chale, uska topic dohrao (par copy nahi).
- 40-50 second ke Shorts, clear awaaz, bade captions.
- Koi guarantee nahi: views YouTube ke algorithm aur tumhare content par depend karte hain.

## Hindi voice/script
`.env` me `VOICE=hi-IN-MadhurNeural`, `SCRIPT_LANGUAGE=Hindi in Devanagari script`, aur `FONT_FILE` me Noto Sans Devanagari ka path do.

## Dhyan do
- Ye code abhi tumhare setup par test nahi hua. Pehla run private rakho aur error aaye to mujhe bhej do.
- Naye Google API projects se upload hue videos kabhi private lock ho jaate hain. Aisa ho to YouTube API audit ke baare me Google ka guide dekho.
