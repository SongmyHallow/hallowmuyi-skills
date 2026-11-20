# 飞书入库：`04_分析` + 资料索引

定稿后默认入库，两件事一起做：**文档进产品目录**、**索引表加一行**。用户说“不入库”时跳过。

## 落点

- 知识库根：`game-library`（Drive 文件夹，token `GjwufECr6liKovdREUScqoIR6xf`）
- 产品目录：`game-library/<【品类】产品名>/`，如 `【动作竞技】永劫无间`
- **生平/复盘类文档落 `04_分析`**（若该产品目录下叫 `04_分析沉淀`，用实际存在的那个，不新建近义目录）
- 索引表：「游戏资料索引」`base_token=L2K8bXfAcaESMUsQFU3cCFuX6bh`，表 `资料索引` `table_id=tbl0W4XEZqTv4QEG`

先核对目录，不要凭记忆拼路径：

```bash
lark-cli drive files list --folder-token GjwufECr6liKovdREUScqoIR6xf --as user --format json
lark-cli drive files list --folder-token <产品目录 token> --as user --format json
```

产品目录不存在时，按 `【主类型】产品名` 新建，并建齐该产品现有目录结构（长线运营型：`01_版本更新`、`02_数据报告`、`03_素材与参考`、`04_分析`）。

## 入库步骤

1. **转格式**：`python3 scripts/to_lark_doc.py bio.md --assets ./assets --out _feishu.md`。图表自动换 `*_light.png`，节点与年表转原生段落/表格，图片走 `@./assets/...`。
2. **直接建到目录**：

```bash
lark-cli docs +create --doc-format markdown --content "@./_feishu.md" \
  --title "[产品]_分析_产品生平（YYYY.MM）" --parent-token <04 目录 token> --as user --format json
```

   `--parent-token` 可直接传 Drive 文件夹 token，一步落位，不必走 wiki 迁转。
3. **核对**：`lark-cli drive files list --folder-token <04 目录>` 确认文档在列。

   若环境不支持 `--parent-token`，退回旧链路：`--parent-position my_library` 建文档 → `wiki +node-get` 取 node_token → `wiki +move-to-drive`。**不要用 `drive +move`**（wiki 节点会报 1061002）。

4. **索引加行**：

```bash
lark-cli base +record-batch-create --app-token L2K8bXfAcaESMUsQFU3cCFuX6bh \
  --table-id tbl0W4XEZqTv4QEG --as user --format json \
  --json '{"create_records":[{...}]}'
```

| 字段 | 取值 |
|---|---|
| 资料标题 | `[产品]_分析_产品生平（YYYY.MM）`，如 `[永劫无间]_分析_产品生平（2021.08–2026.11）` |
| 版本号 | 写当前版本/赛季 + 截止日：`2026 千机赛季（截至 2026-11-20）` |
| 发布日期 | `YYYY-MM-DDT10:00:00.000+08:00` |
| 来源等级 | `["AI整理"]`（可加 `"官方数据"`，因为正文引了财报/公告） |
| 主题标签 | 按内容选 1–3 个：`运营与活动`/`战斗与系统`/`经济与商店`/`技术性能` |
| 时效状态 | `现行`（传记是活文档）；数据明显滞后写 `待验证` |
| 失效条件 | `随版本与运营变化；建议每季度复核（当前截至 YYYY-MM）` |
| 资料类型 | `分析` |
| 一句话结论 | 导语判词，一句，≤60 字 |
| 原链接 | `[URL](URL)`，保持可点 |
| 产品 | select，选项须已存在；缺选项先 `+field-update` 加 |
| 录入人 | `[{"id":"ou_xxx"}]`，用当前用户 open_id |

5. **重跑同标题**：先查索引是否已有同标题行，有则更新，不重复新增。

## 常见坑

- select 字段传数组（`["分析"]`），裸字符串会被拒。
- 日期必须带时区与毫秒，否则 `1254015`。
- 产品 select 没选项时先加选项，别写近似值。
- 产品目录名带品类前缀；新建沿用同一格式。
- 传记正文引用的数据有截止日，索引「失效条件」必须写清复核时间。
- 图片要先进文档（`<img path="@./assets/x.png"/>` 或先上传拿 token），不要留本地路径。
