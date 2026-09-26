"""Recorta las capturas de la portada para enseñar solo la parte que cuenta cada sección.

Recorre todos los idiomas que haya en img/shots (ph-02-light-es.png, ph-02-light-ja.png…).
Los recortes salen en img/shots/recortes/ con el nombre de la captura y su franja
de alto. Se rehacen cuando la captura original es más nueva.

Antes monta ph-27 (la cinta partida en claro y oscuro) a partir de las dos ph-02.

Uso:  python3 tools/crop_shots.py
"""
import glob
import os

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(ROOT, "img", "shots")
DESTINO = os.path.join(SHOTS, "recortes")

RECORTES = [
    # cinta · fila de tres: cabecera, la cinta entera y las pestañas de pista
    ("ph-02-light", 176, 1300),
    ("ph-03-light", 176, 1300),
    ("ph-06-light", 176, 1300),
    # synth · fila de tres, hasta el canto del panel de presets
    ("ph-08-dark", 176, 1228),
    ("ph-07-dark", 176, 1228),
    ("ph-09-dark", 176, 1228),
    ("ph-10-dark", 1222, 2170),
    ("ph-11-dark", 1222, 2170),
    # El seq de ping es más bajo que keys y chords. Se rellena con el fondo de la app
    # para que los tres queden a la misma altura en la fila.
    ("ph-12-dark", 510, 1325, 948),
    ("ph-13-dark", 196, 1600),
    ("ph-14-dark", 196, 1600),
    # pista · fila de dos a pantalla entera, de la cabecera al transporte
    ("ph-15-light", 176, 2380),
    ("ph-05-light", 176, 2380),
    # mezcla · carrusel: la mezcla y los siete efectos, el mismo corte
    ("ph-16-light", 1236, 2176),
    ("ph-17-light", 1236, 2176),
    ("ph-17-delay-light", 1236, 2176),
    ("ph-17-reverb-light", 1236, 2176),
    ("ph-17-crush-light", 1236, 2176),
    ("ph-17-haze-light", 1236, 2176),
    ("ph-17-wobble-light", 1236, 2176),
    ("ph-17-shimmer-light", 1236, 2176),
    ("ph-18-light", 1236, 2176),
    ("ph-19-dark", 192, 1412),
    ("ph-21-light", 392, 1364),
    ("ph-22-light", 1196, 2168),
    ("ph-27-light", 176, 1382),
]


def rellenar(recorte, alto):
    recorte = recorte.convert("RGB")
    fondo = recorte.getpixel((0, recorte.height - 1))
    lienzo = Image.new("RGB", (recorte.width, alto), fondo)
    lienzo.paste(recorte, (0, 0))
    return lienzo


def idiomas():
    return sorted({os.path.basename(p)[len("ph-02-light-"):-4]
                   for p in glob.glob(os.path.join(SHOTS, "ph-02-light-*.png"))})


def mas_nuevo(destino, *origenes):
    return not os.path.exists(destino) or any(
        os.path.getmtime(o) > os.path.getmtime(destino) for o in origenes)


def partida(lang):
    claro = os.path.join(SHOTS, f"ph-02-light-{lang}.png")
    oscuro = os.path.join(SHOTS, f"ph-02-dark-{lang}.png")
    destino = os.path.join(SHOTS, f"ph-27-light-{lang}.png")
    if not (os.path.exists(claro) and os.path.exists(oscuro)) or not mas_nuevo(destino, claro, oscuro):
        return
    a, b = Image.open(claro).convert("RGB"), Image.open(oscuro).convert("RGB")
    mitad = a.width // 2
    a.paste(b.crop((mitad, 0, b.width, b.height)), (mitad, 0))
    a.save(destino, optimize=True)
    print(os.path.basename(destino))


os.makedirs(DESTINO, exist_ok=True)
for lang in idiomas():
    partida(lang)
    for base, y0, y1, *alto in RECORTES:
        nombre = f"{base}-{lang}"
        origen = os.path.join(SHOTS, f"{nombre}.png")
        destino = os.path.join(DESTINO, f"{nombre}-{y0}-{y1}.png")
        if not os.path.exists(origen) or not mas_nuevo(destino, origen):
            continue
        recorte = Image.open(origen).crop((0, y0, 1206, y1))
        if alto:
            recorte = rellenar(recorte, alto[0])
        recorte.save(destino, optimize=True)
        print(f"{nombre}-{y0}-{y1}.png")

# Fuera los recortes que ya no pide nadie (franjas viejas).
vigentes = {f"{base}-{lang}-{y0}-{y1}.png" for lang in idiomas() for base, y0, y1, *_ in RECORTES}
for nombre in os.listdir(DESTINO):
    if nombre.endswith(".png") and nombre not in vigentes:
        os.remove(os.path.join(DESTINO, nombre))
