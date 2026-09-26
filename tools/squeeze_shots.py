"""Aligera las capturas sin cambiar sus medidas.

Una captura de la app son colores planos: con 256 colores es indistinguible del
original y ocupa cuatro veces menos. Redimensionar, en cambio, no sirve — el
remuestreo inventa degradados y el PNG deja de comprimir.

Uso:  python3 tools/squeeze_shots.py img/shots img/manual
"""
import os
import sys

from PIL import Image

total_antes = total_despues = 0
for carpeta in sys.argv[1:]:
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.endswith(".png"):
            continue
        ruta = os.path.join(carpeta, nombre)
        im = Image.open(ruta)
        if im.mode in ("RGBA", "LA", "P") and "transparency" in im.info:
            continue  # con transparencia se queda como está
        if im.mode == "P":
            continue  # ya está en paleta
        antes = os.path.getsize(ruta)
        im.convert("RGB").quantize(colors=256).save(ruta, optimize=True)
        despues = os.path.getsize(ruta)
        total_antes += antes
        total_despues += despues
        print(f"{nombre:24} {antes // 1024:5} → {despues // 1024:4} kb")
print(f"total {total_antes // 1024} → {total_despues // 1024} kb")
