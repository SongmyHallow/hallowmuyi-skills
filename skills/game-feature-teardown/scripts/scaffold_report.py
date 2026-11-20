#!/usr/bin/env python3
"""生成游戏功能拆解报告的 Markdown 骨架。

用法：
  python3 scaffold_report.py --game "原神" --feature "限定祈愿" --platform 手游 \
      --category 开放世界RPG --version 6.0 --dimensions core,numbers,commerce \
      --competitors "鸣潮,崩坏：星穹铁道" --out ./原神_祈愿拆解.md

只生成骨架与提示，结论、证据、数值仍需按 references/ 的规范人工/Agent 填写。
"""

import argparse
import datetime
import os
import sys

DIMENSIONS = {
    "core": ("玩法机制与核心循环", [
        "核心循环：动作 → 系统反馈 → 奖励 → 再投入，一句话写清",
        "决策点：一局内几个关键选择，每个选择的真实代价是什么",
        "失败条件、失败代价、重试成本",
        "节奏：单局/单次时长，难度或频率跃迁点",
    ]),
    "numbers": ("数值与经济", [
        "属性与可反推公式（写明反推过程）",
        "成长曲线：投入-产出比、拐点、边际递减",
        "资源产出源与消耗池，每日上限",
        "概率与保底设计",
    ]),
    "ui": ("UI/交互与体验路径", [
        "入口层级与点击次数",
        "信息架构：主次信息、默认焦点",
        "完成一次核心行为的操作步数",
        "空态/加载/失败/上限等边界态处理",
    ]),
    "commerce": ("商业化与付费设计", [
        "付费点清单：位置、触发时机、价格锚点",
        "免费与付费的体验差",
        "商品结构：首充/月卡/通行证/礼包性价比阶梯",
        "付费墙首次出现的位置",
    ]),
    "retention": ("新手引导与留存节奏", [
        "新手流程时长与前 10 分钟解锁清单",
        "首日目标与“明天再来”钩子",
        "日常/周常结构与单日时间成本",
        "活动节奏、回流设计、社交绑定",
    ]),
    "match": ("匹配、段位与身份机制", [
        "触发条件与能否关闭（段位/身份/开关）",
        "分流结构：混排/隔离/可选，各自代价",
        "决策窗口与选项数量，信息是否现场可见",
        "风险收益矩阵：赢/输/不操作各得到什么",
        "身份外显方式与曝光对象",
        "反滥用闸：亲密度、分数上限、次数限制",
        "进度重置与继承规则，长线标的台阶",
    ]),
}


def build(args):
    dims = [d.strip() for d in args.dimensions.split(",") if d.strip()]
    unknown = [d for d in dims if d not in DIMENSIONS]
    if unknown:
        raise SystemExit(f"未知维度: {', '.join(unknown)}；可选: {', '.join(DIMENSIONS)}")

    lines = []
    add = lines.append
    add(f"# 《{args.game}》「{args.feature}」功能拆解")
    add("")
    add(f"[3 行以内导语：一句话定义 + 本报告主线 + 证据规模。品类 {args.category or '[待填]'}／平台 {args.platform or '[待填]'}／版本 {args.version or '[待填]'}／拆解日期 {args.date}]")
    add("")

    # 1 功能本体
    add("## 1. 功能本体")
    add("")
    add("### 1.1 一句话定义与口径")
    add("[玩家视角一句话 + 设计视角一句话；点名排除的同名口径（如不含赛事模式层）]")
    add("")
    add("### 1.2 系统位置")
    add("[挂在哪个大系统下、上游是谁、下游产出、旁挂系统]")
    add("")
    add("**图 1｜功能在系统中的位置**")
    add("[必须有一张系统位置图：SVG/HTML 关系图，节点 ≤10，标出本功能所在环节]（证据 Ex）")
    add("")
    add("### 1.3 入口与解锁")
    add("- 入口路径：主界面 → … → 功能页，共几步")
    add("- 解锁条件：")
    add("- 准入限制：")
    add("")
    add("### 1.4 界面清单")
    add("- [界面 1]：[这一屏在做什么]")
    add("- [界面 2]：")
    add("")
    add("**图 2｜[界面名]**")
    add("<figure><img src=\"assets/[shot1].jpg\" alt=\"[界面名]\"><figcaption>[这一屏说明什么]（Ex）</figcaption></figure>")
    add("")
    add("### 1.5 主流程")
    for i, item in enumerate([
        "在第 1 步玩家做什么／系统反馈什么",
        "第 2 步",
        "第 3 步",
    ], start=1):
        add(f"{i}. {item}")
    add("")
    add("### 1.6 规则与数值")
    add("")
    add("| 规则/参数 | 具体表现 | 证据 | 类型 |")
    add("|---|---|---|---|")
    add("| [例：单次消耗] | [例：体力 6 点] | [E1] | 事实 / 〔推断〕 |")
    add("")
    add("- 核心换算关系：[能反推才写，附推导过程]")
    add("- 边界与限制：[冷却、上限、失败处理]")
    add("- 未公开数值：[官方未公布的，明确写出，不猜]")
    add("")
    add("### 1.7 版本变更")
    add("[版本号 + 日期 + 改了什么 + 官方说明；无改动写“未发现”]")
    add("")

    # 2 产品分布
    add("## 2. 产品分布")
    add("")
    add("### 2.1 同源机制检索")
    add("[把功能拆成 3–5 个可判定特征，逐产品核对“是否等同本功能”，核过的产品都列出来]")
    add("")
    comps = [c.strip() for c in (args.competitors or "").split(",") if c.strip()]
    products = [args.game] + comps
    add("| 产品 | 同位置之后的安排 | 是否等同本功能 | 证据 |")
    add("|---|---|---|---|")
    for p in products:
        add(f"| {p} | | | |")
    add("")
    add("[只有一款就写“严格意义上仅此一款”；形似但特征对不上的标“否 + 差在哪”]")
    add("")
    add("### 2.2 同设计目的的其他解法")
    add("[先写清本功能的设计目的，再写哪个产品用哪种解法回答了同一问题]")
    add("")
    add("| 机制 | 归属产品 | 与本功能的关系 | 核心做法 | 证据 |")
    add("|---|---|---|---|---|")
    add("| | | 同源 / 同目的 | | |")
    add("")
    add("**不纳入对比的机制**：[形似但问题不同的机制 + 一句原因]")
    add("")
    add("### 2.3 为什么是它先做（可选）")
    add("[只写有证据的原因；无证据删掉本节]")
    add("")

    # 3 设计目的
    add("## 3. 设计目的")
    add("")
    add("### 3.1 供给端：[谁的需求没被满足]")
    add("")
    add("### 3.2 需求端：[官方怎么说的]")
    add("[贴官方公告/FAQ 原话 + （Ex），再解释；没有官方原话就明说没有]")
    add("")
    add("### 3.3 生态与商业化约束")
    add("[付费模型决定能给什么奖励，写清推导]")
    add("")
    add("### 3.4 为什么是这个形态")
    add("")
    add("| 设计选择 | 想解决的问题 | 代价 / 副作用 | 置信度 |")
    add("|---|---|---|---|")
    add("| | | | 高/中/低 |")
    add("")

    # 4 本土化魔改
    add("## 4. 本土化魔改")
    add("")
    for i, p in enumerate(products, start=1):
        add(f"### 4.{i} {p}：改了什么、为什么改")
        add("[改动 + 动机 + 代价，落到受众结构/付费模型/代练生态]")
        add("")
    add(f"### 4.{len(products) + 1} 取舍对照")
    add("")
    header = "| 维度 | " + " | ".join(products) + " |"
    add(header)
    add("|---" * (len(products) + 1) + "|")
    for row in ["要解决的问题", "手段", "对高手的处理", "对弱者的保护", "副作用", "适配的受众"]:
        add("| " + row + " |" + " |" * len(products))
    add("")

    # 5 方法论
    add("## 5. 方法论")
    add("")
    add("### 5.1 适用产品类型")
    add("[满足哪几条才适合引入，逐条带证据；反过来说哪些不该做]")
    add("")
    add("### 5.2 可调参数模板")
    add("")
    add("| 参数 | 取值范围 | 调大/调小的后果 |")
    add("|---|---|---|")
    for p in ["重置粒度", "称号台阶", "决策窗口", "兜底默认", "反滥用闸"]:
        add(f"| {p} | | |")
    add("")
    add("### 5.3 方案选择")
    add("")
    add("| 方案 | 适合什么产品 | 代价 | 已知案例 |")
    add("|---|---|---|---|")
    add("")
    add("### 5.4 优化空间")
    add("[每条写成 现状 + 问题 + 改法 + 预期收益]")
    add("")
    add("### 5.5 验证方式")
    add("[埋什么点、看什么指标、什么算成功]")
    add("")

    # 6 证据
    add("## 6. 证据与存疑")
    add("")
    add("### 6.1 证据表")
    add("")
    add("| ID | 内容 | 来源（点击可查） | 时间 | 等级 |")
    add("|---|---|---|---|---|")
    add("| E1 | | [短标签](URL) | YYYY.MM.DD | A/B/C |")
    add("")
    add("### 6.2 口径冲突")
    add("[冲突在哪、采信哪条、为什么；低等级那条是错误信息而非另一种说法]")
    add("")
    add("### 6.3 存疑点")
    add("1. [未验证问题 + 验证方式]")
    add("2. ")
    add("")

    # 可选：交付检查
    add("---")
    add("")
    add("## 交付检查（写完删除本节）")
    add("- [ ] 六段顺序未动；截图 ≥2 张且带图注与证据编号")
    add("- [ ] 数据已图形化（1–3 张图），每图有结论式标题与口径")
    add("- [ ] 对比表每行至少一条 A/B 级证据，否则整表标“定性对比”")
    add("- [ ] 跑 `check_report.py` 通过，再 `build_html.py` 出暗色 HTML")
    add("- [ ] 需要进知识库时按 lark-doc 规范同步，截图/图表用 img 插入")

    if dims:
        add("")
        add("---")
        add("")
        add("## 附：本次拆解的维度检查清单")
        for key in dims:
            title, items = DIMENSIONS[key]
            add("")
            add(f"### {title}")
            for item in items:
                add(f"- [ ] {item}")
        add("")

    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="生成游戏功能拆解报告骨架")
    p.add_argument("--game", required=True, help="游戏名")
    p.add_argument("--feature", required=True, help="功能/系统名")
    p.add_argument("--platform", default="", help="平台，如 手游/PC/主机")
    p.add_argument("--category", default="", help="品类，如 卡牌/MMO/SLG")
    p.add_argument("--version", default="", help="拆解版本")
    p.add_argument("--date", default=datetime.date.today().isoformat(), help="拆解日期，默认今天")
    p.add_argument("--dimensions", default="core,numbers,ui,commerce,retention,match",
                   help="逗号分隔：core,numbers,ui,commerce,retention,match")
    p.add_argument("--competitors", default="", help="逗号分隔的竞品名")
    p.add_argument("--out", default="", help="输出路径；默认 ./<游戏>_<功能>_拆解.md")
    args = p.parse_args()

    args.game = args.game.strip()
    args.feature = args.feature.strip()
    if not args.game or not args.feature:
        raise SystemExit("--game 与 --feature 不能为空")

    content = build(args)
    out = args.out or f"./{args.game}_{args.feature}_拆解.md"
    out_dir = os.path.dirname(os.path.abspath(out))
    os.makedirs(out_dir, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"已生成：{out}（{len(content)} 字符）")


if __name__ == "__main__":
    sys.exit(main())
