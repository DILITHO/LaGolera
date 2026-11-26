#!/usr/bin/env python3
"""Genera el sitio estático de noticias de fútbol en docs/. Solo librería estándar."""
import json, html, re, hashlib, urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from pathlib import Path

# ============ CONFIGURA AQUÍ ============
SITE_NAME = "LaGolera"
SITE_URL = "https://dilitho.github.io/LaGolera"      # cámbialo por tu dominio cuando lo compres
CONTACT_EMAIL = "miakalifahud007@gmail.com"
MAX_NEWS = 60                                # noticias en portada
SUMMARY_CHARS = 220                          # extracto corto (no copiamos artículos)
FEEDS = [  # (nombre de la fuente, URL del RSS). Si alguna falla, se ignora.
    ("Marca", "https://e00-marca.uecdn.es/rss/futbol/primera-division.xml"),
    ("AS", "https://as.com/rss/tags/ultimas_noticias.xml"),
    ("Mundo Deportivo", "https://www.mundodeportivo.com/feed/rss/futbol"),
    ("Sport", "https://www.sport.es/es/rss/futbol/rss.xml"),
    ("BBC Sport", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
]
# ========================================

ROOT = Path(__file__).parent
OUT = ROOT / "docs"
CACHE = ROOT / "news.json"
UA = {"User-Agent": f"Mozilla/5.0 (compatible; {SITE_NAME}-bot/1.0)"}

def clean(t, n=None):
    t = re.sub(r"<[^>]+>", " ", html.unescape(t or ""))
    t = re.sub(r"\s+", " ", t).strip()
    if n and len(t) > n:
        t = t[:n].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
    return t

def find_img(item):
    for el in item.iter():
        tag = el.tag.split("}")[-1]
        if tag in ("thumbnail", "content", "enclosure"):
            u = el.get("url")
            if u and re.search(r"\.(jpe?g|png|webp)", u, re.I):
                return u
    m = re.search(r'<img[^>]+src="([^"]+)"', item.findtext("description") or "")
    return m.group(1) if m else ""

def fetch(name, url):
    out = []
    try:
        req = urllib.request.Request(url, headers=UA)
        root = ET.fromstring(urllib.request.urlopen(req, timeout=20).read())
    except Exception as e:
        print(f"[!] {name}: {e}")
        return out
    for it in root.iter("item"):
        link = (it.findtext("link") or "").strip()
        title = clean(it.findtext("title"))
        if not link or not title:
            continue
        try:
            d = parsedate_to_datetime(it.findtext("pubDate")).astimezone(timezone.utc)
        except Exception:
            d = datetime.now(timezone.utc)
        out.append(dict(title=title, link=link, source=name, img=find_img(it),
                        summary=clean(it.findtext("description"), SUMMARY_CHARS),
                        ts=d.timestamp()))
    print(f"[ok] {name}: {len(out)}")
    return out

def ad(name):
    p = ROOT / "ads" / name
    return p.read_text(encoding="utf-8") if p.exists() else ""

def ago(ts):
    s = datetime.now(timezone.utc).timestamp() - ts
    if s < 3600: return f"hace {max(1, int(s/60))} min"
    if s < 86400: return f"hace {int(s/3600)} h"
    return f"hace {int(s/86400)} d"

CSS = """
:root{--bg:#f6f5ef;--card:#fff;--ink:#14231c;--mute:#5d6b63;--line:#d9ddd2;--turf:#0f3d2e;--card-y:#f2c300}
@media(prefers-color-scheme:dark){:root{--bg:#0d1612;--card:#15211b;--ink:#eef2ec;--mute:#9aa8a0;--line:#26362d;--turf:#0a2a1f}}
*{box-sizing:border-box}html{scroll-padding-top:70px}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.55 "Source Sans 3",system-ui,sans-serif}
a{color:inherit;text-decoration:none}a:focus-visible{outline:3px solid var(--card-y);outline-offset:2px}
header{background:var(--turf);color:#fff;border-bottom:4px solid var(--card-y)}
.wrap{max-width:1120px;margin:0 auto;padding:0 18px}
.bar{display:flex;align-items:center;justify-content:space-between;padding:14px 0;gap:12px}
.logo{font:800 28px/1 Archivo,Impact,sans-serif;letter-spacing:-.5px}
.logo i{display:inline-block;width:.7em;height:.7em;border-radius:50%;background:var(--card-y);margin-right:8px}
nav a{margin-left:16px;font-size:15px;opacity:.9}
.lead{display:grid;grid-template-columns:2fr 1fr;gap:22px;margin:24px 0}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:6px;overflow:hidden;display:flex;flex-direction:column}
.card:hover h2,.card:hover h3{text-decoration:underline}
.card img{width:100%;aspect-ratio:16/9;object-fit:cover;background:var(--line)}
.card div{padding:12px 14px 16px}
.card h2,.card h3{font:800 19px/1.2 Archivo,Impact,sans-serif;margin:6px 0}
.card p{margin:0;color:var(--mute);font-size:15px}
.meta{font-size:13px;color:var(--mute)}.meta b{color:var(--turf)}
@media(prefers-color-scheme:dark){.meta b{color:var(--card-y)}}
.hero h2{font-size:30px}.hero img{aspect-ratio:16/8}
.ad{margin:22px auto;text-align:center;min-height:20px;overflow:hidden}
.side{display:flex;flex-direction:column;gap:14px}
.page{max-width:720px;margin:32px auto;padding:0 18px}.page h1{font:800 34px Archivo,sans-serif}
footer{margin-top:40px;padding:24px 0;border-top:1px solid var(--line);color:var(--mute);font-size:14px}
footer a{margin-right:14px;text-decoration:underline}
@media(max-width:760px){.lead{grid-template-columns:1fr}nav a{margin-left:10px}}
"""

def shell(title, body, desc="Noticias de fútbol al minuto: LaLiga, Champions y más."):
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><meta name="description" content="{html.escape(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wght@800&family=Source+Sans+3:wght@400;600&display=swap" rel="stylesheet">
<style>{CSS}</style>
{ad("head.html")}
</head><body>
<header><div class="wrap bar"><a class="logo" href="./"><i></i>{SITE_NAME}</a>
<nav><a href="./">Portada</a><a href="sobre-nosotros.html">Sobre nosotros</a><a href="contacto.html">Contacto</a></nav></div></header>
{body}
<footer><div class="wrap"><a href="sobre-nosotros.html">Sobre nosotros</a><a href="contacto.html">Contacto</a>
<a href="privacidad.html">Privacidad</a><a href="cookies.html">Cookies</a>
<p>© {datetime.now().year} {SITE_NAME}. Agregamos titulares y extractos de medios deportivos con enlace a la fuente original; los derechos pertenecen a sus autores.</p></div></footer>
{ad("body-end.html")}
</body></html>"""

def card(n, big=False):
    img = f'<img src="{html.escape(n["img"])}" alt="" loading="lazy">' if n["img"] else '<img alt="">'
    h = "h2" if big else "h3"
    return (f'<a class="card{" hero" if big else ""}" href="{html.escape(n["link"])}" target="_blank" rel="noopener nofollow">{img}'
            f'<div><span class="meta"><b>{html.escape(n["source"])}</b> · {ago(n["ts"])}</span>'
            f'<{h}>{html.escape(n["title"])}</{h}><p>{html.escape(n["summary"])}</p></div></a>')

def main():
    news = []
    for name, url in FEEDS:
        news += fetch(name, url)
    if news:
        seen, uniq = set(), []
        for n in sorted(news, key=lambda x: -x["ts"]):
            k = re.sub(r"\W+", "", n["title"].lower())[:60]
            if k in seen: continue
            seen.add(k); uniq.append(n)
        news = uniq[:MAX_NEWS]
        CACHE.write_text(json.dumps(news, ensure_ascii=False), encoding="utf-8")
    elif CACHE.exists():
        news = json.loads(CACHE.read_text(encoding="utf-8"))  # si todo falla, usa la última copia

    OUT.mkdir(exist_ok=True)
    if news:
        side = "".join(card(n) for n in news[1:3])
        rest = news[3:]
        grid = ""
        for i in range(0, len(rest), 6):
            grid += '<div class="grid">' + "".join(card(n) for n in rest[i:i+6]) + "</div>"
            if i + 6 < len(rest): grid += f'<div class="ad">{ad("in-feed.html")}</div>'
        main_html = (f'<div class="lead">{card(news[0], True)}<div class="side">{side}'
                     f'<div class="ad">{ad("sidebar.html")}</div></div></div>{grid}')
    else:
        main_html = '<p>Aún no hay noticias. Vuelve en unos minutos.</p>'
    upd = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")
    body = (f'<main class="wrap"><div class="ad">{ad("top-banner.html")}</div>{main_html}'
            f'<p class="meta">Actualizado: {upd}</p><div class="ad">{ad("bottom-banner.html")}</div></main>')
    (OUT / "index.html").write_text(shell(f"{SITE_NAME} – Noticias de fútbol", body), encoding="utf-8")

    pages = {
     "sobre-nosotros": ("Sobre nosotros", f"<p>{SITE_NAME} reúne cada hora los titulares más recientes del fútbol: LaLiga, Champions League, selecciones y mercado de fichajes. Mostramos el titular, un extracto breve y el enlace a la noticia completa en el medio original.</p><p>No producimos las noticias; las organizamos para que veas todo en un solo lugar.</p>"),
     "contacto": ("Contacto", f"<p>¿Dudas, sugerencias o quieres que retiremos un enlace? Escríbenos a <a href='mailto:{CONTACT_EMAIL}'><u>{CONTACT_EMAIL}</u></a>.</p>"),
     "privacidad": ("Política de privacidad", f"<p>{SITE_NAME} no pide registro ni recoge datos personales directamente. Sin embargo, usamos servicios de terceros (como la red publicitaria Adsterra) que pueden usar cookies e identificadores para mostrar anuncios y medir su rendimiento.</p><p>Puedes desactivar o borrar las cookies desde la configuración de tu navegador. Los enlaces a medios externos se rigen por la política de privacidad de cada medio.</p><p>Para cualquier solicitud sobre tus datos escribe a {CONTACT_EMAIL}.</p>"),
     "cookies": ("Política de cookies", "<p>Este sitio y sus anunciantes usan cookies para mostrar publicidad y analizar el tráfico. Al seguir navegando aceptas su uso. Puedes bloquearlas o eliminarlas en cualquier momento desde tu navegador.</p>"),
    }
    for slug, (t, b) in pages.items():
        (OUT / f"{slug}.html").write_text(shell(f"{t} – {SITE_NAME}", f'<main class="page"><h1>{t}</h1>{b}</main>'), encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    urls = ["", *[f"/{s}.html" for s in pages]]
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{SITE_URL}{u}</loc></url>" for u in urls) + "</urlset>")
    print(f"Sitio generado: {len(news)} noticias")

if __name__ == "__main__":
    main()
