# 数据要点 · Projects

> 数据库表结构、字段与约束的“唯一事实来源”见：`docs/DATA_SCHEMA.md`。
> 本文仅记录与该模块开发时的注意点与交叉引用，不重复定义结构。

## 索引与主键（引用 SoT-Data）
- 请在开发时直接查阅 `DATA_SCHEMA.md` 对 projects 相关表的主键、唯一约束与索引

## 序列化规则（引用 SoT-Implementation）
- 金额：Decimal 两位小数、ROUND_HALF_UP
- 时间：UTC 存储；序列化遵循统一时间策略





