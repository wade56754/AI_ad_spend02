---
version: v0.1
status: planned
layer: sot
last_reviewed: 2025-11-27
owner: wade
---

# RLS Policies (Row Level Security)

> **⚠️ 注意**: 当前版本项目未启用 RLS，本文档为规划性文档。

## 1. Purpose

定义 PostgreSQL Row Level Security 策略（规划中）。

## 2. Scope

本文档覆盖：
- TODO: RLS 策略定义
- TODO: 用户数据隔离规则
- TODO: 项目数据访问控制
- TODO: 角色权限映射

## 3. Current Status

**当前实现**: Service 层 RBAC（通过 `@require_role` 装饰器）
**RLS 状态**: ❌ 未启用（`ENABLE_RLS=false`）
**启用条件**: 用户量超过 1000 时重新评估

## 4. Structure

### 4.1 RLS 策略概览
- TODO

### 4.2 Users 表策略
- TODO

### 4.3 Projects 表策略
- TODO

### 4.4 Daily Reports 表策略
- TODO

### 4.5 Topup Requests 表策略
- TODO

## 5. Relation to SoT

本文档引用以下 SoT 文档：
- TODO: `docs/2.sot/AUTH_SPEC.md` - 认证授权规范
- TODO: `docs/2.sot/DATA_SCHEMA.md` - 表结构定义
- TODO: `docs/2.sot/BUSINESS_RULES.md` - 业务规则

## 6. Migration Path

TODO: RLS 启用迁移路径
