#!/usr/bin/env python3
"""Builds the HyperFrames composition (index.html) + ducked music for the SV Sweethut reel.
Design: "Patisserie Ribbon" - cream/burgundy/gold, Fraunces italic keywords + Manrope captions,
ribbon-wipe transitions, hand-placed motion graphics kept clear of faces and inside TikTok/IG safe zone
(all graphics between y=230 and y=1500, x<=960)."""
import json, os, subprocess, html

SCR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = f"{SCR}/work"; PROJ = f"{SCR}/hf/sweethut"; SFX = f"{SCR}/sfx"

# ---- edit decision list: (clip, in, out). Pauses + weak opener removed, strongest line first.
PIECES = [
    ("A", 4, 0.10, 4.48),   # HOOK: "Look at that, so soft, moist and beautifully buttery"
    ("B", 1, 1.86, 7.93),   # "Your perfect tea-time treat ... lots of love"
    ("C1", 2, 0.00, 3.10),  # "Every cake begins with our rich buttery batter"
    ("C2", 2, 3.62, 7.80),  # "slowly baked until golden, soft and absolutely delicious"
    ("D", 4, 4.80, 6.36),   # "topped with our signature rich"
    ("D2", 4, 6.88, 7.93),  # "Palkova icing"  (word "creamy" removed: it is hard butter icing)
    ("E1", 3, 0.00, 1.45),  # "One delicious slice"
    ("E2", 3, 1.64, 3.92),  # "one warm cup of tea, pure happiness"
    ("E3", 3, 4.18, 7.80),  # "And for special moments, we create beautiful custom cakes too"
    ("F1", 5, 0.00, 4.22),  # "From rich chocolate brownies to beautiful cupcakes, there's something for everyone"
    ("F2", 5, 5.08, 7.93),  # "Make every moment sweeter with SV Sweethut"
]
END_HOLD = 2.1

t = 0.0; P = {}
for name, c, a, b in PIECES:
    P[name] = dict(clip=c, a=a, b=b, s=round(t, 3), d=round(b - a, 3)); t += b - a
END_S = round(t, 3); TOTAL = round(t + END_HOLD, 3)
def out(name, local):  # source time inside a piece -> output time
    return round(P[name]["s"] + (local - P[name]["a"]), 3)

# ---- words in output time
FIX = {"teatime": "tea-time", "palkova": "Palkova", "SV": "SV", "Sweet": "Sweethut", "Hut.": ""}
KEY = {"soft", "moist", "buttery", "butter", "love", "golden", "delicious", "palkova", "icing",
       "happiness", "custom", "cakes", "brownies", "cupcakes", "everyone", "sweeter", "sweethut", "tea-time"}
words = []
for name, c, a, b in PIECES:
    for w in json.load(open(f"{WORK}/en/clip{c}_words.json")):
        mid = (w["s"] + w["e"]) / 2
        if a <= mid <= b:
            txt = FIX.get(w["w"], w["w"])
            if not txt: continue
            words.append(dict(w=txt, s=max(out(name, max(w["s"], a)), P[name]["s"]), e=out(name, min(w["e"], b)), piece=name))
# whisper put "fresh" late; nudge words that drift past real speech
# group into caption chunks: break on punctuation, gaps, piece change, or 3 words
chunks = []; cur = []
for i, w in enumerate(words):
    cur.append(w)
    nxt = words[i + 1] if i + 1 < len(words) else None
    end_punct = w["w"][-1] in ",.!?"
    if (nxt is None or end_punct or len(cur) >= 3 or nxt["s"] - w["e"] > 0.35 or nxt["piece"][0] != w["piece"][0]):
        chunks.append(cur); cur = []

# ---- SFX cues (file, time, volume)
cues = []
def cue(f, at, v): cues.append((f, round(max(0, at), 3), v))
cue("impact", 0.0, 0.55); cue("sparkle", 0.12, 0.35)
for name in ["B", "C1", "D", "E1", "E3", "F1", "F2"]:
    cue("whoosh", P[name]["s"] - 0.22, 0.4)
cue("riser", out("C2", 4.0) - 0.8, 0.22)
cue("ding", out("C2", 4.85), 0.3)                       # "golden"
cue("pop", out("B", 6.95), 0.32)                         # hearts on "love"
cue("sparkle", P["D2"]["s"], 0.3)                       # "Palkova"
cue("pop", out("E2", 3.3), 0.3)                         # "happiness"
cue("sparkle", out("E3", 6.6), 0.3)                      # "custom cakes"
cue("pop", out("F1", 1.15), 0.3); cue("pop", out("F1", 2.25), 0.3)   # tags
cue("impact", out("F2", 6.74), 0.4)                      # brand
cue("chime", END_S + 0.05, 0.42)
for k, name in enumerate(["B", "C1", "D", "E1", "F1"]):
    cue("tick", P[name]["s"] + 0.15, 0.3)                 # chapter pill

# ---- voice track for sidechain (same cuts) and ducked BGM
def sh(cmd): subprocess.run(cmd, shell=True, check=True)
parts = []; inputs = []
for i, (name, c, a, b) in enumerate(PIECES):
    inputs.append(f"-i {WORK}/clip{c}.mp4")
    parts.append(f"[{i}:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,afade=t=out:st={b-a-0.03:.3f}:d=0.03[a{i}]")
cat = "".join(f"[a{i}]" for i in range(len(PIECES)))
sh(f"ffmpeg -v error -y {' '.join(inputs)} -filter_complex \"{';'.join(parts)};{cat}concat=n={len(PIECES)}:v=0:a=1,apad=whole_dur={TOTAL}[v]\" -map \"[v]\" -ar 48000 -ac 2 {WORK}/voice.wav")
sh(f"python3 {SCR}/scripts/bgm.py {SFX}/bgm_raw.wav {TOTAL + 0.4}")
# music sits ~16 dB under the voice, ducks a further ~8 dB while she talks, swells on the end card
sh(f"ffmpeg -v error -y -i {SFX}/bgm_raw.wav -i {WORK}/voice.wav -filter_complex "
   f"\"[0:a]volume=1.0,volume='if(gte(t,{END_S}),1.3,1)':eval=frame[m];[1:a]highpass=f=150,volume=3[sc];"
   f"[m][sc]sidechaincompress=threshold=0.04:ratio=4:attack=25:release=380:makeup=1[d]\" -map \"[d]\" -t {TOTAL} {PROJ}/assets/sfx/bgm_ducked.wav")
for f in set(c[0] for c in cues):
    sh(f"cp {SFX}/{f}.wav {PROJ}/assets/sfx/{f}.wav")
MAC_D = round(P["D"]["d"] + P["D2"]["d"], 3); SRC_A, SRC_B = 3.98, 5.60
sh(f"ffmpeg -v error -y -ss {SRC_A} -t {SRC_B - SRC_A} -i {WORK}/clip3.mp4 -an -vf \"setpts=PTS*{MAC_D/(SRC_B-SRC_A):.4f},minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:vsbmc=1,trim=duration={MAC_D}\" -c:v libx264 -crf 16 -pix_fmt yuv420p {PROJ}/assets/icing_macro.mp4")
sh(f"ffmpeg -v error -y -sseof -0.08 -i {WORK}/clip5.mp4 -frames:v 1 -q:v 2 {PROJ}/assets/endframe.jpg")

# ---- HTML
E = html.escape
vids = []
for name, c, a, b in PIECES:
    p = P[name]
    vids.append(f'<video id="v{name}" class="clip vid" src="assets/clip{c}.mp4" data-start="{p["s"]}" data-duration="{p["d"]}" '
                f'data-media-start="{a}" data-volume="1.15" data-fade-in="0.03" data-fade-out="0.03" data-has-audio="true" data-track-index="0" playsinline></video>')
vids.append(f'<div id="real" class="clip" data-start="{P["D"]["s"]}" data-duration="{MAC_D}" data-track-index="1"><img id="realbg" src="assets/real_slice.jpg"/><div id="realtint"></div><div id="realcard"><img id="realimg" src="assets/real_slice.jpg"/></div></div>')
auds = [f'<audio id="bgm" src="assets/sfx/bgm_ducked.wav" data-start="0" data-duration="{TOTAL}" data-volume="1" data-track-index="5"></audio>']
for i, (f, at, v) in enumerate(cues):
    dur = float(subprocess.check_output(f"ffprobe -v error -show_entries format=duration -of csv=p=0 {SFX}/{f}.wav", shell=True))
    dur = round(min(dur, TOTAL - at), 3)
    auds.append(f'<audio id="sfx{i}" src="assets/sfx/{f}.wav" data-start="{at}" data-duration="{dur}" data-volume="{v}" data-track-index="{6 + i}"></audio>')

cap_html = []
for ci, ch in enumerate(chunks):
    spans = []
    for wi, w in enumerate(ch):
        clean = w["w"].strip(",.!?").lower()
        k = clean in KEY
        spans.append(f'<span class="w{" k" if k else ""}" id="w{ci}_{wi}">{E(w["w"].rstrip(",."))}' + ('<i class="ul"></i>' if k else '') + '</span>')
    cap_html.append(f'<div class="chunk" id="c{ci}">{" ".join(spans)}</div>')

CHAPTERS = [("B", "01", "the treat"), ("C1", "02", "the bake"), ("D", "03", "the icing"), ("E1", "04", "the moment"), ("F1", "05", "the menu")]
chap_end = {"B": P["C1"]["s"], "C1": P["D"]["s"], "D": P["E1"]["s"], "E1": P["F1"]["s"], "F1": P["F2"]["s"]}

def star(id_, x, y, s, color="#F6D27A"):
    return (f'<svg class="star" id="{id_}" style="left:{x - s/2}px;top:{y - s/2}px;width:{s}px;height:{s}px" viewBox="0 0 100 100">'
            f'<path d="M50 0 C54 38 62 46 100 50 C62 54 54 62 50 100 C46 62 38 54 0 50 C38 46 46 38 50 0Z" fill="{color}"/></svg>')
HEART = '<path d="M50 88 C20 66 4 50 4 30 C4 14 16 4 30 4 C40 4 46 10 50 17 C54 10 60 4 70 4 C84 4 96 14 96 30 C96 50 80 66 50 88Z"/>'

stars_hook = "".join(star(f"hs{i}", x, y, s) for i, (x, y, s) in enumerate([(230, 1020, 70), (800, 980, 54), (860, 1210, 80), (180, 1260, 44)]))
stars_custom = "".join(star(f"cs{i}", x, y, s) for i, (x, y, s) in enumerate([(160, 1000, 60), (880, 940, 48), (820, 1280, 70)]))
hearts = "".join(f'<svg class="heart" id="ht{i}" style="left:{x}px;top:{y}px;width:{s}px;height:{s}px" viewBox="0 0 100 92">{HEART}</svg>'
                 for i, (x, y, s) in enumerate([(700, 960, 90), (820, 880, 60), (610, 860, 50)]))
hearts2 = "".join(f'<svg class="heart" id="hh{i}" style="left:{x}px;top:{y}px;width:{s}px;height:{s}px" viewBox="0 0 100 92">{HEART}</svg>'
                  for i, (x, y, s) in enumerate([(760, 1000, 80), (860, 930, 54), (680, 900, 44)]))
steam = "".join(f'<path id="st{i}" d="M{x} 520 C{x-40} 470 {x+40} 420 {x} 370 C{x-40} 320 {x+40} 270 {x} 230" />' for i, x in enumerate([430, 540, 650]))

chap_html = "".join(f'<div class="chap" id="ch{n}"><b>{num}</b><span>{E(lbl)}</span></div>' for n, num, lbl in CHAPTERS)

js_lines = []
J = js_lines.append
# --- video motion: punch-in at every piece start, slow push; F1 zoomed to hide the old IG overlay
for name, c, a, b in PIECES:
    p = P[name]; s, d = p["s"], p["d"]
    if name == "F1":
        J(f'tl.set("#vF1",{{scale:1.27,transformOrigin:"50% 50%"}},{s});')
        J(f'tl.fromTo("#vF1",{{scale:1.33}},{{scale:1.27,duration:0.35,ease:"expo.out"}},{s});')
        J(f'tl.to("#vF1",{{scale:1.03,duration:0.55,ease:"power2.inOut"}},{out("F1", 3.08)});')
        J(f'tl.to("#vF1",{{scale:1.06,duration:{round(d - 3.63, 3)},ease:"none"}},{out("F1", 3.63)});')
        continue
    J(f'tl.fromTo("#v{name}",{{scale:1.07,transformOrigin:"50% 42%"}},{{scale:1.0,duration:0.4,ease:"expo.out"}},{s});')
    J(f'tl.to("#v{name}",{{scale:1.035,duration:{round(d - 0.4, 3)},ease:"none"}},{round(s + 0.4, 3)});')
# --- hook flash + stars
J('tl.fromTo("#flash",{opacity:0.9},{opacity:0,duration:0.35,ease:"power2.out"},0);')
for i in range(4):
    J(f'tl.fromTo("#hs{i}",{{scale:0,rotation:-60,opacity:1}},{{scale:1,rotation:0,duration:0.45,ease:"back.out(3)"}},{0.12 + i*0.08});')
    J(f'tl.to("#hs{i}",{{scale:0,rotation:40,opacity:0,duration:0.35,ease:"power2.in"}},{1.05 + i*0.05});')
# steam over the slice close-up (A 1.36 -> end)
st0 = out("A", 1.50)
J(f'tl.set("#steam",{{opacity:1}},{st0});')
for i in range(3):
    J(f'tl.fromTo("#st{i}",{{y:60,opacity:0}},{{y:-40,opacity:0.55,duration:1.3,ease:"sine.out"}},{st0 + i*0.35});')
    J(f'tl.to("#st{i}",{{y:-120,opacity:0,duration:1.0,ease:"sine.in"}},{st0 + 1.3 + i*0.35});')
J(f'tl.set("#steam",{{opacity:0}},{P["B"]["s"]});')
# --- ribbon wipes between scenes
for k, name in enumerate(["B", "C1", "D", "E1", "E3", "F1", "F2"]):
    s = P[name]["s"]
    J(f'tl.fromTo("#rib",{{x:-1500,opacity:1}},{{x:1500,opacity:1,duration:0.5,ease:"power3.inOut"}},{round(s - 0.25, 3)});')
J(f'tl.set("#rib",{{opacity:0}},{TOTAL});')
# --- chapter pills
for n, num, lbl in CHAPTERS:
    s = P[n]["s"] + 0.12; e = chap_end[n] - 0.3
    J(f'tl.fromTo("#ch{n}",{{opacity:0,y:20,scale:0.8}},{{opacity:1,y:0,scale:1,duration:0.4,ease:"back.out(2.5)"}},{round(s, 3)});')
    J(f'tl.to("#ch{n}",{{opacity:0,y:-14,duration:0.25,ease:"power2.in"}},{round(e, 3)});')
# --- captions
for ci, ch in enumerate(chunks):
    s = ch[0]["s"] - 0.06
    nxt = chunks[ci + 1][0]["s"] if ci + 1 < len(chunks) else ch[-1]["e"] + 0.6
    e = min(ch[-1]["e"] + 0.5, nxt - 0.06 - 0.2)
    if ch[-1]["piece"] == "F2": e = min(e, END_S - 0.05)
    J(f'tl.set("#c{ci}",{{opacity:1}},{round(s, 3)});')
    for wi, w in enumerate(ch):
        ws = round(max(w["s"] - 0.06, s), 3)
        J(f'tl.fromTo("#w{ci}_{wi}",{{opacity:0,y:46,scale:0.7,rotation:-4}},{{opacity:1,y:0,scale:1,rotation:0,duration:0.32,ease:"back.out(2.2)"}},{ws});')
        if w["w"].strip(",.!?").lower() in KEY:
            J(f'tl.fromTo("#w{ci}_{wi} .ul",{{scaleX:0}},{{scaleX:1,duration:0.35,ease:"power3.out"}},{round(ws + 0.12, 3)});')
    J(f'tl.to("#c{ci}",{{opacity:0,y:-18,duration:0.18,ease:"power2.in"}},{round(e, 3)});')
    J(f'tl.set("#c{ci}",{{y:0}},{round(e + 0.2, 3)});')
# --- butter ring (overhead ingredients shot)
r0 = out("B", 5.15)
J(f'tl.fromTo("#ring",{{opacity:0,scale:0.4,rotation:-90}},{{opacity:1,scale:1,rotation:0,duration:0.5,ease:"back.out(1.8)"}},{r0});')
J(f'tl.fromTo("#ringlbl",{{opacity:0,x:-30}},{{opacity:1,x:0,duration:0.4,ease:"power3.out"}},{r0 + 0.2});')
J(f'tl.to(["#ring","#ringlbl"],{{opacity:0,duration:0.3}},{out("B", 6.9)});')
# hearts on "love"
h0 = out("B", 6.95)
for i in range(3):
    J(f'tl.fromTo("#ht{i}",{{opacity:0,scale:0,y:40}},{{opacity:1,scale:1,y:0,duration:0.45,ease:"back.out(3)"}},{h0 + i*0.1});')
    J(f'tl.to("#ht{i}",{{opacity:0,y:-60,duration:0.3,ease:"power1.in"}},{round(P["C1"]["s"] - 0.33 + i*0.02, 3)});')
# oven gauge (C2: oven shot local 4.92-6.42)
g0 = out("C2", 4.0)
J(f'tl.fromTo("#gauge",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.5,ease:"back.out(2)"}},{g0});')
J(f'tl.fromTo("#needle",{{rotation:-120,transformOrigin:"50% 100%"}},{{rotation:35,duration:1.3,ease:"power2.inOut"}},{g0 + 0.2});')
J(f'tl.to("#gauge",{{opacity:0,scale:0.8,duration:0.25,ease:"power2.in"}},{out("C2", 6.0)});')
# signature badge (D)
b0 = P["D"]["s"] + 0.35
J(f'tl.fromTo("#badge",{{opacity:0,scale:0.3,rotation:-40}},{{opacity:1,scale:1,rotation:0,duration:0.6,ease:"back.out(2)"}},{b0});')
J(f'tl.fromTo("#badgering",{{rotation:0}},{{rotation:120,duration:{round(P["D"]["d"] + P["D2"]["d"], 3)},ease:"none"}},{b0});')
J(f'tl.to("#badge",{{opacity:0,scale:0.7,duration:0.3,ease:"power2.in"}},{round(P["E1"]["s"] - 0.3, 3)});')
J(f'tl.fromTo("#realbg",{{scale:1.9}},{{scale:2.05,duration:{MAC_D},ease:"none"}},{P["D"]["s"]});')
J(f'tl.fromTo("#realcard",{{y:90,scale:0.86,rotation:4}},{{y:0,scale:1,rotation:-2,duration:0.6,ease:"back.out(1.6)"}},{P["D"]["s"]});')
J(f'tl.fromTo("#realimg",{{scale:1.0}},{{scale:1.12,duration:{MAC_D},ease:"none"}},{P["D"]["s"]});')
J(f'tl.fromTo("#firm",{{opacity:0,scale:0.5,rotation:-12}},{{opacity:1,scale:1,rotation:-4,duration:0.45,ease:"back.out(2.5)"}},{round(P["D"]["s"] + 0.9, 3)});')
J(f'tl.to("#firm",{{opacity:0,duration:0.25}},{round(P["E1"]["s"] - 0.3, 3)});')
# hearts on "happiness"
h1 = out("E2", 3.3)
for i in range(3):
    J(f'tl.fromTo("#hh{i}",{{opacity:0,scale:0,y:40}},{{opacity:1,scale:1,y:0,duration:0.45,ease:"back.out(3)"}},{h1 + i*0.1});')
    J(f'tl.to("#hh{i}",{{opacity:0,y:-160,duration:0.5,ease:"power1.in"}},{round(h1 + 0.62 + i*0.05, 3)});')
# twinkles on custom cakes
c0 = out("E3", 6.55)
for i in range(3):
    J(f'tl.fromTo("#cs{i}",{{scale:0,rotation:-60,opacity:1}},{{scale:1,rotation:0,duration:0.45,ease:"back.out(3)"}},{c0 + i*0.1});')
    J(f'tl.to("#cs{i}",{{scale:0,opacity:0,duration:0.3}},{round(P["F1"]["s"] - 0.3 + i*0.03, 3)});')
# swing tags (F1)
for tid, at in [("tag1", out("F1", 1.05)), ("tag2", out("F1", 2.15))]:
    J(f'tl.fromTo("#{tid}",{{opacity:0,y:-120,rotation:-28,transformOrigin:"50% 0%"}},{{opacity:1,y:0,rotation:0,duration:1.1,ease:"elastic.out(1,0.35)"}},{at});')
J(f'tl.to(["#tag1","#tag2"],{{opacity:0,y:-40,duration:0.3,ease:"power2.in"}},{out("F1", 3.0)});')
# end card
J(f'tl.set("#endbg",{{opacity:1}},{END_S});')
J(f'tl.fromTo("#endbg",{{scale:1.0}},{{scale:1.06,duration:{END_HOLD},ease:"none"}},{END_S});')
J(f'tl.fromTo("#card",{{opacity:0,y:80,scale:0.92}},{{opacity:1,y:0,scale:1,duration:0.6,ease:"expo.out"}},{round(END_S - 0.25, 3)});')
J(f'tl.fromTo("#card .brand",{{opacity:0,y:20}},{{opacity:1,y:0,duration:0.45,ease:"power3.out"}},{round(END_S, 3)});')
J(f'tl.fromTo("#card .sub",{{opacity:0}},{{opacity:1,duration:0.4}},{round(END_S + 0.25, 3)});')
J(f'tl.fromTo("#cta",{{opacity:0,scale:0.6}},{{opacity:1,scale:1,duration:0.5,ease:"back.out(2.6)"}},{round(END_S + 0.45, 3)});')
J(f'tl.fromTo("#cta",{{scale:1}},{{scale:1.05,duration:0.45,yoyo:true,repeat:1,ease:"sine.inOut"}},{round(END_S + 1.0, 3)});')
J(f'tl.fromTo("#shine",{{x:-500}},{{x:700,duration:0.8,ease:"power2.inOut"}},{round(END_S + 0.9, 3)});')

doc = f"""<!doctype html>
<html lang="en" data-resolution="portrait">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=1080, height=1920" />
<script src="assets/gsap.min.js"></script>
<style>
@font-face {{ font-family: "Fraunces"; font-style: italic; font-weight: 500 800; src: url(assets/fonts/fraunces-italic.woff2) format("woff2"); }}
@font-face {{ font-family: "Manrope"; font-weight: 400 800; src: url(assets/fonts/manrope.woff2) format("woff2"); }}
:root {{ --cream:#FFF6E9; --burg:#6B1A2A; --burg2:#4A0F1C; --gold:#E7B655; --gold2:#C98F2E; --cocoa:#2B140E; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html, body {{ width:1080px; height:1920px; overflow:hidden; background:#000; }}
#root {{ position:relative; width:1080px; height:1920px; overflow:hidden; font-family:"Manrope",sans-serif; }}
.vid {{ position:absolute; inset:0; width:1080px; height:1920px; object-fit:cover; }}
#grade {{ position:absolute; inset:0; pointer-events:none; z-index:5;
  background: radial-gradient(ellipse 85% 70% at 50% 45%, rgba(0,0,0,0) 55%, rgba(30,10,5,0.38) 100%),
              linear-gradient(180deg, rgba(255,214,160,0.06), rgba(0,0,0,0) 40%, rgba(40,12,8,0.22) 100%); }}
#flash {{ position:absolute; inset:0; background:#FFF6E9; opacity:0; z-index:40; }}
#rib {{ position:absolute; left:-300px; top:-200px; width:1680px; height:2320px; z-index:39; opacity:0; transform:translateX(-1500px);
  background: linear-gradient(100deg, rgba(0,0,0,0) 28%, rgba(231,182,85,0.0) 30%, #E7B655 36%, #FFF6E9 44%, #6B1A2A 52%, #4A0F1C 60%, rgba(74,15,28,0) 70%); }}
/* captions: band y≈1150-1330, inside safe zone, never over faces */
#caps {{ position:absolute; left:90px; width:860px; top:1150px; height:220px; z-index:20; }}
.chunk {{ position:absolute; inset:0; display:flex; flex-wrap:wrap; justify-content:center; align-items:center; align-content:center;
  gap:6px 18px; opacity:0; text-align:center; }}
.w {{ position:relative; display:inline-block; font-weight:800; font-size:70px; line-height:1.02; color:var(--cream); letter-spacing:-0.01em;
  text-shadow:0 3px 0 rgba(74,15,28,0.55), 0 8px 26px rgba(20,6,3,0.65); opacity:0; }}
.w.k {{ font-family:"Fraunces",serif; font-style:italic; font-weight:700; font-size:90px; letter-spacing:-0.01em; color:#FFD677;
  text-shadow:0 3px 0 #4A0F1C, 0 0 2px #4A0F1C, 0 10px 28px rgba(20,6,3,0.75); padding:0 6px; }}
.ul {{ position:absolute; left:6%; right:6%; bottom:2px; height:9px; border-radius:9px; background:var(--burg); transform-origin:0 50%;
  box-shadow:0 0 0 2px rgba(255,231,168,0.85); }}
/* chapter pill */
.chap {{ position:absolute; left:50%; top:1078px; margin-left:-150px; width:300px; height:58px; z-index:21; opacity:0;
  display:flex; align-items:center; justify-content:center; gap:14px; border-radius:40px; background:rgba(74,15,28,0.88);
  border:2px solid rgba(231,182,85,0.85); box-shadow:0 10px 30px rgba(20,6,3,0.35); }}
.chap b {{ font-family:"Manrope"; font-weight:800; font-size:24px; color:var(--burg2); background:var(--gold); border-radius:20px; padding:2px 12px; }}
.chap span {{ font-family:"Fraunces"; font-style:italic; font-weight:600; font-size:32px; color:var(--cream); }}
.star {{ position:absolute; z-index:22; opacity:0; filter: drop-shadow(0 0 12px rgba(255,220,140,0.9)); }}
.heart {{ position:absolute; z-index:22; opacity:0; fill:#C2364E; stroke:#FFE7A8; stroke-width:4; filter: drop-shadow(0 6px 14px rgba(40,5,10,0.5)); }}
#steam {{ position:absolute; left:0; top:0; width:1080px; height:700px; z-index:12; opacity:0; }}
#steam path {{ fill:none; stroke:rgba(255,248,236,0.9); stroke-width:14; stroke-linecap:round; filter: blur(7px); opacity:0; }}
#ring {{ position:absolute; left:250px; top:820px; width:330px; height:330px; z-index:22; opacity:0; }}
#ringlbl {{ position:absolute; left:560px; top:860px; z-index:22; opacity:0; padding:10px 22px; border-radius:16px; background:var(--cream);
  font-family:"Fraunces"; font-style:italic; font-weight:700; font-size:40px; color:var(--burg); box-shadow:0 10px 28px rgba(20,6,3,0.35);
  transform:rotate(-4deg); }}
#gauge {{ position:absolute; left:640px; top:300px; width:280px; height:280px; z-index:22; opacity:0; border-radius:50%;
  background:radial-gradient(circle at 50% 40%, #FFF6E9 0 58%, #F3E2C6 59% 100%); border:8px solid var(--burg);
  box-shadow:0 14px 36px rgba(20,6,3,0.45), inset 0 0 0 4px rgba(231,182,85,0.8); }}
#gauge .tk {{ position:absolute; left:50%; top:50%; width:4px; height:18px; margin:-125px 0 0 -2px; background:var(--burg); transform-origin:2px 125px; border-radius:2px; }}
#needle {{ position:absolute; left:50%; top:52px; width:10px; height:88px; margin-left:-5px; background:linear-gradient(var(--gold2),var(--burg)); border-radius:6px; }}
#gauge .hub {{ position:absolute; left:50%; top:50%; width:30px; height:30px; margin:-15px; border-radius:50%; background:var(--burg); border:4px solid var(--gold); }}
#gauge .deg {{ position:absolute; left:0; right:0; top:166px; text-align:center; font-weight:800; font-size:44px; color:var(--burg2); }}
#gauge .lbl {{ position:absolute; left:0; right:0; top:214px; text-align:center; font-family:"Fraunces"; font-style:italic; font-weight:600; font-size:26px; color:var(--gold2); }}
#badge {{ position:absolute; left:680px; top:300px; width:270px; height:270px; z-index:22; opacity:0; }}
#badge .core {{ position:absolute; inset:46px; border-radius:50%; background:var(--burg); border:4px solid var(--gold);
  display:flex; flex-direction:column; align-items:center; justify-content:center; box-shadow:0 14px 34px rgba(20,6,3,0.45); }}
#badge .core em {{ font-family:"Fraunces"; font-weight:700; font-size:44px; color:#FFE7A8; line-height:1; }}
#badge .core small {{ font-weight:800; font-size:17px; letter-spacing:0.22em; color:var(--cream); margin-top:6px; }}
#badgering {{ position:absolute; inset:0; }}
.tag {{ position:absolute; z-index:22; opacity:0; display:flex; flex-direction:column; align-items:center; }}
.tag .str {{ width:3px; height:90px; background:linear-gradient(#E7B655,#C98F2E); }}
.tag .body {{ position:relative; padding:18px 34px 18px 50px; background:var(--cream); border-radius:12px 22px 22px 12px; border:3px solid var(--gold);
  font-family:"Fraunces"; font-style:italic; font-weight:700; font-size:50px; color:var(--burg); box-shadow:0 14px 30px rgba(20,6,3,0.4); }}
.tag .body:before {{ content:""; position:absolute; left:18px; top:50%; margin-top:-9px; width:18px; height:18px; border-radius:50%; background:var(--burg); }}
#firm {{ position:absolute; left:120px; top:1000px; padding:0 30px; height:76px; z-index:22; opacity:0; display:flex; align-items:center; justify-content:center;
  border-radius:40px; background:#FFF6E9; border:3px solid #E7B655; box-shadow:0 12px 30px rgba(20,6,3,0.35);
  font-family:"Fraunces"; font-style:italic; font-weight:700; font-size:38px; color:#6B1A2A; }}
#real {{ position:absolute; inset:0; z-index:2; overflow:hidden; background:#2B140E; }}
#realbg {{ position:absolute; left:0; top:330px; width:1080px; filter:blur(26px) saturate(1.1); transform-origin:50% 30%; }}
#realtint {{ position:absolute; inset:0; background:linear-gradient(180deg, rgba(74,15,28,0.55), rgba(43,20,14,0.35) 50%, rgba(74,15,28,0.6)); }}
#realcard {{ position:absolute; left:130px; top:250px; width:820px; height:880px; overflow:hidden; border-radius:28px;
  border:10px solid #FFF6E9; box-shadow:0 30px 70px rgba(10,3,2,0.6), 0 0 0 3px rgba(231,182,85,0.9); }}
#realimg {{ position:absolute; left:50%; top:0; height:100%; width:auto; transform:translateX(-50%); transform-origin:40% 40%; }}
#endbg {{ position:absolute; inset:0; width:1080px; height:1920px; object-fit:cover; opacity:0; z-index:15; }}
#card {{ position:absolute; left:110px; width:860px; top:950px; z-index:30; opacity:0; padding:40px 40px 46px; border-radius:40px; text-align:center;
  background:linear-gradient(160deg, rgba(107,26,42,0.94), rgba(58,10,22,0.96)); border:3px solid rgba(231,182,85,0.9);
  box-shadow:0 30px 70px rgba(15,4,2,0.55); overflow:hidden; }}
#card .brand {{ font-family:"Fraunces"; font-style:italic; font-weight:700; font-size:104px; line-height:1; color:#FFD677; text-shadow:0 4px 18px rgba(0,0,0,0.35); }}
#card .sub {{ margin-top:14px; font-weight:600; font-size:30px; letter-spacing:0.28em; color:var(--cream); text-transform:uppercase; }}
#cta {{ display:inline-flex; margin-top:30px; align-items:center; gap:14px; padding:20px 44px; border-radius:60px; background:var(--cream);
  font-weight:800; font-size:40px; color:var(--burg); box-shadow:0 10px 26px rgba(0,0,0,0.3); }}
#cta i {{ font-style:normal; color:var(--gold2); }}
#shine {{ position:absolute; top:-50%; left:0; width:160px; height:200%; transform:rotate(18deg) translateX(-500px);
  background:linear-gradient(90deg, rgba(255,255,255,0), rgba(255,240,200,0.35), rgba(255,255,255,0)); }}
</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1080" data-height="1920">
{chr(10).join(vids)}
<img id="endbg" class="clip" src="assets/endframe.jpg" data-start="{END_S}" data-duration="{END_HOLD}" data-track-index="1" />
<div id="grade"></div>
<svg id="steam" viewBox="0 0 1080 700">{steam}</svg>
{stars_hook}{stars_custom}{hearts}{hearts2}
<svg id="ring" viewBox="0 0 330 330"><circle cx="165" cy="165" r="140" fill="none" stroke="#FFF6E9" stroke-width="10" stroke-dasharray="26 16" stroke-linecap="round"/>
<circle cx="165" cy="165" r="152" fill="none" stroke="#E7B655" stroke-width="4"/></svg>
<div id="ringlbl">real butter ✦</div>
<div id="gauge">{''.join(f'<i class="tk" style="transform:rotate({a}deg)"></i>' for a in range(-120, 121, 30))}<div id="needle"></div><div class="hub"></div><div class="deg">180°C</div><div class="lbl">golden bake</div></div>
<div id="badge"><svg id="badgering" viewBox="0 0 270 270"><defs><path id="cp" d="M135 135 m-112 0 a112 112 0 1 1 224 0 a112 112 0 1 1 -224 0"/></defs>
<circle cx="135" cy="135" r="132" fill="#FFF6E9" stroke="#E7B655" stroke-width="4"/>
<text font-family="Manrope" font-weight="800" font-size="21" letter-spacing="4" fill="#6B1A2A"><textPath href="#cp">HARD BUTTER ICING ✦ SIGNATURE PALKOVA ✦ </textPath></text></svg>
<div class="core"><em>Palkova</em><small>HARD BUTTER</small></div></div>
<div class="tag" id="tag1" style="left:120px;top:250px"><i class="str"></i><div class="body">Brownies</div></div>
<div class="tag" id="tag2" style="left:560px;top:250px"><i class="str"></i><div class="body">Cupcakes</div></div>
{chap_html}
<div id="caps">{''.join(cap_html)}</div>
<div id="card"><div id="shine"></div><div class="brand">SV Sweethut</div><div class="sub">Premium homemade bakery</div>
<div id="cta"><i>✦</i> DM to order · @svsweethut</div></div>
<div id="firm">✦ hard butter icing · Palkova</div>
<div id="rib"></div>
<div id="flash"></div>
{chr(10).join(auds)}
</div>
<script>
const tl = gsap.timeline({{ paused: true }});
{chr(10).join(js_lines)}
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = tl;
tl.seek(0);
</script>
</body>
</html>
"""
import re
first = {}
for ln in js_lines:
    m = re.match(r'tl\.fromTo\(("[^"]+"|\[[^\]]+\]),.*,([0-9.]+)\);$', ln)
    if m: first[m.group(1)] = min(first.get(m.group(1), 1e9), float(m.group(2)))
fixed = []
for ln in js_lines:
    m = re.match(r'tl\.fromTo\(("[^"]+"|\[[^\]]+\]),.*,([0-9.]+)\);$', ln)
    if m and float(m.group(2)) > first[m.group(1)]:
        i = ln.rfind("},"); ln = ln[:i] + ",immediateRender:false" + ln[i:]
    fixed.append(ln)
doc = doc.replace(chr(10).join(js_lines), chr(10).join(fixed))
open(f"{PROJ}/index.html", "w").write(doc)
json.dump(dict(pieces=P, total=TOTAL, end=END_S, chunks=[[w["w"] for w in c] for c in chunks],
               cues=cues), open(f"{WORK}/timeline.json", "w"), indent=1)
print("TOTAL", TOTAL, "chunks", len(chunks), "cues", len(cues))
for c in chunks: print(f'{c[0]["s"]:6.2f}', " ".join(w["w"] for w in c))
