# P2 Global Audit (2025-11)

## 文档说明
- 本文档为 2025-11 的一次全局体检结果，供整改参考。
- 单一事实来源（SoT）仍以 `docs/core/*` 文档为准。
- 本文档仅为问题目录与改造路线图，不作为 SoT 或实现规范。

## Global Analysis
- 代码/文档存在重复与遗留：`backend/init.sql`、`backend/simple_backend.py`、`backend/models/*_fixed.py`、`backend/services/reconciliation_service_optimized.py` 未标弃用；RLS 文档两套（`docs/core/RLS_POLICIES.md` 与 `docs/security/RLS_POLICIES.md`）。
- Alembic 版本有成对重复（如 `20251117_reconciliation_status_align` 系列），迁移顺序存在漂移风险。
- ERROR_CODES 与 RLS 文档各有双份（`docs/core/ERROR_CODES.md` vs `docs/ERROR_CODES.md`，`docs/core/RLS_POLICIES.md` vs `docs/security/RLS_POLICIES.md`）。
- 响应封装重复且不符 SoT：`backend/core/response.py` 与 `backend/utils/response.py` 并存，code=“OK” 非 “SUCCESS”，timestamp 无 UTC/Z，request_id 未透传。
- RLS 迁移脚本启用了 RLS，与 SoT（当前未启用）冲突。

## Spec Consistency Report
- AUTH：`backend/deps/supabase_auth.py`未见；`dependencies.py` 允许构造最小化 User，违背 Supabase Auth + users 查询角色的要求。
- ERROR_CODES：枚举与 `docs/core/ERROR_CODES.md` 基本一致，但响应未强制使用；存在文档重复。
- RLS_POLICIES：SoT 声明未启用，迁移与 mixin 表明已 enable。
- API Envelope：code=OK、timestamp naive、request_id 自生成未贯穿，不符合 SoT 统一 Envelope。
- Pydantic v2：Schemas 普遍缺少 `ConfigDict(from_attributes=True)` 等 v2 强制项。
- 业务/状态机：遗留角色 `data_clerk/manager` 仍在文件/迁移中，违背唯一五角色；状态枚举覆盖需复核。
- 数据 Schema：`backend/init.sql` 与 DATA_SCHEMA 差异巨大；重复 Alembic 版本可能与 SoT 不一致。
- request_id：无全局 middleware 注入/透传。

## Critical Issues
- 🔴 RLS 状态冲突：迁移已启用 RLS，与 SoT 未启用不一致。
- 🔴 认证兜底：无 DB 用户时构造默认 media_buyer 用户，绕过 Supabase Auth + users 校验。
- 🔴 Envelope 不符 SoT：code/时间戳/request_id 处理不符合统一规范。
- 🔴 `init.sql` 与 DATA_SCHEMA 不一致且仍在仓库中，易被误用。
- 🔴 角色/命名漂移：遗留 data_clerk/manager/旧文件名与 SoT 五角色冲突。
- 🔴 Alembic 重复版本导致迁移顺序/结构漂移风险。

## Medium Issues
- 🟡 Pydantic v2 规范未落实（缺 ConfigDict、Decimal 约束等）。
- 🟡 状态机校验覆盖不明，Service 多版本重复。
- 🟡 request_id 未贯穿日志/响应；ERROR_CODES 文档多份需收敛。
- 🟡 RLS/ERROR_CODES 文档重复需合并；权限矩阵硬编码未对齐 SoT。

## Low Issues
- 🟢 Timestamp 未加 UTC/Z；Envelope code 使用 OK；权限表硬编码未核对；重复响应封装未清。
- 🟢 迁移/计划文档大量 P2.x/P3 未注明 SoT 状态。

## Task List
- 【统一 RLS 策略】决定启/停，修迁移或更新 SoT；风险🔴，阶段P2，~1-2d。
- 【删除认证兜底】强制 Supabase Auth + users 查询，无记录即报错；风险🔴，P2，~0.5d。
- 【修复 Envelope】code=SUCCESS，timestamp UTC tz-aware，request_id 透传；风险🔴，P2，~1d。
- 【清理重复迁移】合并/删除重复 Alembic，校验与 DATA_SCHEMA 一致；风险🔴，P2，~1-2d。
- 【Schema 对齐】下线/标记 `backend/init.sql`，核对模型与 DATA_SCHEMA；风险🔴，P2，~1d。
- 【角色/命名清理】移除 data_clerk/manager 等旧值，集中五角色常量；风险🟡，P3，~0.5d。
- 【Pydantic v2 落实】Schemas 配置 ConfigDict/Decimal 校验；风险🟡，P3，总计~1d。
- 【Service 去重】合并 reconciliation/topup/daily_report 多版本，删除 *_optimized/_fixed；风险🟡，P3，~1-2d。
- 【Docs 收敛】保留 docs/core 为 SoT，其余标记 archive；风险🟢，P4，~0.5d。
- 【权限矩阵校验】ROLE_PERMISSIONS 对齐 SoT，补测试；风险🟡，P3，~0.5d。

## Recommended Order
1) 统一 RLS 策略
2) 移除认证兜底，修 Envelope/request_id
3) 清理重复迁移，Schema 校验
4) 角色/命名清理 + Pydantic v2 落实
5) Service 去重
6) 权限矩阵/测试补齐
7) 文档收敛与归档标记

## Summary
- 存在多处与 SoT 冲突（RLS、Auth 兜底、Envelope、迁移重复、旧 schema 文件），需按顺序修复后再继续迭代。
