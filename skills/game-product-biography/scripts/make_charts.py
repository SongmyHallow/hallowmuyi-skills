#!/usr/bin/env python3
"""把图表 JSON 规格渲染成暗色/浅色两张 PNG。

用法：
  python3 make_charts.py spec.json --prefix steam_peak --outdir assets
  python3 make_charts.py spec.json --all specs.json   # 批量

规格（JSON）：
{
  "title": "Steam 同时在线峰值",
  "unit": "万人",
  "kind": "line|area|bar",
  "x": ["2021-08", "2021-09", ...],
  "series": [{"name": "峰值", "values": [12.9, 16.1, null, ...]}],
  "annotations": [{"at": "2023-07", "label": "转免费"}],
  "source": "SteamDB / CSGODT〔E5〕",
  "note": "月度峰值；缺失月留白不插值"
}
输出：<prefix>_dark.png / <prefix>_light.png
"""

import argparse
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

CJK = "Noto Sans CJK SC"
for f in font_manager.findSystemFonts():
    if "NotoSansCJK" in f or "NotoSerifCJK" in f:
        try:
            font_manager.fontManager.addfont(f)
        except Exception:
            pass
plt.rcParams["font.sans-serif"] = [CJK, "PingFang SC", "Microsoft YaHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

PALETTES = {
    "dark": {
        "bg": "#0f131a", "panel": "#151a23", "grid": "#242b37",
        "text": "#e9edf3", "sub": "#8b95a5", "line": "#e3b341",
        "series": ["#e3b341", "#4cc9c0", "#e05d5d", "#8f9bb3"],
        "note": "#8b95a5",
    },
    "light": {
        "bg": "#fffdf8", "panel": "#ffffff", "grid": "#e2ddd2",
        "text": "#1d2026", "sub": "#6d7480", "line": "#a97a10",
        "series": ["#a97a10", "#0f8c84", "#c0392b", "#4a5568"],
        "note": "#6d7480",
    },
}


def _num(v):
    if v is None or v == "":
        return float("nan")
    return float(v)


def draw(spec, theme, path):
    p = PALETTES[theme]
    x = spec.get("x") or []
    series = spec.get("series") or []
    kind = spec.get("kind", "line")
    if not x or not series:
        raise SystemExit("spec 缺少 x 或 series")

    fig, ax = plt.subplots(figsize=(9.6, 4.4), dpi=160)
    fig.patch.set_facecolor(p["bg"])
    ax.set_facecolor(p["panel"])

    n = len(x)
    idx = list(range(n))
    colors = p["series"]
    for si, s in enumerate(series):
        vals = [_num(v) for v in s.get("values", [])][:n]
        color = colors[si % len(colors)]
        if kind == "bar":
            ax.bar(idx, vals, width=0.62, color=color, alpha=0.9, label=s.get("name", ""))
        else:
            if kind == "area":
                ax.fill_between(idx, vals, color=color, alpha=0.18)
            ax.plot(idx, vals, color=color, linewidth=2.2, marker="o", markersize=3.2,
                    label=s.get("name", ""), zorder=3)
            # 标注峰值点
            finite = [(i, v) for i, v in zip(idx, vals) if not math.isnan(v)]
            if finite:
                mi, mv = max(finite, key=lambda t: t[1])
                ax.annotate(f"{mv:g}", (mi, mv), textcoords="offset points", xytext=(0, 9),
                            ha="center", fontsize=9, color=color, fontweight="bold")

    # 网格与坐标轴
    ax.grid(axis="y", color=p["grid"], linewidth=0.8, alpha=0.9, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(p["grid"])
    ax.tick_params(colors=p["sub"], labelsize=9, length=3)

    step = max(1, math.ceil(n / 12))
    ticks = idx[::step]
    ax.set_xticks(ticks)
    ax.set_xticklabels([x[i] for i in ticks], rotation=0, ha="center")
    ax.set_xlim(-0.8, n - 0.2)
    ax.set_ylabel(spec.get("unit", ""), color=p["sub"], fontsize=10)

    title = spec.get("title", "")
    ax.set_title(title, loc="left", fontsize=15, color=p["text"], fontweight="bold", pad=16)

    # 事件竖线
    ann = spec.get("annotations") or []
    for ai, a in enumerate(ann):
        at = a.get("at")
        if at not in x:
            continue
        i = x.index(at)
        ax.axvline(i, color=p["line"], linestyle="--", linewidth=1.1, alpha=0.75, zorder=1)
        y = 0.95 if ai % 2 == 0 else 0.80
        ax.text(i + 0.12, y, a.get("label", ""), transform=ax.get_xaxis_transform(),
                fontsize=8.5, color=p["line"], va="top", ha="left",
                bbox=dict(boxstyle="round,pad=0.25", fc=p["bg"], ec="none", alpha=0.9), zorder=5)

    if len(series) > 1:
        leg = ax.legend(loc="upper right", frameon=False, fontsize=9)
        for t in leg.get_texts():
            t.set_color(p["sub"])

    src = spec.get("source", "")
    note = spec.get("note", "")
    foot = " ｜ ".join([v for v in (src, note) if v])
    if foot:
        fig.text(0.012, 0.018, foot, fontsize=8.2, color=p["note"], ha="left")

    fig.subplots_adjust(left=0.085, right=0.985, top=0.86, bottom=0.15)
    fig.savefig(path, facecolor=p["bg"], edgecolor="none")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description="图表 JSON → 暗/浅 PNG")
    ap.add_argument("spec", nargs="?", help="单个图表 JSON")
    ap.add_argument("--all", help="批量：JSON 数组或 {name: spec} 对象")
    ap.add_argument("--prefix", default="chart", help="输出文件名前缀")
    ap.add_argument("--outdir", default="assets")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)

    jobs = []
    if args.all:
        data = json.load(open(args.all, encoding="utf-8"))
        if isinstance(data, list):
            for i, s in enumerate(data):
                jobs.append((f"{args.prefix}{i+1}", s))
        else:
            for k, s in data.items():
                jobs.append((k, s))
    elif args.spec:
        jobs.append((args.prefix, json.load(open(args.spec, encoding="utf-8"))))
    else:
        raise SystemExit("需要 spec 或 --all")

    out = {}
    for name, spec in jobs:
        dark = os.path.join(args.outdir, f"{name}_dark.png")
        light = os.path.join(args.outdir, f"{name}_light.png")
        draw(spec, "dark", dark)
        draw(spec, "light", light)
        out[name] = {"dark": dark, "light": light}
        print(f"[chart] {name}: {dark} / {light}")
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    sys.exit(main())
