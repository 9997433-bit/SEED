# M0 立项基线 — 验收状态

> **文档性质**：粉丝向非商业复刻项目的里程碑跟踪表（对照规划，不含官方资产）  
> **最后更新**：2026-08-25  
> **当前分支**：`cursor/m0-godot-schema-8ee2`

## 非官方声明

**机动战士启发：命运激斗**（Mobile Frame Inspired: Destiny Clash）与万代南梦宫娱乐、Sunrise、Bandai Namco Forge Digitals 及任何官方权利方 **无关联、未获授权、未获认可**。本文档仅用于内部工程验收，不构成任何官方产品承诺。

---

## 完成率摘要

| 口径 | 计数 | 完成率 |
|------|------|--------|
| **REMAKE-PLAN §六 M0 行**（5 项核心交付） | 5 / 5 ✅ | **100%** |
| **扩展验收表**（下表 M0-01～M0-10、M0-14、M0-15） | 12 / 12 ✅ | **100%** |
| **明确不在 M0**（M0-11～M0-13，标 ⛔） | 3 项 | 不计入未完成 |
| **顺延 M1**（M0-10b 及下文「M1 才启用」） | — | 非 M0 缺口 |

> §六原文「PC CI 出包」在本仓库拆分为：**M0** 完成 headless 导入 + 冒烟守门（[`build-pc.yml`](../.github/workflows/build-pc.yml)）；**M1** 接入 Godot 导出模板与 artifact。与根 [`README.md`](../README.md)、[`game/README.md`](../game/README.md) 表述一致。

图例：**✅** 已完成 · **⛔** 明确不在 M0 范围 · **M1** 顺延至下一里程碑

---

## 对照基准与已锁定决策

| 项 | 内容 |
|----|------|
| **对照产品** | Steam [MOBILE SUIT GUNDAM SEED BATTLE DESTINY REMASTERED](https://store.steampowered.com/app/1857740/)（**AppID 1857740**） |
| **验收口径** | 以 REMASTERED 在 Steam 上可观测的 **系统与体验** 为 Must 级对照；2012 PS Vita 原作仅作机制溯源 |
| **对照方法** | 公开资料 + 合法持有副本的实机/录像观测；**禁止**拆包 Steam depot 或逆向安装包提取资源/数值 |
| **版权红线** | [`docs/REMAKE-PLAN.md`](./REMAKE-PLAN.md) **§五**；流程落地见 [`docs/legal/asset-checklist.md`](./legal/asset-checklist.md)、[`docs/legal/NOTICE.md`](./legal/NOTICE.md)、[`.github/PULL_REQUEST_TEMPLATE.md`](../.github/PULL_REQUEST_TEMPLATE.md) |
| **已锁定决策** | [`docs/adr/ADR-0001-locked-decisions.md`](./adr/ADR-0001-locked-decisions.md) |

### ADR-0001 摘要（已接受，2026-08-25）

| # | 议题 | 结论 |
|---|------|------|
| 1 | 对外身份 | 中性粉丝名「机动战士启发：命运激斗」+ 副标题 **SEED 启发**；显著非官方声明 |
| 2 | 引擎 | **Godot 4 + GDScript**（[`game/project.godot`](../game/project.godot)） |
| 3 | M2 垂直切片 | **大天使号 × C.E.71 × 18 机** |

规划全文见 [`docs/REMAKE-PLAN.md`](./REMAKE-PLAN.md)；下文验收项摘自其 **第六节「里程碑 M0–M4」** M0 行及同节上下文交付物（**不重复**规划全文）。

---

## REMAKE-PLAN §六 M0 行对照（5 项核心）

| §六交付物 | 状态 | 证据 |
|-----------|------|------|
| Godot 骨架 | ✅ | [`game/project.godot`](../game/project.godot)；主场景 [`game/scenes/bridge/title_screen.tscn`](../game/scenes/bridge/title_screen.tscn)；占位机体 [`game/scenes/common/placeholder_mech.tscn`](../game/scenes/common/placeholder_mech.tscn) |
| PC CI 出包 | ✅（M0 冒烟）/ **M1**（导出 artifact） | M0：[`.github/workflows/build-pc.yml`](../.github/workflows/build-pc.yml) + [`tools/ci/godot_log_filter.py`](../tools/ci/godot_log_filter.py) + [`game/scripts/ci/headless_smoke.gd`](../game/scripts/ci/headless_smoke.gd）；M1：`export_presets.cfg` + 导出模板 |
| 数据样板加载 | ✅ | `make validate-data` → [`game/data_build/units_index.json`](../game/data_build/units_index.json)；[`game/scripts/data/unit_catalog.gd`](../game/scripts/data/unit_catalog.gd) |
| Switch spike 文档 | ✅ | [`docs/switch-feasibility-spike.md`](./switch-feasibility-spike.md)；[`platform/switch/README.md`](../platform/switch/README.md) |
| 版权流程初版 | ✅ | [`LICENSE`](../LICENSE)；[`docs/legal/NOTICE.md`](./legal/NOTICE.md)；[`docs/legal/asset-checklist.md`](./legal/asset-checklist.md)；PR 模板资产勾选项 |

---

## 扩展验收表（工程与规范）

| # | 交付项 | 状态 | 证据 / 说明 |
|---|--------|------|-------------|
| M0-01 | **Godot 骨架** — 可导入、可运行占位场景 | ✅ | 见 §六对照；[`game/README.md`](../game/README.md) |
| M0-02 | **数据样板加载** — YAML → 构建产物 → 运行时只读 | ✅ | [`data/README.md`](../data/README.md)；[`Makefile`](../Makefile) `validate-data` |
| M0-03 | **数据 Schema v1 + 校验 CLI** | ✅ | [`data/schema/*.schema.json`](../data/schema/)；[`tools/data_validator/validate.py`](../tools/data_validator/validate.py)；作者指南 [`docs/data-schema.md`](./data-schema.md) |
| M0-04 | **数据 CI 阻断** | ✅ | [`.github/workflows/validate-data.yml`](../.github/workflows/validate-data.yml)（`--strict`、`--check-index`） |
| M0-05 | **首发 18 台底盘数据条目** | ✅ | [`data/units_manifest.yaml`](../data/units_manifest.yaml) `milestone: M0`；`R-MILESTONE-011` 通过 |
| M0-06 | **机制代表数据覆盖**（换装 / 变形 / 装甲） | ✅ | 数据层：强袭三装、圣盾/强夺/混沌变形链、自由 SEED overlay 等；见 [`docs/03-units-and-data.md`](./03-units-and-data.md) |
| M0-07 | **版权流程初版** | ✅ | 见 §六对照；美术红线 [`docs/art-pipeline.md`](./art-pipeline.md) §0 |
| M0-08 | **Switch spike 文档** | ✅ | 公开事实基线、阻塞项 B-1～B-6、PC 侧约束模拟方案；**无 NDA / SDK / 密钥** |
| M0-09 | **Steam 平台占位文档** | ✅ | [`platform/steam/README.md`](../platform/steam/README.md)（AppID 1857740、禁止拆包、M1 出包规划） |
| M0-10 | **PC CI 冒烟** — 工程不腐化守门 | ✅ | [`build-pc.yml`](../.github/workflows/build-pc.yml)：`--import`、全量 `.gd` `--check-only`、主场景 5 秒、冒烟断言 |
| M0-14 | **美术资产管线规范** | ✅ | [`docs/art-pipeline.md`](./art-pipeline.md)；M0 无外部素材，[`game/assets/placeholder/`](../game/assets/placeholder/) 仅说明 |
| M0-15 | **Settings autoload**（音量 / 语言） | ✅ | [`game/scripts/autoload/settings.gd`](../game/scripts/autoload/settings.gd)；[`project.godot`](../game/project.godot) `[autoload]`；`user://settings.cfg` |
| M0-11 | **战斗 / 任务 / 养成玩法** | ⛔ | **M1–M2**；标题「出击」仅为占位 |
| M0-12 | **Steamworks / 成就 / 云存档** | ⛔ | REMAKE-PLAN 全局 **Later** |
| M0-13 | **100+ 机体全量** | ⛔ | M0 仅 18 机样板；全量 **Later** |

---

## M1 才启用（非 M0 验收缺口）

| 项 | 计划 | 证据 / 备注 |
|----|------|-------------|
| M0-10b **PC 出包 CI**（导出 + artifact） | M1 | 需 `export_presets.cfg` 与导出模板；见 [`game/README.md`](../game/README.md) 已知限制 |
| **设置界面 UI**（音量 / 语言） | M1 | `Settings` autoload 已有数据与持久化 |
| **Switch 约束模拟档**（30fps / 720p / 手柄唯一 / 同屏 ≤9） | M1 | [`switch-feasibility-spike.md`](./switch-feasibility-spike.md) §5 |
| **战斗 / 锁敌 / 主副格闘** | M1 | 对照 REMASTERED 默认战斗循环 |
| **机制运行时行为**（换装 / 变形 / 装甲） | M1 | M0-06 仅数据建模 |
| **任务→出击→结算闭环** | M2 | ADR-0001：大天使号 × C.E.71 × 18 机 |
| **资产 CI**（贴图 / 面数 / 命名） | M3 | [`art-pipeline.md`](./art-pipeline.md) §9 |

### 可选 / Should（不影响 M0 完成率）

| 项 | 状态 | 备注 |
|----|------|------|
| [`docs/images/m0-unit-catalog.png`](./images/m0-unit-catalog.png) | 待办 | 根 [`README.md`](../README.md) 引用图；可选宣传图 |
| 蓝异端 / 暴风扩编至 20 机 | Should | 非 M0 硬性 18 机范围 |

---

## M0 数据集快照（2026-08-25 `--strict` 通过）

| 计数 | 数量 |
|------|------|
| 底盘（chassis） | 18 |
| 形态（form） | 29 |
| 武装（weapon） | 27 |
| 技能（ability） | 16 |
| 装甲叠加层（overlay） | 6 |
| 驾驶员（pilot，原创占位） | 5 |
| 基准语言 | `zh_CN`（[`data/locales/zh_cn.yaml`](../data/locales/zh_cn.yaml)，`base: true`） |

全部条目 `asset_binding.placeholder = true`（`R-ASSET-010`）。数值为 **自建相对强度**，非官方数值转录。

---

## 仓库交叉引用索引

| 文档 | 与 M0-STATUS 对齐点 |
|------|---------------------|
| [`README.md`](../README.md) | 当前状态表、快速开始、`make validate-data`、文档索引 |
| [`data/README.md`](../data/README.md) | 数据入口、作者须读 [`data-schema.md`](./data-schema.md)、链回本表 |
| [`game/README.md`](../game/README.md) | 打开方式、数据管线、`Settings` autoload、headless 冒烟、M0 已知限制 |
| [`docs/data-schema.md`](./data-schema.md) | Schema 字段、R-* 规则、新增机体流程 |
| [`tools/data_validator/README.md`](../tools/data_validator/README.md) | CLI 用法与规则详解 |

---

## 相关文档与工具

| 文档 | 用途 |
|------|------|
| [`docs/data-schema.md`](./data-schema.md) | 数据作者 Schema、ID 规范、R-* 规则表 |
| [`docs/art-pipeline.md`](./art-pipeline.md) | 原创资产规范与入库流程 |
| [`docs/switch-feasibility-spike.md`](./switch-feasibility-spike.md) | Switch 可行性、阻塞项与替代验证 |
| [`docs/legal/asset-checklist.md`](./legal/asset-checklist.md) | PR 资产入场逐条检查单 |
| [`docs/03-units-and-data.md`](./03-units-and-data.md) | 机体规划、首发 18 机、100+ 路线图 |
| [`docs/REMAKE-PLAN.md`](./REMAKE-PLAN.md) §五 | 版权红线全文 |

---

## 快速复验（维护者）

```bash
make setup              # 可选：安装 PyYAML / jsonschema
make validate-data      # 校验 + 刷新 game/data_build/units_index.json
make validate-data-strict
python3 tests/test_data_validator.py
# Godot 4.3+ → 导入 game/project.godot → F5
# 无 GUI 时复现 CI：
godot --headless --path game --import
godot --headless --path game --max-fps 60 --quit-after 300
godot --headless --path game --script res://scripts/ci/headless_smoke.gd
```

最近一次本地校验：`0 error, 0 warning`（`--strict`，2026-08-25）。

---

## 下一里程碑预览（M1）

- 单机体单图：移动 / 锁敌 / 主副 / 格斗 / 受击 / 敌 AI  
- 战斗输入回放与性能基线  
- PC 可玩构建 CI（导出 artifact）  

详见 [`docs/REMAKE-PLAN.md`](./REMAKE-PLAN.md) 第六节 M1 行。

---

*本表随里程碑推进更新；对照母带与实测录像不入 Git。*
