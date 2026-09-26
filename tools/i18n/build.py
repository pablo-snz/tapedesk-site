#!/usr/bin/env python3
"""Monta index.<código>.html desde index.es.html y tools/i18n/<código>.json.

    python3 tools/i18n/build.py fr          # escribe index.fr.html
    python3 tools/i18n/build.py all         # todos los idiomas con json
    python3 tools/i18n/build.py --check fr  # claves que faltan, sin traducir, etiquetas cambiadas

index.es.html nunca se toca. Una clave que falta sale en español, con aviso.
"""
import json
import re
import sys
from collections import Counter

from extract import HERE, ROOT, SOURCE, scan

NOT_LANGUAGES = {"es", "notes", "manual-ui", "manual-code-alias", "manual-draw", "privacy"}
TAG = re.compile(r"</?[a-zA-Z][^>]*>")


def load_translation(code):
    return json.loads((HERE / f"{code}.json").read_text(encoding="utf-8"))


def available_codes():
    return sorted(p.stem for p in HERE.glob("*.json") if p.stem not in NOT_LANGUAGES)


def localize_paths(html, code):
    html = re.sub(r'(<html lang=")es(")', rf"\g<1>{code}\2", html, count=1)
    html = re.sub(r"(img/shots/[^\"]*?-)es([-.])", rf"\g<1>{code}\2", html)
    html = re.sub(r'privacy\.es\.html', lambda m: privacy_link(code), html)
    return re.sub(r'manual\.es\.html(#[^"]*)?', lambda m: manual_link(code, m.group(1) or ""), html)


def privacy_link(code):
    name = "privacy.html" if code == "en" else f"privacy.{code}.html"
    return name if (ROOT / name).exists() else "privacy.html"


def manual_link(code, anchor):
    """Each language goes to its own manual with the same anchor: the manual keeps its
    anchors across languages ({#ancla} in TD-manual and its translations). English is
    manual.html; a language whose manual is not written yet goes to the English one."""
    name = "manual.html" if code == "en" else f"manual.{code}.html"
    if not (ROOT / name).exists():
        name = "manual.html"
    return name + anchor


def build(code):
    source = SOURCE.read_text(encoding="utf-8")
    translation = load_translation(code)
    replacements = []
    for seg in scan(source):
        text = translation.get(seg.key)
        if text is None:
            print(f"[{code}] falta {seg.key}: queda en español")
            text = seg.text
        if seg.kind == "attr":
            text = text.replace('"', "&quot;")
        replacements += [(span, text) for span in seg.spans]
    html = source
    for (start, end), text in sorted(replacements, reverse=True):
        html = html[:start] + text + html[end:]
    html = localize_paths(html, code)
    out = ROOT / f"index.{code}.html"
    out.write_text(html, encoding="utf-8", newline="")
    if code == "en":  # English is also the default page of the site
        (ROOT / "index.html").write_text(html, encoding="utf-8", newline="")
    if code != "en" and not (ROOT / f"manual.{code}.html").exists():
        print(f"[{code}] aviso: sin manual.{code}.html, los enlaces van a manual.html")
    print(f"[{code}] -> {out.name}")


def check(code):
    source = json.loads((HERE / "es.json").read_text(encoding="utf-8"))
    notes = json.loads((HERE / "notes.json").read_text(encoding="utf-8"))
    translation = load_translation(code)
    missing = [k for k in source if k not in translation]
    unknown = [k for k in translation if k not in source]
    same = [k for k in source if translation.get(k) == source[k]]
    same_prose = [k for k in same if not notes[k]["control"]]
    tags = [k for k in source if k in translation
            and Counter(TAG.findall(source[k])) != Counter(TAG.findall(translation[k]))]
    report = (("faltan", missing), ("sobran (no están en es.json)", unknown),
              ("iguales al español, texto", same_prose),
              ("iguales al español, mandos de la app (normal si la app no los traduce)", [k for k in same if k not in same_prose]),
              ("HTML en línea distinto", tags))
    for title, keys in report:
        print(f"{title}: {len(keys)}")
        for k in keys:
            print(f"  {k}")
    return 1 if missing or tags else 0


def main(args):
    if len(args) == 2 and args[0] == "--check":
        return check(args[1])
    if len(args) != 1:
        print(__doc__)
        return 2
    codes = available_codes() if args[0] == "all" else [args[0]]
    for code in codes:
        if code in NOT_LANGUAGES:
            print(f"{code}: no se construye (es la fuente)")
            return 2
        build(code)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
