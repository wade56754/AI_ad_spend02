# Architecture Decision Records (ADR)

> **版本**: v1.0
> **创建日期**: 2025-12-31
> **用途**: 记录重要的架构决策及其原因

---

## ADR 格式说明

每个 ADR 遵循以下格式：
- **ID**: ADR-XXX
- **状态**: proposed | accepted | deprecated | superseded
- **日期**: 决策日期
- **上下文**: 为什么需要做这个决策
- **决策**: 我们决定做什么
- **后果**: 这个决策带来的影响

---

## ADR-001: 采用 6 角色模型

**状态**: accepted
**日期**: 2025-12-15
**来源**: MASTER.md v4.6, PRD v2.2

### 上下文
原始设计有 7 个角色（包含 supervisor），但在实际业务中发现：
- supervisor 和 project_owner 职责高度重叠
- data_operator 不在正式业务流程中
- 多角色增加了权限管理复杂度

### 决策
精简为 6 个角色：ceo, project_owner, finance, pitcher, account_manager, admin

废弃角色：
- supervisor → 合并到 project_owner
- data_operator → 不再使用
- media_buyer → 统一使用 pitcher

### 后果
- ✅ 简化权限模型
- ✅ 减少代码中的角色判断分支
- ⚠️ 需要迁移现有 supervisor 用户到 project_owner
- ⚠️ 代码中需清理废弃角色引用

---

## ADR-002: Phase 1 软性执行原则

**状态**: accepted
**日期**: 2025-12-01
**来源**: MASTER.md v4.6 §7

### 上下文
系统需要在"严格执行"和"业务灵活性"之间取得平衡。
早期阶段数据可能不完整，硬性阻断会影响业务流转。

### 决策
Phase 1 采用"照亮"策略：
- 只提示、不阻断
- 只记录、不问责
- 老板是最终裁决人

Phase 2（未来）再引入：
- 自动阻断
- 问责机制
- 强制审批

### 后果
- ✅ 业务可以继续运转
- ✅ 积累真实数据用于规则调优
- ⚠️ 暂时无法自动阻止违规操作
- ⚠️ 需要人工监控异常

---

## ADR-003: SoT 文档分层架构

**状态**: accepted
**日期**: 2025-12-10
**来源**: MASTER.md v4.7 §8

### 上下文
随着系统复杂度增加，文档之间可能产生冲突。
需要明确的优先级裁决机制。

### 决策
建立三层 SoT 架构：

**Tier 1 (宪法层)**:
- MASTER.md - 最高优先级

**Tier 2 (规范层)**:
- STATE_MACHINE.md
- DATA_SCHEMA.md
- BUSINESS_RULES.md
- API_SOT.md
- ERROR_CODES_SOT.md
- AUTH_SPEC.md

**Tier 3 (指南层)**:
- 各类 guides 和 task cards

冲突时，低层级文档让步于高层级。

### 后果
- ✅ 冲突有明确裁决规则
- ✅ 减少 AI 幻觉
- ⚠️ 需要定期同步各层文档版本

---

## ADR-004: 账本采用双账本分离设计

**状态**: accepted
**日期**: 2025-12-20
**来源**: DATA_SCHEMA.md v5.7 §3.4.4

### 上下文
原设计将项目收入和供应商成本放在同一账本，导致：
- 查询逻辑复杂
- 余额计算容易出错
- 审计追踪困难

### 决策
分离为两个独立账本：
1. **PROJECT 账本**: 记录项目收入（REVENUE, TOPUP, REVERSAL）
2. **SUPPLIER 账本**: 记录供应商成本（COST, TOPUP, TRANSFER_OUT/IN, REVERSAL）

两账本通过 topup_id 和 project_id 关联。

### 后果
- ✅ 查询逻辑简化
- ✅ 余额计算更准确
- ✅ 审计追踪清晰
- ⚠️ 需要维护两套账本表

---

## ADR-005: 前端采用 Feature-First 目录结构

**状态**: accepted
**日期**: 2025-11-01
**来源**: architecture.md

### 上下文
Next.js 默认的 pages 目录结构在业务模块多时会导致：
- 相关文件分散
- 模块边界模糊
- 难以按功能拆分

### 决策
采用 feature-first 结构：
```
src/
├── app/                 # 路由层（薄）
├── features/            # 功能模块（厚）
│   ├── auth/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── types/
│   ├── daily-reports/
│   └── ...
├── components/          # 全局共享组件
├── hooks/               # 全局共享 hooks
└── lib/                 # 工具库
```

### 后果
- ✅ 模块高内聚
- ✅ 易于按功能维护
- ✅ 支持未来微前端拆分
- ⚠️ app/ 目录需保持薄层

---

## ADR-006: 废弃 LEDGER_SOT.md

**状态**: accepted
**日期**: 2025-12-31
**来源**: MASTER.md v4.7 审计

### 上下文
MASTER.md v4.6 引用了 LEDGER_SOT.md，但该文件：
- 从未创建
- 其内容已整合到 DATA_SCHEMA.md §3.4.4

### 决策
正式废弃 LEDGER_SOT.md：
- 从裁判链中移除
- 账本规则统一参考 DATA_SCHEMA.md §3.4.4
- 更新 MASTER.md 至 v4.7

### 后果
- ✅ 消除悬空引用
- ✅ 减少文档维护负担
- ✅ 单一来源原则

---

## 待决策事项

### PENDING: 是否引入 Task Master 任务系统

**状态**: proposed
**提议日期**: 2025-12-31

**上下文**:
当前使用 TodoWrite 工具跟踪任务，但缺少：
- 任务持久化
- 跨会话任务跟踪
- 任务依赖管理

**选项**:
1. 保持现状（TodoWrite）
2. 引入 Claude Task Master
3. 自建轻量任务系统

**待讨论**

---

## 变更日志

| 日期 | ADR | 变更 |
|------|-----|------|
| 2025-12-31 | ADR-006 | 新增 |
| 2025-12-31 | 初始化 | 创建 ADR 文档 |
