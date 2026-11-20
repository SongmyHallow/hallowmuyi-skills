# 归档入库（飞书知识库目录 + 资料索引）

报告定稿后默认入库到用户的知识库，两件事一起做：**文档进产品目录**、**索引表加一行**。没有明确说“不入库”时按本流程执行。

## 默认落点

- 知识库根目录：`game-library`（Drive 文件夹，token `GjwufECr6liKovdREUScqoIR6xf`）
- 产品目录：`game-library/<【品类】产品名>/`，如 `【自走棋】王者万象棋`
- 子目录按资料性质分流：

| 资料性质 | 子目录 | 典型内容 |
|---|---|---|
| 版本公告、热修 | `01_版本更新` | 官方更新说明、活动公告 |
| 数据、榜单、流水 | `02_数据报告` | 官方数据页、第三方榜单 |
| 拆解报告、功能参考、调研 | `03_素材与参考` | 本技能产出的功能拆解报告 |
| 复盘、结论沉淀 | `04_分析沉淀` | 决策结论、方法论笔记 |

- 索引表：「游戏资料索引」`base_token=L2K8bXfAcaESMUsQFU3cCFuX6bh`，表 `资料索引` `table_id=tbl0W4XEZqTv4QEG`。token 变动时按标题 `drive +search --query "游戏资料索引"` 重新定位，不要猜。

## 入库步骤

1. **建文档**：按 `lark-doc` 的 `docs +create --parent-position my_library` 创建。注意：这样建出来的是**个人知识库的 wiki 节点**，不是 Drive 文件。
2. **解析 node_token**：`lark-cli wiki +node-get --node-token <docx_token> --as user`，取 `node_token`（≠ `obj_token`）。
3. **迁入目录**：

```bash
lark-cli wiki +move-to-drive --node-token <NODE_TOKEN> \
  --folder-token <产品子目录 token> --as user --format json
```

   迁出后按目录权限模型，原知识库继承权限不再保留。
   **不要用 `drive +move`**：目标若还是 wiki 节点会报 `params error 1061002`，且类型对不上。
4. **核对**：`lark-cli drive files list --folder-token <目录> --as user` 确认文档已在目录内。
5. **索引加行**：`base +record-batch-create --json '{"create_records":[{...}]}'`，字段按下表填。

| 字段 | 类型 | 取值规范 |
|---|---|---|
| 资料标题 | text（主字段） | `[产品]_资料类型_主题`；版本类追加 `_YYYYMMDD` |
| 版本号 | text | `vX.Y.Z`；落后于最新版时写 `vX（截至 YYYY-MM-DD 最新为 vY）` |
| 发布日期 | datetime | `YYYY-MM-DDT10:00:00.000+08:00`（无具体时间用 10:00） |
| 来源等级 | select | 官方公告/官方数据/社区整理/AI整理/个人整理，传数组 |
| 主题标签 | select（多选） | 地图与场景/英雄与平衡/战斗与系统/经济与商店/运营与活动/技术性能 |
| 时效状态 | select | 现行 / 历史 / 待验证 |
| 失效条件 | text | 被哪版取代；或“暂无（当前最新 vX）”；版本未核实时写清范围 |
| 资料类型 | select | 版本更新/功能参考/数据报告/素材/分析/公告 |
| 一句话结论 | text | 一句讲清机制 + 设计意图，不带铺垫 |
| 原链接 | text | `[URL](URL)` 包一层，保持可点 |
| 产品 | select | 产品名，须已在选项里；缺选项先 `+field-update` 加 |
| 录入人 | user | `[{"id":"ou_xxx"}]`，用当前用户 open_id |

6. **版本时效校验**：加行前先看同产品“版本更新”类最新记录。报告引用的版本落后时，索引里必须标注，时效状态按实情填（不能默认“现行”）。

## 常见坑

- select 字段传数组（`["功能参考"]`），传裸字符串会被拒。
- 日期只到天或格式不对会触发 `1254015`；必须带时区与毫秒。
- 产品 select 没有对应选项时，先加选项再写记录，别写近似值。
- 产品目录命名带品类前缀（`【自走棋】王者万象棋`），新建时沿用同一格式。
- 同一份报告重跑入库时，先查索引是否已有同标题行，有则更新而不是新增。
