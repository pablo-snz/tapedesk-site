"""Builds privacy.html with the chrome of the English landing (index.html): same head styles,
top bar, language picker and footer. The policy itself is below, in English only.

    python3 tools/gen_privacy.py
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
landing = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()

import json

DATA = json.load(open(os.path.join(ROOT, "tools", "i18n", "privacy.json"), encoding="utf-8"))


def page_name(code):
    return "privacy.html" if code == "en" else f"privacy.{code}.html"


def landing_for(code):
    name = "index.html" if code == "en" else f"index.{code}.html"
    return open(os.path.join(ROOT, name), encoding="utf-8").read()


def build(code, text):
    landing = landing_for(code)
    head = landing[:landing.index("</head>")]
    head = re.sub(r"<title>.*?</title>", f"<title>TapeDesk · {text["title"].lower()}</title>", head, flags=re.S)
    head = re.sub(r'<meta name="description" content="[^"]*">',
                  '<meta name="description" content="' + text["description"] + '">', head)
    head = re.sub(r'<meta property="og:[^"]*" content="[^"]*">\n?', "", head)
    extra_css = """  .policy{max-width:760px;padding-top:56px;padding-bottom:80px}
      .policy h1{font-weight:300;font-size:clamp(38px,6vw,56px);margin:0 0 10px}
      .policy .date{color:var(--ink2);font-size:15px;margin:0 0 36px}
      .policy .facts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));border-top:1px solid var(--line);border-bottom:1px solid var(--line);margin:0 0 44px}
      .policy .facts div{padding:14px 16px 14px 0}
      .policy .facts dt{color:var(--ink2);font-size:13px;margin-bottom:4px}
      .policy .facts dd{margin:0;font-size:16px}
      .policy section{display:grid;grid-template-columns:48px 1fr;gap:0 16px;padding:22px 0;border-top:1px solid var(--line)}
      .policy .n{font-family:ui-monospace,Menlo,monospace;color:var(--ink2);font-size:13px;padding-top:5px}
      .policy h2{font-weight:400;font-size:21px;margin:0 0 8px}
      .policy p{margin:0;line-height:1.6;color:var(--ink)}
      .policy a{color:inherit}
      .policy .facts + section{border-top:0;padding-top:0}
      @media(max-width:640px){.policy .facts{grid-template-columns:repeat(2,minmax(0,1fr))}}
    </style>"""
    head = head.replace("</style>", extra_css, 1)
    body_start = landing.index("<body")
    top_start = landing.index('<div class="top">')
    top_end = landing.index("</div></div>", top_start) + len("</div></div>")
    footer = landing[landing.index("<footer"):landing.index("</footer>") + len("</footer>")]
    scripts = "".join(re.findall(r"<script>[\s\S]*?</script>\s*", landing[landing.index("</footer>"):]))
    svg_defs = landing[body_start:top_start]

    facts = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in text["facts"])
    sections = "".join(
        f'<section><span class="n">{i:02d}</span><div><h2>{t}</h2><p>{b}</p></div></section>'
        for i, (t, b) in enumerate(text["sections"], 1))
    article = (f'<main class="wrap policy"><h1>{text["title"]}</h1><p class="date">{text["date"]}</p>'
               f'<dl class="facts">{facts}</dl>{sections}</main>')
    top = landing[top_start:top_end].replace('class="brand" href="#"', 'class="brand" href="index.html"')
    page = head + "</head>\n" + svg_defs + top + "\n" + article + "\n" + footer + "\n" + scripts + "</body>\n</html>\n"
    # the picker and every privacy link point at this language's family of pages
    page = re.sub(r'href="index((?:\.[A-Za-z-]+)?)\.html" hreflang="([^"]+)"',
                  lambda m: f'href="{page_name(m.group(2))}" hreflang="{m.group(2)}"', page)
    open(os.path.join(ROOT, page_name(code)), "w", encoding="utf-8").write(page)
    print(page_name(code), len(page))


for code, text in DATA.items():
    if not code.startswith("_"):
        build(code, text)
