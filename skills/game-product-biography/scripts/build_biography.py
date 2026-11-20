#!/usr/bin/env python3
"""把产品传记 Markdown 构建成暗色主题单文件 HTML。

支持三种自定义块（写在 ```chart / ```timeline / ```node 围栏里，内容是 JSON）：
  chart     数据图，构建时自动渲染暗/浅两张 PNG（需要 matplotlib）
  timeline  阶段年表，横向时间轴
  node      关键节点卡（波峰/波谷/转折/事件），含「之前/当时/之后」三栏

用法：
  python3 build_biography.py bio.md --title "《永劫无间》产品生平" \
      --subtitle "……" --meta "PC;2021-08 至今;18 条证据" --out bio.html
"""

import argparse
import base64
import json
import mimetypes
import os
import re
import sys

import markdown

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from make_charts import draw  # noqa: E402

CSS = open(os.path.join(HERE, "theme.css"), encoding="utf-8").read()

BLOCK_RE = re.compile(r"```(chart|timeline|node)\s*\n(.*?)\n```", re.S)
PLACE_RE = re.compile(r"<!--BIOBLOCK(\d+)-->")
FENCE_RE = re.compile(r"```(\w+)?\s*\n(.*?)\n```", re.S)

BADGE = {"peak": "波峰", "trough": "波谷", "turn": "转折", "event": "事件"}


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def render_chart(spec, base_dir, i):
    cid = spec.get("id") or f"biochart{i}"
    assets = os.path.join(base_dir, "assets")
    os.makedirs(assets, exist_ok=True)
    dark = os.path.join(assets, f"{cid}_dark.png")
    light = os.path.join(assets, f"{cid}_light.png")
    draw(spec, "dark", dark)
    draw(spec, "light", light)
    cap = esc(spec.get("caption", ""))
    ev = esc(spec.get("ev", ""))
    cap_html = f"{cap}（{ev}）" if ev else cap
    return (f'<figure class="chart-figure"><img class="chart" src="assets/{cid}_dark.png" '
            f'data-light="assets/{cid}_light.png" alt="{esc(spec.get("title", "数据图"))}">'
            f'<figcaption>{cap_html}</figcaption></figure>')


def render_timeline(spec):
    items = []
    for s in spec.get("stages", []):
        tone = s.get("tone", "normal")
        tone = tone if tone in ("peak", "trough", "turn") else ""
        items.append(
            f'<div class="tl-item {tone}"><span class="tl-dot"></span>'
            f'<div class="tl-period">{esc(s.get("period",""))}</div>'
            f'<div class="tl-title">{esc(s.get("title",""))}</div>'
            f'<div class="tl-desc">{esc(s.get("desc",""))}</div></div>'
        )
    return f'<div class="timeline">{"".join(items)}</div>'


def render_node(spec):
    typ = spec.get("type", "event")
    typ = typ if typ in BADGE else "event"
    mets = "".join(
        f'<div><span>{esc(m.get("label",""))}</span><strong>{esc(m.get("value",""))}</strong></div>'
        for m in spec.get("metrics", [])
    )
    ev = esc(spec.get("evidence", ""))
    ev_html = f'<div class="node-ev">证据：{ev}</div>' if ev else ""
    return f"""<section class="node {typ}">
<div class="node-head"><span class="badge {typ}">{BADGE[typ]}</span><time>{esc(spec.get("date",""))}</time></div>
<div class="node-title">{esc(spec.get("title",""))}</div>
<p class="verdict">{esc(spec.get("verdict",""))}</p>
{('<div class="metrics">' + mets + '</div>') if mets else ''}
<div class="node-grid">
<div><h4>之前</h4><p>{esc(spec.get("before",""))}</p></div>
<div><h4>当时</h4><p>{esc(spec.get("during",""))}</p></div>
<div><h4>之后</h4><p>{esc(spec.get("after",""))}</p></div>
</div>
{ev_html}
</section>"""


def extract_blocks(md_text, base_dir):
    blocks = []

    def repl(m):
        kind, body = m.group(1), m.group(2).strip()
        try:
            spec = json.loads(body)
        except json.JSONDecodeError as e:
            raise SystemExit(f"[error] {kind} 块的 JSON 解析失败：{e}\n{body[:200]}")
        i = len(blocks)
        if kind == "chart":
            html = render_chart(spec, base_dir, i)
        elif kind == "timeline":
            html = render_timeline(spec)
        else:
            html = render_node(spec)
        blocks.append(html)
        return f"<!--BIOBLOCK{i}-->"

    return BLOCK_RE.sub(repl, md_text), blocks


def inline_images(html, base_dir):
    def repl(m):
        attr, src = m.group(1), m.group(2)
        if re.match(r"(http|https|data):", src):
            return m.group(0)
        path = src if os.path.isabs(src) else os.path.join(base_dir, src)
        if not os.path.exists(path):
            print(f"[warn] 图片不存在：{src}", file=sys.stderr)
            return m.group(0)
        mime = mimetypes.guess_type(path)[0] or "image/png"
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f'{attr}="data:{mime};base64,{data}"'

    return re.sub(r'(src|data-light)="([^"]+)"', repl, html)


def slug(text, index):
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text).strip("-")
    return f"s{index}-{text[:24]}" if text else f"s{index}"


def build_toc(html):
    entries = []
    for i, m in enumerate(re.finditer(r"<(h2|h3)[^>]*>(.*?)</\1>", html, flags=re.S), 1):
        level, inner = m.group(1), m.group(2)
        anchor = slug(inner, i)
        entries.append((level, inner, anchor))
        html = html.replace(m.group(0), f'<{level} id="{anchor}">{inner}</{level}>', 1)
    lines = ['<nav class="toc" aria-label="目录"><b>CONTENTS</b>']
    for level, inner, anchor in entries:
        cls = "l2" if level == "h3" else ""
        lines.append(f'<a class="{cls}" href="#{anchor}">{inner}</a>')
    lines.append("</nav>")
    return "\n".join(lines), html


def main():
    ap = argparse.ArgumentParser(description="传记 Markdown → 暗色 HTML")
    ap.add_argument("source")
    ap.add_argument("--out", default="")
    ap.add_argument("--title", default="")
    ap.add_argument("--kicker", default="GAME BIOGRAPHY · 产品生平")
    ap.add_argument("--subtitle", default="")
    ap.add_argument("--meta", default="", help="分号分隔")
    args = ap.parse_args()

    with open(args.source, encoding="utf-8") as f:
        md_text = f.read()
    base_dir = os.path.dirname(os.path.abspath(args.source))

    h1 = re.search(r"^#\s+(.+)$", md_text, flags=re.M)
    title = args.title or (h1.group(1).strip() if h1 else "产品生平")
    body_md = re.sub(r"^#\s+.+\n", "", md_text, count=1) if h1 else md_text

    body_md, blocks = extract_blocks(body_md, base_dir)
    html = markdown.markdown(
        body_md,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list", "md_in_html"],
        output_format="html5",
    )
    def put(m):
        return blocks[int(m.group(1))]

    html = PLACE_RE.sub(put, html)
    html = re.sub(r"<p>\s*(<!--BIOBLOCK)", r"\1", html)
    html = re.sub(r"(-->)\s*</p>", r"\1", html)
    html = inline_images(html, base_dir)

    idx = html.find("<h2")
    lead, body = (html[:idx], html[idx:]) if idx > 0 else ("", html)
    toc, body = build_toc(body)
    meta = "".join(f"<span>{esc(x.strip())}</span>" for x in args.meta.split(";") if x.strip())
    out = args.out or os.path.splitext(args.source)[0] + ".html"

    page = f"""<!doctype html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<style>{CSS}</style>
</head>
<body>
<div class="progress" id="bar"></div>
<button class="theme-toggle" id="themeBtn" type="button">浅色</button>
<div class="layout">
<aside class="sidebar">{toc}</aside>
<main class="content">
<header class="hero">
<div class="kicker">{esc(args.kicker)}</div>
<h1>{esc(title)}</h1>
{('<p class="sub">' + args.subtitle + '</p>') if args.subtitle else ''}
<div class="meta">{meta}</div>
</header>
{lead}
{body}
</main>
</div>
<button class="totop" id="totop" type="button" aria-label="回到顶部">↑</button>
<script>
(function(){{
  var root=document.documentElement, btn=document.getElementById('themeBtn');
  var bar=document.getElementById('bar'), top=document.getElementById('totop');
  var charts=[].slice.call(document.querySelectorAll('img.chart'));
  charts.forEach(function(im){{ im.dataset.dark=im.getAttribute('src'); }});
  function paint(){{
    var light = root.dataset.theme === 'light';
    btn.textContent = light ? '暗色' : '浅色';
    charts.forEach(function(im){{
      im.src = light ? (im.dataset.light || im.dataset.dark) : im.dataset.dark;
    }});
  }}
  var saved=null; try{{ saved=localStorage.getItem('bio-theme'); }}catch(e){{}}
  if(saved) root.dataset.theme=saved; paint();
  btn.addEventListener('click', function(){{
    root.dataset.theme = root.dataset.theme === 'light' ? 'dark' : 'light';
    try{{ localStorage.setItem('bio-theme', root.dataset.theme); }}catch(e){{}}
    paint();
  }});
  var links=[].slice.call(document.querySelectorAll('.toc a'));
  var targets=links.map(function(a){{ return document.getElementById(a.hash.slice(1)); }}).filter(Boolean);
  function setActive(id){{ links.forEach(function(a){{ a.classList.toggle('active', a.hash === '#'+id); }}); }}
  if('IntersectionObserver' in window && targets.length){{
    var io=new IntersectionObserver(function(es){{
      es.forEach(function(en){{ if(en.isIntersecting) setActive(en.target.id); }});
    }},{{rootMargin:'-35% 0px -60% 0px', threshold:0}});
    targets.forEach(function(t){{ io.observe(t); }});
  }}
  window.addEventListener('scroll', function(){{
    var h=document.body.scrollHeight-window.innerHeight;
    bar.style.width = (h>0 ? (window.scrollY/h*100) : 0) + '%';
    top.style.display = window.scrollY > 600 ? 'block' : 'none';
  }});
  top.addEventListener('click', function(){{ window.scrollTo({{top:0,behavior:'smooth'}}); }});
}})();
</script>
</body>
</html>
"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"已生成：{out}（{len(page.encode())/1024:.0f}KB）")


if __name__ == "__main__":
    sys.exit(main())
