# 文档审查报告

## 摘要
- P0 缺陷: 0个
- P1 缺陷: 1个

## P0 缺陷列表
（无）

## P1 缺陷列表
- DailyReportLockedEvent 在 3.1.1 与 6.1 中存在两套字段定义，字段和审计时间戳不一致（3.1.1 含 `locked_at`，6.1 仅有 `occurred_at`/`event_id`），易导致实现与 SoT 对齐时出现歧义；需统一事件结构或明确一处为规范、一处为示例。

## 建议
- 统一 DailyReportLockedEvent 的字段清单与含义，并标注与 SoT（STATE_MACHINE.md / LEDGER_SOT.md / API_SOT.md）的一致性，以免实现时产生双版本事件结构。
