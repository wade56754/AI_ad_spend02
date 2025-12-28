# AI 广告代投管理系统 - 需求文档 (PRD)

> **版本**: v2.2
> **更新日期**: 2025-12-27
> **基准文档**: docs/sot/MASTER.md v4.6

---

## SoT 文档版本对齐表

> 开发前必须确认所有文档版本一致

| 文档 | 版本 | 路径 | 状态 |
|------|------|------|------|
| MASTER.md | v4.6 | docs/sot/MASTER.md | Frozen |
| STATE_MACHINE.md | v2.7 | docs/sot/STATE_MACHINE.md | Frozen |
| DATA_SCHEMA.md | v5.6 | docs/sot/DATA_SCHEMA.md | Frozen |
| BUSINESS_RULES.md | v4.7 | docs/sot/BUSINESS_RULES.md | Frozen |
| ERROR_CODES.md | v2.3 | docs/sot/ERROR_CODES_SOT.md | Frozen |
| AUTH_SPEC.md | v2.2 | docs/sot/AUTH_SPEC.md | Frozen |
| LEDGER_SOT.md | v1.2 | docs/sot/LEDGER_SOT.md | Frozen |
| API_SOT.md | v9.4 | docs/sot/API_SOT.md | Frozen |

---

## 1. 产品定位

广告投放业务的「人、账户、项目、钱」管理系统，让账目清清楚楚、有据可查。

### 核心价值
- **透明**: 每一笔钱的流向清晰可追溯
- **可控**: 预算、消耗、利润实时可见
- **高效**: 减少人工对账，提升运营效率

---

## 2. 用户角色 (6 角色)

> 来源: MASTER.md v4.6 §2.4

| 角色ID | 中文名 | 核心职责 |
|--------|--------|----------|
| `ceo` | 老板 | 资金安全、公司盈亏、最终决策 |
| `project_owner` | 项目负责人 | 项目盈亏、日报审核、确认有效粉 |
| `finance` | 财务 | 资金出入准确、数据真实、对账 |
| `pitcher` | 投手 | CPL 达标、日报准确、执行投放 |
| `account_manager` | 户管 | 账户分配、账户状态监控 |
| `admin` | 管理员 | 系统配置（不参与业务） |

**禁止使用的旧角色**:
- `supervisor` (已合并到 project_owner)
- `data_operator` (已移除)
- `media_buyer` (技术层角色，业务层用 pitcher)

---

## 3. 功能模块

### Phase 1 (MVP 核心) - 照亮阶段
> 原则：记录事实、展示状态、提示异常，**不强制阻断**

| 模块 | 功能 | 优先级 | 任务数 |
|------|------|--------|--------|
| M1 认证 | 登录/登出/Token 管理 | P0 | 5 |
| M2 用户 | 用户 CRUD、角色分配 | P0 | 5 |
| M3 项目 | 项目管理、负责人指定 | P0 | 6 |
| M5 账户 | 广告账户管理、分配 | P0 | 6 |
| M6 日报 | 日报提交 (3 状态简化版) | P0 | 4 |
| M4 渠道 | 渠道/代理商管理 | P1 | 4 |
| M7 充值 | 充值申请、确认 | P1 | 7 |
| M8 账本 | 流水记录、余额计算 | P2 | 4 |
| M10 利润 | 利润计算、统计 | P2 | 4 |
| M11 周报 | 周报生成 | P3 | 3 |

### Phase 2 (增强功能) - 自动化阶段
> 原则：引入约束、强制审批、考核关联

| 模块 | 功能 | 任务数 |
|------|------|--------|
| M6 日报 | 完整 8 状态机 | 5 |
| M9 对账 | 对账批次管理 | 4 |

---

## 4. 核心业务规则 (不变量)

1. **预收款 ≠ 收入**: 履约完成前是负债
2. **平台消耗不含手续费**: 广告费和手续费分开核算
3. **可用资金公式**: `opening_balance + Σtopup - Σad_spend`
4. **锁定后不可改**: 只能红冲 (ref_id + reason)
5. **数据域隔离**: 投手只看自己账户，项目负责人只看自己项目

---

## 5. 日报状态机

### Phase 1 (3 状态)
```
raw_submitted → trend_ok → final_confirmed
    投手提交     趋势通过     最终确认
```

### Phase 2 (8 状态)
```
raw_submitted → trend_pending → trend_ok/trend_flagged
                                      ↓
                               trend_resolved
                                      ↓
                               final_pending → final_confirmed → final_locked
```

---

## 6. 任务卡清单

详见 `docs/guides/TASK_CARDS_v2.md`

### 统计
| Phase | 任务数 | 预估工时 |
|-------|--------|----------|
| Phase 1 | 48 | 146h |
| Phase 2 | 9 | 26h |
| **总计** | **57** | **172h** |

### 开发优先级
| 优先级 | 模块 | 预估工时 |
|--------|------|----------|
| P0 | M1 认证、M2 用户、M3 项目、M5 账户、M6 日报(P1) | 85h |
| P1 | M4 渠道、M7 充值 | 32h |
| P2 | M8 账本、M9 对账、M10 利润 | 39h |
| P3 | M11 周报、M6 日报(P2) | 16h |

---

## 7. 成功指标

| 指标 | 目标 |
|------|------|
| 日报提交准时率 | > 95% |
| 对账差异率 | < 1% |
| 系统可用性 | > 99.5% |
| 用户操作响应时间 | < 500ms |

---

## 8. MVP 验收标准

```markdown
□ 能用 pitcher 账号登录
□ 能创建一个项目
□ 能创建一个广告账户并分配给 pitcher
□ pitcher 能提交日报（raw_submitted）
□ project_owner 能审核日报
□ 日报能走到 final_confirmed 状态
```

**MVP 完成时间**: 第 6 周末

---

## 9. 相关文档索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 任务卡 | docs/guides/TASK_CARDS_v2.md | 57 个任务卡详细定义 |
| 开发 SOP | docs/guides/AI_PROGRAMMING_SOP.md | AI 编程最佳实践 |
| 开发工作流 | memory-bank/dev-workflow.md | 5 步开发循环 |
| 速查表 | memory-bank/quick-reference.md | 角色/状态/错误码速查 |
| 进度记录 | memory-bank/progress.md | 实时进度跟踪 |
