# 数据库真相来源 (SoT-Data)

📌 所有表结构、字段、关系必须参考：
docs/core/DATA_SCHEMA.md

⚠️ 禁止：
- 在模型或 API 中自创字段（如 comment_count, owner_name 等）
- 假设不存在于 DATA_SCHEMA 的列或关系
- 未先更新 DATA_SCHEMA 的情况下直接写 migration

📌 需要 Schema 变更 → 必须先提交 DATA_SCHEMA 更新与 PR
