#!/usr/bin/env python3
"""Draw THE WORLD — 24 November 2026, a newspaper front page (1024x1024).

Build-time renderer: runs on the build machine with Pillow and the system
DejaVu fonts, and writes entry.png next to this file. The shipped program
(main.py) only copies that image to /output/entry.png, so the graded run
needs nothing but the Python standard library.

All facts were verified against reporting on 24 November 2026 (Le Monde,
Reuters, AP, CNN, El Tiempo, Mediazona/Meduza, Banten police).
"""
import os
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (248, 244, 233)
INK = (18, 18, 18)
MUTED = (84, 84, 78)
RED = (158, 27, 30)
NAVY = (22, 50, 79)
GREEN = (74, 116, 0)
GREEN_FILL = (118, 185, 0)
RULE = (18, 18, 18)
LIGHT_RULE = (170, 164, 150)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(text, fnt, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    lines = []
    for raw in text.split("\n"):
        words = raw.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for word in words[1:]:
            trial = cur + " " + word
            if fnt.getlength(trial) <= max_w:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def draw_tracked(d, xy, text, fnt, fill, tracking=2):
    """Draw text with extra pixels between characters; returns width used."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill)
        x += fnt.getlength(ch) + tracking
    return x


def text_w(fnt, text, tracking=0):
    if tracking:
        return sum(fnt.getlength(c) + tracking for c in text) - tracking
    return fnt.getlength(text)


def para(d, x, y, w, text, fnt, fill=INK, leading=1.28):
    """Draw a wrapped paragraph; returns the y below it."""
    lh = int(fnt.size * leading)
    for line in wrap(text, fnt, w):
        d.text((x, y), line, font=fnt, fill=fill)
        y += lh
    return y


def kicker(d, x, y, text, color=RED, size=15):
    fnt = font(SANS_B, size)
    draw_tracked(d, (x, y), text.upper(), fnt, color, tracking=2)
    return y + size + 8


def headline(d, x, y, w, text, size, max_lines=None, fill=INK):
    """Draw a wrapped bold serif headline; returns the y below it."""
    fnt = font(SERIF_B, size)
    lines = wrap(text, fnt, w)
    if max_lines:
        lines = lines[:max_lines]
    lh = int(size * 1.08)
    for line in lines:
        d.text((x, y), line, font=fnt, fill=fill)
        y += lh
    return y


def hrule(d, x0, x1, y, width=1, fill=RULE):
    d.line([(x0, y), (x1, y)], fill=fill, width=width)


def vrule(d, x, y0, y1, width=1, fill=LIGHT_RULE):
    d.line([(x, y0), (x, y1)], fill=fill, width=width)


def draw_chip(d, x, y, w, h):
    """A simple microchip: green body, gold pins, inner die."""
    d.rounded_rectangle([x, y, x + w, y + h], radius=8, fill=GREEN_FILL,
                        outline=INK, width=2)
    pin = 7
    for i in range(4):
        px = x + 12 + i * ((w - 24) // 3)
        d.rectangle([px, y - pin, px + 5, y], fill=(212, 175, 55))
        d.rectangle([px, y + h, px + 5, y + h + pin], fill=(212, 175, 55))
    for i in range(3):
        py = y + 12 + i * ((h - 24) // 2)
        d.rectangle([x - pin, py, x, py + 5], fill=(212, 175, 55))
        d.rectangle([x + w, py, x + w + pin, py + 5], fill=(212, 175, 55))
    d.rectangle([x + w * 0.28, y + h * 0.28, x + w * 0.72, y + h * 0.72],
                fill=(38, 74, 0))
    d.text((x + w * 0.5, y + h * 0.5), "NVDA", font=font(SANS_B, 13),
           fill=(255, 255, 255), anchor="mm")


def draw_radar(d, cx, cy, r):
    """Concentric radar rings with a blip and a sweep line."""
    for rr, wd in ((r, 1), (int(r * 0.66), 1), (int(r * 0.33), 1)):
        d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=NAVY, width=wd)
    d.line([(cx - r, cy), (cx + r, cy)], fill=LIGHT_RULE, width=1)
    d.line([(cx, cy - r), (cx, cy + r)], fill=LIGHT_RULE, width=1)
    d.line([(cx, cy), (cx + r * 0.7, cy - r * 0.7)], fill=RED, width=2)
    d.ellipse([cx + r * 0.45 - 4, cy - r * 0.45 - 4,
               cx + r * 0.45 + 4, cy - r * 0.45 + 4], fill=RED)


def draw_flame(d, cx, cy, s):
    """A simple flame mark for the factory-fire story."""
    pts = [(cx, cy - s), (cx + s * 0.62, cy - s * 0.1),
           (cx + s * 0.45, cy + s * 0.45), (cx + s * 0.15, cy + s * 0.62),
           (cx - s * 0.2, cy + s * 0.75), (cx - s * 0.55, cy + s * 0.5),
           (cx - s * 0.6, cy - s * 0.05)]
    d.polygon(pts, fill=(214, 90, 20))
    d.ellipse([cx - s * 0.22, cy + s * 0.05, cx + s * 0.22, cy + s * 0.55],
              fill=(245, 196, 66))


def render():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    mx = 36                      # side margin
    right = W - mx               # 988
    cw = right - mx              # 952 content width

    # ---- masthead ----
    mast = font(SERIF_B, 96)
    title = "THE WORLD"
    tw = text_w(mast, title, tracking=6)
    draw_tracked(d, ((W - tw) / 2, 16), title, mast, INK, tracking=6)
    hrule(d, mx, right, 126, width=4)
    hrule(d, mx, right, 132, width=1)
    date_f = font(SANS_B, 20)
    date = "TUESDAY, 24 NOVEMBER 2026"
    dw = text_w(date_f, date, tracking=3)
    draw_tracked(d, ((W - dw) / 2, 140), date, date_f, INK, tracking=3)
    hrule(d, mx, right, 166, width=1)

    # ---- hero: NVIDIA (left) ----
    hx, hy, hw = mx, 180, 612
    y = kicker(d, hx, hy, "Technology · Markets")
    y = headline(d, hx, y, hw, "NVIDIA BRINGS BACK HUANG", 54, max_lines=2)
    y += 6
    y = para(d, hx, y, hw,
             "The board votes unanimously to restore Jensen Huang as chief, "
             "11 days after he stepped down — shares jump 31% in the biggest "
             "one-day gain in US corporate history, adding more than $900bn. "
             "Washington blacklists Megaspeed the same day.",
             font(SERIF, 20), leading=1.32)
    # stat strip at the bottom of the hero panel
    sy = 452
    hrule(d, hx, hx + hw, sy - 12, width=1, fill=LIGHT_RULE)
    big = font(SANS_B, 46)
    d.text((hx, sy), "$900BN", font=big, fill=GREEN)
    lab = font(SANS_B, 15)
    d.text((hx + 218, sy + 6), "ADDED IN A DAY", font=lab, fill=INK)
    d.text((hx + 218, sy + 28), "NVDA  +31%", font=lab, fill=RED)
    draw_chip(d, hx + hw - 96, sy + 2, 84, 56)

    # ---- right column: Poland + Zelensky ----
    rx, rw = 664, 324
    vrule(d, 652, 180, 500)
    y = kicker(d, rx, 180, "Europe · Poland")
    y = headline(d, rx, y, rw, "DRONE STRAYS INTO POLISH SKIES", 27, max_lines=2)
    y += 4
    y = para(d, rx, y, rw,
             "Warsaw holds fire to shield civilians as a Russian drone "
             "crosses near Dorohusk. 96 launched, 73 downed.",
             font(SERIF, 18), leading=1.3)
    draw_radar(d, rx + rw - 28, 208, 26)
    hrule(d, rx, rx + rw, 362, width=1, fill=LIGHT_RULE)
    y = kicker(d, rx, 370, "Ukraine · Diplomacy")
    y = headline(d, rx, y, rw, "ZELENSKY URGES FOUR-WAY TALKS", 20,
                 max_lines=2)
    y += 4
    para(d, rx, y, rw,
         "Kyiv says it is ready \u201cliterally tomorrow\u201d. The Kremlin "
         "sees no \u201cadded value\u201d in Europe at the table.",
         font(SERIF, 17), leading=1.3)

    # ---- divider ----
    hrule(d, mx, right, 514, width=3)
    hrule(d, mx, right, 519, width=1)

    # ---- middle band: ICJ + 700,000 ----
    my = 534
    y = kicker(d, mx, my, "The Hague · Justice")
    y = headline(d, mx, y, 464, "COURT FINDS MYANMAR GUILTY OF GENOCIDE", 30,
                 max_lines=2)
    y += 4
    y = para(d, mx, y, 464,
             "The World Court rules 9–6 on the Rohingya — the first time it "
             "has found a state guilty of genocide. Fourteen nations endorse "
             "the verdict.",
             font(SERIF, 18), leading=1.3)
    big3 = font(SANS_B, 36)
    d.text((mx, 700), "9–6", font=big3, fill=NAVY)
    lab3 = font(SANS_B, 14)
    d.text((mx + 92, 708), "THE COURT'S VOTE", font=lab3, fill=INK)
    d.text((mx + 92, 728), "FIRST OF ITS KIND", font=lab3, fill=INK)

    vrule(d, 512, 534, 742)
    y = kicker(d, 524, my, "Ukraine · The Toll")
    y = headline(d, 524, y, 464, "RUSSIAN WAR DEAD TOP 700,000", 30, max_lines=2)
    y += 4
    y = para(d, 524, y, 464,
             "Leaked state records analysed by Meduza and Mediazona put "
             "confirmed deaths at 490,000 — and past 720,000 once the "
             "missing are counted.",
             font(SERIF, 19), leading=1.3)
    big2 = font(SANS_B, 40)
    d.text((524, 694), "700,000", font=big2, fill=RED)
    lab2 = font(SANS_B, 14)
    d.text((524 + 208, 704), "SOLDIERS KILLED", font=lab2, fill=INK)
    d.text((524 + 208, 724), "SINCE 2022", font=lab2, fill=INK)

    # ---- divider ----
    hrule(d, mx, right, 758, width=1)

    # ---- bottom band: three columns ----
    by = 774
    col_w = 301
    cols = [
        ("Indonesia", "26 DEAD IN CANDY FACTORY FIRE",
         "Bodies recovered in Banten after the Milkita plant blaze; dozens "
         "still missing as DNA tests begin.", True),
        ("Colombia", "CAR BOMB HITS GOVERNOR'S OFFICE",
         "23 injured, none killed, in Villavicencio; the president blames "
         "narcoterrorists and rules out talks.", False),
        ("Washington · Iran", "VANCE, RUBIO MEET QATAR PM ON IRAN TALKS",
         "Doha presses to revive stalled negotiations as fears grow of a "
         "new escalation.", False),
    ]
    for i, (kick, head, deck, flame) in enumerate(cols):
        cx = mx + i * (col_w + 24)
        y = kicker(d, cx, by, kick, size=14)
        y = headline(d, cx, y, col_w, head, 21, max_lines=3)
        y += 4
        para(d, cx, y, col_w, deck, font(SERIF, 16), leading=1.3)
        if flame:
            draw_flame(d, cx + col_w - 18, by + 22, 14)
        if i < 2:
            vrule(d, cx + col_w + 12, by, by + 172)

    # ---- footer ----
    hrule(d, mx, right, 966, width=1)
    foot = font(SANS, 13)
    d.text((mx, 976), "ALSO: COP31 climate talks collapse in Antalya — no "
                      "fossil-fuel deal.", font=foot, fill=MUTED)
    src = "Sources: Le Monde · Reuters · AP · CNN · El Tiempo"
    d.text((right - foot.getlength(src), 976), src, font=foot, fill=MUTED)
    return img


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    img = render()
    out = os.path.join(here, "entry.png")
    img.save(out, format="PNG")
    print("wrote", out, img.size, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
