---
name: whiteboard-reel
description: Make a hand-drawn whiteboard explainer reel (white background, marker handwriting that appears in time with the voice, boxes, arrows, strike-throughs, camera zoom-out) voiced with Shaan's own ElevenLabs voice. Use when the person asks for a whiteboard / papan putih / "macam coachkimii" reel, a marker-drawing explainer video, or a new reel in this style on any topic, in Malay or English.
---

# Whiteboard Reel

The person is not technical. Talk in simple words (Malay or English, follow how they write). Don't show commands unless they ask.

Result: a 1080x1920 MP4 (30 fps, H.264 + AAC) on a clean white board. Handwriting is revealed left to right with a marker following the tip, timed to the exact word in the voiceover. The camera starts zoomed in and slowly zooms out as the board fills.

## 0. Setup (every new session)

```bash
SK="$(git rev-parse --show-toplevel)/.claude/skills/whiteboard-reel"
bash "$SK/setup.sh"
```

## 1. Write the script

- 30–45 s spoken (about 70–100 words). Hook first ("X = Y?"), then 3–5 points, then a punchline and a CTA.
- Write original content in the person's own angle. Never copy another creator's script.
- Each point needs a short **box label** (≤ 16 characters, CAPS) and a short **result** (≤ 14 characters, CAPS), plus an optional small note.
- Show the script to the person and get an OK before spending credits, unless they said to just go ahead.

## 2. Voice (ElevenLabs MCP tools)

Shaan's voices (cloned, theirs):
- **Shaan malay**: `4qpG1st806WZlvRyqtDE` (use for Malay)
- **Shaan** (English, Malay accent): `3K6z1apE2wnVa2HjRcRn`

Steps:
1. `creative_create_flow`, then reuse its flow_id for every call below.
2. `creative_generate_speech`: model `eleven_multilingual_v2`, the voice above, `generations_count: 1`. Poll `creative_get_flow_run_status` until it's done.
3. Make a project folder `reels/<short-name>/audio/`, then download the media url to `voice.mp3`.
4. `creative_transcribe_audio` with `model_id: eleven_scribe_v1` and `connect_from: [<speech node_id>]`, so the speech feeds straight in and no upload is needed. Poll, then download `words_download_url` to `audio/words.json`.

Never call a generation tool twice to retry, because each call is charged. Tell the person roughly what it cost (speech ~500 credits for 35 s, transcription ~250–300).

## 3. Scene file: `reels/<name>/scene.json`

**Fastest way:** write a short `reels/<name>/spec.json` (title lines, 5 rows, punchline, CTA) and run
`python3 "$SK/build_scene.py" reels/<name>`. It applies the brand defaults and the layout below. The spec format is documented at the top of `build_scene.py`, and `reels/protein-sehari/spec.json` is a full example. Hand-edit `scene.json` only for extras (e.g. `drops`).

Start from `reels/berat-naik/scene.json` (brand style) or `examples/diet-seksa.scene.json` (white). Board coordinates are 1080 wide. y is the text baseline.

```json
{ "audio": "audio/voice.mp3", "words": "audio/words.json",
  "handle": "@shaan_fittrainer", "handlePosition": "protect",
  "background": "#f8f3ea",
  "colors": { "ink": "#1f2a48", "red": "#d93a3f", "green": "#1f9d55", "blue": "#3b6fd8", "note": "#55596a" },
  "elements": [ ... ] }
```

**Shaan's brand defaults** (use unless told otherwise): cream background `#f8f3ea`, navy ink `#1f2a48`, handle `@shaan_fittrainer` as an anti-crop watermark (`handlePosition: "protect"`: lower-middle, over the content, ~22% opacity, drifting slowly so it can't be cropped or blurred in one spot). Shaan asked for this to protect their content: never move it back to the top or edges unless they ask. Other values: `top`, `bottom`. The latest reel `reels/berat-naik/scene.json` is the best template to copy.

| type | fields |
|---|---|
| `text` | `text, x, y, size, color`, `font: "hand"` for small notes (Kalam); default is the marker font |
| `box` | `text, x, y, w, h`, optional `color`; the label auto-shrinks to fit |
| `arrow` | `x1, x2, y` |
| `strike` / `line` / `circle` | `target` (index of a text element) + optional `part` (the words to cross out / underline / circle) |
| `badge` | `text` (a number), `x, y` = centre |
| `drops` | row of filled water drops, e.g. a urine colour chart: `x, y` = centre of first drop, `r` (40), `gap` (136), `colors` (array, appear one by one). Pair with hand-font labels + an arrow underneath. See `reels/air-sehari/scene.json` |

Every element has `cue`: a word from the voiceover (case and punctuation ignored, prefix match) and optional `delay` in seconds. **Cues are searched in order**: each search starts at the word the previous cue matched. So list elements in the order they are spoken, or a later word will be missed and that element only shows at the very end. The same word can be used twice in a row (e.g. a title and then its underline).

Proven layout (5 rows):
- Title at y 330 / 450, size 92.
- Rows at y 560, 730, 910, 1080, 1250 (step ~170). Each row has:
  - badge at x 112, centred on the row's middle
  - box at x 160, w 400, h 100
  - arrow from x 575 to 640
  - result text at x 655, baseline about box y + 65, size 44–48
  - note at x 655, about 47 px lower, size 30, font hand
- Punchline at y 1520, size 66. CTA box at x 300, y 1610, w 480, h 100, red.

Colour meaning: ink = boxes and title, red = the myth / cross-outs / warnings, green = results, blue = emphasis notes / underline.

## 4. Check, then render

```bash
node "$SK/engine/render.js" reels/<name> --still 10   # one frame -> reels/<name>/out/still.jpg ; look at it
node "$SK/engine/render.js" reels/<name>              # full video -> reels/<name>/out/reel.mp4 (~40 s of work)
```

Before sending, look at stills from the start, middle and end, and a contact sheet:
`ffmpeg -v error -i out/reel.mp4 -vf "fps=1/3,scale=200:-1,tile=6x2" -frames:v 1 -y out/sheet.jpg`.
Check for: text running off the right edge (x + width must stay under ~1040), notes overlapping the next row, and any element missing (usually a cue order problem).

Live preview with sound: `node "$SK/engine/render.js" reels/<name> --serve`, then open http://localhost:8080.

Send the MP4 with the file-sending tool. Don't commit videos (`out/` is git-ignored). Do commit `scene.json` and `audio/`. Remind them to watch it before posting.

## 5. Copywriting (always, with every reel)

Write `reels/<name>/caption.md` and paste the main caption in chat too, ready to copy. Include:
- **Main caption**: a scroll-stopping first line (a feeling or question plus an emoji), a numbered list that mirrors the 5 board rows, one surprising fact, then a reframe.
- **Comment CTA** with one keyword ("Komen \"TIMBANG\"…") plus a save/share line.
- A short alternative caption, 2–3 cover lines, a comment to pin, 10–12 hashtags (Malay + fitness Malaysia + `#shaanfittrainer`), and 2–3 alternative hooks for A/B testing.
- Match the voice: Malay with casual "you", short lines, no long paragraphs. Keep health claims accurate and hedge numbers with "±".

## How the engine works (for changes)

- `engine/board.js`: a pure function of time t that draws everything on a canvas: wobbly hand-drawn strokes (seeded, so they look the same every frame), a clip-mask reveal for text, the 3D marker, and camera keyframes that frame everything drawn so far.
- `engine/index.html`: loads the fonts (`@fontsource` Permanent Marker + Kalam). It is both the preview player and the render target.
- `engine/render.js`: a tiny local server (project files first, then engine files), Playwright Chromium grabbing JPEG frames, piped into ffmpeg together with the voice.

## Reference: the original style (@coachkimii_, "Turun Berat ≠ Hilang Lemak")

53 s, light white-grey board, CAPS marker font plus a small handwriting font, 4 colours. Boxes are chained with "+" and arrows point to results; old results get crossed out as better ones appear. The camera zooms out over time, every word is timed to the voice, and it ends on a "KOMEN PLAN" CTA and then a dark IG-handle end card. Likely made with a whiteboard animation app (VideoScribe / Doodly) or a code renderer driven by word timestamps. Our version adds numbered badges, soft box shadows and a bright ending with no dark card.
