#!/usr/bin/env python3
# news-image-20261122 v1 — rewritten in-session for transcript authorship; 35 stories, Sunday 22 November 2026
"""THE WORLD IN ONE DAY -- front page for Sunday 22 November 2026.

  news22 v1 (22 Nov 2026): 35 stories, all dated Sunday 22 November
  2026 -- a NEW competition, not a revision of news21. Built from
  the news21 v7 base (best score 0.982336) with the v9 real world
  map transplanted in. NEVER pad with a Saturday story: every item
  here happened, or was first reported, on Sun 22 Nov 2026.
  Left out on purpose: El Chapo Isidro capture (raid Fri 20 Nov,
  reported Sat 21 Nov), EU-Indonesia CEPA signing (Sat 21 Nov),
  Venezuela-US military deal (signed Wed 18 Nov), Nigeria boat
  capsize (NEMA statement Sat 21 Nov), ICJ Rohingya ruling
  (Thu 19 Nov), Riemann hypothesis claim (Fri 20 Nov).
  Layout follows the rank-1 news20 reference (date as masthead, stat
  strip, region bar, 3 illustrated leads, 10 featured with thumbnails,
  world map + ALSO list, DATE CHECK box, footer).

  THE #1 FIX -- TRUE SERIF TYPOGRAPHY. The 5x7 and 7x9 bitmap fonts are
  GONE. Every letter on the page is drawn from a hand-built VECTOR
  serif font: each glyph is a filled OUTLINE (stem, bowl and bar
  contours with real counters) in a 100-unit em, with thick vertical
  stems, thin horizontals,
  diagonal contrast and serif feet, rasterised at SS=8 supersampling
  and blended by per-pixel coverage. Large text uses linear coverage
  (genuinely smooth grey edges); small text keeps a sqrt gamma so
  1 px strokes stay dark. That is what makes the masthead,
  headlines and body read as a real newspaper instead of pixel art:
  the shapes themselves are smooth curves, not a finer grid of blocks.
  Bold weights dilate the outlines (masthead 1.45x,
  headlines 1.3x); the subline is a sheared (italic) serif.

  Stdlib only, no network, no external files, no randomness: two runs
  produce byte-identical output. Writes $MAKEFUN_OUTPUT_DIR/entry.png
  (fallback /output). 1024x1024 PNG.

  Stories (35): 3 leads + 10 featured + 22 ALSO, every one dated
  Sunday 22 November 2026, every one carrying its source in
  parentheses. Regions (recounted from the 35 kept stories): EUROPE 10,
  ASIA 8, MIDDLE EAST 6, AFRICA 2, AMERICAS 7, OCEANIA 1, GLOBAL 1.
  v7 grey-bar fix kept (pic_fire chimney height is h - 0.30h, not
  an absolute coordinate). Story 8 (global markets) is off the map,
  noted below the map. v9 bottom block: map 336x176 with 7x11
  cells, ALSO in 2 columns at em 7, leading 15.
  DATE CHECK lists the Fri 20 - Sat 21 Nov items deliberately left
  out -- none of them is claimed as 22 Nov.
"""
import hashlib
import math
import os
import struct
import zlib

W = H = 1024
SS = 8  # text supersampling factor

PAPER = (250, 246, 236)
INK = (17, 17, 17)
GRAY = (74, 74, 74)
RED = (176, 30, 30)
PANEL = (238, 232, 214)
NAVY = (24, 40, 72)
SEA = (70, 110, 170)
LAND = (198, 180, 140)
GREEN = (46, 110, 60)
YELLOW = (255, 200, 60)
BLUE = (30, 70, 160)

# ------------------------------------------------------- vector serif ----
# TRUE OUTLINE SERIF (v2). Every glyph is a set of FILLED OUTLINE
# contours in a 100-unit em (cap top y=0, baseline y=70, descender
# y=92, x-height top y=22) -- not stroked centrelines. A contour is
# a closed polygon; a glyph stroke ('P', [shape, ...]) is one or
# more such contours, each filled separately so overlaps union.
#   * _band(): a curved stroke as an outline -- outer arc + inner
#     arc. Thickness follows the classic serif contrast: thick
#     (8.3) where the curve runs vertically (east/west sides),
#     thin (4.0) where it runs horizontally (top/bottom).
#     A full 360-degree band IS a ring with a real counter.
#   * _stem(): vertical stem with bracketed serif feet -- flared
#     triangular feet, not rounded blobs.
#   * _sband(): an S-curve as a band along a two-arc centreline,
#     so S and s are one continuous stroke with a real middle
#     crossing (the old two-arc S read as C; the old e was a
#     120-degree partial bowl). The e bowl is now a 300-degree
#     band plus a crossbar.
# Bold weights dilate outlines in the renderer (shifted unions).
def _ell_pts(cx, cy, rx, ry, a0, a1, step=6.0):
    pts = []
    if a1 >= a0:
        n = max(2, int((a1 - a0) / step) + 1)
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    else:
        n = max(2, int((a0 - a1) / step) + 1)
        for i in range(n + 1):
            a = math.radians(a0 - (a0 - a1) * i / n)
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts


def _thick(a, tscale=1.0):
    """Stroke thickness at ellipse angle a (0 deg = east, 90 = south):
    thick at the sides, thin at top/bottom -- Times contrast."""
    return (4.0 + 4.3 * abs(math.cos(math.radians(a)))) * tscale


def _band(cx, cy, rx, ry, a0, a1, tscale=1.0):
    """Filled outline of a curved stroke: outer arc + inner arc back.
    a0 -> a1 increasing goes clockwise (through east, south, west,
    north); decreasing goes the other way. A 360-degree band is a
    closed ring with a real counter."""
    full = abs(a1 - a0) >= 359.0
    if a1 >= a0:
        n = max(2, int((a1 - a0) / 6.0) + 1)
        angs = [a0 + (a1 - a0) * i / n for i in range(n + 1)]
    else:
        n = max(2, int((a0 - a1) / 6.0) + 1)
        angs = [a0 - (a0 - a1) * i / n for i in range(n + 1)]
    outer = []
    inner = []
    m = len(angs)
    for j, a in enumerate(angs):
        r = math.radians(a)
        t = _thick(a, tscale)
        if not full:
            d = min(j, m - 1 - j)
            if d < 3:
                t *= 0.78 + 0.22 * d / 3.0
        outer.append((cx + rx * math.cos(r), cy + ry * math.sin(r)))
        inner.append((cx + (rx - t) * math.cos(r),
                      cy + (ry - t) * math.sin(r)))
    return outer + inner[::-1]


def _s_curve(cxT, cyT, rxT, ryT, cxB, cyB, rxB, ryB):
    """Centreline of an S: top bowl arc (terminal at upper right,
    over the top, down to the middle) + bottom bowl arc (middle,
    round the right, under the bottom, terminal at lower left)."""
    pts = _ell_pts(cxT, cyT, rxT, ryT, -35, -270)
    pts += _ell_pts(cxB, cyB, rxB, ryB, -90, 145)[1:]
    return pts


def _sband(pts):
    """Band along a polyline centreline; thickness from the normal's
    x-component (thick where the stroke runs vertically)."""
    n = len(pts)
    left = []
    right = []
    for i, (x, y) in enumerate(pts):
        x0, y0 = pts[max(0, i - 1)]
        x1, y1 = pts[min(n - 1, i + 1)]
        dx, dy = x1 - x0, y1 - y0
        ln = (dx * dx + dy * dy) ** 0.5 or 1.0
        tx, ty = dx / ln, dy / ln
        nx, ny = -ty, tx
        t = 4.0 + 4.3 * abs(nx)
        d = min(i, n - 1 - i)
        if d < 3:
            t *= 0.8 + 0.2 * d / 3.0
        left.append((x + nx * t / 2.0, y + ny * t / 2.0))
        right.append((x - nx * t / 2.0, y - ny * t / 2.0))
    return left + right[::-1]


def _rect_c(x0, y0, x1, y1):
    return [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]


def _stem_c(x, y0, y1, w=7.5, top=True, bot=True, foot=5.0, br=5.0):
    """Vertical stem with bracketed serif feet (flared feet)."""
    x0 = x - w / 2.0
    x1 = x + w / 2.0
    pts = []
    if top:
        pts.append((x0 - foot, y0))
        pts.append((x1 + foot, y0))
        pts.append((x1, y0 + br))
    else:
        pts.append((x0, y0))
        pts.append((x1, y0))
    if bot:
        pts.append((x1, y1 - br))
        pts.append((x1 + foot, y1))
        pts.append((x0 - foot, y1))
        pts.append((x0, y1 - br))
    else:
        pts.append((x1, y1))
        pts.append((x0, y1))
    if top:
        pts.append((x0, y0 + br))
    return [pts]


def _diag_c(x0, y0, x1, y1, w=7.5):
    dx, dy = x1 - x0, y1 - y0
    ln = (dx * dx + dy * dy) ** 0.5
    nx, ny = -dy / ln * w / 2.0, dx / ln * w / 2.0
    return [[(x0 + nx, y0 + ny), (x1 + nx, y1 + ny),
             (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)]]


def _band_c(cx, cy, rx, ry, a0, a1, tscale=1.0):
    return [_band(cx, cy, rx, ry, a0, a1, tscale)]


def _s_c(cxT, cyT, rxT, ryT, cxB, cyB, rxB, ryB):
    return [_sband(_s_curve(cxT, cyT, rxT, ryT, cxB, cyB, rxB, ryB))]


def P(*shapes):
    """A filled-outline glyph stroke: list of shapes (contours)."""
    return ('P', list(shapes))


def D(r, x, y):
    return ('D', r, x, y)


GLYPHS = {
    # ---- uppercase: cap top 0, baseline 70 ----
    'A': (68, [P(_diag_c(6, 70, 34, 2, 9), _diag_c(34, 2, 62, 70, 7),
                  _rect_c(18, 44, 50, 49), _rect_c(0, 66, 14, 70),
                  _rect_c(54, 66, 68, 70))]),
    'B': (54, [P(_stem_c(10, 2, 68),
                  _band_c(10, 19, 27, 17.5, -90, 90),
                  _band_c(10, 52, 29, 16.5, -90, 90),
                  _rect_c(10, 33, 38, 38))]),
    'C': (62, [P(_band_c(32, 35, 29, 35, 50, 310))]),
    'D': (60, [P(_stem_c(10, 2, 68), _band_c(10, 35, 44, 35, -90, 90))]),
    'E': (54, [P(_stem_c(10, 2, 68), _rect_c(10, 2, 50, 7),
                  _rect_c(10, 33, 42, 38), _rect_c(10, 63, 52, 68))]),
    'F': (52, [P(_stem_c(10, 2, 68), _rect_c(10, 2, 50, 7),
                  _rect_c(10, 33, 42, 38))]),
    'G': (62, [P(_band_c(32, 35, 29, 35, 50, 310),
                  _rect_c(30, 42, 58, 47), _rect_c(52, 42, 58, 68))]),
    'H': (68, [P(_stem_c(10, 2, 68), _stem_c(58, 2, 68),
                  _rect_c(16, 33, 52, 38))]),
    'I': (46, [P(_stem_c(23, 2, 68), _rect_c(8, 2, 38, 7),
                  _rect_c(8, 63, 38, 68))]),
    'J': (58, [P(_rect_c(34, 2, 60, 7), _rect_c(43, 2, 53, 54),
                  _band_c(30, 52, 18, 16, 0, 180))]),
    'K': (60, [P(_stem_c(10, 2, 68), _diag_c(22, 38, 54, 4, 8),
                  _diag_c(28, 32, 56, 68, 9), _rect_c(46, 2, 60, 6),
                  _rect_c(48, 66, 62, 70))]),
    'L': (56, [P(_stem_c(10, 2, 68), _rect_c(10, 63, 54, 68))]),
    'M': (72, [P(_stem_c(8, 2, 68), _stem_c(64, 2, 68),
                  _diag_c(14, 4, 36, 46, 8), _diag_c(36, 46, 58, 4, 8))]),
    'N': (66, [P(_stem_c(8, 2, 68), _stem_c(58, 2, 68),
                  _diag_c(14, 4, 52, 66, 8))]),
    'O': (68, [P(_band_c(34, 35, 29, 35, 0, 360))]),
    'P': (54, [P(_stem_c(10, 2, 68), _band_c(10, 19, 27, 17.5, -90, 90),
                  _rect_c(10, 33, 36, 38))]),
    'Q': (68, [P(_band_c(34, 35, 29, 35, 0, 360),
                  _diag_c(44, 52, 62, 72, 7))]),
    'R': (56, [P(_stem_c(10, 2, 68), _band_c(10, 19, 27, 17.5, -90, 90),
                  _rect_c(10, 33, 36, 38), _diag_c(30, 36, 56, 68, 9))]),
    # S: one continuous band, top terminal upper right, middle
    # crossing, bottom terminal lower left -- unmistakably S, not C.
    'S': (58, [P(_s_c(29, 20, 24, 17, 29, 50, 24, 17))]),
    'T': (64, [P(_rect_c(4, 2, 60, 7), _stem_c(32, 4, 68, 10))]),
    'U': (66, [P(_stem_c(8, 2, 52, bot=False),
                  _stem_c(58, 2, 52, bot=False),
                  _band_c(33, 50, 25, 20, 0, 180))]),
    'V': (62, [P(_diag_c(6, 2, 31, 68, 9), _diag_c(31, 68, 56, 2, 9),
                  _rect_c(0, 2, 12, 6), _rect_c(50, 2, 62, 6))]),
    'W': (74, [P(_diag_c(4, 2, 18, 68, 8), _diag_c(18, 68, 36, 14, 8),
                  _diag_c(36, 14, 54, 68, 8), _diag_c(54, 68, 70, 2, 8))]),
    'X': (62, [P(_diag_c(8, 2, 54, 68, 9), _diag_c(54, 2, 8, 68, 9),
                  _rect_c(2, 2, 14, 6), _rect_c(48, 2, 60, 6),
                  _rect_c(2, 66, 14, 70), _rect_c(48, 66, 60, 70))]),
    'Y': (62, [P(_diag_c(6, 2, 31, 36, 9), _diag_c(56, 2, 31, 36, 9),
                  _stem_c(31, 36, 68, 10), _rect_c(0, 2, 12, 6),
                  _rect_c(50, 2, 62, 6))]),
    'Z': (58, [P(_rect_c(4, 2, 54, 7), _diag_c(52, 6, 8, 64, 8),
                  _rect_c(4, 63, 54, 68))]),
    # ---- lowercase: x-height top 22, baseline 70, descender 92 ----
    'a': (54, [P(_band_c(26, 48, 20, 22, 0, 360),
                  _band_c(26, 36, 20, 14, 180, 360),
                  _stem_c(46, 20, 68, 8, top=False))]),
    'b': (52, [P(_stem_c(8, 0, 68, 10), _band_c(28, 48, 20, 22, 0, 360))]),
    'c': (50, [P(_band_c(27, 46, 20, 24, 50, 310))]),
    'd': (56, [P(_band_c(26, 48, 20, 22, 0, 360),
                  _stem_c(46, 0, 68, 10))]),
    # e: open bowl (90-degree gap at upper right) + crossbar -- the eye
    # is visibly open, unmistakably e, not o/theta. No right connector.
    'e': (48, [P(_band_c(24, 46, 19, 23, 25, 295),
                  _rect_c(5, 40, 42, 46))]),
    'f': (46, [P(_stem_c(26, 12, 68, 9, top=False),
                  _band_c(26, 14, 15, 14, 180, 320),
                  _rect_c(10, 32, 42, 37))]),
    'g': (54, [P(_band_c(26, 46, 20, 22, 0, 360),
                  _stem_c(46, 20, 80, 8, top=False, bot=False),
                  _band_c(30, 80, 16, 12, 0, 180))]),
    'h': (56, [P(_stem_c(8, 0, 68, 10), _band_c(28, 46, 20, 24, 180, 360),
                  _rect_c(43, 46, 53, 68))]),
    'i': (30, [P(_stem_c(15, 22, 68, 9)), D(5.5, 15, 9)]),
    'j': (34, [P(_stem_c(19, 22, 78, 9, top=False, bot=False),
                  _band_c(19, 78, 11, 12, 0, 180)), D(5.5, 19, 9)]),
    'k': (54, [P(_stem_c(8, 0, 68, 10), _diag_c(20, 40, 44, 22, 8),
                  _diag_c(26, 36, 48, 68, 9))]),
    'l': (30, [P(_stem_c(15, 0, 68, 10))]),
    'm': (78, [P(_stem_c(6, 22, 68, 9, top=False),
                  _band_c(22, 44, 16, 22, 180, 360),
                  _rect_c(33, 44, 43, 68),
                  _band_c(54, 44, 16, 22, 180, 360),
                  _rect_c(65, 44, 75, 68))]),
    'n': (56, [P(_stem_c(8, 22, 68, 9, top=False),
                  _band_c(28, 46, 20, 24, 180, 360),
                  _rect_c(43, 46, 53, 68))]),
    'o': (52, [P(_band_c(26, 46, 20, 24, 0, 360))]),
    'p': (56, [P(_stem_c(8, 22, 90, 10, top=False),
                  _band_c(28, 48, 20, 22, 0, 360))]),
    'q': (56, [P(_band_c(26, 48, 20, 22, 0, 360),
                  _stem_c(46, 22, 90, 10, top=False))]),
    'r': (46, [P(_stem_c(8, 22, 68, 9, top=False),
                  _band_c(24, 36, 16, 14, 180, 360))]),
    's': (50, [P(_s_c(25, 34, 18, 12, 25, 58, 18, 12))]),
    't': (44, [P(_stem_c(22, 6, 64, 9, top=False),
                  _band_c(34, 60, 12, 12, 90, 180),
                  _rect_c(8, 32, 36, 37))]),
    'u': (52, [P(_stem_c(8, 22, 56, 9, top=False, bot=False),
                  _stem_c(44, 22, 56, 9, top=False, bot=False),
                  _band_c(26, 54, 18, 16, 0, 180))]),
    'v': (50, [P(_diag_c(6, 22, 25, 68, 8), _diag_c(25, 68, 44, 22, 8))]),
    'w': (54, [P(_diag_c(4, 22, 13, 68, 8), _diag_c(13, 68, 25, 30, 8),
                  _diag_c(25, 30, 37, 68, 8), _diag_c(37, 68, 50, 22, 8))]),
    'x': (50, [P(_diag_c(6, 22, 44, 68, 8), _diag_c(44, 22, 6, 68, 8))]),
    'y': (50, [P(_diag_c(6, 22, 25, 58, 8), _diag_c(44, 22, 25, 58, 8),
                  _diag_c(25, 58, 13, 90, 8))]),
    'z': (52, [P(_rect_c(6, 22, 46, 27), _diag_c(44, 26, 8, 66, 8),
                  _rect_c(6, 65, 46, 70))]),
    # ---- digits: cap top 0, baseline 70 ----
    '0': (56, [P(_band_c(28, 35, 23, 35, 0, 360))]),
    '1': (48, [P(_diag_c(10, 26, 28, 4, 7), _stem_c(28, 2, 68, 10),
                  _rect_c(12, 63, 44, 68))]),
    '2': (56, [P(_band_c(28, 20, 22, 18, 180, 360),
                  _diag_c(50, 20, 10, 64, 8), _rect_c(8, 63, 50, 68))]),
    '3': (56, [P(_band_c(28, 19, 20, 16, 200, 420),
                  _band_c(28, 52, 22, 17, -60, 140))]),
    '4': (54, [P(_diag_c(38, 2, 10, 48, 8), _rect_c(6, 43, 50, 48),
                  _stem_c(38, 2, 68, 10))]),
    '5': (54, [P(_rect_c(10, 2, 48, 7), _rect_c(10, 4, 17, 36),
                  _rect_c(10, 31, 42, 36),
                  _band_c(30, 50, 20, 17, -75, 140))]),
    '6': (56, [P(_band_c(28, 46, 22, 24, 0, 360),
                  _band_c(30, 26, 20, 22, -30, -220))]),
    '7': (54, [P(_rect_c(8, 2, 50, 7), _diag_c(48, 6, 20, 68, 9))]),
    '8': (52, [P(_band_c(26, 20, 18, 16, 0, 360),
                  _band_c(26, 51, 20, 19, 0, 360))]),
    '9': (56, [P(_band_c(28, 24, 22, 22, 0, 360),
                  _band_c(28, 44, 22, 24, 0, 130))]),
    # ---- punctuation ----
    ' ': (28, []),
    '.': (20, [D(5, 10, 66)]),
    ',': (20, [D(5, 10, 66), P(_diag_c(10, 66, 4, 80, 6))]),
    ':': (20, [D(5, 10, 26), D(5, 10, 58)]),
    ';': (20, [D(5, 10, 26), D(5, 10, 58), P(_diag_c(10, 58, 4, 72, 6))]),
    '-': (48, [P(_rect_c(8, 33, 40, 39))]),
    '/': (48, [P(_diag_c(38, 2, 10, 68, 7))]),
    '(': (30, [P(_band_c(34, 35, 20, 35, 110, 250))]),
    ')': (30, [P(_band_c(-4, 35, 20, 35, -70, 70))]),
    '%': (64, [P(_band_c(18, 18, 10, 10, 0, 360, 0.55),
                  _band_c(46, 52, 10, 10, 0, 360, 0.55),
                  _diag_c(52, 4, 12, 66, 6))]),
    '&': (56, [P(_band_c(26, 24, 13, 12, 0, 360, 0.7),
                  _diag_c(38, 14, 14, 68, 6),
                  _band_c(26, 54, 16, 14, 0, 180))]),
    '+': (48, [P(_rect_c(8, 31, 40, 37), _rect_c(21, 16, 27, 52))]),
    '$': (52, [P(_s_c(26, 22, 20, 15, 26, 48, 20, 15),
                  _rect_c(23, 0, 29, 70))]),
    "'": (20, [P(_diag_c(12, 2, 8, 20, 6))]),
    '"': (36, [P(_diag_c(10, 2, 6, 20, 6), _diag_c(26, 2, 22, 20, 6))]),
    '!': (20, [P(_rect_c(7, 2, 13, 52)), D(5, 10, 64)]),
    '?': (52, [P(_band_c(26, 18, 18, 16, 200, 420),
                  _diag_c(42, 26, 28, 44, 8)), D(5, 28, 62)]),
    '=': (48, [P(_rect_c(8, 24, 40, 29), _rect_c(8, 44, 40, 49))]),
    '•': (24, [D(6, 12, 40)]),
    '·': (20, [D(5, 10, 36)]),
}

# characters normalised before lookup
NORMALISE = {'’': "'", '‘': "'", '“': '"', '”': '"',
             '–': '-', '—': '-', '…': '.', '×': 'x'}

# ------------------------------------------------------ font rendering ----
# Each glyph is rasterised once per (char, em_px, weight, italic) into a
# coverage map at output resolution, cached, then blended onto the page.
# Coverage comes from a SS=8 supersampled mask: smooth curves get grey
# edge pixels instead of stair-steps. Large text (em >= 14) blends with
# linear coverage; small text uses a sqrt gamma to keep 1 px strokes dark.
_GLYPH_CACHE = {}


def _arc_points(cx, cy, rx, ry, a0, a1):
    step = 6.0
    pts = []
    if a1 >= a0:
        n = max(2, int((a1 - a0) / step) + 1)
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    else:
        n = max(2, int((a0 - a1) / step) + 1)
        for i in range(n + 1):
            a = math.radians(a0 - (a0 - a1) * i / n)
            pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts


def _fill_poly_mask(mask, mw, mh, pts):
    """Scanline-fill a polygon (float coords) into a bytearray mask."""
    if len(pts) < 3:
        return
    ys = [p[1] for p in pts]
    y0 = max(0, int(math.floor(min(ys))))
    y1 = min(mh - 1, int(math.ceil(max(ys))))
    n = len(pts)
    for y in range(y0, y1 + 1):
        yc = y + 0.5
        xs = []
        for i in range(n):
            x1, yy1 = pts[i]
            x2, yy2 = pts[(i + 1) % n]
            if (yy1 <= yc < yy2) or (yy2 <= yc < yy1):
                xs.append(x1 + (yc - yy1) * (x2 - x1) / (yy2 - yy1))
        xs.sort()
        row = y * mw
        for i in range(0, len(xs) - 1, 2):
            xa = max(0, int(math.floor(xs[i])))
            xb = min(mw - 1, int(math.ceil(xs[i + 1])))
            if xb >= xa:
                mask[row + xa:row + xb + 1] = b'\x01' * (xb - xa + 1)


def _fill_circle_mask(mask, mw, mh, cx, cy, r):
    y0 = max(0, int(math.floor(cy - r)))
    y1 = min(mh - 1, int(math.ceil(cy + r)))
    for y in range(y0, y1 + 1):
        dy = (y + 0.5) - cy
        if r * r <= dy * dy:
            continue  # row is outside the circle: fill nothing
        dx = (r * r - dy * dy) ** 0.5
        xa = max(0, int(math.floor(cx - dx)))
        xb = min(mw - 1, int(math.ceil(cx + dx)))
        if xb >= xa:
            mask[y * mw + xa:y * mw + xb + 1] = b'\x01' * (xb - xa + 1)


def _stroke_segment(mask, mw, mh, p0, p1, half_w, caps=True):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    ln = (dx * dx + dy * dy) ** 0.5
    if ln < 1e-6:
        _fill_circle_mask(mask, mw, mh, p0[0], p0[1], half_w)
        return
    nx, ny = -dy / ln * half_w, dx / ln * half_w
    _fill_poly_mask(mask, mw, mh, [
        (p0[0] + nx, p0[1] + ny), (p1[0] + nx, p1[1] + ny),
        (p1[0] - nx, p1[1] - ny), (p0[0] - nx, p0[1] - ny)])
    if caps:
        _fill_circle_mask(mask, mw, mh, p0[0], p0[1], half_w)
        _fill_circle_mask(mask, mw, mh, p1[0], p1[1], half_w)


def _render_glyph(ch, em, weight, italic):
    """Return (advance_px, w_px, h_px, [(dx, dy, alpha), ...]) where
    alpha is 0..1 coverage for each inked output pixel."""
    key = (ch, em, weight, italic)
    hit = _GLYPH_CACHE.get(key)
    if hit is not None:
        return hit
    width, strokes = GLYPHS.get(ch, GLYPHS[' '])
    k = em * SS / 100.0          # mask px per em unit
    shear = 0.16 if italic else 0.0
    # mask size: em box is 100 units tall. Italic shear moves the cap
    # top left by up to 11.2 units and descenders right by ~3.5 units;
    # allow ~21 units of left margin plus stroke half-width.
    pad = 2
    pad_l = pad + (int(math.ceil(21 * k)) if italic else 0)
    mw = int(math.ceil((width + 34) * k)) + 2 * pad
    mh = int(math.ceil(100 * k)) + 2 * pad
    mask = bytearray(mw * mh)

    def tx(x, y):
        return pad_l + (x + shear * (y - 70)) * k, pad + y * k

    for st in strokes:
        kind = st[0]
        if kind == 'L':
            wdt = st[1] * weight
            pts = [tx(x, y) for x, y in st[2]]
            hw = wdt * k / 2.0
            for a, b in zip(pts, pts[1:]):
                _stroke_segment(mask, mw, mh, a, b, hw, caps=False)
            for p in pts:
                _fill_circle_mask(mask, mw, mh, p[0], p[1], hw)
        elif kind == 'A':
            wdt = st[1] * weight
            pts = [tx(x, y) for x, y in
                   _arc_points(st[2], st[3], st[4], st[5], st[6], st[7])]
            hw = wdt * k / 2.0
            for a, b in zip(pts, pts[1:]):
                _stroke_segment(mask, mw, mh, a, b, hw, caps=False)
            for p in pts[::4]:
                _fill_circle_mask(mask, mw, mh, p[0], p[1], hw)
        elif kind == 'D':
            cx, cy = tx(st[2], st[3])
            _fill_circle_mask(mask, mw, mh, cx, cy, st[1] * weight * k)
        elif kind == 'P':
            # Filled-outline glyph: each shape is one closed contour
            # (a band, a stem, a bar, ...). Shapes are filled one by
            # one, so overlaps union instead of cutting holes. Bold
            # weights dilate the outline by unioning shifted copies.
            e = (weight - 1.0) * 5.0 * k
            contours = [[tx(x, y) for x, y in contour]
                        for shape in st[1] for contour in shape]
            shifts = [(0.0, 0.0)] if e <= 0.01 else (
                (0.0, 0.0), (-e, 0.0), (e, 0.0), (0.0, -e), (0.0, e))
            for dx, dy in shifts:
                for contour in contours:
                    _fill_poly_mask(mask, mw, mh,
                                    [(px + dx, py + dy)
                                     for px, py in contour])
    # downsample SSxSS -> coverage; collect inked output pixels
    out_w = (mw + SS - 1) // SS
    out_h = (mh + SS - 1) // SS
    ink = []
    for oy in range(out_h):
        for ox in range(out_w):
            s = 0
            for my in range(oy * SS, min(mh, (oy + 1) * SS)):
                row = my * mw + ox * SS
                # clamp the window to the row: never bleed into the
                # next row's first columns (that painted a phantom
                # vertical line at every glyph's right edge).
                s += sum(mask[row:min(row + SS, (my + 1) * mw)])
            if s:
                cov = s / (SS * SS)
                # Large text (masthead, stat numbers, headlines, em >= 14)
                # uses linear coverage so edges fade genuinely smoothly;
                # small text keeps the sqrt gamma so 1 px strokes stay dark.
                ink.append((ox, oy, cov if em >= 14 else cov ** 0.5))
    adv = int(round(width * em / 100.0)) + max(0, int(round(0.03 * em)))
    res = (adv, out_w, out_h, ink)
    _GLYPH_CACHE[key] = res
    return res


# Kerning (em units, negative tightens): pairs whose side bearings
# leave a visibly wider gap than the surrounding pairs.
KERN = {
    ('r', 'd'): -3,
}


def _pair_kern(prev, ch, em):
    if prev is None:
        return 0
    return int(round(KERN.get((prev, ch), 0) * em / 100.0))


def _glyph_adv(ch, em, weight, italic):
    return _render_glyph(ch, em, weight, italic)[0]


# -------------------------------------------------------------- canvas ----
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = c[0]
            self.buf[i + 1] = c[1]
            self.buf[i + 2] = c[2]

    def get(self, x, y):
        i = (y * self.w + x) * 3
        return (self.buf[i], self.buf[i + 1], self.buf[i + 2])

    def fill_rect(self, x, y, w, h, c):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            for xx in range(x0, x1):
                i = base + (xx - x0) * 3
                self.buf[i] = c[0]
                self.buf[i + 1] = c[1]
                self.buf[i + 2] = c[2]

    def hline(self, x0, x1, y, c, t=1):
        if x1 < x0:
            x0, x1 = x1, x0
        for yy in range(y, y + t):
            for xx in range(x0, x1 + 1):
                self.set(xx, yy, c)

    def vline(self, x, y0, y1, c, t=1):
        if y1 < y0:
            y0, y1 = y1, y0
        for xx in range(x, x + t):
            for yy in range(y0, y1 + 1):
                self.set(xx, yy, c)

    def line(self, x0, y0, x1, y1, c, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.fill_rect(x, y, t, t, c)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def fill_circle(self, cx, cy, r, c):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.hline(cx - dx, cx + dx, cy + dy, c)

    def circle(self, cx, cy, r, c, t=1):
        x, y, d = 0, r, 1 - r
        while x <= y:
            for px, py in ((cx + x, cy + y), (cx - x, cy + y),
                           (cx + x, cy - y), (cx - x, cy - y),
                           (cx + y, cy + x), (cx - y, cy + x),
                           (cx + y, cy - x), (cx - y, cy - x)):
                self.fill_rect(px, py, t, t, c)
            if d < 0:
                d += 2 * x + 3
            else:
                d += 2 * (x - y) + 5
                y -= 1
            x += 1

    def fill_poly(self, pts, c):
        ys = [p[1] for p in pts]
        n = len(pts)
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(n):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % n]
                if (y1 <= y < y2) or (y2 <= y < y1):
                    xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hline(int(xs[i]), int(xs[i + 1]), y, c)

    def star(self, cx, cy, r, c, t=2):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1),
                       (1, 1), (1, -1), (-1, 1), (-1, -1)):
            self.line(cx, cy, cx + dx * r, cy + dy * r, c, t)
        self.fill_circle(cx, cy, max(2, r // 4), c)

    # ------------------------------------------------------------ text ----
    def vtext(self, x, y, s, em, c, weight=1.0, italic=False):
        """Draw smooth vector serif text. (x, y) = top-left of the em
        box; em = em height in px. Returns x just past the last glyph."""
        prev = None
        for ch in s:
            ch = NORMALISE.get(ch, ch)
            if prev is not None:
                x += _pair_kern(prev, ch, em)
            adv, gw, gh, ink = _render_glyph(ch, em, weight, italic)
            for dx, dy, a in ink:
                px, py = x + dx, y + dy
                if 0 <= px < self.w and 0 <= py < self.h:
                    if a >= 1.0:
                        self.set(px, py, c)
                    else:
                        bg = self.get(px, py)
                        self.set(px, py, tuple(
                            int(bg[i] + (c[i] - bg[i]) * a + 0.5)
                            for i in range(3)))
            x += adv
            prev = ch
        return x

    def vtext_width(self, s, em, weight=1.0, italic=False):
        w = 0
        prev = None
        for ch in s:
            ch = NORMALISE.get(ch, ch)
            if prev is not None:
                w += _pair_kern(prev, ch, em)
            w += _glyph_adv(ch, em, weight, italic)
            prev = ch
        return w

    def vtext_centred(self, cx, y, s, em, c, weight=1.0, italic=False):
        x = cx - self.vtext_width(s, em, weight, italic) // 2
        self.vtext(x, y, s, em, c, weight, italic)
        return x

    def vtext_right(self, x_right, y, s, em, c, weight=1.0, italic=False):
        x = x_right - self.vtext_width(s, em, weight, italic)
        self.vtext(x, y, s, em, c, weight, italic)
        return x

    def vwrap(self, s, em, max_w, weight=1.0, italic=False):
        lines, cur = [], ''
        for word in s.split(' '):
            trial = (cur + ' ' + word).strip() if cur else word
            if self.vtext_width(trial, em, weight, italic) <= max_w:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        return lines


# ------------------------------------------------------------------ png ----
def write_png(path, canvas):
    w, h = canvas.w, canvas.h
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += canvas.buf[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        out = struct.pack('>I', len(data)) + typ + data
        out += struct.pack('>I', zlib.crc32(typ + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
    png = (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr)
           + chunk(b'IDAT', comp) + chunk(b'IEND', b''))
    with open(path, 'wb') as f:
        f.write(png)
    return png


# ------------------------------------------------------- drawing helpers ----
def grad_v(cv, x, y, w, h, c1, c2):
    for yy in range(h):
        t = yy / max(1, h - 1)
        c = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        cv.hline(x, x + w - 1, y + yy, c)

def grad_h(cv, x, y, w, h, c1, c2):
    for xx in range(w):
        t = xx / max(1, w - 1)
        c = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
        cv.vline(x + xx, y, y + h - 1, c)

def hatch_diag(cv, x, y, w, h, c, step=6):
    for k in range(-h, w + h, step):
        cv.line(x + k, y + h - 1, x + k + h, y, c, 1)

def stipple(cv, x, y, w, h, c, seed=7, density=3):
    s = seed
    for yy in range(y, y + h, 2):
        for xx in range(x, x + w, 2):
            s = (s * 1103515245 + 12345) & 0x7FFFFFFF
            if s % 10 < density:
                cv.set(xx, yy, c)

def apply_grain(cv, amp=1, cov=0.45):
    """Fine deterministic newsprint grain. amp 1 on 45% of pixels
    keeps the file well under 1 MiB (v5: ~720 KB at this setting)."""
    buf = cv.buf
    state = 987654321
    span = 2 * amp + 1
    for i in range(0, len(buf), 3):
        state = (state * 1664525 + 1013904223) & 0xFFFFFFFF
        px = i // 3
        h = ((px * 2654435761) & 0xFFFFFFFF) / 4294967296.0
        if h >= cov:
            continue
        d = (state >> 24) % span - amp
        if d:
            v = buf[i] + d
            buf[i] = 255 if v > 255 else (0 if v < 0 else v)
        d = ((state >> 16) & 0xFF) % span - amp
        if d:
            v = buf[i + 1] + d
            buf[i + 1] = 255 if v > 255 else (0 if v < 0 else v)
        d = ((state >> 8) & 0xFF) % span - amp
        if d:
            v = buf[i + 2] + d
            buf[i + 2] = 255 if v > 255 else (0 if v < 0 else v)

# ---------------------------------------------------------- pictograms ----
# Every picture is drawn from geometric primitives in code -- original
# work, no images, no copying of any reference artwork.

def dashed(cv, x0, y0, x1, y1, c):
    n = max(abs(x1 - x0), abs(y1 - y0)) // 8
    if n == 0:
        return
    for i in range(n):
        t0 = i / n
        t1 = (i + 0.55) / n
        cv.line(int(x0 + (x1 - x0) * t0), int(y0 + (y1 - y0) * t0),
                int(x0 + (x1 - x0) * t1), int(y0 + (y1 - y0) * t1), c, 1)


def pic_box(cv, x, y, w, h, bg=PANEL):
    cv.fill_rect(x, y, w, h, bg)
    cv.hline(x, x + w - 1, y, INK, 1)
    cv.hline(x, x + w - 1, y + h - 1, INK, 1)
    cv.vline(x, y, y + h - 1, INK, 1)
    cv.vline(x + w - 1, y, y + h - 1, INK, 1)


def tag(cv, x, y, s, em=10):
    """Red tag with paper text; returns its width."""
    w = cv.vtext_width(s, em, 1.3) + 8
    h = em + 5
    cv.fill_rect(x, y, w, h, RED)
    cv.vtext(x + 4, y + 2, s, em, PAPER, 1.3)
    return w


def tag_white(cv, x, y, s, em=10):
    """Paper tag with ink text and ink frame; returns its width."""
    w = cv.vtext_width(s, em, 1.3) + 8
    h = em + 5
    cv.fill_rect(x, y, w, h, PAPER)
    cv.hline(x, x + w - 1, y, INK, 1)
    cv.hline(x, x + w - 1, y + h - 1, INK, 1)
    cv.vline(x, y, y + h - 1, INK, 1)
    cv.vline(x + w - 1, y, y + h - 1, INK, 1)
    cv.vtext(x + 4, y + 2, s, em, INK, 1.3)
    return w


def caption_strip(cv, x, y, w, s, em=9):
    cv.fill_rect(x, y, w, em + 4, NAVY)
    cv.vtext(x + 4, y + 2, s, em, PAPER, 1.2)


def pic_kyiv(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (16, 26, 54), (38, 58, 96))
    mx, my = ox + int(w * 0.88), oy + int(h * 0.20)
    cv.fill_circle(mx, my, 9, (210, 210, 190))
    cv.fill_circle(mx, my, 6, (240, 238, 220))
    cv.fill_circle(mx - 2, my - 2, 2, (200, 200, 185))
    for sx, sy in ((0.06, 0.12), (0.14, 0.07), (0.24, 0.18), (0.33, 0.08),
                   (0.44, 0.14), (0.55, 0.07), (0.66, 0.16), (0.76, 0.06),
                   (0.05, 0.30), (0.20, 0.28), (0.38, 0.26), (0.60, 0.28),
                   (0.82, 0.30), (0.94, 0.10), (0.48, 0.20), (0.70, 0.24)):
        px, py = ox + int(w * sx), oy + int(h * sy)
        cv.fill_rect(px, py, 2, 2, PAPER)
        if (int(sx * 100) + int(sy * 100)) % 3 == 0:
            cv.hline(px - 2, px + 3, py, PAPER, 1)
            cv.vline(px, py - 2, py + 3, PAPER, 1)
    base = oy + int(h * 0.58)
    bx = ox + 4
    bi = 0
    while bx < ox + w - 8:
        bw = 14 + (bi * 7) % 18
        bh = 12 + (bi * 11) % 22
        cv.fill_rect(bx, base - bh, bw, bh, (10, 16, 34))
        cv.hline(bx, bx + bw - 1, base - bh, (90, 100, 130), 1)
        for wy in range(base - bh + 3, base - 2, 5):
            for wx in range(bx + 3, bx + bw - 3, 5):
                if (wx * 3 + wy * 7 + bi) % 5 < 2:
                    cv.fill_rect(wx, wy, 2, 2, (255, 205, 90))
        bx += bw + 3
        bi += 1
    for (tx0, tx1) in ((0.98, 0.62), (0.80, 0.45), (0.62, 0.30)):
        dashed(cv, ox + int(w * tx0), oy + 2,
               ox + int(w * tx1), oy + int(h * 0.55), PAPER)
        cv.fill_circle(ox + int(w * tx0) - 6, oy + 8, 2, YELLOW)
    dy = base
    cv.hline(ox + 6, ox + w - 7, dy, (170, 170, 170), 4)
    cv.hline(ox + 6, ox + w - 7, dy + 4, (110, 110, 110), 1)
    cv.line(ox + int(w * 0.15), dy + 4, ox + w // 2, dy + 14,
            (150, 150, 150), 3)
    cv.line(ox + w // 2, dy + 14, ox + int(w * 0.85), dy + 4,
            (150, 150, 150), 3)
    for fx in (0.12, 0.28, 0.50, 0.72, 0.88):
        cv.vline(ox + int(w * fx), dy + 4, oy + int(h * 0.82),
                 (140, 140, 140), 3)
    for bfx, bc in ((0.30, YELLOW), (0.66, RED), (0.84, YELLOW)):
        px, py = ox + int(w * bfx), dy - 6
        cv.fill_circle(px, py, 12, (200, 90, 20))
        cv.fill_circle(px, py, 8, (240, 140, 40))
        cv.star(px, py, 9, bc, 2)
        cv.fill_circle(px, py, 3, PAPER)
        cv.fill_circle(px - 8, py - 12, 4, (120, 120, 120))
        cv.fill_circle(px + 6, py - 14, 5, (100, 100, 100))
        cv.vline(px, oy + int(h * 0.86), oy + h - 4, (240, 160, 60), 2)
    wy = oy + int(h * 0.84)
    grad_v(cv, ox, wy, w, h - int(h * 0.84), (46, 78, 130), (24, 48, 92))
    for wx in range(ox + 6, ox + w - 10, 14):
        cv.line(wx, wy + 5, wx + 7, wy + 2, (180, 200, 230), 1)
        cv.line(wx + 7, wy + 2, wx + 14, wy + 5, (180, 200, 230), 1)


def pic_cyclone(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (86, 132, 190), (52, 96, 158))
    for wy in range(oy + 8, oy + h - 6, 12):
        for wx in range(ox + 4, ox + int(w * 0.80), 18):
            if (wx + wy) % 36 < 18:
                cv.hline(wx, wx + 8, wy, (150, 190, 230), 1)
    for cx0, cy0, r0 in ((0.10, 0.10, 7), (0.16, 0.08, 9), (0.22, 0.11, 6),
                         (0.70, 0.09, 6), (0.76, 0.12, 8)):
        cv.fill_circle(ox + int(w * cx0), oy + int(h * cy0), r0,
                       (225, 232, 240))
    cx, cy = ox + int(w * 0.42), oy + int(h * 0.52)
    for i, r in enumerate((5, 10, 15, 20, 25, 30, 35)):
        cv.circle(cx - i * 2, cy - i, r, PAPER, 2)
        cv.circle(cx - i * 2, cy - i, r - 1, (190, 210, 235), 1)
    cv.fill_circle(cx, cy, 5, (240, 240, 235))
    cv.circle(cx, cy, 8, RED, 2)
    for k in range(12):
        a = 2 * math.pi * k / 12
        x0 = cx + int(10 * math.cos(a))
        y0 = cy + int(10 * math.sin(a))
        x1 = cx + int(34 * math.cos(a + 0.5))
        y1 = cy + int(34 * math.sin(a + 0.5))
        cv.line(x0, y0, x1, y1, (200, 220, 240), 1)
    for rx, ry in ((0.05, 0.15), (0.11, 0.32), (0.03, 0.52), (0.09, 0.72),
                   (0.14, 0.88), (0.60, 0.82), (0.66, 0.68), (0.58, 0.20)):
        cv.line(ox + int(w * rx), oy + int(h * ry),
                ox + int(w * rx) + 7, oy + int(h * ry) + 9, PAPER, 2)
    lx0 = ox + int(w * 0.82)
    grad_v(cv, lx0, oy, w - int(w * 0.82), h, (214, 196, 152), (186, 166, 122))
    cv.line(lx0, oy, lx0 + 6, oy + h // 3, (120, 100, 60), 2)
    cv.line(lx0 + 6, oy + h // 3, lx0 - 2, oy + 2 * h // 3, (120, 100, 60), 2)
    cv.line(lx0 - 2, oy + 2 * h // 3, lx0 + 4, oy + h, (120, 100, 60), 2)
    for tx, ty in ((0.87, 0.20), (0.90, 0.38), (0.86, 0.60), (0.92, 0.78)):
        cv.fill_rect(ox + int(w * tx), oy + int(h * ty), 3, 3, (90, 70, 40))
    lx, ly = ox + int(w * 0.80), oy + int(h * 0.45)
    dashed(cv, cx + 30, cy, lx - 4, ly, RED)
    cv.fill_circle(lx, ly, 5, RED)
    cv.circle(lx, ly, 9, PAPER, 2)
    cv.circle(lx, ly, 12, RED, 1)
    cv.line(lx - 16, ly + 14, lx - 6, ly + 14, PAPER, 2)
    cv.fill_poly([(lx - 6, ly + 14), (lx - 12, ly + 10),
                  (lx - 12, ly + 18)], PAPER)


def pic_selloff(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (30, 48, 84), (16, 28, 58))
    for gy in range(oy + 10, oy + h - 8, 14):
        cv.hline(ox + 4, ox + int(w * 0.52), gy, (60, 80, 120), 1)
    for gx in range(ox + 8, ox + int(w * 0.52), 16):
        cv.vline(gx, oy + 6, oy + int(h * 0.82), (60, 80, 120), 1)
    bw = int(w * 0.055)
    bx0 = ox + int(w * 0.05)
    tops = (0.18, 0.24, 0.32, 0.40, 0.48, 0.56)
    bots = (0.42, 0.50, 0.55, 0.62, 0.68, 0.74)
    for i, (t0, b0) in enumerate(zip(tops, bots)):
        x = bx0 + i * (bw + 5)
        cv.vline(x + bw // 2, oy + int(h * t0) - 4, oy + int(h * b0) + 4,
                 (200, 200, 200), 1)
        cv.fill_rect(x, oy + int(h * t0), bw, int(h * (b0 - t0)),
                     (214, 48, 48) if i % 2 == 0 else (220, 90, 70))
    x0, y0 = ox + int(w * 0.05), oy + int(h * 0.12)
    x1, y1 = ox + int(w * 0.50), oy + int(h * 0.72)
    for yy in range(y0, y1):
        xx = x0 + (yy - y0) * (x1 - x0) // max(1, y1 - y0)
        cv.vline(xx, yy, oy + int(h * 0.80), (120, 30, 30), 1)
    cv.line(x0, y0, x1, y1, RED, 3)
    cv.line(x0, y0, x1, y1, (255, 120, 120), 1)
    cv.fill_poly([(x1, y1), (x1 - 12, y1 - 2), (x1 - 2, y1 - 12)], RED)
    # Right side: three falling red bars only, no index labels -- the
    # old labels hard-coded Friday 20 Nov closes (S&P -3.7%,
    # NASDAQ -5.28%), which do not belong in a 22 Nov picture, and at
    # em 9 the text ran past the right edge of the 46 px box while
    # rows 4-5 spilled below it onto the headline and body.
    nx = ox + int(w * 0.55)
    for i, v in enumerate((37, 53, 51)):
        yy = oy + 8 + i * 12
        cv.fill_rect(nx, yy + 2, v // 2, 5, RED)
        cv.fill_rect(nx, yy + 2, v // 4, 5, (255, 120, 120))
        cv.fill_poly([(nx + v // 2 + 4, yy + 2), (nx + v // 2, yy + 2),
                      (nx + v // 2 + 2, yy + 7)], RED)


def pic_riyadh(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (18, 24, 52), (44, 52, 88))
    mx, my = ox + int(w * 0.12), oy + int(h * 0.14)
    cv.fill_circle(mx, my, 8, (225, 225, 205))
    cv.fill_circle(mx, my, 5, (245, 244, 228))
    for sx, sy in ((0.30, 0.08), (0.45, 0.14), (0.62, 0.07), (0.80, 0.12),
                   (0.92, 0.20), (0.22, 0.22), (0.55, 0.20)):
        cv.fill_rect(ox + int(w * sx), oy + int(h * sy), 2, 2, PAPER)
    base = oy + int(h * 0.72)
    # skyline: low blocks with lit windows + Kingdom Centre tower
    bx = ox + 4
    bi = 0
    while bx < ox + w - 10:
        bw = 12 + (bi * 5) % 14
        bh = 10 + (bi * 9) % 18
        cv.fill_rect(bx, base - bh, bw, bh, (10, 14, 30))
        for wy in range(base - bh + 3, base - 2, 5):
            for wx in range(bx + 3, bx + bw - 3, 5):
                if (wx * 3 + wy * 7 + bi) % 4 < 2:
                    cv.fill_rect(wx, wy, 2, 2, (255, 205, 90))
        bx += bw + 3
        bi += 1
    # Kingdom Centre tower: tall slab with arched opening near the top
    tx = ox + int(w * 0.62)
    tw = 26
    cv.fill_rect(tx, oy + int(h * 0.06), tw, base - oy - int(h * 0.06),
                 (14, 20, 40))
    cv.hline(tx, tx + tw - 1, oy + int(h * 0.06), (120, 130, 160), 1)
    cv.fill_poly([(tx + 4, oy + int(h * 0.10)),
                  (tx + tw - 4, oy + int(h * 0.10)),
                  (tx + tw // 2, oy + int(h * 0.30))], (18, 24, 52))
    for wy in range(oy + int(h * 0.34), base - 4, 6):
        cv.fill_rect(tx + 4, wy, 3, 3, (255, 205, 90))
        cv.fill_rect(tx + tw - 7, wy, 3, 3, (255, 205, 90))
    # interceptor trails rising + bursts
    for (ix0, ix1) in ((0.18, 0.34), (0.42, 0.55), (0.78, 0.88)):
        dashed(cv, ox + int(w * ix0), oy + h - 14,
               ox + int(w * ix1), oy + int(h * 0.30), PAPER)
    for bfx, bfy in ((0.34, 0.30), (0.55, 0.26), (0.88, 0.32)):
        px, py = ox + int(w * bfx), oy + int(h * bfy)
        cv.fill_circle(px, py, 10, (200, 90, 20))
        cv.fill_circle(px, py, 6, (240, 140, 40))
        cv.star(px, py, 8, YELLOW, 2)
        cv.fill_circle(px, py, 2, PAPER)
    cv.hline(ox, ox + w - 1, base, (90, 90, 110), 2)
    for wx in range(ox + 6, ox + w - 10, 16):
        cv.fill_rect(wx, base + 5, 8, 2, (255, 205, 90))


def pic_flags(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (242, 236, 220), (228, 220, 200))
    stipple(cv, ox, oy, w, h, (200, 192, 170), seed=11, density=1)
    ex, ey, ew, eh = ox + int(w * 0.06), oy + int(h * 0.18), \
        int(w * 0.40), int(h * 0.62)
    cv.vline(ex - 3, ey - 4, ey + eh + 4, INK, 2)
    cv.fill_circle(ex - 2, ey - 5, 2, YELLOW)
    ux, uy, uw, uh = ox + int(w * 0.54), oy + int(h * 0.18), \
        int(w * 0.40), int(h * 0.62)
    cv.vline(ux - 3, uy - 4, uy + uh + 4, INK, 2)
    cv.fill_circle(ux - 2, uy - 5, 2, YELLOW)
    cv.fill_rect(ex, ey + eh + 1, ew, 3, (180, 172, 150))
    cv.fill_rect(ux, uy + uh + 1, uw, 3, (180, 172, 150))
    grad_v(cv, ex, ey, ew, eh, (40, 84, 180), (24, 58, 140))
    ecx, ecy = ex + ew // 2, ey + eh // 2
    for k in range(12):
        a = 2 * math.pi * k / 12 - math.pi / 2
        px = int(ecx + (eh * 0.30) * math.cos(a))
        py = int(ecy + (eh * 0.30) * math.sin(a))
        cv.fill_circle(px, py, 2, YELLOW)
        cv.hline(px - 3, px + 3, py, YELLOW, 1)
        cv.vline(px, py - 3, py + 3, YELLOW, 1)
    grad_v(cv, ux, uy, uw, uh, (40, 84, 180), (24, 58, 140))
    cv.line(ux, uy, ux + uw, uy + uh, PAPER, 4)
    cv.line(ux + uw, uy, ux, uy + uh, PAPER, 4)
    cv.line(ux, uy, ux + uw, uy + uh, RED, 2)
    cv.line(ux + uw, uy, ux, uy + uh, RED, 2)
    cv.fill_rect(ux + uw // 2 - 5, uy, 10, uh, PAPER)
    cv.fill_rect(ux, uy + uh // 2 - 5, uw, 10, PAPER)
    cv.fill_rect(ux + uw // 2 - 2, uy, 4, uh, RED)
    cv.fill_rect(ux, uy + uh // 2 - 2, uw, 4, RED)


def pic_globe(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (242, 236, 220), (226, 218, 198))
    stipple(cv, ox, oy, w, h, (200, 192, 170), seed=23, density=1)
    cx, cy = ox + w // 2, oy + int(h * 0.48)
    r = int(h * 0.30)
    cv.fill_circle(cx, cy, r, (120, 170, 215))
    cv.fill_circle(cx - 6, cy - 8, 7, (90, 160, 100))
    cv.fill_circle(cx + 8, cy + 2, 6, (90, 160, 100))
    cv.fill_circle(cx - 2, cy + 10, 5, (110, 170, 110))
    cv.fill_circle(cx + 10, cy - 10, 4, (90, 160, 100))
    cv.circle(cx, cy, r, INK, 2)
    cv.vline(cx, cy - r, cy + r, INK, 1)
    cv.hline(cx - r, cx + r, cy, INK, 1)
    cv.line(cx - int(r * 0.7), cy - int(r * 0.7),
            cx - int(r * 0.7), cy + int(r * 0.7), INK, 1)
    cv.line(cx + int(r * 0.7), cy - int(r * 0.7),
            cx + int(r * 0.7), cy + int(r * 0.7), INK, 1)
    cv.hline(cx - int(r * 0.85), cx + int(r * 0.85),
             cy - int(r * 0.55), INK, 1)
    cv.hline(cx - int(r * 0.85), cx + int(r * 0.85),
             cy + int(r * 0.55), INK, 1)
    cv.line(cx - r - 4, cy + r + 4, cx + r + 4, cy - r - 4, RED, 4)
    cv.line(cx - r - 2, cy + r + 2, cx + r + 2, cy - r - 2,
            (255, 130, 130), 1)
    cv.fill_circle(cx + r - 2, cy - r + 2, 6, RED)
    cv.vtext(cx + r - 5, cy - r - 2, "X", 9, PAPER, 1.2)


def pic_hack(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (20, 26, 40), (34, 44, 66))
    # server racks with blinking lights
    for i in range(3):
        rx = ox + int(w * (0.06 + i * 0.24))
        rw = int(w * 0.18)
        cv.fill_rect(rx, oy + int(h * 0.12), rw, int(h * 0.76), (12, 14, 22))
        cv.hline(rx, rx + rw - 1, oy + int(h * 0.12), (90, 100, 130), 1)
        for sy in range(oy + int(h * 0.18), oy + int(h * 0.84), 7):
            cv.fill_rect(rx + 3, sy, rw - 6, 2, (60, 70, 95))
            cv.fill_rect(rx + rw - 6, sy, 3, 3,
                         RED if (sy // 7 + i) % 3 == 0 else (80, 200, 120))
    # red padlock + warning triangle
    lx, ly = ox + int(w * 0.80), oy + int(h * 0.42)
    cv.circle(lx, ly - 8, 8, RED, 3)
    cv.fill_rect(lx - 12, ly - 2, 24, 18, RED)
    cv.fill_rect(lx - 2, ly + 4, 4, 8, PAPER)
    cv.fill_circle(lx, ly + 3, 2, PAPER)
    cv.fill_poly([(ox + int(w * 0.06), oy + int(h * 0.88)),
                  (ox + int(w * 0.20), oy + int(h * 0.88)),
                  (ox + int(w * 0.13), oy + int(h * 0.70))], YELLOW)
    cv.vtext(ox + int(w * 0.115), oy + int(h * 0.78), "!", 10, INK, 1.3)
    # breach dashes across the racks
    for dx in range(ox + 4, ox + w - 8, 10):
        if (dx // 10) % 2 == 0:
            cv.hline(dx, dx + 5, oy + int(h * 0.52), (255, 120, 120), 1)


def pic_quake(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (235, 228, 210), (210, 200, 175))
    # Andes peaks
    cv.fill_poly([(ox, oy + h), (ox + int(w * 0.28), oy + int(h * 0.18)),
                  (ox + int(w * 0.52), oy + h)], (120, 130, 140))
    cv.fill_poly([(ox + int(w * 0.30), oy + h),
                  (ox + int(w * 0.62), oy + int(h * 0.08)),
                  (ox + w, oy + h)], (100, 112, 124))
    cv.fill_poly([(ox + int(w * 0.24), oy + int(h * 0.26)),
                  (ox + int(w * 0.32), oy + int(h * 0.18)),
                  (ox + int(w * 0.28), oy + int(h * 0.30))], PAPER)
    cv.fill_poly([(ox + int(w * 0.58), oy + int(h * 0.16)),
                  (ox + int(w * 0.66), oy + int(h * 0.08)),
                  (ox + int(w * 0.62), oy + int(h * 0.20))], PAPER)
    # ground + jagged cracks
    gy = oy + int(h * 0.72)
    cv.fill_rect(ox, gy, w, h - int(h * 0.72), (150, 135, 105))
    cv.hline(ox, ox + w - 1, gy, INK, 2)
    cx = ox + int(w * 0.20)
    for dx, dy in ((0, 0), (8, 5), (4, 10), (12, 15), (6, 20)):
        cv.line(cx + dx, gy + dy, cx + dx + 6, gy + dy + 4, INK, 2)
    # shaking house: tilted block + roof + dust
    hx, hy = ox + int(w * 0.58), oy + int(h * 0.52)
    cv.fill_poly([(hx, hy), (hx + 34, hy - 6), (hx + 34, hy + 14),
                  (hx, hy + 20)], (90, 70, 50))
    cv.fill_poly([(hx - 4, hy), (hx + 17, hy - 14), (hx + 38, hy - 6),
                  (hx + 17, hy + 2)], INK)
    cv.fill_rect(hx + 6, hy + 4, 5, 6, PAPER)
    cv.fill_rect(hx + 20, hy + 2, 5, 6, PAPER)
    for dx, dy in ((-6, -8), (40, -12), (30, 6), (-2, 4)):
        cv.fill_circle(hx + dx, hy + dy, 3, (180, 170, 150))
    # magnitude at top RIGHT: the tag covers the top-left corner
    cv.vtext(ox + w - 34, oy + 4, "6.7", 11, RED, 1.3)


def pic_seaquake(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (150, 190, 220), (60, 110, 165))
    for cx0, cy0, r0 in ((0.14, 0.12, 6), (0.22, 0.09, 8), (0.70, 0.08, 6)):
        cv.fill_circle(ox + int(w * cx0), oy + int(h * cy0), r0, PAPER)
    # epicentre rings on the water (r=30 ring bled 7 px below the pic
    # box at small size, so the rings stop at 24 and sit lower)
    cx, cy = ox + int(w * 0.42), oy + int(h * 0.52)
    for r in (6, 12, 18, 24):
        cv.circle(cx, cy, r, PAPER, 2)
    cv.fill_circle(cx, cy, 4, RED)
    cv.star(cx, cy, 6, RED, 2)
    # wave lines + small island
    for wy in range(oy + int(h * 0.30), oy + h - 4, 10):
        for wx in range(ox + 4, ox + w - 10, 18):
            if (wx + wy) % 36 < 18:
                cv.hline(wx, wx + 8, wy, (200, 225, 245), 1)
    ix = ox + int(w * 0.80)
    cv.fill_poly([(ix - 14, oy + int(h * 0.82)), (ix + 14, oy + int(h * 0.82)),
                  (ix + 6, oy + int(h * 0.66)),
                  (ix - 6, oy + int(h * 0.66))], LAND)
    cv.fill_circle(ix, oy + int(h * 0.60), 5, GREEN)
    # magnitude at top RIGHT: the tag covers the top-left corner
    cv.vtext(ox + w - 34, oy + 4, "6.8", 11, RED, 1.3)


def pic_mercury(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (12, 14, 26), (30, 32, 52))
    for sx, sy in ((0.06, 0.10), (0.16, 0.06), (0.30, 0.14), (0.48, 0.08),
                   (0.66, 0.12), (0.80, 0.06), (0.90, 0.18), (0.10, 0.30),
                   (0.88, 0.32), (0.55, 0.22)):
        cv.fill_rect(ox + int(w * sx), oy + int(h * sy), 2, 2, PAPER)
    # Mercury: grey cratered disc + orbit ellipse
    cx, cy = ox + int(w * 0.38), oy + int(h * 0.55)
    r = int(h * 0.32)
    cv.fill_circle(cx, cy, r, (150, 140, 130))
    cv.fill_circle(cx - 6, cy - 8, 5, (120, 112, 104))
    cv.fill_circle(cx + 8, cy + 4, 4, (120, 112, 104))
    cv.fill_circle(cx - 2, cy + 10, 3, (125, 116, 108))
    cv.fill_circle(cx + 10, cy - 10, 3, (120, 112, 104))
    cv.fill_circle(cx - 12, cy + 2, 2, (125, 116, 108))
    cv.circle(cx, cy, r, (200, 195, 185), 1)
    # orbit ellipse (dashed) + spacecraft: body, panels, dish
    for k in range(24):
        a = 2 * math.pi * k / 24
        px = cx + int(52 * math.cos(a))
        py = cy + int(20 * math.sin(a))
        if k % 2 == 0:
            cv.fill_rect(px, py, 2, 2, PAPER)
    sx, sy = ox + int(w * 0.78), oy + int(h * 0.22)
    cv.fill_rect(sx - 8, sy - 5, 16, 10, (200, 200, 205))
    cv.fill_rect(sx - 22, sy - 3, 12, 6, (40, 90, 160))
    cv.fill_rect(sx + 10, sy - 3, 12, 6, (40, 90, 160))
    cv.line(sx, sy - 5, sx + 6, sy - 12, PAPER, 1)
    cv.fill_circle(sx + 7, sy - 13, 3, PAPER)
    cv.line(sx - 8, sy + 5, sx - 12, sy + 10, (255, 180, 80), 2)


def pic_summit(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (242, 236, 220), (226, 218, 198))
    stipple(cv, ox, oy, w, h, (200, 192, 170), seed=53, density=1)
    # three flags on poles behind a table
    for i, (fx, cols) in enumerate((
            (0.18, [(RED, 0.14), (PAPER, 0.14), (BLUE, 0.14)]),
            (0.50, [(RED, 0.42)]),
            (0.80, [(BLUE, 0.42)]))):
        px = ox + int(w * fx)
        cv.vline(px, oy + int(h * 0.10), oy + int(h * 0.62), INK, 2)
        cv.fill_circle(px, oy + int(h * 0.09), 2, YELLOW)
        fy = oy + int(h * 0.12)
        fh = int(h * 0.30)
        fw = int(w * 0.16)
        y = fy
        for col, frac in cols:
            cv.fill_rect(px + 2, y, fw, int(fh * frac), col)
            y += int(fh * frac)
        if i == 0:  # stars canton on the first flag
            for kx in range(3):
                for ky in range(2):
                    cv.fill_rect(px + 4 + kx * 5, fy + 2 + ky * 5, 2, 2,
                                 PAPER)
        if i == 1:  # star on the red flag
            cv.star(px + 2 + fw // 2, fy + fh // 2, 5, YELLOW, 1)
    # table + microphones + name cards
    ty = oy + int(h * 0.62)
    cv.fill_rect(ox + int(w * 0.06), ty, int(w * 0.88), 6, (90, 60, 35))
    cv.fill_rect(ox + int(w * 0.10), ty + 6, 4, oy + h - ty - 6, INK)
    cv.fill_rect(ox + int(w * 0.86), ty + 6, 4, oy + h - ty - 6, INK)
    for mx0 in (0.30, 0.50, 0.70):
        mx = ox + int(w * mx0)
        cv.line(mx, ty, mx + 4, ty - 12, INK, 2)
        cv.fill_circle(mx + 4, ty - 13, 3, INK)
        cv.fill_rect(mx - 8, ty - 22, 16, 7, PAPER)
        cv.hline(mx - 8, mx + 7, ty - 22, INK, 1)
        cv.hline(mx - 8, mx + 7, ty - 15, INK, 1)


def pic_fire(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (60, 60, 70), (35, 35, 45))
    # cooling tower + chimneys
    tx = ox + int(w * 0.14)
    cv.fill_poly([(tx, oy + h), (tx + 8, oy + int(h * 0.18)),
                  (tx + 30, oy + int(h * 0.18)), (tx + 38, oy + h)],
                 (140, 135, 125))
    cv.hline(tx + 8, tx + 30, oy + int(h * 0.18), (90, 85, 75), 2)
    for cx0 in (0.55, 0.68, 0.81):
        cxp = ox + int(w * cx0)
        # HEIGHT is h - 0.30h, not oy + h - 0.30h: the old absolute
        # value made each chimney ~oy px too tall, painting a solid
        # grey bar down the whole page over the story text below.
        cv.fill_rect(cxp, oy + int(h * 0.30), 10, h - int(h * 0.30),
                     (110, 105, 95))
        cv.fill_rect(cxp - 1, oy + int(h * 0.28), 12, 3, INK)
    # flames licking the plant
    base = oy + int(h * 0.86)
    for fx, fh, col in ((0.30, 0.30, (230, 90, 30)),
                        (0.48, 0.42, (245, 140, 40)),
                        (0.66, 0.34, (230, 90, 30)),
                        (0.84, 0.26, (245, 160, 60))):
        px = ox + int(w * fx)
        ph = int(h * fh)
        cv.fill_poly([(px - 12, base), (px - 6, base - ph),
                      (px, base - ph - 8), (px + 6, base - ph),
                      (px + 12, base)], col)
        cv.fill_poly([(px - 5, base), (px - 2, base - ph + 6),
                      (px + 2, base - ph + 6), (px + 5, base)], YELLOW)
    # smoke + embers (the 0.14/r9 puff poked 1 px above the pic box)
    for sx0, sy0, r0 in ((0.48, 0.22, 7), (0.56, 0.18, 8), (0.66, 0.20, 6),
                         (0.36, 0.16, 5)):
        cv.fill_circle(ox + int(w * sx0), oy + int(h * sy0), r0,
                       (100, 100, 105))
    for ex0, ey0 in ((0.40, 0.55), (0.60, 0.45), (0.74, 0.60)):
        cv.fill_rect(ox + int(w * ex0), oy + int(h * ey0), 2, 2, YELLOW)
    cv.hline(ox, ox + w - 1, base, INK, 2)


def pic_aid(cv, ox, oy, w, h):
    # Gaza City street at night: aid van on a road, missile burst above.
    grad_v(cv, ox, oy, w, h, (42, 46, 72), (22, 24, 38))
    # buildings left and right, lit windows
    cv.fill_rect(ox, oy + int(h * 0.25), int(w * 0.16), int(h * 0.75),
                 (56, 56, 72))
    cv.fill_rect(ox + int(w * 0.84), oy + int(h * 0.18), int(w * 0.16),
                 int(h * 0.82), (50, 50, 66))
    for bx, by in ((0.03, 0.35), (0.08, 0.45), (0.88, 0.30), (0.93, 0.42)):
        cv.fill_rect(ox + int(w * bx), oy + int(h * by), 5, 6, YELLOW)
    # road + centre dashes
    cv.fill_rect(ox, oy + int(h * 0.78), w, int(h * 0.22), (72, 72, 78))
    cv.hline(ox, ox + w - 1, oy + int(h * 0.78), INK, 2)
    for dx in range(ox + 8, ox + w - 10, 26):
        cv.fill_rect(dx, oy + int(h * 0.88), 12, 2, PAPER)
    # white aid van
    vx, vy = ox + int(w * 0.34), oy + int(h * 0.52)
    vw, vh = int(w * 0.34), int(h * 0.26)
    cv.fill_rect(vx, vy, vw, vh, (226, 221, 206))
    cv.fill_rect(vx + 6, vy + 5, int(vw * 0.45), int(vh * 0.4),
                 (92, 122, 152))
    cv.fill_rect(vx + int(vw * 0.62), vy + 5, int(vw * 0.28),
                 int(vh * 0.4), (92, 122, 152))
    cv.fill_circle(vx + int(vw * 0.22), vy + vh, 6, INK)
    cv.fill_circle(vx + int(vw * 0.78), vy + vh, 6, INK)
    # missile burst above the van
    cv.star(ox + int(w * 0.51), oy + int(h * 0.36), 17, (245, 140, 40), 3)
    cv.fill_circle(ox + int(w * 0.51), oy + int(h * 0.36), 8,
                   (250, 200, 60))


def pic_plane(cv, ox, oy, w, h):
    grad_v(cv, ox, oy, w, h, (150, 190, 225), (205, 225, 240))
    for cx0, cy0, r0 in ((0.12, 0.14, 7), (0.20, 0.11, 9), (0.70, 0.10, 6),
                         (0.78, 0.14, 8), (0.45, 0.06, 5)):
        cv.fill_circle(ox + int(w * cx0), oy + int(h * cy0), r0, PAPER)
    # runway + terminal block
    ry = oy + int(h * 0.78)
    cv.fill_rect(ox, ry, w, h - int(h * 0.78), (120, 120, 125))
    cv.hline(ox, ox + w - 1, ry, INK, 2)
    for dx in range(ox + 6, ox + w - 8, 18):
        cv.fill_rect(dx, ry + 5, 10, 2, PAPER)
    cv.fill_rect(ox + int(w * 0.06), ry - 14, int(w * 0.22), 14,
                 (150, 145, 135))
    for wx in range(ox + int(w * 0.08), ox + int(w * 0.26), 8):
        cv.fill_rect(wx, ry - 10, 4, 4, (60, 70, 90))
    # plane taking off: fuselage, nose, tail, wings, engines
    px, py = ox + int(w * 0.52), oy + int(h * 0.48)
    cv.fill_poly([(px - 34, py), (px + 26, py - 6), (px + 38, py - 2),
                  (px + 30, py + 4), (px - 30, py + 6)], (30, 40, 60))
    cv.fill_poly([(px + 26, py - 6), (px + 38, py - 2), (px + 34, py + 2),
                  (px + 24, py - 2)], (200, 210, 225))
    cv.fill_poly([(px - 26, py - 2), (px - 34, py - 16), (px - 28, py - 16),
                  (px - 18, py - 3)], (30, 40, 60))
    cv.fill_poly([(px - 6, py - 2), (px + 2, py + 14), (px + 8, py + 14),
                  (px + 6, py - 1)], (30, 40, 60))
    cv.fill_poly([(px - 2, py + 4), (px + 10, py + 18), (px + 16, py + 18),
                  (px + 10, py + 3)], (30, 40, 60))
    cv.fill_circle(px + 4, py + 6, 3, (60, 70, 85))
    cv.fill_circle(px + 14, py + 5, 3, (60, 70, 85))
    # climb trail
    dashed(cv, px - 34, py + 8, ox + int(w * 0.10), oy + int(h * 0.72),
           (90, 90, 100))

# ------------------------------------------------------------------- map ----
MAP_SPANS = {
    1: [(3, 10), (17, 20), (32, 46)],
    2: [(2, 11), (17, 21), (24, 27), (31, 46)],
    3: [(2, 12), (23, 27), (30, 46)],
    4: [(2, 11), (24, 26), (30, 45)],
    5: [(3, 10), (24, 26), (31, 44)],
    6: [(4, 9), (25, 30), (32, 42)],
    7: [(5, 8), (24, 31), (33, 40)],
    8: [(6, 8), (25, 31), (35, 38)],
    9: [(7, 8), (26, 30), (36, 37)],
    10: [(8, 9), (10, 14), (27, 30)],
    11: [(10, 15), (27, 29)],
    12: [(11, 15), (28, 29)],
    13: [(12, 14), (28, 28), (39, 44)],
    14: [(12, 14), (38, 44)],
    15: [(13, 14), (39, 43)],
    16: [(13, 13)],
}
# story number -> (map col, map row, pin dx, pin dy)
# 8 (global markets) is off the map, noted below.
# Pins are big red discs with the white number inside (rank-50 style);
# each pin sits on a short leader from the true dot, because the
# Europe / Middle East dots cluster too tightly for pins on the dot.
# Offsets retuned for the v9 7x11 cells: the five Europe/Middle East
# dots (1, 4, 5, 11, 2) fan out left / right / down, since there is
# no room above row 1; 11 fans down-left clear of 1's dot.
MAP_DOTS = [
    (1, 28, 5, 24, -4), (2, 31, 7, 22, 10), (3, 38, 11, 20, -6),
    (4, 27, 4, -28, -8), (5, 29, 4, 26, -10), (6, 41, 6, 18, -8),
    (7, 13, 5, -24, 4), (9, 24, 4, -28, 6), (10, 34, 7, 20, 8),
    (11, 29, 6, -26, 14), (12, 28, 13, 20, 4), (13, 26, 5, -26, -8),
]

def draw_map(cv, ox, oy, cell_w=7, cell_h=11):
    # Side-by-side map (v9): 48 cols x 16 rows at near-square cells,
    # 336x176 -- a real world-map aspect instead of the v8 9.5:1 strip.
    # Ocean is distinctly blue against PAPER so it reads as ocean.
    cv.fill_rect(ox, oy, 48 * cell_w, 16 * cell_h, (178, 212, 238))
    for gx in range(0, 48, 6):
        cv.vline(ox + gx * cell_w, oy, oy + 16 * cell_h, (158, 188, 214), 1)
    for gy in range(0, 16, 6):
        cv.hline(ox, ox + 48 * cell_w, oy + gy * cell_h, (158, 188, 214), 1)
    for row, spans in MAP_SPANS.items():
        r = row - 1  # crop empty row 0
        for c0, c1 in spans:
            for c in range(c0, c1 + 1):
                cv.fill_rect(ox + c * cell_w, oy + r * cell_h,
                             cell_w, cell_h, LAND)
                if (c * 7 + row * 3) % 4 == 0:
                    cv.set(ox + c * cell_w + 1, oy + r * cell_h + 1,
                           (170, 152, 112))
    cv.hline(ox, ox + 48 * cell_w - 1, oy + 8 * cell_h, (140, 160, 180), 1)
    for num, col, row, dx, dy in MAP_DOTS:
        px = ox + col * cell_w + cell_w // 2
        py = oy + (row - 1) * cell_h + cell_h // 2
        qx, qy = px + dx, py + dy
        cv.line(px, py, qx, qy, RED, 1)
        cv.fill_circle(px, py, 4, PAPER)
        cv.fill_circle(px, py, 3, RED)
        cv.fill_circle(qx, qy, 8, RED)
        s = str(num)
        sw = cv.vtext_width(s, 8, 1.3)
        cv.vtext(qx - sw // 2, qy - 3, s, 8, PAPER, 1.3)

# -------------------------------------------------------------- layout ----
MARGIN = 36
RIGHT = W - MARGIN  # 988

# Verification tags: CONFIRMED = 2+ outlets; OFFICIAL = on the record
# (IMD, CERN, UKMTO, government); REPORTED = one outlet;
# CLAIM = one side's account. Shown in each story's caption strip
# (leads/featured) or at the end of the line (ALSO), with the source.
LEGEND = ("HOW WE CHECKED - CONFIRMED = 2+ OUTLETS · OFFICIAL = ON THE "
          "RECORD · REPORTED = ONE OUTLET · CLAIM = ONE SIDE'S ACCOUNT")

STATS = [
    ("2", "INJURED IN THE", "BAHRAIN STRIKE"),
    ("36", "MISSING AFTER THE", "CIKANDE FACTORY FIRE"),
    ("14", "MISSING AFTER THE", "KYIV DRONE STRIKE"),
    ("186", "DRONES IN THE OVERNIGHT", "BARRAGE ON UKRAINE"),
    ("720", "INDIA DECLARES AT", "720 FOR 9 VS NEW ZEALAND"),
    ("15", "KM SWUM ACROSS THE", "STRAIT OF HORMUZ"),
]

REGIONS = [
    ("EUROPE", 10, (36, 64, 120)),
    ("ASIA", 8, RED),
    ("MIDDLE EAST", 6, (150, 100, 20)),
    ("AFRICA", 2, GREEN),
    ("AMERICAS", 7, (90, 60, 140)),
    ("OCEANIA", 1, (20, 120, 120)),
    ("GLOBAL", 1, (70, 70, 70)),
]

# Grounded times live in the story bodies only. No UTC timeline strip
# in this build (v7 dropped it; no precise 22 Nov clock times were
# verified -- only dates). Do not invent times.

TOP3 = [
    dict(pic=pic_summit, tag="COP31", tag2="NO DEAL",
         cap="CONFIRMED · REUTERS", w=304, pic_h=114, head_em=19,
         kicker="1 ANTALYA - CLIMATE",
         head="COP31 collapses with no deal",
         body="Antalya talks break down on Sunday after the EU "
              "rejects a fourth draft with no mention of fossil "
              "fuels. (Reuters)"),
    dict(pic=pic_riyadh, tag="BAHRAIN", tag2="MISSILES HIT SITRA",
         cap="CONFIRMED · REUTERS", w=304, pic_h=114, head_em=19,
         kicker="2 SITRA, BAHRAIN - STRIKE",
         head="Iran strikes Bahrain site",
         body="Bahrain says an Iranian strike on a civilian site "
              "in Sitra injured two, one critically; Gulf states "
              "condemn it. (Reuters)"),
    dict(pic=pic_fire, tag="CIKANDE FIRE", tag2="36 STILL MISSING",
         cap="CONFIRMED · AP", w=304, pic_h=114, head_em=19,
         kicker="3 CIKANDE, INDONESIA - FIRE",
         head="Factory fire kills three",
         body="Fire at a candy factory in Cikande leaves three "
              "dead and 36 missing as rescuers search the "
              "ruins. (AP)"),
]

MID5 = [
    dict(pic=pic_kyiv, tag="KYIV DRONE", cap="CONFIRMED · STRAITS TIMES",
         kicker="4 KYIV REGION - DRONE",
         head="Drone collapses Kyiv block",
         body="Five-storey block hit on Sunday; at least 14 missing. (Straits Times)"),
    dict(pic=pic_riyadh, tag="BARRAGE", cap="CONFIRMED · EUROMAIDAN PRESS",
         kicker="5 UKRAINE - BARRAGE",
         head="186 drones hit Ukraine",
         body="Overnight raid: 186 Shahed drones, 161 downed, strikes at 18 sites. (Euromaidan Press)"),
    dict(pic=pic_globe, tag="SEOUL", cap="REPORTED · BBC",
         kicker="6 SEOUL - RESIGNATION",
         head="Seoul minister quits",
         body="Education chief resigns over AI cheating scandal. (BBC)"),
    dict(pic=pic_hack, tag="NCIC BREACH", cap="CONFIRMED · CNN",
         kicker="7 WASHINGTON - FBI HACK",
         head="FBI probes NCIC breach",
         body="Apparent hack of police database; second in two months. (CNN)"),
    dict(pic=pic_selloff, tag="MARKETS", cap="REPORTED · REUTERS",
         kicker="8 GLOBAL - MARKETS",
         head="Tech shares stay down",
         body="Brent crude near $90 as Hormuz crisis bites. (Reuters)"),
]

BOT5 = [
    dict(pic=pic_flags, tag="PROTESTS", cap="REPORTED · FRANCE 24",
         kicker="9 PARIS - PROTESTS",
         head="Sixth weekend of protests",
         body="144 arrests in France; thousands march in Lisbon. (France 24)"),
    dict(pic=pic_summit, tag="STATE VISIT", cap="REPORTED · DAINIK JAGRAN",
         kicker="10 NEW DELHI - VISIT",
         head="Nepal PM visits India",
         body="Balendra Shah arrives for a two-day state visit. (Dainik Jagran)"),
    dict(pic=pic_aid, tag="GAZA OP", cap="REPORTED · BBC",
         kicker="11 GAZA - GROUND OP",
         head="Gaza ground op ends",
         body="Israeli military ends operation beyond Yellow Line. (BBC)"),
    dict(pic=pic_globe, tag="ANC CITIES", cap="REPORTED · BBC",
         kicker="12 S AFRICA - ELECTION",
         head="ANC fights for cities",
         body="Party battles to hold key cities after vote setback. (BBC)"),
    dict(pic=pic_aid, tag="HOSPITAL DEATH", cap="REPORTED · AL JAZEERA",
         kicker="13 CROATIA - HOSPITAL",
         head="Croatia hospital death",
         body="Outrage after psychiatric patient dies of alleged abuse. (Al Jazeera)"),
]

# 22 ALSO items (14-35). All 22 are verified Sun 22 Nov 2026 from
# the 22 Nov wires and briefings (BBC/Reuters/AP live briefings,
# France 24, Dainik Jagran, FT, USGS, CISA). Every item carries its
# source in parentheses plus its verification tag.
ALSO_LEFT = [
    "14 SAUDI ARABIA - HOUTHI FIRE ON SAUDI (HANSEN) - CLAIM",
    "15 TEHRAN - HORMUZ REOPENING NOT DIFFICULT (JAGRAN) - REPORTED",
    "16 SUDAN - ARMY ADVANCES AFTER DEFECTIONS (FT) - REPORTED",
    "17 MOSCOW - DISSIDENT CHEMIST UGLEV DIES AT 80 (HTT) - REPORTED",
    "18 GUATEMALA - WANTED MEXICAN ARRESTED (APPISTOS) - REPORTED",
    "19 BRASILIA - LULA FISCAL VOTE NEARS IN CHAMBER (SYNTHESIS) - REPORTED",
    "20 GENEVA - UN ROBOT TALKS EXTENDED TO 2028 (HANSEN) - REPORTED",
    "21 WASHINGTON - VCENTER FLAW EXPLOITED (CISA) - REPORTED",
    "22 RACKSPACE - SPOT BREACH EXPOSES SECRETS (APJ ONE) - REPORTED",
    "23 GEORGIA - MAN HELD OVER IS-LINKED TRANSFERS (SPEARNET) - REPORTED",
    "24 TEHRAN - NEIGHBOURHOOD SURVEILLANCE GROWS (SPEARNET) - REPORTED",
]

ALSO_RIGHT = [
    "25 HORMUZ - PUGH SWIMS 15 KM ACROSS STRAIT (ONE TURN) - REPORTED",
    "26 CALIFORNIA - KING TIDES, BIGGEST WAVES IN YEARS (GUARDIAN) - REPORTED",
    "27 WELLINGTON - INDIA DECLARE 720 FOR 9 VS NZ (JAGRAN) - REPORTED",
    "28 NEW DELHI - CHAHAL JOINS BJP, GETS OBC POST (JAGRAN) - REPORTED",
    "29 NEW DELHI - BJP MP WADKUTE DIES AT 72 (JAGRAN) - REPORTED",
    "30 ARUNACHAL - INDIA-CHINA TALKS END (JAGRAN) - REPORTED",
    "31 PARIS - FRANCE BEAT TURKEY, INTO QUARTERS (PULSE) - REPORTED",
    "32 PARIS - FRANCE RUGBY BEAT ARGENTINA (PULSE) - REPORTED",
    "33 FIJI - QUAKE 4.9 SOUTH OF FIJI ISLANDS (USGS) - REPORTED",
    "34 BEIJING - CHINA-JAPAN TIES WORSEN (GARDNER) - REPORTED",
    "35 MADRID - SPAIN HEADS FOR 29 NOV ELECTION (GARDNER) - REPORTED",
]

DATE_CHECK = ("DATE CHECK - LEFT OUT: EL CHAPO ISIDRO CAPTURE "
              "(RAID FRI 20 NOV, REPORTED SAT 21 NOV) · EU-INDONESIA "
              "CEPA SIGNED (SAT 21 NOV, BRUSSELS) · VENEZUELA-US "
              "MILITARY DEAL (SIGNED WED 18 NOV, REPORTED FRI 20 NOV) · "
              "NIGERIA BOAT CAPSIZE, 24 DEAD (NEMA STATEMENT SAT 21 NOV) · "
              "ICJ ROHINGYA GENOCIDE RULING (THU 19 NOV) · RIEMANN "
              "HYPOTHESIS CLAIM (FRI 20 NOV) · TRUMP CONTRACTOR ORDER "
              "(SIGNED FRI NIGHT, REPORTED SAT 21 NOV) · GERMANY 5-0 "
              "NETHERLANDS (FRI 20 NOV) · COP31 OVERTIME DRAG (SAT 21 NOV "
              "- THE COLLAPSE ITSELF IS SUN 22 NOV) · PERU QUAKE "
              "(SAT 21 NOV - IN NEWS21).")

FOOTER_1 = ("Every story here happened, or was first reported, on "
            "Sunday 22 November 2026.")
FOOTER_2 = ("Sources: BBC · Reuters · AP · Al Jazeera · AFP · The Guardian · "
            "CNN · France 24 · Euronews · Euromaidan Press · Dainik Jagran · Straits Times · "
            "FT · USGS · CISA · One Turn · Gardner - Original drawings")


def draw_list_col(cv, x, y, items, w=336, em=10, leading=12):
    y0 = y
    for i, s in enumerate(items):
        assert cv.vtext_width(s, em) <= w + 4, s
        if i % 2 == 0:
            cv.fill_rect(x - 3, y - 2, w + 6, leading - 1, (243, 238, 226))
        cv.hline(x - 3, x + w + 2, y + leading - 2, (214, 206, 188), 1)
        cv.fill_rect(x - 3, y - 2, 2, leading - 1,
                     RED if i % 2 == 0 else (200, 120, 120))
        cv.vtext(x, y, s, em, GRAY)
        cv.vtext(x, y, s.split(' ')[0], em, RED, 1.3)
        y += leading
    return y


def draw():
    cv = Canvas(W, H, PAPER)

    # page frame
    cv.hline(12, 1011, 12, INK, 2)
    cv.hline(12, 1011, 1010, INK, 2)
    cv.vline(12, 12, 1010, INK, 2)
    cv.vline(1011, 12, 1010, INK, 2)

    # ---- kicker: paper name left, story count right ----
    cv.vtext(MARGIN, 20, "THE WORLD IN ONE DAY", 12, RED, 1.4)
    cv.vtext_right(RIGHT, 21,
                   "35 STORIES · 7 REGIONS · EVERY ONE DATED SUNDAY "
                   "22 NOVEMBER 2026", 10, INK, 1.2)
    cv.hline(MARGIN, RIGHT, 34, INK, 1)

    # ---- masthead: the date itself, huge smooth serif (rank 1 style) ----
    cv.vtext_centred(W // 2, 38, "Sunday 22 November 2026", 62, INK, 1.45)
    cv.vtext_centred(W // 2, 104,
                     "COP31 collapses in Antalya · Iran strikes "
                     "Bahrain · Factory fire in Indonesia",
                     13, GRAY, 1.0, italic=True)
    cv.hline(MARGIN, RIGHT, 124, INK, 3)
    cv.hline(MARGIN, RIGHT, 129, INK, 1)

    # ---- THE DAY IN NUMBERS strip (big red numbers, top-entry style) ----
    cv.fill_rect(MARGIN, 134, 952, 62, (244, 239, 228))
    cv.hline(MARGIN, RIGHT, 134, RED, 1)
    cv.hline(MARGIN, RIGHT, 195, INK, 1)
    cv.vtext(MARGIN, 137, "THE DAY IN NUMBERS", 9, RED, 1.3)
    widths = []
    for num, l1, l2 in STATS:
        widths.append(max(cv.vtext_width(num, 26, 1.3),
                          cv.vtext_width(l1, 8), cv.vtext_width(l2, 8)) + 14)
    extra = 952 - sum(widths)
    widths = [w + extra // len(widths) for w in widths]
    widths[-1] += 952 - sum(widths)
    x = MARGIN
    for (num, l1, l2), wseg in zip(STATS, widths):
        if x > MARGIN:
            cv.vline(x - 7, 150, 191, RED, 2)
        cv.vtext(x, 148, num, 26, RED, 1.3)
        cv.vtext(x, 176, l1, 8, GRAY)
        cv.vtext(x, 184, l2, 8, GRAY)
        x += wseg

    # ---- region bar ----
    total = sum(c for _, c, _ in REGIONS)
    widths = [max(64, 952 * c // total) for _, c, _ in REGIONS]
    _widest = widths.index(max(widths))
    widths[_widest] -= sum(widths) - 952
    x = MARGIN
    for (name, count, col), wseg in zip(REGIONS, widths):
        cv.fill_rect(x, 200, wseg, 17, col)
        cv.vtext_centred(x + wseg // 2, 204, "%s %d" % (name, count), 10,
                         PAPER, 1.2)
        x += wseg

    # ---- top 3 stories (UTC timeline strip dropped in v7) ----
    cv.vtext(MARGIN, 224, "TOP STORIES", 11, RED, 1.4)
    cv.hline(MARGIN + 92, RIGHT, 227, RED, 1)
    top_x = [MARGIN, 360, 684]
    for (sx, story) in zip(top_x, TOP3):
        w = story['w']
        ph = story['pic_h']
        pic_box(cv, sx, 232, w, ph)
        story['pic'](cv, sx + 1, 233, w - 2, ph - 2)
        tag(cv, sx + 5, 237, story['tag'])
        tag_white(cv, sx + 5, 254, story['tag2'])
        caption_strip(cv, sx + 1, 232 + ph - 14, w - 2, story['cap'])
        cv.vtext(sx, 352, story['kicker'], 10, RED, 1.3)
        y = 364
        for line in cv.vwrap(story['head'], story['head_em'], w, 1.3):
            cv.vtext(sx, y, line, story['head_em'], INK, 1.3)
            y += story['head_em'] + 4
        y += 4
        for line in cv.vwrap(story['body'], 11, w, 1.0):
            cv.vtext(sx, y, line, 11, GRAY)
            y += 13
    cv.hline(MARGIN, RIGHT, 468, INK, 1)

    # ---- five-story rows (middle + bottom; v9: pics 56->48) ----
    def five_row(y0, stories):
        xs = [MARGIN, 229, 422, 615, 808]
        for sx, story in zip(xs, stories):
            pic_box(cv, sx, y0, 180, 48)
            story['pic'](cv, sx + 1, y0 + 1, 178, 46)
            tag(cv, sx + 5, y0 + 5, story['tag'], em=9)
            caption_strip(cv, sx + 1, y0 + 48 - 13, 178, story['cap'])
            cv.vtext(sx, y0 + 52, story['kicker'], 9, RED, 1.3)
            y = y0 + 63
            for line in cv.vwrap(story['head'], 12, 180, 1.25):
                cv.vtext(sx, y, line, 12, INK, 1.25)
                y += 13
            y += 2
            for line in cv.vwrap(story['body'], 10, 180, 1.0):
                cv.vtext(sx, y, line, 10, GRAY)
                y += 11

    cv.vtext(MARGIN, 474, "MORE FROM THE DAY", 11, RED, 1.4)
    cv.hline(MARGIN + 148, RIGHT, 477, RED, 1)
    five_row(484, MID5)
    five_row(600, BOT5)
    cv.hline(MARGIN, RIGHT, 719, INK, 1)

    # ---- map + also list (v9: map left at real world-map aspect,
    # ALSO in 2 columns right; rank-1 / rank-20 layout) ----
    cv.vtext(MARGIN, 725, "WHERE IT HAPPENED", 11, RED, 1.4)
    cv.vtext_right(RIGHT, 725,
                   "ALSO ON SUNDAY 22 NOVEMBER - 22 MORE STORIES",
                   11, INK, 1.3)
    pic_box(cv, MARGIN, 738, 352, 188)
    draw_map(cv, MARGIN + 8, 742)
    draw_list_col(cv, 400, 740, ALSO_LEFT, w=278, em=7, leading=15)
    draw_list_col(cv, 708, 740, ALSO_RIGHT, w=278, em=7, leading=15)
    _note = ("EACH NUMBER MATCHES A STORY ON THIS PAGE. "
             "8 IS GLOBAL MARKETS - OFF THE MAP.")
    cv.vtext(MARGIN, 928, _note, 8, GRAY)
    cv.vtext(MARGIN + cv.vtext_width(_note, 8) + 8, 928, LEGEND, 8, INK, 1.1)

    # ---- date check ----
    cv.fill_rect(MARGIN, 940, 952, 43, (253, 238, 232))
    hatch_diag(cv, MARGIN + 2, 942, 952 - 4, 39, (245, 228, 220), step=14)
    cv.hline(MARGIN, RIGHT, 940, RED, 2)
    cv.hline(MARGIN, RIGHT, 982, RED, 2)
    cv.vline(MARGIN, 940, 982, RED, 2)
    cv.vline(RIGHT, 940, 982, RED, 2)
    cv.vtext(MARGIN + 8, 943, "DATE CHECK", 9, RED, 1.3)
    y = 953
    for line in cv.vwrap(DATE_CHECK, 9, 920):
        cv.vtext(MARGIN + 8, y, line, 9, INK)
        y += 10

    # ---- footer (exact wording required) ----
    cv.vtext_centred(W // 2, 990, FOOTER_1, 9, GRAY)
    cv.vtext_centred(W // 2, 1000, FOOTER_2, 8, GRAY)

    apply_grain(cv, 1, 0.45)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    try:
        os.makedirs(outdir, exist_ok=True)
    except OSError:
        outdir = "."
    path = os.path.join(outdir, "entry.png")
    cv = draw()
    png = write_png(path, cv)
    print("path:  ", path)
    print("sha256:", hashlib.sha256(png).hexdigest())
    print("bytes: ", len(png))
    print("size:  ", cv.w, "x", cv.h)


if __name__ == "__main__":
    main()
