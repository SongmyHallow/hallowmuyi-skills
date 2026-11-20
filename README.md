# hallowmuyi-skills

个人开发的 AI Agent Skills 仓库。每个技能一个目录，`SKILL.md` 为入口，其余资源按需加载。

## 技能列表

| 技能 | 说明 | 状态 |
|---|---|---|
| [`game-feature-teardown`](skills/game-feature-teardown/SKILL.md) | 游戏功能拆解：把单个功能拆成「本体 → 产品分布 → 设计目的 → 本土化魔改 → 方法论 → 证据」六段式暗色 HTML 报告，可同步飞书云文档 | 可用 |
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

## 维护

- 新增技能：新建 `skills/<name>/SKILL.md`，frontmatter 写 `name` 与 `description`。
- 改动一律走分支 + PR，不要直接改 `main`。
