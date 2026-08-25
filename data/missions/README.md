# data/missions

任务数据目录（M1 起启用）。

M0 不含任务数据：任务图、解锁条件 DSL 与存档 schema 属于 M1 交付
（见 `docs/REMAKE-PLAN.md` 二、战役与养成，以及附录 C 的里程碑依赖链）。

新增任务文件时需同步：

1. 在 `data/schema/` 下补 `mission.schema.json`；
2. 在 `data/units_manifest.yaml` 或新的 `missions_manifest.yaml` 中登记引用
   （校验器会把未被引用的 YAML 报为 `R-MANIFEST-002` 孤儿文件）；
3. 在 `tools/data_validator/validate.py` 中补对应的引用完整性规则与反向测试。
