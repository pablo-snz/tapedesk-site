"""Genera manual.es.html a partir del manual en markdown."""
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_draw as gd

SRC, OUT = sys.argv[1], sys.argv[2]
md = open(SRC, encoding="utf-8").read()

md = re.sub(r"(\n## 12\..*?)\n## .*", r"\1\n", md, flags=re.S)
md = re.sub(r"^# .*?\n", "", md, count=1)

PROTECT = ["TapeDesk", "Ableton Link", "Apple Pencil", "iPhone", "iPad", "iOS"]
CODE_CLASS = {"rec": "rec", "loop": "loop", "adsr": "motor", "filter": "motor", "lfo": "motor",
              "fx1": "g1", "fx2": "g2", "eq": "g4", "low": "g1", "body": "g2", "pres": "g3", "air": "g4"}


def slug_for(num, text):
    if num:
        return "s" + num.rstrip(".").replace(".", "-")
    return re.sub(r"[^a-z0-9]+", "-", re.sub(r"`", "", text.lower())).strip("-")


def lower_title(text):
    parts = re.split(r"(`[^`]*`)", text)
    out = []
    for p in parts:
        if p.startswith("`"):
            out.append(p)
            continue
        q = p.lower()
        for w in PROTECT:
            q = re.sub(re.escape(w.lower()), w, q)
        out.append(q)
    return "".join(out)


def inline(text, first_code_class=None):
    codes = []

    def stash(m):
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    t = re.sub(r"`([^`]*)`", stash, text)
    e = html.escape(t, quote=False)
    e = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", e)
    e = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<em>\1</em>", e)

    def unstash(m):
        i = int(m.group(1))
        inner = codes[i]
        cls = first_code_class if (first_code_class and i == 0) else CODE_CLASS.get(inner.strip().lower())
        c = f' class="{cls}"' if cls else ""
        return f"<code{c}>{html.escape(inner)}</code>"

    return re.sub(r"\x00(\d+)\x00", unstash, e)


PH_RE = re.compile(r"^> \*\*\[(imagen|gif|vídeo|foto) (m[\d.]+-\d+)(?: · ([^\]]*))?\]\*\* (.*)$")


def placeholder(kind, pid, meta, desc):
    meta = meta or ""
    bits = [b.strip() for b in meta.split("·") if b.strip()]
    device = bits[0] if bits else ""
    rest = bits[1:]
    count = 1
    m = re.search(r"×(\d+)", device)
    if m:
        count = int(m.group(1))
        device = device[: m.start()].strip()
    if device.startswith("iphone"):
        shape = "phone"
    elif device.startswith("ipad"):
        shape = "pad"
    elif device.startswith("lámina"):
        shape = "sheet"
    else:
        shape = "photo"
    meta_txt = " · ".join([kind] + ([device] if device else []) + rest)
    boxes = "".join(f'<div class="ph {shape}"><span class="id">{html.escape(pid) if i == 0 else ""}</span></div>'
                    for i in range(count))
    return (f'<figure class="phfig {shape}{" multi" if count > 1 else ""}"><div class="phrow">{boxes}</div>'
            f'<figcaption><span class="pmeta">{html.escape(meta_txt)}</span>{inline(desc)}</figcaption></figure>')


def phone_svg(name, content, label):
    body = gd.phone(0, 0, content).replace("url(#td-screen)", f"url(#td-screen-{name})")
    return (f'<figure class="drawing phonefig"><svg viewBox="-2 -2 204 436" role="img" aria-label="{label}" '
            f'xmlns="http://www.w3.org/2000/svg"><defs><clipPath id="td-screen-{name}" clipPathUnits="userSpaceOnUse">'
            f'<rect x="{gd.SX0}" y="9" width="{gd.SW}" height="414" rx="22"/></clipPath></defs>{body}</svg></figure>')


DRAW_AFTER = {
    "s2": phone_svg("tape", gd.screen_tape(), "dibujo de la pantalla tape"),
    "s3": phone_svg("synth", gd.screen_synth(), "dibujo de la pantalla synth"),
    "s4": phone_svg("track", gd.screen_track(), "dibujo de la pantalla track"),
    "s5": phone_svg("mix", gd.screen_mix(), "dibujo de la pantalla mix"),
}
EQ_FIG = '<figure class="drawing eq-draw">' + gd.eq_drawing() + "</figure>"

blocks = re.split(r"\n\s*\n", md.strip("\n"))
heads = []
for b in blocks:
    m = re.match(r"^(#{2,3}) (?:(\d+(?:\.\d+)*\.?) )?(.*)$", b.strip())
    if m and "\n" not in b.strip():
        lvl = len(m.group(1))
        num = m.group(2) or ""
        heads.append((lvl, num, m.group(3), slug_for(num, m.group(3))))
ids = {h[3] for h in heads}

body, section, eq_done = [], "", False
pending_first_code = None
for b in blocks:
    s = b.strip("\n")
    st = s.strip()
    if not st:
        continue
    if st == "---":
        continue
    m = re.match(r"^(#{2,3}) (?:(\d+(?:\.\d+)*\.?) )?(.*)$", st)
    if m and "\n" not in st:
        lvl, num, title = len(m.group(1)), m.group(2) or "", m.group(3)
        hid = slug_for(num, title)
        section = num.rstrip(".")
        n = f'<span class="num">{html.escape(num.rstrip("."))}</span>' if num else ""
        body.append(f'<h{lvl} id="{hid}">{n}{inline(lower_title(title))}</h{lvl}>')
        if hid in DRAW_AFTER:
            body.append(DRAW_AFTER[hid])
        continue
    lines = s.split("\n")
    if all(l.startswith(">") for l in lines):
        for l in lines:
            pm = PH_RE.match(l)
            if pm:
                fig = placeholder(*pm.groups())
                if body and body[-1].startswith('<div class="phgroup">'):
                    body[-1] = body[-1][:-len("</div>")] + fig + "</div>"
                else:
                    body.append('<div class="phgroup">' + fig + "</div>")
        continue
    joined = " ".join(l.strip() for l in lines)
    nm = re.match(r"^\*\((.*)\)\*$", joined)
    if nm:
        txt = nm.group(1)
        if len(txt) < 90:
            body.append(f'<p class="modenote">{inline(lower_title(txt))}</p>')
        else:
            body.append(f'<p class="aside">{inline(txt)}</p>')
        continue
    para, items = [], []
    for l in lines:
        if l.startswith("- "):
            items.append(l[2:].strip())
        elif l.startswith("  ") and items:
            items[-1] += " " + l.strip()
        elif items:
            items[-1] += " " + l.strip()
        else:
            para.append(l.strip())
    if para:
        body.append(f"<p>{inline(' '.join(para))}</p>")
        if section == "5.6" and not eq_done and "neumático" in " ".join(para):
            pass
    if items:
        mix_fx = section == "5.3" and para and para[0].startswith("**`") and len(items) <= 5
        lis = []
        for i, it in enumerate(items):
            cls = f"g{i+1}" if (mix_fx and i < 4) else None
            h = inline(it, first_code_class=cls)
            if section == "12":
                head, sep, tail = h.rpartition(": ")
                if sep:
                    def link(mm):
                        k = "s" + mm.group(1).replace(".", "-")
                        return f'<a href="#{k}">{mm.group(1)}</a>' if k in ids else mm.group(1)
                    tail = re.sub(r"(?<![\w.#-])(\d+(?:\.\d+)*)(?![\w.])", link, tail)
                    h = head + sep + tail
            lis.append(f"<li>{h}</li>")
        cls = ' class="terms"' if section == "12" else ""
        body.append(f"<ul{cls}>" + "".join(lis) + "</ul>")
        if section == "5.6" and not eq_done:
            body.append(EQ_FIG)
            eq_done = True

toc = []
for lvl, num, title, hid in heads:
    n = num.rstrip(".")
    label = inline(lower_title(title))
    cls = "l3" if lvl == 3 else "l2"
    toc.append(f'<a class="{cls}" href="#{hid}"><span class="tn">{n}</span><span class="tt">{label}</span></a>')

TEMPLATE = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "manual_template.html"), encoding="utf-8").read()
page = TEMPLATE.replace("{{TOC}}", "\n".join(toc)).replace("{{BODY}}", "\n".join(body))
open(OUT, "w", encoding="utf-8").write(page)
print("headings", len(heads), "placeholders", page.count('class="phfig'), "eq", eq_done)
