## 三、机体与数据

> **定位**：本章定义粉丝重制版《机动战士高达 SEED 激斗命运》的机体内容规模、换装/变形/装甲的数据建模方式，以及无官方资源条件下的数据驱动工作流。所有设计以「可扩展至 100+ 机体、可维护、可验证」为约束，不涉及具体引擎实现代码。

---

### 3.1 设计目标与约束

| 维度 | 目标 | 说明 |
|------|------|------|
| **内容规模** | 100+ 可操控机体 | 含主机体、换装形态、变形形态、装甲变体；同一型号不同驾驶员视为独立条目或共享底盘（见 3.3） |
| **玩法还原** | 激斗命运核心体验 | 单机任务、联机共斗、机体养成、SP 技能、换装即时切换、部分机体变形/合体 |
| **数据来源** | 零官方资源 | 数值、模型、动画、音效均来自社区整理、逆向观测、粉丝复刻；数据与资产解耦 |
| **可维护性** | 数据驱动 | 策划/粉丝通过 JSON/YAML 增删改机体，无需改代码即可入库、校验、生成游戏内配置 |
| **版权边界** | 粉丝非商用 | 命名与设定引用 SEED 世界观；对外分发遵循非商用与署名约定 |

**核心原则**：机体不是「一个模型 + 一组固定数值」，而是「**底盘（Chassis）+ 形态（Form）+ 武装（Loadout）+ 驾驶员（Pilot）**」的组合实体，由数据层声明关系，运行时解析装配。

---

### 3.2 数据驱动总体架构

```text
┌─────────────────────────────────────────────────────────────┐
│  策划层：YAML/JSON 源数据（人类可读、可 diff、可 PR 审核）      │
└──────────────────────────┬──────────────────────────────────┘
                           │ Schema 校验（JSON Schema / 自定义规则）
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  构建层：引用解析、继承展开、形态图编译、数值归一化            │
└──────────────────────────┬──────────────────────────────────┘
                           │ 生成中间产物（游戏内 ID 表、兼容矩阵、本地化键）
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  运行时：机体实例 = 解析(底盘, 当前形态, 武装, 驾驶员, 养成)   │
└─────────────────────────────────────────────────────────────┘
```

**无官方资源时的数据获取策略**：

1. **基准观测**：参考原版激斗命运、SEED/SEED DESTINY 动画与设定资料，建立「相对强度」与「机制标签」，而非追求绝对数值一致。
2. **社区共建**：机体条目以 Pull Request 形式提交；必填出处备注（动画集数、设定集页码、实测录像时间戳等）。
3. **版本戳记**：每条数据带 `schema_version` 与 `balance_patch`，支持平衡性迭代而不破坏存档兼容策略（见 3.7）。

---

### 3.3 核心概念模型

#### 3.3.1 实体分层

| 概念 | 英文键 | 含义 | 示例 |
|------|--------|------|------|
| **机体底盘** | `chassis` | 不可拆分的「素体」身份，决定基础机动、体型、可接入的形态族 | `GAT-X105` 强袭素体 |
| **形态** | `form` | 可在战斗中切换或战前选择的完整外观/性能包 | 强袭·空装 / 强袭·剑装 |
| **武装槽** | `loadout_slot` | 形态内的可替换部件（非全形态换装） | 盾牌、辅助推进器 |
| **变体** | `variant` | 同底盘不同涂装、不同默认武装或驾驶员绑定 | 强袭嫣红 |
| **驾驶员** | `pilot` | 影响成长曲线、专属 SP、部分形态解锁 | 基拉·大和 |
| **可玩条目** | `playable_unit` | 玩家可选的最终单位 ID，= 底盘 + 形态组 + 驾驶员 + 解锁状态 | `playable.strike.kira.aile` |

#### 3.3.2 三种特殊机制的数据表达

**① 换装（Equipment Swap）**

- 同一 `chassis` 下挂载多个 `form`，共享 HP/EN 条（或按规则部分继承）。
- 切换有冷却、硬直或消耗（由 `form_switch_policy` 声明）。
- 代表机体：强袭、脉冲、扎古勇士、强袭嫣红。

**② 变形（Transform）**

- `form` 之间构成有向图（`transform_graph`），边带条件：速度阈值、能量、地面/空中、是否装备特定背包。
- 变形时常伴随碰撞体积、受击框、可用武装列表变化。
- 代表机体：圣盾、强夺、混沌、盖亚、深渊、正义/自由（流星装备）。

**③ 装甲/模式（Armor / Mode）**

- 不改变外形骨架，但修改伤害减免、移动方式、武装生效规则。
- 用 `mode_modifier` 叠加在 `form` 上，而非新建完整形态（减少资产量）。
- 代表机体：灾恶（重火力站桩）、禁断（相转移护盾面）、自由/命运（觉醒/SEED 模式类 buff）。

```text
换装：  底盘 ──< 形态A, 形态B, 形态C >── 运行时切换
变形：  形态A ──transform──> 形态A'（单向或双向）
装甲：  形态A + mode_modifier（同一 mesh 骨骼，参数覆写）
```

---

### 3.4 Schema 概念设计（JSON/YAML）

以下用 **YAML 风格片段** 说明字段语义；实际可采用 JSON 等价表示，并由 JSON Schema 约束。

#### 3.4.1 顶层清单 `units_manifest.yaml`

```yaml
schema_version: "1.0.0"
balance_patch: "2026.08.0"
factions:
  - id: faction.omni
    name_key: loc.faction.omni
  - id: faction.zaft
    name_key: loc.faction.zaft
  - id: faction.orb
    name_key: loc.faction.orb
  - id: faction.three_ships
    name_key: loc.faction.three_ships
  - id: faction.mercenary
    name_key: loc.faction.mercenary

chassis_index:        # 指向各底盘文件
  - ref: chassis/GAT-X105.yaml
  - ref: chassis/ZGMF-X56S.yaml
  # ... 100+ 条目

playable_index:       # 可操控组合（驾驶员 × 形态组）
  - ref: playable/strike_kira.yaml
```

#### 3.4.2 底盘定义 `chassis/GAT-X105.yaml`

```yaml
id: chassis.gat_x105
display_name_key: loc.unit.strike
series: seed
faction_default: faction.omni
era: ce71
tags: [g_project, striker, swap_pack]

base_stats:
  hp: 1000          # 相对基准，非绝对
  en: 120
  mobility: 0.72
  defense: 0.65
  size_class: medium

forms:
  - id: form.strike.aile
    ref: forms/strike_aile.yaml
  - id: form.strike.sword
    ref: forms/strike_sword.yaml
  - id: form.strike.launcher
    ref: forms/strike_launcher.yaml

form_switch_policy:
  type: mid_battle_swap
  cooldown_sec: 8
  inherit_hp_ratio: 1.0
  inherit_en_ratio: 0.8
  allowed_states: [ground, air]

compatible_pilots:
  - pilot.kira_yamato
  - pilot.mu_la_flaga

asset_binding:
  model_id: fan_model.gat_x105       # 与数据解耦的模型键
  skeleton_id: skel.gundam_seed_v1
```

#### 3.4.3 形态定义 `forms/strike_aile.yaml`

```yaml
id: form.strike.aile
parent_chassis: chassis.gat_x105
display_name_key: loc.form.aile
type: equipment_form          # equipment_form | transform_form | mode_overlay

stat_modifiers:
  mobility: +0.08
  defense: -0.02

weapons:
  - slot: main
    weapon_id: weapon.beam_rifle_strike
  - slot: sub
    weapon_id: weapon.beam_saber
  - slot: back
    weapon_id: weapon.aile_pack_vulcan

abilities:
  - ability.sp.boost_dash

transform_graph: []           # 换装形态无变形边

mode_overlays:                # 可选装甲/觉醒叠加
  - overlay_id: overlay.seed_mode
    requires: { pilot_trait: trait.seed }
```

#### 3.4.4 变形形态 `forms/aegis_ma.yaml`

```yaml
id: form.aegis.ma
parent_chassis: chassis.gat_x303
type: transform_form
display_name_key: loc.form.aegis_ma

stat_modifiers:
  mobility: +0.15
  defense: +0.10
  size_class: large

transform_graph:
  - to: form.aegis.ms
    trigger: manual
    duration_sec: 2.5
    constraints:
      min_altitude_m: 0
      forbid_states: [grappled]

weapons:
  - slot: main
    weapon_id: weapon.scylla_cannon
  - slot: sub
    weapon_id: weapon.phase_cannon_array
```

#### 3.4.5 可玩条目 `playable/strike_kira.yaml`

```yaml
id: playable.strike.kira
chassis: chassis.gat_x105
pilot: pilot.kira_yamato
default_form: form.strike.aile
unlock:
  campaign: mission.arc1.m03
  cost: { points: 0 }

growth:
  template: growth.striker_hero
  sp_skills:
    - sp.kira.full_burst
    - sp.kira.pilot_instinct

ui:
  icon_id: ui.icon.strike
  sort_weight: 10
  faction_display: faction.three_ships   # 剧情阵营可与生产阵营不同
```

#### 3.4.6 跨条目引用与校验规则

| 规则 ID | 描述 | 严重级别 |
|---------|------|----------|
| `R-CHASSIS-001` | 每个 `form` 必须且仅属于一个 `chassis` | Error |
| `R-FORM-002` | `transform_graph` 边必须双向闭合或显式声明单向 | Error |
| `R-WEAPON-003` | `weapon_id` 必须在武器库中存在 | Error |
| `R-PILOT-004` | `compatible_pilots` 为空时视为剧情专用不可选 | Warning |
| `R-ASSET-005` | `asset_binding` 缺失时允许占位（开发中机体） | Warning |
| `R-BALANCE-006` | 同级机体 `power_budget` 总和偏差 ≤ 15% | Warning |

---

### 3.5 100+ 机体规模规划

#### 3.5.1 计数口径

| 口径 | 目标 | 说明 |
|------|------|------|
| **底盘数** | 55–65 | 合并极度相似量产型（如金恩/扎古量产） |
| **形态数** | 120–150 | 含换装包、变形态、流星等合体形态 |
| **可玩条目** | 100–130 | 驾驶员差异、剧情专用机、异端涂装变体 |
| **NPC/杂兵** | 40+ | 可复用底盘 + 数值缩放，不全部进入玩家库 |

#### 3.5.2 分阶段扩充路线（内容）

| 批次 | 数量级 | 内容侧重 |
|------|--------|----------|
| **首发** | 15–20 可玩条目 | 验证换装/变形/装甲全链路 |
| **CE71 篇** | +30 | G 计划五机、三舰同盟主力、奥布线 |
| **CE73 篇** | +35 | 脉冲系、扎古、混沌/盖亚/深渊、自由/正义新形态 |
| **外传/异端** | +25 | 异端系列、MBF/P 变体、杂志机体 |
| **量产/杂兵** | +20 | 联机敌人、生存模式、舰队战 |

#### 3.5.3 阵营标签策略

每台机体持有：

- `faction_production`：生产/所属势力（用于图鉴与生产线）。
- `faction_playable`：玩家选用时默认归类（随剧情可变更，如强袭→三舰同盟）。
- `tags`：机制检索用（`transform`, `swap_pack`, `heavy`, `support`, `boss`）。

---

### 3.6 首发机体名单（18 机）

以下 18 台为 **Must 首发** 可玩条目，按阵营分类，刻意覆盖 **换装 / 变形 / 装甲** 三类机制代表。

#### 地球联合军（OMNI）— 5 机

| # | 机体 | 型号 | 机制代表 | 设计备注 |
|---|------|------|----------|----------|
| 1 | **强袭高达** | GAT-X105 | **换装** | 空装/剑装/炮装三形态切换，全项目换装基准 |
| 2 | **短剑 L** | GAT-01A2R | 量产 | 联机友军/敌人模板，低门槛机体 |
| 3 | **灾恶高达** | GAT-X131 | **装甲/重火力** | 高 HP、低机动、站桩炮击；验证重机体手感 |
| 4 | **禁断高达** | GAT-X252 | **装甲/防御** | 相转移护盾方向性减伤，验证方向装甲逻辑 |
| 5 | **强夺高达** | GAT-X370 | **变形** | MS↔MA 双形态，验证大型变形碰撞与武装差分 |

#### ZAFT — 6 机

| # | 机体 | 型号 | 机制代表 | 设计备注 |
|---|------|------|----------|----------|
| 6 | **圣盾高达** | GAT-X303 | **变形** | 圣盾 MS↔MA；早期 G 计划机体，ZAFT 俘获设定 |
| 7 | **盖茨** | ZGMF-600 | 二代主力 | CE71 后期 ZAFT 标准战力，平衡型基准 |
| 8 | **金恩** | ZGMF-1017 | 量产 | 杂兵代表，生存模式基础敌人 |
| 9 | **扎古勇士** | ZGMF-1000 | **换装** | 战士型/幻影型；验证幻影粒子涂装与命中修正 |
| 10 | **脉冲高达** | ZGMF-X56S | **换装+核心** | 空装/剑装/炮装 + 核心战机分离（可简化为形态切换） |
| 11 | **混沌高达** | ZGMF-X24S | **变形** | 空中 MA 形态；与盖亚/深渊组成异端三机变形组 |

#### 三舰同盟 — 4 机

| # | 机体 | 型号 | 机制代表 | 设计备注 |
|---|------|------|----------|----------|
| 12 | **自由高达** | ZGMF-X10A | **装甲/觉醒** | 五彩炮击；SEED 模式叠加层验证 |
| 13 | **正义高达** | ZGMF-X09A | **变形/合体** | 本体 + 流星装备（大型合体形态，独立 form） |
| 14 | **命运高达** | ZGMF-X42S | **装甲/高机动** | 光翼、掌中炮；高机动 Boss 级手感调校 |
| 15 | **无限正义高达** | ZGMF-X20A | 综合 | 流星背包可选形态；首发后期解锁目标 |

#### 奥布 — 2 机

| # | 机体 | 型号 | 机制代表 | 设计备注 |
|---|------|------|----------|----------|
| 16 | **强袭嫣红** | MBF-02 | **换装（精简）** | 空装/剑装；验证「少形态换装」与女性向 UI 资源 |
| 17 | **M1 异端** | MBF-M1 | 量产/防御 | 光束军刀盾、团队支援；奥布量产代表 |

#### 佣兵 / 中立 — 3 机

| # | 机体 | 型号 | 机制代表 | 设计备注 |
|---|------|------|----------|----------|
| 18 | **红色异端** | MBF-P02 | 近战特化 | 菊一文字；验证异端骨架与自定义武装 |
| 19 | **蓝色异端** | MBF-P03 | 炮击特化 | 超级火箭筒；远程物理武装代表 |
| 20 | **暴风高达** | GAT-X103 | 火力/协作 | 双炮齐射、友军增益标签；G 计划协作机体 |

> **首发实际可玩 18 机**：上表 1–18 为硬性首发；19–20（蓝异端、暴风）为首发末周或首日补丁 **Should**，用于验证「非主角势力 G 计划机」入库流程。

**机制覆盖自检**：

| 机制 | 首发代表机体 |
|------|----------------|
| 换装 | 强袭、扎古勇士、脉冲、强袭嫣红 |
| 变形 | 圣盾、强夺、混沌（+ 正义流星） |
| 装甲/模式 | 灾恶、禁断、自由（SEED 模式）、命运 |

---

### 3.7 Must / Should / Later 优先级

#### Must（首发版本必须具备）

| 类别 | 项 | 验收标准 |
|------|----|----------|
| **数据** | Schema v1 + 校验 CLI | 全量 YAML 通过 `R-*` 规则；CI 阻断 Error |
| **数据** | 18 机完整条目 | 底盘/形态/武装/驾驶员/成长/本地化键齐全 |
| **机制** | 换装切换 | 强袭三装战内切换，冷却与 EN 继承符合 `form_switch_policy` |
| **机制** | 变形 | 至少 3 条变形链（圣盾、强夺、混沌）可玩 |
| **机制** | 模式叠加 | 自由 SEED 模式 1 种；验证 `mode_overlay` 管线 |
| **资产** | 占位→替换流程 | 允许方块人/低模占位；`asset_binding` 可热更 |
| **养成** | 单机成长曲线 | 每机 10 级基础成长 + 2 个 SP |
| **联机** | 机体选择同步 | 双方可见对方机体形态与涂装 ID |

#### Should（首发后 3 个月内）

| 类别 | 项 | 说明 |
|------|----|------|
| **内容** | 蓝异端、暴风、盖亚、深渊 | 补全变形三机与 G 计划剩余 |
| **数据** | 形态继承可视化工具 | 策划查看「底盘→形态→武装」树状图 |
| **机制** | 脉冲核心战机分离 | 简化为视觉演出 + 形态切换亦可 |
| **机制** | 流星装备独立 HP 段 | 正义/自由流星被击毁后回退素体 |
| **平衡** | `power_budget` 自动报告 | 超标机体标红，供平衡 Patch |
| **联机** | 换装/变形状态快照 | 断线重连后恢复当前 `form` |

#### Later（长期路线图）

| 类别 | 项 | 说明 |
|------|----|------|
| **内容** | 100+ 全量机体 | 按 3.5.2 批次推进 |
| **内容** | 异端全系列、流星计划、外传机体 | 含黑异端、白异端等 |
| **机制** | 母舰/战舰支援数据化 | 大天使、密涅瓦技能挂接 `battlefield_entity` |
| **机制** | 自定义涂装与贴纸 | `variant` 层扩展玩家创作 |
| **数据** | 社区 Wiki 双向同步 | PR 入库 ↔ 图鉴网站自动生成 |
| **AI** | NPC 机体智能选形态 | 基于 `tags` 与战况的规则/行为树 |

---

### 3.8 数值与平衡框架（无官方资源）

#### 3.8.1 相对基准制

- 定义 **「标准机动 MS」**（盖茨或短剑 L）为 `power_budget = 1000`。
- 每项能力（HP、EN、机动、防御、火力、射程、硬直抗性）分配权重，总和≈1000。
- 特殊机制消耗预算：换装 +50、变形 +80、二段变形 +120、流星合体 +150。

#### 3.8.2 机制标签与克制（软克制）

| 标签 | 弱势对抗 | 强势对抗 |
|------|----------|----------|
| `heavy` | 高机动、绕背 | 站桩、护盾正面 |
| `transform_ma` | 对空弹幕、预判拦截 | 地面量产、追击 |
| `swap_pack` | 被压制时的硬直窗口 | 多距离适应性 |
| `seed_mode` | 持久战 EN 耗尽 | 爆发窗口、Boss 阶段 |

#### 3.8.3 平衡迭代

- 每月一个小 `balance_patch`；仅调整 `stat_modifiers` 与 `weapon` 引用，不改 `id`。
- 存档记录机体 `schema_version`；过时条目读档时按迁移表升级。

---

### 3.9 资产绑定与占位策略

```yaml
# asset_binding 示例字段
asset_binding:
  model_id: fan_model.gat_x105
  lod: [lod0, lod1, lod2]
  animations:
    idle: anim.strike.idle
    transform_to_ma: anim.aegis.transform_out
  vfx:
    beam_color: vfx.beam.blue.kira
  audio:
    footstep: sfx.mech.medium
  placeholder: true          # true 时使用引擎默认几何体
```

- **数据先行**：机体可先于模型完成，用 `placeholder: true` 进入平衡测试。
- **社区分包**：模型/动画/音效独立仓库，通过 `model_id` 松耦合。
- **版权**：每条资产登记来源与授权（自制 / CC / 委托），禁止未授权商用素材。

---

### 3.10 本地化与图鉴

| 键类型 | 约定 | 示例 |
|--------|------|------|
| `display_name_key` | `loc.unit.<slug>` | `loc.unit.strike` → 「强袭高达」 |
| `description_key` | `loc.unit.<slug>.desc` | 图鉴正文 |
| `form.*` | 形态名独立键 | 「空装型」「MA 形态」 |
| `faction.*` | 阵营名 | 地球联合军 / ZAFT / 奥布 / 三舰同盟 / 佣兵 |

图鉴自动生成字段：生产国、驾驶员列表、形态树、武装表、出场任务（`unlock.campaign` 反查）。

---

### 3.11 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| 无官方数值，平衡争议大 | 社区分裂 | 公开 `power_budget` 公式；平衡委员会投票 Patch |
| 变形机体资产量大 | 工期爆炸 | 变形链共享骨骼；MA 形态可先做低模 |
| 100+ 规模数据腐化 | 引用断裂 | CI 强制 Schema 校验；废弃 ID 进 `deprecated.yaml` |
| 驾驶员版权形象 | 法律风险 | 原创肖像或剪影；名称可做可配置 |
| 换装同步联机作弊 | 对战不公 | 服务端校验 `form_switch_policy` 与冷却 |

---

### 3.12 本章小结

- 机体内容以 **底盘—形态—武装—驾驶员** 四层数据模型支撑 **100+** 规模，换装、变形、装甲均可在同一 Schema 下表达，无需为每类机制单独造表。
- **首发 18 机**（可扩至 20）按五大阵营配置，已覆盖激斗命运最具代表性的机制组合；后续按 CE71 / CE73 / 外传批次放量。
- 全流程 **数据驱动**：YAML/JSON 源数据 → Schema 校验 → 构建产物 → 运行时实例化；无官方资源条件下，依靠社区观测、相对基准平衡与占位资产策略可持续迭代。

---

*下一章建议：「四、战斗与联机」— 在机体数据之上定义 hitbox、同步、伤害公式与 SP 触发器。*
