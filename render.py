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
    # Sunset now: no star field. A pale disc plus 140 stars read as a
    # full moon at night; the poster commits to golden-hour sunset.
    return


def sun_glow(img, cx, cy):
    # A low setting sun: deep orange disc, warm halo spilling sideways.
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    for r, alpha in [(300, 22), (230, 36), (170, 55), (120, 85), (85, 120)]:
        g.ellipse([cx - r, cy - r, cx + r, cy + r],
                  fill=(255, 158, 70, alpha))
    glow = glow.filter(ImageFilter.GaussianBlur(20))
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - 62, cy - 62, cx + 62, cy + 62],
              fill=(255, 138, 40, 255))
    d.ellipse([cx - 50, cy - 50, cx + 50, cy + 50],
              fill=(255, 176, 72, 255))
    d.ellipse([cx - 36, cy - 36, cx + 36, cy + 36],
              fill=(255, 206, 110, 255))


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


def cloud_mound(layer_draw, cx, cy, rw, rh, rng):
    """One billowing mound: mauve shadowed underside, warm lit top."""
    sh = (186, 128, 152)
    lt = (255, 228, 178)
    hi = (255, 244, 216)
    layer_draw.ellipse([cx - rw, cy - rh * 0.55 + 16,
                        cx + rw, cy + rh * 0.55 + 16],
                       fill=sh + (120,))
    layer_draw.ellipse([cx - rw, cy - rh, cx + rw, cy + rh * 0.45],
                       fill=lt + (220,))
    layer_draw.ellipse([cx - rw * 0.62, cy - rh * 0.95,
                        cx + rw * 0.28, cy - rh * 0.05],
                       fill=hi + (225,))


def light_shaft(img, cx, cy):
    """Warm shaft from the low sun spilling across the cloud tops."""
    shaft = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(shaft)
    d.polygon([(cx - 40, cy + 20), (cx + 40, cy + 20),
               (cx + 260, H), (cx - 300, H)],
              fill=(255, 178, 90, 34))
    shaft = shaft.filter(ImageFilter.GaussianBlur(22))
    img.alpha_composite(shaft)


def cloud_sea(img, rng):
    """The sea of clouds: distinct overlapping mounds, not a flat band."""
    base = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(base)
    for y in range(600, H):
        t = (y - 600) / (H - 600)
        col = lerp((252, 200, 142), (216, 160, 170), t)
        d.line([(0, y), (W, y)], fill=col + (255,))
    img.alpha_composite(base)
    # Five staggered, heavily overlapping rows of tall puffs, so no
    # flat band of base gradient shows between rows.
    rows = [
        (640, 130, 88, [90, 270, 450, 640, 830, 970]),
        (725, 150, 96, [40, 230, 420, 610, 800, 960]),
        (815, 165, 102, [110, 300, 500, 700, 900]),
        (905, 175, 106, [0, 200, 420, 640, 860, 1024]),
        (985, 180, 96, [80, 280, 500, 720, 940]),
    ]
    for y_base, rw_base, rh_base, xs in rows:
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        for cx in xs:
            cx = cx + rng.uniform(-32, 32)
            rw = rw_base * rng.uniform(0.85, 1.25)
            rh = rh_base * rng.uniform(0.8, 1.2)
            cy = y_base + rng.uniform(-18, 18)
            cloud_mound(ld, cx, cy, rw, rh, rng)
            # A smaller satellite puff on each mound's lit shoulder.
            cloud_mound(ld, cx + rw * 0.55, cy - rh * 0.35,
                        rw * 0.45, rh * 0.55, rng)
        layer = layer.filter(ImageFilter.GaussianBlur(11))
        img.alpha_composite(layer)
    # A few soft mauve cloud shadows between the mounds for depth.
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for (sx, sy, sw) in [(180, 720, 190), (560, 830, 230),
                         (860, 730, 180), (330, 930, 240)]:
        sd.ellipse([sx - sw, sy - 22, sx + sw, sy + 22],
                   fill=(178, 122, 148, 70))
    shade = shade.filter(ImageFilter.GaussianBlur(14))
    img.alpha_composite(shade)


def bezier(p0, p1, p2, n=60):
    pts = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    return pts


def draw_bridge(draw, rng):
    """One landmark bridge: a stone arc from the island to a big rock,
    landing squarely on the rock's flat top, not floating past it."""
    pts = bezier((736, 452), (830, 402), (922, 468))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=(88, 58, 52, 255), width=8)
    for i in range(0, len(pts), 4):
        x, y = pts[i]
        draw.line([(x, y), (x, y - 17)], fill=(88, 58, 52, 255), width=3)
    # A few lantern dots along the arc.
    for i in range(2, len(pts) - 2, 7):
        x, y = pts[i]
        draw.ellipse([x - 3, y - 20, x + 3, y - 14],
                     fill=(255, 214, 130, 255))
    # Landing platform planks where the arc meets the rock.
    draw.rectangle([896, 462, 950, 472], fill=(104, 68, 56, 255))
    # Two tiny figures strolling across, mid-bridge.
    for (fx, fy) in [(806, 414), (838, 412)]:
        draw.ellipse([fx - 3, fy - 12, fx + 3, fy - 6],
                     fill=(40, 26, 34, 255))
        draw.rectangle([fx - 2, fy - 6, fx + 2, fy + 4],
                       fill=(40, 26, 34, 255))


def draw_house(draw, x, y, w, h, rng, lit):
    body = (122, 74, 62) if rng.random() < 0.5 else (104, 64, 58)
    draw.rectangle([x, y, x + w, y + h], fill=body + (255,))
    roof = (72, 40, 44) if rng.random() < 0.5 else (88, 48, 46)
    draw.polygon([(x - 3, y), (x + w / 2, y - 14), (x + w + 3, y)],
                 fill=roof + (255,))
    if lit:
        # Big glowing windows: two per house so the town reads warm.
        for wx in (x + 5, x + w - 13):
            draw.rectangle([wx, y + h / 2 - 3, wx + 8, y + h / 2 + 9],
                           fill=(255, 208, 110, 255))
            draw.rectangle([wx, y + 5, wx + 8, y + 13],
                           fill=(255, 190, 90, 230))


def draw_town(draw, rng):
    """Cliffside town on the enlarged plateau: houses, a tall tower,
    warm windows, and a warm light wash across the grass."""
    # Terraced green-gold plateau top, ~28% wider than before.
    draw.polygon([(244, 428), (756, 428), (724, 482), (276, 482)],
                 fill=(96, 104, 58, 255))
    draw.polygon([(276, 482), (724, 482), (694, 506), (306, 506)],
                 fill=(78, 86, 48, 255))
    # No separate wash: the glowing windows already warm the town;
    # a pale wash ellipse read as a sand patch on the grass.
    # Tower with a beacon — taller now, the town's signature landmark.
    draw.rectangle([628, 282, 658, 432], fill=(110, 66, 56, 255))
    draw.polygon([(624, 282), (643, 240), (662, 282)],
                 fill=(66, 38, 42, 255))
    # Glowing beacon: halo + large bright core.
    draw.ellipse([626, 238, 660, 272], fill=(255, 190, 80, 110))
    draw.ellipse([632, 244, 654, 266], fill=(255, 224, 130, 255))
    draw.ellipse([637, 249, 649, 261], fill=(255, 244, 200, 255))
    for yy in range(300, 424, 24):
        draw.rectangle([634, yy, 652, yy + 12],
                       fill=(255, 208, 110, 255))
    # Houses in two loose rows, ~30% bigger than before.
    spots = [(282, 392), (336, 402), (392, 390), (447, 400), (500, 392),
             (554, 402), (311, 430), (377, 436), (438, 428), (500, 436),
             (562, 430), (674, 400), (690, 432)]
    for (hx, hy) in spots:
        w = rng.uniform(32, 44)
        h = rng.uniform(28, 38)
        draw_house(draw, hx, hy, w, h, rng, lit=True)
    # A cypress tree or two for silhouette.
    for tx in (268, 730):
        draw.rectangle([tx - 2, 400, tx + 2, 430], fill=(52, 40, 36, 255))
        draw.ellipse([tx - 10, 374, tx + 10, 404], fill=(46, 66, 40, 255))


def draw_island(draw, rng):
    """The floating peak, ~28% larger: jagged rock underside, lit on
    the sun side, strata in rock tones only."""
    # Main rock mass, widened and deepened so the tip dips into cloud.
    rock = [(244, 428), (756, 428), (741, 480), (705, 543), (679, 593),
            (643, 668), (610, 728), (577, 768), (551, 788), (515, 768),
            (482, 728), (438, 668), (398, 593), (362, 543), (321, 490),
            (282, 460)]
    draw.polygon(rock, fill=(104, 66, 58, 255))
    # Sunlit right face.
    lit = [(577, 482), (756, 428), (741, 480), (705, 543), (679, 593),
           (643, 668), (610, 728), (577, 768), (577, 560)]
    draw.polygon(lit, fill=(168, 106, 82, 255))
    # Shadowed left face.
    dark = [(244, 428), (282, 460), (321, 490), (362, 543), (398, 593),
            (438, 668), (482, 728), (515, 768), (515, 560), (470, 480)]
    draw.polygon(dark, fill=(66, 40, 40, 255))
    # Strata lines across the rock, in rock tones (kept inside outline).
    for x0, y0, x1, y1 in [(360, 510, 660, 524), (410, 580, 660, 596),
                           (448, 650, 610, 666), (480, 700, 580, 712)]:
        draw.line([(x0, y0), (x1, y1)], fill=(78, 48, 44, 255), width=5)
    # Strata lines only; the old dark ledge ovals read as holes.
    # Waterfall: one wide cascade off the left edge, ending in soft
    # mist where it meets the cloud below (no solid foam disc).
    for k in range(5):
        x = 292 + k * 8
        draw.line([(x, 482), (x + 5, 648)], fill=(240, 226, 200, 210),
                  width=7)
    mist = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(mist)
    for _ in range(26):
        mx = rng.uniform(290, 360)
        my = rng.uniform(630, 680)
        md.ellipse([mx - 22, my - 10, mx + 22, my + 10],
                   fill=(255, 240, 210, 46))
    mist = mist.filter(ImageFilter.GaussianBlur(8))
    return mist


def draw_small_rock(draw, rng):
    """The larger floating rock the bridge lands on, flat-topped."""
    rock = [(858, 470), (982, 470), (968, 508), (940, 552), (908, 538),
            (876, 500)]
    draw.polygon(rock, fill=(96, 60, 54, 255))
    draw.polygon([(918, 470), (982, 470), (968, 508), (940, 552)],
                 fill=(150, 94, 74, 255))
    # A lone pine on the rock.
    draw.rectangle([930, 432, 934, 472], fill=(52, 40, 36, 255))
    draw.polygon([(916, 450), (932, 412), (948, 450)], fill=(52, 72, 44, 255))
    draw.polygon([(920, 436), (932, 406), (944, 436)], fill=(62, 84, 50, 255))


def draw_balloon(draw, rng):
    """One small hot-air balloon in the mid-sky, left of the island —
    the single life element besides the bridge figures."""
    bx, by = 140, 398
    draw.ellipse([bx - 34, by - 44, bx + 34, by + 8],
                 fill=(214, 84, 66, 255))
    draw.ellipse([bx - 12, by - 44, bx + 12, by + 8],
                 fill=(255, 196, 110, 255))
    draw.line([(bx - 20, by + 6), (bx - 12, by + 30)],
              fill=(52, 34, 44, 255), width=2)
    draw.line([(bx + 20, by + 6), (bx + 12, by + 30)],
              fill=(52, 34, 44, 255), width=2)
    draw.rectangle([bx - 12, by + 30, bx + 12, by + 44],
                   fill=(88, 58, 52, 255))


def draw_birds(draw, rng):
    for _ in range(5):
        x = rng.uniform(260, 900)
        y = rng.uniform(280, 380)
        s = rng.uniform(7, 15)
        draw.arc([x - s, y - s * 0.6, x, y + s * 0.6], 200, 340,
                 fill=(52, 34, 44, 230), width=3)
        draw.arc([x, y - s * 0.6, x + s, y + s * 0.6], 200, 340,
                 fill=(52, 34, 44, 230), width=3)


def draw_foreground(draw, rng):
    """No ground ridges any more — the poster is above the clouds.
    The cloud sea already fills the bottom, so no corner framing
    is needed; the footer sits on clean cloud as-is."""
    return


def tracked_text(draw, cx, y, text, font, fill, tracking=0):
    """Draw centred text with letter tracking, plus a strong shadow."""
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        draw.text((x + 3, y + 4), ch, font=font, fill=(30, 20, 44, 200))
        draw.text((x + 2, y + 3), ch, font=font, fill=(30, 20, 44, 160))
        draw.text((x, y), ch, font=font, fill=fill)
        x += w + tracking


def draw_type(draw):
    title = ImageFont.truetype(SERIF_BOLD, 118)
    sub = ImageFont.truetype(SANS_BOLD, 30)
    foot = ImageFont.truetype(SANS_BOLD, 25)
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
    tracked_text(draw, 512, 932, "COME STAY ABOVE THE WORLD", foot,
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
    sun_glow(img, 800, 566)
    cloud_sea(img, rng)
    light_shaft(img, 800, 566)
    draw = ImageDraw.Draw(img, "RGBA")
    mist = draw_island(draw, rng)
    img.alpha_composite(mist)
    draw = ImageDraw.Draw(img, "RGBA")
    draw_town(draw, rng)
    draw_small_rock(draw, rng)
    draw_bridge(draw, rng)
    draw_balloon(draw, rng)
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
