# game/ —— Godot 4 工程（M0 骨架）

## 打开与运行

1. 安装 **Godot 4.3 或更新版本**（标准版即可，无需 .NET 版）。
2. Godot 项目管理器 → **导入** → 选择本目录下的 `project.godot`。
3. 直接 **F5** 运行；主场景为 `scenes/bridge/title_screen.tscn`。

运行后应看到：暗色展示间中的 **原创方块占位机体**（缓慢自转）、标题 UI、以及一行数据管线状态
（例如「已载入 18 台底盘 / 29 个形态 / 27 件武装」）。点「机体一览」可查看首发 18 台机体列表。

## 目录

| 路径 | 说明 |
|------|------|
| `scenes/bridge/` | 舰桥/菜单层场景（M0 仅标题画面） |
| `scenes/combat/` | 战斗场景（M1 起） |
| `scenes/common/` | 通用场景，含占位机体 |
| `scripts/ui/` | UI 逻辑 |
| `scripts/autoload/` | 全局单例（M0 仅 `Settings`：音量 / 界面语言占位） |
| `scripts/ci/` | CI 冒烟脚本（headless 断言，不参与玩法） |
| `scripts/common/` | 通用运行时组件（占位机体拼装） |
| `scripts/data/` | 数据构建产物载入 |
| `scripts/combat/` `scripts/mission/` `scripts/progression/` | M1+ 预留 |
| `assets/placeholder/` | 原创占位资产（M0 全部为运行时生成的方块，无外部素材） |
| `data_build/units_index.json` | **构建产物**，由校验器生成，请勿手工编辑 |

## 数据管线

游戏不直接读取 `data/**.yaml`（GDScript 无内置 YAML 解析器，且 `data/` 在工程目录之外）。
流程是：

```text
data/**.yaml → 校验器（Schema + 引用完整性）→ game/data_build/units_index.json → 运行时只读载入
```

改完 `data/` 后在仓库根目录执行：

```bash
make validate-data
```

产物过期时 CI 会失败（`make check-data-index`）。

## 全局设置（Settings autoload）

`scripts/autoload/settings.gd` 注册为 autoload `Settings`，M0 只覆盖 **音量**（`master` / `music` /
`sfx`，写入同名音频总线，总线不存在时静默跳过）与 **界面语言**（`zh_CN` / `en`），持久化到
`user://settings.cfg`。不含任何战斗或任务逻辑；画质档与键位自定义在 M1+ 接入。

```gdscript
Settings.set_volume("master", 0.6)
Settings.set_locale("en")
Settings.settings_changed.connect(func(section, key, value): pass)
```

## headless 冒烟（CI 复现）

```bash
godot --headless --path game --import
godot --headless --path game --max-fps 60 --quit-after 300          # 主场景跑约 5 秒
godot --headless --path game --script res://scripts/ci/headless_smoke.gd
```

冒烟脚本断言数据构建产物规模、`Settings` autoload 可用、主场景可实例化并跑满 120 帧。
headless 假渲染器会刷 `Parameter "m" is null.`，由 `tools/ci/godot_log_filter.py` 放行；
其余 `ERROR` / `SCRIPT ERROR` 一律判失败。完整流程见 `.github/workflows/build-pc.yml`。

## 已知限制（M0）

- **中文字体**：UI 使用 `SystemFont` 按名查找系统中的 CJK 字体（Noto Sans CJK / 思源黑体 / 微软雅黑 / 苹方等）。
  若系统缺少上述字体，中文会显示为缺字方框；正式的字体授权与打包在本地化管线（M3）处理。
- 无战斗、无任务、无存档；按钮「出击」仅提示 M1 实装。
- `Settings` 只有数据与持久化，尚无设置界面（UI 在 M1 与标题画面一起做）。
- 未提交 `export_presets.cfg`：导出配置由各自本地生成，PC 出包（导出模板 + artifact）在 M1 的 CI 中接入；
  M0 的 `build-pc` 工作流只做导入与 headless 冒烟。
