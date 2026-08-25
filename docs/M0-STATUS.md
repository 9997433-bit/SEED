# M0 立项基线 — 验收状态

> **文档性质**：粉丝向非商业复刻项目的里程碑跟踪表（对照规划，不含官方资产）  
> **最后更新**：2026-08-25  
> **当前分支**：`cursor/m0-godot-schema-8ee2`

## 非官方声明

**机动战士启发：命运激斗**（Mobile Frame Inspired: Destiny Clash）与万代南梦宫娱乐、Sunrise、Bandai Namco Forge Digitals 及任何官方权利方 **无关联、未获授权、未获认可**。本文档仅用于内部工程验收，不构成任何官方产品承诺。

## 对照基准与已锁定决策

| 项 | 内容 |
|----|------|
| **对照产品** | Steam [MOBILE SUIT GUNDAM SEED BATTLE DESTINY REMASTERED](https://store.steampowered.com/app/1857740/)（**AppID 1857740**） |
| **验收口径** | 以 REMASTERED 在 Steam 上可观测的 **系统与体验** 为 Must 级对照；2012 PS Vita 原作仅作机制溯源 |
| **对照方法** | 公开资料 + 合法持有副本的实机/录像观测；**禁止**拆包 Steam depot 或逆向安装包提取资源/数值 |
| **已锁定决策** | 见 [`docs/adr/ADR-0001-locked-decisions.md`](./adr/ADR-0001-locked-decisions.md) |

### ADR-0001 摘要（已接受，2026-08-25）

| # | 议题 | 结论 |
|---|------|------|
| 1 | 对外身份 | 中性粉丝名「机动战士启发：命运激斗」+ 副标题 **SEED 启发**；显著非官方声明 |
| 2 | 引擎 | **Godot 4 + GDScript**（`game/project.godot`） |
| 3 | M2 垂直切片 | **大天使号 × C.E.71 × 18 机** |

规划全文见 [`docs/REMAKE-PLAN.md`](./REMAKE-PLAN.md)；M0 验收项摘自其 **第六节「里程碑 M0–M4」** 中 M0 行及同节上下文交付物。

---

## M0 验收表（对照 REMAKE-PLAN 第六节）

图例：**✅** 已完成 · **⛔** 明确不在 M0 范围 · **待办** 属 M0 但未完成

| # | 交付项（REMAKE-PLAN §六） | 状态 | 证据 / 说明 |
|---|---------------------------|------|-------------|
| M0-01 | **Godot 骨架** — 可导入工程、可运行占位场景 | ✅ | `game/project.godot`；主场景 `scenes/bridge/title_screen.tscn`；方块占位机体 `scenes/common/placeholder_mech.tscn` |
| M0-02 | **数据样板加载** — 外部 YAML → 构建产物 → 运行时只读载入 | ✅ | `make validate-data` → `game/data_build/units_index.json`；`game/scripts/data/unit_catalog.gd` 在标题画面展示 18 台底盘摘要 |
| M0-03 | **数据 Schema v1 + 校验 CLI** | ✅ | `data/schema/*.schema.json`；`tools/data_validator/validate.py`；`make validate-data` / `--strict` |
| M0-04 | **数据 CI 阻断** — 校验失败或构建产物过期则失败 | ✅ | `.github/workflows/validate-data.yml`（含 jsonschema 与内置子集双路径、`--check-index`） |
| M0-05 | **首发 18 台底盘数据条目** | ✅ | `data/units_manifest.yaml` `milestone: M0`；18 chassis / 29 forms / 27 weapons；`R-MILESTONE-011` 通过 |
| M0-06 | **机制代表数据覆盖**（换装 / 变形 / 装甲模式） | ✅ | 数据层已建模：强袭三装、圣盾/强夺/混沌变形链、自由 SEED 叠加层等；**运行时行为** ⛔ M1 起 |
| M0-07 | **版权流程初版** | ✅ | 根目录 `LICENSE`（MIT）；[`docs/legal/NOTICE.md`](./legal/NOTICE.md) 非官方声明 + 资产登记表；README 显著免责声明 |
| M0-08 | **Switch spike 文档** | ✅ | [`platform/switch/README.md`](../platform/switch/README.md) — 性能预算、输入、devkit 边界；不含 SDK/密钥 |
| M0-09 | **Steam 平台占位文档** | ✅ | [`platform/steam/README.md`](../platform/steam/README.md) — 对照 AppID 1857740、禁止拆包、M1 出包规划 |
| M0-10 | **PC CI 出包** — 自动化导出可玩 PC 构建 | 待办 | M0 仅数据 CI；`game/README.md` 注明 `export_presets.cfg` 与 Godot 导出 CI **M1 接入** |
| M0-11 | **战斗 / 任务 / 养成玩法** | ⛔ | 明确为 **M1–M2** 范围；标题画面「出击」仅为占位提示 |
| M0-12 | **Steamworks / 成就 / 云存档** | ⛔ | REMAKE-PLAN 全局优先级 **Later** |
| M0-13 | **100+ 机体全量** | ⛔ | M0 仅 18 机数据样板；全量 **Later** |

### M0 数据集快照（2026-08-25 校验通过）

| 计数 | 数量 |
|------|------|
| 底盘（chassis） | 18 |
| 形态（form） | 29 |
| 武装（weapon） | 27 |
| 技能（ability） | 16 |
| 装甲叠加层（overlay） | 6 |
| 驾驶员（pilot，原创占位） | 5 |
| 基准语言 | `zh_CN`（`data/locales/zh_cn.yaml`，`base: true`） |

全部条目 `asset_binding.placeholder = true`（M0 规则 `R-ASSET-010`）。数值为项目 **自建相对强度**，非官方数值转录。

---

## 相关文档与工具索引

| 文档 | 用途 |
|------|------|
| [`docs/data-schema.md`](./data-schema.md) | 数据作者 Schema 说明、ID 规范、新增机体流程、R-* 规则表 |
| [`docs/03-units-and-data.md`](./03-units-and-data.md) | 机体内容规划、首发 18 机名单、100+ 路线图 |
| [`tools/data_validator/README.md`](../tools/data_validator/README.md) | 校验 CLI 用法与规则详解 |
| [`game/README.md`](../game/README.md) | Godot 工程打开方式与数据管线 |

---

## 快速复验（维护者）

```bash
make setup              # 可选：安装 PyYAML / jsonschema
make validate-data      # 校验 + 刷新 game/data_build/units_index.json
make validate-data-strict
python3 tests/test_data_validator.py
# Godot 4.3+ → 导入 game/project.godot → F5
```

最近一次本地校验：`0 error, 0 warning`（`--strict`）。

---

## M0 仍未完成项（截至 2026-08-25）

| 项 | 计划里程碑 | 备注 |
|----|------------|------|
| PC CI 出包（Godot 导出 + artifact） | M1 | 需 `export_presets.cfg` 与 headless 导出脚本 |
| 战斗 / 锁敌 / 主副格闘等玩法 | M1 | 对照 REMASTERED 默认战斗循环 |
| 任务→出击→结算闭环 | M2 | ADR-0001：大天使号 × C.E.71 × 18 机 |
| `docs/images/m0-unit-catalog.png`（README 引用图） | 待办 | 可选宣传图；不影响数据/工程验收 |
| 蓝异端 / 暴风（Should 扩编至 20 机） | Should | 非 M0 硬性 18 机范围 |

---

## 下一里程碑预览（M1，非本表验收范围）

- 单机体单图：移动 / 锁敌 / 主副 / 格斗 / 受击 / 敌 AI  
- 战斗输入回放与性能基线  
- PC 可玩构建 CI  

详见 [`docs/REMAKE-PLAN.md`](./REMAKE-PLAN.md) 第六节 M1 行。

---

*本表随里程碑推进更新；对照母带与实测录像不入 Git。*
