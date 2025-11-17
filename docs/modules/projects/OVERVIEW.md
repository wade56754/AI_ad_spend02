# 模块概览 · Projects

> 本文为项目管理模块的业务与使用概览，所有实现性定义以 SoT 为准：
> - 实现/开发规范（SoT-Implementation）：`docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md`
> - 数据库结构（SoT-Data）：`docs/DATA_SCHEMA.md`

## 角色与数据边界（引用 SoT）
- 采用五角色：admin, finance, data_operator, account_manager, media_buyer
- 授权在服务层（BFF/FastAPI）通过 RBAC + 查询范围过滤落地；数据库 RLS 为未来方案，当前未启用

## 相关链接
- 状态机与流程：参考 `docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md`
- 数据表与字段：参考 `docs/DATA_SCHEMA.md` 中与 projects 相关的表





