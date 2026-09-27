"""Genera manual.es.html a partir del manual en markdown.

Uso:  python3 tools/gen_manual.py ../TD-manual.md manual.es.html [idioma]
      El idioma (es por defecto) elige los textos de alrededor de tools/i18n/manual-ui.json.
      En inglés escribe también manual.html, la página por defecto.
  {#ancla}                     al final de un título fija su ancla. Las traducciones la conservan,
                               así los enlaces [texto](#ancla) no se rompen al traducir el título.

Marcas propias del markdown
  {groovebox} o {grabadora}    al final de un título o al principio de un bloque o de un punto
                               de lista, para lo que solo existe en ese modo.
  [fichas]                     al final de un título. Cada bloque que empieza en negrita se monta
                               como ficha, con su lista de mandos.
  > [captura img 190-340] pie  recorte de una captura, de 190 a 340 px de alto (x0-x1 para el ancho).
  > [pantalla img] pie         captura entera del teléfono.
  > [dibujo nombre] pie        boceto de tools/manual_draw.py.
  > [lamina img] pie           imagen ancha.
  > [pendiente texto] pie      hueco por hacer. Solo se ve con ?borrador en la dirección.
  La palabra ancho dentro de los corchetes saca la figura a todo el ancho de la sección.
"""
import html
import os
import re
import sys
import unicodedata

from PIL import Image

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
import manual_draw  # noqa: E402

SRC, OUT = sys.argv[1], sys.argv[2]
LANG = sys.argv[3] if len(sys.argv) > 3 else "es"
UI_ALL = __import__("json").load(open(os.path.join(TOOLS, "i18n", "manual-ui.json"), encoding="utf-8"))
if LANG not in UI_ALL:
    sys.exit(f"falta {LANG} en tools/i18n/manual-ui.json")
UI = UI_ALL[LANG]
manual_draw.LANG = LANG
CODE_ALIAS = __import__("json").load(
    open(os.path.join(TOOLS, "i18n", "manual-code-alias.json"), encoding="utf-8")).get(LANG, {})
ANCHOR_RE = re.compile(r"\s*\{#([a-z0-9-]+)\}\s*$")
IMAGE_DIRS = ("img/manual", "img/shots")
CROP_DIR = "img/manual/recortes"
INDEX_SLUG = "index-of-terms"
MIX_EFFECTS_SLUG = "mix-effects"
MIX_COLORS = ("g1", "g2", "g3", "g4")
CODE_CLASS = {"rec": "rec", "loop": "loop", "adsr": "motor", "filter": "motor", "lfo": "motor",
              "fx 1": "g1", "fx 2": "g2", "sd1": "g1", "sd2": "g2", "eq": "g4",
              "low": "g1", "body": "g2", "pres": "g3", "air": "g4"}

HEADING_RE = re.compile(r"^(#{2,3}) (.+)$")
FIGURE_RE = re.compile(r"^> (?:\{(grabadora|groovebox)\} )?\[(captura|pantalla|dibujo|lamina|pendiente) ?([^\]]*)\] ?(.*)$")
MODE_PREFIX_RE = re.compile(r"^\{(grabadora|groovebox)\} ")
CARD_HEAD_RE = re.compile(r"^\*\*(.+?)\*\*(?: · (.*))?$")


class Unit:
    def __init__(self, level, title, slug, mode, cards):
        self.level = level
        self.title = title
        self.slug = slug
        self.mode = mode
        self.cards = cards
        self.text = []
        self.side = []
        self.wide = []


def slugify(text):
    plain = unicodedata.normalize("NFKD", re.sub(r"[`*]", "", text)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")


def solo(mode):
    return f' data-solo="{mode}"' if mode else ""


def chip(mode):
    label = UI["MODE_REC"] if mode == "grabadora" else UI["MODE_GROOVE"]
    return f' <span class="solo">{label}</span>' if mode else ""


def inline(text, first_code_class=None):
    codes = []

    def stash(match):
        codes.append(match.group(1))
        return f"\x00{len(codes) - 1}\x00"

    escaped = html.escape(re.sub(r"`([^`]*)`", stash, text), quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\((#[a-z0-9-]+)\)", r'<a href="\2">\1</a>', escaped)

    def unstash(match):
        index = int(match.group(1))
        inner = codes[index]
        css = first_code_class if (first_code_class and index == 0) else CODE_CLASS.get(CODE_ALIAS.get(inner.strip().lower(), inner.strip().lower()))
        attribute = f' class="{css}"' if css else ""
        return f"<code{attribute}>{html.escape(inner)}</code>"

    return re.sub(r"\x00(\d+)\x00", unstash, escaped)


def plain(text):
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    return html.escape(re.sub(r"[`*]", "", text), quote=True)


def split_mode(text):
    match = MODE_PREFIX_RE.match(text)
    if not match:
        return None, text
    return match.group(1), text[match.end():]


def parse_title(raw):
    mode = None
    match = re.search(r"\s*\{(grabadora|groovebox)\}", raw)
    if match:
        mode = match.group(1)
        raw = raw.replace(match.group(0), "")
    cards = "[fichas]" in raw
    return raw.replace("[fichas]", "").strip(), mode, cards


def localized(name):
    """El manual se escribe con las capturas en español (`…-es`); cada idioma usa la suya si existe."""
    if LANG == "es" or not name.endswith("-es"):
        return name
    candidate = f"{name[:-3]}-{LANG}"
    if any(os.path.exists(os.path.join(ROOT, folder, f"{candidate}.png")) for folder in IMAGE_DIRS):
        return candidate
    print(f"aviso: {candidate} no existe, sale {name}", file=sys.stderr)
    return name


def find_image(name):
    for folder in IMAGE_DIRS:
        path = os.path.join(ROOT, folder, f"{name}.png")
        if os.path.exists(path):
            return folder, path
    sys.exit(f"no encuentro la imagen {name}")


def crop(name, y_range, x_range):
    _, path = find_image(name)
    image = Image.open(path)
    x0, x1 = x_range or (0, image.width)
    y0, y1 = y_range or (0, image.height)
    y1 = min(y1, image.height)
    suffix = f"-{y0}-{y1}" + (f"-x{x0}-{x1}" if x_range else "")
    relative = f"{CROP_DIR}/{name}{suffix}.png"
    target = os.path.join(ROOT, relative)
    if not os.path.exists(target) or os.path.getmtime(target) < os.path.getmtime(path):
        os.makedirs(os.path.dirname(target), exist_ok=True)
        image.crop((x0, y0, x1, y1)).save(target, optimize=True)
    return relative, x1 - x0, y1 - y0


def figure(kind, args, caption, mode):
    tokens = args.split()
    wide = "ancho" in tokens
    tokens = [token for token in tokens if token != "ancho"]
    figcaption = f"<figcaption>{inline(caption)}</figcaption>" if caption else ""
    if kind == "pendiente":
        return "lado", "pendiente", (f'<figure class="fig pendiente"{solo(mode)}>'
                                     f'<div class="hueco">{html.escape(args)}</div>{figcaption}</figure>')
    if kind == "dibujo":
        drawing = manual_draw.DIBUJOS[tokens[0]]()
        return ("ancho" if wide else "texto"), kind, f'<figure class="fig dibujo"{solo(mode)}>{drawing}{figcaption}</figure>'
    name = localized(tokens[0])
    y_range = x_range = None
    for token in tokens[1:]:
        match = re.fullmatch(r"(x?)(\d+)-(\d+)", token)
        if match:
            span = (int(match.group(2)), int(match.group(3)))
            if match.group(1):
                x_range = span
            else:
                y_range = span
    if y_range or x_range:
        source, width, height = crop(name, y_range, x_range)
    else:
        folder, path = find_image(name)
        width, height = Image.open(path).size
        source = f"{folder}/{name}.png"
    place = "ancho" if wide or kind == "lamina" else "lado"
    return place, kind, (f'<figure class="fig {kind}"{solo(mode)}><img src="{source}" width="{width}" '
                         f'height="{height}" alt="{plain(caption)}" loading="lazy" decoding="async">'
                         f'{figcaption}</figure>')


def add_figures(unit, figures):
    for place in ("texto", "lado", "ancho"):
        chosen = [(kind, markup) for spot, kind, markup in figures if spot == place]
        if not chosen:
            continue
        if len(chosen) == 1:
            group = chosen[0][1]
        else:
            kinds = {kind for kind, _ in chosen}
            css = "grupo pantallas" if kinds == {"pantalla"} else "grupo"
            group = f'<div class="{css}">{"".join(markup for _, markup in chosen)}</div>'
        if place == "texto":
            unit.text.append(("html", group, None))
        elif place == "lado" and not unit.cards:
            unit.side.append(group)
        else:
            unit.wide.append(group)


def prose(lines, unit):
    paragraph, items = [], []
    for line in lines:
        if line.startswith("- "):
            items.append(line[2:].strip())
        elif items:
            items[-1] += " " + line.strip()
        else:
            paragraph.append(line.strip())
    out = []
    if paragraph:
        lead = unit.level == 2 and not unit.text
        out.append(f"<p{' class=\"lead\"' if lead else ''}>{inline(' '.join(paragraph))}</p>")
    if items:
        entries = []
        for item in items:
            mode, item = split_mode(item)
            entries.append(f"<li{solo(mode)}>{inline(item)}</li>")
        css = ' class="terms"' if unit.slug == INDEX_SLUG else ""
        out.append(f"<ul{css}>{''.join(entries)}</ul>")
    return "".join(out)


def card(lines, unit):
    head = CARD_HEAD_RE.match(lines[0])
    name, subtitle = head.group(1), head.group(2)
    before, rows, after = [], [], []
    for line in lines[1:]:
        if line.startswith("- "):
            rows.append(line[2:].strip())
        elif rows:
            after.append(line.strip())
        else:
            before.append(line.strip())
    colors = MIX_COLORS if unit.slug == MIX_EFFECTS_SLUG else ()
    entries = []
    for index, row in enumerate(rows):
        mode, row = split_mode(row)
        match = re.match(r"^`([^`]+)`\s*(.*)$", row)
        if match:
            css = f' class="{colors[index]}"' if index < len(colors) else ""
            term, detail = f"<code{css}>{html.escape(match.group(1))}</code>", inline(match.group(2))
        else:
            term, detail = "", inline(row)
        entries.append(f"<div{solo(mode)}><dt>{term}</dt><dd>{detail}</dd></div>")
    parts = [f"<h4>{html.escape(name)}</h4>"]
    if subtitle:
        parts.append(f'<p class="sub">{inline(subtitle)}</p>')
    if before:
        parts.append(f'<p class="nota">{inline(" ".join(before))}</p>')
    if entries:
        parts.append(f"<dl>{''.join(entries)}</dl>")
    if after:
        parts.append(f'<p class="nota">{inline(" ".join(after))}</p>')
    return "".join(parts)


def parse(markdown):
    markdown = markdown.split("\n## Notas de voz")[0]
    markdown = markdown[markdown.index("\n## ") + 1:]
    chapters = []
    for block in re.split(r"\n\s*\n", markdown):
        block = block.strip("\n")
        if not block.strip() or block.strip() == "---":
            continue
        heading = HEADING_RE.match(block)
        if heading and "\n" not in block:
            raw = heading.group(2)
            anchor = ANCHOR_RE.search(raw)
            raw = ANCHOR_RE.sub("", raw)
            title, mode, cards = parse_title(raw)
            slug = anchor.group(1) if anchor else slugify(title)
            if len(heading.group(1)) == 2:
                chapters.append({"title": title, "slug": slug, "mode": mode,
                                 "units": [Unit(2, None, slug, None, False)]})
            else:
                chapters[-1]["units"].append(Unit(3, title, slug, mode, cards))
            continue
        unit = chapters[-1]["units"][-1]
        lines = block.split("\n")
        if all(line.startswith(">") for line in lines):
            matches = [FIGURE_RE.match(line) for line in lines]
            add_figures(unit, [figure(m.group(2), m.group(3), m.group(4), m.group(1)) for m in matches if m])
            continue
        mode, first = split_mode(lines[0])
        lines[0] = first
        if unit.cards and CARD_HEAD_RE.match(lines[0]):
            unit.text.append(("card", card(lines, unit), mode))
        else:
            unit.text.append(("html", prose(lines, unit), mode))
    return chapters


def render_unit(unit):
    parts, cards = [], []

    def flush_cards():
        if cards:
            parts.append(f'<div class="fichas">{"".join(cards)}</div>')
            cards.clear()

    for kind, markup, mode in unit.text:
        if kind == "card":
            cards.append(f'<div class="ficha"{solo(mode)}>{markup}</div>')
            continue
        flush_cards()
        parts.append(f"<div{solo(mode)}>{markup}</div>" if mode else markup)
    flush_cards()
    heading = f'<h3 id="{unit.slug}">{inline(unit.title)}{chip(unit.mode)}</h3>' if unit.level == 3 else ""
    css = ["unidad", f"u-{unit.slug}"]
    if unit.side:
        css.append("con-figuras")
    out = [f'<div class="{" ".join(css)}"{solo(unit.mode)}>', f'<div class="texto">{heading}{"".join(parts)}</div>']
    if unit.side:
        out.append(f'<div class="figuras">{"".join(unit.side)}</div>')
    if unit.wide:
        out.append(f'<div class="ancho">{"".join(unit.wide)}</div>')
    out.append("</div>")
    return "".join(out)


def render(chapters):
    body, toc = [], []
    for chapter in chapters:
        units = "".join(render_unit(unit) for unit in chapter["units"] if unit.text or unit.side or unit.wide
                        or unit.level == 3)
        body.append(f'<section class="cap"{solo(chapter["mode"])}>'
                    f'<h2 id="{chapter["slug"]}">{inline(chapter["title"])}{chip(chapter["mode"])}</h2>{units}</section>')
        toc.append(f'<a class="l2" href="#{chapter["slug"]}"{solo(chapter["mode"])}>{inline(chapter["title"])}</a>')
        for unit in chapter["units"][1:]:
            toc.append(f'<a class="l3" href="#{unit.slug}"{solo(unit.mode or chapter["mode"])}>{inline(unit.title)}</a>')
    return "\n".join(body), "\n".join(toc)


def check_links(chapters, page):
    ids = [chapter["slug"] for chapter in chapters] + [u.slug for c in chapters for u in c["units"][1:]]
    repeated = sorted({slug for slug in ids if ids.count(slug) > 1})
    broken = sorted({href for href in re.findall(r'href="#([^"]+)"', page) if href not in ids})
    for slug in repeated:
        print(f"aviso · ancla repetida #{slug}")
    for slug in broken:
        print(f"aviso · enlace roto #{slug}")
    return not repeated and not broken


chapters = parse(open(SRC, encoding="utf-8").read())
body, toc = render(chapters)
template = open(os.path.join(TOOLS, "manual_template.html"), encoding="utf-8").read()


def page_for(code):
    return "manual.html" if code == "en" else f"manual.{code}.html"


def home_for(code):
    return "index.html" if code == "en" else f"index.{code}.html"


langs = " ".join(
    f'<a href="{page_for(code)}" hreflang="{code}" lang="{code}"'
    + (' aria-current="page"' if code == LANG else "") + f">{name}</a>"
    for code, name in UI_ALL["_languages"] if code in UI_ALL)
privacy = "privacy.html" if LANG == "en" else f"privacy.{LANG}.html"
if not os.path.exists(os.path.join(ROOT, privacy)):
    privacy = "privacy.html"
fills = dict(UI, LANG=LANG, MANUAL_HREF=page_for(LANG), HOME_HREF=home_for(LANG), PRIVACY_HREF=privacy,
             LANGS=f'<nav class="langs" translate="no">{langs}</nav>', TOC=toc, BODY=body)
page = template
for key, value in fills.items():
    page = page.replace("{{" + key + "}}", value)
if "{{" in page:
    sys.exit("hueco sin rellenar en la plantilla: " + ", ".join(sorted(set(re.findall(r"\{\{[A-Z_]+\}\}", page)))))
open(OUT, "w", encoding="utf-8").write(page)
if LANG == "en" and os.path.basename(OUT) != "manual.html":
    open(os.path.join(os.path.dirname(os.path.abspath(OUT)), "manual.html"), "w", encoding="utf-8").write(page)
units = sum(len(chapter["units"]) - 1 for chapter in chapters)
print(f"capítulos {len(chapters)} · apartados {units} · figuras {page.count('class=\"fig ')}"
      f" · pendientes {page.count('fig pendiente')}")
if not check_links(chapters, body + toc):
    sys.exit(1)
