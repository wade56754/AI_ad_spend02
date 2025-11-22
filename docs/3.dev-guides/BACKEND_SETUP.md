# 后端开发环境与运行指南（Backend Setup）

> 本文为工程实践指南，所有“定义性规则”以 SoT 为准：
> - SoT-Implementation：`docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md`
> - SoT-Data：`docs/DATA_SCHEMA.md`

## 环境要求
- Python 3.11（按仓库要求）
- FastAPI + SQLAlchemy + Pydantic v2（已在项目依赖中）
- PostgreSQL（Supabase 托管）

## 启动与调试
- 本地运行 FastAPI（参考仓库脚本与 README）
- 统一通过 `/api/v1` 路由对外；响应采用 Envelope（禁止 `{detail}`）
- 鉴权通过 Supabase Auth（JWT），后端强制 RBAC + 查询范围过滤

## 约束（引用 SoT）
- 金额：Decimal，两位小数，ROUND_HALF_UP
- 时间：UTC 存储，序列化遵循统一策略
- 分页：`?page`（1-based）与 `?size`（≤100）必备





