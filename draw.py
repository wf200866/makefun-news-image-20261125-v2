#!/usr/bin/env python3
"""Front page of THE WORLD for Wednesday 25 November 2026.

A broadsheet layout: one dominant lead story with a large drawn panel, a
dark full-height second story, and four smaller pieces of unequal size.
Everything is drawn in a 1024x1024 space at 2x and reduced with Lanczos so
the serif type keeps clean edges.  Pillow is needed at build time only; the
repository ships the finished PNG and main.ts just copies it.

Run:  python3 draw.py [entry.png]
"""

from PIL import Image, ImageDraw, ImageFont
import math
import random
import sys

W = H = 1024
S = 2

PAPER = (246, 242, 233)
PAPER_2 = (238, 232, 219)
INK = (24, 20, 15)
SOFT = (94, 87, 74)
FAINT = (183, 174, 157)
RED = (158, 34, 30)
ORANGE = (205, 91, 27)
TEAL = (28, 104, 100)
SLATE = (47, 66, 94)
CREAM = (250, 246, 236)

FONT_DIR = "/usr/share/fonts/truetype"
SERIF_BLACK = "noto/NotoSerifDisplay-Black.ttf"
SERIF_BOLD = "noto/NotoSerif-Bold.ttf"
SERIF = "noto/NotoSerif-Regular.ttf"
SERIF_ITAL = "noto/NotoSerif-Italic.ttf"
SANS_BOLD = "liberation/LiberationSans-Bold.ttf"
SANS = "liberation/LiberationSans-Regular.ttf"

WARNINGS = []


def font(rel, size):
    return ImageFont.truetype(f"{FONT_DIR}/{rel}", max(1, int(round(size * S))))


def mix(c0, c1, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a + (b - a) * t)) for a, b in zip(c0, c1))


class Paper:
    def __init__(self):
        self.img = Image.new("RGB", (W * S, H * S), PAPER)
        self.d = ImageDraw.Draw(self.img)

    # ---------------------------------------------------------------- primitives
    def text(self, x, y, s, f, fill=INK, anchor="lt", tracking=0.0):
        x, y = x * S, y * S
        if not tracking:
            self.d.text((x, y), s, font=f, fill=fill, anchor=anchor)
            return self.d.textlength(s, font=f) / S
        total = 0.0
        for ch in s:
            self.d.text((x + total * S, y), ch, font=f, fill=fill, anchor=anchor)
            total += self.d.textlength(ch, font=f) / S + tracking
        return total

    def line(self, x0, y0, x1, y1, fill=INK, width=1):
        self.d.line((x0 * S, y0 * S, x1 * S, y1 * S), fill=fill,
                    width=max(1, int(round(width * S))))

    def rect(self, x0, y0, x1, y1, fill=None, outline=None, width=1):
        self.d.rectangle((x0 * S, y0 * S, x1 * S, y1 * S), fill=fill,
                         outline=outline, width=max(1, int(round(width * S))))

    def ellipse(self, x0, y0, x1, y1, fill=None, outline=None, width=1):
        self.d.ellipse((x0 * S, y0 * S, x1 * S, y1 * S), fill=fill,
                       outline=outline, width=max(1, int(round(width * S))))

    def polygon(self, pts, fill=None, outline=None):
        self.d.polygon([(x * S, y * S) for x, y in pts], fill=fill, outline=outline)

    def arc(self, x0, y0, x1, y1, a0, a1, fill=INK, width=1):
        self.d.arc((x0 * S, y0 * S, x1 * S, y1 * S), a0, a1, fill=fill,
                   width=max(1, int(round(width * S))))

    def measure(self, s, f):
        return self.d.textlength(s, font=f) / S

    def wrap(self, s, f, maxw):
        words, lines, cur = s.split(), [], ""
        for w in words:
            trial = (cur + " " + w).strip()
            if self.measure(trial, f) <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines

    def block(self, x, y, s, f, maxw, leading, fill=INK, max_lines=None, tag=""):
        lines = self.wrap(s, f, maxw)
        if max_lines is not None and len(lines) > max_lines:
            WARNINGS.append(f"{tag}: {len(lines)} lines > {max_lines} at width {maxw:.0f}")
        for i, ln in enumerate(lines):
            self.text(x, y + i * leading, ln, f, fill=fill)
            if self.measure(ln, f) > maxw + 0.6:
                WARNINGS.append(f"{tag}: line too wide ({self.measure(ln, f):.1f}>{maxw:.0f})")
        return len(lines) * leading

    def tracked_center(self, cx, y, s, f, fill=INK, tracking=2.0):
        width = sum(self.measure(ch, f) + tracking for ch in s) - tracking
        self.text(cx - width / 2.0, y, s, f, fill=fill, tracking=tracking)

    def star(self, cx, cy, r, fill=INK, points=5):
        pts = []
        for i in range(points * 2):
            ang = -math.pi / 2 + i * math.pi / points
            rad = r if i % 2 == 0 else r * 0.42
            pts.append((cx + math.cos(ang) * rad, cy + math.sin(ang) * rad))
        self.polygon(pts, fill=fill)

    def fit_size(self, s, rel, maxw, hi, lo, step=0.5):
        size = hi
        while size > lo and self.measure(s, font(rel, size)) > maxw:
            size -= step
        return size

    # ---------------------------------------------------------------- fills
    def vgrad(self, x0, y0, x1, y1, c0, c1):
        h = max(1, int(round((y1 - y0) * S)))
        for i in range(h):
            t = i / max(1, h - 1)
            self.d.line((x0 * S, y0 * S + i, x1 * S, y0 * S + i),
                        fill=mix(c0, c1, t))

    def hgrad(self, x0, y0, x1, y1, c0, c1):
        w = max(1, int(round((x1 - x0) * S)))
        for i in range(w):
            t = i / max(1, w - 1)
            self.d.line((x0 * S + i, y0 * S, x0 * S + i, y1 * S),
                        fill=mix(c0, c1, t))

    def glow(self, cx, cy, r, c0, c1, steps=26):
        """Soft radial wash: c0 at the centre, c1 at the rim."""
        for i in range(steps, 0, -1):
            t = i / steps
            rr = r * t
            col = mix(c0, c1, t ** 0.7)
            self.ellipse(cx - rr, cy - rr, cx + rr, cy + rr, fill=col)

    def save(self, path):
        out = self.img.resize((W, H), Image.LANCZOS)
        out.save(path, "PNG", optimize=True)


# ---------------------------------------------------------------------------
# illustration 1: the tariff wall (hero panel)
# ---------------------------------------------------------------------------

def art_tariffs(p, x, y, w, h):
    # warm dusk sky
    p.vgrad(x, y, x + w, y + h, (252, 232, 203), (224, 150, 104))
    p.glow(x + w * 0.72, y + h * 0.30, 74, (255, 240, 200), (246, 200, 148), steps=22)
    # halftone dots in the sky
    rng = random.Random(825)
    for _ in range(620):
        px = x + rng.random() * w
        py = y + rng.random() * (h - 44)
        p.d.point((px * S, py * S), fill=(232, 190, 152))

    # sea
    sea_y = y + h - 58
    p.vgrad(x, sea_y, x + w, y + h, (58, 74, 84), (30, 40, 48))
    for i in range(7):
        yy = sea_y + 8 + i * 7
        p.line(x, yy, x + w, yy, fill=mix((70, 88, 98), (36, 46, 54), i / 6), width=0.7)

    # container ship silhouette
    sx, sy = x + w * 0.42, sea_y - 2
    p.polygon([(sx, sy - 40), (sx + 190, sy - 40), (sx + 218, sy - 12),
               (sx + 350, sy - 12), (sx + 332, sy + 14), (sx + 16, sy + 14),
               (sx - 8, sy - 10)], fill=(34, 38, 42))
    p.rect(sx + 292, sy - 66, sx + 330, sy - 40, fill=(34, 38, 42))
    p.rect(sx + 300, sy - 58, sx + 312, sy - 48, fill=(226, 178, 120))
    cols = [(178, 58, 46), (214, 150, 52), (46, 104, 106), (196, 90, 42)]
    for row in range(3):
        for col in range(9):
            cx = sx + 12 + col * 30
            cy = sy - 40 - row * 15
            p.rect(cx, cy - 13, cx + 26, cy - 2, fill=cols[(row + col) % 4],
                   outline=(26, 28, 30), width=0.6)

    # globe, engraved line style
    gx, gy, gr = x + 92, y + h * 0.40, 58
    p.ellipse(gx - gr, gy - gr, gx + gr, gy + gr, fill=(247, 226, 196),
              outline=(60, 44, 36), width=1.4)
    for k in (0.38, 0.72):
        p.ellipse(gx - gr * math.sqrt(1 - k * k), gy - gr * k,
                  gx + gr * math.sqrt(1 - k * k), gy + gr * k,
                  outline=(120, 92, 70), width=0.7)
    p.line(gx, gy - gr, gx, gy + gr, fill=(120, 92, 70), width=0.7)
    p.ellipse(gx - gr * 0.55, gy - gr, gx + gr * 0.55, gy + gr,
              outline=(120, 92, 70), width=0.7)
    p.ellipse(gx - gr * 0.22, gy - gr, gx + gr * 0.22, gy + gr,
              outline=(120, 92, 70), width=0.7)
    p.polygon([(gx - 40, gy - 26), (gx - 16, gy - 40), (gx - 2, gy - 22),
               (gx - 14, gy - 4), (gx - 30, gy + 8), (gx - 44, gy - 6)],
              fill=(206, 178, 142), outline=(80, 60, 48))
    p.polygon([(gx + 8, gy - 40), (gx + 40, gy - 34), (gx + 44, gy - 12),
               (gx + 24, gy - 6), (gx + 10, gy - 22)],
              fill=(206, 178, 142), outline=(80, 60, 48))
    p.polygon([(gx + 6, gy + 2), (gx + 34, gy + 6), (gx + 30, gy + 38),
               (gx + 12, gy + 30)], fill=(206, 178, 142), outline=(80, 60, 48))

    # tariff bars rising toward the sky
    bars = [(x + 424, 0.40, "40%", "CHINA"),
            (x + 474, 0.33, "35%", "VIETNAM"),
            (x + 524, 0.22, "25%", "EU · JAPAN")]
    for bx, frac, pct, name in bars:
        top = sea_y - 30 - frac * 190
        p.rect(bx, top, bx + 26, sea_y - 30, fill=RED, outline=(90, 18, 16), width=0.8)
        p.text(bx + 13, top - 15, pct, font(SANS_BOLD, 10.5), fill=(70, 20, 18),
               anchor="mt")
        p.text(bx + 13, sea_y - 25, name, font(SANS_BOLD, 6.6), fill=CREAM,
               anchor="mt")

    # bottom caption strip
    p.rect(x, y + h - 20, x + w, y + h, fill=(38, 26, 22))
    p.text(x + 10, y + h - 15.5,
           "NEW DUTIES ON 14 ECONOMIES · CHINA UP TO 40% · STOCKS SLIDE",
           font(SANS_BOLD, 7.4), fill=(246, 220, 186), tracking=1.0)
    p.rect(x, y, x + w, y + h, outline=(54, 38, 28), width=1.3)


# ---------------------------------------------------------------------------
# illustration 2: Russia's toll (dark card)
# ---------------------------------------------------------------------------

def art_war_dead(p, x, y, w, h):
    # engraved cemetery: rows of small crosses fading into the dark
    rng = random.Random(2526)
    for row in range(7):
        yy = y + h - 18 - row * 15
        n = 15 - row
        for i in range(n):
            cx = x + 10 + (i + 0.5) * (w - 20) / max(1, n) + (row % 2) * 5
            hh = 7 + rng.random() * 3
            col = mix((132, 112, 104), (58, 46, 46), row / 6)
            p.line(cx, yy, cx, yy - hh, fill=col, width=1.0)
            p.line(cx - 3, yy - hh + 3, cx + 3, yy - hh + 3, fill=col, width=1.0)
    # barbed wire across the field
    wy = y + 12
    p.line(x + 2, wy, x + w - 2, wy, fill=(168, 146, 132), width=0.9)
    for i in range(16):
        cx = x + 8 + i * (w - 16) / 15
        p.line(cx - 4, wy - 5, cx + 4, wy + 5, fill=(168, 146, 132), width=0.8)
        p.line(cx - 4, wy + 5, cx + 4, wy - 5, fill=(168, 146, 132), width=0.8)


# ---------------------------------------------------------------------------
# illustration 3: Cairo tanker fire
# ---------------------------------------------------------------------------

def art_cairo(p, x, y, w, h):
    p.vgrad(x, y, x + w, y + h, (250, 214, 150), (206, 92, 38))
    p.glow(x + w * 0.48, y + h * 0.66, 70, (255, 246, 196), (236, 154, 62), steps=20)
    for i in range(5):
        cx = x + w * 0.42 + i * 8
        cy = y + 22 + i * 12
        p.arc(cx - 18, cy - 12, cx + 18, cy + 12, 200, 340,
              fill=(90, 62, 52), width=1.2)
    for fx, fh in ((0.30, 46), (0.46, 62), (0.62, 40)):
        cx = x + w * fx
        base = y + h - 24
        p.polygon([(cx - 14, base), (cx - 4, base - fh * 0.55),
                   (cx, base - fh), (cx + 5, base - fh * 0.5),
                   (cx + 14, base)], fill=(244, 120, 34))
        p.polygon([(cx - 7, base), (cx, base - fh * 0.6), (cx + 7, base)],
                  fill=(255, 214, 120))
    p.rect(x, y + h - 26, x + w, y + h, fill=(48, 42, 44))
    p.line(x, y + h - 26, x + w, y + h - 26, fill=(24, 20, 20), width=1.0)
    p.polygon([(x + 8, y + h - 30), (x + w - 34, y + h - 58),
               (x + w - 26, y + h - 38), (x + 16, y + h - 16)],
              fill=(28, 28, 32))
    p.ellipse(x + 16, y + h - 28, x + 30, y + h - 14,
              outline=(220, 200, 170), width=1.0)
    p.ellipse(x + w - 46, y + h - 54, x + w - 32, y + h - 40,
              outline=(220, 200, 170), width=1.0)
    p.rect(x + w - 40, y + h - 56, x + w - 20, y + h - 48, fill=(160, 40, 30))


# ---------------------------------------------------------------------------
# illustration 4: inflation chart
# ---------------------------------------------------------------------------

def art_inflation(p, x, y, w, h):
    """Compact sparkline strip that fits inside any h >= 24."""
    p.rect(x, y, x + w, y + h, fill=(226, 240, 233))
    for gx in range(int(x + 4), int(x + w - 2), 18):
        for gy in range(int(y + 4), int(y + h - 3), 10):
            p.d.point((gx * S, gy * S), fill=(180, 208, 196))
    vals = (0.08, 0.20, 0.16, 0.34, 0.29, 0.50, 0.44, 0.66, 0.84)
    pts = [(x + 4 + i * (w - 8) / (len(vals) - 1), y + h - 4 - v * (h - 10))
           for i, v in enumerate(vals)]
    p.polygon(pts + [(pts[-1][0], y + h - 4), (pts[0][0], y + h - 4)],
              fill=(196, 224, 210))
    for a, b in zip(pts, pts[1:]):
        p.line(a[0], a[1], b[0], b[1], fill=TEAL, width=1.8)
    p.line(x + 4, y + h - 4, x + w - 4, y + h - 4,
           fill=(90, 132, 120), width=0.8)


# ---------------------------------------------------------------------------
# illustration 5: Netanyahu trial (courthouse)
# ---------------------------------------------------------------------------

def art_court(p, x, y, w, h):
    p.rect(x, y, x + w, y + h, fill=(224, 231, 242))
    for i in range(-h, w, 7):
        p.line(x + i, y + h, x + i + h, y, fill=(204, 214, 230), width=0.6)
    cx = x + w / 2
    p.polygon([(x + 8, y + 34), (cx, y + 12), (x + w - 8, y + 34)],
              fill=(58, 78, 112))
    p.rect(x + 12, y + 34, x + w - 12, y + 38, fill=(58, 78, 112))
    for i in range(4):
        colx = x + 22 + i * (w - 44) / 3
        p.rect(colx - 4, y + 40, colx + 4, y + h - 30, fill=(74, 96, 132))
        p.rect(colx - 7, y + 36, colx + 7, y + 41, fill=(48, 66, 96))
        p.rect(colx - 7, y + h - 34, colx + 7, y + h - 28, fill=(48, 66, 96))
    p.rect(x + 12, y + h - 28, x + w - 12, y + h - 22, fill=(58, 78, 112))
    p.line(x + w - 64, y + h - 58, x + w - 34, y + h - 78,
           fill=(30, 42, 64), width=3)
    p.rect(x + w - 42, y + h - 90, x + w - 22, y + h - 74, fill=(30, 42, 64))
    p.line(x + w - 64, y + h - 58, x + w - 72, y + h - 48,
           fill=(30, 42, 64), width=3)


# ---------------------------------------------------------------------------
# illustration 6: Tiangong handshake
# ---------------------------------------------------------------------------

def art_space(p, x, y, w, h):
    p.vgrad(x, y, x + w, y + h, (14, 22, 50), (36, 54, 96))
    rng = random.Random(2411)
    for _ in range(90):
        sx = x + rng.random() * w
        sy = y + rng.random() * h
        r = 0.4 + rng.random() * 0.9
        p.ellipse(sx - r, sy - r, sx + r, sy + r,
                  fill=mix((230, 236, 255), (130, 150, 200), rng.random()))
    # crescent Earth, kept inside the card
    ex, ey = x + 30, y + h - 30
    p.ellipse(ex - 24, ey - 24, ex + 24, ey + 24, fill=(52, 104, 156))
    p.ellipse(ex - 10, ey - 24, ex + 38, ey + 24, fill=(18, 30, 60))
    p.arc(ex - 24, ey - 24, ex + 24, ey + 24, 120, 300,
          fill=(126, 190, 226), width=1.4)
    cx, cy = x + w - 74, y + h - 34
    p.rect(cx - 38, cy - 5, cx + 38, cy + 5, fill=(226, 232, 240),
           outline=(150, 170, 200), width=0.8)
    p.rect(cx - 5, cy - 26, cx + 5, cy + 26, fill=(226, 232, 240),
           outline=(150, 170, 200), width=0.8)
    for i in range(3):
        p.rect(cx - 58, cy - 14 + i * 10, cx - 38, cy - 7 + i * 10,
               fill=(38, 58, 96), outline=(150, 170, 200), width=0.6)
        p.rect(cx + 38, cy - 14 + i * 10, cx + 58, cy - 7 + i * 10,
               fill=(38, 58, 96), outline=(150, 170, 200), width=0.6)
    p.ellipse(cx + 1, cy + 30, cx + 6, cy + 35, fill=(120, 220, 226))
    for i in range(20):
        ang = i * math.pi * 2 / 20
        p.d.point(((cx + 30 * math.cos(ang)) * S,
                   (cy + 24 * math.sin(ang)) * S), fill=(110, 160, 200))


# ---------------------------------------------------------------------------
# page
# ---------------------------------------------------------------------------

def build(out_path="entry.png"):
    p = Paper()
    rng = random.Random(25112026)

    # paper grain
    for _ in range(2600):
        x, y = rng.randrange(W), rng.randrange(H)
        p.d.point((x * S, y * S), fill=mix(PAPER, PAPER_2, rng.random()))

    M, R = 32, 992
    WID = R - M

    # ---- masthead ---------------------------------------------------------
    p.text(M, 15, "VOL. XCII · NO. 321", font(SANS, 7.2), fill=SOFT, tracking=1.2)
    p.text(R, 15, "FINAL EDITION · $3.00", font(SANS, 7.2), fill=SOFT,
           anchor="rt", tracking=1.2)
    p.line(M, 29, R, 29, fill=INK, width=1.0)

    p.tracked_center(W / 2, 34, "THE WORLD", font(SERIF_BLACK, 84),
                     fill=INK, tracking=3.4)
    p.star(M + 4, 66, 5, fill=RED)
    p.star(R - 4, 66, 5, fill=RED)
    p.line(M, 124, R, 124, fill=INK, width=1.5)

    # ---- date banner ------------------------------------------------------
    p.rect(M, 131, R, 165, fill=INK)
    p.text(M + 12, 140, "WORLD NEWS", font(SANS_BOLD, 8), fill=(226, 214, 192),
           tracking=1.6)
    p.tracked_center(W / 2, 140, "WEDNESDAY · 25 NOVEMBER 2026",
                     font(SANS_BOLD, 14.5), fill=CREAM, tracking=1.6)
    p.text(R - 12, 140, "SIX STORIES", font(SANS_BOLD, 8), fill=(226, 214, 192),
           anchor="rt", tracking=1.6)
    p.line(M, 169, R, 169, fill=INK, width=0.8)

    # ---- hero -------------------------------------------------------------
    p.text(M, 180, "TRADE WAR · WASHINGTON", font(SANS_BOLD, 9.2), fill=RED,
           tracking=1.8)
    head = "TARIFF WALL HITS 14 NATIONS"
    hs = p.fit_size(head, SERIF_BLACK, WID - 24, 57, 44)
    p.text(M, 193, head, font(SERIF_BLACK, hs), fill=INK, tracking=0.6)
    p.text(M, 255, "Washington slaps new duties on China, the EU and 12 others "
                   "over excess capacity as US stocks slide.",
           font(SERIF_ITAL, 15.2), fill=SOFT)

    panel_y, panel_h = 282, 252
    art_tariffs(p, M, panel_y, 592, panel_h)
    p.rect(M, panel_y, M + 592, panel_y + panel_h, outline=INK, width=1.2)

    sx = M + 612
    sw = R - sx
    p.text(sx, 282, "THE STORY", font(SANS_BOLD, 8), fill=RED, tracking=1.6)
    summary = ("The Trump administration proposed tariffs on 14 trading partners "
               "after an eight-month inquiry, with China facing the steepest rate, "
               "up to 40%. Beijing called the overcapacity case \u201cpolitical "
               "manipulation\u201d. US stocks fell as investors weighed a wider "
               "trade war.")
    p.block(sx, 298, summary, font(SERIF, 12.6), sw, 15.6, fill=INK,
            max_lines=7, tag="hero summary")

    p.text(sx, 377, "WHY IT MATTERS", font(SANS_BOLD, 6.8), fill=RED,
           tracking=1.2)
    p.block(sx, 388, "Economists warn the duties could lift US prices and chill "
                     "global trade.", font(SERIF, 9.6), sw, 11.4, fill=INK,
            max_lines=2, tag="hero analysis")

    # tariff ladder
    ly = 414
    p.line(sx, ly, R, ly, fill=FAINT, width=0.8)
    p.text(sx, ly + 6, "PROPOSED RATES", font(SANS_BOLD, 7), fill=SOFT,
           tracking=1.2)
    rows = [("CHINA", "UP TO 40%", 1.00), ("VIETNAM", "UP TO 35%", 0.88),
            ("12 OTHERS", "20-25%", 0.62)]
    for i, (name, rate, frac) in enumerate(rows):
        ry = ly + 19 + i * 20
        p.text(sx, ry, name, font(SANS_BOLD, 7.6), fill=INK, tracking=0.8)
        p.text(sx + 92, ry, rate, font(SANS_BOLD, 7.6), fill=RED, tracking=0.6)
        p.rect(sx + 166, ry + 2, sx + 166 + 150 * frac, ry + 8, fill=RED)
        p.rect(sx + 166, ry + 2, sx + 316, ry + 8, outline=FAINT, width=0.5)

    p.text(sx, 496, "\u201cLevel the playing field for American workers.\u201d",
           font(SERIF_ITAL, 11.2), fill=SOFT)
    p.text(sx, 510, "— USTR Jamieson Greer", font(SANS, 7.2), fill=SOFT,
           tracking=0.6)
    p.text(sx, 523, "BBC · REUTERS · AP", font(SANS_BOLD, 6.4), fill=SOFT,
           tracking=1.0)

    p.line(M, 545, R, 545, fill=INK, width=1.3)
    p.line(M, 549, R, 549, fill=INK, width=0.5)

    # ---- second story: Russia (tall dark card) ----------------------------
    rx0, ry0, rx1, ry1 = M, 559, 356, 892
    p.vgrad(rx0, ry0, rx1, ry1, (52, 20, 22), (26, 12, 14))
    p.rect(rx0, ry0, rx1, ry1, outline=(96, 46, 44), width=1.0)
    p.line(rx0 + 14, ry0 + 46, rx1 - 14, ry0 + 46, fill=(104, 48, 46), width=0.6)
    p.text(rx0 + 14, ry0 + 10, "EUROPE · WAR", font(SANS_BOLD, 7.2),
           fill=(214, 130, 118), tracking=1.4)
    p.text(rx0 + 14, ry0 + 21, "RUSSIA\u2019S TOLL", font(SERIF_BOLD, 28),
           fill=(238, 222, 202))
    p.text(rx0 + 12, ry0 + 50, "490,000", font(SERIF_BLACK, 58),
           fill=(255, 248, 234), tracking=-0.6)
    p.text(rx0 + 14, ry0 + 112, "RUSSIAN SOLDIERS DEAD", font(SANS_BOLD, 8.2),
           fill=(224, 168, 158), tracking=1.1)
    p.line(rx0 + 14, ry0 + 126, rx1 - 14, ry0 + 126, fill=(120, 58, 54), width=0.8)
    art_war_dead(p, rx0, ry0 + 126, rx1 - rx0, 126)
    body = ("BBC Russian matched leaked Rosstat records with Mediazona\u2019s "
            "confirmed-death list and found more than 490,000 military deaths "
            "since the 2022 invasion.")
    p.block(rx0 + 14, ry0 + 258, body, font(SERIF, 10.2), rx1 - rx0 - 28, 12.2,
            fill=(226, 214, 200), max_lines=4, tag="russia body")
    p.text(rx0 + 14, ry1 - 15, "CBS NEWS · BBC RUSSIAN", font(SANS_BOLD, 6.2),
           fill=(186, 138, 128), tracking=0.9)

    # ---- Cairo (wide amber card) ----------------------------------------
    cx0, cy0, cx1, cy1 = 372, 559, 716, 724
    p.rect(cx0, cy0, cx1, cy1, fill=(250, 232, 204),
           outline=(198, 122, 66), width=0.9)
    art_cairo(p, cx0, cy0, 92, cy1 - cy0)
    p.text(cx0 + 104, cy0 + 10, "AFRICA · DISASTER", font(SANS_BOLD, 7),
           fill=ORANGE, tracking=1.2)
    p.text(cx0 + 104, cy0 + 24, "CAIRO TANKER BLAST", font(SERIF_BOLD, 18.5),
           fill=INK)
    body = ("A fuel tanker overturned on Cairo\u2019s ring road and exploded, "
            "killing at least 30 people and injuring 21.")
    p.block(cx0 + 104, cy0 + 50, body, font(SERIF, 10.4), cx1 - cx0 - 116, 12.8,
            fill=INK, max_lines=5, tag="cairo body")
    p.text(cx0 + 104, cy1 - 20, "SKY NEWS · AL JAZEERA", font(SANS_BOLD, 6.0),
           fill=SOFT, tracking=0.8)

    # ---- inflation (mint chart card) ------------------------------------
    ix0, iy0, ix1, iy1 = 732, 559, 992, 724
    p.rect(ix0, iy0, ix1, iy1, fill=(226, 240, 233),
           outline=(96, 150, 132), width=0.9)
    p.text(ix0 + 12, iy0 + 8, "ECONOMY · UNITED STATES", font(SANS_BOLD, 6.8),
           fill=TEAL, tracking=1.1)
    p.text(ix0 + 12, iy0 + 18, "3.8%", font(SERIF_BLACK, 42), fill=TEAL)
    p.text(ix0 + 128, iy0 + 32, "OCTOBER", font(SANS_BOLD, 7), fill=SOFT,
           tracking=1.0)
    p.text(ix0 + 128, iy0 + 42, "YEAR ON YEAR", font(SANS, 6.8), fill=SOFT,
           tracking=0.8)
    p.line(ix0 + 12, iy0 + 58, ix1 - 12, iy0 + 58, fill=(150, 188, 172), width=0.7)
    p.text(ix0 + 12, iy0 + 62, "INFLATION HITS 3.8%", font(SERIF_BOLD, 16.5),
           fill=INK)
    body = ("The Fed\u2019s preferred gauge rose at its fastest pace since May, "
            "ahead of next month\u2019s rate call.")
    p.block(ix0 + 12, iy0 + 80, body, font(SERIF, 9.5), ix1 - ix0 - 24, 11.4,
            fill=INK, max_lines=2, tag="inflation body")
    art_inflation(p, ix0 + 10, iy0 + 104, ix1 - ix0 - 20, 36)
    p.text(ix0 + 12, iy1 - 15, "ABC NEWS · CNBC", font(SANS_BOLD, 6.0),
           fill=SOFT, tracking=0.8)

    # ---- Netanyahu (slate card) -----------------------------------------
    nx0, ny0, nx1, ny1 = 372, 740, 688, 892
    p.rect(nx0, ny0, nx1, ny1, fill=(226, 232, 242),
           outline=(104, 126, 160), width=0.9)
    art_court(p, nx0, ny0, 86, ny1 - ny0)
    p.text(nx0 + 98, ny0 + 10, "MIDDLE EAST · LAW", font(SANS_BOLD, 6.8),
           fill=SLATE, tracking=1.1)
    p.text(nx0 + 98, ny0 + 23, "NETANYAHU CASE", font(SERIF_BOLD, 19.5),
           fill=INK)
    p.text(nx0 + 98, ny0 + 45, "FALTERS", font(SERIF_BOLD, 19.5), fill=INK)
    body = ("Israeli judges suggested dropping the most serious corruption "
            "charges; Netanyahu says the trial \u201cmust end\u201d.")
    p.block(nx0 + 98, ny0 + 72, body, font(SERIF, 10.2), nx1 - nx0 - 110, 12.4,
            fill=INK, max_lines=3, tag="netanyahu body")
    p.text(nx0 + 98, ny1 - 18, "NYT · BBC · AL JAZEERA", font(SANS_BOLD, 6.0),
           fill=SLATE, tracking=0.8)

    # ---- China space (navy card) ----------------------------------------
    qx0, qy0, qx1, qy1 = 704, 740, 992, 892
    art_space(p, qx0, qy0, qx1 - qx0, qy1 - qy0)
    p.rect(qx0, qy0, qx1, qy1, outline=(70, 96, 150), width=0.9)
    p.text(qx0 + 12, qy0 + 10, "ASIA · SPACE", font(SANS_BOLD, 6.8),
           fill=(124, 214, 220), tracking=1.1)
    p.text(qx0 + 12, qy0 + 23, "SPACE HANDSHAKE", font(SERIF_BOLD, 17),
           fill=(242, 244, 250))
    body = ("Shenzhou-24 docked at Tiangong with Muhammad Zeeshan Ali, the first "
            "foreign astronaut aboard China\u2019s station.")
    p.block(qx0 + 12, qy0 + 48, body, font(SERIF, 9.8), qx1 - qx0 - 24, 11.8,
            fill=(226, 230, 242), max_lines=3, tag="space body")
    p.text(qx0 + 12, qy1 - 16, "REUTERS · THE GUARDIAN", font(SANS_BOLD, 5.9),
           fill=(150, 170, 210), tracking=0.7)

    # ---- ticker + sources + footer --------------------------------------
    p.line(M, 902, R, 902, fill=INK, width=1.2)
    p.text(M, 909, "ALSO ON THE DAY", font(SANS_BOLD, 7.6), fill=RED,
           tracking=1.4)
    brief = ("Houthis hit Saudi Arabia\u2019s Ras Tanura refinery  ·  Hera probe "
             "images the DART crater  ·  Bangladesh garment wage set at Tk 17,000  ·  "
             "Andy Taylor, Duran Duran guitarist, dies at 65")
    p.block(M, 921, brief, font(SERIF, 9.2), WID, 11.4, fill=INK, max_lines=2,
            tag="briefs")

    p.line(M, 952, R, 952, fill=FAINT, width=0.7)
    p.text(M, 957, "SOURCES: REUTERS · AP · BBC · CBS · CNBC · SKY NEWS · "
                   "AL JAZEERA · THE GUARDIAN · NYT",
           font(SANS, 7.8), fill=SOFT, tracking=0.5)
    p.line(M, 979, R, 979, fill=FAINT, width=0.7)
    p.text(M, 985, "THE WORLD · WEDNESDAY 25 NOVEMBER 2026", font(SANS, 6.4),
           fill=SOFT, tracking=0.9)
    p.text(R, 985, "PAGE 1 · $3.00", font(SANS_BOLD, 6.4), fill=SOFT,
           anchor="rt", tracking=0.9)

    if WARNINGS:
        for w in WARNINGS:
            print("LAYOUT WARNING:", w)
    p.save(out_path)
    print(f"wrote {out_path} ({W}x{H})")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "entry.png")
