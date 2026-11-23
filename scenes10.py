"""Detailed scene illustrations for the news22 v10 newspaper image.

paint_scene10(pg, x, y, w, h, kind) -- a drop-in replacement for the
flat paint_scene() in main.py. Pure stdlib, deterministic, no network.
All coordinates are logical (the Page rasterises at SS=2 underneath),
so every size below is computed from w and h and the same code reads
well at lead size (304x80) and feature size (187x48).

Technique: vertical gradients built from thin rects, two/three-tone
shading on every solid, and MANY small elements (window grids, stars,
smoke discs, people, layered flames, debris). Drawn back to front.
"""

INK = (18, 16, 14)
WHITE = (255, 255, 255)
CREAM = (240, 232, 210)
NAVY = (16, 24, 54)
SKY = (188, 214, 232)
BLUE_DK = (28, 52, 96)
BLUE = (42, 84, 150)
RED = (176, 30, 36)
ORANGE = (232, 110, 24)
YELLOW = (244, 196, 48)
GOLD = (176, 132, 52)
GREEN = (46, 110, 62)
GREY = (90, 86, 80)


# ---------------------------------------------------------------- helpers
def _mix(c1, c2, t):
    return (int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))


def _shade(col, f):
    return tuple(max(0, min(255, int(c * f))) for c in col)


def _vgrad(pg, x, y, w, h, c1, c2):
    """Vertical gradient as thin horizontal rects."""
    if h <= 0 or w <= 0:
        return
    for i in range(h):
        pg.rect(x, y + i, w, 1, _mix(c1, c2, i / max(1, h - 1)))


def _det(i, n):
    """Deterministic scatter: pseudo-random in [0, n)."""
    return ((i * 2654435761 + 97) >> 8) % max(1, n)


def _stars(pg, x, y, w, h, n, col=WHITE, ymax=None):
    hh = h if ymax is None else ymax
    for i in range(n):
        sx = x + 2 + _det(i * 2 + 1, max(1, w - 4))
        sy = y + 1 + _det(i * 3 + 5, max(1, hh - 2))
        if _det(i * 7 + 3, 5) == 0:
            pg.disc(sx, sy, 1, col)
        else:
            pg.put(sx, sy, col)


def _win_grid(pg, bx, by, bw, bh, cols, rows, lit, dark, seed=0):
    """Grid of windows, deterministically some lit, some dark."""
    if cols <= 0 or rows <= 0 or bw <= 0 or bh <= 0:
        return
    for r in range(rows):
        for c in range(cols):
            wx = int(bx + c * bw / cols) + 1
            wy = int(by + r * bh / rows) + 1
            ww = max(2, int((c + 1) * bw / cols) - int(c * bw / cols) - 2)
            wh = max(2, int((r + 1) * bh / rows) - int(r * bh / rows) - 2)
            v = (r * 5 + c * 7 + r * c * 3 + seed) % 5
            pg.rect(wx, wy, ww, wh, lit if v < 3 else dark)


def _skyline(pg, x, base_y, w, hmax, col, win_lit, win_dark, seed, n=None):
    """Row of buildings rising from base_y, with lit windows."""
    n = n or max(4, w // 34)
    bw = w / n
    for i in range(n):
        bh = hmax * (4 + _det(i * 3 + seed, 7)) // 10
        bx = int(x + i * bw)
        bwid = max(6, int(bw) - 2)
        pg.rect(bx + 1, base_y - bh, bwid, bh, col)
        # a darker roof cap and a lighter side face for depth
        pg.rect(bx + 1, base_y - bh, bwid, 2, _shade(col, 0.7))
        pg.rect(bx + 1, base_y - bh, 2, bh, _shade(col, 1.25))
        _win_grid(pg, bx + 1, base_y - bh + 2, bwid, bh - 3,
                  max(2, bwid // 7), max(2, bh // 8),
                  win_lit, win_dark, seed + i * 11)


def _trail(pg, x0, y0, x1, y1, col, step=4):
    """Dotted missile/drone trail."""
    import math
    d = math.hypot(x1 - x0, y1 - y0)
    n = max(1, int(d // step))
    for i in range(n + 1):
        t = i / n
        pg.disc(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), 1, col)


def _burst2(pg, cx, cy, r, glow=True):
    """Explosion: faint glow disc, orange starburst, yellow core."""
    if glow:
        pg.disc(cx, cy, r + 5, (120, 60, 20))
        pg.disc(cx, cy, r + 3, (200, 110, 30))
    pg.burst(cx, cy, max(2, r // 2), r, 8, ORANGE, YELLOW)
    pg.disc(cx, cy, max(2, r // 2), (255, 224, 130))


def _flame2(pg, fx, base_y, fw, fh):
    """Layered teardrop flame: orange outer, yellow mid, pale core."""
    pg.poly([(fx, base_y),
             (fx + fw // 6, base_y - fh * 2 // 3),
             (fx + fw * 2 // 5, base_y - fh * 9 // 10),
             (fx + fw // 2, base_y - fh),
             (fx + fw * 3 // 5, base_y - fh * 3 // 4),
             (fx + fw * 5 // 6, base_y - fh // 2),
             (fx + fw, base_y)], ORANGE)
    pg.poly([(fx + fw // 5, base_y),
             (fx + fw * 2 // 5, base_y - fh * 2 // 3),
             (fx + fw // 2, base_y - fh * 3 // 4),
             (fx + fw * 3 // 5, base_y - fh // 2),
             (fx + fw * 4 // 5, base_y)], YELLOW)
    pg.poly([(fx + fw // 3, base_y),
             (fx + fw // 2, base_y - fh // 3),
             (fx + fw * 2 // 3, base_y)], (255, 224, 130))


def _smoke(pg, cx, top_y, base_y, r0):
    """Rising smoke: stacked grey discs, lighter as they rise."""
    cols = [(96, 92, 90), (126, 122, 120), (150, 146, 142), (176, 172, 168)]
    n = 5
    for i in range(n):
        t = i / (n - 1)
        cy = int(base_y + (top_y - base_y) * t)
        r = max(2, int(r0 * (1 - t * 0.35)))
        dx = ((i * 5) % 7) - 3
        pg.disc(cx + dx, cy, r, cols[i % len(cols)])


def _person(pg, cx, top_y, hr, skin, shirt, hair):
    """Seated person: hair, head, shoulders. top_y = top of shoulders."""
    sh = hr * 3
    pg.poly([(cx - sh, top_y + sh), (cx - hr, top_y),
             (cx + hr, top_y), (cx + sh, top_y + sh)], shirt)
    # shirt collar / tie hint
    pg.poly([(cx - hr // 2, top_y), (cx, top_y + hr),
             (cx + hr // 2, top_y)], _shade(shirt, 1.3))
    pg.disc(cx, top_y - hr, hr, hair)
    pg.disc(cx, top_y - hr + 1, hr - 1, skin)


def _standing(pg, cx, base_y, ht, skin, suit, hair):
    """Standing figure: legs, jacket, head. base_y = feet."""
    hw = max(3, ht // 7)
    # legs
    pg.rect(cx - hw, base_y - ht // 3, hw, ht // 3, _shade(suit, 0.6))
    pg.rect(cx + 1, base_y - ht // 3, hw, ht // 3, _shade(suit, 0.6))
    # jacket
    pg.poly([(cx - hw - 2, base_y - ht // 3), (cx - hw, base_y - ht * 2 // 3),
             (cx + hw, base_y - ht * 2 // 3), (cx + hw + 2, base_y - ht // 3)],
            suit)
    # shirt V
    pg.poly([(cx - hw // 2, base_y - ht * 2 // 3), (cx, base_y - ht // 2),
             (cx + hw // 2, base_y - ht * 2 // 3)], WHITE)
    # head + hair
    hr = max(2, ht // 8)
    pg.disc(cx, base_y - ht * 2 // 3 - hr, hr, hair)
    pg.disc(cx, base_y - ht * 2 // 3 - hr + 1, hr - 1, skin)
    return (cx, base_y - ht * 2 // 3)  # shoulder point


def _drone_sil(pg, cx, cy, s, col=(40, 42, 48)):
    pg.rect(cx - s, cy - 1, 2 * s + 1, 2, col)
    pg.rect(cx - 1, cy - s // 2, 2, s, col)
    pg.disc(cx - s, cy, 2, col)
    pg.disc(cx + s, cy, 2, col)
    pg.disc(cx, cy, 1, (200, 60, 50))


def _flag_india(pg, x, y, w, h):
    pg.rect(x, y, w, h // 3 + 1, (255, 153, 51))
    pg.rect(x, y + h // 3, w, h // 3 + 1, WHITE)
    pg.rect(x, y + 2 * h // 3, w, h // 3 + 1, (19, 136, 8))
    pg.ring(x + w // 2, y + h // 2, max(2, h // 4), BLUE_DK, 1)


def _flag_nepal(pg, x, y, w, h):
    pg.frame(x, y, w, h, BLUE, 2)
    pg.rect(x + 2, y + 2, w - 4, h - 4, (220, 20, 60))
    pg.disc(x + w // 2, y + h // 3, max(2, h // 6), WHITE)
    pg.disc(x + w // 2, y + 2 * h // 3, max(2, h // 6), WHITE)


# ------------------------------------------------------------------- scenes
def _scene_table(pg, x, y, w, h):
    """COP31 climate meeting: warm room, window, clock, flags, globe,
    long table with seated delegates, documents, microphones."""
    _vgrad(pg, x, y, w, h, (238, 230, 205), (212, 196, 162))
    # back wall: a window with sky, sun and hills (left)
    wx, wy, ww, wh = x + w // 20, y + h // 12, w // 4, h // 2
    _vgrad(pg, wx, wy, ww, wh, (168, 204, 230), (224, 236, 244))
    pg.disc(wx + ww * 3 // 4, wy + wh // 4, max(2, wh // 6), (255, 224, 130))
    pg.poly([(wx, wy + wh), (wx, wy + wh * 3 // 4), (wx + ww // 2, wy + wh * 5 // 8),
             (wx + ww, wy + wh * 3 // 4), (wx + ww, wy + wh)], (120, 160, 100))
    pg.poly([(wx, wy + wh), (wx + ww // 3, wy + wh * 5 // 6),
             (wx + ww * 2 // 3, wy + wh * 5 // 6), (wx + ww, wy + wh)],
            (90, 130, 80))
    pg.frame(wx, wy, ww, wh, (120, 100, 70), 1)
    pg.vline(wx + ww // 2, wy, wh, (120, 100, 70), 1)
    pg.hline(wx, wy + wh // 2, ww, (120, 100, 70), 1)
    # wall clock (centre top)
    ccx, ccy = x + w * 2 // 5, y + h // 6
    cr = max(4, h // 7)
    pg.disc(ccx, ccy, cr, WHITE)
    pg.ring(ccx, ccy, cr, INK, 1)
    for k in range(12):
        import math
        a = 2 * math.pi * k / 12
        pg.put(ccx + int((cr - 1) * math.cos(a)), ccy + int((cr - 1) * math.sin(a)), INK)
    pg.line(ccx, ccy, ccx, ccy - cr + 3, INK, 1)
    pg.line(ccx, ccy, ccx + cr - 4, ccy + 2, INK, 1)
    pg.disc(ccx, ccy, 1, RED)
    # three small flags on the wall (right)
    for i, cols in enumerate((((42, 84, 150),), ((176, 30, 36), (255, 255, 255), (176, 30, 36)),
                              ((42, 84, 150), (255, 255, 255), (176, 30, 36)))):
        fx = x + w * (58 + i * 13) // 100
        fw, fh = max(10, w // 11), max(6, h // 6)
        fy = y + h // 10
        if len(cols) == 1:
            pg.rect(fx, fy, fw, fh, cols[0])
            pg.disc(fx + fw // 2, fy + fh // 2, 1, YELLOW)
        else:
            for j, c in enumerate(cols):
                pg.rect(fx, fy + j * fh // 3, fw, fh // 3 + 1, c)
        pg.frame(fx, fy, fw, fh, INK, 1)
        pg.vline(fx + fw // 2, fy + fh, h // 4, INK, 1)
    # the long table
    ty = y + h * 3 // 5
    pg.rect(x + w // 25, ty, w * 23 // 25, max(3, h // 14), (150, 110, 70))
    pg.rect(x + w // 25, ty + max(3, h // 14), w * 23 // 25,
            h - (ty - y) - max(3, h // 14), (122, 84, 52))
    pg.rect(x + w // 25, ty + max(3, h // 14), w * 23 // 25, 1, GOLD)
    pg.rect(x + w // 20, ty + h // 6, 4, h // 4, (100, 66, 40))
    pg.rect(x + w * 19 // 20 - 4, ty + h // 6, 4, h // 4, (100, 66, 40))
    # seated delegates behind the table
    skins = [(232, 190, 150), (198, 150, 110), (240, 205, 170),
             (170, 120, 88), (226, 182, 140), (205, 160, 120)]
    shirts = [(28, 52, 96), (176, 30, 36), (22, 110, 110),
              (90, 86, 80), (46, 110, 62), (120, 60, 90)]
    hairs = [(30, 24, 20), (70, 70, 70), (200, 200, 200),
             (18, 16, 14), (90, 60, 30), (40, 32, 26)]
    hr = max(3, h // 13)
    n = 6
    for i in range(n):
        cx = x + w * (10 + i * 16) // 100
        _person(pg, cx, ty - 1, hr, skins[i % len(skins)],
                shirts[i % len(shirts)], hairs[i % len(hairs)])
    # globe on the table (left of centre) + documents + microphones
    gx, gy = x + w // 4, ty + h // 10
    gr = max(4, h // 9)
    pg.rect(gx - 1, gy + gr - 1, 3, 4, GOLD)
    pg.disc(gx, gy, gr, (42, 120, 180))
    pg.disc(gx - gr // 3, gy - gr // 4, max(1, gr // 3), (70, 160, 90))
    pg.disc(gx + gr // 3, gy + gr // 3, max(1, gr // 4), (70, 160, 90))
    pg.ring(gx, gy, gr, (20, 60, 110), 1)
    for i, dx in enumerate((w * 38 // 100, w * 55 // 100, w * 72 // 100)):
        dx0 = x + dx
        pg.poly([(dx0, ty + h // 8), (dx0 + 10, ty + h // 8 - 2),
                 (dx0 + 12, ty + h // 8 + 5), (dx0 + 2, ty + h // 8 + 6)],
                WHITE)
        pg.hline(dx0 + 2, ty + h // 8 + 1, 8, (150, 150, 150), 1)
    for mx0 in (w // 3, w * 2 // 3):
        pg.line(x + mx0, ty + 2, x + mx0 + 4, ty - h // 8, INK, 1)
        pg.disc(x + mx0 + 4, ty - h // 8, 2, INK)


def _scene_night(pg, x, y, w, h):
    """Bahrain strike at night: navy sky, stars, moon, lit skyline with
    a dome and minaret, dotted missile trails, bursts, dark sea."""
    _vgrad(pg, x, y, w, h, (13, 19, 46), (40, 34, 68))
    _stars(pg, x, y, w, h, 30, ymax=h * 3 // 5)
    pg.disc(x + w * 7 // 8, y + h // 8, max(3, h // 12), (235, 230, 200))
    pg.disc(x + w * 7 // 8 - 2, y + h // 8 + 1, 1, (200, 194, 164))
    pg.disc(x + w * 7 // 8 + 2, y + h // 8 + 3, 1, (200, 194, 164))
    # red glow band on the horizon
    _vgrad(pg, x, y + h * 3 // 5, w, h // 5, (150, 55, 32), (70, 28, 44))
    # far skyline (dim windows), then near skyline (many lit windows)
    _skyline(pg, x, y + h * 4 // 5, w, h // 2, (30, 34, 62),
             (150, 130, 70), (22, 26, 50), seed=3)
    _skyline(pg, x, y + h * 5 // 6, w, h * 3 // 5, (10, 14, 34),
             (255, 200, 80), (14, 18, 40), seed=9)
    # dome + minaret silhouette in the middle
    dx = x + w // 2
    pg.rect(dx - w // 40, y + h // 2, w // 20, h // 3, (10, 14, 34))
    pg.disc(dx, y + h // 2, max(3, w // 40), (10, 14, 34))
    pg.vline(dx + w // 8, y + h // 3, h // 2, (10, 14, 34), 2)
    pg.disc(dx + w // 8, y + h // 3, 2, (10, 14, 34))
    # missile trails (dotted) ending in bursts
    _trail(pg, x + w // 6, y + h // 10, x + w // 4, y + h * 2 // 5,
           (240, 220, 160))
    _burst2(pg, x + w // 4, y + h * 2 // 5, max(4, h // 8))
    _trail(pg, x + w * 5 // 6, y + h // 12, x + w * 3 // 4, y + h // 3,
           (240, 220, 160))
    _burst2(pg, x + w * 3 // 4, y + h // 3, max(4, h // 8))
    pg.disc(x + w // 4, y + h * 2 // 5 - max(4, h // 8) - 3, 3, (120, 118, 116))
    pg.disc(x + w * 3 // 4, y + h // 3 - max(4, h // 8) - 3, 3, (140, 138, 136))
    # dark sea with wave lines and burst reflections
    sy = y + h * 5 // 6
    _vgrad(pg, x, sy, w, h - (sy - y), (12, 20, 38), (8, 12, 26))
    for i, wy in enumerate((sy + 3, sy + 7, sy + 11)):
        for j in range(6):
            wx = x + 6 + _det(i * 7 + j * 3, max(1, w - 14))
            pg.hline(wx, wy, 5 + _det(j, 6), (60, 90, 130), 1)
    pg.vline(x + w // 4, sy + 2, 6, (255, 200, 80), 1)
    pg.vline(x + w * 3 // 4, sy + 2, 6, (255, 200, 80), 1)


def _scene_fire(pg, x, y, w, h):
    """Cikande factory fire: smoky sky, factory blocks with broken
    roofs and chimneys, layered flames, smoke plumes, embers, rubble,
    red glow at the base, a small fire truck."""
    _vgrad(pg, x, y, w, h, (52, 44, 40), (150, 96, 58))
    # orange glow behind the factory
    _vgrad(pg, x, y + h // 2, w, h // 2, (190, 100, 40), (120, 60, 30))
    # smoke plumes rising from the roofs
    _smoke(pg, x + w // 3, y + 2, y + h // 3, max(4, h // 8))
    _smoke(pg, x + w * 2 // 3, y + 4, y + h // 4, max(5, h // 7))
    _smoke(pg, x + w // 6, y + 6, y + h // 2, max(3, h // 10))
    base = y + h * 3 // 4
    # factory block 1 (left, pitched roof)
    b1x, b1w = x + w // 20, w * 7 // 20
    pg.rect(b1x, y + h // 2, b1w, base - (y + h // 2), (96, 90, 88))
    pg.poly([(b1x - 2, y + h // 2), (b1x + b1w // 2, y + h // 3),
             (b1x + b1w + 2, y + h // 2)], (70, 64, 64))
    _win_grid(pg, b1x + 4, y + h * 9 // 16, b1w - 8, base - (y + h * 9 // 16) - 4,
              4, 2, (255, 170, 60), (50, 48, 48), seed=2)
    # factory block 2 (centre, taller, broken roof + chimney)
    b2x, b2w = x + w * 2 // 5, w * 3 // 10
    pg.rect(b2x, y + h // 3, b2w, base - (y + h // 3), (118, 112, 110))
    pg.poly([(b2x - 2, y + h // 3), (b2x + b2w // 5, y + h // 4),
             (b2x + b2w * 2 // 5, y + h // 3 + 2), (b2x + b2w * 3 // 5, y + h // 4 - 2),
             (b2x + b2w * 4 // 5, y + h // 3), (b2x + b2w + 2, y + h // 3)],
            (60, 54, 52))
    pg.rect(b2x + b2w * 3 // 4, y + h // 6, max(4, w // 40), h // 4, (80, 76, 74))
    pg.rect(b2x + b2w * 3 // 4 - 1, y + h // 6 - 2, max(6, w // 40) + 2, 3, (60, 56, 54))
    pg.disc(b2x + b2w * 3 // 4 + 2, y + h // 6 - 4, 3, (150, 146, 142))
    _win_grid(pg, b2x + 4, y + h // 2, b2w - 8, base - (y + h // 2) - 4,
              3, 3, (255, 170, 60), (52, 50, 50), seed=5)
    pg.rect(b2x + b2w // 3, base - h // 6, w // 16, h // 6, (40, 38, 38))
    # factory block 3 (right, lower)
    b3x, b3w = x + w * 3 // 4, w // 5
    pg.rect(b3x, y + h * 7 // 12, b3w, base - (y + h * 7 // 12), (84, 80, 82))
    pg.poly([(b3x - 2, y + h * 7 // 12), (b3x + b3w // 2, y + h // 2),
             (b3x + b3w + 2, y + h * 7 // 12)], (62, 58, 58))
    _win_grid(pg, b3x + 3, y + h * 2 // 3, b3w - 6, base - (y + h * 2 // 3) - 3,
              2, 1, (255, 170, 60), (48, 46, 46), seed=8)
    # flames along the base and bursting from a roof
    for i, fx in enumerate((w // 8, w // 4, w * 3 // 8, w // 2,
                            w * 5 // 8, w * 3 // 4, w * 7 // 8)):
        fw = max(8, w // 16)
        fh = max(10, h // 3 + (i % 3) * 4 - 4)
        _flame2(pg, x + fx - fw // 2, base + 2, fw, fh)
    _flame2(pg, b2x + b2w // 4, y + h // 3 + 2, max(8, w // 18), max(8, h // 4))
    # embers rising
    for i in range(18):
        ex = x + 4 + _det(i * 5 + 1, max(1, w - 8))
        ey = y + h // 4 + _det(i * 11 + 2, max(1, h // 2))
        pg.disc(ex, ey, 1, (255, 200, 80) if i % 3 else ORANGE)
    # rubble + debris at the base
    pg.poly([(x + w // 3, base + 4), (x + w // 2, base - 4),
             (x + w * 2 // 3, base + 4)], (110, 104, 98))
    for i in range(10):
        dx = x + 6 + _det(i * 13 + 4, max(1, w - 12))
        pg.rect(dx, base + 2 + _det(i, 4), 2, 2, (70, 66, 62))
    # red glow band + dark ground
    _vgrad(pg, x, base, w, max(3, h // 8), (200, 60, 24), (90, 26, 18))
    pg.rect(x, y + h * 7 // 8, w, h // 8, (40, 34, 32))
    # small fire truck (bottom left)
    tx, tw = x + w // 16, w // 6
    th = max(6, h // 7)
    pg.rect(tx, y + h - th - 3, tw, th, (176, 30, 36))
    pg.rect(tx + tw * 2 // 3, y + h - th - 6, tw // 3, 6, (176, 30, 36))
    pg.rect(tx + 2, y + h - th, tw // 3, 2, WHITE)
    pg.disc(tx + tw // 4, y + h - 3, 2, INK)
    pg.disc(tx + tw * 3 // 4, y + h - 3, 2, INK)


def _scene_drone(pg, x, y, w, h):
    """Kyiv apartment block hit: grey-blue sky, searchlight beams,
    five-storey block with many windows, collapsed corner, rubble,
    dust, a drone silhouette, trees."""
    _vgrad(pg, x, y, w, h, (148, 160, 180), (198, 202, 210))
    # clouds
    for cx, cy, cr in ((w // 5, h // 6, 6), (w // 2, h // 9, 5), (w * 4 // 5, h // 5, 6)):
        pg.disc(x + cx, y + cy, cr, (225, 228, 232))
        pg.disc(x + cx + cr, y + cy + 1, cr - 1, (225, 228, 232))
        pg.disc(x + cx - cr, y + cy + 1, cr - 1, (225, 228, 232))
    pg.disc(x + w * 9 // 10, y + h // 10, max(3, h // 14), (245, 240, 210))
    # searchlight beams (pale triangles from the ground)
    for bx in (w // 10, w * 9 // 10):
        pg.poly([(x + bx, y + h), (x + bx + w // 12, y + h // 6),
                 (x + bx + w // 8, y + h // 6)], (242, 238, 200))
    # background block (left, smaller)
    pg.rect(x + w // 24, y + h * 2 // 5, w // 8, h * 3 // 5, (140, 142, 150))
    _win_grid(pg, x + w // 24 + 2, y + h * 2 // 5 + 3, w // 8 - 4, h // 2,
              2, 4, (255, 210, 110), (80, 82, 88), seed=4)
    # main five-storey block
    bx, bw = x + w // 6, w * 2 // 3
    top, bot = y + h // 6, y + h * 7 // 8
    pg.rect(bx, top, bw * 2 // 3, bot - top, (128, 130, 138))
    pg.rect(bx + bw * 2 // 3, top, bw // 3, bot - top, (110, 112, 120))
    pg.rect(bx, top, bw, 3, (88, 90, 98))
    pg.vline(bx + bw * 2 // 3, top, bot - top, (96, 98, 106), 1)
    # windows: 6 cols x 5 rows, some lit, some dark, some broken
    for r in range(5):
        for c in range(6):
            wx = bx + 4 + c * (bw - 8) // 6
            wy = top + 5 + r * (bot - top - 8) // 5
            ww = max(3, (bw - 8) // 6 - 4)
            wh = max(3, (bot - top - 8) // 5 - 4)
            v = (r * 5 + c * 7 + r * c) % 6
            if v == 0:
                pg.rect(wx, wy, ww, wh, (255, 210, 110))
            elif v == 1:
                pg.rect(wx, wy, ww, wh, (40, 40, 46))
                pg.line(wx, wy + wh, wx + ww, wy, (200, 200, 200), 1)
            else:
                pg.rect(wx, wy, ww, wh, (58, 60, 66))
                if v == 2:
                    pg.rect(wx + 1, wy + 1, max(1, ww // 2), max(1, wh // 2),
                            (90, 110, 140))
    # collapsed corner (top right): a jagged bite out of the block
    pg.poly([(bx + bw * 3 // 4, top), (bx + bw, top),
             (bx + bw, top + (bot - top) // 3),
             (bx + bw * 7 // 8, top + (bot - top) // 5),
             (bx + bw * 5 // 6, top + (bot - top) // 8)],
            (148, 160, 180))
    # tilted slab hanging from the break
    pg.poly([(bx + bw * 3 // 4, top + (bot - top) // 4),
             (bx + bw * 7 // 8, top + (bot - top) // 5),
             (bx + bw * 5 // 6, top + (bot - top) // 3),
             (bx + bw * 2 // 3, top + (bot - top) // 3)], (100, 102, 110))
    # rubble pile + dust at the base of the break
    pg.poly([(bx + bw * 2 // 3, bot), (bx + bw * 3 // 4, bot - h // 6),
             (bx + bw, bot - h // 10), (bx + bw, bot)], (120, 114, 106))
    pg.poly([(bx + bw * 3 // 4, bot), (bx + bw * 5 // 6, bot - h // 9),
             (bx + bw, bot)], (96, 90, 84))
    for i, (dx, dy, r) in enumerate(((6, 2, 4), (-4, 4, 3), (10, 5, 3))):
        pg.disc(bx + bw * 4 // 5 + dx, bot - h // 8 + dy, r, (210, 206, 200))
    for i in range(8):
        dx = bx + bw * 2 // 3 + _det(i * 7 + 1, max(1, bw // 3))
        pg.rect(dx, bot - 2 + _det(i, 3), 2, 2, (80, 76, 70))
    # drone silhouette with dotted trail
    _trail(pg, x + w * 3 // 4, y + h // 12, x + w * 7 // 8, y + h // 5,
           (120, 124, 132))
    _drone_sil(pg, x + w * 7 // 8, y + h // 5, max(3, w // 60))
    # trees at the base left
    for tx in (w // 12, w // 8):
        pg.vline(x + tx, bot - h // 8, h // 8, (90, 70, 50), 2)
        pg.disc(x + tx, bot - h // 8, max(3, h // 10), (60, 110, 60))
        pg.disc(x + tx - 3, bot - h // 10, max(2, h // 14), (80, 130, 70))
    # ground strip
    pg.rect(x, bot, w, y + h - bot, (96, 96, 102))
    pg.hline(x, bot, w, (70, 70, 76), 1)


def _scene_barrage(pg, x, y, w, h):
    """186 drones over Ukraine: very dark sky packed with drone
    silhouettes and faint tracers, bursts, red horizon glow, a dark
    skyline with a few lit windows at the bottom."""
    _vgrad(pg, x, y, w, h, (8, 10, 26), (32, 24, 48))
    _stars(pg, x, y, w, h, 18, ymax=h // 2)
    # red glow on the horizon
    _vgrad(pg, x, y + h * 2 // 3, w, h // 5, (160, 55, 30), (80, 30, 32))
    # many drones: deterministic scatter over the top two thirds
    for i in range(22):
        dx = x + 4 + _det(i * 3 + 1, max(1, w - 8))
        dy = y + 3 + _det(i * 5 + 7, max(1, h * 2 // 3))
        _drone_sil(pg, dx, dy, max(2, w // 90), col=(70, 72, 80))
        if i % 3 == 0:
            _trail(pg, dx - 2, dy, dx - 12, dy - 3, (150, 150, 160), step=3)
    # bursts at several heights
    for bx, by, br in ((w // 5, h // 3, 5), (w // 2, h // 5, 6),
                       (w * 4 // 5, h // 2, 5), (w * 3 // 5, h * 2 // 5, 4)):
        _burst2(pg, x + bx, y + by, max(4, br * h // 80))
    # dark skyline with a few lit windows + one tower
    _skyline(pg, x, y + h * 9 // 10, w, h // 3, (12, 14, 26),
             (255, 200, 80), (16, 18, 30), seed=6)
    pg.rect(x + w // 2 - 2, y + h // 2, 4, h * 2 // 5, (12, 14, 26))
    pg.disc(x + w // 2, y + h // 2, 2, (220, 60, 50))
    pg.rect(x, y + h * 9 // 10, w, h // 10, (8, 9, 18))


def _scene_seoul(pg, x, y, w, h):
    """Seoul government building: pale sky, stone facade with columns
    and pediment, windows, steps, Korean flag, trees, small podium."""
    _vgrad(pg, x, y, w, h, (198, 216, 234), (168, 190, 212))
    for cx, cy, cr in ((w // 6, h // 8, 5), (w * 3 // 4, h // 6, 6)):
        pg.disc(x + cx, y + cy, cr, WHITE)
        pg.disc(x + cx + cr, y + cy + 1, cr - 1, WHITE)
    pg.disc(x + w * 9 // 10, y + h // 10, max(3, h // 14), (250, 244, 200))
    # facade
    fx, fw = x + w // 8, w * 3 // 4
    ftop, fbot = y + h // 4, y + h * 5 // 6
    pg.rect(fx, ftop, fw, fbot - ftop, (210, 204, 188))
    pg.rect(fx, fbot - 4, fw, 4, (180, 172, 152))
    # pediment triangle + emblem
    pg.poly([(fx + fw // 4, ftop), (fx + fw // 2, ftop - h // 6),
             (fx + fw * 3 // 4, ftop)], (190, 182, 164))
    pg.disc(fx + fw // 2, ftop - h // 14, max(2, h // 16), (176, 132, 52))
    pg.ring(fx + fw // 2, ftop - h // 14, max(2, h // 16), INK, 1)
    # columns (6) with capitals, windows between them
    n = 6
    cw = fw / n
    for i in range(n):
        cx0 = int(fx + i * cw) + 2
        pg.rect(cx0, ftop + 3, max(3, int(cw) - 5), fbot - ftop - 3,
                (238, 232, 216))
        pg.rect(cx0 - 1, ftop + 3, max(4, int(cw) - 3), 2, (200, 192, 172))
        pg.rect(cx0 - 1, fbot - 5, max(4, int(cw) - 3), 2, (200, 192, 172))
    for r in range(2):
        for c in range(5):
            wx = int(fx + (c + 0.5) * cw) + 1
            wy = ftop + 6 + r * (fbot - ftop - 10) // 2
            pg.rect(wx, wy, max(3, int(cw) - 8), max(4, (fbot - ftop) // 4),
                    (70, 90, 120))
            pg.frame(wx, wy, max(3, int(cw) - 8), max(4, (fbot - ftop) // 4),
                     WHITE, 1)
    # steps
    for i in range(3):
        pg.rect(fx - 4 - i * 4, fbot + i * 3, fw + 8 + i * 8, 3,
                _shade((200, 192, 172), 1.0 - i * 0.08))
    # Korean flag on a pole (right)
    px = x + w * 19 // 20
    pg.vline(px, y + h // 8, h * 5 // 8, INK, 2)
    pg.disc(px, y + h // 8, 2, GOLD)
    fw2, fh2 = max(12, w // 10), max(8, h // 6)
    pg.rect(px - fw2, y + h // 8, fw2, fh2, WHITE)
    pg.frame(px - fw2, y + h // 8, fw2, fh2, INK, 1)
    pg.disc(px - fw2 // 2, y + h // 8 + fh2 // 3, max(2, fh2 // 5), RED)
    pg.disc(px - fw2 // 2, y + h // 8 + 2 * fh2 // 3, max(2, fh2 // 5), BLUE)
    for cx0, cy0 in ((px - fw2 + 1, y + h // 8 + 1),
                     (px - 3, y + h // 8 + 1),
                     (px - fw2 + 1, y + h // 8 + fh2 - 3),
                     (px - 3, y + h // 8 + fh2 - 3)):
        pg.rect(cx0, cy0, 2, 2, INK)
    # trees flanking the building
    for tx in (w // 20, w * 3 // 40):
        pg.vline(x + tx, fbot - h // 6, h // 6, (90, 70, 50), 2)
        pg.disc(x + tx, fbot - h // 6, max(3, h // 9), (60, 110, 60))
    # small podium with microphone in front of the steps
    px0 = x + w // 2 - 4
    pg.rect(px0, y + h - h // 6, 8, h // 6, (60, 52, 44))
    pg.line(px0 + 4, y + h - h // 6, px0 + 6, y + h - h // 4, INK, 1)
    pg.disc(px0 + 6, y + h - h // 4, 2, INK)


def _scene_visit(pg, x, y, w, h):
    """Nepal PM state visit: grand facade with dome and arches, two
    flagpoles (India + Nepal), red carpet, two figures shaking hands."""
    _vgrad(pg, x, y, w, h, (190, 210, 228), (242, 230, 202))
    for cx, cy, cr in ((w // 8, h // 8, 5), (w * 7 // 8, h // 10, 5)):
        pg.disc(x + cx, y + cy, cr, WHITE)
        pg.disc(x + cx + cr, y + cy + 1, cr - 1, WHITE)
    # grand facade with a dome
    fx, fw = x + w // 10, w * 4 // 5
    ftop, fbot = y + h // 5, y + h * 3 // 4
    pg.rect(fx, ftop, fw, fbot - ftop, (226, 208, 170))
    pg.rect(fx, ftop, fw, 3, (200, 178, 138))
    pg.disc(fx + fw // 2, ftop, max(4, w // 22), (210, 190, 150))
    pg.rect(fx + fw // 2 - 1, ftop - max(4, w // 22) - 3, 2, 4, GOLD)
    pg.disc(fx + fw // 2, ftop - max(4, w // 22) - 3, 2, GOLD)
    # columns + arched doorways + windows
    n = 5
    cw = fw / n
    for i in range(n):
        cx0 = int(fx + i * cw) + 2
        pg.rect(cx0, ftop + 4, max(3, int(cw) - 6), fbot - ftop - 4,
                (240, 226, 196))
    for i in range(4):
        ax = int(fx + (i + 0.5) * cw)
        aw = max(5, int(cw) - 12)
        ay = ftop + (fbot - ftop) // 2
        pg.rect(ax - aw // 2, ay, aw, fbot - ay, (90, 70, 50))
        pg.disc(ax, ay, aw // 2, (90, 70, 50))
        pg.rect(ax - aw // 2 + 1, ay + 2, aw - 2, fbot - ay - 2, (60, 46, 34))
    for i in range(4):
        wx = int(fx + (i + 0.5) * cw) - 3
        pg.rect(wx, ftop + 6, 6, max(4, h // 8), (70, 90, 120))
        pg.frame(wx, ftop + 6, 6, max(4, h // 8), WHITE, 1)
    # flagpoles: India (left), Nepal (right)
    for px, kind in ((x + w // 6, "india"), (x + w * 5 // 6, "nepal")):
        pg.vline(px, y + h // 10, h * 3 // 5, INK, 2)
        pg.disc(px, y + h // 10, 2, GOLD)
        fw2, fh2 = max(12, w // 9), max(8, h // 6)
        if kind == "india":
            _flag_india(pg, px + 2, y + h // 10, fw2, fh2)
        else:
            _flag_nepal(pg, px - fw2 - 2, y + h // 10, fw2, fh2)
    # red carpet from the door to the bottom edge
    cx0 = x + w // 2
    pg.poly([(cx0 - w // 14, fbot), (cx0 + w // 14, fbot),
             (cx0 + w // 8, y + h), (cx0 - w // 8, y + h)], (176, 30, 36))
    pg.line(cx0 - w // 14, fbot, cx0 - w // 8, y + h, GOLD, 1)
    pg.line(cx0 + w // 14, fbot, cx0 + w // 8, y + h, GOLD, 1)
    for i in range(4):
        yy = fbot + (y + h - fbot) * i // 4
        pg.hline(cx0 - w // 10, yy, w // 5, GOLD, 1)
    # two figures shaking hands on the carpet
    ht = max(14, h // 3)
    fy = y + h - 2
    p1 = _standing(pg, cx0 - w // 16, fy, ht, (232, 190, 150),
                   (28, 52, 96), (30, 24, 20))
    p2 = _standing(pg, cx0 + w // 16, fy, ht, (198, 150, 110),
                   (40, 40, 44), (18, 16, 14))
    pg.line(p1[0] + 2, p1[1] + 3, cx0, p1[1] + 6, (232, 190, 150), 1)
    pg.line(p2[0] - 2, p2[1] + 3, cx0, p1[1] + 6, (198, 150, 110), 1)
    pg.disc(cx0, p1[1] + 6, 2, (232, 190, 150))
    # shrubs along the carpet
    for sx in (w // 4, w * 3 // 4):
        pg.disc(x + sx, y + h - h // 10, max(3, h // 10), (60, 110, 60))
        pg.disc(x + sx - 3, y + h - h // 12, max(2, h // 14), (80, 130, 70))


# ------------------------------------------------------------- stub kinds
def _scene_ncic(pg, x, y, w, h):
    """FBI database hack: dark screen, binary rows, warning triangle,
    padlock, scan lines."""
    _vgrad(pg, x, y, w, h, (16, 22, 40), (28, 38, 66))
    for r in range(6):
        for c in range(14):
            if (r * 7 + c * 3) % 4 == 0:
                pg.rect(x + 4 + c * (w - 8) // 14, y + 3 + r * 4,
                        max(2, (w - 8) // 28), 2, (90, 200, 120))
    for yy in range(y + 4, y + h - 4, 5):
        pg.hline(x + 2, yy, w - 4, (40, 54, 84), 1)
    cx, cy = x + w // 2, y + h // 2
    pg.poly([(cx, cy - h // 4), (cx + w // 10, cy + h // 5),
             (cx - w // 10, cy + h // 5)], RED)
    pg.rect(cx - 1, cy - h // 8, 2, h // 6, WHITE)
    pg.disc(cx, cy + h // 8, 1, WHITE)
    # padlock (left)
    lx = x + w // 6
    pg.ring(lx, y + h // 3, max(3, h // 8), GOLD, 2)
    pg.rect(lx - w // 16, y + h // 3, w // 8, h // 4, GOLD)
    pg.disc(lx, y + h // 2, 2, INK)
    # fingerprint arcs (right)
    for r in range(4, max(5, h // 4), 3):
        pg.ring(x + w * 5 // 6, y + h // 2, r, (150, 170, 200), 1)


def _scene_markets(pg, x, y, w, h):
    """Markets plunge: white chart, grid, candlesticks, red down-trend,
    volume bars."""
    pg.rect(x, y, w, h, WHITE)
    for i in range(1, 5):
        pg.hline(x + 2, y + i * h // 5, w - 4, (225, 225, 225), 1)
    for i in range(1, 7):
        pg.vline(x + i * w // 7, y + 2, h - 4, (235, 235, 235), 1)
    # candlesticks: alternating green/red, falling
    for i in range(8):
        cx = x + 6 + i * (w - 12) // 8
        top = y + 6 + i * (h // 14)
        bh = max(4, h // 4 - i)
        col = GREEN if i % 3 == 0 else RED
        pg.vline(cx + 2, top - 3, bh + 6, col, 1)
        pg.rect(cx, top, 5, bh, col)
    # red down-trend line
    pg.line(x + 6, y + 6, x + w // 3, y + h // 3, RED, 2)
    pg.line(x + w // 3, y + h // 3, x + 2 * w // 3, y + h // 2, RED, 2)
    pg.line(x + 2 * w // 3, y + h // 2, x + w - 6, y + h - 10, RED, 2)
    pg.poly([(x + w - 10, y + h - 14), (x + w - 4, y + h - 8),
             (x + w - 12, y + h - 6)], RED)
    # volume bars at the bottom
    for i in range(10):
        bh = 3 + _det(i * 3 + 1, max(1, h // 5))
        pg.rect(x + 4 + i * (w - 8) // 10, y + h - 2 - bh,
                max(2, (w - 8) // 12), bh, (160, 160, 160))
    pg.rect(x, y + h - 2, w, 2, (180, 180, 180))


def _scene_protests(pg, x, y, w, h):
    """Paris protests: dusk sky, rooftops, crowd of heads and placards,
    one big banner."""
    _vgrad(pg, x, y, w, h, (120, 140, 180), (220, 200, 170))
    # rooftops
    for i in range(4):
        bx = x + i * w // 4
        pg.rect(bx + 2, y + h // 3, w // 4 - 4, h // 6, (110, 100, 92))
        pg.poly([(bx + 2, y + h // 3), (bx + w // 8, y + h // 5),
                 (bx + w // 4 - 2, y + h // 3)], (84, 76, 70))
    # big banner across the crowd
    pg.rect(x + w // 4, y + h * 5 // 12, w // 2, max(4, h // 8), WHITE)
    pg.frame(x + w // 4, y + h * 5 // 12, w // 2, max(4, h // 8), RED, 1)
    pg.rect(x + w // 4 + 2, y + h * 5 // 12 + 2, w // 2 - 4, 1, RED)
    pg.rect(x + w // 4 + 2, y + h * 5 // 12 + max(4, h // 8) - 3,
            w // 2 - 4, 1, BLUE)
    # placards on sticks
    pcols = [WHITE, YELLOW, (255, 120, 120), (150, 200, 255), WHITE]
    for i in range(5):
        px = x + w * (12 + i * 19) // 100
        py = y + h // 4 + (i % 2) * 3
        pg.vline(px + 5, py + 6, h // 4, (120, 100, 70), 1)
        pg.rect(px, py, 11, 7, pcols[i % len(pcols)])
        pg.frame(px, py, 11, 7, INK, 1)
        pg.hline(px + 2, py + 3, 7, INK, 1)
    # crowd: two rows of heads + shoulders
    skins = [(232, 190, 150), (198, 150, 110), (240, 205, 170), (170, 120, 88)]
    shirts = [(176, 30, 36), (28, 52, 96), (46, 110, 62), (220, 200, 60),
              (120, 60, 90), (22, 110, 110)]
    hr = max(2, h // 14)
    for row, yy in enumerate((y + h * 2 // 3, y + h * 5 // 6)):
        for i in range(9):
            cx = x + w * (6 + i * 11) // 100 + (row * 4)
            pg.disc(cx, yy, hr + 1, (30, 24, 20) if (i + row) % 3 else (90, 60, 30))
            pg.disc(cx, yy + 1, hr, skins[(i + row) % len(skins)])
            pg.poly([(cx - hr * 2, yy + hr * 3), (cx - hr, yy + hr),
                     (cx + hr, yy + hr), (cx + hr * 2, yy + hr * 3)],
                    shirts[(i * 2 + row) % len(shirts)])


def _scene_gaza(pg, x, y, w, h):
    """Gaza operation ends: sandy sky, ruined blocks with jagged tops,
    rubble, smoke, olive tree, dust."""
    _vgrad(pg, x, y, w, h, (222, 200, 150), (190, 160, 110))
    pg.disc(x + w * 5 // 6, y + h // 7, max(3, h // 10), (250, 236, 190))
    _smoke(pg, x + w // 3, y + 2, y + h // 3, max(4, h // 8))
    base = y + h * 4 // 5
    # ruined block 1
    pg.rect(x + w // 12, y + h // 2, w // 4, base - (y + h // 2), (150, 128, 88))
    pg.poly([(x + w // 12, y + h // 2), (x + w // 6, y + h * 2 // 5),
             (x + w // 5, y + h // 2 + 2), (x + w // 4, y + h * 2 // 5 + 3),
             (x + w // 3, y + h // 2)], (120, 100, 60))
    _win_grid(pg, x + w // 12 + 3, y + h * 3 // 5, w // 4 - 6,
              base - (y + h * 3 // 5) - 3, 3, 2, (60, 56, 50), (90, 78, 56),
              seed=1)
    # ruined block 2
    pg.rect(x + w * 3 // 5, y + h * 3 // 5, w // 4, base - (y + h * 3 // 5),
            (140, 118, 80))
    pg.poly([(x + w * 3 // 5, y + h * 3 // 5), (x + w * 2 // 3, y + h // 2),
             (x + w * 3 // 4, y + h * 3 // 5 + 2), (x + w * 17 // 20, y + h * 3 // 5)],
            (110, 90, 54))
    _win_grid(pg, x + w * 3 // 5 + 3, y + h * 2 // 3, w // 4 - 6,
              base - (y + h * 2 // 3) - 3, 3, 2, (60, 56, 50), (88, 76, 54),
              seed=6)
    # low broken wall between the blocks + a second dust cloud
    pg.rect(x + w * 2 // 5, base - h // 10, w // 6, h // 10, (130, 110, 76))
    pg.poly([(x + w * 2 // 5, base - h // 10), (x + w * 7 // 15, base - h // 6),
             (x + w * 7 // 12, base - h // 10)], (104, 86, 56))
    pg.disc(x + w // 2, base - h // 6, max(3, h // 10), (206, 198, 184))
    pg.disc(x + w // 2 + 5, base - h // 8, max(2, h // 12), (216, 208, 196))
    # rubble piles + debris
    pg.poly([(x + w // 3, base), (x + w * 5 // 12, base - h // 8),
             (x + w // 2, base)], (120, 104, 74))
    pg.poly([(x + w * 7 // 10, base), (x + w * 3 // 4, base - h // 10),
             (x + w * 5 // 6, base)], (110, 94, 66))
    for i in range(8):
        dx = x + 4 + _det(i * 11 + 2, max(1, w - 8))
        pg.rect(dx, base - 2 + _det(i, 3), 2, 2, (90, 78, 58))
    # olive tree
    pg.vline(x + w // 2, base - h // 5, h // 5, (90, 70, 50), 2)
    pg.disc(x + w // 2, base - h // 5, max(3, h // 9), (90, 120, 70))
    pg.disc(x + w // 2 - 4, base - h // 6, max(2, h // 12), (110, 140, 80))
    pg.rect(x, base, w, y + h - base, (170, 140, 92))


def _scene_anc(pg, x, y, w, h):
    """ANC cities: the ANC flag (black field, green Y edged in gold)
    on a pole, crowd silhouettes below, gold sun."""
    pg.rect(x, y, w, h, (28, 92, 58))
    pg.disc(x + w * 5 // 6, y + h // 8, max(3, h // 10), (250, 220, 120))
    # flag on a pole, waving (two panels for a wave hint)
    fx, fy, fw, fh = x + w // 6, y + h // 8, w * 3 // 5, h // 2
    pg.vline(fx - 2, fy - 2, fh + h // 4, GOLD, 2)
    pg.disc(fx - 2, fy - 2, 2, GOLD)
    pg.rect(fx, fy, fw, fh, INK)
    # gold Y, then green Y on top (thinner)
    cx, cy = fx + fw // 3, fy + fh // 2
    for col, t in ((GOLD, 7), (GREEN, 5)):
        pg.line(cx, cy, fx + fw, fy + 2, col, t)
        pg.line(cx, cy, fx + fw, fy + fh - 2, col, t)
        pg.line(cx, cy, fx, cy, col, t)
    pg.frame(fx, fy, fw, fh, GOLD, 1)
    # crowd silhouettes below the flag
    for i in range(10):
        cx0 = x + w * (5 + i * 10) // 100
        pg.disc(cx0, y + h * 5 // 6, max(2, h // 14), (20, 20, 22))
        pg.poly([(cx0 - 5, y + h), (cx0 - 3, y + h * 5 // 6 + 2),
                 (cx0 + 3, y + h * 5 // 6 + 2), (cx0 + 5, y + h)],
                (24, 24, 28))
    # small flags in the crowd
    for i, px in enumerate((w // 4, w // 2, w * 3 // 4)):
        pg.vline(x + px, y + h * 3 // 4, h // 6, GOLD, 1)
        pg.rect(x + px, y + h * 3 // 4, 8, 5, GREEN if i % 2 else GOLD)


def _scene_hospital(pg, x, y, w, h):
    """Hospital: pale sky, white hospital block with a red cross sign,
    window grid, entrance canopy, ambulance, trees."""
    _vgrad(pg, x, y, w, h, (210, 222, 232), (232, 232, 228))
    for cx, cy, cr in ((w // 6, h // 8, 5), (w * 5 // 6, h // 6, 5)):
        pg.disc(x + cx, y + cy, cr, WHITE)
        pg.disc(x + cx + cr, y + cy + 1, cr - 1, WHITE)
    bx, bw = x + w // 6, w * 2 // 3
    top, bot = y + h // 5, y + h * 7 // 8
    pg.rect(bx, top, bw, bot - top, (240, 240, 238))
    pg.rect(bx, top, bw, 3, (200, 200, 198))
    # red cross sign on the facade
    cx = bx + bw // 2
    pg.rect(cx - 2, top + 4, 4, max(6, h // 5), RED)
    pg.rect(cx - max(3, h // 10), top + 4 + max(3, h // 10) - 2,
            max(6, h // 5), 4, RED)
    _win_grid(pg, bx + 4, top + h // 4, bw - 8, bot - top - h // 4 - 6,
              6, 3, (70, 90, 120), (180, 190, 200), seed=7)
    # entrance canopy + door
    pg.rect(bx + bw // 3, bot - h // 6, bw // 3, 3, (150, 152, 158))
    pg.rect(bx + bw // 2 - 3, bot - h // 6 + 3, 6, h // 6 - 3, (60, 70, 84))
    # ambulance (bottom right)
    ax, aw = x + w * 3 // 4, w // 6
    ah = max(6, h // 6)
    pg.rect(ax, bot - ah, aw, ah, WHITE)
    pg.frame(ax, bot - ah, aw, ah, INK, 1)
    pg.rect(ax + 2, bot - ah + 2, 3, 3, RED)
    pg.rect(ax + aw - 5, bot - ah + 2, 3, 3, (70, 90, 120))
    pg.disc(ax + aw // 4, bot, 2, INK)
    pg.disc(ax + aw * 3 // 4, bot, 2, INK)
    pg.rect(ax, bot - ah + ah // 2, aw, 1, RED)
    # trees
    for tx in (w // 12, w * 11 // 12):
        pg.vline(x + tx, bot - h // 8, h // 8, (90, 70, 50), 2)
        pg.disc(x + tx, bot - h // 8, max(3, h // 10), (60, 110, 60))
    pg.rect(x, bot, w, y + h - bot, (150, 150, 146))


def _scene_tennis(pg, x, y, w, h):
    """ATP Finals: stands, blue hard court, centre net, two players, ball."""
    # stands (dark, top quarter) with crowd dots
    _vgrad(pg, x, y, w, h // 4, (34, 38, 56), (18, 20, 34))
    crowd = ((220, 220, 220), (200, 60, 60), (240, 200, 60), (120, 160, 220))
    for i in range(60):
        cx = x + 3 + _det(i * 2 + 1, max(1, w - 6))
        cy = y + 2 + _det(i * 3 + 5, max(1, h // 4 - 4))
        pg.put(cx, cy, crowd[_det(i * 7 + 2, len(crowd))])
    # blue hard court (bottom three-quarters)
    cy0 = y + h // 4
    ch = h - h // 4
    _vgrad(pg, x, cy0, w, ch, (46, 116, 186), (26, 82, 152))
    # court boundary + service lines
    pg.frame(x + 6, cy0 + 3, w - 12, ch - 6, WHITE, 1)
    pg.hline(x + 6, cy0 + ch // 2, w - 12, WHITE, 1)
    pg.vline(x + w // 4, cy0 + 3, ch - 6, WHITE, 1)
    pg.vline(x + 3 * w // 4, cy0 + 3, ch - 6, WHITE, 1)
    # net (vertical band in the centre, with dark posts)
    pg.rect(x + w // 2 - 1, cy0 + 3, 3, ch - 6, (235, 235, 235))
    pg.rect(x + w // 2 - 1, cy0 + 1, 3, 3, INK)
    pg.rect(x + w // 2 - 1, y + h - 4, 3, 3, INK)
    # players (left in white, right in navy) with rackets
    sx1, sy1 = _standing(pg, x + w // 5, y + h - 4, ch // 2,
                         (210, 170, 130), (255, 255, 255), (40, 30, 20))
    pg.line(sx1 + 4, sy1 + 4, sx1 + 10, sy1 - 2, (120, 90, 50), 1)
    pg.ring(sx1 + 11, sy1 - 3, 3, (120, 90, 50), 1)
    sx2, sy2 = _standing(pg, x + 4 * w // 5, y + h - 4, ch // 2,
                         (190, 150, 110), (20, 40, 90), (20, 20, 20))
    pg.line(sx2 - 4, sy2 + 4, sx2 - 10, sy2 - 2, (120, 90, 50), 1)
    pg.ring(sx2 - 11, sy2 - 3, 3, (120, 90, 50), 1)
    # ball (yellow, near the net)
    pg.disc(x + w // 2 + 10, cy0 + ch // 3, 3, (240, 230, 40))
    pg.disc(x + w // 2 + 10, cy0 + ch // 3, 1, (200, 190, 20))


def _scene_football(pg, x, y, w, h):
    """Football: stands, striped green pitch, goals, players, ball."""
    # stands (dark, top quarter) with crowd dots
    _vgrad(pg, x, y, w, h // 4, (30, 34, 52), (16, 18, 30))
    crowd = ((220, 220, 220), (200, 60, 60), (240, 200, 60), (120, 160, 220))
    for i in range(50):
        cx = x + 3 + _det(i * 2 + 1, max(1, w - 6))
        cy = y + 2 + _det(i * 3 + 5, max(1, h // 4 - 4))
        pg.put(cx, cy, crowd[_det(i * 7 + 2, len(crowd))])
    # pitch (green, bottom three-quarters) with mowing stripes
    py = y + h // 4
    ph = h - h // 4
    for i in range(4):
        col = (62, 152, 72) if i % 2 == 0 else (46, 128, 58)
        pg.rect(x, py + i * ph // 4, w, ph // 4 + 1, col)
    # pitch markings: boundary, halfway line, centre circle
    pg.frame(x + 4, py + 4, w - 8, ph - 8, WHITE, 1)
    pg.vline(x + w // 2, py + 4, ph - 8, WHITE, 1)
    pg.ring(x + w // 2, py + ph // 2, max(4, h // 9), WHITE, 1)
    # goals (left and right ends, white frames)
    gh = max(6, ph // 3)
    gy = py + (ph - gh) // 2
    pg.frame(x + 4, gy, 5, gh, WHITE, 1)
    pg.frame(x + w - 9, gy, 5, gh, WHITE, 1)
    # players (red vs navy)
    _standing(pg, x + w // 3, y + h - 4, h // 3,
              (210, 170, 130), (200, 30, 40), (40, 30, 20))
    _standing(pg, x + w // 2 + w // 12, y + h - 4, h // 3,
              (190, 150, 110), (20, 40, 90), (20, 20, 20))
    _standing(pg, x + 2 * w // 3, y + h - 4, h // 3,
              (200, 160, 120), (200, 30, 40), (30, 20, 10))
    # ball
    pg.disc(x + w // 2 - w // 16, py + ph // 2, 3, WHITE)
    pg.disc(x + w // 2 - w // 16, py + ph // 2, 1, INK)


# ------------------------------------------------------------------- entry
_SCENES = {
    "table": _scene_table,
    "night": _scene_night,
    "fire": _scene_fire,
    "drone": _scene_drone,
    "barrage": _scene_barrage,
    "seoul": _scene_seoul,
    "visit": _scene_visit,
    "ncic": _scene_ncic,
    "markets": _scene_markets,
    "protests": _scene_protests,
    "gaza": _scene_gaza,
    "anc": _scene_anc,
    "hospital": _scene_hospital,
    "tennis": _scene_tennis,
    "football": _scene_football,
}


def paint_scene10(pg, x, y, w, h, kind):
    """Draw a detailed illustration for `kind` inside (x, y, w, h).

    Unknown kinds fall back to a plain paper panel so the page never
    breaks; every kind main.py actually uses is implemented above.
    """
    fn = _SCENES.get(kind)
    if fn is None:
        pg.rect(x, y, w, h, CREAM)
    else:
        fn(pg, x, y, w, h)
    pg.frame(x, y, w, h, INK, 1)
