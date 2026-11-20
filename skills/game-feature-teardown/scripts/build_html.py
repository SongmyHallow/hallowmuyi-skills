#!/usr/bin/env python3
"""把拆解报告 Markdown 构建成暗色主题单文件 HTML。

特性：
  - 暗色主题、金色强调，适合长时间阅读
  - 自动生成目录（按 h2/h3）
  - 本地图片自动转为 base64，成品单文件可直接分享
  - 原生支持 Markdown 中内嵌的 HTML 片段（图卡、矩阵、流程图）
  - --block 模式产出可写入飞书 html5-block 的片段（图片保持 URL，不内联 base64）

用法：
  python3 build_html.py report.md --title "《某某》某功能拆解" --out report.html
  python3 build_html.py report.md --block --out widget.html
"""

import argparse
import base64
import mimetypes
import os
import re
import sys

try:
    import markdown
except ImportError:  # pragma: no cover
    markdown = None

def _read(name):
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), name), encoding="utf-8") as f:
        return f.read()


CSS = _read("theme.css")
BLOCK_CSS = _read("block.css")

BLOCK_CSS = """
body{margin:0;background:#0b0d10;color:#e9ecf1;font-family:"PingFang SC","Noto Sans CJK SC",sans-serif}
.wrap{padding:18px 4px}
h3{font-size:17px;margin:0 0 12px;color:#e3b341;font-weight:600}
table{border-collapse:collapse;width:100%;font-size:14px;background:#12161c}
th,td{border:1px solid #242b36;padding:8px 10px;text-align:left}
th{background:#1b222c;color:#fff}
td{color:#d6dbe2}
.opts{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.opt{background:#12161c;border:1px solid #242b36;border-top:3px solid #8a6a24;padding:12px;border-radius:4px}
.opt h4{margin:0 0 6px;font-size:15px;color:#fff}
.opt .tag{font-size:12px;color:#98a1ad}
.opt p{font-size:13px;color:#cdd3db;margin:8px 0 0}
@media (max-width:680px){.opts{grid-template-columns:1fr}}
"""


def inline_images(html, base_dir):
    """本地图片 → base64；远程 URL 保持不动。"""
    def repl(m):
        src = m.group(1)
        if re.match(r"^(http|https|data):", src):
            return m.group(0)
        path = src.lstrip("./")
        if not os.path.isabs(path):
            path = os.path.join(base_dir, path)
        if not os.path.exists(path):
            print(f"[warn] 图片不存在，保留原路径：{src}", file=sys.stderr)
            return m.group(0)
        mime = mimetypes.guess_type(path)[0] or "image/jpeg"
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f'src="data:{mime};base64,{data}"'
    return re.sub(r'src="([^"]+)"', repl, html)


def slug(text, index):
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text).strip("-")
    return f"s{index}-{text[:24]}" if text else f"s{index}"


def build_toc(html):
    entries = []
    counter = 0
    for m in re.finditer(r"<(h2|h3)[^>]*>(.*?)</\1>", html, flags=re.S):
        level, inner = m.group(1), m.group(2)
        counter += 1
        anchor = slug(inner, counter)
        entries.append((level, inner, anchor))
        html = html.replace(m.group(0), f'<{level} id="{anchor}">{inner}</{level}>', 1)
    if not entries:
        return "", html
    lines = ['<nav class="toc" aria-label="目录"><b>CONTENTS</b>']
    for level, inner, anchor in entries:
        cls = "l2" if level == "h3" else ""
        lines.append(f'<a class="{cls}" href="#{anchor}">{inner}</a>')
    lines.append("</nav>")
    return "\n".join(lines), html


def convert(md_text):
    if markdown is None:
        raise SystemExit("缺少 python-markdown，请先安装：pip install markdown")
    return markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
        output_format="html5",
    )


def main():
    p = argparse.ArgumentParser(description="Markdown → 暗色 HTML 报告")
    p.add_argument("source", help="Markdown 文件")
    p.add_argument("--out", default="", help="输出 HTML 路径")
    p.add_argument("--title", default="", help="页面标题（不填则取第一个 h1）")
    p.add_argument("--kicker", default="GAME FEATURE TEARDOWN", help="顶部小标")
    p.add_argument("--subtitle", default="", help="标题下一行说明")
    p.add_argument("--meta", default="", help="元信息，分号分隔")
    p.add_argument("--block", action="store_true", help="输出飞书 html5-block 片段")
    args = p.parse_args()

    path = args.source
    with open(path, encoding="utf-8") as f:
        md_text = f.read()

    h1 = re.search(r"^#\s+(.+)$", md_text, flags=re.M)
    title = args.title or (h1.group(1).strip() if h1 else "功能拆解报告")
    body_md = re.sub(r"^#\s+.+\n", "", md_text, count=1) if h1 else md_text
    html = convert(body_md)
    html = inline_images(html, os.path.dirname(os.path.abspath(path)))

    if args.block:
        out = args.out or "widget.html"
        doc = ("<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
               "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
               "<meta name=\"use-iframe\" content=\"true\">"
               "<meta name=\"html-box-height-mode\" content=\"auto\">"
               f"<meta name=\"description\" content=\"{re.sub('<[^>]+>', '', title)[:80]}\">"
               f"<title>{title}</title><style>{BLOCK_CSS}</style></head>"
               f"<body><div class=\"wrap\">{html}</div></body></html>")
        size = len(doc.encode())
        if size > 500 * 1024:
            print(f"[error] HTML 块 {size/1024:.0f}KB 超过 500KB 上限，请减少内嵌内容", file=sys.stderr)
            return 1
        with open(out, "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"已生成 HTML block：{out}（{size/1024:.1f}KB）")
        return 0

    idx = html.find("<h2")
    lead, body = (html[:idx], html[idx:]) if idx > 0 else ("", html)
    toc, body = build_toc(body)
    meta = "".join(f"<span>{m.strip()}</span>" for m in args.meta.split(";") if m.strip())
    out = args.out or os.path.splitext(path)[0] + ".html"
    clean_title = re.sub(r"<[^>]+>", "", title)
    page = f"""<!doctype html>
<html lang="zh-CN" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{clean_title}</title>
<style>{CSS}</style>
</head>
<body>
<button class="theme-toggle" id="themeBtn" type="button" aria-label="切换浅色/暗色">浅色</button>
<div class="layout">
<aside class="sidebar">
{toc}
</aside>
<main class="content">
<header class="hero">
<div class="kicker">{args.kicker}</div>
<h1>{title}</h1>
{('<p class="sub">' + args.subtitle + '</p>') if args.subtitle else ''}
<div class="meta">{meta}</div>
</header>
{lead}
{body}
</main>
</div>
<script>
(function(){{
  var root=document.documentElement, btn=document.getElementById('themeBtn');
  function sync(){{ btn.textContent = root.dataset.theme === 'light' ? '暗色' : '浅色'; }}
  var saved=null; try{{ saved=localStorage.getItem('teardown-theme'); }}catch(e){{}}
  if(saved) root.dataset.theme=saved; sync();
  btn.addEventListener('click', function(){{
    root.dataset.theme = root.dataset.theme === 'light' ? 'dark' : 'light';
    try{{ localStorage.setItem('teardown-theme', root.dataset.theme); }}catch(e){{}}
    sync();
  }});
  var links=[].slice.call(document.querySelectorAll('.toc a'));
  var targets=links.map(function(a){{ return document.getElementById(a.hash.slice(1)); }}).filter(Boolean);
  function setActive(id){{
    links.forEach(function(a){{ a.classList.toggle('active', a.hash === '#'+id); }});
    var cur=links.filter(function(a){{ return a.hash === '#'+id; }})[0];
    if(cur && cur.scrollIntoView){{ /* 不滚动整页，仅让侧栏可见 */ }}
  }}
  if('IntersectionObserver' in window && targets.length){{
    var io=new IntersectionObserver(function(es){{
      es.forEach(function(en){{ if(en.isIntersecting) setActive(en.target.id); }});
    }},{{rootMargin:'-40% 0px -55% 0px', threshold:0}});
    targets.forEach(function(t){{ io.observe(t); }});
  }}
}})();
</script>
</body>
</html>
"""
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"已生成：{out}（{len(page.encode())/1024:.0f}KB）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
