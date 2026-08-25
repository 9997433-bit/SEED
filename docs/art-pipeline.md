# 美术资产管线（占位规范 · M0）

> **文档性质**：原创资产制作与入库规范（M0 占位版，随 M2/M3 收敛）  
> **最后更新**：2026-08-25  
> **红线**：本项目 **不接受任何官方资产**。所有资产必须是原创、委托原创，或明确许可可再分发的第三方素材。

## 0. 第一原则：资产必须是原创

| 允许 | 禁止 |
|------|------|
| 完全原创的建模 / 贴图 / 动画 / 音频 | 从原作游戏、动画、模型套件、官方网站提取或复制的任何文件 |
| 委托美术按本项目设定稿制作（有合同/授权凭证） | 对官方模型做重拓扑、减面、改材质、改比例后入库 |
| 许可明确且可再分发的第三方素材（CC0 / CC-BY / OFL / 有商用授权） | 逐帧描摹官方图像、把官方截图当贴图或 UI 底图 |
| 参考 **公开设定的机体机能与轮廓语汇** 做风格化再设计 | 以官方资产为训练/生成输入的产物（含图生图、模型重建） |
| 自制的占位几何体（方块拼装等） | 来源不明、无法举证作者与许可的素材 |

**判定原则**：任何资产都要能回答「谁做的、什么许可、从哪来」。答不出 → 不合入。入库登记见 [`docs/legal/asset-checklist.md`](./legal/asset-checklist.md) 与 [`docs/legal/NOTICE.md`](./legal/NOTICE.md)。

**造型合规底线**：机体设计需 **可区分**。允许致敬「双眼摄像头 + V 型天线 + 人形 MS」这类通用类型语汇，禁止复刻具体官方机体的可识别专有造型特征组合与配色到「一眼认成官方机体」的程度。有疑问时，走 PR 讨论并保留设计稿溯源。

## 1. 当前状态（M0）

M0 的全部「资产」是 **运行时程序化生成的方块占位机体**（`game/scripts/common/placeholder_mech.gd`），仓库内 **没有任何外部素材文件**。

数据层已为资产替换预留接口：每台机体的 `asset_binding` 与数据解耦，M0 阶段全部 `placeholder: true`（校验规则 `R-ASSET-010` 会阻断非占位资产在 M0 入库）。

```text
data/units/**.yaml  ──asset_binding──▶  game/assets/**（M2 起）
        │                                      ▲
        └── placeholder: true（M0）────────────┘ 占位由代码生成
```

## 2. 工具链

```text
Blender 4.x（建模/绑定/动画）
   └─ glTF 2.0 (.glb) 导出 ─▶ game/assets/<域>/<资产>/  ─▶ Godot 4.3 导入 (.import 随源文件提交)
Krita / Substance / Materialize（贴图） ─▶ PNG（源）─▶ Godot VRAM 压缩
Audacity / Reaper（音频）              ─▶ WAV（源，48 kHz）─▶ OGG（长音轨）
```

| 环节 | 选型 | 说明 |
|------|------|------|
| DCC | **Blender 4.x** | 开源、免许可摩擦；`.blend` 源文件按需入库（见 §6 体积规则） |
| 交换格式 | **glTF 2.0（.glb）** | Godot 原生支持；避免 FBX 的转换歧义 |
| 贴图 | PNG（8-bit sRGB / 线性） | 源文件无损；压缩交给引擎导入设置 |
| 音频 | WAV 48 kHz 源；短音效 WAV、长音轨 OGG Vorbis | 与 Godot 导入默认一致 |
| 版本管理 | Git（不使用 LFS，除非单文件 > 10 MB 成为常态） | 体积失控时再评估 LFS |

## 3. 坐标、单位与命名

| 约定 | 值 |
|------|-----|
| 单位 | **1 Godot 单位 = 1 米**；Blender 场景单位设为米，导出不缩放 |
| 朝向 | Godot 中模型 **面向 -Z**，**+Y 向上**；Blender 导出勾选 `+Y Up` |
| 原点 | 机体原点在 **双脚之间地面高度**；武装/挂点原点在其安装面 |
| 机体尺度 | 人形 MS 高度 **16–20 m**（项目自建口径，非官方数值） |
| 三角面朝向 | 逆时针为正面；导出前清理反转法线 |

**命名规范**（全小写 + 下划线，与数据层 ID 对齐）：

```text
game/assets/
├── units/<chassis_id>/                  # 例：units/gat-x105/
│   ├── gat-x105_body.glb
│   ├── gat-x105_albedo.png
│   ├── gat-x105_orm.png                 # R=AO, G=Roughness, B=Metallic
│   └── gat-x105_normal.png
├── weapons/<weapon_id>/
├── vfx/<effect_id>/
├── ui/<screen>/
├── audio/{bgm,se,voice}/
└── placeholder/                          # 占位资产（M0 全部在此，且当前为空目录 + 说明）
```

节点/骨骼命名：`root`、`hips`、`spine`、`head`、`arm_l_upper`…（左右后缀 `_l` / `_r`），挂点用 `socket_<name>`（如 `socket_weapon_r`、`socket_thruster_back`）。

## 4. 网格预算与 LOD（受 Switch 约束驱动）

预算按 REMAKE-PLAN §4.5「同屏机体 ≤ 9、运行时纹理 ≤ ~1.5 GB」反推，属 **初稿**，M1 性能基线后修订。

| 类别 | LOD0 三角面 | LOD1 | LOD2 | 贴图（Albedo） |
|------|-------------|------|------|----------------|
| 主角/可玩机体 | ≤ 40 k | ≤ 18 k | ≤ 6 k | 2048² |
| 量产/杂兵机体 | ≤ 20 k | ≤ 9 k | ≤ 3 k | 1024² |
| Boss / 超规格机体 | ≤ 70 k | ≤ 30 k | ≤ 10 k | 2048²（可 +1 张） |
| 武装 / 挂件 | ≤ 6 k | ≤ 2 k | — | 1024² |
| 场景模块件 | ≤ 8 k | ≤ 3 k | — | 1024²（可平铺） |

规则：

- 每台机体的材质槽 **≤ 4**；优先靠图集合并而不是拆材质。
- 贴图边长为 2 的幂；ORM 三通道打包，禁止一张图只用一个通道。
- 法线贴图用切线空间；不烘焙光照进 Albedo。
- LOD 由 Godot 的自动 LOD 生成兜底，人工 LOD 仅对轮廓关键机体制作。

## 5. 材质与压缩

| 平台 | VRAM 压缩 |
|------|-----------|
| PC（Steam） | S3TC / BPTC |
| Switch（未来） | ETC2 / ASTC（`project.godot` 已开 `import_etc2_astc`） |

- 统一 **PBR Metallic-Roughness**；不使用引擎独占的高级材质特性（见 Switch spike §4「渲染后端」风险）。
- 发光部件（推进器、光束刃、单眼）用 `emission`，强度值写进数据层的可调参数，避免美术侧硬编码。
- 透明材质仅用于必要的 VFX；机体本体禁止使用 alpha blend。

## 6. 动画

| 约定 | 值 |
|------|-----|
| 采样率 | 30 fps 烘焙（引擎侧插值到显示帧率） |
| 根运动 | 战斗位移由代码驱动，动画 **不带根位移**（`root` 骨骼保持原地） |
| 命名 | `idle`、`walk_fwd`、`boost_dash`、`melee_01`…（小写下划线，序号两位） |
| 骨骼数 | 单机体 ≤ 80（含挂点骨骼） |
| 混合 | 通过 AnimationTree 状态机；导出的 glTF 只提供裸动画片段 |

## 7. 音频

- 全部 **原创或 CC0/明确授权**；旋律不得与原作曲目构成实质性相似。
- 采样率 48 kHz；BGM 循环点用 Godot 导入设置里的 loop offset，不靠文件裁剪。
- 响度目标：BGM ≈ -18 LUFS，SE 峰值 ≤ -3 dBFS（初稿，M3 混音时统一）。
- 音量分组对应运行时的 `Settings` autoload（`master` / `music` / `sfx`）。

## 8. 入库流程

1. 在 `game/assets/<域>/<id>/` 建目录，放 **源文件 + 导出件 + Godot `.import`**。
2. 更新对应数据条目的 `asset_binding`；离开占位阶段时把 `placeholder` 置为 `false`。
3. 在 [`docs/legal/NOTICE.md`](./legal/NOTICE.md) §4 资产登记表补一行（ID / 类型 / 作者 / 许可 / 来源 / 备注）。
4. 提 PR 时逐条勾选 [`docs/legal/asset-checklist.md`](./legal/asset-checklist.md)。
5. CI 通过（数据校验 + Godot headless 导入冒烟）后方可合入。

**体积规则**：单个提交新增资产 > 50 MB 需在 PR 说明理由；`.blend` 源文件超过 20 MB 时改为仅提交 `.glb` + 外部归档链接。

## 9. 待补（M2/M3）

| 项 | 里程碑 |
|----|--------|
| 资产 CI：贴图尺寸/三角面/命名的自动检查 | M3 |
| 机体设计稿模板与轮廓审查流程 | M2 |
| 字体选型与再分发许可（CJK） | M3（见 Switch spike B-6） |
| VFX 规范（光束、推进、爆炸的统一语汇） | M2 |
| 材质母版（machine / glass / emissive 的共享 shader） | M2 |

---

*本文件为工程规范，不构成法律意见。资产合规最终以 [`docs/legal/NOTICE.md`](./legal/NOTICE.md) 与 PR 检查单为准。*
