# 文档审查报告
## 摘要
- P0 缺陷: 1个
- P1 缺陷: 3个

## P0 缺陷列表
- 复定义 SoT 内容：文档在 3.1.1（状态机、字段）和 4.2（端点路径、状态流转）完整罗列了状态机与 API 细节，已属于 SoT 范畴（STATE_MACHINE.md / API_SOT.md）。这是对 SoT 的重复定义且未来变更易冲突，应改为仅引用 SoT 版本而非重述具体列表。

## P1 缺陷列表
- 事件定义自相矛盾：`DailyReportLockedEvent` 在 3.1.1（Money 类型、字段名）与 6.1（字符串金额、字段集合不同）出现两套定义，字段与类型不一致，示例代码与文档说明不一致，需统一。
- 转账领域逻辑与描述不符：`Supplier.transfer_balance` 代码要求 `self.id == to_supplier.id` 才允许迁移，等同于禁止跨供应商/账户迁移；而 API `POST /api/v1/suppliers/{supplier_id}/transfer` 与描述“迁移余额”暗示跨账号/跨供应商使用场景，行为与说明不一致。
- 缺少必要的 SoT 版本声明：文中引用 `LEDGER_SOT.md v1.1`、`TrendDetectionRules` 等，但在开头 SoT 引用列表未声明这些 SoT/版本，违反“缺少必要的引用声明或版本信息”。

## 建议
- 将状态机、API 路径、字段等 SoT 范围内容改为“引用 SoT + 链接/版本”，避免在本设计文档中逐项重述。
- 统一 `DailyReportLockedEvent` 的字段与类型定义（单一权威定义），并确保示例代码与说明一致。
- 明确供应商余额迁移的业务规则：如需跨供应商/账户迁移，放宽 `transfer_balance` 校验并与 API 语义一致；如限制同供应商内迁移，需在 API 说明中声明并去除无效的自相矛盾条件。
- 在 SoT 引用声明中补充所有被引用的 SoT 文件及版本（如 `LEDGER_SOT.md v1.1`、趋势风控规则 SoT），保证可追溯。
