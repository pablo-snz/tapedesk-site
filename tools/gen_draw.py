"""Dibuja las pantallas de TapeDesk y la curva del EQ para la web."""
import math
import re
import sys

INK = "#141412"
BODY = "#D6D7D3"
PAPER = "#F6F5F1"
LANE = "#EAE8E3"
SUBTLE = "#C8C8C3"
GREY = "#6F6F6F"
REC = "#E84D1F"
TRK = ["#375E80", "#A35B3D", "#7A8A5A", "#8E5060", "#487957", "#7D517F"]
GRAB = ["#46619E", "#B0545C", "#6E8C46", "#7B55A0"]
MOTOR = "#4A4F78"
TOUCH = "#47703C"
METER = "#6F9442"

SX0, SX1 = 9, 191
SW = SX1 - SX0
CLAY = "#AE705C"
LOOPBAND = "#E9DFDA"
RECIDLE = "#A37871"
STARTGREY = "#8C8C88"
FAMILY = "#4A42A6"
PIECE = "#FDFCF9"
TINT = ["#D8DDE3", "#EADBD3", "#E3E6DA", "#E8DADF"]


def t(x, y, s, size=6.5, fill=INK, anchor="start", cls="mono", extra="", weight=None):
    w = f' font-weight="{weight}"' if weight else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" class="{cls}"{w}{extra}>{s}</text>')


def line(x1, y1, x2, y2, stroke=INK, w=1, extra=""):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="{w}" stroke-linecap="round"{extra}/>'


def rect(x, y, w, h, fill="none", stroke=INK, sw=1, rx=0, extra=""):
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{extra}/>')


def circ(cx, cy, r, fill="none", stroke=INK, sw=1):
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def path(d, stroke=INK, w=1.2, fill="none"):
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>'


def star(cx, cy, r):
    return (f'<path d="M{cx:.1f} {cy-r:.1f} Q{cx:.1f} {cy:.1f} {cx+r:.1f} {cy:.1f} Q{cx:.1f} {cy:.1f} {cx:.1f} {cy+r:.1f} '
            f'Q{cx:.1f} {cy:.1f} {cx-r:.1f} {cy:.1f} Q{cx:.1f} {cy:.1f} {cx:.1f} {cy-r:.1f}Z" fill="{INK}"/>')


def sine(cx, cy, w, amp, cycles=1.0):
    pts = []
    for i in range(25):
        x = cx - w / 2 + w * i / 24
        pts.append(f"{'M' if i == 0 else 'L'}{x:.1f} {cy - amp * math.sin(i / 24 * 2 * math.pi * cycles):.1f}")
    return " ".join(pts)


def status_and_header():
    out = [t(30, 22, "9:41", size=6.6, cls="sans", weight=500),
           rect(160, 17.5, 11, 5.5, stroke=INK, sw=0.8, rx=1.4),
           rect(161.2, 18.7, 7, 3.1, fill="#5FA04A", stroke="none", sw=0, rx=0.8)]
    y0, y1 = 32, 58
    widths = [45.5, 45.5, 45.5, 22.75, 22.75]
    xs = [SX0]
    for w in widths[:-1]:
        xs.append(xs[-1] + w)
    out.append(line(SX0, y0, SX1, y0, w=1))
    cells = [("project", "tape_009"), ("timecode", "1.1.1"), ("speed", "+1.00x")]
    for (lab, val), x in zip(cells, xs):
        out.append(t(x + 4, 40.5, lab, size=4.6, fill=GREY, cls="sans"))
        out.append(t(x + 4, 52, val, size=7))
    for x in xs[1:]:
        out.append(line(x, y0, x, y1, w=0.9))
    ex = xs[3] + widths[3] / 2
    out.append(f'<path d="M{ex-4:.1f} {46:.1f} L{ex:.1f} {41:.1f} L{ex+4:.1f} {46:.1f}Z" fill="{INK}"/>')
    out.append(rect(ex - 4, 47.4, 8, 1.8, fill=INK, stroke="none", sw=0))
    gx, gy = xs[4] + widths[4] / 2, 45
    out.append(circ(gx, gy, 3.6, sw=1))
    for k in range(8):
        a = k * math.pi / 4
        out.append(line(gx + 3.6 * math.cos(a), gy + 3.6 * math.sin(a),
                        gx + 5.4 * math.cos(a), gy + 5.4 * math.sin(a), w=1.3))
    out.append(line(SX0, y1, SX1, y1, w=1.2))
    return out


def transport():
    out = []
    y0, y1 = 356, 390
    w = SW / 5
    out.append(line(SX0, y0, SX1, y0, w=1.2))
    out.append(line(SX0, y1, SX1, y1, w=1.2))
    for i, lab in enumerate(["rew", "stop", "start", "rec", "loop"]):
        x = SX0 + i * w
        cx, gy = x + w / 2, 368
        if i:
            out.append(line(x, y0, x, y1, w=0.9))
        col = {"start": STARTGREY, "rec": RECIDLE, "loop": CLAY}.get(lab, INK)
        if lab == "rew":
            out.append(f'<path d="M{cx:.1f} {gy-4} L{cx-5:.1f} {gy} L{cx:.1f} {gy+4}Z M{cx+5:.1f} {gy-4} L{cx:.1f} {gy} L{cx+5:.1f} {gy+4}Z" fill="{INK}"/>')
        elif lab == "stop":
            out.append(rect(cx - 3.8, gy - 3.8, 7.6, 7.6, fill=INK, stroke="none", sw=0, rx=1))
        elif lab == "start":
            out.append(f'<path d="M{cx-3:.1f} {gy-4.5} L{cx+4.5:.1f} {gy} L{cx-3:.1f} {gy+4.5}Z" fill="{STARTGREY}"/>')
        elif lab == "rec":
            out.append(circ(cx, gy, 4.8, fill=RECIDLE, stroke="none", sw=0))
        else:
            d = (f"M{cx:.1f} {gy} C{cx-2:.1f} {gy-4} {cx-7:.1f} {gy-4} {cx-7:.1f} {gy} C{cx-7:.1f} {gy+4} {cx-2:.1f} {gy+4} {cx:.1f} {gy} "
                 f"C{cx+2:.1f} {gy-4} {cx+7:.1f} {gy-4} {cx+7:.1f} {gy} C{cx+7:.1f} {gy+4} {cx+2:.1f} {gy+4} {cx:.1f} {gy}Z")
            out.append(path(d, stroke=CLAY, w=1.5))
        out.append(t(cx, 383, lab, size=5.4, fill=col, anchor="middle"))
    return out


def places(active):
    out = []
    w = SW / 4
    for i, lab in enumerate(["synth", "track", "tape", "mix"]):
        cx = SX0 + i * w + w / 2
        out.append(t(cx, 405, lab, size=6, fill=INK if i == active else GREY, anchor="middle"))
        if i == active:
            half = len(lab) * 1.85
            out.append(rect(cx - half, 408.5, 2 * half, 1.6, fill=INK, stroke="none", sw=0))
    return out


def tab_glyph(kind, cx, cy, col):
    if kind == "synth":
        return path(sine(cx, cy, 12, 1.6, 2), stroke=col, w=1.1)
    if kind == "adsr":
        return path(f"M{cx-6:.1f} {cy+3:.1f} Q{cx-4:.1f} {cy-4:.1f} {cx-2:.1f} {cy-3:.1f} L{cx+2:.1f} {cy+1:.1f} L{cx+4:.1f} {cy+1:.1f} L{cx+6:.1f} {cy+3:.1f}", stroke=col, w=1.1)
    if kind == "filter":
        return path(f"M{cx-6:.1f} {cy-2:.1f} L{cx+1:.1f} {cy-2:.1f} Q{cx+5:.1f} {cy-2:.1f} {cx+6:.1f} {cy+3:.1f}", stroke=col, w=1.1)
    if kind == "lfo":
        return path(sine(cx, cy, 12, 2.2, 1), stroke=col, w=1.1)
    if kind == "fx":
        return "".join(line(cx + 4 * math.cos(a), cy + 4 * math.sin(a), cx - 4 * math.cos(a), cy - 4 * math.sin(a), stroke=col, w=1.1)
                       for a in (0, math.pi / 3, 2 * math.pi / 3))
    if kind == "keys":
        return rect(cx - 5, cy - 3, 10, 6, stroke=col, sw=1, rx=1) + "".join(
            line(cx - 5 + k * 2.5, cy - 3, cx - 5 + k * 2.5, cy + 1, stroke=col, w=0.8) for k in (1, 2, 3))
    if kind == "chords":
        return "".join(circ(cx, cy - 3 + k * 2.6, 1.3, fill=col, stroke="none", sw=0) for k in range(3))
    if kind == "seq":
        return "".join(rect(cx - 5 + c * 3.6, cy - 3 + r * 3.6, 2.6, 2.6, stroke=col, sw=0.7, rx=0.4)
                       for r in range(2) for c in range(3))
    return ""


def tab_row(y0, y1, labels, active, accent, colors, glyphs=None, size=5.6):
    out = []
    w = SW / len(labels)
    for i, lab in enumerate(labels):
        x = SX0 + i * w
        on = i == active
        out.append(rect(x, y0, w, y1 - y0, fill=PIECE if on else LANE, stroke="none", sw=0))
        col = INK if on else colors[i]
        cx = x + w / 2
        if glyphs:
            out.append(tab_glyph(glyphs[i], cx, y0 + 6.5, col))
            out.append(t(cx, y1 - 3.5, lab, size=size, fill=col, anchor="middle"))
        else:
            out.append(t(cx, (y0 + y1) / 2 + 2.4, lab, size=size + 0.8, fill=col, anchor="middle"))
        if i:
            out.append(line(x, y0, x, y1, w=0.9))
    out.append(rect(SX0 + active * w, y1 - 2.2, w, 2.2, fill=accent, stroke="none", sw=0))
    out.append(line(SX0, y1, SX1, y1, w=1.1))
    return out


def lcg(seed):
    while True:
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        yield (seed % 1000) / 1000


def bars_dense(x0, x1, yc, h, col, seed=3):
    r = lcg(seed)
    out, x = [], x0 + 1.2
    while x < x1 - 1:
        hh = h * (0.78 + 0.22 * next(r))
        out.append(line(x, yc - hh / 2, x, yc + hh / 2, stroke=col, w=0.8))
        x += 1.6
    return out


def bars_bursts(x0, x1, yc, h, col, seed=5):
    r = lcg(seed)
    out, x = [], x0 + 1
    out.append(line(x0, yc, x1, yc, stroke=col, w=0.5, extra=' stroke-dasharray="1.2 1.2"'))
    while x < x1 - 2:
        n = 5 + int(next(r) * 8)
        for k in range(n):
            if x > x1 - 1:
                break
            hh = h * (0.7 + 0.3 * next(r))
            out.append(line(x, yc - hh / 2, x, yc + hh / 2, stroke=col, w=0.9))
            x += 1.5
        x += 6 + next(r) * 6
    return out


def bars_sparse(x0, x1, yc, h, col, seed=9):
    r = lcg(seed)
    out, x = [], x0 + 2
    out.append(line(x0, yc, x1, yc, stroke=col, w=0.5, extra=' stroke-dasharray="1.2 1.2"'))
    while x < x1 - 1:
        hh = h * (0.15 + 0.85 * next(r))
        out.append(line(x, yc - hh / 2, x, yc + hh / 2, stroke=col, w=1))
        x += 3.4
    return out


def loop_band(y0, y1, x0, x1):
    out = [rect(x0, y0, x1 - x0, y1 - y0, fill=LOOPBAND, stroke="none", sw=0)]
    for i, x in enumerate(range(int(SX0) + 2, int(SX1), 4)):
        out.append(line(x, y0, x, y0 + (1.8 if i % 5 else 3.5), stroke=GREY if i % 5 else INK, w=0.6))
    for lab, x in (("3", x0 + (x1 - x0) * 0.25), ("5", x0 + (x1 - x0) * 0.5), ("7", x0 + (x1 - x0) * 0.75)):
        out.append(t(x, y1 - 1.8, lab, size=5, fill=GREY, anchor="middle"))
    yc = (y0 + y1) / 2
    for x in (x0, x1):
        out.append(f'<rect x="{x-3:.1f}" y="{yc-3:.1f}" width="6" height="6" fill="{CLAY}" transform="rotate(45 {x:.1f} {yc:.1f})"/>')
    return out


def tool_square(x, y, kind):
    out = [rect(x, y, 16, 14, fill=PIECE, stroke=INK, sw=1, rx=2.5)]
    cx, cy = x + 8, y + 7
    if kind == "import":
        out.append(path(f"M{cx-3:.1f} {cy-4:.1f} L{cx+1.5:.1f} {cy-4:.1f} L{cx+3:.1f} {cy-2.5:.1f} L{cx+3:.1f} {cy+4:.1f} L{cx-3:.1f} {cy+4:.1f}Z", w=0.9))
        out.append(path(f"M{cx:.1f} {cy-1.5:.1f} L{cx:.1f} {cy+2.2:.1f} M{cx-1.4:.1f} {cy+1:.1f} L{cx:.1f} {cy+2.2:.1f} L{cx+1.4:.1f} {cy+1:.1f}", w=0.8))
    elif kind == "cut":
        out += [circ(cx - 3.5, cy - 2, 1.4, sw=0.9), circ(cx - 3.5, cy + 2, 1.4, sw=0.9),
                line(cx - 2.2, cy - 1.4, cx + 4, cy + 1.6, w=0.9), line(cx - 2.2, cy + 1.4, cx + 4, cy - 1.6, w=0.9)]
    elif kind == "join":
        out.append(path(f"M{cx:.1f} {cy-4:.1f} L{cx:.1f} {cy+1:.1f} M{cx-3:.1f} {cy+4:.1f} L{cx:.1f} {cy+1:.1f} L{cx+3:.1f} {cy+4:.1f} M{cx-1.4:.1f} {cy-2.6:.1f} L{cx:.1f} {cy-4:.1f} L{cx+1.4:.1f} {cy-2.6:.1f}", w=0.9))
    elif kind == "trash":
        out.append(path(f"M{cx-3.5:.1f} {cy-2.5:.1f} L{cx+3.5:.1f} {cy-2.5:.1f} M{cx-2.6:.1f} {cy-2.5:.1f} L{cx-2:.1f} {cy+4:.1f} L{cx+2:.1f} {cy+4:.1f} L{cx+2.6:.1f} {cy-2.5:.1f} M{cx-1:.1f} {cy-4:.1f} L{cx+1:.1f} {cy-4:.1f}", w=0.9))
    return out


def tools_row(y, pill):
    out = [rect(13, y, 44, 14, fill=PIECE, stroke=INK, sw=1, rx=2.5)]
    if pill == "synth":
        out.append(tab_glyph("keys", 21, y + 7, TRK[0]))
        out.append(t(28, y + 9.3, "synth", size=5.6))
    else:
        for k, col in enumerate(["#C8C8C3", METER, METER]):
            out.append(circ(17, y + 3.5 + k * 3.5, 1.1, fill=col, stroke="none", sw=0))
        out.append(rect(22, y + 3, 3, 5, stroke=INK, sw=0.8, rx=1.5))
        out.append(line(23.5, y + 9, 23.5, y + 11, w=0.8))
        out.append(t(29, y + 9.3, "mic…", size=5.6))
    out += tool_square(61, y, "import")
    out += tool_square(129, y, "cut") + tool_square(151, y, "join") + tool_square(173, y, "trash")
    return out


def edit_bar(cx, y):
    out = []
    w = 22
    x0 = cx - 1.5 * w
    out.append(rect(x0, y, 3 * w, 18, fill=LANE, stroke=INK, sw=1, rx=2.5))
    for i, lab in enumerate(["lift", "rev", "loop"]):
        x = x0 + i * w
        c = x + w / 2
        if i:
            out.append(line(x, y, x, y + 18, w=0.8))
        if lab == "lift":
            out.append(path(f"M{c:.1f} {y+9:.1f} L{c:.1f} {y+3.5:.1f} M{c-2:.1f} {y+5.5:.1f} L{c:.1f} {y+3.5:.1f} L{c+2:.1f} {y+5.5:.1f}", w=0.9))
        elif lab == "rev":
            out.append(f'<path d="M{c+2:.1f} {y+3.5:.1f} L{c-2.5:.1f} {y+6.3:.1f} L{c+2:.1f} {y+9:.1f}Z" fill="{INK}"/>')
        else:
            out.append(path(f"M{c:.1f} {y+6.3:.1f} C{c-1:.1f} {y+4:.1f} {c-4.5:.1f} {y+4:.1f} {c-4.5:.1f} {y+6.3:.1f} C{c-4.5:.1f} {y+8.6:.1f} {c-1:.1f} {y+8.6:.1f} {c:.1f} {y+6.3:.1f} C{c+1:.1f} {y+4:.1f} {c+4.5:.1f} {y+4:.1f} {c+4.5:.1f} {y+6.3:.1f} C{c+4.5:.1f} {y+8.6:.1f} {c+1:.1f} {y+8.6:.1f} {c:.1f} {y+6.3:.1f}Z", w=0.9))
        out.append(t(c, y + 15.5, lab, size=4.8, anchor="middle"))
    return out


def overview(y0, lane_h):
    out = []
    kinds = [bars_dense, bars_bursts, bars_sparse, None]
    for i in range(4):
        y = y0 + i * lane_h
        out.append(rect(SX0, y, SW, lane_h, fill=PAPER if i % 2 == 0 else LANE, stroke="none", sw=0))
        out.append(line(SX0, y, SX1, y, stroke=SUBTLE, w=0.6))
        for k in range(4):
            out.append(circ(14, y + lane_h / 2 - 4.5 + k * 3, 0.9, fill="#BDBDB8", stroke="none", sw=0))
        if kinds[i]:
            out.append(rect(23, y + 3, 128, lane_h - 6, fill=TINT[i], stroke="none", sw=0))
            out += kinds[i](23, 151, y + lane_h / 2, lane_h - 10, TRK[i], seed=11 + i)
    out.append(line(22, y0 - 12, 22, y0 + 4 * lane_h, w=0.9))
    return out


def keyed_pad(x, y, w, h, on):
    return rect(x, y, w, h, fill=INK if on else PIECE, stroke=INK, sw=1, rx=3)


def screen_synth():
    out = status_and_header()
    motor = ["synth", "adsr", "filter", "lfo", "fx"]
    out += tab_row(58, 78, motor, 1, INK, [MOTOR] * 5, glyphs=motor)
    out.append(rect(14, 85, 26, 12, fill=FAMILY, stroke=INK, sw=0.8, rx=2))
    out.append(t(27, 93.4, "fold", size=6.8, fill=PAPER, anchor="middle"))
    out.append(t(45, 93.4, "growl* ⌄", size=6.8))
    out.append(rect(170, 84, 14, 14, fill="none", stroke=INK, sw=1.2, rx=3))
    for dx, dy in [(-3.5, -3.5), (3.5, -3.5), (0, 0), (-3.5, 3.5), (3.5, 3.5)]:
        out.append(circ(177 + dx, 91 + dy, 1.1, fill=INK, stroke="none", sw=0))
    for base, lab, ax in ((118, "amp", 36), (150, "filt", 26)):
        out.append(t(13, base + 2, lab, size=4.8, fill=GREY, cls="sans"))
        pts = [(ax, base - 9), (74, base), (124, base), (152, base + 5)]
        d = (f"M26 {base+7} Q{ax-6} {base-9} {ax} {base-9} Q{ax+12} {base-1} 74 {base} "
             f"L140 {base} Q145 {base+5} 152 {base+5}")
        out.append(path(d, w=1.6))
        for (px, py), col in zip(pts, GRAB):
            out.append(circ(px, py, 3.3, fill=col, stroke=INK, sw=1))
        for lx, word in zip((44, 80, 120, 160), ("attack", "decay", "sustain", "release")):
            out.append(t(lx, base + 16, word, size=4.6, fill=GREY, anchor="middle", cls="sans"))
    out.append(line(SX0, 172, SX1, 172, w=1.1))
    surf = ["keys", "chords", "seq"]
    out += tab_row(172, 192, surf, 0, TRK[0], [TRK[0]] * 3, glyphs=surf, size=6)
    out.append(t(13, 203, "root", size=5, fill=GREY, cls="sans"))
    out.append(t(27, 203, "f♯", size=5.6, weight=600))
    out.append(t(48, 203, "scale", size=5, fill=GREY, cls="sans"))
    out.append(t(64, 203, "mixo", size=5.6, weight=600))
    out.append(t(186, 203, "−   oct 3   +", size=5.6, anchor="end"))
    notes = [["D#", "E", "F#5", "G#"], ["G#", "A#", "B", "C#"], ["C#", "D#", "E", "F#4"], ["F#3", "G#", "A#", "B"]]
    lit = {(0, 2), (2, 3), (3, 0)}
    kw = (174 - 3 * 3) / 4
    for r in range(4):
        for c in range(4):
            x, y = 13 + c * (kw + 3), 209 + r * 36.5
            on = (r, c) in lit
            out.append(keyed_pad(x, y, kw, 33, on))
            out.append(t(x + kw / 2, y + 19, notes[r][c], size=7.2, fill=PAPER if on else INK, anchor="middle", cls="sans", weight=600))
    out += transport() + places(0)
    return out


def screen_track():
    out = status_and_header()
    names = ["trk_01", "trk_02", "trk_03", "trk_04"]
    out += tab_row(58, 78, names, 2, TRK[2], TRK[:4])
    out += tools_row(84, "synth")
    out += loop_band(104, 116, 15, 150)
    out.append(rect(13, 122, 139, 36, fill=TINT[2], stroke=INK, sw=1.5, rx=1.5))
    out += bars_sparse(14, 151, 140, 28, TRK[2], seed=21)
    out.append(line(100, 78, 100, 172, stroke=CLAY, w=1.3))
    out += edit_bar(100, 150)
    out.append(line(SX0, 172, SX1, 172, w=1.1))
    surf = ["keys", "chords", "seq"]
    out += tab_row(172, 192, surf, 1, TRK[2], [TRK[2]] * 3, glyphs=surf, size=6)
    out.append(t(13, 203, "mode", size=5, fill=GREY, cls="sans"))
    out.append(t(30, 203, "scale ⌄", size=5.6, weight=600))
    out.append(t(186, 203, "−   oct 0   +", size=5.6, anchor="end"))
    pads = [("I", "F♯7", "7"), ("ii", "G♯m", ""), ("iii°", "A♯m♭5", "13"), ("IV", "Badd9", "9"),
            ("v", "C♯m", ""), ("vi", "D♯m11", "11"), ("♭VII", "Emaj7", "7 sus"), ("V", "C♯sus4", "9 11")]
    pw = (174 - 3 * 3) / 4
    for i, (deg, name, mod) in enumerate(pads):
        r, c = divmod(i, 4)
        x, y = 13 + c * (pw + 3), 209 + r * 52
        on = i == 0
        col = PAPER if on else INK
        out.append(keyed_pad(x, y, pw, 49, on))
        out.append(t(x + 3.5, y + 7.5, deg, size=5, fill=col))
        out.append(t(x + pw / 2, y + 28, name, size=7.2 if len(name) < 6 else 6, fill=col, anchor="middle"))
        if mod:
            out.append(t(x + 3.5, y + 45, mod, size=4.4, fill=GREY if not on else "#BDBDB8"))
    mw = (174 - 6 * 2.5) / 7
    for i, m in enumerate(["7", "9", "11", "13", "sus", "min", "V/"]):
        x = 13 + i * (mw + 2.5)
        out.append(rect(x, 316, mw, 18, fill=PIECE, stroke=INK, sw=1, rx=2.5))
        out.append(t(x + mw / 2, 327.5, m, size=5.8, anchor="middle"))
    out += transport() + places(1)
    return out


def screen_tape():
    out = status_and_header()
    out += loop_band(58, 70, 22, 150)
    out += overview(70, 34)
    out.append(line(SX0, 206, SX1, 206, w=1.1))
    names = ["trk_01", "trk_02", "trk_03", "trk_04"]
    out += tab_row(206, 226, names, 1, TRK[1], TRK[:4])
    out += tools_row(232, "mic")
    out += loop_band(252, 264, 22, 150)
    out.append(rect(22, 270, 128, 42, fill=TINT[1], stroke=INK, sw=1.5, rx=1.5))
    out += bars_bursts(23, 149, 291, 30, TRK[1], seed=12)
    out += edit_bar(100, 322)
    out.append(line(100, 58, 100, 356, stroke=CLAY, w=1.3))
    out += transport() + places(2)
    return out


def fx_tile(x, y, w, h, name, on):
    out = [rect(x, y, w, h, fill=PIECE if on else PAPER, stroke=INK, sw=1.8 if on else 1, rx=3)]
    cx, cy = x + w / 2, y + h / 2 - 6
    if name == "tapesat":
        out.append(rect(cx - 14, cy - 1.6, 13, 3.2, fill=INK, stroke="none", sw=0, rx=0.8))
        for dx, dy in [(2, -2.5), (4.5, 0), (6.5, -3), (8, 1.5), (10, -1), (12.5, 2.5), (6, 3)]:
            out.append(rect(cx + dx - 0.9, cy + dy - 0.9, 1.8, 1.8, fill=INK, stroke="none", sw=0))
    elif name == "delay":
        out.append(path(sine(cx - 5, cy, 16, 5, 1.3), w=1.5))
        for k in range(3):
            out.append(circ(cx + 6 + k * 3, cy, 0.9, fill=INK, stroke="none", sw=0))
    elif name == "reverb":
        for rr in (2.5, 5.5, 8.5):
            out.append(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rr*1.15:.1f}" ry="{rr:.1f}" fill="none" stroke="{INK}" stroke-width="1.3"/>')
    elif name == "crush":
        out.append(path(f"M{cx-12:.1f} {cy+5:.1f} L{cx-7:.1f} {cy+5:.1f} L{cx-7:.1f} {cy-4:.1f} L{cx-2:.1f} {cy-4:.1f} L{cx-2:.1f} {cy+5:.1f} L{cx+3:.1f} {cy+5:.1f} L{cx+3:.1f} {cy-4:.1f} L{cx+8:.1f} {cy-4:.1f} L{cx+8:.1f} {cy+5:.1f} L{cx+12:.1f} {cy+5:.1f}", w=1.5))
        out.append(rect(cx - 5.5, cy - 8, 2, 2, fill=INK, stroke="none", sw=0))
        out.append(rect(cx + 4.5, cy - 8, 2, 2, fill=INK, stroke="none", sw=0))
    elif name == "haze":
        for k in (-4, 0, 4):
            out.append(path(sine(cx, cy + k, 22, 1.6, 2), w=1.3))
    elif name == "wobble":
        pts = []
        for i in range(41):
            xx = cx - 12 + 24 * i / 40
            env = math.exp(-((i - 20) / 7) ** 2)
            pts.append(f"{'M' if i == 0 else 'L'}{xx:.1f} {cy - 6 * env * math.sin(i * 1.3):.1f}")
        out.append(path(" ".join(pts), w=1.4))
    elif name == "shimmer":
        out += [star(cx - 8, cy + 5, 2), star(cx - 1, cy, 3.2), star(cx + 7, cy - 5, 4.6)]
    elif name == "plugins":
        out.append(rect(cx - 4, cy - 5.5, 11, 11, stroke=INK, sw=1.4, rx=1.5))
        out.append(circ(cx + 3.5, cy, 1, fill=INK, stroke="none", sw=0))
        out.append(line(cx - 10, cy - 2.5, cx - 4, cy - 2.5, w=1.3))
        out.append(line(cx - 10, cy + 2.5, cx - 4, cy + 2.5, w=1.3))
    out.append(t(cx, y + h - 6, name, size=5.2, anchor="middle"))
    return out


def screen_mix():
    out = status_and_header()
    out += loop_band(58, 70, 22, 150)
    out += overview(70, 24)
    out.append(line(100, 58, 100, 166, stroke=CLAY, w=1.3))
    out.append(line(SX0, 166, SX1, 166, w=1.1))
    out += tab_row(166, 186, ["fx 1", "fx 2", "mix", "eq"], 0, GRAB[0], GRAB)
    out.append(t(100, 199, "select effect · fx1", size=5.2, fill=GREY, anchor="middle"))
    names = ["tapesat", "delay", "reverb", "crush", "haze", "wobble", "shimmer", "plugins"]
    tw = (174 - 3 * 3) / 4
    for i, n in enumerate(names):
        r, c = divmod(i, 4)
        out += fx_tile(13 + c * (tw + 3), 206 + r * 62, tw, 58, n, i == 0)
    out.append(rect(80, 337, 40, 12, fill="none", stroke=GREY, sw=0.9, rx=2.5))
    out.append(t(100, 345.2, "cancel", size=5, fill=GREY, anchor="middle"))
    out += transport() + places(3)
    return out


def phone(ox, oy, content):
    g = [f'<g transform="translate({ox},{oy})">',
         rect(0, 0, 200, 432, fill=BODY, stroke=INK, sw=1.6, rx=30),
         rect(SX0, 9, SW, 414, fill=PAPER, stroke=INK, sw=1.2, rx=22),
         '<g clip-path="url(#td-screen)">']
    g += content
    g += ['</g>', rect(86, 15, 28, 9, fill=INK, stroke="none", sw=0, rx=4.5), '</g>']
    return "\n".join(g)


def four_screens():
    screens = [("synth", screen_synth()), ("track", screen_track()),
               ("tape", screen_tape()), ("mix", screen_mix())]
    out = ['<svg viewBox="0 0 1000 520" role="img" aria-label="las cuatro pantallas de TapeDesk dibujadas: synth, track, tape y mix" xmlns="http://www.w3.org/2000/svg">',
           '<defs><clipPath id="td-screen" clipPathUnits="userSpaceOnUse">'
           f'<rect x="{SX0}" y="9" width="{SW}" height="414" rx="22"/></clipPath></defs>']
    for i, (name, content) in enumerate(screens):
        ox = 16 + i * 256
        cx = ox + 100
        out.append(t(cx, 22, name, size=15, fill="#DADAD6", anchor="middle", cls="sans"))
        out.append(line(cx, 32, cx, 70, stroke="#A3A39E", w=1))
        out.append(phone(ox, 74, content))
        out.append(circ(cx, 70, 3.4, fill="#DADAD6", stroke="none", sw=0))
    out.append('</svg>')
    return "\n".join(out)


def eq_drawing():
    W, H = 1000, 300
    x0, x1 = 60, 940
    f0, f1 = 30.0, 20000.0

    def fx(f):
        return x0 + (math.log10(f) - math.log10(f0)) / (math.log10(f1) - math.log10(f0)) * (x1 - x0)

    y0 = 150
    px_db = 12.0
    bands = [("low", 150, 3.0, "ls", GRAB[0]), ("body", 400, -2.0, "bell", GRAB[1]),
             ("pres", 2500, 2.5, "bell", GRAB[2]), ("air", 8000, 4.0, "hs", GRAB[3])]

    def gain(f):
        s = 0.0
        for _, fc, g, kind, _ in bands:
            o = math.log2(f / fc)
            if kind == "ls":
                s += g / (1 + math.exp(o * 2.6))
            elif kind == "hs":
                s += g / (1 + math.exp(-o * 2.6))
            else:
                s += g * math.exp(-(o ** 2) / (2 * 0.55 ** 2))
        return s

    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="la curva del eq maestro con sus cuatro bandas" xmlns="http://www.w3.org/2000/svg">',
           rect(1, 1, W - 2, H - 2, fill=PAPER, stroke=INK, sw=1.6, rx=16)]
    for f in [50, 100, 200, 500, 1000, 2000, 5000, 10000]:
        x = fx(f)
        out.append(line(x, 40, x, 240, stroke=SUBTLE, w=1))
        lab = f"{f//1000}k" if f >= 1000 else str(f)
        out.append(t(x, 258, lab, size=11, fill=GREY, anchor="middle"))
    out.append(line(x0, y0, x1, y0, stroke=SUBTLE, w=1, extra=' stroke-dasharray="4 5"'))
    pts = []
    n = 240
    for i in range(n + 1):
        f = f0 * (f1 / f0) ** (i / n)
        pts.append(f"{'M' if i == 0 else 'L'}{fx(f):.1f} {y0 - gain(f) * px_db:.1f}")
    out.append(f'<path d="{" ".join(pts)}" fill="none" stroke="{INK}" stroke-width="3.2" stroke-linecap="round"/>')
    for name, fc, g, _, col in bands:
        x = fx(fc)
        y = y0 - gain(fc) * px_db
        out.append(circ(x, y, 15, fill=col, stroke=INK, sw=2))
        out.append(circ(x, y, 4.5, fill=PAPER, stroke=INK, sw=1.5))
        freq = f"{fc/1000:g} kHz" if fc >= 1000 else f"{fc} Hz"
        out.append(t(x, 284, f"{name}", size=14, fill=INK, anchor="middle", cls="sans"))
        out.append(t(x + 1, 222 if y < 180 else 70, f"{g:+.1f} dB", size=11, fill=GREY, anchor="middle"))
    out.append('</svg>')
    return "\n".join(out)


if __name__ == "__main__":
    html_path = sys.argv[1]
    s = open(html_path, encoding="utf-8").read()
    hero = '<figure class="drawing hero-draw">\n' + four_screens() + '\n</figure>'
    s, n1 = re.subn(r'<div class="ph video">.*?</div>', lambda m: hero, s, count=1, flags=re.S)
    if n1 == 0:
        s, n1 = re.subn(r'<figure class="drawing hero-draw">.*?</figure>', lambda m: hero, s, count=1, flags=re.S)
    eq = '<figure class="drawing eq-draw">\n' + eq_drawing() + '\n</figure>'
    anchor = '<code class="g4">air</code> 8 kHz.</p>\n  </div>'
    if '<figure class="drawing eq-draw">' in s:
        s = re.sub(r'<figure class="drawing eq-draw">.*?</figure>', lambda m: eq, s, count=1, flags=re.S)
        n2 = 1
    else:
        n2 = s.count(anchor)
        s = s.replace(anchor, anchor + "\n  " + eq, 1)
    open(html_path, "w", encoding="utf-8").write(s)
    print("hero:", n1, "eq:", n2)
