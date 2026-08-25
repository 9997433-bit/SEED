# 数据 Schema 说明（面向数据作者）

> **读者**：编写或审核 `data/` 下 YAML 的策划、贡献者  
> **非官方声明**：本仓库为粉丝向非商业项目；`data/` 内数值均为 **自建相对强度设计**，不得从 Steam AppID **1857740** 或任何官方产品抄录数值表。机制标签可参考公开作品设定与攻略社区的 **机制描述**，不复制官方文本。  
> **Schema 版本**：`1.0.0` · **平衡戳记**：`2026.08.0` · **当前里程碑**：`M0`

## 1. 管线总览

```text
data/units_manifest.yaml          ← 入口：阵营、库文件、底盘索引
        │
        ├── libraries/            ← 武装、技能、叠加层、驾驶员、语言
        └── chassis_index/        ← 各底盘 YAML
                │
                ├── units/chassis/<slug>.yaml
                └── units/forms/<slug>.yaml   （由 chassis.forms_ref 指向）

        ↓  python3 tools/data_validator/validate.py
        ↓  （Schema + R-* 引用规则）

game/data_build/units_index.json  ← 构建产物（勿手工编辑）
        ↓
Godot 运行时只读载入（game/scripts/data/unit_catalog.gd）
```

**原则**

- 改内容只改 YAML；**不要**改 `units_index.json`。  
- 合并前在仓库根目录执行 `make validate-data`（或 `make validate-data-strict`）。  
- M0 阶段所有条目的 `asset_binding.placeholder` **必须为 `true`**（规则 `R-ASSET-010`）。  
- 显示名一律通过 `loc.*` 键引用，写在 `data/locales/zh_cn.yaml`（基准语言）。

更完整的概念模型见 [`docs/03-units-and-data.md`](./03-units-and-data.md)。

---

## 2. 目录结构

```text
data/
├── units_manifest.yaml       # 顶层清单（必读入口）
├── schema/                   # JSON Schema（机器校验用）
├── units/
│   ├── chassis/              # 一台底盘一个文件（18 个）
│   │   ├── gat-x105.yaml
│   │   ├── zgmf-x10a.yaml
│   │   └── …
│   └── forms/                # 与底盘 1:1 的形态集文件
│       ├── gat-x105.yaml
│       └── …
├── weapons/                  # 武装库（按类别分文件）
├── abilities/                # 技能库
├── overlays/                 # 装甲/模式叠加层
├── pilots/                   # 驾驶员与特质（M0：仅原创占位）
├── locales/                  # 本地化条目
└── missions/                 # 任务数据（M2+，当前仅占位 README）
```

### 2.1 文件命名约定

| 类型 | 路径模式 | 示例 |
|------|----------|------|
| 底盘 | `units/chassis/<model-slug>.yaml` | `gat-x105.yaml` ← 型号 `GAT-X105` 小写化 |
| 形态集 | `units/forms/<model-slug>.yaml` | 与底盘 slug 相同，由 `forms_ref` 链接 |
| 武装库 | `weapons/<category>.yaml` | `beam.yaml`、`ballistic.yaml` |
| 清单引用 | `units_manifest.yaml` 内 `ref` | 相对 `data/` 的 POSIX 路径 |

**slug 规则**：型号字母数字段用 **小写 + 连字符**，与 `model_number` 对应（如 `ZGMF-X56S` → `zgmf-x56s`）。

---

## 3. 全局 ID 规范

所有可引用实体使用 **全局唯一、带点分前缀** 的字符串 ID。合并后不可改名（仅可 `deprecated` 迁移，见 03 文档 3.7）。

| 前缀 | 实体 | 模式 | 示例 |
|------|------|------|------|
| `chassis.` | 底盘 | `chassis.<slug>` | `chassis.gat_x105` |
| `form.` | 形态 | `form.<chassis_slug>.<variant>` | `form.gat_x105.aile` |
| `weapon.` | 武装 | `weapon.<name>` | `weapon.beam_rifle_standard` |
| `ability.` | 技能 | `ability.(sp\|passive\|additional).<name>` | `ability.sp.assault_dash` |
| `overlay.` | 叠加层 | `overlay.<name>` | `overlay.seed_mode` |
| `pilot.` | 驾驶员 | `pilot.<name>` | `pilot.avatar_lead` |
| `trait.` | 特质 | `trait.<name>` | `trait.seed_awakening` |
| `faction.` | 阵营 | `faction.<name>` | `faction.three_ships` |
| `loc.` | 本地化键 | `loc.<domain>.<slug>` | `loc.unit.strike` |

**命名建议**

- 底盘 slug 与文件名一致，下划线连接：`gat_x105`。  
- 形态第二段表示变体：`aile`、`sword`、`ma`、`meteor` 等。  
- 新建 ID 前在仓库内 `rg '^id: '` 或运行校验器，避免 `R-ID-001` 重复。

---

## 4. 顶层清单 `units_manifest.yaml`

**职责**：声明 Schema 版本、平衡戳记、里程碑、阵营表、共享库路径、底盘索引。校验器 **只加载此处引用的文件**；未引用的 YAML 视为孤儿（`R-MANIFEST-002`）。

| 字段 | 必填 | 语义 |
|------|------|------|
| `schema_version` | 是 | 数据格式主版本，当前 `"1.0.0"` |
| `balance_patch` | 是 | 平衡迭代戳记，格式 `YYYY.MM.N` |
| `milestone` | 否 | 里程碑标签，如 `M0`；触发 `R-MILESTONE-011` |
| `notes` | 否 | 人类可读说明 |
| `factions[]` | 是 | 阵营列表：`id` + `name_key`（`loc.*`） |
| `libraries` | 是 | `weapons` / `abilities` / `overlays` / `pilots` / `locales` 各为 ref 数组 |
| `chassis_index[]` | 是 | `{ ref, note? }` 指向底盘 YAML |

**阵营 ID**（M0 已定义）：`faction.omni`、`faction.zaft`、`faction.orb`、`faction.three_ships`、`faction.mercenary`。

---

## 5. 底盘 `chassis`（`units/chassis/*.yaml`）

**语义**：不可拆分的素体身份——基础机动、体型、阵营归属、可接入的形态族、战内换装/变形策略。

| 字段 | 必填 | 语义 |
|------|------|------|
| `id` | 是 | `chassis.*` 全局 ID |
| `model_number` | 是 | 设定型号，大写（如 `GAT-X105`），用于 UI 与图鉴 |
| `display_name_key` / `description_key` | 是 | 图鉴名称与正文，`loc.*` |
| `series` | 是 | `seed` \| `seed_destiny` \| `astray` |
| `era` | 是 | `ce71` \| `ce73` |
| `faction_production` | 是 | 生产/所属势力（图鉴生产线） |
| `faction_playable` | 是 | 玩家选用默认归类（可与剧情阵营不同） |
| `tags` | 否 | 机制检索：`swap_pack`、`transform`、`phase_shift`、`seed_mode` 等 |
| `power_budget` | 是 | 相对强度总分；标准机动 MS 基准 **1000**（盖茨） |
| `base_stats` | 是 | `hp` / `en` / `mobility` / `defense` / `size_class` |
| `forms` | 是 | 本底盘拥有的 `form.*` ID 列表（与形态文件双向一致） |
| `forms_ref` | 是 | 形态集 YAML 路径（**每台底盘独占一个形态文件**） |
| `default_form` | 是 | 出击默认形态，必须在 `forms` 中 |
| `form_switch_policy` | 条件 | 多形态时 **必填**；单形态应为 `type: none` |
| `compatible_pilots` | 否 | 可驾驶驾驶员 ID；空 → 剧情专用（`R-PILOT-004` Warning） |
| `sources` | 否 | 考据出处（文档章节、公开设定引用），非官方数值 |
| `asset_binding` | 是 | 模型/骨骼/图标键；M0 必须 `placeholder: true` |

### 5.1 `form_switch_policy`

| `type` | 含义 | 典型机体 |
|--------|------|----------|
| `none` | 无战内切换 | 单形态机（自由、盖茨） |
| `mid_battle_swap` | 战内换装（无限次，可配冷却/继承） | 强袭、扎古勇士、脉冲 |
| `pre_sortie_only` | 仅出击前选择 | 部分量产配置 |
| `transform_only` | 仅通过变形图切换 | 纯变形机 |
| `purge_one_way` | 单程パージ，不可恢复 | 决斗シュラウド（后续批次） |

可选子字段：`cooldown_sec`、`inherit_hp_ratio`、`inherit_en_ratio`、`allowed_states`（`ground` / `air` / `space`）。

### 5.2 `base_stats` 与 `power_budget`

- `base_stats` 为底盘级 **相对标量**，不是官方绝对数值。  
- `power_budget` 用于平衡巡检（`R-BALANCE-006`：偏离 1000 超过 ±20% 报 Warning）。  
- 特殊机制在规划文档中建议额外消耗预算（换装 +50、变形 +80 等），由作者自行分配至 `base_stats` 与形态修正。

---

## 6. 形态集 `form`（`units/forms/*.yaml`）

**语义**：一台底盘下的完整外观/性能包集合；每个形态携带武装装配、技能、变形边、模式叠加。

文件级字段：

| 字段 | 必填 | 语义 |
|------|------|------|
| `parent_chassis` | 是 | 所属 `chassis.*`，须与底盘 `forms_ref` 互指 |
| `forms[]` | 是 | 形态对象数组 |

每个形态对象：

| 字段 | 必填 | 语义 |
|------|------|------|
| `id` | 是 | `form.<chassis>.<variant>` |
| `display_name_key` | 是 | 形态显示名 |
| `type` | 是 | `equipment_form`（换装）\| `transform_form`（变形）\| `base_form`（素体） |
| `stat_modifiers` | 否 | 相对底盘的增减：`mobility`、`defense`、`firepower` 等 |
| `size_class_override` | 否 | 覆盖底盘体型（MA 等） |
| `weapons[]` | 是 | `{ slot, weapon_id }` 列表；至少一件 `main` 或 `melee` |
| `abilities[]` | 否 | `ability.*` ID 列表 |
| `transform_graph[]` | 否 | 变形有向边（见下） |
| `mode_overlays[]` | 否 | 觉醒/PS 等叠加层引用 |
| `asset_binding` | 是 | M0：`placeholder: true` |

### 6.1 武装槽 `slot`

| 槽位 | 用途 |
|------|------|
| `main` | 主兵装 |
| `sub` | 副兵装 |
| `melee` | 格斗武装 |
| `shield` | 盾牌/防御装备 |
| `special` | 特殊系统（ファンネル、方向装甲等） |

同一形态内 `(slot, weapon_id)` 不可重复（`R-FORM-012`）。

### 6.2 `transform_graph`（变形）

```yaml
transform_graph:
  - to: form.gat_x303.ms
    trigger: manual          # manual | auto_speed | auto_altitude | purge
    duration_sec: 2.5
    one_way: false           # true = 单程パージ/不可逆
    constraints:
      min_altitude_m: 0
      forbid_states: [grappled]
```

- 目标 `to` 必须存在且与当前形态 **同一底盘**（`R-FORM-002`）。  
- 非 `one_way` 的边须在目标形态上有反向边，否则报错。

### 6.3 `mode_overlays`（装甲/觉醒）

```yaml
mode_overlays:
  - overlay_id: overlay.seed_mode
    requires:
      pilot_trait: trait.seed_awakening
      hp_ratio_below: 0.35    # 可选
```

叠加层定义在 `data/overlays/`；若 overlay 声明 `requires_trait`，形态侧应显式写出对应 `pilot_trait`（否则 `R-OVERLAY-007` Warning）。

---

## 7. 武装 `weapon`（`weapons/*.yaml`）

**语义**：可被多形态复用的兵装定义；通过 `weapon_id` 引用。

| 字段 | 必填 | 语义 |
|------|------|------|
| `id` | 是 | `weapon.*` |
| `display_name_key` | 是 | 显示名 |
| `category` | 是 | `beam` \| `ballistic` \| `melee` \| `special` |
| `slot_types` | 是 | 可装配槽位列表，须覆盖形态中的 `slot` |
| `damage_class` | 是 | `light` \| `medium` \| `heavy` \| `siege` |
| `range_class` | 是 | `melee` \| `short` \| `mid` \| `long` |
| `magazine` / `total_ammo` / `reload_sec` | 否 | 弹匣与总弹数（射击类） |
| `melee_combo` | 否 | 格斗段数 |
| `lock_count` | 否 | 多目标锁定上限（如全弹齐射） |
| `tags` | 否 | `chargeable`、`multi_lock`、`predictive` 等机制标签 |
| `notes` | 否 | 设计者备注 |
| `asset_binding` | 是 | `model_id` / `vfx_id` / `sfx_id`；M0 占位 |

**槽位匹配**：形态装配时武装的 `slot_types` 必须包含所用 `slot`（`R-WEAPON-004`）。

---

## 8. 驾驶员 `pilot`（`pilots/*.yaml`）

**语义**：原创驾驶员与通用模板（M0 **不收录**官方角色姓名/肖像）。

**特质 `traits[]`**

| 字段 | 语义 |
|------|------|
| `id` | `trait.*` |
| `display_name_key` | 显示名 |

**驾驶员 `pilots[]`**

| 字段 | 必填 | 语义 |
|------|------|------|
| `id` | 是 | `pilot.*` |
| `display_name_key` | 是 | 显示名 |
| `kind` | 是 | `player_avatar` \| `partner` \| `generic` \| `guest` |
| `origin` | 是 | M0 固定 `original` |
| `growth_template` | 是 | 成长曲线模板键（如 `growth.balanced`） |
| `traits` | 否 | 特质 ID 列表 |
| `abilities` | 否 | 驾驶员技能 |
| `notes` | 否 | 备注 |

底盘通过 `compatible_pilots` 声明可驾驶关系。

---

## 9. 本地化 `locale`（`locales/*.yaml`）

| 字段 | 必填 | 语义 |
|------|------|------|
| `locale` | 是 | BCP 47 风格，如 `zh_CN` |
| `base` | 否 | **有且仅有一个** 文件为 `true`；基准语言 |
| `entries` | 是 | `loc.*` → 显示字符串 映射 |

规则：

- 任意数据文件中出现 `loc.foo.bar`，**基准语言**必须提供翻译（`R-LOC-009` Error）。  
- 非基准语言缺失为 Warning。  
- 基准语言中未被引用的键为 Info（`R-LOC-010`）。

**键命名惯例**

| 用途 | 模式 |
|------|------|
| 机体名 | `loc.unit.<slug>` |
| 机体描述 | `loc.unit.<slug>.desc` |
| 形态名 | `loc.form.<slug>` |
| 武装名 | `loc.weapon.<slug>` |
| 阵营 | `loc.faction.<slug>` |

术语可参考公开中文译名，**不复制**官方长文本。

---

## 10. 首发 18 机索引

名单来源：[`docs/03-units-and-data.md`](./03-units-and-data.md) §3.6 第 1–18 项。

| # | 显示名 | 型号 | 底盘文件 | 机制标签 |
|---|--------|------|----------|----------|
| 1 | 强袭 | GAT-X105 | `gat-x105` | 换装 |
| 2 | 短剑 L | GAT-01A2R | `gat-01a2r` | 量产基准 |
| 3 | 灾恶 | GAT-X131 | `gat-x131` | 重火力/装甲 |
| 4 | 禁断 | GAT-X252 | `gat-x252` | 方向防御 |
| 5 | 强夺 | GAT-X370 | `gat-x370` | 变形 MS↔MA |
| 6 | 圣盾 | GAT-X303 | `gat-x303` | 变形 |
| 7 | 盖茨 | ZGMF-600 | `zgmf-600` | 平衡基准（power_budget 1000） |
| 8 | 金恩 | ZGMF-1017 | `zgmf-1017` | 量产杂兵 |
| 9 | 扎古勇士 | ZGMF-1000 | `zgmf-1000` | 换装 |
| 10 | 脉冲 | ZGMF-X56S | `zgmf-x56s` | 换装+核心 |
| 11 | 混沌 | ZGMF-X24S | `zgmf-x24s` | 变形 MA |
| 12 | 自由 | ZGMF-X10A | `zgmf-x10a` | SEED 模式叠加 |
| 13 | 正义 | ZGMF-X09A | `zgmf-x09a` | 流星合体形态 |
| 14 | 命运 | ZGMF-X42S | `zgmf-x42s` | 高机动 |
| 15 | 无限正义 | ZGMF-X20A | `zgmf-x20a` | 综合/后期 |
| 16 | 强袭嫣红 | MBF-02 | `mbf-02` | 精简换装 |
| 17 | M1 异端 | MBF-M1 | `mbf-m1` | 量产/防御 |
| 18 | 红色异端 | MBF-P02 | `mbf-p02` | 近战特化 |

---

## 11. 如何新增一台机体

以下 checklist 适用于 M0 之后扩编；M0 新增机体须同步更新 `milestone` 与里程碑规则。

### 11.1 步骤

1. **规划** — 确认机制类型（换装/变形/单形态）、阵营、`power_budget` 区间、考据 `sources`。  
2. **本地化** — 在 `data/locales/zh_cn.yaml` 添加 `loc.unit.*`、`loc.form.*` 及武装/技能键。  
3. **武装** — 若需新兵装，在 `data/weapons/*.yaml` 添加条目，并在 `units_manifest.yaml` 的 `libraries.weapons` 中已引用的文件内编写。  
4. **形态集** — 新建 `data/units/forms/<slug>.yaml`，填写 `parent_chassis` 与各 `form`。  
5. **底盘** — 新建 `data/units/chassis/<slug>.yaml`，`forms` 列表与 `forms_ref` 与形态文件 **双向一致**。  
6. **清单** — 在 `units_manifest.yaml` 的 `chassis_index` 追加 `{ ref: units/chassis/<slug>.yaml }`。  
7. **校验** — `make validate-data-strict`；提交 PR 时 CI 自动复验。  
8. **引擎** — 构建产物刷新后，Godot 标题画面「机体一览」自动反映新条目。

### 11.2 常见陷阱

| 陷阱 | 规则 |
|------|------|
| 形态文件被两台底盘共用 | `R-CHASSIS-001`：每个 `forms_ref` 独占 |
| 底盘 `forms` 与形态文件列表不一致 | `R-CHASSIS-001` 双向校验 |
| 多形态但未写 `form_switch_policy` | `R-CHASSIS-003` Error |
| 武装装到不支持的槽位 | `R-WEAPON-004` |
| 忘记在 manifest 注册文件 | `R-MANIFEST-002` 孤儿文件 |
| M0 使用非占位资产 | `R-ASSET-010` Error |

### 11.3 最小单形态模板（示意）

底盘 `units/chassis/example.yaml`：

```yaml
schema_version: "1.0.0"
balance_patch: "2026.08.0"
id: chassis.example
model_number: EXAMPLE-00
display_name_key: loc.unit.example
description_key: loc.unit.example.desc
series: seed
era: ce71
faction_production: faction.omni
faction_playable: faction.omni
tags: [mass_produced]
power_budget: 1000
base_stats:
  hp: 1000
  en: 120
  mobility: 0.70
  defense: 0.65
  size_class: medium
forms:
  - form.example.standard
forms_ref: units/forms/example.yaml
default_form: form.example.standard
form_switch_policy:
  type: none
compatible_pilots:
  - pilot.generic_rookie
sources:
  - "贡献者 PR 说明"
asset_binding:
  model_id: placeholder.mech.block_medium
  placeholder: true
```

形态 `units/forms/example.yaml`：

```yaml
schema_version: "1.0.0"
parent_chassis: chassis.example
forms:
  - id: form.example.standard
    display_name_key: loc.form.example_standard
    type: base_form
    weapons:
      - slot: main
        weapon_id: weapon.beam_rifle_standard
      - slot: melee
        weapon_id: weapon.beam_saber_standard
    transform_graph: []
    asset_binding:
      model_id: placeholder.mech.block_medium
      placeholder: true
```

（模板数值仅为结构示例，请按相对强度自行调整。）

---

## 12. 校验规则 R-* 对照表

实现：`tools/data_validator/validate.py`。级别：**E** = Error，**W** = Warning，**I** = Info。

| 规则 ID | 级别 | 触发条件 | 数据作者应对 |
|---------|------|----------|--------------|
| `R-SCHEMA-000` | E | YAML 语法/重复键，或不符合 JSON Schema | 对照 `data/schema/*.json` 修正字段类型与必填项 |
| `R-MANIFEST-001` | E | manifest 引用的文件不存在 | 修正 `ref` 路径或补文件 |
| `R-MANIFEST-002` | E | `data/` 下 YAML 未被 manifest 引用 | 加入 `chassis_index` 或 `libraries`，或删除孤儿文件 |
| `R-ID-001` | E | 全局 ID 重复 | 改用新 ID |
| `R-CHASSIS-001` | E | 形态归属/声明不一致；`forms_ref` 被多底盘引用 | 保持底盘↔形态 1:1 文件；双向列表一致 |
| `R-CHASSIS-002` | E | `default_form` 不在 `forms` 列表 | 修正默认形态 ID |
| `R-CHASSIS-003` | E/W | 多形态无 policy / 单形态多余 policy | 按 §5.1 设置 `form_switch_policy` |
| `R-FORM-002` | E | 变形目标缺失、跨底盘、双向边未闭合 | 补全 `transform_graph` 或设 `one_way: true` |
| `R-FORM-005` | E | 形态无 `main`/`melee` 武装 | 至少装配一件攻击武装 |
| `R-FORM-012` | E | 重复 `(slot, weapon_id)` | 删除重复行 |
| `R-WEAPON-003` | E | `weapon_id` 不存在 | 先建武装或改引用 |
| `R-WEAPON-004` | E | 武装不支持该槽位 | 改 `slot` 或换 `slot_types` 匹配的武装 |
| `R-ABILITY-006` | E | 技能 ID 不存在 | 在 `abilities/` 补条目 |
| `R-OVERLAY-007` | E/W | 叠加层或特质缺失；特质未显式声明 | 补 `overlays/` / `traits` 并写 `requires.pilot_trait` |
| `R-PILOT-004` | E/W | 驾驶员/特质不存在；`compatible_pilots` 为空 | 补 pilot 或确认剧情专用 |
| `R-FACTION-008` | E | 阵营 ID 未在 manifest 定义 | 扩 `factions` 或改 ID |
| `R-LOC-009` | E/W | 基准语言缺键 / 其他语言缺键 | 在 `locales/zh_cn.yaml` 补全 |
| `R-LOC-010` | I | 基准语言多余键 | 可清理或保留 |
| `R-ASSET-005` | W | 缺少 `asset_binding` | 开发中可暂缺；合入前应补全 |
| `R-ASSET-010` | E | M0 非占位资产 | 设 `placeholder: true` |
| `R-BALANCE-006` | W | `power_budget` 偏离 1000 超过 ±20% | 复核强度设计 |
| `R-MILESTONE-011` | W | `milestone: M0` 但底盘数 ≠ 18 | 扩编时改 milestone 或补全名单 |

完整 CLI 说明：[`tools/data_validator/README.md`](../tools/data_validator/README.md)。

---

## 13. 相关文档

| 文档 | 内容 |
|------|------|
| [`docs/M0-STATUS.md`](./M0-STATUS.md) | M0 验收状态与未完成项 |
| [`docs/03-units-and-data.md`](./03-units-and-data.md) | 100+ 规划、平衡框架、Must/Should/Later |
| [`docs/REMAKE-PLAN.md`](./REMAKE-PLAN.md) | 总方案；对照 Steam AppID 1857740 |
| [`docs/adr/ADR-0001-locked-decisions.md`](./adr/ADR-0001-locked-decisions.md) | 已锁定工程决策 |

---

*本文档描述数据结构，不保证与任何官方产品数值一致。*
