"""Whiteboard-style animation from the 3x3 storyboard.

Each 5s scene: a marker "draws" a pencil sketch of the panel in zig-zag
strokes, then the full-colour panel fades in and holds.
Usage: python3 whiteboard.py STORYBOARD.png OUT_silent.mp4
"""
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

SRC, OUT = sys.argv[1], sys.argv[2]
W, H, FPS = 1080, 1920, 30
SCENE = 5.0
DRAW_END, COLOR_END = 2.8, 3.6
BANDS = 7

sheet = Image.open(SRC).convert("RGB")
xs = [(8, 337), (348, 676), (687, 1017)]
ys = [(8, 506), (517, 1013), (1024, 1531)]
panels = [sheet.crop((x0, y0, x1, y1)) for y0, y1 in ys for x0, x1 in xs]


def sketch(img):
    g = ImageOps.grayscale(img)
    inv = ImageOps.invert(g).filter(ImageFilter.GaussianBlur(12))
    a, b = np.asarray(g, float), np.asarray(inv, float)
    dodge = np.clip(a * 255.0 / np.maximum(255.0 - b, 1), 0, 255)
    dodge = 255 - (255 - dodge) * 1.6  # darken lines a little
    s = np.clip(dodge, 0, 255)
    # keep the green/navy title boxes faintly tinted so text reads well
    return np.repeat(s[..., None], 3, axis=2)


def marker():
    m = Image.new("RGBA", (260, 260), (0, 0, 0, 0))
    d = ImageDraw.Draw(m)
    # body pointing down-left; tip at (20, 240)
    d.polygon([(20, 240), (40, 200), (60, 220)], fill=(30, 30, 30, 255))
    d.polygon([(40, 200), (60, 220), (200, 80), (180, 60)], fill=(25, 45, 85, 255))
    d.polygon([(180, 60), (200, 80), (245, 35), (225, 15)], fill=(140, 175, 140, 255))
    d.line([(52, 196), (190, 58)], fill=(255, 255, 255, 90), width=4)
    return m.filter(ImageFilter.SMOOTH)


PEN = marker()
PH = int(W * 498 / 329)  # panel height on screen
TOP = (H - PH) // 2
rng = np.random.default_rng(7)

ff = subprocess.Popen(
    ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
     "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset",
     "medium", "-crf", "19", "-pix_fmt", "yuv420p", OUT],
    stdin=subprocess.PIPE)

board = np.full((H, W, 3), 250, np.uint8)
yy, xx = np.mgrid[0:PH, 0:W]
band_h = PH / BANDS
band_idx = np.minimum((yy / band_h).astype(int), BANDS - 1)
jitter = rng.normal(0, 18, (PH, 1)).astype(float)  # ragged stroke edge

for p in panels:
    color = np.asarray(p.resize((W, PH), Image.LANCZOS), float)
    sk = sketch(p.resize((W, PH), Image.LANCZOS))
    sk = 0.85 * sk + 0.15 * color  # hint of colour in the sketch
    for f in range(int(SCENE * FPS)):
        t = f / FPS
        frame = board.copy()
        if t < DRAW_END:
            prog = (t / DRAW_END) * BANDS
            b, frac = int(prog), prog - int(prog)
            col = np.where(band_idx % 2 == 0, xx, W - 1 - xx) + jitter
            mask = (band_idx < b) | ((band_idx == b) & (col < frac * W))
            region = np.where(mask[..., None], sk, 250)
            frame[TOP:TOP + PH] = region.astype(np.uint8)
            px = frac * W if b % 2 == 0 else W - frac * W
            py = TOP + (b + 0.5) * band_h + 25 * np.sin(t * 40)
            img = Image.fromarray(frame)
            img.paste(PEN, (int(px) - 20, int(py) - 240), PEN)
            frame = np.asarray(img)
        else:
            a = min(1.0, (t - DRAW_END) / (COLOR_END - DRAW_END))
            frame[TOP:TOP + PH] = (sk * (1 - a) + color * a).astype(np.uint8)
        ff.stdin.write(np.ascontiguousarray(frame).tobytes())

ff.stdin.close()
ff.wait()
