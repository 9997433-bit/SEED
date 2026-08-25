# data_validator

`data/` 下 YAML 源数据的 **Schema 校验 + 跨条目引用完整性校验** CLI。不依赖 Godot。

## 运行

```bash
python3 tools/data_validator/validate.py                # 校验（退出码 0 = 通过）
python3 tools/data_validator/validate.py --strict       # Warning 也视为失败
python3 tools/data_validator/validate.py --format github  # GitHub Actions 注解格式
make validate-data                                      # 校验 + 刷新构建产物
make check-data-index                                   # 只检查构建产物是否过期
```

| 退出码 | 含义 |
|--------|------|
| `0` | 通过 |
| `1` | 存在 Error（`--strict` 下 Warning 同样失败），或构建产物过期 |
| `2` | 用法错误 / 数据目录不存在 / 缺少 PyYAML |

## 依赖

- **PyYAML**：必需。
- **jsonschema**：可选。未安装时自动回退到内置的 JSON Schema 子集校验器
  （覆盖本仓库 schema 实际使用的关键字：`type` / `enum` / `const` / `required` /
  `properties` / `patternProperties` / `additionalProperties` / `items` / `$ref` /
  `pattern` / 数值与长度边界 / `uniqueItems` / `allOf` / `anyOf` / `oneOf`）。
  设 `SEED_VALIDATOR_FORCE_BUILTIN=1` 可强制走回退路径，CI 会同时回归两条路径。

## 校验规则

| 规则 | 级别 | 说明 |
|------|------|------|
| `R-SCHEMA-000` | Error | YAML 解析（含重复键）或 JSON Schema 校验失败 |
| `R-MANIFEST-001` | Error | 清单引用的数据文件不存在 |
| `R-MANIFEST-002` | Error | `data/` 下存在未被 `units_manifest.yaml` 引用的孤儿 YAML |
| `R-ID-001` | Error | 全局 ID 重复（底盘 / 形态 / 武装 / 技能 / 叠加层 / 驾驶员 / 特质） |
| `R-CHASSIS-001` | Error | 每个 `form` 必须且仅属于一个 `chassis`，且双向声明一致 |
| `R-CHASSIS-002` | Error | `default_form` 必须在该底盘的 `forms` 列表中 |
| `R-CHASSIS-003` | Error / Warning | 多形态底盘必须声明换装或变形策略；单形态底盘不应声明 |
| `R-FORM-002` | Error | `transform_graph` 目标存在、同底盘，且非 `one_way` 的边必须双向闭合 |
| `R-FORM-005` | Error | 每个形态至少装备 1 件 `main` 或 `melee` 武装 |
| `R-FORM-012` | Error | 同一形态内重复的「槽位 + 武装」组合 |
| `R-WEAPON-003` | Error | `weapon_id` 必须在武装库中存在 |
| `R-WEAPON-004` | Error | 武装必须支持它被装配到的槽位（`slot_types`） |
| `R-ABILITY-006` | Error | 引用的技能必须存在 |
| `R-OVERLAY-007` | Error / Warning | 引用的叠加层与特质必须存在；叠加层要求的特质应显式声明 |
| `R-PILOT-004` | Error / Warning | 引用的驾驶员/特质必须存在；`compatible_pilots` 为空视为剧情专用（Warning） |
| `R-FACTION-008` | Error | 阵营必须在 `units_manifest.yaml` 的 `factions` 中定义 |
| `R-LOC-009` | Error / Warning | 基准语言必须覆盖全部被引用的 `loc.*` 键；其他语言缺失为 Warning |
| `R-LOC-010` | Info | 基准语言中存在未被任何数据引用的条目 |
| `R-ASSET-005` | Warning | 条目缺少 `asset_binding`（开发中条目） |
| `R-ASSET-010` | Error | M0 只允许占位资产：`asset_binding.placeholder` 必须为 `true` |
| `R-BALANCE-006` | Warning | `power_budget` 偏离标准机动 MS 基准（1000）超过 ±20% |
| `R-MILESTONE-011` | Warning | `milestone: M0` 时底盘数量应为 18 |

规则编号沿用 `docs/03-units-and-data.md` 3.4.6 的命名；新增规则请同时更新本表与
`tests/test_data_validator.py` 的反向测试。

## 构建产物

`--emit-index <path>` 会写出一份 **只读快照**（默认 `game/data_build/units_index.json`），
把底盘、形态、武装、阵营与基准语言的显示名合并成一份 JSON，供 Godot 直接读取——
GDScript 因此不需要 YAML 解析器。产物由 CI 用 `--check-index` 校验是否与源数据一致，
过期即失败。**请勿手工编辑产物。**
