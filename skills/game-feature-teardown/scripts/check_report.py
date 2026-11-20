#!/usr/bin/env python3
"""拆解报告交付前自检（六段式 + 视觉规范）。

检查项：
  1. 六段章节齐全、顺序正确（1 功能本体 → 2 产品分布 → 3 设计目的 → 4 本土化魔改 → 5 方法论 → 6 证据与存疑）
  2. 第 1 节必备：口径、系统位置（含位置图）、规则与数值
  3. 截图不少于 2 张；每个 <figure> 都要有 <figcaption>；图注建议带证据编号
  4. 至少 1 张数据/图表类图片（文件名含 chart 或扩展名 .svg/.png）
  5. 证据表每行「来源」列必须是可点击链接（http），不允许裸文本
  6. 模板占位符残留、Markdown 表格列数、证据编号连续性、存疑清单条数
  7. 警告：〔推断〕缺依据、无证据的精确数值、对比表缺「证据」列

用法：
  python3 check_report.py <报告.md>
退出码：0 = 通过（可能有警告）；1 = 存在错误。
"""

import argparse
import re
import sys

SECTIONS = {
    1: "功能本体",
    2: "产品分布",
    3: "设计目的",
    4: "本土化魔改",
    5: "方法论",
    6: "证据与存疑",
}
SECTION_RE = re.compile(r"^##\s+(\d)\.\s*(.*)$")
SUB_RE = re.compile(r"^###\s+(\d)\.(\d)\s*(.*)$")
PLACEHOLDER_RE = re.compile(r"\[[^\[\]]*[\u4e00-\u9fff][^\[\]]*\]")
EVIDENCE_RE = re.compile(r"E(\d+)")
INFER_RE = re.compile(r"〔推断")
BASIS_RE = re.compile(r"依据|E\d")
NUM_RE = re.compile(r"\d+(?:\.\d+)?\s*(%|元|倍)")
INLINE_CHECKBOX = re.compile(r"\[[ xX]\]")
FIG_RE = re.compile(r"<figure[^>]*>(.*?)</figure>", re.S | re.I)
IMG_RE = re.compile(r"<img[^>]+src=\"([^\"]+)\"", re.I)
MD_IMG_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
SRC_LINK_RE = re.compile(r"\](https?://|\()|https?://")


def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def check_sections(lines):
    errors = []
    found = []
    for i, line in enumerate(lines, 1):
        m = SECTION_RE.match(line)
        if m:
            found.append((int(m.group(1)), m.group(2).strip(), i))
    if not found:
        return ["未找到任何 `## N. 章节` 标题，报告可能不是六段式"]
    nums = [n for n, _, _ in found]
    if nums != sorted(nums):
        errors.append(f"章节顺序错误：实际为 {nums}，应为 1→6")
    missing = [n for n in SECTIONS if n not in nums]
    if missing:
        errors.append("缺少章节：" + "、".join(f"第{n}章（{SECTIONS[n]}）" for n in missing))
    extra = [n for n in nums if n not in SECTIONS]
    if extra:
        errors.append(f"出现六段式以外的编号章节：{extra}（如需附注用 `## 附：…` 或 `## 交付检查`）")
    dup = [n for n in set(nums) if nums.count(n) > 1]
    if dup:
        errors.append(f"章节编号重复：{dup}")
    return errors


def check_section1(lines):
    """第 1 节要能让没玩过的人看懂：口径、系统位置图、规则与数值都必须有。"""
    errors = []
    idx = next((i for i, l in enumerate(lines) if re.match(r"^##\s+1\.", l)), None)
    if idx is None:
        return ["未找到第 1 节，无法检查功能本体"]
    end = next((i for i, l in enumerate(lines[idx + 1:], idx + 1) if re.match(r"^##\s+", l)), len(lines))
    body = "\n".join(lines[idx:end])
    for key, msg in [
        ("口径", "第 1 节缺少「口径」说明（同名功能必须消歧）"),
        ("系统位置", "第 1 节缺少「系统位置」小节"),
        ("规则", "第 1 节缺少规则与数值表"),
    ]:
        if key not in body:
            errors.append(msg)
    if "系统位置" in body and not ("<svg" in body.lower() or "```mermaid" in body or "图" in body):
        errors.append("第 1 节系统位置缺图：应有一张 SVG/关系图或至少明确的流程图")
    return errors


def check_figures(text):
    errors, warns = [], []
    imgs = IMG_RE.findall(text) + MD_IMG_RE.findall(text)
    if len(imgs) < 2:
        errors.append(f"图片仅 {len(imgs)} 张，实机截图至少 2 张")
    fig_blocks = FIG_RE.findall(text)
    for block in fig_blocks:
        if "figcaption" not in block.lower():
            src = (IMG_RE.search(block) or [None, "?"])[1] if IMG_RE.search(block) else "?"
            errors.append(f"<figure> 缺 <figcaption>：{src}")
        elif not (EVIDENCE_RE.search(block) or "数据来源" in block or "推导" in block):
            warns.append("有图注但未标证据编号或数据来源，建议在图注末尾加（Ex）")
    has_chart = any(
        re.search(r"chart|\.svg|\.png", p, re.I) for p in imgs
    )
    if not has_chart:
        warns.append("未发现图表类图片（文件名含 chart 或 .png/.svg），数据类内容建议图形化")
    return errors, warns


def check_evidence_table(lines):
    """第 6.1 证据表：每行来源列必须带链接。"""
    errors = []
    idx = next((i for i, l in enumerate(lines) if re.match(r"^###\s+6\.1", l)), None)
    if idx is None:
        return ["未找到 6.1 证据表"]
    end = next((i for i, l in enumerate(lines[idx + 1:], idx + 1) if re.match(r"^###?\s+", l)), len(lines))
    rows = [l for l in lines[idx:end] if l.strip().startswith("|")]
    if len(rows) < 3:
        return ["6.1 证据表为空或只有表头"]
    header = rows[0]
    try:
        src_col = [c.strip() for c in header.strip().strip("|").split("|")].index("来源（点击可查）")
    except ValueError:
        cols = [c.strip() for c in header.strip().strip("|").split("|")]
        src_col = next((i for i, c in enumerate(cols) if "来源" in c), None)
        if src_col is None:
            return ["6.1 证据表缺少「来源」列"]
    bad = 0
    for line in rows[2:]:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) <= src_col:
            bad += 1
            continue
        if not re.search(r"https?://", cells[src_col]):
            bad += 1
    if bad:
        errors.append(f"6.1 证据表有 {bad} 行来源列没有可点击链接（链接须可直接点开）")
    return errors


def check_competitor_table(lines):
    warns = []
    has_matrix = any(re.match(r"^###\s+4\.\d+", l) and "对照" in l for l in lines)
    if not has_matrix:
        warns.append("未发现本土化「取舍对照」表，多产品对比建议补矩阵")
    return warns


def check_placeholders(lines):
    hits = []
    in_fence = False
    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or INLINE_CHECKBOX.search(line):
            continue
        for m in PLACEHOLDER_RE.finditer(line):
            token = m.group(0)
            if re.fullmatch(r"\[E\d+\]", token):
                continue
            rest = line[m.end():m.end() + 1]
            if rest == "(":
                continue
            hits.append((i, token))
    return hits


def check_evidence_ids(lines):
    ids = []
    for line in lines:
        for m in EVIDENCE_RE.finditer(line):
            ids.append(int(m.group(1)))
    if not ids:
        return [], []
    uniq = sorted(set(ids))
    missing = [n for n in range(1, uniq[-1] + 1) if n not in uniq]
    crowded = [n for n in uniq if ids.count(n) > 12]
    return missing, crowded


def check_tables(lines):
    problems = []
    block = []

    def audit(rows):
        if len(rows) < 2:
            return
        counts = []
        for ln, text in rows:
            cells = text.strip().strip("|").split("|")
            is_sep = all(re.fullmatch(r":?-{2,}:?", c.strip()) or c.strip() == "" for c in cells)
            counts.append((ln, len(cells), is_sep))
        header_len = counts[0][1]
        for ln, n, is_sep in counts[1:]:
            if is_sep:
                continue
            if n != header_len:
                problems.append(f"第 {ln} 行表格列数 {n}，表头为 {header_len} 列（表头在第 {counts[0][0]} 行）")

    for i, line in enumerate(lines, 1):
        if line.strip().startswith("|"):
            block.append((i, line))
        else:
            if block:
                audit(block)
                block = []
    if block:
        audit(block)
    return problems


def check_doubt(lines):
    idx = next((i for i, l in enumerate(lines) if re.match(r"^##\s+6\.", l)), None)
    if idx is None:
        return ["未找到第 6 节，无法检查存疑清单"]
    if not any("存疑" in l for l in lines[idx:]):
        return ["第 6 节缺少「存疑点」小节"]
    items = [l for l in lines[idx:] if re.match(r"^\s*(?:\d+\.|[-*])\s+\S", l)]
    if len(items) < 2:
        return [f"存疑清单过短（仅 {len(items)} 条），至少列 2 条未验证问题"]
    return []


def warn_inference(lines):
    warns = []
    for i, line in enumerate(lines, 1):
        if INFER_RE.search(line) and not BASIS_RE.search(line) and "|" not in line:
            warns.append(f"第 {i} 行含〔推断〕但没写依据（{line.strip()[:40]}…）")
    return warns


def warn_numbers(lines):
    warns = []
    for i, line in enumerate(lines, 1):
        if "证据" in line or line.strip().startswith(("|", "<")):
            continue
        if NUM_RE.search(line) and not (EVIDENCE_RE.search(line) or "〔" in line):
            warns.append(f"第 {i} 行出现精确数值但无证据标注：{line.strip()[:50]}")
    return warns


def main():
    p = argparse.ArgumentParser(description="拆解报告交付前自检（六段式）")
    p.add_argument("report", help="报告 Markdown 路径")
    args = p.parse_args()

    text = read_lines(args.report)
    lines = text.splitlines()

    errors = []
    errors += check_sections(lines)
    errors += check_section1(lines)
    fig_err, fig_warn = check_figures(text)
    errors += fig_err
    errors += check_evidence_table(lines)
    errors += check_doubt(lines)
    for ln, tok in check_placeholders(lines):
        errors.append(f"第 {ln} 行残留模板占位符：{tok}")
    missing_e, crowded_e = check_evidence_ids(lines)
    if missing_e:
        errors.append("证据编号缺号：" + ", ".join("E%d" % n for n in missing_e))
    for prob in check_tables(lines):
        errors.append("表格列数不一致：" + prob)

    warns = warn_inference(lines) + warn_numbers(lines) + fig_warn + check_competitor_table(lines)

    ev_count = len(set(e for l in lines for e in EVIDENCE_RE.findall(l)))
    inf_count = sum(len(INFER_RE.findall(l)) for l in lines)
    todo = sum(len(re.findall(r"〔待验证〕", l)) for l in lines)
    imgs = len(IMG_RE.findall(text) + MD_IMG_RE.findall(text))

    print(f"文件：{args.report}")
    print(f"规模：{len(lines)} 行 | 证据 {ev_count} 条 | 图片 {imgs} 张 | 推断 {inf_count} 处 | 待验证 {todo} 处")
    if errors:
        print(f"\n错误 {len(errors)} 项：")
        for e in errors:
            print("  [ERROR] " + e)
    else:
        print("\n结构检查：通过")
    if warns:
        print(f"\n警告 {len(warns)} 项：")
        for w in warns[:10]:
            print("  [WARN] " + w)
    if crowded_e:
        print(f"\n提示：证据编号被引用超过 12 次，确认不是滥用：{crowded_e}")

    if errors:
        return 1
    print("\n结论：可交付（接下来跑 build_html.py 生成暗色 HTML）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
