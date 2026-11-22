"""Edits applied to each enlarged storyboard panel (1080 px wide)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"


def remove_time_badge(img):
    """Paint over the navy '0-5s' badge in the top-left corner."""
    a = np.asarray(img).astype(int).copy()
    navy = (a[..., 2] - a[..., 0] > 15) & (a.max(axis=2) < 110)
    for y in range(0, 150):
        xs = np.nonzero(navy[y, :620])[0]
        if len(xs) < 20:
            continue
        r = xs.max()
        src = a[y, min(r + 16, a.shape[1] - 1)]
        a[y, :r + 8] = src
    out = Image.fromarray(a.astype(np.uint8))
    region = out.crop((0, 0, 640, 160)).filter(ImageFilter.GaussianBlur(3))
    out.paste(region, (0, 0))
    return out


def text_center(draw, cx, y, s, size, fill=(255, 255, 255)):
    f = ImageFont.truetype(FONT, size)
    w = draw.textlength(s, font=f)
    draw.text((cx - w / 2, y), s, font=f, fill=fill)


def last_panel(img):
    img = img.copy()
    a = np.asarray(img)
    d = ImageDraw.Draw(img)
    # DM box: "DM Coach / shaan_fittrainer" -> "DM / shaan_fittrainer"
    box_navy = tuple(int(v) for v in a[580, 425])
    d.rectangle((430, 485, 1022, 675), fill=box_navy)
    text_center(d, 724, 495, "DM", 66)
    text_center(d, 724, 580, "shaan_fittrainer", 66)
    # bottom-right logo: dumbbell + "Coach Shaan" -> dumbbell + "shaan_fittrainer"
    dumbbell = img.crop((585, 1440, 772, 1545))
    navy = tuple(int(v) for v in a[1600, 1000])
    m = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(m)
    # area under the diagonal green stripe
    md.polygon([(560, 1460), (1075, 1235), (1075, 1590), (560, 1590)], fill=255)
    img.paste(Image.new("RGB", img.size, navy), (0, 0), m)
    d = ImageDraw.Draw(img)
    dumbbell = dumbbell.resize((131, 74), Image.LANCZOS)
    da = np.asarray(dumbbell).astype(int)
    green = np.clip((da[..., 1] - da[..., 2]) * 6 + (da.sum(axis=2) - 300) // 2, 0, 255)
    img.paste(dumbbell, (830 - 65, 1375), Image.fromarray(green.astype(np.uint8)))
    text_center(d, 830, 1470, "shaan_fittrainer", 56)
    return img


def edit(img, index):
    img = remove_time_badge(img)
    if index == 8:
        img = last_panel(img)
    return img
