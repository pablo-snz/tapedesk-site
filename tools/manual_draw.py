"""Bocetos del manual. Dibujos de línea que explican una idea sin enseñar el teléfono entero.

Los textos salen de tools/i18n/manual-draw.json en el idioma de `LANG` (lo fija gen_manual.py):
`A()` da el nombre de un mando tal como lo enseña la app, `T()` la prosa del dibujo.
"""
import html
import json
import math
import os
import re
import sys

import gen_draw as gd
from gen_draw import CLAY, GREY, INK, LANE, LOOPBAND, MOTOR, PAPER, PIECE, REC, TINT, TRK

SANS = "sans"
LANG = "es"
_STRINGS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n", "manual-draw.json"),
                          encoding="utf-8"))
_CJK = re.compile(r"[　-鿿가-힯＀-￯]")


def A(name):
    return _STRINGS["app"][LANG][name]


def T(key, **values):
    table = _STRINGS["text"].get(LANG, {})
    if key not in table:
        print(f"aviso: falta el texto de dibujo {key} en {LANG}", file=sys.stderr)
        table = _STRINGS["text"]["es"]
    return table[key].format(**values)


def width(text, size, mono_face=False):
    """Ancho aproximado para colocar un texto detrás de otro."""
    return sum(size * (1.0 if _CJK.match(ch) else (0.6 if mono_face else 0.55)) for ch in text)


def svg(canvas_width, height, aria, body):
    frame = gd.rect(1, 1, canvas_width - 2, height - 2, fill=PAPER, stroke=INK, sw=1.4, rx=14)
    return (f'<svg viewBox="0 0 {canvas_width} {height}" role="img" aria-label="{html.escape(aria)}" '
            f'xmlns="http://www.w3.org/2000/svg">{frame}{"".join(body)}</svg>')


def label(x, y, text, size=13, fill=INK, anchor="start", weight=None):
    return gd.t(x, y, html.escape(text), size=size, fill=fill, anchor=anchor, cls=SANS, weight=weight)


def mono(x, y, text, size=12, fill=INK, anchor="start"):
    return gd.t(x, y, html.escape(text), size=size, fill=fill, anchor=anchor, cls="mono")


def arrow(x1, y1, x2, y2, stroke=INK, line_width=1.4, dashed=False):
    angle = math.atan2(y2 - y1, x2 - x1)
    tip = 7
    left = (x2 - tip * math.cos(angle - 0.45), y2 - tip * math.sin(angle - 0.45))
    right = (x2 - tip * math.cos(angle + 0.45), y2 - tip * math.sin(angle + 0.45))
    dash = ' stroke-dasharray="4 4"' if dashed else ""
    return (gd.line(x1, y1, x2, y2, stroke=stroke, w=line_width, extra=dash)
            + f'<path d="M{left[0]:.1f} {left[1]:.1f} L{x2:.1f} {y2:.1f} L{right[0]:.1f} {right[1]:.1f}" '
              f'fill="none" stroke="{stroke}" stroke-width="{line_width}" stroke-linecap="round" '
              f'stroke-linejoin="round"/>')


def key(x, y, key_width, height, text, on=False, size=12, color=INK):
    fill = INK if on else PIECE
    ink = PAPER if on else color
    return (gd.rect(x, y, key_width, height, fill=fill, stroke=INK, sw=1.3, rx=5)
            + mono(x + key_width / 2, y + height / 2 + size * 0.36, text, size=size, fill=ink, anchor="middle"))


def region(x0, x1, y, height, color_index, seed, kind=gd.bars_dense, opacity=1.0):
    group = [gd.rect(x0, y, x1 - x0, height, fill=TINT[color_index % 4], stroke="none", sw=0)]
    group += kind(x0, x1, y + height / 2, height - 8, TRK[color_index], seed=seed)
    return f'<g opacity="{opacity}">{"".join(group)}</g>'


def dotted(*names):
    return " · ".join(A(name) for name in names)


def pantalla():
    phone = gd.phone(0, 0, gd.screen_tape()).replace("url(#td-screen)", "url(#td-clip-pantalla)")
    for name in ("project", "timecode", "speed", "lift", "rev", "loop", "rew", "stop", "start", "rec",
                 "synth", "track", "tape", "mix"):
        phone = phone.replace(f">{name}</text>", f">{html.escape(A(name))}</text>")
    # gen_draw pinta la fila de sitios con los nombres de la app en español.
    for spanish, name in (("pista", "track"), ("cinta", "tape"), ("mezcla", "mix")):
        phone = phone.replace(f">{spanish}</text>", f">{html.escape(A(name))}</text>")
    body = [f'<defs><clipPath id="td-clip-pantalla" clipPathUnits="userSpaceOnUse">'
            f'<rect x="{gd.SX0}" y="9" width="{gd.SW}" height="414" rx="22"/></clipPath></defs>',
            f'<g transform="translate(26,20)">{phone}</g>']
    callouts = [
        (45, 52, T("screen.header"), dotted("project", "timecode", "speed")),
        (132, 118, T("screen.tape"), T("screen.tape.detail")),
        (216, 184, T("screen.tabs"), T("screen.tabs.detail")),
        (239, 244, T("screen.tools"), T("screen.tools.detail")),
        (291, 304, T("screen.armed"), T("screen.armed.detail")),
        (373, 370, T("screen.transport"), dotted("rew", "stop", "start", "rec", "loop")),
        (405, 430, T("screen.places"), dotted("synth", "track", "tape", "mix")),
    ]
    for anchor_y, label_y, name, detail in callouts:
        ay = anchor_y + 20
        body.append(gd.circ(224, ay, 2.8, fill=INK, stroke="none", sw=0))
        body.append(gd.path(f"M224 {ay} L244 {ay} L262 {label_y} L272 {label_y}", stroke=GREY, w=1))
        body.append(label(280, label_y - 1, name, size=15, weight=500))
        body.append(label(280, label_y + 15, detail, size=12, fill=GREY))
    return svg(580, 472, T("screen.aria"), body)


def modos():
    """El dibujo de los dos modos de la portada (gen_draw.py). Va en español: la portada se escribe en
    español y tools/i18n/build.py traduce sus textos. El manual ya no lo usa: enseña capturas."""
    body = [label(30, 40, "grabadora", size=16, weight=500),
            label(30, 60, "la cinta y la mezcla", size=12.5, fill=GREY),
            label(310, 40, "groovebox", size=16, weight=500),
            label(310, 60, "los cuatro sitios", size=12.5, fill=GREY)]
    body.append(gd.rect(30, 80, 240, 70, fill=LANE, stroke=INK, sw=1.2, rx=8))
    body.append(key(46, 96, 104, 38, "cinta", on=True))
    body.append(key(154, 96, 104, 38, "mezcla"))
    body.append(gd.rect(310, 80, 240, 70, fill=LANE, stroke=INK, sw=1.2, rx=8))
    for i, (name, color) in enumerate((("synth", MOTOR), ("pista", MOTOR), ("cinta", INK), ("mezcla", INK))):
        body.append(key(322 + i * 56, 96, 52, 38, name, size=11, color=color))
    body.append(label(30, 176, "cambias con el conmutador de la esquina", size=12, fill=GREY))
    body.append(label(310, 176, "la fila de abajo te lleva a cada sitio", size=12, fill=GREY))
    return svg(580, 196, "lo que ves en modo grabadora y en modo groovebox", body)


def suma_cambio():
    body = []
    for y, name, detail in ((40, A("sos"), T("sos.detail")), (136, A("punch"), T("punch.detail"))):
        body.append(mono(30, y, name, size=15))
        body.append(label(30 + width(name, 15, mono_face=True) + 16, y, detail, size=12.5, fill=GREY))
    body.append(region(30, 550, 56, 40, 0, 11))
    body.append(f'<g opacity="0.85">{region(210, 390, 62, 28, 1, 5, kind=gd.bars_bursts)}</g>')
    body.append(gd.rect(210, 62, 180, 28, fill="none", stroke=REC, sw=1.6, rx=2))
    body.append(region(30, 210, 152, 40, 0, 11))
    body.append(region(210, 390, 152, 40, 1, 5, kind=gd.bars_bursts))
    body.append(gd.rect(210, 152, 180, 40, fill="none", stroke=REC, sw=1.6, rx=2))
    body.append(region(390, 550, 152, 40, 0, 13))
    return svg(580, 214, T("sospunch.aria", sos=A("sos"), punch=A("punch")), body)


def umbral():
    body = []
    center = 108
    threshold = 26
    body.append(gd.rect(254, 40, 296, 136, fill=REC, stroke="none", sw=0, extra=' opacity="0.07"'))
    random = gd.lcg(7)
    x = 30
    while x < 550:
        if x < 250:
            height = 3 + 6 * next(random)
        elif x < 270:
            height = 110 * (1 - (x - 250) / 30)
        else:
            height = 12 + 50 * next(random) * (0.6 + 0.4 * math.sin(x / 19))
        body.append(gd.line(x, center - height / 2, x, center + height / 2, stroke=TRK[0], w=1.6))
        x += 4
    for y in (center - threshold, center + threshold):
        body.append(gd.line(30, y, 550, y, stroke=REC, w=1.2, extra=' stroke-dasharray="6 5"'))
    body.append(mono(546, center - threshold - 8, T("threshold"), size=12, fill=REC, anchor="end"))
    body.append(gd.line(254, 36, 254, 180, stroke=CLAY, w=1.6))
    body.append(label(262, 50, T("threshold.start"), size=13, weight=500))
    body.append(label(30, 50, T("threshold.silence"), size=12.5, fill=GREY))
    return svg(580, 196, T("threshold.aria"), body)


def looper():
    body = [gd.rect(30, 40, 250, 16, fill=LOOPBAND, stroke="none", sw=0)]
    for x in (30, 280):
        body.append(f'<rect x="{x-5}" y="43" width="10" height="10" fill="{CLAY}" transform="rotate(45 {x} 48)"/>')
    for i, (seed, kind) in enumerate(((3, gd.bars_dense), (5, gd.bars_bursts), (9, gd.bars_sparse))):
        y = 68 + i * 36
        body.append(region(30, 280, y, 30, i, seed, kind=kind))
        body.append(mono(290, y + 20, T("looper.pass", n=i + 1), size=11, fill=GREY))
    body.append(arrow(380, 122, 414, 122))
    body.append(mono(397, 110, A("stop"), size=12, anchor="middle"))
    stacked = [region(420, 550, 88, 68, 0, 3)]
    stacked.append(f'<g opacity="0.55">{"".join(gd.bars_bursts(420, 550, 122, 40, TRK[1], seed=5))}</g>')
    stacked.append(f'<g opacity="0.55">{"".join(gd.bars_sparse(420, 550, 122, 30, TRK[2], seed=9))}</g>')
    body += stacked
    body.append(label(485, 176, T("looper.one"), size=13, anchor="middle", weight=500))
    return svg(580, 196, T("looper.aria"), body)


def rejilla():
    body = [label(30, 34, T("grid.channels"), size=12.5, fill=GREY)]
    channel_colors = [[0], [0, 1], [1], [2], [], []]
    channel_width = 78
    for i, colors in enumerate(channel_colors):
        x = 30 + i * (channel_width + 8)
        body.append(gd.rect(x, 46, channel_width, 40, fill=PIECE, stroke=INK, sw=1.2, rx=5))
        for k, color in enumerate(colors):
            stripe = channel_width / len(colors)
            body.append(gd.rect(x + k * stripe, 46, stripe, 40, fill=TRK[color], stroke="none", sw=0,
                                extra=' opacity="0.45"'))
        body.append(mono(x + channel_width / 2, 71, f"in {i + 1}", size=12, anchor="middle"))
    track_width = 122
    links = [(0, 0), (1, 0), (1, 1), (2, 1), (3, 2)]
    for channel, track in links:
        x1 = 30 + channel * (channel_width + 8) + channel_width / 2
        x2 = 30 + track * (track_width + 8) + track_width / 2
        body.append(gd.path(f"M{x1:.1f} 88 C{x1:.1f} 118 {x2:.1f} 118 {x2:.1f} 146", stroke=TRK[track], w=1.8))
    for i in range(4):
        x = 30 + i * (track_width + 8)
        body.append(gd.rect(x, 148, track_width, 34, fill=PIECE, stroke=INK, sw=1.2, rx=5))
        body.append(gd.rect(x, 178, track_width, 4, fill=TRK[i], stroke="none", sw=0))
        body.append(mono(x + track_width / 2, 170, f"trk_0{i + 1}", size=12, anchor="middle"))
    body.append(label(30, 204, T("grid.tracks"), size=12.5, fill=GREY))
    body.append(label(550, 204, T("grid.note"), size=12, fill=GREY, anchor="end"))
    return svg(580, 220, T("grid.aria"), body)


def loop_dibujo():
    start, end = 170, 420
    body = [gd.rect(30, 44, 520, 16, fill=LANE, stroke="none", sw=0),
            gd.rect(start, 44, end - start, 16, fill=LOOPBAND, stroke="none", sw=0)]
    for x in range(34, 550, 10):
        body.append(gd.line(x, 44, x, 48 if (x - 34) % 50 else 52, stroke=GREY, w=0.8))
    for x, name in ((start, T("loop.in")), (end, T("loop.out"))):
        body.append(f'<rect x="{x-6}" y="46" width="12" height="12" fill="{CLAY}" transform="rotate(45 {x} 52)"/>')
        body.append(label(x, 34, name, size=12.5, anchor="middle", weight=500))
    for i, kind in enumerate((gd.bars_dense, gd.bars_bursts, gd.bars_sparse)):
        y = 72 + i * 30
        body.append(region(30, start, y, 24, i, 20 + i, kind=kind, opacity=0.35))
        body.append(region(start, end, y, 24, i, 30 + i, kind=kind))
        body.append(region(end, 550, y, 24, i, 40 + i, kind=kind, opacity=0.35))
    body.append(gd.line(end - 14, 170, end + 14, 158, w=1.4))
    body.append(gd.line(end - 14, 158, end + 14, 170, w=1.4))
    body.append(label(end - 22, 169, T("loop.fade"), size=12, fill=GREY, anchor="end"))
    body.append(label(30, 169, T("loop.max"), size=12, fill=GREY))
    return svg(580, 190, T("loop.aria"), body)


def suma_sustituye():
    body = []
    for ox, title, names, replaces in (
            (30, T("fx.add"), dotted("tapesat", "delay", "reverb", "shimmer"), False),
            (310, T("fx.replace"), dotted("crush", "haze", "wobble"), True)):
        body.append(label(ox, 36, title, size=15, weight=500))
        body.append(mono(ox, 54, names, size=11, fill=GREY))
        top, bottom, left, right = 80, 180, ox + 10, ox + 230
        body.append(gd.line(left, bottom, right, bottom, w=1.2))
        body.append(gd.line(left, top - 6, left, bottom, w=1.2))
        body.append(label(right, bottom + 18, T("fx.send"), size=12, fill=GREY, anchor="end"))
        dry_end = bottom - 6 if replaces else top
        body.append(gd.line(left, top, right, dry_end, stroke=INK, w=2.4))
        body.append(gd.line(left, bottom, right, top, stroke=REC, w=2.4))
        body.append(label(left + 8, top - 8, T("fx.dry"), size=11.5, fill=INK))
        body.append(label(left + (right - left) * 0.62 + 10, bottom - (bottom - top) * 0.62 + 16, T("fx.wet"),
                          size=11.5, fill=REC))
    return svg(580, 212, T("fx.aria"), body)


def senal():
    body = [label(95, 42, dotted("in", "pan") + " · fader", size=11.5, fill=GREY, anchor="middle")]
    for x, box_width, name in ((30, 130, A("track")), (250, 120, A("mix")), (440, 100, A("drive")),
                               (590, 80, A("eq")), (720, 110, T("signal.limiter"))):
        body.append(key(x, 56, box_width, 44, name, size=13))
    body.append(key(150, 178, 90, 44, "fx 1", size=13))
    body.append(key(280, 178, 90, 44, "fx 2", size=13))
    body.append(arrow(160, 78, 248, 78))
    body.append(arrow(120, 100, 190, 176))
    body.append(arrow(145, 100, 320, 176))
    body.append(mono(140, 148, "sd1", size=11, fill=GREY, anchor="end"))
    body.append(mono(262, 138, "sd2", size=11, fill=GREY))
    body.append(arrow(215, 178, 290, 102))
    body.append(arrow(335, 178, 335, 102))
    for x1, x2 in ((370, 438), (540, 588), (670, 718), (830, 866)):
        body.append(arrow(x1, 78, x2, 78))
    body.append(mono(872, 82, T("signal.out"), size=12))
    body.append(arrow(405, 78, 405, 204, stroke=GREY, dashed=True))
    body.append(label(415, 200, T("signal.stems"), size=12, fill=GREY))
    return svg(940, 240, T("signal.aria"), body)


def eq():
    return gd.eq_drawing()


DIBUJOS = {
    "pantalla": pantalla,
    "suma-cambio": suma_cambio,
    "umbral": umbral,
    "looper": looper,
    "rejilla": rejilla,
    "loop": loop_dibujo,
    "suma-sustituye": suma_sustituye,
    "senal": senal,
    "eq": eq,
}
