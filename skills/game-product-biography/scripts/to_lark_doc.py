#!/usr/bin/env python3
"""把传记 Markdown 转成飞书文档友好的 Markdown。

- chart 块 -> 浅色图表 PNG + 图注
- timeline 块 -> 原生表格
- node 块 -> 节点小节（判定 / 关键数据 / 之前·当时·之后 / 证据）
- <figure> -> Markdown 图片（alt 即图注）
- 首个 H1 换成 callout 元信息 + 判词（文档标题走 --title）

用法：
  python3 to_lark_doc.py 永劫无间_产品生平.md --assets ./assets --out _feishu.md
"""
import argparse, json, re, sys
from pathlib import Path

CHART_SUFFIX = "_light.png"
TYPE_LABEL = {"peak": "波峰", "trough": "波谷", "turn": "转折", "event": "事件"}


def load_blocks(md):
    """把 ```kind\\n{json}\\n``` 换成占位符，返回 (文本, 块列表)。"""
    blocks = []
    def repl(m):
        blocks.append((m.group(1), json.loads(m.group(2))))
        return f"\n@@BLOCK{len(blocks)-1}@@\n"
    text = re.sub(r"```(timeline|node|chart)\n(.*?)\n```", repl, md, flags=re.S)
    return text, blocks


def render_timeline(d):
    rows = ["| 阶段 | 时间 | 主线 |", "|---|---|---|"]
    for s in d["stages"]:
        rows.append(f"| **{s['title']}** | {s['period']} | {s['desc']} |")
    return "\n".join(rows)


def render_node(d, idx):
    kind = TYPE_LABEL.get(d.get("type"), "节点")
    lines = [f"### 节点 {idx}｜{d['date']}｜{kind} · {d['title']}", "", f"**判定**：{d['verdict']}", ""]
    if d.get("metrics"):
        lines.append("**关键数据**：" + " ｜ ".join(f"{m['label']} {m['value']}" for m in d["metrics"]))
        lines.append("")
    for key, label in (("before", "之前"), ("during", "当时"), ("after", "之后")):
        if d.get(key):
            lines.append(f"- **{label}**：{d[key]}")
    lines += ["", f"证据：{d.get('evidence', '')}", ""]
    return "\n".join(lines)


def render_chart(d, assets):
    img = Path(assets) / (d["id"] + CHART_SUFFIX)
    if not img.exists():
        img = Path(assets) / (d["id"] + "_dark.png")
    if not img.exists():
        print(f"[warn] 图表不存在：{img}", file=sys.stderr)
    alt = f"图：{d['title']}"
    note = f"（{d['caption']}）" if d.get("caption") else ""
    return f"![{alt}](@./{img.as_posix()})\n\n{note}\n"


def render_figure(m, assets):
    src, cap = m.group("src"), m.group("cap")
    return f"![{cap}](@./{src})\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    ap.add_argument("--assets", default="./assets")
    ap.add_argument("--out", default="_feishu.md")
    a = ap.parse_args()

    raw = Path(a.md).read_text(encoding="utf-8")
    text = raw
    text, blocks = load_blocks(text)

    # 标题：取第一行 H1，正文改为元信息 callout
    m = re.match(r"#\s+(.*)\n", text)
    title = m.group(1).strip() if m else Path(a.md).stem
    text = text[m.end():] if m else text

    # 判词引用块 -> callout
    q = re.search(r">\s*\*\*判词\*\*：(.+?)\n", text)
    verdict = q.group(1).strip() if q else ""
    text = re.sub(r">\s*\*\*判词\*\*：.+\n", "", text)

    evidence = len(re.findall(r"^\| (E\d+) \|", raw, re.M))
    callout = (
        '<callout emoji="📌">\n'
        f"**{title}**　产品生平 / 游戏史复盘\n\n"
        f"**口径**：Steam + 小黑盒（含官服）+ 官方财报与公告　|　**证据**：{evidence} 条　|　**截稿**：2026-11\n\n"
        f"**判词**：{verdict}\n"
        "</callout>\n"
    )
    text = callout + "\n" + text.lstrip()

    # 图表 / 年表 / 节点
    def block_repl(mm):
        i = int(mm.group(1))
        kind, d = blocks[i]
        if kind == "timeline":
            return render_timeline(d) + "\n"
        if kind == "node":
            return render_node(d, sum(1 for k, _ in blocks[: i + 1] if k == "node")) + "\n"
        return render_chart(d, a.assets)

    text = re.sub(r"@@BLOCK(\d+)@@", block_repl, text)

    # 图片 figure
    text = re.sub(
        r'<figure><img src="(?P<src>[^"]+)" alt="[^"]*"><figcaption>(?P<cap>.*?)</figcaption></figure>',
        lambda m: render_figure(m, a.assets), text, flags=re.S,
    )

    # 飞书里 〔E6〕 较长，统一成（E6）更好读
    text = text.replace("〔", "（").replace("〕", "）")

    out = Path(a.out)
    out.write_text(text, encoding="utf-8")
    print(f"已生成：{out}（{len(text)} 字，标题：{title}）")


if __name__ == "__main__":
    main()
