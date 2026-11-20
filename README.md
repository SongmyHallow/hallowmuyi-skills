# hallowmuyi-skills

个人开发的 AI Agent Skills 仓库。每个技能一个目录，`SKILL.md` 为入口，其余资源按需加载。

## 技能列表

| 技能 | 说明 | 状态 |
|---|---|---|
| [`game-feature-teardown`](skills/game-feature-teardown/SKILL.md) | 游戏功能拆解：把单个功能拆成「本体 → 产品分布 → 设计目的 → 本土化魔改 → 方法论 → 证据」六段式暗色 HTML 报告，可同步飞书云文档 | 可用 |
| [`game-product-biography`](skills/game-product-biography/SKILL.md) | 游戏产品生平：七段式发展史（现状侧写 → 年表 → 关键节点 → 起伏曲线 → 兴衰解剖 → 可迁移教训 → 证据存疑），暗色 HTML + 飞书入库 | 可用 |
| `game-knowledge-base` | 游戏产品知识库搭建与维护 | 规划中 |

## 目录约定

```
skills/<skill-name>/
├── SKILL.md          # 入口：触发条件、流程、自检
├── references/       # 按阶段读取的细则文档
└── scripts/          # 可执行脚本（Python）
```

## game-feature-teardown 使用

```bash
# 1. 生成六段式骨架
python3 skills/game-feature-teardown/scripts/scaffold_report.py \
  --game "王者万象棋" --feature "王中王" --competitors "王者荣耀" --out report.md

# 2. 填完正文后自检
python3 skills/game-feature-teardown/scripts/check_report.py report.md

# 3. 构建暗色 HTML（含侧边栏目录与暗/浅切换）
python3 skills/game-feature-teardown/scripts/build_html.py report.md \
  --title "《王者万象棋》「王中王」功能拆解" \
  --subtitle "一句话主线" --meta "自走棋;v1.7.1;2026-11-20;13 条证据" \
  --out report.html
```

## game-product-biography 使用

```bash
# 1. 自检七段结构、节点字段与证据链接
python3 skills/game-product-biography/scripts/check_biography.py bio.md

# 2. 构建暗色 HTML（侧栏锚定目录、图表、节点卡、暗/浅切换）
python3 skills/game-product-biography/scripts/build_biography.py bio.md \
  --title "《永劫无间》产品生平" --subtitle "2019—2026：三次台阶，两次退潮" \
  --meta "PC/Steam;2021.08—2026.11;31 条证据" --out bio.html

# 3. 转飞书可读版（图表换浅色图，节点/年表转原生块）
python3 skills/game-product-biography/scripts/to_lark_doc.py bio.md \
  --assets ./assets --out _feishu.md
```

## 维护

- 新增技能：新建 `skills/<name>/SKILL.md`，frontmatter 写 `name` 与 `description`。
- 改动一律走分支 + PR，不要直接改 `main`。
