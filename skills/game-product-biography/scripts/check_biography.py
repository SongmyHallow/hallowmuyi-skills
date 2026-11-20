#!/usr/bin/env python3
"""产品传记交付前自检（七段式 + 图表/节点规范）。

七段：1 现状侧写 → 2 生平年表 → 3 关键节点 → 4 起伏曲线 →
      5 兴衰解剖 → 6 可迁移的教训 → 7 证据与存疑

用法：python3 check_biography.py bio.md
退出码：0 通过（可带警告）；1 有错误。
"""

import argparse
import json
import re
import sys

SECTIONS = {
    1: "现状侧写", 2: "生平年表", 3: "关键节点", 4: "起伏曲线",
    5: "兴衰解剖", 6: "可迁移的教训", 7: "证据与存疑",
}
SEC_RE = re.compile(r"^##\s+(\d)\.\s*(.*)$")
EVID_RE = re.compile(r"〔?E(\d+)〕?")
EVID_TAG = re.compile(r"〔E(\d+)〕")
INFER_RE = re.compile(r"〔推断")
NUM_RE = re.compile(r"\d+(?:\.\d+)?\s*(%|万|亿|元|万份|万人)")
BLOCK_RE = re.compile(r"```(chart|timeline|node)\s*\n(.*?)\n```", re.S)
PLACE_RE = re.compile(r"〔[^〕]*待填[^〕]*〕|【[^】]*】|TRIM")


def sections(lines):
    found = [(int(m.group(1)), m.group(2).strip(), i) for i, l in enumerate(lines, 1)
             if (m := SEC_RE.match(l))]
    errs = []
    if not found:
        return [], ["未找到 `## N. 章节` 标题"]
    nums = [n for n, _, _ in found]
    if nums != sorted(nums):
        errs.append(f"章节顺序错误：{nums}")
    miss = [n for n in SECTIONS if n not in nums]
    if miss:
        errs.append("缺少章节：" + "、".join(f"{n}.{SECTIONS[n]}" for n in miss))
    dup = [n for n in set(nums) if nums.count(n) > 1]
    if dup:
        errs.append(f"章节编号重复：{dup}")
    return found, errs


def section_body(lines, found, n):
    start = next((i for num, _, i in found if num == n), None)
    if start is None:
        return ""
    end = next((i for num, _, i in found if num > n), len(lines) + 1)
    return "\n".join(lines[start - 1:end - 1])


def parse_blocks(text):
    out, errs = [], []
    for kind, body in BLOCK_RE.findall(text):
        try:
            out.append((kind, json.loads(body)))
        except json.JSONDecodeError as e:
            errs.append(f"{kind} 块 JSON 解析失败：{e}")
    return out, errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    args = ap.parse_args()
    text = open(args.report, encoding="utf-8").read()
    lines = text.splitlines()
    found, errs = sections(lines)
    blocks, berrs = parse_blocks(text)
    errs += berrs
    warns = []

    # 1 现状
    s1 = section_body(lines, found, 1)
    if "官方" not in s1:
        errs.append("第 1 节缺少官方口径（财报/公告/官方数据）")
    if not any(k in s1 for k in ("社区", "舆论", "评测")):
        errs.append("第 1 节缺少社区舆论角度")
    if len(s1) < 600:
        warns.append("第 1 节偏短，现状侧写建议 ≥600 字")

    # 2 年表
    s2 = section_body(lines, found, 2)
    tls = [s for k, s in blocks if k == "timeline"]
    stages = sum(len(s.get("stages", [])) for s in tls)
    if stages < 5:
        errs.append(f"年表只覆盖 {stages} 个阶段，至少 5 个")
    timeline_text = " ".join(
        f"{s.get('title','')}{s.get('desc','')}" for tl in tls for s in tl.get("stages", [])
    )
    if not any(k in (s2 + timeline_text) for k in ("上线", "公测", "开服")):
        warns.append("年表未提及上线/公测节点")

    # 3 节点
    nodes = [s for k, s in blocks if k == "node"]
    if len(nodes) < 5:
        errs.append(f"关键节点只有 {len(nodes)} 个，至少 5 个")
    types = [s.get("type") for s in nodes]
    if "peak" not in types:
        errs.append("关键节点缺少波峰（type=peak）")
    if "trough" not in types:
        errs.append("关键节点缺少波谷（type=trough）")
    for i, n in enumerate(nodes, 1):
        for key in ("date", "title", "verdict", "before", "during", "after", "evidence"):
            if not n.get(key):
                errs.append(f"节点 {i}「{n.get('title','?')}」缺少字段 {key}")
        if len(n.get("before", "")) < 20 or len(n.get("after", "")) < 20:
            warns.append(f"节点 {i} 的「之前/之后」过短，因果链可能不完整")

    # 4 曲线
    s4 = section_body(lines, found, 4)
    charts = [s for k, s in blocks if k == "chart"]
    if len(charts) < 2:
        errs.append(f"起伏曲线只有 {len(charts)} 张图，至少 2 张")
    for i, c in enumerate(charts, 1):
        if not c.get("source"):
            errs.append(f"图表 {i} 缺少 source（数据出处）")
        if not c.get("caption"):
            errs.append(f"图表 {i} 缺少 caption（图注）")
        if not c.get("x") or not c.get("series"):
            errs.append(f"图表 {i} 缺少 x 或 series")
    if not any(k in s4 for k in ("口径", "Steam 口径", "统计范围")):
        warns.append("第 4 节未说明数据口径（Steam/小黑盒/官方口径必须分开）")

    # 5 因子
    s5 = section_body(lines, found, 5)
    if "|" not in s5:
        errs.append("第 5 节缺少驱动因子表")
    elif len([l for l in s5.splitlines() if l.strip().startswith("|")]) < 6:
        warns.append("驱动因子表行数偏少，建议 ≥5 个因子")

    # 6 教训
    s6 = section_body(lines, found, 6)
    items = [l for l in s6.splitlines() if re.match(r"^\s*(?:\d+\.|[-*])\s+\S", l)]
    if len(items) < 3:
        errs.append(f"可迁移教训只有 {len(items)} 条，至少 3 条")

    # 7 证据
    s7 = section_body(lines, found, 7)
    rows = [l for l in s7.splitlines() if l.strip().startswith("|")]
    if len(rows) < 4:
        errs.append("7.1 证据表为空或行数过少")
    else:
        header = [c.strip() for c in rows[0].strip().strip("|").split("|")]
        src = next((i for i, c in enumerate(header) if "来源" in c), None)
        if src is None:
            errs.append("证据表缺少「来源」列")
        else:
            bad = sum(1 for l in rows[2:] if len([c for c in l.strip().strip("|").split("|")]) <= src
                      or "http" not in l.strip().strip("|").split("|")[src])
            if bad:
                errs.append(f"证据表 {bad} 行来源列没有可点击链接")
    defined = set(int(m.group(1)) for l in rows[2:] if (m := re.match(r"\|\s*E(\d+)", l.strip())))
    used = set(int(m) for m in EVID_TAG.findall(text))
    undef = sorted(used - defined)
    if undef:
        errs.append("正文引用了证据表里没有的编号：" + ", ".join(f"E{n}" for n in undef))
    missing = [n for n in range(1, max(defined or {0}) + 1) if n not in defined]
    if missing:
        errs.append("证据编号缺号：" + ", ".join(f"E{n}" for n in missing))
    if not any("存疑" in l for l in s7.splitlines()):
        errs.append("第 7 节缺少「存疑点」")
    doubt = [l for l in s7.splitlines() if re.match(r"^\s*(?:\d+\.|[-*])\s+\S", l)]
    if len(doubt) < 2:
        errs.append("存疑点少于 2 条")

    # 通用
    in_fence = False
    for i, l in enumerate(lines, 1):
        if l.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if PLACE_RE.search(l):
            errs.append(f"第 {i} 行残留模板占位符：{l.strip()[:40]}")
        if INFER_RE.search(l) and not re.search(r"依据|E\d", l) and "|" not in l:
            warns.append(f"第 {i} 行〔推断〕未写依据")
        if NUM_RE.search(l) and not EVID_RE.search(l) and not l.strip().startswith(("|", "<")):
            warns.append(f"第 {i} 行精确数值无证据标注：{l.strip()[:50]}")

    ev_count = len(defined)
    print(f"文件：{args.report}")
    print(f"规模：{len(text)} 字 | 证据 {ev_count} 条 | 节点 {len(nodes)} 个 | 图 {len(charts)} 张 | 阶段 {stages} 个")
    if errs:
        print(f"\n错误 {len(errs)} 项：")
        for e in errs:
            print("  [ERROR] " + e)
    else:
        print("\n结构检查：通过")
    if warns:
        print(f"\n警告 {len(warns)} 项：")
        for w in warns[:10]:
            print("  [WARN] " + w)
    if len(text) < 5000:
        warns.append("全文不足 5000 字，生平传记信息密度可能不够")
    if errs:
        return 1
    print("\n结论：可交付（接着跑 build_biography.py 生成暗色 HTML）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
