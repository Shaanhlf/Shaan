---
name: easy-video-editing
description: Simple video editing for reels and short clips with ffmpeg, faster-whisper and OpenCV. Use when the person uploads a video and asks to transcribe it ("write down what they say"), add captions, make it vertical / follow the face, cut silent parts, trim, join clips, add background music, speed up, make it smaller for WhatsApp, or grab a cover photo. Handles English and Malay.
---

# Easy Video Editing

The person is not technical. Talk in plain, simple words. Don't show commands unless they ask.

## 0. Make sure the tools are installed (every new session)

Cloud sessions start on a fresh machine. Run the setup once per session (safe to re-run; takes seconds if the environment's setup script already did it):

```bash
S="$(git rev-parse --show-toplevel 2>/dev/null || pwd)/.claude/skills/easy-video-editing"
bash "$S/setup.sh"
```

All scripts below live in `$S/scripts/`.

If it prints "Speech model could not download", tell the person: "Speech-to-text needs the Hugging Face websites allowed in your cloud settings (Allowed domains)." Everything else still works.

## 1. Where files are

- Uploaded files in Claude Code cloud sessions are in `~/.claude/uploads/<session-id>/` (on claude.ai chat: `/mnt/user-data/uploads/`). Find them with `ls -t ~/.claude/uploads/*/ /mnt/user-data/uploads/ 2>/dev/null`.
- Work on a copy. Never change the original. Name outputs clearly (`reel-captions.mp4`).
- Put results in the project folder (the repo) so the person can open them, and send them with the file-sending tool if available.
- Videos are large: don't commit them to git unless the person asks.

## 2. Check your own work after every edit

```bash
ffmpeg -v error -i out.mp4 -vf "fps=1/3,scale=270:-1,tile=6x1" -frames:v 1 -y sheet.jpg   # look at it
ffprobe -v error -show_entries format=duration:stream=width,height -of default=nw=1 out.mp4
```

Reels: 1080x1920 (9:16), H.264 + AAC, `-pix_fmt yuv420p`, `-movflags +faststart`.

## 3. Recipes

**Transcribe / make captions file**
```bash
python3 $S/scripts/transcribe.py in.mp4 --lang en
python3 $S/scripts/transcribe.py in.mp4 --lang ms --model medium --prompt "names, brand words"   # Malay
```
Gives `in.srt` and `in_words.json`. Show the person the text. Fix wrong names in the .srt by hand.
(`medium` is a ~1.5 GB download the first time.)

**Pop-up captions burned in** (video must already be 1080x1920)
```bash
python3 $S/scripts/popcaps.py in.srt caps.ass --accent "FREE,WEIGHT"
ffmpeg -i in.mp4 -vf "ass=caps.ass" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a copy -movflags +faststart out.mp4
```

**Plain captions burned in**
```bash
ffmpeg -i in.mp4 -vf "subtitles=in.srt:force_style='FontName=Montserrat,FontSize=14,Bold=1,Outline=2,MarginV=60'" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a copy -movflags +faststart out.mp4
```

**Face tracking to vertical** (~3 s of work per 1 s of video)
```bash
python3 $S/scripts/facetrack.py in.mp4 out.mp4      # calmer: --smooth 0.04, faster: --every 5
```
Already-vertical video is just scaled to 1080x1920. With two people it follows the biggest face.

**Cut pauses**
```bash
python3 $S/scripts/cutpauses.py in.mp4 out.mp4 --min 0.35
```

**Trim** (e.g. keep 0:05 to 0:20)
```bash
ffmpeg -ss 00:00:05 -to 00:00:20 -i in.mp4 -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -movflags +faststart out.mp4
```

**Join clips** (re-encodes, so clips from different phones still join)
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v0];[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v1];[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -movflags +faststart out.mp4
```
More clips: add inputs and `[v2][2:a]`, set `n=`. A clip with no sound needs a silent track first: add `-f lavfi -t <its length> -i anullsrc=r=48000:cl=stereo` and use that input's audio.

**9:16 with blurred background** (for landscape video, no face tracking)
```bash
ffmpeg -i in.mp4 -filter_complex "[0]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20[bg];[0]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a copy -movflags +faststart out.mp4
```

**Music under the voice** (music ~15 %, fades out over the last 2 s; `normalize=0` keeps the voice at full volume)
```bash
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 in.mp4)
ffmpeg -i in.mp4 -i music.mp3 -filter_complex "[1:a]volume=0.15,afade=t=out:st=$(awk "BEGIN{print $DUR-2}"):d=2[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -movflags +faststart out.mp4
```
Only use music the person owns or that is royalty-free. Never put song lyrics on screen.

**Speed up 1.2x**
```bash
ffmpeg -i in.mp4 -filter_complex "[0:v]setpts=PTS/1.2[v];[0:a]atempo=1.2[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -movflags +faststart out.mp4
```

**Smaller for WhatsApp** (long side 1280 px, works for vertical and landscape)
```bash
ffmpeg -i in.mp4 -vf "scale='if(gt(iw,ih),min(1280,iw),-2)':'if(gt(iw,ih),-2,min(1280,ih))'" -c:v libx264 -crf 28 -preset slow -pix_fmt yuv420p -c:a aac -b:a 96k -movflags +faststart small.mp4
```

**Cover photo**
```bash
ffmpeg -ss 00:00:03 -i in.mp4 -frames:v 1 -q:v 2 cover.jpg
```

## Rules
- Simple words. No commands unless asked.
- Keep the original untouched.
- Captions sit in the lower middle so TikTok/Instagram buttons don't cover them.
- If something fails, say what failed in one line and try the next simplest way.
- Remind them: always watch the video before posting.
