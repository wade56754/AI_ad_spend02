# AI 广告代投管理系统 - 开发历史记录

> **版本**: v1.0
> **创建日期**: 2026-01-02
> **用途**: 记录架构决策、Bug 修复、学习经验
> **合并来源**: decisions.md, bugs.md, learned.md, change_log.md

---

## 1. 架构决策记录 (ADR)

### ADR-001: 6 角色模型
**日期**: 2025-12
**状态**: ✅ 已实施

**决策**: 采用 6 角色模型，废弃 supervisor 角色，其职责合并到 project_owner。

| 角色 | 中文名 | 职责 |
|------|--------|------|
| ceo | 老板 | 资金安全、公司盈亏 |
| project_owner | 项目负责人 | 项目盈亏、日报审核 |
| finance | 财务 | 资金出入准确 |
| pitcher | 投手 | CPL 达标、日报准确 |
| account_manager | 户管 | 账户分配 |
| admin | 管理员 | 系统配置 |

**废弃角色**: supervisor → project_owner, data_operator → 移除, media_buyer → pitcher

---

### ADR-002: Phase 1 软性约束
**日期**: 2025-12
**状态**: ✅ 已实施

**决策**: Phase 1 采用"只提示、不阻断、不问责"原则。

**允许**: 记录事实、展示状态、提示异常、高亮警告
**禁止**: 自动阻断提交、自动冻结账户、自动扣分惩罚、强制审批流程

---

### ADR-003: 日报三状态机
**日期**: 2025-12
**状态**: ✅ 已实施

**决策**: Phase 1 使用简化的 3 状态机:
```
raw_submitted → trend_ok → final_confirmed
```

Phase 2 保留完整 8 状态机。

---

### ADR-004: Letta 集成方案
**日期**: 2026-01-01
**状态**: ✅ 已决策

**决策**: 采用 Memory Bank 自动化方案，复用现有 memory-bank 结构。

---

## 2. Bug 修复历史

### [2025-12-31] Phase 1 状态机错误
- **问题**: 在 Phase 1 状态机中使用了废弃的状态 (trend_pending, trend_flagged)
- **原因**: 开发过程中未能及时更新状态机定义
- **修复**: 更新状态机逻辑，确保只使用 raw_submitted, trend_ok, final_confirmed
- **影响文件**: state_machine.md, progress.md

---

## 3. 学习记录

### 编码技能
- **前端规范**: Next.js 16 必须使用 'use client'、apiGet/apiPost、DataTable 组件，禁止直接 fetch/axios
- **后端规范**: FastAPI 必须使用 SQLAlchemy 2.x、Pydantic v2、Supabase Auth + JWT
- **状态转换**: Phase 1 状态流转: raw_submitted → trend_ok → final_confirmed

### 角色定义更新
- 更新了项目中的角色定义为 6 角色模型
- 废弃了 supervisor、data_operator、media_buyer

### 实施计划版本对齐
- 确保所有开发阶段的 SoT 文档版本一致性

---

## 4. 变更日志

> 重要代码变更记录

| 日期 | 类型 | 描述 |
|------|------|------|
| 2026-01-02 | REFACTOR | Memory Bank 文档整合优化 |
| 2026-01-02 | DOCS | 统一 SoT 版本引用 |
| 2025-12-31 | BUG_FIX | Phase 1 状态机错误修复 |

---

## 更新说明

此文件由以下文件合并而成:
- `decisions.md` - 架构决策记录
- `bugs.md` - Bug 修复历史
- `learned.md` - AI 助手学习记录
- `change_log.md` - 代码变更日志

如需记录新内容，请直接在对应章节添加。
