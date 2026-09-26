#!/bin/bash
# Rebuilds the whole site in order: landing strings, landing pages, privacy, manuals.
set -e
cd "$(dirname "$0")/.."
python3 tools/i18n/extract.py
python3 tools/i18n/build.py all
python3 tools/gen_privacy.py
python3 tools/gen_manual.py ../TD-manual.md manual.es.html es
for l in en fr de it pt-BR nl pl tr id ru ja ko zh-Hans zh-Hant; do
  python3 tools/gen_manual.py ../TD-manual.$l.md manual.$l.html $l | tail -1
done
python3 tools/i18n/build.py all > /dev/null   # second pass: landing links see the new privacy pages
