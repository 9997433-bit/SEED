# data/ — 游戏内容源数据

YAML 源数据目录。运行时 **不** 直接读取此处文件；Godot 载入的是校验器生成的 `game/data_build/units_index.json`。

## 快速命令

```bash
# 在仓库根目录
make validate-data          # 校验 + 刷新构建产物
make validate-data-strict   # Warning 也视为失败
```

## 入口文件

| 文件 | 说明 |
|------|------|
| [`units_manifest.yaml`](./units_manifest.yaml) | 顶层清单：阵营、库路径、18 台底盘索引 |
| [`schema/`](./schema/) | JSON Schema（机器校验） |

## 作者文档

**请先阅读** [`docs/data-schema.md`](../docs/data-schema.md) — 字段语义、ID 规范、18 机目录、新增机体流程、R-* 校验规则对照表。

里程碑状态：[`docs/M0-STATUS.md`](../docs/M0-STATUS.md)

## 非官方声明

数值为本项目自建的相对强度设计，非官方数值转录。禁止从 Steam 或其他官方产品拆包提取数据。
