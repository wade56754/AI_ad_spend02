# 系统约束 (System Constraints)

## SoT 裁判链 (动态版本)

按优先级从高到低:

1. MASTER.md ${MASTER_VERSION} - 架构宪法
2. STATE_MACHINE.md ${STATE_MACHINE_VERSION} - 状态机定义
3. DATA_SCHEMA.md ${DATA_SCHEMA_VERSION} - 数据模型
4. BUSINESS_RULES.md ${BUSINESS_RULES_VERSION} - 业务规则
5. API_SOT.md ${API_SOT_VERSION} - API 契约
6. ERROR_CODES.md ${ERROR_CODES_VERSION} - 错误码注册表
7. AUTH_SPEC.md ${AUTH_SPEC_VERSION} - 认证授权

**规则**: 高层文档覆盖低层文档。遇到冲突时，先查 MASTER.md。

## Phase 1 约束

系统处于 Phase 1（照亮阶段）:

- 系统照亮而非问责
- 状态问题仅警告，不阻断
- 禁止自动惩罚逻辑
- 投手 KPI 仅用于观察与沟通，不用于问责与考核

**允许**: 记录、提示、高亮、统计
**禁止**: 阻断、拒绝、暂停、冻结、自动批准/拒绝

## 技术栈约束

| 层 | 技术 |
|---|------|
| 后端 | FastAPI + SQLAlchemy 2.x + Pydantic v2 |
| 前端 | Next.js 16 + TanStack Query v5 + shadcn/ui |
| 认证 | Supabase Auth |
| 数据库 | PostgreSQL (via Supabase) |

