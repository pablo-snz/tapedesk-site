"""Dibujos de montaje para la portada: TapeDesk con un teclado MIDI y dentro de un host.

Mismo trazo que las cuatro pantallas de la cabecera (gen_draw.py). Sin marcas ajenas:
el teclado y el host son genéricos.

Uso:  python3 tools/gen_draw_setups.py index.es.html
"""
import math
import re
import sys

import gen_draw as gd
from gen_draw import BODY, GRAB, GREY, INK, MOTOR, PAPER, PIECE, SUBTLE, TRK, circ, line, path, rect, t

LIGHT = "#DADAD6"
LIGHT2 = "#A3A39E"
WHITE_KEYS = ["C", "D", "E", "F", "G", "A", "B"]
BLACK_AFTER = {0, 1, 3, 4, 5}


def keyboard(x, y, w, h, octaves, pressed=(), black_pressed=()):
    """Teclas de piano: blancas con su trazo y negras encima. `pressed` = índices de blancas."""
    n = 7 * octaves
    kw = w / n
    out = []
    for i in range(n):
        on = i in pressed
        out.append(rect(x + i * kw, y, kw, h, fill=TRK[0] if on else PIECE, stroke=INK, sw=1.1, rx=2))
    for i in range(n - 1):
        if i % 7 in BLACK_AFTER:
            on = i in black_pressed
            bx = x + (i + 1) * kw - kw * 0.3
            out.append(rect(bx, y, kw * 0.6, h * 0.6, fill=TRK[0] if on else INK, stroke=INK, sw=1, rx=1.5))
    return out


# Paleta plana, como los aparatos de la guía del OP-1: sin contornos, la forma la da el relleno.
TE_BODY = "#C9C9C3"
TE_BODY_DARK = "#B4B4AE"
TE_KEY = "#E4E3DB"
TE_SCREEN = "#0C0C0B"
TE_GLARE = "#3A4048"
TE_PLUG = "#D8D7CF"
TE_CABLE = "#8E8E89"
KNOBS = ["#517FA8", "#C4754F", "#94A86E", "#AD6A7C", "#9770BC", "#A3A39E", "#F25A2A", "#A3A39E"]


def flat(x, y, w, h, fill, rx=0):
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}"/>'


def dot(cx, cy, r, fill):
    return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{fill}"/>'


def flat_phone(x, y, w, h):
    """El iPhone con TapeDesk en keys: cuerpo plano, pantalla clara de la app, tres notas sonando."""
    out = [flat(x, y, w, h, TE_BODY, rx=22), flat(x + 6, y + 6, w - 12, h - 12, PAPER, rx=17),
           flat(x + w / 2 - 16, y + 12, 32, 9, TE_SCREEN, rx=4.5)]
    ix, iw = x + 14, w - 28
    # cabecera y pestañas del motor
    for i in range(3):
        out.append(flat(ix + i * (iw / 3), y + 30, iw / 3 - 3, 16, "#E9E7E0", rx=2))
    out.append(t(ix + 4, y + 42, "tape_019", size=7.5, fill=INK))
    out.append(flat(ix, y + 52, iw, 34, "#EFEDE6", rx=3))
    out.append(path(gd.sine(ix + iw / 2, y + 69, iw - 20, 9, 2.5), stroke=gd.GRAB[1], w=2.2))
    # la superficie: keys, cuatro por cuatro, con tres notas pulsadas
    pw, ph_, gap = (iw - 9) / 4, 25, 3
    lit = {(0, 2): INK, (1, 1): TRK[0], (3, 0): INK}
    for r in range(4):
        for c in range(4):
            fill = lit.get((r, c), "#E6E4DC")
            out.append(flat(ix + c * (pw + gap), y + 96 + r * (ph_ + gap), pw, ph_, fill, rx=3))
    # transporte
    ty = y + 96 + 4 * (ph_ + gap) + 8
    out.append(flat(ix, ty, iw, 22, "#E9E7E0", rx=3))
    for i, col in enumerate([INK, INK, "#9A9A96", gd.REC, gd.CLAY]):
        cx = ix + iw / 10 + i * iw / 5
        out.append(dot(cx, ty + 11, 4.2, col))
    out.append(flat(x + w / 2 - 24, y + h - 13, 48, 3.5, TE_BODY_DARK, rx=1.75))
    return out


def flat_keyboard(x, y, w, h):
    """Un controlador de 37 teclas: pantallita, ocho mandos de color, ocho pads y dos ruedas."""
    out = [flat(x, y, w, h, TE_BODY, rx=8)]
    top = y + 12
    # pantallita con reflejo
    out.append(flat(x + 16, top, 96, 40, TE_SCREEN, rx=3))
    out.append(f'<path d="M{x + 16 + 50} {top} L{x + 16 + 96 - 3} {top} L{x + 16 + 96 - 3} {top + 40} L{x + 16 + 30} {top + 40} Z" fill="{TE_GLARE}" opacity="0.55"/>')
    out.append(t(x + 24, top + 16, "ch 01", size=10, fill="#F2A36B"))
    out.append(t(x + 24, top + 32, "omni", size=9, fill="#6C7E96"))
    # ocho mandos: tapas claras con su marca, dos con un acento apagado
    caps = [TE_KEY, TE_KEY, "#8FA0B2", TE_KEY, TE_KEY, "#BE9A86", TE_KEY, TE_KEY]
    for i, cap in enumerate(caps):
        cx = x + 146 + i * 34
        ang = math.radians(-140 + i * 37)
        out.append(dot(cx, top + 20, 13, TE_BODY_DARK))
        out.append(dot(cx, top + 20, 9.5, cap))
        out.append(line(cx, top + 20, cx + 7.5 * math.sin(ang), top + 20 - 7.5 * math.cos(ang), stroke="#3A3A37", w=1.8))
    # ocho pads
    for i in range(6):
        out.append(flat(x + w - 196 + i * 30, top + 6, 24, 28, gd.REC if i == 3 else TE_KEY, rx=3))
    # ruedas de bend y mod
    wy = top + 56
    for i in range(2):
        out.append(flat(x + 16 + i * 26, wy, 18, h - (wy - y) - 14, TE_SCREEN, rx=4))
        out.append(flat(x + 18 + i * 26, wy + (h - (wy - y) - 14) / 2 - 3 - i * 16, 14, 6, "#8B8B86", rx=2))
    # teclas: las blancas como pastillas claras, las negras son el fondo del teclado
    kx0, ky0, kw_, kh_ = x + 76, wy, w - 90, h - (wy - y) - 12
    n = 21
    kw = kw_ / n
    pressed = {9: TRK[0], 11: TRK[0], 13: TRK[0]}
    for i in range(n):
        out.append(flat(kx0 + i * kw + 1, ky0, kw - 2, kh_, pressed.get(i, TE_KEY), rx=2))
    for i in range(n - 1):
        if i % 7 in BLACK_AFTER:
            bx = kx0 + (i + 1) * kw - kw * 0.28
            out.append(flat(bx, ky0, kw * 0.56, kh_ * 0.6, TE_SCREEN, rx=1.5))
    return out


def plug(x, y, horizontal=True):
    return flat(x, y, 16, 9, TE_PLUG, rx=1.5) if horizontal else flat(x, y, 9, 16, TE_PLUG, rx=1.5)


def midi_drawing():
    """El teléfono y un teclado MIDI, separados y unidos por un cable, como la página «control»
    de la guía del OP-1: formas planas, sin contornos, cable fino con sus dos conectores."""
    W, H = 1000, 420
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="un iPhone con TapeDesk abierto en keys, conectado por un cable USB a un teclado MIDI de 37 teclas" xmlns="http://www.w3.org/2000/svg">']
    px, py, pw, ph_ = 70, 40, 150, 300
    kx, ky, kw, kh = 330, 142, 610, 198
    cx = px + pw / 2
    cy = ky + kh / 2 + 20
    # cable: baja del teléfono, gira y entra por el lateral del teclado
    low = py + ph_ + 36
    turn = kx - 60
    out.append(path(f"M{cx} {py + ph_ + 16} L{cx} {low - 10} Q{cx} {low} {cx + 10} {low} L{turn - 10} {low} "
                    f"Q{turn} {low} {turn} {low - 10} L{turn} {cy + 10} Q{turn} {cy} {turn + 10} {cy} L{kx - 16} {cy}",
                    stroke=TE_CABLE, w=2.2))
    out.append(plug(cx - 4.5, py + ph_, horizontal=False))
    out.append(plug(kx - 16, cy - 4.5))
    scale = ph_ / 432
    out.append('<defs><clipPath id="td-screen" clipPathUnits="userSpaceOnUse">'
               f'<rect x="{gd.SX0}" y="9" width="{gd.SW}" height="414" rx="22"/></clipPath></defs>')
    out.append(f'<g transform="translate({px + (pw - 200 * scale) / 2:.1f},{py}) scale({scale:.4f})">{gd.phone(0, 0, gd.screen_synth())}</g>')
    out += flat_keyboard(kx, ky, kw, kh)
    out.append(t(kx + kw, ky + kh + 38, "usb · bluetooth · red", size=13, fill=LIGHT2, anchor="end"))
    out.append('</svg>')
    return "\n".join(out)


def recorder_screen():
    """La cinta en modo grabadora: sin fila de sitios, con el conmutador en la esquina."""
    out = gd.status_and_header()
    out += gd.loop_band(58, 70, 22, 150)
    out += gd.overview(70, 34)
    out.append(line(gd.SX0, 206, gd.SX1, 206, w=1.1))
    out += gd.tab_row(206, 226, ["trk_01", "trk_02", "trk_03", "trk_04"], 1, TRK[1], TRK[:4])
    out += gd.tools_row(232, "mic")
    out += gd.loop_band(252, 264, 22, 150)
    out.append(rect(22, 270, 128, 42, fill=gd.TINT[1], stroke=INK, sw=1.5, rx=1.5))
    out += gd.bars_bursts(23, 149, 291, 30, TRK[1], seed=12)
    out.append(line(100, 58, 100, 356, stroke=gd.CLAY, w=1.3))
    out += gd.transport()
    # el conmutador de la esquina: tecla cuadrada con el icono de cinta y el sitio en el que estás
    kx, ky, k = 164, 176, 22
    out.append(rect(kx, ky, k, k, fill=PAPER, stroke=INK, sw=1, rx=3))
    cx, cy = kx + k / 2, ky + 8
    out.append(circ(cx - 3.6, cy, 2.4, stroke=INK, sw=0.9))
    out.append(circ(cx + 3.6, cy, 2.4, stroke=INK, sw=0.9))
    out.append(line(cx - 3.6, cy + 2.4, cx + 3.6, cy + 2.4, stroke=INK, w=0.9))
    out.append(t(cx, ky + 18.5, "cinta", size=4.2, anchor="middle", weight=700))
    return out


def modes_drawing():
    W, H = 1000, 520
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="la misma cinta en modo grabadora y en modo groovebox" xmlns="http://www.w3.org/2000/svg">',
           '<defs><clipPath id="td-screen" clipPathUnits="userSpaceOnUse">'
           f'<rect x="{gd.SX0}" y="9" width="{gd.SW}" height="414" rx="22"/></clipPath></defs>']
    for ox, name, content in ((60, "grabadora", recorder_screen()), (560, "groovebox", gd.screen_tape())):
        out.append(t(ox + 100, 30, name, size=17, fill=INK, anchor="middle", cls="sans", weight=500))
        out.append(gd.phone(ox, 60, content))
    # las dos diferencias, señaladas
    out.append(circ(60 + 187, 60 + 187, 3, fill=INK, stroke="none", sw=0))
    out.append(path(f"M{60 + 187} {60 + 187} L300 {60 + 187} L318 {60 + 160} L330 {60 + 160}", stroke=GREY, w=1))
    out.append(t(338, 60 + 157, "cinta y mezcla", size=14, fill=INK, cls="sans", weight=500))
    out.append(t(338, 60 + 175, "se cambian en la esquina", size=12, fill=GREY, cls="sans"))
    out.append(circ(560 + 188, 60 + 405, 3, fill=INK, stroke="none", sw=0))
    out.append(path(f"M{560 + 188} {60 + 405} L800 {60 + 405} L818 {60 + 372} L830 {60 + 372}", stroke=GREY, w=1))
    out.append(t(838, 60 + 369, "los cuatro sitios", size=14, fill=INK, cls="sans", weight=500))
    out.append(t(838, 60 + 387, "synth · pista · cinta · mezcla", size=12, fill=GREY, cls="sans"))
    out.append('</svg>')
    return "\n".join(out)


def mini_tape(x, y, w, h):
    out = [rect(x, y, w, h, fill=PAPER, stroke=INK, sw=1.2, rx=6)]
    out.append(t(x + 10, y + 16, "reloj", size=9, fill=GREY, cls="sans"))
    out.append(t(x + 42, y + 16, "host", size=10, fill=INK))
    out.append(line(x, y + 24, x + w, y + 24, w=1))
    lane_h = (h - 60) / 4
    kinds = [gd.bars_dense, gd.bars_bursts, gd.bars_dense, gd.bars_sparse]
    for i in range(4):
        ly = y + 24 + i * lane_h
        out.append(rect(x + 1, ly, w - 2, lane_h, fill=PAPER if i % 2 == 0 else gd.LANE, stroke="none", sw=0))
        x0 = x + 20 + (i * 37) % 60
        out += kinds[i](x0, x0 + w * 0.55, ly + lane_h / 2, lane_h * 0.6, TRK[i], seed=11 + i)
    out.append(line(x + w * 0.42, y + 24, x + w * 0.42, y + 24 + 4 * lane_h, stroke=gd.REC, w=1.4))
    ty = y + h - 36
    out.append(line(x, ty, x + w, ty, w=1))
    tw = w / 5
    for i, lab in enumerate(["rew", "stop", "start", "rec", "loop"]):
        if i:
            out.append(line(x + i * tw, ty, x + i * tw, y + h, w=0.9))
        col = {"rec": gd.RECIDLE, "loop": gd.CLAY, "start": gd.STARTGREY}.get(lab, INK)
        out.append(t(x + i * tw + tw / 2, ty + 22, lab, size=10, fill=col, anchor="middle"))
    return out


def mini_play(x, y, w, h):
    out = [rect(x, y, w, h, fill=PAPER, stroke=INK, sw=1.2, rx=6)]
    out.append(rect(x + 10, y + 10, 38, 18, fill=gd.FAMILY, stroke=INK, sw=0.9, rx=3))
    out.append(t(x + 29, y + 23, "fold", size=10, fill=PAPER, anchor="middle"))
    out.append(t(x + 56, y + 23, "tectonic", size=10, fill=INK))
    for i, lab in enumerate(("fold", "shape", "warp", "motion")):
        cx = x + 40 + i * (w - 80) / 3
        out.append(path(gd.sine(cx, y + 50, 26, 7, 1 + i * 0.5), stroke=GRAB[i], w=2))
        out.append(t(cx, y + 72, lab, size=8.5, fill=GREY, anchor="middle", cls="sans"))
    out += keyboard(x + 10, y + 84, w - 20, h - 94, 2, pressed=(2, 4), black_pressed=(7,))
    return out


def ipad_host_drawing():
    W, H = 1000, 640
    ox, oy, iw, ih = 40, 20, 920, 600
    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="un iPad en horizontal con un host de audio abierto, con TapeDesk Tape y TapeDesk Play cargados como plugins" xmlns="http://www.w3.org/2000/svg">']
    out.append(rect(ox, oy, iw, ih, fill=BODY, stroke=INK, sw=1.8, rx=40))
    sx, sy, sw_, sh = ox + 22, oy + 22, iw - 44, ih - 44
    out.append(rect(sx, sy, sw_, sh, fill=PAPER, stroke=INK, sw=1.3, rx=22))
    # barra del host: transporte y tempo, nada de marca
    out.append(line(sx, sy + 44, sx + sw_, sy + 44, w=1.2))
    out.append(f'<path d="M{sx+30} {sy+14} L{sx+44} {sy+22} L{sx+30} {sy+30}Z" fill="{INK}"/>')
    out.append(rect(sx + 58, sy + 15, 14, 14, fill=INK, stroke="none", sw=0, rx=2))
    out.append(t(sx + 92, sy + 28, "120 bpm", size=13))
    out.append(t(sx + sw_ - 24, sy + 28, "host", size=12, fill=GREY, anchor="end", cls="sans"))
    # la columna de canales del host
    cx0, cw = sx, 220
    out.append(line(cx0 + cw, sy + 44, cx0 + cw, sy + sh, w=1.1))
    rows = [("in 1–2", GREY, None), ("TapeDesk: Tape", INK, TRK[0]), ("TapeDesk: Play", INK, MOTOR), ("out", GREY, None)]
    for i, (lab, col, dot) in enumerate(rows):
        ry = sy + 70 + i * 110
        out.append(rect(cx0 + 16, ry, cw - 32, 70, fill=PIECE, stroke=INK, sw=1.1, rx=6))
        if dot:
            out.append(rect(cx0 + 16, ry, 6, 70, fill=dot, stroke="none", sw=0, rx=2))
        out.append(t(cx0 + 34, ry + 41, lab, size=13, fill=col))
        if i < len(rows) - 1:
            out.append(line(cx0 + cw / 2, ry + 70, cx0 + cw / 2, ry + 110, stroke=GREY, w=1.2))
    # las dos ventanas de plugin
    px, pw = cx0 + cw + 24, sw_ - cw - 48
    out.append(t(px, sy + 76, "TapeDesk: Tape", size=13, fill=GREY, cls="sans"))
    out += mini_tape(px, sy + 86, pw, 230)
    out.append(t(px, sy + 348, "TapeDesk: Play", size=13, fill=GREY, cls="sans"))
    out += mini_play(px, sy + 358, pw, 176)
    out.append('</svg>')
    return "\n".join(out)


def place(html, marker_id, figure):
    """Sustituye el bloque de huecos que contiene `ph-NN` (o el dibujo de antes) por la figura."""
    cls = f"setup-{marker_id}"
    fig = f'<figure class="drawing setup {cls}">\n{figure}\n</figure>'
    if f'class="drawing setup {cls}"' in html:
        return re.sub(rf'<figure class="drawing setup {cls}">.*?</figure>', lambda m: fig, html, count=1, flags=re.S), 1
    return re.subn(rf'<div class="shots[^"]*">\s*<div><div class="ph [a-z]+"><span class="id">{marker_id}.*?\n  </div>',
                   lambda m: fig, html, count=1, flags=re.S)


def drop(html, marker_id):
    return re.subn(rf'\n  <div class="shots[^"]*">\s*<div><div class="ph [a-z]+"><span class="id">{marker_id}.*?\n  </div>',
                   "", html, count=1, flags=re.S)


if __name__ == "__main__":
    page = sys.argv[1]
    s = open(page, encoding="utf-8").read()
    s, a = place(s, "ph-23", midi_drawing())
    s, b = place(s, "ph-24", ipad_host_drawing())
    s, c = drop(s, "ph-26")
    fig = '<figure class="drawing modes-draw">\n' + modes_drawing() + '\n</figure>'
    s = re.sub(r'<figure class="drawing modes-draw">.*?</figure>', lambda m: fig, s, count=1, flags=re.S)
    open(page, "w", encoding="utf-8").write(s)
    print("midi:", a, "host:", b, "fuera ph-26:", c)
