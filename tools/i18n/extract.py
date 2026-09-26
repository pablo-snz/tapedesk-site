#!/usr/bin/env python3
"""Saca de index.es.html todas las cadenas que se ven o se oyen.

    python3 tools/i18n/extract.py

Escribe tools/i18n/es.json (clave -> texto en español) y tools/i18n/notes.json
(clave -> contexto). build.py usa scan() para volver a encontrar cada cadena.
"""
import json
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "index.es.html"
HERE = Path(__file__).resolve().parent

SVG_NAMES = {"hero-draw": "hero", "modes-draw": "modes", "setup-ph-23": "midi", "setup-ph-24": "host"}
SKIP_TEXT = {"TapeDesk", "App Store"}
# Texto de SVG que no es lengua: notas, acordes, grados, nombres de pista, cifras.
SVG_NOT_LANGUAGE = re.compile(
    r"^(?:[A-G][#♯♭b]?\S*|[♭]?[ivxIVX]+[°/]?|trk_\d+|tape_\d+|ch \d+|TapeDesk: \w+|[\d\s:.,+x−-]*)$"
)
# En los dibujos, lo que va a menos de 9 px es la interfaz de la app dibujada.
SVG_ANNOTATION_MIN_SIZE = 9.0
# Mandos dibujados más grandes (el plugin en el iPad, el canal MIDI) que no salen en otro sitio.
EXTRA_UI_WORDS = {"tectonic", "omni"}
# Un nombre de motor en su pastilla (texto claro sobre el morado) es contenido: la app lo deja
# igual en los quince. Clave propia, para que no comparta cadena con la macro que se llama igual.
ENGINE_NAMES = {"drift", "poly", "fold", "fm", "pluck", "mallet", "wave", "cz", "ensemble"}
ENGINE_CHIP_FILL = "#F6F5F1"

CONTROL_NOTE = ("Nombre de control de la app: debe coincidir con la cadena localizada de la app "
                "(si la app lo deja en inglés como serigrafía, se deja igual).")


@dataclass
class Segment:
    key: str
    text: str
    kind: str  # "text" (contenido HTML) o "attr" (valor de atributo)
    note: str
    control: bool = False
    spans: list = field(default_factory=list)


def slug(text):
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-") or "x"


def has_letters(text):
    return any(ch.isalpha() for ch in text)


class Scanner:
    def __init__(self, html):
        self.html = html
        self.segments = {}
        self.svg_ranges = [m.span() for m in re.finditer(r'<svg viewBox[^>]*role="img".*?</svg>', html, re.S)]
        self.sections = [(m.start(), html.index("</section>", m.start()), m.group(1))
                         for m in re.finditer(r'<section id="([^"]+)"', html)]

    def add(self, key, span, kind, note, control=False):
        text = self.html[span[0]:span[1]]
        base, n = key, 1
        while key in self.segments and self.segments[key].text != text:
            n += 1
            key = f"{base}-{n}"
        if key in self.segments:
            self.segments[key].spans.append(span)
            return
        self.segments[key] = Segment(key, text, kind, note, control, [span])

    def in_svg(self, pos):
        return any(a <= pos < b for a, b in self.svg_ranges)

    def section_at(self, pos):
        return next((sid for a, b, sid in self.sections if a <= pos < b), None)

    def region_at(self, pos):
        section = self.section_at(pos)
        if section:
            return section
        for marker, name in (("<footer", "footer"), ('<nav class="places"', "nav"),
                             ('<div class="wrap hero"', "hero"), ('<div class="top"', "top")):
            start = self.html.find(marker)
            if 0 <= start <= pos:
                return name
        return "meta"

    def scan(self):
        self.scan_head()
        self.scan_links()
        self.scan_headings_and_paragraphs()
        self.scan_figures()
        self.scan_tables()
        self.scan_spec()
        self.scan_misc()
        self.scan_svgs()
        self.check_no_overlap()
        return sorted(self.segments.values(), key=lambda seg: seg.spans[0][0])

    def scan_head(self):
        m = re.search(r"<title>(.*?)</title>", self.html)
        self.add("meta.title", m.span(1), "text", "Título de la pestaña y de los buscadores.")
        for name, key in (('name="description"', "meta.description"), ('property="og:description"', "meta.og_description")):
            m = re.search(r"<meta " + name + r' content="([^"]*)"', self.html)
            self.add(key, m.span(1), "attr", "Descripción para buscadores / vista previa al compartir. Unos 150 caracteres como mucho.")

    def scan_links(self):
        for m in re.finditer(r'<a\b([^>]*)>([^<]+)</a>', self.html):
            text, attrs = m.group(2), m.group(1)
            if text in SKIP_TEXT or "@" in text or self.in_svg(m.start()):
                continue
            region = self.region_at(m.start())
            href = re.search(r'href="([^"]*)"', attrs).group(1)
            if 'class="ref"' in attrs:
                self.add(f"{region}.ref", m.span(2), "text",
                         f"Enlace al manual desde la cabecera de «{region}». Debe coincidir con el título de esa sección en el manual del idioma.")
            elif region == "nav":
                self.add(f"nav.{href.lstrip('#')}", m.span(2), "text",
                         "Barra de secciones fija. Una o dos palabras; tiene que caber en una fila en el móvil.")
            else:
                target = {"privacy.html": "privacy", "mailto:tape.desk.admin@gmail.com": "contact"}.get(href, slug(text))
                self.add(f"{region}.link.{target}", m.span(2), "text", f"Enlace de texto ({region}).")

    def scan_headings_and_paragraphs(self):
        counters = {}
        for m in re.finditer(r"<(h1|h2|h3|p)\b([^>]*)>(.*?)</\1>", self.html, re.S):
            tag, attrs, inner = m.groups()
            if not has_letters(inner) or inner in SKIP_TEXT or 'class="col"' in attrs:
                continue
            region = self.region_at(m.start())
            if tag == "h2":
                key = f"{region}.h2"
            elif tag == "p" and 'class="print"' in attrs:
                key = f"{region}.print"
            else:
                counters[(region, tag)] = counters.get((region, tag), 0) + 1
                key = f"{region}.{tag}{counters[(region, tag)]}" if tag == "p" else f"{region}.{tag}.{counters[(region, tag)]}"
            note = {"h2": "Título de sección.", "h3": "Subtítulo dentro de la sección.",
                    "p": "Párrafo. Conserva el HTML en línea (<code>, <b>, enlaces) con sus clases."}[tag]
            self.add(key, m.span(3), "text", note)
        for i, m in enumerate(re.finditer(r'<p class="col"><span>([^<]*)</span><span>([^<]*)</span></p>', self.html)):
            for j in (1, 2):
                self.add(f"hero.col{i + 1}.line{j}", m.span(j), "text",
                         "Portada, junto al logo: una línea corta que no debe partirse. Aprox. el largo del español.")

    def scan_figures(self):
        for fig in re.finditer(r"<figure\b[^>]*>.*?</figure>", self.html, re.S):
            img = re.search(r'<img\b[^>]*src="([^"]+)"[^>]*alt="([^"]*)"', fig.group(0))
            if not img:
                continue
            name = re.search(r"(ph-\d+(?:-[a-z]+)?)-(?:light|dark)", img.group(1)).group(1)
            base = fig.start()
            self.add(f"fig.{name}.alt", (base + img.start(2), base + img.end(2)), "attr",
                     f"Texto alternativo de la captura {name} (lector de pantalla). Frase completa, describe la captura del idioma.")
            cap = re.search(r"<figcaption>([^<]*)</figcaption>", fig.group(0))
            if cap:
                self.add(f"fig.{name}.caption", (base + cap.start(1), base + cap.end(1)), "text",
                         "Pie bajo la captura: nombre de la pantalla o del mando que se ve. " + CONTROL_NOTE, control=True)

    def scan_tables(self):
        for row in re.finditer(r'<tr><td class="n">([^<]*)</td><td class="p">([^<]*)</td><td class="d">(.*?)</td></tr>', self.html):
            prefix = f"{self.region_at(row.start())}.tbl.{slug(row.group(1))}"
            self.add(f"{prefix}.name", row.span(1), "text", "Nombre de motor o efecto. " + CONTROL_NOTE, control=True)
            if has_letters(row.group(2)):
                self.add(f"{prefix}.params", row.span(2), "text", "Los cuatro mandos, separados por « · ». " + CONTROL_NOTE, control=True)
            self.add(f"{prefix}.desc", row.span(3), "text", "Descripción en la tabla. Corta; conserva los <code>.")

    def scan_spec(self):
        for cell in re.finditer(r'<div class="k">([^<]*)</div><div class="v">([^<]*)', self.html):
            prefix = f"ficha.{slug(cell.group(1))}"
            self.add(f"{prefix}.k", cell.span(1), "text", "Etiqueta de la ficha técnica. Una o dos palabras.")
            if has_letters(cell.group(2)):
                self.add(f"{prefix}.v", cell.span(2), "text", "Valor de la ficha técnica. Cifras y unidades igual; « · » separa.")

    def scan_misc(self):
        m = re.search(r'<nav class="places" aria-label="([^"]*)"', self.html)
        self.add("nav.label", m.span(1), "attr", "aria-label de la barra de secciones (solo lector de pantalla).")
        for m in re.finditer(r'<span class="id">([^<]*)</span><span class="what">([^<]*)</span>', self.html):
            ph = m.group(1).split(" ")[0]
            self.add(f"{self.region_at(m.start())}.{ph}.placeholder", m.span(2), "text",
                     "Hueco de captura pendiente: solo se ve con ?borrador en la dirección.")

    def svg_texts(self, start, end):
        for m in re.compile(r"<text\b([^>]*)>([^<]*)</text>").finditer(self.html, start, end):
            text = m.group(2)
            if has_letters(text) and not SVG_NOT_LANGUAGE.match(text):
                size = float(re.search(r'font-size="([\d.]+)"', m.group(1)).group(1))
                anchor = re.search(r'text-anchor="(\w+)"', m.group(1)).group(1)
                yield m, text, size, anchor

    def app_vocabulary(self):
        """Palabras que son mandos de la app: las de las tablas y pies, y todo lo dibujado a tamaño de interfaz."""
        words = set(EXTRA_UI_WORDS)
        for seg in self.segments.values():
            if seg.control:
                words.update(seg.text.split(" · "))
        for start, end in self.svg_ranges:
            words.update(text for _, text, size, _ in self.svg_texts(start, end) if size < SVG_ANNOTATION_MIN_SIZE)
        return words

    def scan_svgs(self):
        vocabulary = self.app_vocabulary()
        for start, end in self.svg_ranges:
            figure_class = re.findall(r'<figure class="drawing ([^"]*)">', self.html[:start])[-1].split()[-1]
            name = SVG_NAMES.get(figure_class, figure_class)
            label = re.compile(r'aria-label="([^"]*)"').search(self.html, start, end)
            self.add(f"svg.{name}.aria", label.span(1), "attr",
                     f"aria-label del dibujo «{name}» (solo lector de pantalla). Frase que describe el dibujo.")
            printed = {text for m, text, _, _ in self.svg_texts(start, end) if 'class="sans"' in m.group(1)}
            for m, text, size, anchor in self.svg_texts(start, end):
                # «host» rotula el dibujo y a la vez es el valor de reloj que enseña la app (mono):
                # el valor es de la app y no puede compartir cadena con el rótulo.
                shown_by_app = text in printed and 'class="mono"' in m.group(1)
                room = (f"El dibujo no parte líneas: {len(text)} caracteres en español, a {size:g} px, "
                        f"anclaje {anchor}; no pases de unos {round(len(text) * 1.25) + 1}.")
                if text in ENGINE_NAMES and f'fill="{ENGINE_CHIP_FILL}"' in m.group(1):
                    self.add(f"svg.{name}.engine.{slug(text)}", m.span(2), "text",
                             "Nombre de motor en su pastilla: no se traduce, la app lo enseña igual en todos los idiomas.",
                             control=True)
                elif text in vocabulary or shown_by_app:
                    self.add(f"svg.{name}.ui.{slug(text)}", m.span(2), "text",
                             f"Interfaz de la app dibujada en «{name}». {CONTROL_NOTE} {room}", control=True)
                else:
                    self.add(f"svg.{name}.label.{slug(text)}", m.span(2), "text", f"Rótulo del dibujo «{name}». {room}")

    def check_no_overlap(self):
        spans = sorted((s, key) for seg in self.segments.values() for s in seg.spans for key in [seg.key])
        for (a, key_a), (b, key_b) in zip(spans, spans[1:]):
            if b[0] < a[1]:
                raise ValueError(f"cadenas solapadas: {key_a} y {key_b}")


def scan(html):
    return Scanner(html).scan()


def main():
    segments = scan(SOURCE.read_text(encoding="utf-8"))
    strings = {seg.key: seg.text for seg in segments}
    notes = {seg.key: {"note": seg.note, "control": seg.control} for seg in segments}
    for path, data in ((HERE / "es.json", strings), (HERE / "notes.json", notes)):
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(strings)} claves -> {HERE / 'es.json'}")


if __name__ == "__main__":
    main()
