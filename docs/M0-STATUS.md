# M0 里程碑状态

> **最后更新**：2026-08-25  
> 本文记录 M0 立项基线的工程与合规状态；其他交付项由后续文档子代理补全。

---

## 合规审计

**审计日期**：2026-08-25  
**审计范围**：`cursor/m0-godot-schema-8ee2` 分支全仓库（`game/`、`data/`、`tools/`、`platform/`、`docs/`、根目录配置）  
**审计方法**：全文检索拆包/提取/解密相关关键词；枚举二进制媒体与 `tools/` 脚本用途；抽查 `asset_binding` 与占位资产实现。

### 结论

**通过** — 当前 M0 仓库未发现官方资产引用、拆包路径说明或提取类工具。

### 检查项

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 拆包 / 提取路径或教程 | ✅ 未发现 | 全库无 Steam 安装目录、`steamapps`、`depot`、`.pak` 拆包步骤或逆向流程说明 |
| 官方二进制资产 | ✅ 未发现 | 无 `.png` / `.wav` / `.gltf` / `.fbx` / 字体等外部媒体；`game/assets/` 仅 README，无入库素材 |
| `game/` 资产来源 | ✅ 合规 | 占位机体由 `game/scripts/common/placeholder_mech.gd` 运行时 `BoxMesh` 拼装；`game/icon.svg` 为原创方块图标 |
| `data/` 资产绑定 | ✅ 合规 | 全部 `asset_binding.placeholder: true`；`tools/data_validator` 以规则 `R-ASSET-010` 强制 M0 仅允许占位资产 |
| `tools/` 工具性质 | ✅ 合规 | 仅含 `data_validator/`（YAML Schema 校验与 `units_index.json` 构建），无拆包/解密/提取脚本 |
| 对照录像隔离 | ✅ 已配置 | `.gitignore` 排除 `reference/` 及 `*.mp4` / `*.mkv`，防止对照母带误入版本库 |
| 文档表述 | ✅ 合规 | `docs/REMAKE-PLAN.md` 第五章、`docs/legal/NOTICE.md`、`README.md` 均声明禁止提取；无「如何拆包」技术说明 |

### 备注

- 机体型号（如 `gat-x105`）与机制标签来自公开设定与项目自建数据，**非**官方数值表或资源文件转录。
- 后续里程碑新增任何二进制资产前，须在 `docs/legal/NOTICE.md` 资产登记表登记来源与许可；官方提取物一律拒绝合入。

完整合规红线见 [`docs/REMAKE-PLAN.md`](REMAKE-PLAN.md) 第五章。
