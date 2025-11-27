# ARCHITECTURE.md - AI 广告代投系统架构约束

> **文档性质**: 组件约束与技术拓扑
> **约束级别**: 项目级，所有技术实现必须遵循本文档定义的架构边界
> **版本**: v1.0
> **status**: frozen
> **基准**: MASTER.md v3.4, PROJECT.md v1.2, DOMAIN.md v1.0
> **owner**: wade
> **last_reviewed**: 2025-11-27

---

## 第一章 文档定位与约束

### 1.1 本文档职责

ARCHITECTURE.md 定义系统技术架构约束：

- 组件边界与职责划分
- 技术栈约束
- 分层架构规则
- 通信与集成约束
- 非功能性约束

> 引用: MASTER.md 第九章 文档索引

### 1.2 本文档不做

本文档不承担以下职责：

- 不定义业务规则（属于 BUSINESS_RULES.md）
- 不定义数据结构细节（属于 DATA_SCHEMA.md）
- 不定义 API 接口规范（属于 API_SOT.md）
- 不定义部署流程（属于 DEPLOYMENT.md）
- 不定义测试策略（属于 TESTING.md）

### 1.3 约束强制级别

| 级别 | 说明 | 违反后果 |
|-----|------|---------|
| MUST | 强制要求 | PR 拒绝 |
| SHOULD | 推荐要求 | 需说明理由 |
| MAY | 可选建议 | 自由选择 |

---

## 第二章 系统分层架构

### 2.1 分层结构

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │
│         (Frontend / API Gateway)        │
├─────────────────────────────────────────┤
│           Application Layer             │
│         (API Routes / Services)         │
├─────────────────────────────────────────┤
│             Domain Layer                │
│      (Business Logic / State Machine)   │
├─────────────────────────────────────────┤
│          Infrastructure Layer           │
│    (Database / External Services)       │
└─────────────────────────────────────────┘
```

### 2.2 层间依赖约束

| 约束 | 级别 | 说明 |
|-----|------|------|
| 上层可依赖下层 | MUST | Presentation → Application → Domain → Infrastructure |
| 禁止下层依赖上层 | MUST | Infrastructure 不可依赖 Domain |
| 禁止跨层依赖 | MUST | Presentation 不可直接依赖 Infrastructure |
| Domain 层无外部依赖 | MUST | 业务逻辑不依赖框架/数据库 |

### 2.3 层职责定义

| 层 | 职责 | 禁止 |
|---|------|------|
| Presentation | 请求解析、响应格式化、认证 | 业务逻辑、数据库访问 |
| Application | 用例编排、事务管理、权限校验 | 直接 SQL、UI 逻辑 |
| Domain | 业务规则、状态机、领域事件 | HTTP、数据库、框架依赖 |
| Infrastructure | 数据持久化、外部 API、缓存 | 业务规则、状态判断 |

> 引用: docs/3.dev-guides/DDD_API_ARCHITECTURE.md

---

## 第三章 组件边界与职责

### 3.1 后端组件

| 组件 | 职责 | 所属层 |
|-----|------|-------|
| API Router | 路由分发、请求验证 | Application |
| Auth Service | 认证、授权、会话管理 | Application |
| Daily Report Service | 日报业务逻辑 | Domain |
| Ledger Service | 账本业务逻辑 | Domain |
| State Machine | 状态流转控制 | Domain |
| Repository | 数据持久化 | Infrastructure |
| RLS Policies | 行级安全策略 | Infrastructure |

### 3.2 前端组件

| 组件 | 职责 | 所属层 |
|-----|------|-------|
| Pages | 页面路由与布局 | Presentation |
| Components | 可复用 UI 组件 | Presentation |
| Hooks | 状态管理与副作用 | Application |
| API Client | 后端通信 | Infrastructure |

### 3.3 组件依赖约束

| 约束 | 级别 |
|-----|------|
| Service 之间禁止循环依赖 | MUST |
| Repository 只被 Service 调用 | MUST |
| 状态机逻辑集中在 Domain 层 | MUST |
| 账本操作必须经过 Ledger Service | MUST |

> 引用: DOMAIN.md 第六章 跨域依赖约束

---

## 第四章 技术栈约束

### 4.1 后端技术栈

| 技术 | 版本约束 | 级别 | 用途 |
|-----|---------|------|------|
| Python | >= 3.11 | MUST | 运行时 |
| FastAPI | >= 0.100 | MUST | Web 框架 |
| SQLAlchemy | >= 2.0 | MUST | ORM |
| Alembic | >= 1.12 | MUST | 数据库迁移 |
| Pydantic | >= 2.0 | MUST | 数据验证 |
| Supabase | - | MUST | 数据库 + Auth |

### 4.2 前端技术栈

| 技术 | 版本约束 | 级别 | 用途 |
|-----|---------|------|------|
| TypeScript | >= 5.0 | MUST | 语言 |
| Next.js | >= 14 | MUST | 框架 |
| React | >= 18 | MUST | UI 库 |
| Zod | >= 3.0 | MUST | Schema 验证 |
| TailwindCSS | >= 3.0 | SHOULD | 样式 |

### 4.3 代码约束

| 约束 | 级别 | 说明 |
|-----|------|------|
| TypeScript strict mode | MUST | tsconfig.json 设置 strict: true |
| 禁止 any 类型 | MUST | 所有变量必须有明确类型 |
| Result 模式错误处理 | MUST | 业务逻辑禁止 throw Error |
| 金额使用 Decimal | MUST | 禁止 Float/Double |
| 时间使用 UTC | MUST | 数据库存 TIMESTAMPTZ |

> 引用: MASTER.md 第七章 代码约束

---

## 第五章 通信与集成约束

### 5.1 前后端通信

| 约束 | 级别 | 说明 |
|-----|------|------|
| RESTful API | MUST | 遵循 API_SOT.md 定义 |
| JSON 响应格式 | MUST | 统一响应结构 |
| 错误码规范 | MUST | 使用 ERROR_CODES_SOT.md 定义的错误码 |
| JWT 认证 | MUST | Bearer Token 方式 |

### 5.2 数据库通信

| 约束 | 级别 | 说明 |
|-----|------|------|
| 连接池 | MUST | 使用 SQLAlchemy 连接池 |
| 事务边界 | MUST | Service 层控制事务 |
| RLS 策略 | MUST | 所有表启用行级安全 |
| 迁移管理 | MUST | 使用 Alembic 管理 |

### 5.3 外部服务集成

| 服务 | 用途 | 约束 |
|-----|------|------|
| Supabase Auth | 用户认证 | MUST 使用官方 SDK |
| Supabase Storage | 文件存储 | SHOULD 用于报表导出 |

### 5.4 禁止的集成方式

| 禁止方式 | 级别 | 原因 |
|---------|------|------|
| 直接 SQL 查询绕过 ORM | MUST | 绕过 RLS 策略 |
| 跨服务直接数据库访问 | MUST | 破坏服务边界 |
| 外部数据直接写入账本 | MUST | 违反 BI-04 |

> 引用: MASTER.md D-02「跳过日报直入账本」

---

## 第六章 非功能性约束

### 6.1 可靠性约束

| 约束 | 级别 | 目标值 |
|-----|------|-------|
| 账务数据完整性 | MUST | 100% |
| 审计链可追溯性 | MUST | 100% |
| 终态数据篡改事件 | MUST | 0 |

> 引用: PROJECT.md 第九章 合规红线

### 6.2 安全性约束

| 约束 | 级别 | 说明 |
|-----|------|------|
| 认证必须 | MUST | 所有 API 需认证（除登录） |
| 授权校验 | MUST | 基于角色的访问控制 |
| RLS 启用 | MUST | 数据库行级安全 |
| 敏感数据加密 | MUST | 密码/Token 不明文存储 |

### 6.3 可维护性约束

| 约束 | 级别 | 说明 |
|-----|------|------|
| 测试覆盖率 | MUST | >= 80% |
| 代码审查 | MUST | PR 必须审查 |
| 文档同步 | MUST | 代码变更需更新相关 SoT |
| 日志记录 | MUST | 关键操作必须记录审计日志 |

### 6.4 性能约束

| 约束 | 级别 | 目标值 |
|-----|------|-------|
| API 响应时间 | SHOULD | P95 < 500ms |
| 页面加载时间 | SHOULD | < 3s |
| 数据库查询 | SHOULD | 避免 N+1 查询 |

> 引用: MASTER.md 第一章 1.2 核心风险

---

## 第七章 架构决策记录 (ADR)

本章记录关键架构决策，采用 ADR (Architecture Decision Record) 格式。

### 7.1 ADR 格式说明

每条 ADR 包含：
- **编号**: ADR-XXX
- **状态**: Proposed / Accepted / Deprecated / Superseded
- **上下文**: 决策背景
- **决策**: 具体选择
- **后果**: 影响与约束

### 7.2 已接受的架构决策

#### ADR-001 采用双账本架构

- **状态**: Accepted
- **上下文**: 需同时追踪收入（项目维度）与成本（供应商维度）
- **决策**: 采用 PROJECT 账本 + SUPPLIER 账本的双账本设计
- **后果**:
  - 收入与成本可独立核算
  - 需维护两份账本一致性
  - 红冲操作需同时处理双方

> 引用: MASTER.md INV-001, LEDGER_SOT.md §2

#### ADR-002 采用 8 状态机控制日报流程

- **状态**: Accepted
- **上下文**: 日报数据需经过多阶段审核与确认
- **决策**: 采用 8 状态单向流转：raw_submitted → trend_pending → trend_ok/flagged → trend_resolved → final_pending → final_confirmed → final_locked
- **后果**:
  - 状态不可回退（终态保护）
  - 每次状态变更需记录审计日志
  - 错误修正只能通过红冲

> 引用: STATE_MACHINE.md §8

#### ADR-003 采用 Supabase RLS 实现行级安全

- **状态**: Accepted
- **上下文**: 需实现基于角色的数据隔离
- **决策**: 使用 Supabase Row Level Security 策略
- **后果**:
  - 数据库层强制访问控制
  - 所有表必须启用 RLS
  - 需维护 RLS_POLICIES_SOT.md

> 引用: AUTH_SPEC.md §4, RLS_POLICIES_SOT.md

#### ADR-004 账务只追加不修改

- **状态**: Accepted
- **上下文**: 账务数据需满足审计要求
- **决策**: ledger_entries 表只允许 INSERT，禁止 UPDATE/DELETE
- **后果**:
  - 完整审计追溯能力
  - 错误修正通过 REVERSAL 实现
  - 存储成本增加（可接受）

> 引用: MASTER.md INV-001「账务只追加，不修改」

#### ADR-005 禁止跨层依赖

- **状态**: Accepted
- **上下文**: 保持系统可维护性与测试性
- **决策**: 严格遵循四层架构，禁止跨层调用
- **后果**:
  - Presentation 不可直接访问 Infrastructure
  - Domain 层保持框架无关
  - 可能增加代码量（可接受）

> 引用: 本文档第二章 §2.2

### 7.3 待决策项

| 编号 | 主题 | 状态 | 备注 |
|-----|------|------|------|
| ADR-006 | 缓存策略选型 | Proposed | 待评估 Redis vs 本地缓存 |
| ADR-007 | 报表导出方案 | Proposed | 待评估同步 vs 异步 |

### 7.4 ADR 变更流程

1. 提出新 ADR → 状态设为 Proposed
2. 团队评审通过 → 状态改为 Accepted
3. 被新决策替代 → 状态改为 Superseded，引用新 ADR
4. 不再适用 → 状态改为 Deprecated

> 注: ADR 变更需经过 RFC 流程审批

---

## 附录 A: 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-11-25 | 初始版本 | AI Doc Orchestrator |

---

**文档版本**: v1.0
**最后更新**: 2025-11-25
**对齐文档**: MASTER.md v3.4, PROJECT.md v1.2, DOMAIN.md v1.0
**维护者**: 系统架构师
