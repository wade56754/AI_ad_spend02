# 文档审查报告
## 摘要
- P0 缺陷: 1 个
- P1 缺陷: 3 个

## P0 缺陷列表
- 在 3.1.1 状态机定义、3.1.1/4.1.3/4.2 API 端点表、DailyReport 字段明细等多处，重新列出了 SoT 已定义的状态枚举、数据字段和 API 路径（如 3.1.1 状态枚举、4.1.3/4.2 的具体路由）。根据要求，这类 SoT 内容不应在本设计文档重复定义，属于“重复定义已在 SoT 中定义的内容”。

## P1 缺陷列表
- 同名事件 `DailyReportLockedEvent` 出现两套不一致的结构定义：3.1.1 中的事件含 `revenue_amount/ cost_amount` 等字段（并声明 Money 类型），而 6.1 中重新定义为字符串字段并缺失成本公式；这会导致事件契约不一致。
- 供应商余额迁移 API 路径描述不一致：4.1.1 资源层级示例使用 `/api/v1/suppliers/{supplier_id}/transfer-requests`，而 4.2.2 示例使用 `/api/v1/suppliers/{supplier_id}/transfer`，示例与规范不一致。
- 状态机流转缺口：列出了 `trend_pending` 状态，但文档未说明 `raw_submitted → trend_pending` 的触发动作或端点，导致八态流转链路缺失，信息不完整。

## 建议
- 将状态枚举、数据字段、API 路径等 SoT 内容改为“引用 SoT、不得覆盖/重复描述”，必要时只保留跳转到 SoT 的链接或版本占位。
- 合并并唯一化 `DailyReportLockedEvent` 定义，确保字段、类型和公式一致，并标注引用的 SoT 版本。
- 统一供应商转账 API 的路径命名，选择一处作为唯一规范并在另一处更新为一致。
- 补充 `raw_submitted → trend_pending` 的触发条件与端点/动作，闭合完整八态流转。
