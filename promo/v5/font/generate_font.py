#!/usr/bin/env python3
"""
Wireframech Line — 鋼弦機兵 宣傳影片用 原創線條字型產生器
================================================================

每個字都用「中心線骨架」(polyline) 定義在一個方格座標上，
再用 shapely 把線條加粗 (mitre 接角)、合併、裁切，最後用 fontTools 輸出字型。

座標系統 (骨架座標)：
  * 大寫高度 H = 700，基線 y = 0，中線 y = 350
  * x 從 0 開始往右，每個字自己定義寬度 W
  * 骨架座標是「線條中心」，輸出時會自動內縮半個線寬，
    所以不論粗細，大寫字的外緣永遠剛好是 0 ~ 700。

修改字形：找到下面 GLYPHS 字典中的字元，改座標後重新執行：
    python generate_font.py
輸出會放在本檔案所在的資料夾 (或用 --out 指定)。

需要：pip install fonttools shapely brotli pillow
"""
import argparse
import math
import os

from shapely.geometry import LineString, Polygon, MultiPolygon, box, Point
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from shapely import set_precision

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.ttLib import TTFont
from fontTools.misc.timeTools import timestampFromString

# ----------------------------------------------------------------------------
# 基本參數
# ----------------------------------------------------------------------------
FAMILY = "Wireframech Line"
VERSION = "1.000"
UPM = 1000
CAP = 700            # 大寫高度
ASC = 900            # 行高上緣
DESC = -250          # 行高下緣
SB = 70              # 左右預設字距 (side bearing)

WEIGHTS = {
    # 名稱: (線寬, OS/2 weight class)
    "Thin":    (40, 200),
    "Regular": (70, 400),
}

# ----------------------------------------------------------------------------
# 字形定義
#   每個字： dict(w=骨架寬度, p=[線段...], d=[點...], f=[實心多邊形...], sb=(左,右))
#   p: 每條線是座標列表；若最後一點等於第一點 = 封閉形 (例如 O)
#   d: 方形點 (x, y)；y=0 表示貼齊基線的句點
#   f: 實心多邊形 (骨架座標)，例如 ●
# ----------------------------------------------------------------------------
C = 120   # 大切角 (O, C, G, D...)
c = 90    # 小切角 (B, S, 數字...)


def octa(x0, y0, x1, y1, k):
    """封閉的八角形 (四角 45° 切角)。"""
    return [(x0 + k, y0), (x1 - k, y0), (x1, y0 + k), (x1, y1 - k),
            (x1 - k, y1), (x0 + k, y1), (x0, y1 - k), (x0, y0 + k), (x0 + k, y0)]


G = {}

# ---- 大寫字母 ----------------------------------------------------------------
G["A"] = dict(w=560, p=[[(0, 0), (0, 580), (120, 700), (440, 700), (560, 580), (560, 0)],
                        [(0, 290), (560, 290)]])
G["B"] = dict(w=540, p=[[(0, 0), (0, 700), (420, 700), (500, 620), (500, 430), (420, 350), (0, 350)],
                        [(420, 350), (450, 350), (540, 260), (540, 90), (450, 0), (0, 0)]])
G["C"] = dict(w=540, p=[[(540, 700), (C, 700), (0, 700 - C), (0, C), (C, 0), (540, 0)]])
G["D"] = dict(w=560, p=[[(0, 0), (0, 700), (420, 700), (560, 560), (560, 140), (420, 0), (0, 0)]])
G["E"] = dict(w=500, p=[[(500, 700), (0, 700), (0, 0), (500, 0)], [(0, 350), (400, 350)]])
G["F"] = dict(w=470, p=[[(470, 700), (0, 700), (0, 0)], [(0, 350), (380, 350)]])
G["G"] = dict(w=560, p=[[(560, 700), (C, 700), (0, 700 - C), (0, C), (C, 0), (560, 0), (560, 320), (300, 320)]])
G["H"] = dict(w=560, p=[[(0, 0), (0, 700)], [(560, 0), (560, 700)], [(0, 350), (560, 350)]])
G["I"] = dict(w=0, p=[[(0, 0), (0, 700)]], sb=(90, 90))
G["J"] = dict(w=500, p=[[(500, 700), (500, C), (500 - C, 0), (C, 0), (0, C), (0, 230)]])
G["K"] = dict(w=540, p=[[(0, 0), (0, 700)], [(0, 350), (190, 350), (540, 700)], [(190, 350), (540, 0)]])
G["L"] = dict(w=480, p=[[(0, 700), (0, 0), (480, 0)]])
G["M"] = dict(w=640, p=[[(0, 0), (0, 700), (320, 380), (640, 700), (640, 0)]])
G["N"] = dict(w=560, p=[[(0, 0), (0, 700), (560, 0), (560, 700)]])
G["O"] = dict(w=600, p=[octa(0, 0, 600, 700, C)])
G["P"] = dict(w=540, p=[[(0, 0), (0, 700), (440, 700), (540, 600), (540, 420), (440, 320), (0, 320)]])
G["Q"] = dict(w=600, p=[octa(0, 0, 600, 700, C), [(380, 210), (620, -30)]])
G["R"] = dict(w=540, p=[[(0, 0), (0, 700), (440, 700), (540, 600), (540, 420), (440, 320), (0, 320)],
                        [(380, 320), (540, 160), (540, 0)]])
G["S"] = dict(w=540, p=[[(540, 610), (450, 700), (c, 700), (0, 610), (0, 440), (c, 350),
                         (450, 350), (540, 260), (540, c), (450, 0), (c, 0), (0, c)]])
G["T"] = dict(w=560, p=[[(0, 700), (560, 700)], [(280, 700), (280, 0)]])
G["U"] = dict(w=560, p=[[(0, 700), (0, C), (C, 0), (560 - C, 0), (560, C), (560, 700)]])
G["V"] = dict(w=580, p=[[(0, 700), (290, 0), (580, 700)]])
G["W"] = dict(w=760, p=[[(0, 700), (170, 0), (380, 520), (590, 0), (760, 700)]])
G["X"] = dict(w=560, p=[[(0, 700), (560, 0)], [(0, 0), (560, 700)]])
G["Y"] = dict(w=580, p=[[(0, 700), (290, 360), (580, 700)], [(290, 360), (290, 0)]])
G["Z"] = dict(w=540, p=[[(0, 700), (540, 700), (0, 0), (540, 0)]])

# ---- 數字 (等寬，方便計時/版本號對齊) ---------------------------------------
DW = 500
G["0"] = dict(w=DW, p=[octa(0, 0, DW, 700, 140), [(170, 210), (330, 490)]])
G["1"] = dict(w=340, p=[[(40, 570), (170, 700), (170, 0)], [(0, 0), (340, 0)]])  # 底座橫線 = 與 I 區分
G["2"] = dict(w=DW, p=[[(0, 610), (c, 700), (DW - c, 700), (DW, 610), (DW, 440), (DW - c, 350),
                        (c, 350), (0, 260), (0, 0), (DW, 0)]])
G["3"] = dict(w=DW, p=[[(0, 610), (c, 700), (DW - c, 700), (DW, 610), (DW, 440), (DW - c, 350), (140, 350)],
                       [(DW - c, 350), (DW, 260), (DW, c), (DW - c, 0), (c, 0), (0, c)]])
G["4"] = dict(w=DW, p=[[(380, 0), (380, 700), (0, 210), (DW, 210)]])
G["5"] = dict(w=DW, p=[[(480, 700), (0, 700), (0, 390), (DW - c, 390), (DW, 300), (DW, c),
                        (DW - c, 0), (0, 0)]])
G["6"] = dict(w=DW, p=[[(440, 700), (C, 700), (0, 700 - C), (0, c), (c, 0), (DW - c, 0), (DW, c),
                        (DW, 300), (DW - c, 390), (0, 390)]])
G["7"] = dict(w=DW, p=[[(0, 700), (DW, 700), (DW, 580), (200, 0)]])
G["8"] = dict(w=DW, p=[[(c, 350), (20, 420), (20, 620), (100, 700), (400, 700), (480, 620), (480, 420), (410, 350), (c, 350)],
                       [(c, 350), (0, 260), (0, c), (c, 0), (DW - c, 0), (DW, c), (DW, 260), (410, 350)]])
G["9"] = dict(w=DW, p=[[(60, 0), (DW - C, 0), (DW, C), (DW, 700 - c), (DW - c, 700), (c, 700), (0, 700 - c),
                        (0, 400), (c, 310), (DW, 310)]])

# ---- 標點與符號 --------------------------------------------------------------
G[" "] = dict(adv=300)
G["."] = dict(w=0, d=[(0, 0)], sb=(80, 80))
G[","] = dict(w=0, comma=[(0, 0)], sb=(80, 80))
G[":"] = dict(w=0, d=[(0, 0), (0, 420)], sb=(80, 80))
G[";"] = dict(w=0, d=[(0, 420)], comma=[(0, 0)], sb=(80, 80))
G["!"] = dict(w=0, p=[[(0, 700), (0, 230)]], d=[(0, 0)], sb=(90, 90))
G["?"] = dict(w=480, p=[[(0, 610), (c, 700), (480 - c, 700), (480, 610), (480, 450), (390, 360), (240, 360), (240, 220)]],
              d=[(240, 0)])
G["'"] = dict(w=0, p=[[(0, 700), (0, 500)]], sb=(90, 90))
G['"'] = dict(w=140, p=[[(0, 700), (0, 500)], [(140, 700), (140, 500)]], sb=(90, 90))
G["`"] = dict(w=100, p=[[(0, 760), (100, 660)]])
G["-"] = dict(w=320, p=[[(0, 330), (320, 330)]])
G["_"] = dict(w=540, p=[[(0, -110), (540, -110)]], sb=(20, 20))
G["/"] = dict(w=380, p=[[(0, -60), (380, 760)]], sb=(40, 40))
G["\\"] = dict(w=380, p=[[(0, 760), (380, -60)]], sb=(40, 40))
G["("] = dict(w=150, p=[[(150, 790), (0, 640), (0, 0), (150, -150)]], sb=(90, 50))
G[")"] = dict(w=150, p=[[(0, 790), (150, 640), (150, 0), (0, -150)]], sb=(50, 90))
G["["] = dict(w=150, p=[[(150, 790), (0, 790), (0, -150), (150, -150)]], sb=(90, 50))
G["]"] = dict(w=150, p=[[(0, 790), (150, 790), (150, -150), (0, -150)]], sb=(50, 90))
G["{"] = dict(w=200, p=[[(200, 790), (100, 790), (60, 750), (60, 380), (0, 320), (60, 260), (60, -110), (100, -150), (200, -150)]], sb=(80, 50))
G["}"] = dict(w=200, p=[[(0, 790), (100, 790), (140, 750), (140, 380), (200, 320), (140, 260), (140, -110), (100, -150), (0, -150)]], sb=(50, 80))
G["+"] = dict(w=420, p=[[(0, 330), (420, 330)], [(210, 120), (210, 540)]])
G["="] = dict(w=420, p=[[(0, 230), (420, 230)], [(0, 430), (420, 430)]])
G["&"] = dict(w=560, p=[[(560, 0), (130, 430), (130, 620), (210, 700), (350, 700), (430, 620), (430, 500),
                         (0, 260), (0, c), (c, 0), (330, 0), (560, 230)]])
G["#"] = dict(w=540, p=[[(170, 40), (170, 660)], [(370, 40), (370, 660)], [(0, 240), (540, 240)], [(0, 460), (540, 460)]])
G["@"] = dict(w=620, p=[[(430, 200), (430, 480), (220, 480), (160, 420), (160, 200), (620, 200),
                         (620, 700 - C), (620 - C, 700), (C, 700), (0, 700 - C), (0, C), (C, 0), (560, 0)]])
G["%"] = dict(w=560, p=[octa(0, 440, 180, 700, 40), octa(380, 0, 560, 260, 40), [(60, 0), (500, 700)]])
G["*"] = dict(w=380, p=[[(190, 300), (190, 700)], [(0, 400), (380, 600)], [(0, 600), (380, 400)]])
G["<"] = dict(w=380, p=[[(380, 590), (0, 330), (380, 70)]])
G[">"] = dict(w=380, p=[[(0, 590), (380, 330), (0, 70)]])
G["|"] = dict(w=0, p=[[(0, -150), (0, 790)]], sb=(110, 110))
G["~"] = dict(w=520, p=[[(0, 270), (110, 380), (210, 380), (310, 280), (410, 280), (520, 390)]])
G["^"] = dict(w=420, p=[[(0, 450), (210, 700), (420, 450)]])
G["$"] = dict(w=540, p=G["S"]["p"] + [[(270, 790), (270, 700)], [(270, 0), (270, -90)]])
G["×"] = dict(w=400, p=[[(0, 130), (400, 530)], [(0, 530), (400, 130)]])           # ×
G["·"] = dict(w=0, d=[(0, 330)], sb=(90, 90))                                        # ·
G["•"] = dict(w=0, f=[octa(-80, 250, 80, 410, 45)], sb=(140, 140))                   # •
G["●"] = dict(w=0, f=[octa(-230, 100, 230, 560, 130)], sb=(310, 310))               # ●
G["–"] = dict(w=500, p=[[(0, 330), (500, 330)]])                                   # –
G["—"] = dict(w=860, p=[[(0, 330), (860, 330)]], sb=(40, 40))                      # —
G["→"] = dict(w=640, p=[[(0, 330), (640, 330)], [(430, 540), (640, 330), (430, 120)]])  # →
G["←"] = dict(w=640, p=[[(640, 330), (0, 330)], [(210, 540), (0, 330), (210, 120)]])    # ←
G["↑"] = dict(w=420, p=[[(210, -60), (210, 760)], [(0, 550), (210, 760), (420, 550)]])  # ↑
G["↓"] = dict(w=420, p=[[(210, 760), (210, -60)], [(0, 150), (210, -60), (420, 150)]])  # ↓
G["▶"] = dict(w=420, f=[[(0, 90), (420, 330), (0, 570)]], sb=(110, 110))           # ▶
G["°"] = dict(w=200, p=[octa(0, 500, 200, 700, 60)])                               # °

# 小寫字母直接對應到大寫字形 (HUD 風格全大寫)
LOWER_TO_UPPER = True

GLYPH_NAMES = {
    " ": "space", ".": "period", ",": "comma", ":": "colon", ";": "semicolon", "!": "exclam",
    "?": "question", "'": "quotesingle", '"': "quotedbl", "`": "grave", "-": "hyphen",
    "_": "underscore", "/": "slash", "\\": "backslash", "(": "parenleft", ")": "parenright",
    "[": "bracketleft", "]": "bracketright", "{": "braceleft", "}": "braceright", "+": "plus",
    "=": "equal", "&": "ampersand", "#": "numbersign", "@": "at", "%": "percent", "*": "asterisk",
    "<": "less", ">": "greater", "|": "bar", "~": "asciitilde", "^": "asciicircum", "$": "dollar",
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five", "6": "six",
    "7": "seven", "8": "eight", "9": "nine",
    "×": "multiply", "·": "periodcentered", "•": "bullet", "●": "uni25CF",
    "–": "endash", "—": "emdash", "→": "arrowright", "←": "arrowleft",
    "↑": "arrowup", "↓": "arrowdown", "▶": "uni25B6", "°": "degree",
}

# 簡單的字距微調 (kerning)：(左, 右): 調整量
KERN = {
    ("L", "T"): -110, ("L", "V"): -90, ("L", "Y"): -90, ("L", "W"): -60,
    ("T", "A"): -60, ("A", "T"): -60, ("A", "V"): -70, ("V", "A"): -70,
    ("A", "Y"): -60, ("Y", "A"): -60, ("A", "W"): -40, ("W", "A"): -40,
    ("P", "A"): -50, ("F", "A"): -40, ("T", "period"): -90, ("T", "comma"): -90,
    ("V", "period"): -90, ("V", "comma"): -90, ("Y", "period"): -80, ("P", "period"): -80,
    ("F", "period"): -80, ("W", "period"): -60, ("seven", "period"): -60,
    ("V", "four"): -50, ("one", "V"): -20, ("V", "one"): -20, ("T", "Y"): 0,
    ("L", "quotesingle"): -80, ("L", "quotedbl"): -80, ("Y", "O"): -20, ("O", "Y"): -20,
    ("P", "comma"): -80, ("Y", "comma"): -80, ("W", "comma"): -60,
}


# ----------------------------------------------------------------------------
# 幾何處理
# ----------------------------------------------------------------------------
def make_mapper(s):
    """骨架座標 -> 字型座標：y 依線寬縮放，讓外緣剛好落在 0..CAP。"""
    ky = (CAP - s) / CAP

    def m(pt):
        x, y = pt
        return (x + s / 2.0, s / 2.0 + y * ky)
    return m


def dot_size(s):
    return max(round(s * 1.75), 95)


def build_shape(spec, s):
    m = make_mapper(s)
    half = s / 2.0
    parts = []
    clip_parts = []
    for line in spec.get("p", []):
        pts = [m(p) for p in line]
        closed = len(pts) > 2 and pts[0] == pts[-1]
        if closed:
            poly = Polygon(pts)
            outer = poly.buffer(half, join_style="mitre", mitre_limit=3.0)
            inner = poly.buffer(-half, join_style="mitre", mitre_limit=3.0)
            g = outer.difference(inner)
        else:
            g = LineString(pts).buffer(half, cap_style="square", join_style="mitre", mitre_limit=2.0)
        parts.append(g)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        clip_parts.append(box(min(xs) - half, min(ys) - half, max(xs) + half, max(ys) + half))
    d = dot_size(s)
    for (x, y) in spec.get("d", []):
        cx = x + s / 2.0
        cy = d / 2.0 if y == 0 else m((x, y))[1]
        b = box(cx - d / 2, cy - d / 2, cx + d / 2, cy + d / 2)
        parts.append(b)
        clip_parts.append(b)
    for (x, y) in spec.get("comma", []):
        # 逗號 = 基線方點 + 往左下斜的尾巴 (一個實心多邊形)
        x0 = x + s / 2.0 - d / 2
        pg = Polygon([(x0, d), (x0 + d, d), (x0 + d, 0), (x0 + 0.35 * d, -1.25 * d),
                      (x0 - 0.2 * d, -1.25 * d), (x0, -0.2 * d)])
        parts.append(pg)
        clip_parts.append(pg.buffer(1))
    for poly in spec.get("f", []):
        pg = Polygon([m(p) for p in poly])
        parts.append(pg)
        clip_parts.append(pg.buffer(1))
    if not parts:
        return None
    shape = unary_union(parts)
    # 斜線端點的方形筆帽會凸出去；裁切到各筆畫外框的聯集
    shape = shape.intersection(unary_union(clip_parts))
    shape = set_precision(shape, 1.0)
    return shape


def polygons_of(geom):
    if geom is None or geom.is_empty:
        return []
    if isinstance(geom, Polygon):
        return [geom]
    out = []
    for g in getattr(geom, "geoms", []):
        out.extend(polygons_of(g))
    return out


def draw(pen, geom, ps_dir, dx):
    """ps_dir=True: 外框逆時針 (CFF)；False: 外框順時針 (TrueType)。"""
    for poly in polygons_of(geom):
        poly = orient(poly, sign=1.0 if ps_dir else -1.0)
        for ring in [poly.exterior] + list(poly.interiors):
            coords = list(ring.coords)[:-1]
            # 去除共線點
            clean = []
            n = len(coords)
            for i in range(n):
                a, b, cc = coords[i - 1], coords[i], coords[(i + 1) % n]
                cross = (b[0] - a[0]) * (cc[1] - b[1]) - (b[1] - a[1]) * (cc[0] - b[0])
                if abs(cross) > 1e-6:
                    clean.append(b)
            if len(clean) < 3:
                continue
            pen.moveTo((int(round(clean[0][0] + dx)), int(round(clean[0][1]))))
            for p in clean[1:]:
                pen.lineTo((int(round(p[0] + dx)), int(round(p[1]))))
            pen.closePath()


# ----------------------------------------------------------------------------
# 建立字型
# ----------------------------------------------------------------------------
def build(weight, out_dir):
    s, wclass = WEIGHTS[weight]
    order = [".notdef"]
    cmap = {}
    shapes = {}
    metrics = {}

    names = {}
    for ch in G:
        names[ch] = GLYPH_NAMES.get(ch, ch)
    for ch, spec in G.items():
        gn = names[ch]
        order.append(gn)
        cmap[ord(ch)] = gn
        if "adv" in spec:
            shapes[gn] = None
            metrics[gn] = (spec["adv"], 0)
            continue
        shape = build_shape(spec, s)
        lsb, rsb = spec.get("sb", (SB, SB))
        minx = shape.bounds[0]
        maxx = shape.bounds[2]
        dx = lsb - minx
        adv = int(round(maxx - minx + lsb + rsb))
        shapes[gn] = (shape, dx)
        metrics[gn] = (adv, int(round(lsb)))
    if LOWER_TO_UPPER:
        for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            cmap[ord(ch.lower())] = ch
    cmap[0x00A0] = "space"
    cmap[0x2027] = "periodcentered"   # 中文間隔號 ‧
    cmap[0x30FB] = "periodcentered"   # ・

    # .notdef: 空心方框
    nd = box(60, 0, 540, CAP).difference(box(60 + s, s, 540 - s, CAP - s))
    shapes[".notdef"] = (nd, 0)
    metrics[".notdef"] = (600, 60)

    psname = FAMILY.replace(" ", "") + "-" + weight
    name_table = dict(
        familyName=FAMILY, styleName=weight, uniqueFontIdentifier=f"{psname};{VERSION}",
        fullName=f"{FAMILY} {weight}", psName=psname, version=f"Version {VERSION}",
        copyright="Copyright (c) 2026 the WIREFRAMECH project. Original design.",
        designer="WIREFRAMECH team (generated with generate_font.py)",
        description="Original monoline chamfered HUD display face for WIREFRAMECH 鋼弦機兵.",
    )

    results = {}
    for flavor in ("ttf", "otf"):
        fb = FontBuilder(UPM, isTTF=(flavor == "ttf"))
        fb.setupGlyphOrder(order)
        fb.setupCharacterMap(cmap)
        if flavor == "ttf":
            glyphs = {}
            for gn in order:
                pen = TTGlyphPen(None)
                if shapes[gn] is not None:
                    draw(pen, shapes[gn][0], False, shapes[gn][1])
                glyphs[gn] = pen.glyph()
            fb.setupGlyf(glyphs)
        else:
            charstrings = {}
            for gn in order:
                pen = T2CharStringPen(metrics[gn][0], None)
                if shapes[gn] is not None:
                    draw(pen, shapes[gn][0], True, shapes[gn][1])
                charstrings[gn] = pen.getCharString()
            fb.setupCFF(psname, {"FullName": f"{FAMILY} {weight}", "FamilyName": FAMILY,
                                 "Weight": weight}, charstrings, {})
        fb.setupHorizontalMetrics(metrics)
        fb.setupHorizontalHeader(ascent=ASC, descent=DESC, lineGap=0)
        fb.setupNameTable(name_table)
        fb.setupOS2(
            sTypoAscender=ASC, sTypoDescender=DESC, sTypoLineGap=0,
            usWinAscent=ASC, usWinDescent=-DESC, sxHeight=CAP, sCapHeight=CAP,
            usWeightClass=wclass, achVendID="WFMC", fsType=0,
            fsSelection=0x40 | 0x80,  # REGULAR + USE_TYPO_METRICS
            version=4,
        )
        fb.setupPost(isFixedPitch=0, underlinePosition=-120, underlineThickness=s)
        fb.setupHead(unitsPerEm=UPM, fontRevision=float(VERSION),
                     created=timestampFromString("Mon Nov 23 00:00:00 2026"),
                     modified=timestampFromString("Mon Nov 23 00:00:00 2026"))
        # kerning (GPOS)
        fea = ["languagesystem DFLT dflt;", "languagesystem latn dflt;", "feature kern {"]
        for (a, b), v in KERN.items():
            for la in {a, a.lower()} if len(a) == 1 else {a}:
                for lb in {b, b.lower()} if len(b) == 1 else {b}:
                    ga = la.upper() if len(la) == 1 else la
                    gb = lb.upper() if len(lb) == 1 else lb
                    fea.append(f"  pos {ga} {gb} {v};")
        fea.append("} kern;")
        fea_txt = "\n".join(dict.fromkeys(fea))  # 去除重複
        fb.addOpenTypeFeatures(fea_txt)
        path = os.path.join(out_dir, f"{psname}.{flavor}")
        fb.save(path)
        results[flavor] = path
        if flavor == "ttf":
            f = TTFont(path)
            f.flavor = "woff2"
            w2 = os.path.join(out_dir, f"{psname}.woff2")
            f.save(w2)
            results["woff2"] = w2
    return results


def main():
    ap = argparse.ArgumentParser(description="Generate Wireframech Line fonts")
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--weights", nargs="*", default=list(WEIGHTS))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for w in a.weights:
        r = build(w, a.out)
        for k, v in r.items():
            print(f"[{w}] {k}: {v}")


if __name__ == "__main__":
    main()
