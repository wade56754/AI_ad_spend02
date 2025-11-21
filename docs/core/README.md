# AI广告代投系统·核心文档目录 (Core Documentation)

> **最后更新**: 2025-01-21
> **维护团队**: 系统架构团队

---

## 📋 文档结构说明

### 🎯 核心规范文档 (SoT - Single Source of Truth)

这些文档是系统开发的最高权威指导,所有实现必须严格遵循:

| 文档 | 版本 | 说明 | 优先级 |
|-----|------|------|--------|
| [AI_AD_SYSTEM_MASTER_SPEC_v2.2.md](AI_AD_SYSTEM_MASTER_SPEC_v2.2.md) | **v2.2** | **核心开发手册** (最新版,已对齐BRD v3.1) | ⭐⭐⭐ |
| [DATA_SCHEMA.md](DATA_SCHEMA.md) | v5.0+ | 数据结构唯一真相源 | ⭐⭐⭐ |
| [STATE_MACHINE.md](STATE_MACHINE.md) | v2.5+ | 状态机唯一真相源 | ⭐⭐⭐ |
| [ERROR_CODES.md](ERROR_CODES.md) | - | 错误码SoT | ⭐⭐⭐ |
| [AUTH_SPEC.md](AUTH_SPEC.md) | - | 认证授权规范 | ⭐⭐⭐ |
| [BUSINESS_RULES.md](BUSINESS_RULES.md) | - | 业务规则SoT | ⭐⭐⭐ |

### 📐 开发规范文档

| 文档 | 说明 |
|-----|------|
| [API_DEVELOPMENT_FLOW.md](API_DEVELOPMENT_FLOW.md) | API开发流程 |
| [FRONTEND_SPEC_v2.md](FRONTEND_SPEC_v2.md) | 前端规范v2 |
| [RLS_POLICIES.md](RLS_POLICIES.md) | RLS策略参考 (当前未启用) |

### 📊 业务需求文档

| 文档 | 版本 | 说明 |
|-----|------|------|
| [BRD_chapter1_v3.1.md](BRD_chapter1_v3.1.md) | **v3.1** | **业务流程总览** (最新基线,2025-01-21) |

### 📖 参考文档

| 文档 | 说明 |
|-----|------|
| [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) | 系统概览 |
| [SQL_SCRIPTS_REVIEW.md](SQL_SCRIPTS_REVIEW.md) | SQL脚本审查 |

---

## 📁 子目录说明

### 📦 archive/ (归档文档)

已废弃的历史版本文档,仅供参考,**不得作为开发依据**:

- `AI_AD_SYSTEM_MASTER_SPEC_v2.0.md` - Master Spec v2.0 (2025-11-20)
- `AI_AD_SYSTEM_MASTER_SPEC_v2.1.md` - Master Spec v2.1 (2025-01-20)
- `MASTER_DESIGN_DOCUMENT_v1.0.md` - 旧版设计文档
- `AI_AD_SYSTEM_MAIN_DOCUMENT_v3.x.md` - 旧版主文档
- `BRD_chapter1_v3.0.md` - BRD v3.0 (已被v3.1替代)

### 📁 planning/ (规划文档)

项目规划、执行计划等过渡性文档:

- `MASTER_SPEC_v2.2_EXECUTION_PLAN.md` - v2.2执行计划
- `MASTER_SPEC_v2.2_BRD_ALIGNMENT_SUMMARY.md` - BRD v3.1对齐摘要

---

## 🎯 快速导航

### 新手开发者必读:
1. [AI_AD_SYSTEM_MASTER_SPEC_v2.2.md](AI_AD_SYSTEM_MASTER_SPEC_v2.2.md) - 从第1-6章开始
2. [BRD_chapter1_v3.1.md](BRD_chapter1_v3.1.md) - 理解业务逻辑
3. [DATA_SCHEMA.md](DATA_SCHEMA.md) - 数据库设计
4. [STATE_MACHINE.md](STATE_MACHINE.md) - 状态流转规则

### 开发任务:
1. 查阅 [AI_AD_SYSTEM_MASTER_SPEC_v2.2.md](AI_AD_SYSTEM_MASTER_SPEC_v2.2.md) 对应章节
2. 查阅相关SoT文档 (DATA_SCHEMA/STATE_MACHINE/ERROR_CODES)
3. 遵循 [API_DEVELOPMENT_FLOW.md](API_DEVELOPMENT_FLOW.md) 开发流程

### Code Review:
使用 [AI_AD_SYSTEM_MASTER_SPEC_v2.2.md](AI_AD_SYSTEM_MASTER_SPEC_v2.2.md) 第6.3节的检查清单

---

## ⚖️ 冲突仲裁规则

当文档之间出现冲突时,按以下优先级仲裁:

| 领域 | 最高权威 |
|-----|---------|
| **数据结构** | DATA_SCHEMA.md |
| **状态流转** | STATE_MACHINE.md |
| **认证授权** | AUTH_SPEC.md |
| **错误处理** | ERROR_CODES.md |
| **业务约束** | BUSINESS_RULES.md |
| **技术栈/架构** | AI_AD_SYSTEM_MASTER_SPEC_v2.2.md |

---

## 📅 文档版本历史

| 日期 | 版本 | 主要变更 |
|------|------|---------|
| 2025-01-21 | v2.2 | BRD v3.1对齐更新:粉数确认状态机、Ledger双账本、趋势风控 |
| 2025-01-20 | v2.1 | 结构化优化与内容增强 |
| 2025-11-20 | v2.0 | 合并两份Master Design Document |
| 2025-11-20 | v1.0 | 初始版本 |

---

**文档状态**: ✅ 已完成整理 (2025-01-21)
