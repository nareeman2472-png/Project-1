"""Srichand Timeless v4 ad: motion-graphics clip synced to the user's voiceover.

Usage:
  python3 tools/render_srichand_v4.py input/srichand_timeless.jpg input/voiceover_v4.mp3 output/srichand_timeless_v4.mp4
  add a 4th arg "t1,t2,..." to write preview stills instead of the video.
Timings come from pause detection on the voiceover (26 phrases = 26 script phrases).
"""
import math
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

SRC, AUDIO, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
W, H, FPS = 1080, 1920, 30
DUR = float(subprocess.check_output(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", AUDIO]).decode())
F = "work/fonts/"
GOLD, WHITE, DEEP, RED = (246, 214, 150), (255, 255, 255), (50, 0, 5), (179, 18, 27)
RAQM = ImageFont.Layout.RAQM


def font(name, size):
    return ImageFont.truetype(F + name, size, layout_engine=RAQM)


K_XB = lambda s: font("Kanit-ExtraBold.ttf", s)
K_SB = lambda s: font("Kanit-SemiBold.ttf", s)
K_RG = lambda s: font("Kanit-Regular.ttf", s)
CINZ = lambda s: font("Cinzel-Bold.ttf", s)
EMOJI_FONT = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 109, layout_engine=RAQM)
_emoji_cache = {}


def emoji(ch, size):
    key = (ch, size)
    if key not in _emoji_cache:
        im = Image.new("RGBA", (160 * max(1, len(ch)), 140), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((0, 0), ch, font=EMOJI_FONT, embedded_color=True)
        im = im.crop(im.getbbox())
        _emoji_cache[key] = im.resize((round(im.width * size / im.height), size), Image.LANCZOS)
    return _emoji_cache[key]


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 0.5 - 0.5 * math.cos(math.pi * x)


def back_out(x):  # overshoot pop
    x = min(max(x, 0.0), 1.0)
    c = 1.70158
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


lerp = lambda a, b, x: a + (b - a) * x

# ---------------- source + static layers ----------------
src = Image.open(SRC).convert("RGB").crop((0, 0, 1140, 1197))
SW, SH = src.size
PIC_H, PIC_Y = round(W * SH / SW), 430

cover = src.resize((round(SW * H / SH), H), Image.BICUBIC)
o = (cover.width - W) // 2
cover = cover.crop((o, 0, o + W, H)).filter(ImageFilter.GaussianBlur(40))
BG_RED = Image.blend(cover, Image.new("RGB", (W, H), (20, 0, 2)), 0.45).convert("RGBA")
grey = ImageOps.grayscale(cover).convert("RGB")
BG_GREY = Image.blend(grey, Image.new("RGB", (W, H), (12, 12, 16)), 0.6).convert("RGBA")

mask = Image.new("L", (W, PIC_H), 255)
md = ImageDraw.Draw(mask)
for i in range(70):
    a = round(255 * (i / 70) ** 1.5)
    md.line([(0, i), (W, i)], fill=a)
    md.line([(0, PIC_H - 1 - i), (W, PIC_H - 1 - i)], fill=a)

# ---------------- timeline (seconds, from the voiceover) ----------------
PHRASES = [  # (start, end, caption)
    (0.00, 1.23, "อยากลองเรตินอล"), (1.44, 2.15, "แต่กลัวแสบ"), (2.47, 3.19, "กลัวหน้าลอก"),
    (3.42, 5.27, "ผิวก็เริ่มดูไม่เด้งเหมือนเดิม ใช่มั้ย?"),
    (5.80, 6.85, "งั้นต้องตัวนี้เลย"), (7.07, 9.01, "ศรีจันทร์ อินสกิน ไทม์เลส เซรั่ม"),
    (9.26, 10.64, "เป็นแบรนด์ที่ทำเพื่อคนไทย"), (10.83, 12.90, "ใช้บาคูชิออล สารสกัดจากพืช"),
    (13.11, 14.24, "ทางเลือกแทนเรตินอล"), (14.46, 15.89, "แถมโฉมใหม่เป็นฝาปั๊ม"),
    (16.04, 17.17, "กดใช้ง่ายกว่าเดิม"), (17.47, 19.75, "บาคูชิออล ช่วยให้ผิวดูเรียบเนียน"),
    (20.02, 20.78, "ไฮยาลูรอน"), (20.93, 23.02, "เติมความชุ่มชื้นให้ผิวดูอิ่มฟู"),
    (23.28, 24.18, "ไนอาซินาไมด์"), (24.36, 25.86, "ช่วยให้ผิวดูกระจ่างใส"),
    (26.10, 27.85, "เซราไมด์ห้าชนิดกับเปปไทด์"), (28.04, 30.37, "ช่วยดูแลผิวให้ดูแข็งแรง ดูเด้ง"),
    (30.59, 32.05, "ใช้ได้ทั้งเช้าและก่อนนอน"), (32.24, 34.11, "หลังล้างหน้า แค่ 1–2 ปั๊ม"),
    (34.27, 35.76, "ลูบให้ทั่วหน้าและลำคอ"), (35.96, 37.64, "ตอนเช้า ทากันแดดทับด้วยนะ"),
    (37.95, 38.53, "ตัวเดียวครบ"), (38.77, 41.31, "ทั้งชุ่มชื้น กระจ่างใส ดูอ่อนเยาว์"),
    (41.51, 43.82, "สั่งในตะกร้านี้ รับโค้ดส่วนลดไปเลย"), (44.01, 45.24, "กดตะกร้าด้านล่างได้เลย!"),
]

# shots: (start, end, window_from, window_to); window = (cx, cy, scale) on the source; None = no product band
SHOTS = [
    (0.00, 5.55, None, None),
    (5.55, 9.13, (570, 598, 1.00), (560, 570, 0.86)),
    (9.13, 14.35, (380, 760, 0.45), (380, 880, 0.45)),
    (14.35, 17.32, (270, 360, 0.48), (270, 360, 0.40)),
    (17.32, 19.89, (420, 740, 0.60), (420, 720, 0.54)),
    (19.89, 23.15, (570, 598, 0.95), (570, 598, 0.85)),
    (23.15, 25.98, (390, 800, 0.50), (400, 760, 0.46)),
    (25.98, 30.48, (570, 598, 0.88), (570, 598, 1.00)),
    (30.48, 35.86, (270, 380, 0.46), (300, 420, 0.52)),
    (35.86, 37.80, (570, 598, 1.00), (570, 598, 0.94)),
    (37.80, 41.41, (500, 650, 0.84), (570, 598, 1.00)),
    (41.41, 99.00, (570, 598, 1.00), (570, 598, 0.93)),
]
XF = 0.3


def window(shot, t):
    s, e, a, b = shot
    x = ease((t - s) / max(e - s, 0.01)) if e < 90 else ease((t - s) / (DUR - s))
    cx, cy, sc = (lerp(a[k], b[k], x) for k in range(3))
    ww, wh = SW * sc, SH * sc
    x0 = min(max(cx - ww / 2, 0), SW - ww)
    y0 = min(max(cy - wh / 2, 0), SH - wh)
    return (x0, y0, x0 + ww, y0 + wh)


def band(i, t):
    sh = SHOTS[i]
    if sh[2] is None:
        return None
    return src.resize((W, PIC_H), Image.BICUBIC, box=window(sh, t))


def shot_index(t):
    for i, s in enumerate(SHOTS):
        if s[0] <= t < s[1]:
            return i
    return len(SHOTS) - 1


# ---------------- drawing helpers ----------------
def shadowed_text(layer, xy, txt, fnt, col, alpha=255, anchor="mt", stroke=2):
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).text((xy[0] + 4, xy[1] + 6), txt, font=fnt, fill=(*DEEP, round(alpha * 0.9)), anchor=anchor)
    layer.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)))
    ImageDraw.Draw(layer).text(xy, txt, font=fnt, fill=(*col, alpha), anchor=anchor,
                               stroke_width=stroke, stroke_fill=(*DEEP, round(alpha * 0.6)))


def pop(t, t0, dur=0.35):
    return back_out((t - t0) / dur) if t >= t0 else 0.0


def fade(t, t0, dur=0.3):
    return ease((t - t0) / dur)


def place(canvas, im, cx, cy, scale=1.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    if scale != 1.0:
        im = im.resize((max(1, round(im.width * scale)), max(1, round(im.height * scale))), Image.BICUBIC)
    if alpha < 1.0:
        im = im.copy()
        im.putalpha(im.getchannel("A").point(lambda v: round(v * alpha)))
    canvas.alpha_composite(im, (round(cx - im.width / 2), round(cy - im.height / 2)))


_txt_cache = {}


def text_sprite(txt, fnt, col, stroke=2, pad=30):
    key = (txt, fnt.path, fnt.size, col, stroke)
    if key not in _txt_cache:
        d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        l, tp, r, b = d.textbbox((0, 0), txt, font=fnt, stroke_width=stroke)
        im = Image.new("RGBA", (r - l + 2 * pad, b - tp + 2 * pad), (0, 0, 0, 0))
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).text((pad - l + 4, pad - tp + 6), txt, font=fnt, fill=(*DEEP, 230))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(9)))
        ImageDraw.Draw(im).text((pad - l, pad - tp), txt, font=fnt, fill=(*col, 255),
                                stroke_width=stroke, stroke_fill=(*DEEP, 150))
        _txt_cache[key] = im
    return _txt_cache[key]


def row_sprite(parts, gap=18):
    """parts: list of PIL images; returns them laid out horizontally, vertically centred."""
    w = sum(p.width for p in parts) + gap * (len(parts) - 1)
    h = max(p.height for p in parts)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = 0
    for p in parts:
        im.alpha_composite(p, (x, (h - p.height) // 2))
        x += p.width + gap
    return im


def panel(w, h, alpha=150):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), radius=36, fill=(30, 0, 4, alpha),
                                         outline=(*GOLD, 200), width=3)
    return im


# ---------------- per-section overlays ----------------
def problem_section(c, t):
    items = [(0.00, "อยากลองเรตินอล?", "🤔"), (1.44, "กลัวแสบ", "😣"),
             (2.47, "กลัวหน้าลอก", "😖"), (3.42, "ผิวดูไม่เด้งเหมือนเดิม?", "😟")]
    f = K_XB(92)
    for k, (t0, txt, em) in enumerate(items):
        p = pop(t, t0)
        if p <= 0:
            continue
        spr = row_sprite([emoji(em, 96), text_sprite(txt, f, WHITE if k != 3 else GOLD)], gap=10)
        place(c, spr, W / 2, 560 + k * 230, scale=0.6 + 0.4 * p, alpha=min(1, p))


def header(c, t, t0, lines, t_end):
    """lines: list of (sprite, y). Pop in at t0, fade out before t_end."""
    a = 1.0
    if t > t_end - 0.25:
        a = max(0.0, (t_end - t) / 0.25)
    for k, (spr, y) in enumerate(lines):
        p = pop(t, t0 + 0.1 * k)
        if p > 0:
            place(c, spr, W / 2, y, 0.7 + 0.3 * p, min(1, p) * a)


def card(c, t, t0, t_end, icon, title, sub, title_font=None):
    a = 1.0 if t < t_end - 0.2 else max(0.0, (t_end - t) / 0.2)
    p = pop(t, t0, 0.4)
    if p <= 0:
        return
    tf = title_font or CINZ(76)
    title_s = text_sprite(title, tf, GOLD, stroke=1)
    sub_s = text_sprite(sub, K_XB(80), WHITE)
    top = row_sprite([emoji(icon, 92), title_s], gap=8)
    pw = max(top.width, sub_s.width) + 40
    pn = panel(min(pw, 1020), 300)
    pn.alpha_composite(top, ((pn.width - top.width) // 2, 10))
    pn.alpha_composite(sub_s, ((pn.width - sub_s.width) // 2, 140))
    x = lerp(-W / 2, W / 2, ease((t - t0) / 0.4))
    place(c, pn, x, 270, 1.0, min(1, p) * a)


def check_row(c, t):
    pa = fade(t, 38.7, 0.25)
    if pa > 0:
        place(c, panel(520, 330, 170), W / 2, 1225, 1.0, pa)
    items = [(38.77, "ชุ่มชื้น"), (39.6, "กระจ่างใส"), (40.4, "ดูอ่อนเยาว์")]
    for k, (t0, txt) in enumerate(items):
        p = pop(t, t0)
        if p > 0:
            spr = row_sprite([emoji("✅", 64), text_sprite(txt, K_SB(64), WHITE)], gap=4)
            place(c, spr, W / 2, 1125 + k * 100, 0.6 + 0.4 * p, min(1, p))


def cta_button(c, t, t0):
    p = ease((t - t0) / 0.4)
    if p <= 0:
        return
    pulse = 1 + 0.045 * math.sin((t - t0) * 2 * math.pi * 1.4)
    bw, bh = 700, 150
    lay = Image.new("RGBA", (bw + 80, bh + 120), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    ox, oy = 40, 10
    d.rounded_rectangle((ox, oy + 8, ox + bw, oy + bh + 8), radius=bh // 2, fill=(40, 0, 4, 160))
    d.rounded_rectangle((ox, oy, ox + bw, oy + bh), radius=bh // 2, fill=(*GOLD, 255), outline=WHITE, width=4)
    em = emoji("🛒", 84)
    lay.alpha_composite(em, (ox + 55, oy + (bh - em.height) // 2))
    d.text((ox + 165, oy + bh // 2), "กดตะกร้าเลย", font=K_XB(72), fill=(120, 0, 12), anchor="lm")
    ay = oy + bh + 22 + round(12 * abs(math.sin((t - t0) * math.pi * 1.4)))
    d.polygon([(ox + bw / 2 - 34, ay), (ox + bw / 2 + 34, ay), (ox + bw / 2, ay + 40)], fill=WHITE)
    place(c, lay, W / 2, 1250, pulse * (0.6 + 0.4 * back_out((t - t0) / 0.4)), p)


def caption(c, t):
    for s, e, txt in PHRASES:
        if s - 0.05 <= t < e + 0.15:
            spr = text_sprite(txt, K_SB(58), WHITE, stroke=0, pad=0)
            pw, ph = min(spr.width + 70, 1000), spr.height + 44
            pn = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
            ImageDraw.Draw(pn).rounded_rectangle((0, 0, pw - 1, ph - 1), radius=ph // 2, fill=(0, 0, 0, 150))
            if spr.width > pw - 40:
                spr = spr.resize((pw - 40, round(spr.height * (pw - 40) / spr.width)), Image.BICUBIC)
            pn.alpha_composite(spr, ((pw - spr.width) // 2, (ph - spr.height) // 2))
            a = min(fade(t, s - 0.05, 0.12), 1.0)
            if t > e:
                a *= max(0.0, (e + 0.15 - t) / 0.15)
            place(c, pn, W / 2, 1480, 1.0, a)
            return


def overlays(c, t):
    if t < 5.55:
        problem_section(c, t)
        return
    if t < 9.13:
        header(c, t, 5.8, [(text_sprite("SRICHAND IN-SKIN", CINZ(46), GOLD, 1), 150),
                           (text_sprite("TIMELESS", CINZ(150), WHITE, 2), 270)], 9.13)
    elif t < 10.75:
        header(c, t, 9.26, [(text_sprite("แบรนด์ที่ทำ", K_SB(80), WHITE), 160),
                            (text_sprite("เพื่อคนไทย", K_XB(140), GOLD), 290)], 10.75)
    elif t < 14.35:
        card(c, t, 10.83, 14.35, "🌿", "BAKUCHIOL", "ทางเลือกแทนเรตินอล")
    elif t < 17.32:
        header(c, t, 14.46, [(text_sprite("โฉมใหม่! ฝาปั๊ม", K_XB(120), WHITE), 160),
                             (text_sprite("กดใช้ง่ายกว่าเดิม", K_SB(76), GOLD), 310)], 17.32)
    elif t < 19.89:
        card(c, t, 17.40, 19.89, "🌿", "BAKUCHIOL", "ผิวดูเรียบเนียน")
    elif t < 23.15:
        card(c, t, 19.95, 23.15, "💧", "HYALURONIC", "ชุ่มชื้น ดูอิ่มฟู")
    elif t < 25.98:
        card(c, t, 23.20, 25.98, "✨", "NIACINAMIDE", "ผิวดูกระจ่างใส")
    elif t < 30.48:
        card(c, t, 26.05, 30.48, "🛡️", "5 CERAMIDES + PEPTIDES", "ผิวดูแข็งแรง ดูเด้ง", CINZ(56))
    elif t < 35.86:
        top = row_sprite([emoji("☀️", 90), text_sprite("เช้า", K_XB(100), WHITE),
                          emoji("🌙", 90), text_sprite("ก่อนนอน", K_XB(100), WHITE)], gap=14)
        steps = text_sprite("ล้างหน้า → 1–2 ปั๊ม → หน้า+คอ", K_SB(64), GOLD)
        header(c, t, 30.59, [(top, 170)], 35.86)
        if t >= 32.24:
            header(c, t, 32.24, [(steps, 320)], 35.86)
    elif t < 37.80:
        header(c, t, 35.96, [(row_sprite([emoji("☀️", 90), text_sprite("ตอนเช้า", K_XB(100), WHITE)]), 170),
                             (text_sprite("+ ทากันแดดทับ", K_XB(90), GOLD), 320)], 37.80)
    elif t < 41.41:
        header(c, t, 37.95, [(text_sprite("ตัวเดียวครบ!", K_XB(140), WHITE), 230)], 41.41)
        check_row(c, t)
    else:
        header(c, t, 41.51, [(text_sprite("สั่งในตะกร้านี้", K_SB(80), WHITE), 150),
                             (text_sprite("รับโค้ดส่วนลด!", K_XB(140), GOLD), 260)], 999)
        cta_button(c, t, 42.0)
    caption(c, t)


def frame(t):
    i = shot_index(t)
    base = BG_GREY if SHOTS[i][2] is None else BG_RED
    c = base.copy()
    # background crossfade grey -> red at the reveal
    if i == 1 and t < SHOTS[1][0] + 0.25:
        c = Image.blend(BG_GREY, BG_RED, ease((t - SHOTS[1][0]) / 0.25))
    pic = band(i, t)
    s, e = SHOTS[i][0], SHOTS[i][1]
    if pic is not None and i > 1 and t < s + XF / 2:
        prev = band(i - 1, s - 1e-3)
        if prev is not None:
            pic = Image.blend(prev, pic, ease((t - (s - XF / 2)) / XF))
    elif pic is not None and i < len(SHOTS) - 1 and t >= e - XF / 2:
        pic = Image.blend(pic, band(i + 1, SHOTS[i + 1][0]), ease((t - (e - XF / 2)) / XF))
    if pic is not None:
        if i == 1:  # reveal: scale-in pop
            p = back_out((t - s) / 0.45)
            sc = 0.8 + 0.2 * p
            pr = pic.resize((round(W * sc), round(PIC_H * sc)), Image.BICUBIC)
            mr = mask.resize(pr.size)
            c.paste(pr.convert("RGBA"), (round((W - pr.width) / 2), round(PIC_Y + (PIC_H - pr.height) / 2)),
                    mr.point(lambda v: round(v * min(1, p))))
        else:
            c.paste(pic.convert("RGBA"), (0, PIC_Y), mask)
    # white flash on the reveal
    if 5.55 <= t < 5.8:
        c = Image.blend(c, Image.new("RGBA", (W, H), (255, 255, 255, 255)), 0.6 * (1 - (t - 5.55) / 0.25))
    overlays(c, t)
    if t < 0.2:
        c = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), c, t / 0.2)
    return c.convert("RGB")


if __name__ == "__main__":
    if len(sys.argv) > 4:
        for ts in sys.argv[4].split(","):
            frame(float(ts)).save(f"{OUT}_{ts}.jpg", quality=85)
        sys.exit()
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-i", AUDIO,
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11,afade=t=out:st=%.2f:d=0.2" % (DUR - 0.2),
        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-shortest",
        "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    for k in range(int(DUR * FPS)):
        ff.stdin.write(frame(k / FPS).tobytes())
    ff.stdin.close()
    sys.exit(ff.wait())
