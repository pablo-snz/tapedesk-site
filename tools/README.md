# tools

- `gen_manual.py` genera `manual.es.html` desde `TD-manual.md`:
  `python3 tools/gen_manual.py ../TD-manual.md manual.es.html`
- `gen_draw.py` dibuja las cuatro pantallas y el EQ y los mete en `index.es.html`:
  `python3 tools/gen_draw.py index.es.html`
- `gen_draw_setups.py` dibuja el teclado MIDI y el host con los dos plugins, en lugar de fotos:
  `python3 tools/gen_draw_setups.py index.es.html`
- `crop_shots.py` recorta las capturas de la portada en `img/shots/recortes/`. Recorre todos los idiomas que haya y monta ph-27 con las dos ph-02. Las franjas de cada recorte están al principio del script.
- `manual_template.html` es la plantilla del manual (estilos, índice, pie).
- `manual_draw.py` dibuja los bocetos del manual. La sintaxis de figuras, modos y fichas está al principio de `gen_manual.py`.
- Los recortes de capturas se generan solos en `img/manual/recortes/`. Con `?borrador` en la dirección se ven los huecos pendientes.

## Traducir la portada (`tools/i18n/`)

La portada se escribe en español (`index.es.html`) y las demás salen de ella.

- `extract.py` lee `index.es.html` y escribe `es.json` (clave → texto en español, en el orden de la página) y `notes.json` (dónde sale cada texto y si es el nombre de un mando de la app, que tiene que coincidir con la app traducida). Se vuelve a correr cada vez que cambia la portada:
  `python3 tools/i18n/extract.py`
- Para traducir, se copia `es.json` a `<código>.json` (`fr.json`, `zh-Hans.json`, `pt-BR.json`…) y se cambian los textos. El HTML de dentro (`<code class="…">`, `<b>`) se deja igual.
- `build.py` escribe `index.<código>.html`: el mismo HTML con los textos cambiados, `lang` puesto, las capturas `-es-` cambiadas por las del idioma y los enlaces a `manual.<código>.html`. Si falta una clave, sale en español y lo avisa. No toca `index.es.html`.
  `python3 tools/i18n/build.py fr` · `python3 tools/i18n/build.py all`
- `--check` dice qué claves faltan, cuáles siguen iguales al español y dónde el HTML de dentro no cuadra:
  `python3 tools/i18n/build.py --check fr`

- `gen_privacy.py` escribe `privacy.html` con la cabecera, el selector y el pie de `index.html`. Se vuelve a correr después de `build.py all`.
