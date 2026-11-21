#!/usr/bin/env python3
"""Render a travel poster for THALVOR, a city above the clouds.

Procedural PIL renderer, deterministic (fixed seed, no network, no
timestamps in the image). Run: python3 render.py  -> writes entry.png
(1024x1024) next to this file.
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W = H = 1024
SEED = 20261121
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "entry.png")

SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def sky_gradient(draw, rng):
    """Golden-hour sky: deep violet at the top, amber at the horizon."""
    stops = [
        (0.00, (24, 28, 66)),
        (0.28, (64, 48, 104)),
        (0.48, (146, 74, 110)),
        (0.62, (214, 110, 96)),
        (0.74, (247, 168, 96)),
        (1.00, (252, 205, 130)),
    ]
    for y in range(H):
        t = y / (H - 1)
        for i in range(len(stops) - 1):
            t0, c0 = stops[i]
            t1, c1 = stops[i + 1]
            if t0 <= t <= t1:
                f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
                draw.line([(0, y), (W, y)], fill=lerp(c0, c1, f))
                break


def stars(draw, rng):
    for _ in range(140):
        x = rng.uniform(0, W)
        y = rng.uniform(0, 330)
        r = rng.uniform(0.6, 1.8)
        a = rng.randint(90, 220)
        # Fade stars out as the sky warms toward the horizon.
        a = int(a * max(0.0, 1.0 - y / 380.0))
        if a > 20:
            draw.ellipse([x - r, y - r, x + r, y + r],
                         fill=(255, 244, 214, a))


def sun_glow(img, cx, cy):
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    for r, alpha in [(260, 26), (200, 40), (150, 60), (110, 90), (80, 130)]:
        g.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=(255, 196, 110, alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - 52, cy - 52, cx + 52, cy + 52],
              fill=(255, 214, 130, 255))
    d.ellipse([cx - 40, cy - 40, cx + 40, cy + 40],
              fill=(255, 232, 170, 255))


def cloud_layer(img, rng, y_base, count, x_spread, y_spread,
                palette, blur, x0=0, x1=W):
    """One soft bank of clouds: many translucent ellipses, then blurred."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(count):
        cx = rng.uniform(x0, x1)
        cy = y_base + rng.uniform(-y_spread, y_spread)
        rw = rng.uniform(60, 220)
        rh = rng.uniform(14, 42)
        col = rng.choice(palette)
        alpha = rng.randint(28, 78)
        d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh],
                  fill=col + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    img.alpha_composite(layer)


def cloud_sea(img, rng):
    """The sea of clouds the city floats above."""
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    # Warm lit mass, brightest near the sun side (right).
    for y in range(600, H):
        t = (y - 600) / (H - 600)
        col = lerp((250, 196, 138), (214, 158, 168), t)
        d.line([(0, y), (W, y)], fill=col + (255,))
    img.alpha_composite(base)
    warm = [(255, 226, 170), (252, 206, 150), (250, 190, 140)]
    cloud_layer(img, rng, 660, 90, W, 46, warm, 10)
    soft = [(255, 240, 214), (248, 214, 176), (240, 196, 180)]
    cloud_layer(img, rng, 760, 110, W, 60, soft, 14)
    shade = [(196, 140, 160), (176, 124, 150), (210, 160, 160)]
    cloud_layer(img, rng, 880, 90, W, 70, shade, 16)
    bright = [(255, 244, 220), (255, 232, 190)]
    cloud_layer(img, rng, 700, 60, W, 30, bright, 8, x0=420, x1=W)
    # Soften the hard horizon edge and add depth low down.
    horizon = [(255, 238, 205), (250, 214, 170)]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(130):
        cx = rng.uniform(0, W)
        cy = 612 + rng.uniform(-24, 24)
        rw = rng.uniform(70, 200)
        rh = rng.uniform(12, 30)
        col = rng.choice(horizon)
        d.ellipse([cx - rw, cy - rh, cx + rw, cy + rh],
                  fill=col + (rng.randint(55, 100),))
    layer = layer.filter(ImageFilter.GaussianBlur(6))
    img.alpha_composite(layer)
    deep = [(224, 178, 172), (206, 158, 168)]
    cloud_layer(img, rng, 950, 70, W, 40, deep, 12)


def bezier(p0, p1, p2, n=60):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts


def draw_bridge(draw, rng):
    """One landmark bridge: a stone arc from the island to a small rock."""
    pts = bezier((668, 452), (790, 400), (898, 470))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=(88, 58, 52, 255), width=7)
    for i in range(0, len(pts), 4):
        x, y = pts[i]
        draw.line([(x, y), (x, y - 16)], fill=(88, 58, 52, 255), width=3)
    # A few lantern dots along the arc.
    for i in range(2, len(pts) - 2, 7):
        x, y = pts[i]
        draw.ellipse([x - 3, y - 19, x + 3, y - 13],
                     fill=(255, 214, 130, 255))


def draw_house(draw, x, y, w, h, rng, lit):
    body = (122, 74, 62) if rng.random() < 0.5 else (104, 64, 58)
    draw.rectangle([x, y, x + w, y + h], fill=body + (255,))
    roof = (72, 40, 44) if rng.random() < 0.5 else (88, 48, 46)
    draw.polygon([(x - 3, y), (x + w / 2, y - 12), (x + w + 3, y)],
                 fill=roof + (255,))
    if lit:
        wx = x + w / 2 - 3
        draw.rectangle([wx, y + h / 2 - 2, wx + 6, y + h / 2 + 5],
                       fill=(255, 208, 110, 255))


def draw_town(draw, rng):
    """Cliffside town on the plateau: houses, a tower, warm windows."""
    # Terraced green-gold plateau top.
    draw.polygon([(300, 430), (700, 430), (668, 470), (330, 470)],
                 fill=(96, 104, 58, 255))
    draw.polygon([(330, 470), (668, 470), (640, 492), (360, 492)],
                 fill=(78, 86, 48, 255))
    # Tower with a beacon — the town's vertical accent.
    draw.rectangle([596, 330, 622, 432], fill=(110, 66, 56, 255))
    draw.polygon([(592, 330), (609, 296), (626, 330)],
                 fill=(66, 38, 42, 255))
    draw.ellipse([602, 306, 616, 320], fill=(255, 220, 130, 255))
    for yy in range(344, 428, 22):
        draw.rectangle([603, yy, 615, yy + 9],
                       fill=(255, 208, 110, 255))
    # Houses in two loose rows.
    spots = [(330, 402), (372, 410), (416, 398), (458, 408), (500, 400),
             (542, 410), (352, 438), (404, 444), (452, 436), (500, 444),
             (548, 438), (636, 408), (648, 440)]
    for (hx, hy) in spots:
        w = rng.uniform(24, 34)
        h = rng.uniform(20, 30)
        draw_house(draw, hx, hy, w, h, rng, lit=True)
    # A cypress tree or two for silhouette.
    for tx in (322, 668):
        draw.rectangle([tx - 2, 408, tx + 2, 436], fill=(52, 40, 36, 255))
        draw.ellipse([tx - 9, 384, tx + 9, 412], fill=(46, 66, 40, 255))


def draw_island(draw, rng):
    """The floating peak: jagged rock underside, lit on the sun side."""
    # Main rock mass.
    rock = [(300, 428), (700, 428), (688, 470), (660, 520), (640, 560),
            (612, 620), (586, 668), (560, 700), (540, 716), (512, 700),
            (486, 660), (452, 620), (420, 570), (392, 530), (360, 490),
            (330, 460)]
    draw.polygon(rock, fill=(104, 66, 58, 255))
    # Sunlit right face.
    lit = [(560, 470), (700, 428), (688, 470), (660, 520), (640, 560),
           (612, 620), (586, 668), (560, 700), (560, 560)]
    draw.polygon(lit, fill=(168, 106, 82, 255))
    # Shadowed left face.
    dark = [(300, 428), (330, 460), (360, 490), (392, 530), (420, 570),
            (452, 620), (486, 660), (512, 700), (512, 560), (470, 480)]
    draw.polygon(dark, fill=(66, 40, 40, 255))
    # Strata lines across the rock (kept inside the rock outline).
    for x0, y0, x1, y1 in [(400, 500, 628, 512), (448, 560, 628, 574),
                           (478, 620, 592, 634)]:
        draw.line([(x0, y0), (x1, y1)], fill=(78, 48, 44, 255), width=4)
    # Pale stone outcrops.
    for (ox, oy, ow, oh) in [(420, 500, 46, 14), (520, 580, 60, 16),
                             (470, 640, 40, 12), (580, 540, 44, 12)]:
        draw.ellipse([ox, oy, ox + ow, oy + oh], fill=(188, 132, 104, 255))
    # Waterfall spilling off the left edge into the clouds.
    for k in range(3):
        x = 356 + k * 9
        draw.line([(x, 470), (x + 6, 640)], fill=(240, 226, 200, 200),
                  width=5)
    mist = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(mist)
    for _ in range(26):
        mx = rng.uniform(340, 410)
        my = rng.uniform(620, 680)
        md.ellipse([mx - 22, my - 10, mx + 22, my + 10],
                   fill=(255, 240, 210, 46))
    mist = mist.filter(ImageFilter.GaussianBlur(8))
    return mist


def draw_small_rock(draw, rng):
    """The small floating rock the bridge lands on."""
    rock = [(872, 470), (946, 470), (936, 500), (916, 528), (898, 514),
            (884, 492)]
    draw.polygon(rock, fill=(96, 60, 54, 255))
    draw.polygon([(906, 470), (946, 470), (936, 500), (916, 528)],
                 fill=(150, 94, 74, 255))
    # A lone pine on the rock.
    draw.rectangle([906, 436, 910, 472], fill=(52, 40, 36, 255))
    draw.polygon([(894, 452), (908, 418), (922, 452)], fill=(52, 72, 44, 255))
    draw.polygon([(898, 438), (908, 410), (918, 438)], fill=(62, 84, 50, 255))


def draw_birds(draw, rng):
    for _ in range(9):
        x = rng.uniform(90, 900)
        y = rng.uniform(240, 420)
        s = rng.uniform(7, 15)
        draw.arc([x - s, y - s * 0.6, x, y + s * 0.6], 200, 340,
                 fill=(52, 34, 44, 230), width=3)
        draw.arc([x, y - s * 0.6, x + s, y + s * 0.6], 200, 340,
                 fill=(52, 34, 44, 230), width=3)


def draw_foreground(draw, rng):
    """Dark framing ridges at the bottom corners."""
    draw.polygon([(0, 1024), (0, 940), (120, 900), (260, 950), (300, 1024)],
                 fill=(38, 26, 40, 255))
    draw.polygon([(1024, 1024), (1024, 950), (920, 910), (800, 960),
                  (760, 1024)], fill=(38, 26, 40, 255))
    # Pine silhouettes on the ridges.
    for (tx, ty, s) in [(90, 930, 46), (150, 918, 36), (930, 936, 42),
                        (860, 922, 32)]:
        draw.polygon([(tx - s * 0.32, ty), (tx, ty - s), (tx + s * 0.32, ty)],
                     fill=(30, 22, 34, 255))
        draw.polygon([(tx - s * 0.26, ty - s * 0.45), (tx, ty - s * 1.35),
                      (tx + s * 0.26, ty - s * 0.45)],
                     fill=(30, 22, 34, 255))


def tracked_text(draw, cx, y, text, font, fill, tracking=0):
    """Draw centred text with letter tracking, plus a soft shadow."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        draw.text((x + 2, y + 3), ch, font=font, fill=(30, 20, 44, 160))
        draw.text((x, y), ch, font=font, fill=fill)
        x += w + tracking


def draw_type(draw):
    title = ImageFont.truetype(SERIF_BOLD, 118)
    sub = ImageFont.truetype(SANS_BOLD, 30)
    foot = ImageFont.truetype(SANS, 24)
    # Thin gold rules flanking the subtitle, measured clear of the text.
    sub_text = "A CITY ABOVE THE CLOUDS"
    sub_w = (draw.textlength(sub_text, font=sub) + 6 * (len(sub_text) - 1))
    gap, rule_len = 22, 110
    left_end = 512 - sub_w / 2 - gap
    draw.line([(left_end - rule_len, 232), (left_end, 232)],
              fill=(255, 214, 140, 255), width=3)
    right_start = 512 + sub_w / 2 + gap
    draw.line([(right_start, 232), (right_start + rule_len, 232)],
              fill=(255, 214, 140, 255), width=3)
    tracked_text(draw, 512, 78, "THALVOR", title, (255, 243, 214), tracking=14)
    tracked_text(draw, 512, 216, sub_text, sub,
                 (255, 226, 170), tracking=6)
    tracked_text(draw, 512, 962, "COME STAY ABOVE THE WORLD", foot,
                 (255, 238, 200), tracking=5)


def grain(img, rng):
    """Fine deterministic grain so the PNG carries rich detail."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(9000):
        x = rng.randint(0, W - 1)
        y = rng.randint(0, H - 1)
        v = rng.randint(0, 255)
        a = rng.randint(6, 18)
        d.point((x, y), fill=(v, v, v, a))
    img.alpha_composite(layer)


def render():
    rng = random.Random(SEED)
    img = Image.new("RGBA", (W, H), (24, 28, 66, 255))
    draw = ImageDraw.Draw(img, "RGBA")
    sky_gradient(draw, rng)
    stars(draw, rng)
    sun_glow(img, 742, 448)
    cloud_sea(img, rng)
    draw = ImageDraw.Draw(img, "RGBA")
    mist = draw_island(draw, rng)
    img.alpha_composite(mist)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_town(draw, rng)
    draw_small_rock(draw, rng)
    draw_bridge(draw, rng)
    draw_birds(draw, rng)
    draw_foreground(draw, rng)
    draw_type(ImageDraw.Draw(img, "RGBA"))
    grain(img, rng)
    # Thin warm frame to finish the poster.
    frame = ImageDraw.Draw(img, "RGBA")
    frame.rectangle([14, 14, W - 15, H - 15], outline=(255, 220, 150, 220),
                    width=3)
    img.convert("RGB").save(OUT, format="PNG", optimize=True)
    return OUT


if __name__ == "__main__":
    path = render()
    print(path, os.path.getsize(path), "bytes")
