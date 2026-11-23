#!/usr/bin/env python3
"""The World in One Day -- Sunday 22 November 2026.

Fresh rebuild: a single 1024x1024 newspaper front page summing up the
world news of Sunday 22 November 2026. 35 stories, all dated that day:
3 illustrated leads, 10 featured stories, 22 more in the ALSO list,
a numbered world map, and a DATE CHECK box listing the big 20-21 Nov
stories deliberately left out.

Pure Python standard library only, no network, no randomness:
running this program twice writes byte-identical output.
Usage:  python3 main.py   ->  writes /output/entry.png if /output
exists, otherwise ./entry.png next to this file.
"""

import hashlib
import os
import struct
import sys
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
PAPER = (248, 244, 233)
INK = (18, 16, 14)
RED = (176, 30, 36)
RED_DK = (140, 20, 26)
BLUE_DK = (28, 52, 96)
BLUE = (42, 84, 150)
NAVY = (16, 24, 54)
SKY = (188, 214, 232)
LAND = (217, 196, 154)
SAND = (232, 220, 188)
GREY = (90, 86, 80)
GREY_LT = (226, 220, 208)
GOLD = (176, 132, 52)
GREEN = (46, 110, 62)
TEAL = (22, 110, 110)
ORANGE = (232, 110, 24)
YELLOW = (244, 196, 48)
WHITE = (255, 255, 255)
CREAM = (240, 232, 210)


def _crc(chunk_type, data):
    return zlib.crc32(chunk_type + data) & 0xFFFFFFFF


def write_png(path, rgb, w, h):
    """Encode a flat RGB bytearray as a PNG (filter 0, zlib level 9)."""
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)
    out = bytearray(b"\x89PNG\r\n\x1a\n")
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    out += struct.pack(">I", 13) + b"IHDR" + ihdr
    out += struct.pack(">I", _crc(b"IHDR", ihdr))
    out += struct.pack(">I", len(comp)) + b"IDAT" + comp
    out += struct.pack(">I", _crc(b"IDAT", comp))
    out += struct.pack(">I", 0) + b"IEND"
    out += struct.pack(">I", _crc(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(bytes(out))
    return len(out)


class Page:
    """An RGB raster with small drawing helpers (all integer math)."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def put(self, x, y, col):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = col

    def rect(self, x, y, w, h, col):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(col) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def frame(self, x, y, w, h, col, t=1):
        self.rect(x, y, w, t, col)
        self.rect(x, y + h - t, w, t, col)
        self.rect(x, y, t, h, col)
        self.rect(x + w - t, y, t, h, col)

    def hline(self, x, y, w, col, t=1):
        self.rect(x, y, w, t, col)

    def vline(self, x, y, h, col, t=1):
        self.rect(x, y, t, h, col)

    def line(self, x0, y0, x1, y1, col, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        r = t // 2
        while True:
            self.rect(x0 - r, y0 - r, t, t, col)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, col):
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= r else 0
            self.rect(cx - dx, yy, dx * 2 + 1, 1, col)

    def ring(self, cx, cy, r, col, t=2):
        for yy in range(cy - r - 1, cy + r + 2):
            for xx in range(cx - r - 1, cx + r + 2):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if abs(d - r) <= t / 2.0:
                    self.put(xx, yy, col)

    def poly(self, pts, col):
        """Scanline fill of a simple polygon."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for yy in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    xs.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for k in range(0, len(xs) - 1, 2):
                self.rect(int(xs[k]), yy, max(1, int(xs[k + 1]) - int(xs[k])), 1, col)

    def burst(self, cx, cy, r0, r1, spikes, col, col2=None):
        """Starburst: alternating long/short spikes around a centre."""
        import math as _m
        pts = []
        for i in range(spikes * 2):
            ang = _m.pi * i / spikes - _m.pi / 2
            r = r1 if i % 2 == 0 else r0
            pts.append((cx + int(r * _m.cos(ang)), cy + int(r * _m.sin(ang))))
        self.poly(pts, col)
        if col2 is not None:
            self.disc(cx, cy, max(2, r0 // 2), col2)

    def flame(self, x, y, w, h, col, col2):
        """A flame: tall triangle-ish blob with a bright core."""
        self.poly([(x, y + h), (x + w // 2, y), (x + w, y + h)], col)
        self.poly([(x + w // 4, y + h), (x + w // 2, y + h // 2),
                   (x + 3 * w // 4, y + h)], col2)


def flag_eu(pg, x, y, w, h):
    pg.rect(x, y, w, h, BLUE)
    import math as _m
    cx, cy = x + w // 2, y + h // 2
    for k in range(12):
        a = 2 * _m.pi * k / 12 - _m.pi / 2
        pg.disc(cx + int((w // 3) * _m.cos(a)), cy + int((h // 3) * _m.sin(a)), 1, YELLOW)


def flag_stripe(pg, x, y, w, h, cols):
    n = len(cols)
    for i, c in enumerate(cols):
        pg.rect(x, y + i * h // n, w, h // n + 1, c)


def flagpole(pg, x, y, h, col=INK):
    pg.vline(x, y, h, col, 2)
    pg.disc(x, y, 2, GOLD)

# ------------------------------------------------------------------- font
# Hand-drawn 5x7 bitmap font. '#' is ink, '.' is blank. Capitals and
# digits use all 7 rows; lower case uses an x-height of rows 2-6, with
# ascenders reaching row 0 and descenders hooking in rows 5-6.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    'a': ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    'b': ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    'c': ("00000", "00000", "01110", "10000", "10000", "10001", "01110"),
    'd': ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    'e': ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    'f': ("00110", "01000", "01000", "11110", "01000", "01000", "01000"),
    'g': ("00000", "00000", "01110", "10001", "10001", "01111", "00001"),
    'h': ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    'i': ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    'j': ("00010", "00000", "00110", "00010", "00010", "00010", "01100"),
    'k': ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    'l': ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    'm': ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    'n': ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    'o': ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    'p': ("00000", "00000", "11110", "10001", "10001", "11110", "10000"),
    'q': ("00000", "00000", "01111", "10001", "10001", "01111", "00001"),
    'r': ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    's': ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    't': ("01000", "01000", "11110", "01000", "01000", "01000", "00110"),
    'u': ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    'v': ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    'w': ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    'x': ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    'y': ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    'z': ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '-': ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    '\u2013': ("00000", "00000", "00000", "01111", "00000", "00000", "00000"),
    '\u2014': ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '\u2019': ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '\u00b7': ("00000", "00000", "00000", "00000", "01100", "01100", "00000"),
    '\u2022': ("00000", "00000", "01100", "01100", "00000", "00000", "00000"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '*': ("00000", "00100", "10101", "01110", "10101", "00100", "00000"),
    '[': ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    ']': ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '@': ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '~': ("00000", "00000", "01001", "10110", "00000", "00000", "00000"),
    '^': ("00100", "01010", "00000", "00000", "00000", "00000", "00000"),
    '\\': ("10000", "01000", "01000", "00100", "00010", "00010", "00001"),
    '|': ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
    '`': ("01000", "00100", "00000", "00000", "00000", "00000", "00000"),
}


def adv(ch, s):
    """Advance width of one glyph at scale s (narrow glyphs are tighter)."""
    if ch in "ilj.,:;!'|":
        return int(4 * s) + 1
    if ch == ' ':
        return int(4 * s) + 1
    if ch in "mwMW":
        return int(7 * s) + 1
    return int(6 * s) + 1


def text_w(s, txt):
    return sum(adv(c, s) for c in txt)


def draw_text(pg, x, y, txt, s, col, bold=False, track=0):
    """Draw text at (x, y) = top-left of the 7-row cell, scale s (float
    allowed, nearest-neighbour). Returns width in pixels."""
    cx = x
    hgt = int(7 * s + 0.5)
    for ch in txt:
        g = FONT.get(ch, FONT['?'])
        wdt = int(5 * s + 0.5)
        passes = (0, 1) if bold else (0,)
        for dx0 in passes:
            for r in range(7):
                row = g[r]
                for c in range(5):
                    if row[c] == '1':
                        x0 = cx + dx0 + int(c * s)
                        y0 = y + int(r * s)
                        pg.rect(x0, y0, max(1, int(s + 0.5)), max(1, int(s + 0.5)), col)
        cx += adv(ch, s) + track
    return cx - x - track if txt else 0


def wrap(txt, s, maxw):
    """Greedy word wrap; returns a list of lines fitting maxw pixels."""
    lines = []
    for chunk in txt.split("\n"):
        words = chunk.split(" ")
        cur = ""
        for wd in words:
            trial = (cur + " " + wd).strip()
            if text_w(s, trial) <= maxw or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = wd
        if cur:
            lines.append(cur)
    return lines


def para(pg, x, y, txt, s, col, maxw, lh=None, bold=False, max_lines=None):
    """Draw a wrapped paragraph; returns the y just below the last line."""
    if lh is None:
        lh = int(7 * s + 4)
    lines = wrap(txt, s, maxw)
    if max_lines is not None:
        lines = lines[:max_lines]
    for ln in lines:
        draw_text(pg, x, y, ln, s, col, bold=bold)
        y += lh
    return y


def centre(pg, cx, y, txt, s, col, bold=False):
    draw_text(pg, cx - text_w(s, txt) // 2, y, txt, s, col, bold=bold)


def fit_scale(txt, maxw, s_hi, s_lo=1.0, step=0.25):
    """Largest scale in [s_lo, s_hi] at which txt fits maxw."""
    s = s_hi
    while s > s_lo and text_w(s, txt) > maxw:
        s -= step
    return max(s, s_lo)

# -------------------------------------------------------------------- data
NUMBERS = [
    ("2", "INJURED IN THE BAHRAIN STRIKE"),
    ("36", "MISSING AFTER THE CIKANDE FACTORY FIRE"),
    ("14", "MISSING AFTER THE KYIV DRONE STRIKE"),
    ("186", "OVERNIGHT DRONE BARRAGE ON UKRAINE"),
    ("720", "INDIA DECLARES AT 720 FOR 9 VS NEW ZEALAND"),
    ("15", "KM SWUM ACROSS THE STRAIT OF HORMUZ"),
]

REGIONS = [
    ("EUROPE 10", (30, 58, 110), 208),
    ("ASIA 8", (178, 32, 38), 178),
    ("MIDDLE EAST 6", (172, 128, 48), 172),
    ("AFRICA 2", (46, 110, 62), 88),
    ("AMERICAS 7", (128, 30, 34), 170),
    ("OCEANIA 1", (22, 110, 110), 90),
    ("GLOBAL 1", (70, 70, 74), 90),
]

# (num, place, topic, label lines, headline, body, status, scene)
LEADS = [
    (1, "ANTALYA", "CLIMATE",
     ["COP31", "NO DEAL"],
     "COP31 collapses with no deal",
     "Antalya talks break down on Sunday after the EU rejects a fourth "
     "draft with no mention of fossil fuels. (Reuters)",
     "CONFIRMED - REUTERS", "table"),
    (2, "SITRA, BAHRAIN", "STRIKE",
     ["BAHRAIN", "MISSILES HIT SITRA"],
     "Iran strikes Bahrain site",
     "Bahrain says an Iranian strike on a civilian site in Sitra injured "
     "two, one critically; Gulf states condemn it. (Reuters)",
     "CONFIRMED - REUTERS", "night"),
    (3, "CIKANDE, INDONESIA", "FIRE",
     ["CIKANDE FIRE", "36 STILL MISSING"],
     "Factory fire kills three",
     "Fire at a candy factory in Cikande leaves three dead and 36 missing "
     "as rescuers search the ruins. (AP)",
     "CONFIRMED - AP", "fire"),
]

# (num, place, topic, chip, headline, body, status, scene)
FEATURES = [
    (4, "KYIV REGION", "DRONE", "KYIV DRONE",
     "Drone collapses Kyiv block",
     "Five-storey block hit on Sunday; at least 14 missing. (Straits Times)",
     "CONFIRMED - STRAITS TIMES", "drone"),
    (5, "UKRAINE", "BARRAGE", "BARRAGE",
     "186 drones hit Ukraine",
     "186 Shahed drones, 161 downed; strikes at 18 sites. "
     "(Euromaidan Press)",
     "CONFIRMED - EUROMAIDAN PRESS", "barrage"),
    (6, "SEOUL", "RESIGNATION", "SEOUL",
     "Seoul minister quits",
     "Education chief resigns over AI cheating scandal. (BBC)",
     "REPORTED - BBC", "seoul"),
    (7, "WASHINGTON", "FBI HACK", "NCIC BREACH",
     "FBI probes NCIC breach",
     "Apparent hack of police database; second in two months. (CNN)",
     "CONFIRMED - CNN", "ncic"),
    (8, "GLOBAL", "MARKETS", "MARKETS",
     "Tech shares stay down",
     "Brent crude near $90 as Hormuz crisis bites. (Reuters)",
     "REPORTED - REUTERS", "markets"),
    (9, "PARIS", "PROTESTS", "PROTESTS",
     "Sixth weekend of protests",
     "144 arrests in France; thousands march in Lisbon. (France 24)",
     "REPORTED - FRANCE 24", "protests"),
    (10, "NEW DELHI", "VISIT", "STATE VISIT",
     "Nepal PM visits India",
     "Balendra Shah arrives for a two-day state visit. (Dainik Jagran)",
     "REPORTED - DAINIK JAGRAN", "visit"),
    (11, "GAZA", "GROUND OP", "GAZA OP",
     "Gaza ground op ends",
     "Israeli military ends operation beyond Yellow Line. (BBC)",
     "REPORTED - BBC", "gaza"),
    (12, "S AFRICA", "ELECTION", "ANC CITIES",
     "ANC fights for cities",
     "Party battles to hold key cities after vote setback. (BBC)",
     "REPORTED - BBC", "anc"),
    (13, "CROATIA", "HOSPITAL", "HOSPITAL DEATH",
     "Croatia hospital death",
     "Outrage after psychiatric patient dies of alleged abuse. (Al Jazeera)",
     "REPORTED - AL JAZEERA", "hospital"),
]

ALSO = [
    (14, "SAUDI ARABIA", "HOUTHI FIRE ON SAUDI", "HANSEN", "CLAIM"),
    (15, "TEHRAN", "HORMUZ REOPENING NOT DIFFICULT", "JAGRAN", "REPORTED"),
    (16, "SUDAN", "ARMY ADVANCES AFTER DEFECTIONS", "FT", "REPORTED"),
    (17, "MOSCOW", "DISSIDENT CHEMIST UGLEV DIES AT 80", "HT", "REPORTED"),
    (18, "GUATEMALA", "WANTED MEXICAN ARRESTED", "AP", "REPORTED"),
    (19, "BRASILIA", "LULA FISCAL VOTE NEARS IN CHAMBER", "SYNTHESIS", "REPORTED"),
    (20, "GENEVA", "UN ROBOT TALKS EXTENDED TO 2028", "HANSEN", "REPORTED"),
    (21, "WASHINGTON", "VCENTER FLAW EXPLOITED", "CISA", "REPORTED"),
    (22, "BACKSPACE", "SPOT BREACH EXPOSES SECRETS", "AP", "REPORTED"),
    (23, "GEORGIA", "MAN HELD OVER IS-LINKED TRANSFERS", "SPEARNET", "REPORTED"),
    (24, "TEHRAN", "NEIGHBOURHOOD SURVEILLANCE GROWS", "SPEARNET", "REPORTED"),
    (25, "HORMUZ", "PUGH SWIMS 15 KM ACROSS STRAIT", "ONE TURN", "REPORTED"),
    (26, "CALIFORNIA", "KING TIDES, BIGGEST WAVES IN YEARS", "GUARDIAN", "REPORTED"),
    (27, "WELLINGTON", "INDIA DECLARE 720 FOR 9 VS NZ", "JAGRAN", "REPORTED"),
    (28, "NEW DELHI", "CHAHAL JOINS BJP, GETS OBC POST", "JAGRAN", "REPORTED"),
    (29, "NEW DELHI", "BJP MP WADKUTE DIES AT 72", "JAGRAN", "REPORTED"),
    (30, "ARUNACHAL", "INDIA-CHINA TALKS END", "JAGRAN", "REPORTED"),
    (31, "PARIS", "FRANCE BEAT TURKEY, INTO QUARTERS", "PULSE", "REPORTED"),
    (32, "PARIS", "FRANCE RUGBY BEAT ARGENTINA", "PULSE", "REPORTED"),
    (33, "FIJI", "QUAKE 4.9 SOUTH OF FIJI ISLANDS", "USGS", "REPORTED"),
    (34, "BEIJING", "CHINA-JAPAN TIES WORSEN", "GARDNER", "REPORTED"),
    (35, "MADRID", "SPAIN HEADS FOR 29 NOV ELECTION", "GARDNER", "REPORTED"),
]

DATE_CHECK = (
    "LEFT OUT: EL CHAPO ISIDRO CAPTURE (RAID FRI 20 NOV, REPORTED SAT 21 NOV) "
    "\u00b7 EU-INDONESIA CEPA SIGNED (SAT 21 NOV, BRUSSELS) \u00b7 VENEZUELA-US "
    "MILITARY DEAL (SIGNED WED 18 NOV, REPORTED FRI 20 NOV) \u00b7 NIGERIA BOAT "
    "CAPSIZE, 24 DEAD (NEMA STATEMENT SAT 21 NOV) \u00b7 ICJ ROHINGYA GENOCIDE "
    "RULING (THU 19 NOV) \u00b7 RIEMANN HYPOTHESIS CLAIM (FRI 20 NOV) \u00b7 TRUMP "
    "CONTRACTOR ORDER (SIGNED FRI NIGHT, REPORTED SAT 21 NOV) \u00b7 GERMANY 5-0 "
    "NETHERLANDS (FRI 20 NOV) \u00b7 COP31 OVERTIME DRAG (SAT 21 NOV - THE "
    "COLLAPSE ITSELF IS SUN 22 NOV) \u00b7 PERU QUAKE (SAT 21 NOV - IN NEWS20)."
)

FOOTER_SOURCES = (
    "Sources: BBC \u00b7 Reuters \u00b7 AP \u00b7 Al Jazeera \u00b7 AFP \u00b7 The Guardian "
    "\u00b7 CNN \u00b7 France 24 \u00b7 Euronews \u00b7 Euromaidan Press \u00b7 Dainik Jagran "
    "\u00b7 Straits Times \u00b7 FT \u00b7 USGS \u00b7 CISA \u00b7 One Turn \u00b7 Gardner "
    "\u00b7 Original drawings."
)

# Blocky world map: 20 rows x 47 cols, '#' = land, '.' = ocean.
# Equirectangular, lon -180..180 left to right, lat ~75..-60 top to bottom.
MAP_GRID = [
    "..###.#######...###..........#####.######.#####",
    "..#############.####....###.######.#######.####",
    "..#############.###.....#######.#######.#######",
    "....###########........#############.######.###",
    ".......#######........#######.##############...",
    ".......#######........##.######.###########....",
    "........######........###..########.######.....",
    ".........###..........#############............",
    "...........###........#########.##..##.........",
    ".............######...########..##..###........",
    ".............######......####.......###........",
    ".............######......####........##.##.....",
    ".............#####.......####........##.#......",
    "..............####........###.........#####....",
    "..............###.........###.........######...",
    "..............###.........##..........######...",
    "...............#.......................####.##.",
    "...............#............................#..",
    "...............#...............................",
    "...............................................",
]

# (story number, grid col, grid row) -- pins placed by lon/lat:
# col = (lon + 180) / 360 * 47, row = (75 - lat) / 135 * 20.
PINS = [
    (1, 27.4, 5.8), (2, 31.5, 8.6), (3, 37.3, 12.0), (4, 27.4, 3.7),
    (5, 29.5, 2.6), (6, 40.1, 5.6), (7, 13.4, 5.3), (9, 23.7, 3.85),
    (10, 33.6, 7.0), (11, 29.8, 7.8), (12, 27.3, 15.0), (13, 25.6, 4.4),
]

# ------------------------------------------------------------------ scenes
def _windows(pg, x, y, w, h, cols, rows, col):
    cw, ch = w // cols, h // rows
    for r in range(rows):
        for c in range(cols):
            if (r * 7 + c * 3) % 4 != 0:
                pg.rect(x + c * cw + 2, y + r * ch + 2, max(2, cw - 4),
                        max(2, ch - 4), col)


def _skyline(pg, x, y, w, h, base, col, win):
    n = 6
    bw = w // n
    for i in range(n):
        bh = h * (5 + ((i * 37) % 5)) // 12
        bx = x + i * bw
        pg.rect(bx + 1, y + h - bh, bw - 2, bh, col)
        _windows(pg, bx + 1, y + h - bh, bw - 2, bh, 4, max(2, bh // 9), win)


def paint_scene(pg, x, y, w, h, kind):
    if kind == "table":
        pg.rect(x, y, w, h, (233, 224, 196))
        pg.rect(x, y + h * 3 // 5, w, h * 2 // 5, (206, 188, 150))
        pg.rect(x + w // 8, y + h // 2, w * 3 // 4, h // 8, (122, 84, 52))
        pg.rect(x + w // 8 + 6, y + h * 5 // 8, 4, h // 4, (122, 84, 52))
        pg.rect(x + w * 7 // 8 - 10, y + h * 5 // 8, 4, h // 4, (122, 84, 52))
        fx = x + w // 6
        flag_eu(pg, fx, y + 8, 34, 20)
        flagpole(pg, fx + 17, y + 8, h // 2)
        flag_stripe(pg, fx + w // 3, y + 8, 34, 20, [RED, WHITE, RED])
        flagpole(pg, fx + w // 3 + 17, y + 8, h // 2)
        flag_stripe(pg, fx + 2 * w // 3, y + 8, 34, 20, [BLUE, WHITE, RED])
        flagpole(pg, fx + 2 * w // 3 + 17, y + 8, h // 2)
        for i in range(3):
            pg.rect(x + w // 6 + i * w // 4, y + h // 2 - 8, 26, 8, WHITE)
    elif kind == "night":
        pg.rect(x, y, w, h, NAVY)
        for i in range(14):
            pg.disc(x + (i * 53) % w, y + (i * 29) % (h // 2), 1, WHITE)
        _skyline(pg, x, y + h // 3, w, h * 2 // 3, 0, (10, 16, 40), YELLOW)
        pg.line(x + w // 4, y + 6, x + w // 4 + 26, y + h // 2, (240, 220, 160), 1)
        pg.burst(x + w // 4, y + 8, 4, 11, 8, ORANGE, YELLOW)
        pg.line(x + 3 * w // 4, y + 10, x + 3 * w // 4 - 22, y + h // 2, (240, 220, 160), 1)
        pg.burst(x + 3 * w // 4, y + 12, 4, 11, 8, ORANGE, YELLOW)
    elif kind == "fire":
        pg.rect(x, y, w, h, (46, 38, 44))
        pg.rect(x + 6, y + h // 2, w // 3, h // 2, (96, 92, 96))
        pg.rect(x + w // 3, y + h // 3, w // 4, h * 2 // 3, (120, 116, 118))
        pg.rect(x + w * 2 // 3, y + h // 2, w // 4, h // 2, (84, 80, 84))
        pg.rect(x + w // 2, y + 6, 8, h // 3, (70, 66, 68))
        pg.disc(x + w // 2 + 4, y + 4, 9, (150, 148, 146))
        pg.disc(x + w * 3 // 4, y + 10, 12, (140, 138, 136))
        for i, fx in enumerate((w // 8, w // 3, w // 2, 3 * w // 4)):
            pg.flame(x + fx, y + h - 30 - (i % 2) * 8, 16, 30, ORANGE, YELLOW)
    elif kind == "drone":
        pg.rect(x, y, w, h, (168, 176, 188))
        pg.rect(x + w // 6, y + h // 4, w * 2 // 3, h * 3 // 4, (110, 112, 118))
        _windows(pg, x + w // 6, y + h // 4, w * 2 // 3, h // 3, 4, 2, (60, 60, 66))
        pg.poly([(x + w // 6, y + h // 4), (x + w // 2, y + 4),
                 (x + w * 5 // 6, y + h // 4)], (84, 86, 92))
        pg.burst(x + w // 4, y + h // 3, 3, 9, 8, ORANGE, YELLOW)
        pg.burst(x + 3 * w // 4, y + h // 4, 3, 9, 8, ORANGE, YELLOW)
        pg.rect(x, y + h - 8, w, 8, (90, 92, 98))
    elif kind == "barrage":
        pg.rect(x, y, w, h, (18, 22, 48))
        for i in range(10):
            pg.disc(x + (i * 41) % w, y + (i * 17) % h, 1, WHITE)
        for bx, by in ((w // 5, h // 3), (w // 2, h // 5), (4 * w // 5, h // 2)):
            pg.burst(x + bx, y + by, 3, 10, 8, ORANGE, YELLOW)
        pg.line(x + 6, y + h - 6, x + w - 6, y + h - 6, (70, 70, 90), 2)
    elif kind == "seoul":
        pg.rect(x, y, w, h, (206, 216, 228))
        pg.rect(x + w // 6, y + h // 3, w // 4, h * 2 // 3, (120, 128, 140))
        pg.rect(x + w // 2, y + h // 4, w // 3, h * 3 // 4, (96, 104, 118))
        _windows(pg, x + w // 2, y + h // 4, w // 3, h // 2, 2, 3, YELLOW)
        flagpole(pg, x + w - 18, y + 6, h // 2)
        pg.rect(x + w - 34, y + 6, 30, 18, WHITE)
        pg.disc(x + w - 19, y + 12, 5, RED)
        pg.disc(x + w - 19, y + 18, 5, BLUE)
        pg.rect(x + w - 34, y + 15, 30, 3, WHITE)
    elif kind == "ncic":
        pg.rect(x, y, w, h, (20, 28, 48))
        draw_text(pg, x + 6, y + 4, "0101 1100", 1.0, (90, 120, 160))
        draw_text(pg, x + 6, y + h - 12, "1010 0110", 1.0, (90, 120, 160))
        pg.ring(x + w // 2, y + h // 2 - 4, 10, (200, 200, 200), 3)
        pg.rect(x + w // 2 - 14, y + h // 2 - 6, 28, 22, RED)
        pg.rect(x + w // 2 - 4, y + h // 2 + 2, 8, 8, WHITE)
    elif kind == "markets":
        pg.rect(x, y, w, h, WHITE)
        pg.rect(x, y + h - 8, w, 2, (180, 180, 180))
        for i, bh in enumerate((26, 20, 24, 14, 10, 6)):
            pg.rect(x + 8 + i * (w - 16) // 6, y + h - 10 - bh, (w - 16) // 7, bh, BLUE)
        pg.line(x + 8, y + 10, x + w // 3, y + h // 3, RED, 2)
        pg.line(x + w // 3, y + h // 3, x + 2 * w // 3, y + h // 2, RED, 2)
        pg.line(x + 2 * w // 3, y + h // 2, x + w - 8, y + h - 12, RED, 2)
    elif kind == "protests":
        pg.rect(x, y, w, h, BLUE_DK)
        pg.line(x, y, x + w, y + h, WHITE, 4)
        pg.line(x + w, y, x, y + h, WHITE, 4)
        pg.rect(x, y + h // 2 - 3, w, 6, RED)
        pg.rect(x + w // 2 - 3, y, 6, h, RED)
        for i in range(9):
            pg.disc(x + 10 + i * (w - 20) // 8, y + h - 8, 3, INK)
    elif kind == "visit":
        pg.rect(x, y, w, h, SAND)
        pg.rect(x + w // 8, y + h // 2, w * 3 // 4, h // 2, (150, 130, 100))
        flagpole(pg, x + w // 4, y + 6, h // 2)
        flag_stripe(pg, x + w // 4 - 16, y + 6, 32, 18,
                    [(255, 153, 51), WHITE, (19, 136, 8)])
        flagpole(pg, x + 3 * w // 4, y + 6, h // 2)
        pg.rect(x + 3 * w // 4 - 16, y + 6, 32, 18, (220, 20, 60))
        pg.frame(x + 3 * w // 4 - 16, y + 6, 32, 18, BLUE, 2)
    elif kind == "gaza":
        pg.rect(x, y, w, h, (214, 190, 140))
        pg.burst(x + w // 2, y + h // 3, 8, 20, 10, YELLOW, ORANGE)
        pg.rect(x, y + 3 * h // 4, w, 2, (120, 100, 60))
        pg.rect(x + w // 6, y + h // 2, w // 5, h // 4, (150, 128, 88))
        pg.rect(x + 2 * w // 3, y + h * 5 // 8, w // 5, h // 8, (150, 128, 88))
    elif kind == "anc":
        pg.rect(x, y, w, h, (28, 92, 58))
        cx, cy, r = x + w // 2, y + h // 2, min(w, h) // 2 - 4
        pg.disc(cx, cy, r, (90, 150, 210))
        pg.disc(cx - r // 3, cy - r // 4, r // 3, LAND)
        pg.disc(cx + r // 3, cy + r // 3, r // 4, LAND)
        for k in range(-2, 3):
            for yy in range(cy - r, cy + r + 1):
                xx = cx + k * r // 2
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    pg.put(xx, yy, (220, 230, 240))
            for xx in range(cx - r, cx + r + 1):
                yy = cy + k * r // 2
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    pg.put(xx, yy, (220, 230, 240))
    elif kind == "hospital":
        pg.rect(x, y, w, h, (228, 228, 226))
        pg.rect(x + w // 6, y + h // 4, w * 2 // 3, h * 3 // 4, (150, 152, 158))
        _windows(pg, x + w // 6, y + h // 4, w * 2 // 3, h // 2, 4, 2, (70, 90, 120))
        pg.burst(x + w // 2, y + h // 4, 6, 14, 8, YELLOW, ORANGE)
        pg.rect(x + w // 2 - 3, y + h // 4 - 10, 6, 20, RED)
        pg.rect(x + w // 2 - 10, y + h // 4 - 3, 20, 6, RED)
    pg.frame(x, y, w, h, INK, 1)


def chip(pg, x, y, lines, s=1.5):
    wdt = max(text_w(s, ln) for ln in lines) + 8
    hgt = int(7 * s + 0.5) * len(lines) + 6 + (len(lines) - 1) * 2
    pg.rect(x, y, wdt, hgt, WHITE)
    pg.frame(x, y, wdt, hgt, INK, 1)
    yy = y + 3
    for ln in lines:
        draw_text(pg, x + 4, yy, ln, s, INK, bold=True)
        yy += int(7 * s + 0.5) + 2
    return wdt, hgt


def status_strip(pg, x, y, w, txt):
    pg.rect(x, y, w, 14, (24, 22, 20))
    draw_text(pg, x + 5, y + 3, txt, 1.0, WHITE, bold=True)

# ----------------------------------------------------------------- compose
MAP_FOOTNOTE = (
    "EACH NUMBER MATCHES A STORY ON THIS PAGE. 8 IS GLOBAL MARKETS - OFF THE "
    "MAP. HOW WE CHECKED - CONFIRMED = 2+ OUTLETS \u00b7 OFFICIAL = ON THE "
    "RECORD \u00b7 REPORTED = ONE OUTLET \u00b7 CLAIM = ONE SIDE'S ACCOUNT"
)


def draw_map(pg, x, y, w, h):
    pg.rect(x, y, w, h, SKY)
    cw = w / 47.0
    ch = h / 20.0
    for r, row in enumerate(MAP_GRID):
        for c, cell in enumerate(row):
            if cell == '#':
                pg.rect(x + int(c * cw), y + int(r * ch),
                        int((c + 1) * cw) - int(c * cw),
                        int((r + 1) * ch) - int(r * ch), LAND)
    for k in range(1, 10):
        pg.vline(x + int(k * w / 10), y, h, (205, 224, 236), 1)
    for k in range(1, 4):
        pg.hline(x, y + int(k * h / 4), w, (205, 224, 236), 1)
    pg.frame(x, y, w, h, INK, 1)
    for num, col, rw in PINS:
        px = x + int((col + 0.5) * cw)
        py = y + int((rw + 0.5) * ch)
        pg.disc(px, py, 7, RED)
        pg.ring(px, py, 7, WHITE, 1)
        label = str(num)
        draw_text(pg, px - text_w(1.0, label) // 2, py - 3, label, 1.0, WHITE, bold=True)


def build():
    pg = Page(W, H, PAPER)
    pg.frame(8, 8, W - 16, H - 16, INK, 3)
    pg.frame(14, 14, W - 28, H - 28, INK, 1)
    mx, rx = 24, 1000

    # ---- masthead
    draw_text(pg, mx, 20, "THE WORLD IN ONE DAY", 2.0, RED, bold=True)
    right = "35 STORIES \u00b7 7 REGIONS \u00b7 EVERY ONE DATED SUNDAY 22 NOVEMBER 2026"
    rw = sum(adv(c, 2.0) - 1 for c in right)
    draw_text(pg, rx - rw, 20, right, 2.0, INK, bold=True, track=-1)
    centre(pg, W // 2, 40, "Sunday 22 November 2026", 4.5, INK, bold=True)
    centre(pg, W // 2, 80,
           "COP31 collapses in Antalya \u00b7 Iran strikes Bahrain \u00b7 "
           "Factory fire in Indonesia", 1.75, INK)
    pg.hline(mx, 96, rx - mx, INK, 3)
    pg.hline(mx, 101, rx - mx, INK, 1)

    # ---- the day in numbers
    draw_text(pg, mx, 106, "THE DAY IN NUMBERS", 1.5, RED, bold=True)
    cell = (rx - mx) // 6
    for i, (num, label) in enumerate(NUMBERS):
        cx = mx + i * cell
        if i:
            pg.vline(cx - 4, 106, 58, GREY, 1)
        centre(pg, cx + cell // 2, 118, num, 2.75, RED, bold=True)
        para(pg, cx + 4, 141, label, 1.0, INK, cell - 10, lh=9, max_lines=2)

    # ---- region bar
    ry, rh = 162, 16
    total = sum(w for _, _, w in REGIONS)
    xx = mx
    for name, col, wdt in REGIONS:
        seg = (rx - mx) * wdt // total
        pg.rect(xx, ry, seg, rh, col)
        sc = fit_scale(name, seg - 6, 1.5, 1.0)
        centre(pg, xx + seg // 2, ry + 3, name, sc, WHITE, bold=True)
        xx += seg
    pg.frame(mx, ry, rx - mx, rh, INK, 1)

    # ---- top stories
    draw_text(pg, mx, 184, "TOP STORIES", 1.75, RED, bold=True)
    lead_w = 304
    for i, (num, place, topic, label, head, body, status, scene) in enumerate(LEADS):
        lx = mx + i * (lead_w + 20)
        paint_scene(pg, lx, 198, lead_w, 80, scene)
        chip(pg, lx + 6, 204, label, s=1.5)
        status_strip(pg, lx, 198 + 80 - 14, lead_w, status)
        draw_text(pg, lx, 284, "%d %s \u00b7 %s" % (num, place, topic),
                  1.5, RED, bold=True)
        para(pg, lx, 300, head, 2.75, INK, lead_w, lh=22, bold=True, max_lines=2)
        para(pg, lx, 346, body, 1.25, INK, lead_w, lh=11, max_lines=4)

    # ---- more from the day
    draw_text(pg, mx, 396, "MORE FROM THE DAY", 1.75, RED, bold=True)
    feat_w = 187
    for r in range(2):
        for c in range(5):
            f = FEATURES[r * 5 + c]
            num, place, topic, chip_txt, head, body, status, scene = f
            fx = mx + c * (feat_w + 10)
            ty = 412 + r * 129
            paint_scene(pg, fx, ty, feat_w, 48, scene)
            chip(pg, fx + 4, ty + 4, [chip_txt], s=1.0)
            draw_text(pg, fx, ty + 52, "%d %s \u00b7 %s" % (num, place, topic),
                      1.25, RED, bold=True)
            para(pg, fx, ty + 66, head, 1.75, INK, feat_w, lh=15,
                 bold=True, max_lines=2)
            para(pg, fx, ty + 98, body, 1.0, INK, feat_w, lh=9, max_lines=3)

    # ---- map + also list
    draw_text(pg, mx, 670, "WHERE IT HAPPENED", 1.75, RED, bold=True)
    draw_text(pg, 506, 670, "ALSO ON SUNDAY 22 NOVEMBER - 22 MORE STORIES",
              1.5, INK, bold=True)
    draw_map(pg, mx, 686, 470, 190)
    para(pg, mx, 882, MAP_FOOTNOTE, 1.0, INK, 470, lh=8, max_lines=3)
    for col in range(2):
        lx = 506 + col * 250
        yy = 686
        for item in ALSO[col * 11:(col + 1) * 11]:
            num, place, head, src, status = item
            txt = "%d %s - %s (%s) - %s" % (num, place, head, src, status)
            for ln in wrap(txt, 0.9, 242):
                draw_text(pg, lx, yy, ln, 0.9, INK)
                yy += 8
            yy += 1

    # ---- date check
    pg.frame(mx, 912, rx - mx, 60, RED, 2)
    draw_text(pg, mx + 6, 918, "DATE CHECK", 1.25, RED, bold=True)
    para(pg, mx + 6, 932, DATE_CHECK, 1.0, INK, rx - mx - 12, lh=8,
         max_lines=5)

    # ---- footer
    centre(pg, W // 2, 978,
           "Every story here happened, or was first reported, on Sunday "
           "22 November 2026.", 1.25, INK)
    for i, ln in enumerate(wrap(FOOTER_SOURCES, 1.0, rx - mx)):
        centre(pg, W // 2, 992 + i * 8, ln, 1.0, GREY)
    return pg


def main():
    pg = build()
    outdir = "/output" if os.path.isdir("/output") else "."
    path = os.path.join(outdir, "entry.png")
    size = write_png(path, pg.px, W, H)
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print("wrote %s (%d bytes, sha256 %s)" % (path, size, digest))
    if size > 1048576:
        print("WARNING: over the 1 MiB limit", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
