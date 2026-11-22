#!/usr/bin/env python3
"""Build reels/<name>/scene.json from a short spec.json using the proven 5-row layout + brand defaults.

Usage: python3 build_scene.py reels/<name>        (reads spec.json, writes scene.json)

spec.json:
{
  "title": [ {"text": "PROTEIN SEHARI?", "cue": "protein"},                       # line 1 (ink, 92)
             {"text": "1.6G X BERAT BADAN", "cue": "satu", "color": "blue", "size": 66} ],
  "strike": {"line": 1, "part": "ROSAK DIET?", "cue": "tak"},                       # optional
  "underline": {"line": 1, "cue": "darab", "color": "red"},                         # optional
  "sub": {"text": "contoh: 70kg = ±110g", "cue": "contoh", "color": "note"},        # optional small line under title
  "rows": [ {"cue": "pertama", "box": "TELUR (2 BIJI)", "arrow": "dua", "result": "12G PROTEIN",
             "rcue": "belas", "rcolor": "green", "under": ["teks", "cue"], "note": ["teks", "cue"]}, ... ],
  "punch": {"text": "BAHAGI SETIAP WAKTU MAKAN", "cue": "ingat", "size": 56},
  "circle": {"part": "BAHAGI", "cue": "setiap", "color": "red"},                   # optional, on the punch line
  "punchNote": {"text": "...", "cue": "..."},                                       # optional
  "cta": {"text": "FOLLOW UNTUK TIPS", "cue": "follow", "color": "green"}
}
Remember: cues are matched in spoken order. Within a row the order is box -> under -> arrow -> result -> note.
"""
import json, sys, os

BRAND = dict(handle="@shaan_fittrainer", handlePosition="protect", background="#f8f3ea",
             colors=dict(ink="#1f2a48", red="#d93a3f", green="#1f9d55", blue="#3b6fd8", note="#55596a"))

def build(spec):
    E = []
    def text(t, x, y, size, color, cue, **k):
        E.append(dict(type="text", text=t, x=x, y=y, size=size, color=color, cue=cue, **k)); return len(E) - 1
    title_idx = []
    ys = [330, 440]
    for i, t in enumerate(spec["title"]):
        title_idx.append(text(t["text"], 90, ys[i], t.get("size", 92 if i == 0 else 64),
                              t.get("color", "ink" if i == 0 else "red"), t["cue"], **({"delay": t["delay"]} if "delay" in t else {})))
    if spec.get("strike"):
        s = spec["strike"]; E.append(dict(type="strike", target=title_idx[s["line"]], part=s.get("part"), color="red", cue=s["cue"]))
    if spec.get("underline"):
        u = spec["underline"]; E.append(dict(type="line", target=title_idx[u["line"]], color=u.get("color", "blue"), cue=u["cue"], delay=u.get("delay", 0.3)))
    row0 = 560
    if spec.get("sub"):
        s = spec["sub"]
        text(s["text"], 95, 530, s.get("size", 38 if s.get("font", "hand") == "hand" else 52), s.get("color", "note"), s["cue"],
             **({"font": "hand"} if s.get("font", "hand") == "hand" else {}), **({"delay": s["delay"]} if "delay" in s else {}))
        row0 = 620
    for n, r in enumerate(spec["rows"]):
        y = row0 + n * 170 if row0 == 560 else row0 + n * 170
        E.append(dict(type="badge", text=str(n + 1), x=112, y=y + 50, color="red", cue=r["cue"]))
        E.append(dict(type="box", text=r["box"], x=160, y=y, w=400, h=100, cue=r["cue"], delay=0.15))
        if r.get("under"): text(r["under"][0], 165, y + 138, 30, "blue", r["under"][1], font="hand")
        E.append(dict(type="arrow", x1=575, x2=640, y=y + 50, cue=r["arrow"]))
        res = r["result"]
        text(res, 655, y + 65, 40 if len(res) > 14 else 44 if len(res) > 12 else 48, r.get("rcolor", "green"), r["rcue"],
             **({"delay": 0.2} if r["rcue"] == r["arrow"] else {}))
        if r.get("note"): text(r["note"][0], 655, y + 112, 30, "note", r["note"][1], font="hand")
    py = row0 + 5 * 170 + 110          # punchline baseline
    p = spec["punch"]
    pi = text(p["text"], 100, py, p.get("size", 62), "ink", p["cue"])
    if spec.get("circle"):
        c = spec["circle"]; E.append(dict(type="circle", target=pi, part=c["part"], color=c.get("color", "red"), cue=c["cue"]))
    cy = py + 50
    if spec.get("punchNote"):
        pn = spec["punchNote"]; text(pn["text"], pn.get("x", 260), py + 80, 40, pn.get("color", "blue"), pn["cue"], font="hand"); cy = py + 130
    c = spec["cta"]
    E.append(dict(type="box", text=c["text"], x=280, y=cy, w=520, h=100, color=c.get("color", "green"), cue=c["cue"]))
    return dict(title=spec["title"][0]["text"], audio="audio/voice.mp3", words="audio/words.json", **BRAND, elements=E)

if __name__ == "__main__":
    d = sys.argv[1]
    spec = json.load(open(os.path.join(d, "spec.json")))
    json.dump(build(spec), open(os.path.join(d, "scene.json"), "w"), indent=1, ensure_ascii=False)
    print("wrote", os.path.join(d, "scene.json"))
