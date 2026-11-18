"""Render a 30s 9:16 ad for Srichand Timeless serum from a single still.

Usage: python3 tools/render_srichand.py input/srichand_timeless.jpg output/srichand_timeless_30s.mp4
Frames are drawn with Pillow (raqm for correct Thai shaping) and piped to ffmpeg.
"""
import math
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
W, H, FPS, DUR = 1080, 1920, 30, 30.0
FONT_DIR = "work/fonts/"
GOLD = (246, 214, 150)
WHITE = (255, 255, 255)
DEEP = (60, 0, 6)

src = Image.open(SRC).convert("RGB").crop((0, 0, 1140, 1197))  # strip screenshot border
SW, SH = src.size
PIC_W = W
PIC_H = round(W * SH / SW)  # 1134
PIC_Y = 430


def font(weight, size):
    return ImageFont.truetype(f"{FONT_DIR}Kanit-{weight}.ttf", size, layout_engine=ImageFont.Layout.RAQM)


# ---------- static background: blurred, darkened cover of the source ----------
scale = H / SH
bg = src.resize((round(SW * scale), H), Image.BICUBIC)
off = (bg.width - W) // 2
bg = bg.crop((off, 0, off + W, H)).filter(ImageFilter.GaussianBlur(40))
bg = Image.blend(bg, Image.new("RGB", (W, H), (20, 0, 2)), 0.45)

# soft vertical edge mask for the picture band
mask = Image.new("L", (PIC_W, PIC_H), 255)
md = ImageDraw.Draw(mask)
FEATHER = 70
for i in range(FEATHER):
    a = round(255 * (i / FEATHER) ** 1.5)
    md.line([(0, i), (PIC_W, i)], fill=a)
    md.line([(0, PIC_H - 1 - i), (PIC_W, PIC_H - 1 - i)], fill=a)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def lerp(a, b, x):
    return a + (b - a) * x


# ---------- scenes: (start, end, (cx0, cy0, s0), (cx1, cy1, s1)) ; s = window width / source width
SCENES = [
    (0.0, 4.0, (570, 598, 1.00), (560, 560, 0.86)),   # 1 hook: โฉมใหม่!
    (4.0, 10.0, (270, 360, 0.48), (270, 360, 0.40)),  # 2 pump close-up
    (10.0, 17.0, (380, 760, 0.45), (380, 880, 0.45)), # 3 pan down the label
    (17.0, 24.0, (570, 598, 0.90), (570, 598, 1.00)), # 4 slow zoom out
    (24.0, 30.0, (570, 598, 1.00), (570, 598, 0.94)), # 5 CTA
]
XFADE = 0.4


def window_at(i, t):
    s, e, a, b = SCENES[i]
    x = ease((t - s) / (e - s))
    cx, cy, sc = (lerp(a[k], b[k], x) for k in range(3))
    ww, wh = SW * sc, SH * sc
    x0 = min(max(cx - ww / 2, 0), SW - ww)
    y0 = min(max(cy - wh / 2, 0), SH - wh)
    return (x0, y0, x0 + ww, y0 + wh)


def picture(i, t):
    return src.resize((PIC_W, PIC_H), Image.BICUBIC, box=window_at(i, t))


def scene_index(t):
    for i, (s, e, *_ ) in enumerate(SCENES):
        if s <= t < e:
            return i
    return len(SCENES) - 1


# ---------- text helpers ----------
def text_layer(lines, t_in, t):
    """lines: list of (text, font, color, y). Fade + slide up starting at t_in."""
    p = ease((t - t_in) / 0.45)
    if p <= 0:
        return None
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d, sd = ImageDraw.Draw(layer), ImageDraw.Draw(shadow)
    dy = round((1 - p) * 40)
    for k, (txt, f, col, y) in enumerate(lines):
        # stagger each line slightly
        pk = ease((t - t_in - 0.12 * k) / 0.45)
        if pk <= 0:
            continue
        a = round(255 * pk)
        sd.text((W // 2 + 4, y + dy + 6), txt, font=f, fill=(*DEEP, round(a * 0.9)), anchor="mt")
        d.text((W // 2, y + dy), txt, font=f, fill=(*col, a), anchor="mt",
               stroke_width=2, stroke_fill=(*DEEP, round(a * 0.6)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    return Image.alpha_composite(shadow, layer)


F_HUGE = font("ExtraBold", 190)
F_BIG = font("ExtraBold", 150)
F_MED = font("SemiBold", 78)
F_SM = font("Regular", 48)
F_BTN = font("ExtraBold", 72)

TEXTS = [
    [("SRICHAND IN-SKIN", F_SM, GOLD, 150), ("โฉมใหม่!", F_HUGE, WHITE, 200)],
    [("ฝาปั๊ม", F_BIG, WHITE, 130), ("สะดวก ใช้งานง่าย", F_MED, GOLD, 315)],
    [("TIMELESS", F_BIG, WHITE, 140), ("Anti-Aging Facial Serum", F_MED, GOLD, 315)],
    [("เพิ่มสเต็ปบำรุง", F_BIG, WHITE, 140), ("ในรูทีนของคุณ", F_MED, GOLD, 315)],
    [("สั่งในตะกร้านี้", F_MED, WHITE, 150), ("รับโค้ดส่วนลด!", F_BIG, GOLD, 240)],
]
TEXT_CACHE = {}


def cta_button(t):
    """Pulsing pill button with cart icon + down arrow, shown in scene 5."""
    t0 = 24.6
    p = ease((t - t0) / 0.4)
    if p <= 0:
        return None
    pulse = 1 + 0.045 * math.sin((t - t0) * 2 * math.pi * 1.4)
    bw, bh = 700, 150
    layer = Image.new("RGBA", (bw + 80, bh + 160), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    ox, oy = 40, 30
    d.rounded_rectangle((ox, oy + 8, ox + bw, oy + bh + 8), radius=bh // 2, fill=(40, 0, 4, 160))
    d.rounded_rectangle((ox, oy, ox + bw, oy + bh), radius=bh // 2, fill=(*GOLD, 255),
                        outline=(255, 255, 255, 255), width=4)
    # cart icon
    cx, cy = ox + 105, oy + bh // 2
    col = (120, 0, 12, 255)
    d.line([(cx - 45, cy - 35), (cx - 28, cy - 35), (cx - 12, cy + 18), (cx + 38, cy + 18)], fill=col, width=9, joint="curve")
    d.polygon([(cx - 22, cy - 22), (cx + 48, cy - 22), (cx + 38, cy + 8), (cx - 13, cy + 8)], fill=col)
    for wx in (cx - 5, cx + 30):
        d.ellipse((wx - 9, cy + 26, wx + 9, cy + 44), fill=col)
    d.text((ox + 175, cy), "กดตะกร้าเลย", font=F_BTN, fill=col, anchor="lm")
    # bouncing arrow under the button
    ay = oy + bh + 30 + round(10 * abs(math.sin((t - t0) * math.pi * 1.4)))
    ax = ox + bw // 2
    d.polygon([(ax - 34, ay), (ax + 34, ay), (ax, ay + 40)], fill=(255, 255, 255, 255))
    sw, sh = round(layer.width * pulse * p), round(layer.height * pulse * p)
    if sw < 2 or sh < 2:
        return None
    return layer.resize((sw, sh), Image.BICUBIC)


def frame(t):
    i = scene_index(t)
    pic = picture(i, t)
    s = SCENES[i][0]
    # crossfade from previous scene around the cut
    if i > 0 and t < s + XFADE / 2:
        prev = picture(i - 1, min(t, SCENES[i - 1][1] - 1e-3))
        pic = Image.blend(prev, pic, ease((t - (s - XFADE / 2)) / XFADE))
    elif i < len(SCENES) - 1 and t >= SCENES[i][1] - XFADE / 2:
        nxt = picture(i + 1, SCENES[i + 1][0])
        pic = Image.blend(pic, nxt, ease((t - (SCENES[i][1] - XFADE / 2)) / XFADE))
    img = bg.copy()
    img.paste(pic, (0, PIC_Y), mask)
    img = img.convert("RGBA")
    # text: fade out last 0.3s of each scene (except final)
    tl = text_layer(TEXTS[i], s + 0.15, t)
    if tl is not None:
        e = SCENES[i][1]
        if i < len(SCENES) - 1 and t > e - 0.3:
            a = max(0.0, (e - t) / 0.3)
            tl.putalpha(tl.getchannel("A").point(lambda v: round(v * a)))
        img = Image.alpha_composite(img, tl)
    if i == 4:
        b = cta_button(t)
        if b is not None:
            img.alpha_composite(b, (W // 2 - b.width // 2, 1330 - b.height // 2 + 50))
    # global fade-in from black at start
    if t < 0.3:
        img = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), img, t / 0.3)
    return img.convert("RGB")


if __name__ == "__main__":
    if len(sys.argv) > 3:  # preview mode: write stills at given times
        for ts in sys.argv[3].split(","):
            frame(float(ts)).save(f"{OUT}_{ts}.jpg", quality=85)
        sys.exit()
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-t", str(DUR), "-i", "anullsrc=r=48000:cl=stereo",
        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest",
        "-movflags", "+faststart", OUT,
    ], stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for k in range(n):
        ff.stdin.write(frame(k / FPS).tobytes())
    ff.stdin.close()
    sys.exit(ff.wait())
