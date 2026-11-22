#!/usr/bin/env python3
"""The Sunday World -- one-page newspaper summing up the world news of
Sunday 22 November 2026. Draws the whole page with the Python standard
library only (no network, no fonts on disk) and writes entry.png.

Layout: masthead, lead story, then three columns of 13 stories each
(40 stories in total). Deterministic: same input, same bytes.
"""

import os
import struct
import zlib

W = 1024
H = 1024

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GREY = (90, 90, 90)
RED = (178, 34, 34)
LIGHT = (238, 238, 235)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, "1" = ink. Uppercase, digits and punctuation.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    ":": ("00000", "01100", "00000", "00000", "00000", "01100", "00000"),
    ";": ("00000", "01100", "00000", "00000", "01100", "00100", "01000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
}

CLEAN = {
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u00b7": ".", "\u00e9": "E",
    "\u00e8": "E", "\u00fc": "U", "\u00f6": "O", "\u00e4": "A",
    "\u00df": "S", "\u00a3": "L", "\u20ac": "E", "\u2011": "-",
}


def clean(text):
    out = []
    for ch in text.upper():
        out.append(CLEAN.get(ch, ch))
    return "".join(out)


# ------------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h):
        self.w = w
        self.h = h
        self.px = bytearray([255, 255, 255]) * (w * h)

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x, y, w, color, thick=1):
        self.rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.rect(x, y, thick, h, color)

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, color, thick=2):
        for yy in range(cy - r - 1, cy + r + 2):
            for xx in range(cx - r - 1, cx + r + 2):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if abs(d - r) <= thick / 2.0:
                    self.set(xx, yy, color)

    def text_width(self, text, scale):
        return len(clean(text)) * 6 * scale - scale

    def draw_text(self, x, y, text, scale, color):
        """Draw text at top-left (x, y). Returns width in px."""
        text = clean(text)
        cx = x
        for ch in text:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == "1":
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx - x - scale

    def text_center(self, y, text, scale, color, cx=512):
        w = self.text_width(text, scale)
        self.draw_text(cx - w // 2, y, text, scale, color)
        return w


def wrap(text, max_width, scale):
    """Greedy word wrap. Returns list of lines (cleaned text)."""
    text = clean(text)
    char_w = 6 * scale
    max_chars = max(1, (max_width + scale) // char_w)
    lines = []
    for para in text.split("\n"):
        words = para.split()
        cur = ""
        for word in words:
            trial = (cur + " " + word).strip()
            if len(trial) <= max_chars:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                while len(word) > max_chars:
                    lines.append(word[:max_chars])
                    word = word[max_chars:]
                cur = word
        if cur:
            lines.append(cur)
    return lines


def draw_block(cv, x, y, width, headline, standfirst, h_scale=2,
               s_scale=1, head_color=BLACK, max_head_lines=2,
               max_stand_lines=2):
    """One story: headline + standfirst. Returns height used."""
    lines = wrap(headline, width, h_scale)[:max_head_lines]
    yy = y
    for line in lines:
        cv.draw_text(x, yy, line, h_scale, head_color)
        yy += 7 * h_scale + 1
    yy += 1
    slines = wrap(standfirst, width, s_scale)[:max_stand_lines]
    for line in slines:
        cv.draw_text(x, yy, line, s_scale, GREY)
        yy += 7 * s_scale + 1
    return yy - y


# ---------------------------------------------------------------- PNG encode
def png_bytes(cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * stride:(y + 1) * stride]

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))

# ------------------------------------------------------------------ stories
# 40 real stories of Sunday 22 November 2026, as reported that day.
# (headline, standfirst). Headlines are the paper's own wording of the
# reported facts; figures are the ones reported on the day.

LEAD = (
    "COP31 ON THE BRINK AS FINAL DRAFT DROPS FOSSIL FUELS",
    "Talks in Antalya run into a second day of overtime after a draft "
    "deal published early on Sunday mentions neither fossil fuels nor a "
    "phase-out. Nearly 200 nations must agree by consensus.",
)

# Three columns of 13 stories each.
COLUMNS = [
    ("WAR AND DIPLOMACY", [
        ("IRAN STRIKES BAHRAIN, HITS FACTORY",
         "Tehran says it hit US bases at Al-Riffa and Awali; a civilian "
         "site burns, with no injuries reported."),
        ("THREE HOUTHI MISSILES DOWNED OVER RIYADH",
         "The Saudi-led coalition downs the missiles aimed at the "
         "capital; eight alerts go out in 24 hours."),
        ("BURNING RUSSIAN SHIP STILL ADRIFT OFF FINLAND",
         "The Sparta II, hit by drones in the Gulf of Finland, keeps "
         "burning as Finnish crews fight the fire."),
        ("RUSSIA HITS ZELENSKY'S HOME TOWN",
         "A missile strike on Kryvyi Rih kills two and wounds dozens; "
         "Ukraine says it hit a Russian ship."),
        ("ISRAELI STRIKES GO ON IN GAZA",
         "Strikes continue across the Strip and an aid vehicle is hit, "
         "as the ceasefire frays further."),
        ("TRUMP, XI AND PUTIN MEET IN SHENZHEN",
         "The three leaders hold a trilateral summit in China and agree "
         "to begin talks on reducing nuclear risks."),
        ("DENMARK EXPELS RUSSIAN ATTACHE",
         "Copenhagen orders the diplomat out over an alleged plot, the "
         "latest flare-up on NATO's northern flank."),
        ("IRAN STARTS RATIONING ELECTRICITY",
         "Power cuts bite as the war with the US and Israel damages the "
         "energy network, Tehran says."),
        ("HORMUZ REOPENING 'NOT DIFFICULT'",
         "Iran's foreign minister says the strait can reopen if the US "
         "accepts Tehran's conditions."),
        ("MEXICO CAPTURES 'EL CHAPO ISIDRO'",
         "Cartel boss Fausto Isidro Meza Flores is held in Sinaloa; "
         "11 die in the violence that follows."),
        ("EU AND INDONESIA SIGN TRADE DEAL",
         "After ten years of talks, Brussels and Jakarta sign a pact "
         "covering goods, services and investment."),
        ("EU PLASTIC WASTE BAN TAKES EFFECT",
         "Exports of plastic scrap to non-OECD states stop, rerouting "
         "735,000 tonnes a year."),
        ("NEPAL PM HEADS TO INDIA FOR TALKS",
         "Balendra Shah begins a two-day state visit to meet Narendra "
         "Modi in New Delhi."),
    ]),
    ("POLITICS AND MONEY", [
        ("INDIA AND CHINA HOLD BORDER TALKS",
         "Commanders conclude a fresh round of talks over tensions "
         "along the Arunachal frontier."),
        ("CRIMEA BRIDGE STRIKES SPARK FUEL RUSH",
         "Petrol sales are restricted in Sevastopol after strikes on "
         "the bridge set off queues for fuel."),
        ("KYIV HOMES ABLAZE IN OVERNIGHT RAID",
         "A Russian missile assault sets homes alight in the capital "
         "as explosions rock the city."),
        ("QATAR ENVOY VISITS TEHRAN",
         "Doha sends a representative to Iran for talks as Gulf "
         "tensions keep climbing."),
        ("LEBANON RETHINKS HEZBOLLAH STRATEGY",
         "Beirut weighs moving from coexistence to reasserting state "
         "control over the armed group."),
        ("ROHINGYA: A LONG WAY HOME",
         "After the world court's genocide ruling, refugees face a "
         "slow road back to Myanmar."),
        ("EX-ISRAELI PM BACKS EISENKOT",
         "A former prime minister backs Gadi Eisenkot for the top job "
         "and rules out serving with Netanyahu."),
        ("BAGHDAD WEIGHS OIL-SMUGGLING ARRESTS",
         "Iraqi authorities do not rule out detentions in the "
         "oil-smuggling case, officials say."),
        ("SEVEN KILLED IN PAKISTAN FEUD",
         "A community dispute over forest ownership turns into a "
         "gunfight that leaves seven dead."),
        ("PALESTINIANS STILL OUTSIDERS IN EGYPT",
         "Generations of Egypt-born Palestinians are still denied a "
         "normal life, a report finds."),
        ("WHO WARNS ON ANTIBIOTIC RESISTANCE",
         "The health agency warns that drug-resistant infections are "
         "spreading faster than new treatments."),
        ("US STOCKS FALL INTO CORRECTION",
         "The Dow and S&P 500 slide into correction territory as an "
         "AI sell-off rattles world markets."),
        ("AMAZON NEARS $7.5BN AI DEAL",
         "Amazon is close to buying Israeli AI start-up Decart to "
         "boost its Trainium chips, reports say."),
    ]),
    ("TECH AND SPORT", [
        ("IBM UNVEILS 520-QUBIT CHIP",
         "The 'Nighthawk r3' quantum processor is aimed at real "
         "workloads, IBM says, not breaking codes."),
        ("TRUMP CONFIRMS FBI DATABASE BREACH",
         "The president confirms a breach of the FBI's NCIC system "
         "of fingerprints and wanted records."),
        ("GTA 6 SETS $3.79BN LAUNCH RECORD",
         "Grand Theft Auto VI takes an estimated $3.79 billion on "
         "its first day, a record for a game debut."),
        ("APPLE BLACK FRIDAY DEALS ROLL OUT",
         "Discounts land on AirPods, watches and MacBooks as the "
         "holiday shopping season opens."),
        ("LEEDS STUN CHELSEA 4-1",
         "Leeds come from behind at Stamford Bridge for their first "
         "win there since 1999; Okafor scores twice."),
        ("ARSENAL HELD 2-2 AT NEWCASTLE",
         "Madueke rescues a point for the leaders after Barnes and "
         "Thiaw turn the game; Raya goes off injured."),
        ("MAN CITY DRAW 1-1 WITH FULHAM",
         "City's winless league run stretches to four games as "
         "Fulham hold them at the Etihad."),
        ("SPURS BEAT IPSWICH 2-0",
         "Teenager Williams-Barnett stars on his first league start "
         "as Tottenham win at Portman Road."),
        ("BOURNEMOUTH BEAT FOREST 2-0",
         "The Cherries make it nine straight wins in all "
         "competitions with victory over Forest."),
        ("COVENTRY 3-2 CRYSTAL PALACE",
         "Thomas Frank loses his first game in charge of Palace as "
         "a late own goal settles a thriller."),
        ("INDIA DECLARE ON 720-9 IN WELLINGTON",
         "India pile up 720 for 9 against New Zealand and take a "
         "352-run lead in the first Test."),
        ("REAL MADRID COME BACK TO WIN 2-1",
         "Real recover from a goal down to beat Celta Vigo and "
         "stretch their winning run to nine games."),
        ("CHAHAL JOINS THE BJP",
         "Cricketer Yuzvendra Chahal joins India's ruling party and "
         "takes a role in its OBC Morcha wing."),
    ]),
]


# ------------------------------------------------------------------ layout
def draw_globe(cv, cx, cy, r):
    cv.ring(cx, cy, r, BLACK, 3)
    # latitude lines
    for k in range(-2, 3):
        yy = cy + k * r // 3
        half = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) < r else 0
        if half:
            cv.hline(cx - half, yy, 2 * half, GREY, 1)
    # longitude ellipse
    for yy in range(cy - r, cy + r + 1):
        dx = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) < r else 0
        if dx:
            xoff = dx // 2
            cv.set(cx - xoff, yy, GREY)
            cv.set(cx + xoff, yy, GREY)
    cv.vline(cx, cy - r, 2 * r, GREY, 1)


def build():
    cv = Canvas(W, H)
    mx = 24                      # side margin
    cw = W - 2 * mx              # content width

    # ---- masthead
    cv.hline(mx, 14, cw, BLACK, 3)
    cv.text_center(26, "THE SUNDAY WORLD", 6, BLACK)
    cv.text_center(76, "SUNDAY 22 NOVEMBER 2026", 2, RED)
    cv.text_center(94, "ONE DAY. THE WHOLE WORLD. FORTY STORIES.",
                   1, GREY)
    cv.hline(mx, 112, cw, BLACK, 2)
    cv.hline(mx, 116, cw, BLACK, 1)

    # ---- lead story with a small globe
    ly = 130
    cv.draw_text(mx, ly, "CLIMATE", 1, RED)
    cv.hline(mx + 62, ly + 4, cw - 62, RED, 1)
    ly += 16
    lead_w = cw - 150
    lines = wrap(LEAD[0], lead_w, 3)[:3]
    yy = ly
    for line in lines:
        cv.draw_text(mx, yy, line, 3, BLACK)
        yy += 7 * 3 + 3
    yy += 2
    slines = wrap(LEAD[1], lead_w, 2)[:3]
    for line in slines:
        cv.draw_text(mx, yy, line, 2, GREY)
        yy += 7 * 2 + 3
    draw_globe(cv, W - mx - 62, ly + 56, 50)
    cv.text_center(ly + 112, "ANTALYA, TURKEY", 1, GREY,
                   cx=W - mx - 62)
    lead_bottom = max(yy, ly + 130)
    cv.hline(mx, lead_bottom + 8, cw, BLACK, 2)

    # ---- three columns
    top = lead_bottom + 26
    col_w = (cw - 2 * 20) // 3
    col_x = [mx, mx + col_w + 20, mx + 2 * (col_w + 20)]
    # section headers
    for i, (title, _) in enumerate(COLUMNS):
        cv.draw_text(col_x[i], top, title, 1, RED)
        cv.hline(col_x[i], top + 11, col_w, RED, 1)
    y = top + 20
    col_y = [y, y, y]
    for i, (_, stories) in enumerate(COLUMNS):
        yy = y
        for headline, standfirst in stories:
            used = draw_block(cv, col_x[i], yy, col_w, headline,
                              standfirst)
            yy += used + 2
            cv.hline(col_x[i], yy, col_w, LIGHT, 1)
            yy += 2
        col_y[i] = yy
    bottom = max(col_y)

    # ---- footer
    fy = H - 26
    cv.hline(mx, fy - 8, cw, BLACK, 2)
    cv.text_center(fy + 2,
                   "THE SUNDAY WORLD - SUNDAY 22 NOVEMBER 2026 - "
                   "40 STORIES FROM ONE DAY - NO. 1",
                   1, GREY)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = build()
    data = png_bytes(cv)
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    main()
