# platform/switch

Nintendo Switch 平台适配层占位目录。

M0 不含任何实现，且 **不会** 在公有仓库存放任何 SDK、密钥或 devkit 相关文件。

可行性调研（公开信息、阻塞项、PC 侧约束模拟方案）见
[`docs/switch-feasibility-spike.md`](../../docs/switch-feasibility-spike.md)。

规划中的内容：

- 内存与性能预算约束（纹理运行时 ≤ ~1.5 GB，同屏机体 ≤ ~9）
- 30/60fps 画质档切换
- Joy-Con / Pro 手柄映射

无 IP 授权前提下，公有 eShop 上架属于 **非目标**；仅在自有 devkit 上做技术验证。
