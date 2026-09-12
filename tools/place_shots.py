"""Sustituye los huecos de imagen de la portada por las capturas que existan.

Cada sección pide el tema CONTRARIO a su fondo, para que la captura se recorte
sola contra la página: las secciones oscuras llevan capturas en claro, y las
franjas hueso (modos · synth · cintas) las llevan en oscuro.

Uso:  python3 tools/place_shots.py index.es.html [idioma]
"""
import os
import re
import sys

PAGE = sys.argv[1]
LANG = sys.argv[2] if len(sys.argv) > 2 else "en"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, "img", "shots")

# Huecos que caen dentro de una franja hueso: captura OSCURA.
ON_BONE = {f"ph-{n:02d}" for n in list(range(7, 15)) + [19, 20]}

PH = re.compile(
    r'<div class="ph (?P<shape>[a-z]+)"><span class="id">(?P<id>ph-\d+)[^<]*</span>'
    r'<span class="what">(?P<alt>[^<]*)</span></div>')


def candidates(shot_id):
    theme = "dark" if shot_id in ON_BONE else "light"
    return [f"{shot_id}-{theme}-{LANG}.png", f"{shot_id}-{theme}.png", f"{shot_id}.png"]


def replace(m):
    for name in candidates(m["id"]):
        if os.path.exists(os.path.join(SHOTS, name)):
            alt = m["alt"].replace('"', "&quot;")
            return (f'<img class="shot {m["shape"]}" src="img/shots/{name}" '
                    f'alt="{alt}" loading="lazy" decoding="async">')
    return m.group(0)


page = open(PAGE, encoding="utf-8").read()
out, n = PH.subn(replace, page)
open(PAGE, "w", encoding="utf-8").write(out)
faltan = len(PH.findall(out))
print(f"{n} huecos con captura · {faltan} siguen vacíos")
