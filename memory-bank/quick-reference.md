# 速查参考表

> **版本**: v1.3
> **更新日期**: 2026-01-02
> **用途**: 开发时快速查阅，避免 AI 幻觉
> **变更记录**: 统一 SoT 版本引用至最新版本

---

## 1. SoT 文档版本对齐表

> 每次开发前必须确认版本一致 (更新于 2026-01-02)

| 文档 | 版本 | 路径 | 用途 |
|------|------|------|------|
| MASTER.md | v4.9 | docs/sot/MASTER.md | 架构宪法、角色定义 |
| DATA_SCHEMA.md | v5.10 | docs/sot/DATA_SCHEMA.md | 数据库表结构 |
| STATE_MACHINE.md | v2.9 | docs/sot/STATE_MACHINE.md | 状态机定义 |
| BUSINESS_RULES.md | v5.1 | docs/sot/BUSINESS_RULES.md | 业务规则 |
| API_SOT.md | v9.7 | docs/sot/API_SOT.md | API 规范 |
| AUTH_SPEC.md | v2.2 | docs/sot/AUTH_SPEC.md | 认证授权 |
| ERROR_CODES_SOT.md | v2.2 | docs/sot/ERROR_CODES_SOT.md | 错误码定义 |

---

## 2. 合法角色（6 角色）

> **来源**: MASTER.md v4.9 §2.4（宪法）
> **PRD v5.1 变更**: 移除 supervisor 角色，其职责合并到 project_owner

| 角色ID | 中文名 | 职责范围 | 系统权限 |
|--------|--------|----------|----------|
| `ceo` | 老板 | 资金安全、公司盈亏、最终决策 | 全部可见，批准充值，锁定结算 |
| `project_owner` | 项目负责人 | 项目盈亏、资金使用效率、日报审核 | 申请充值，审核日报，调配投手 |
| `finance` | 财务 | 资金出入准确、数据真实、对账 | 审核充值，更新资金表，锁定结算 |
| `pitcher` | 投手 | CPL 达标、日报准确、执行投放 | 填报日报，查看自己数据 |
| `account_manager` | 户管 | 账户分配、账户状态监控 | 管理账户分配，收集充值需求 |
| `admin` | 管理员 | 系统配置（不参与业务） | 系统设置 |

### 废弃角色（禁止使用）

| 角色 | 状态 | 替代方案 |
|------|------|---------|
| `supervisor` | ❌ 已废弃 (PRD v5.1) | 合并到 project_owner |
| `data_operator` | ❌ 不在宪法中 | 移除 |
| `media_buyer` | ❌ 非标准术语 | 使用 pitcher |

> ⚠️ 代码中如存在非标准角色，应修正为宪法定义

---

## 3. 日报状态机

### Phase 1 (简化版 - 3 状态)
```
raw_submitted → trend_ok → final_confirmed
```

### Phase 2 (完整版 - 8 状态)
```
raw_submitted → trend_pending → trend_ok/trend_flagged
                                      ↓
                               trend_resolved
                                      ↓
                               final_pending → final_confirmed → final_locked
```

---

## 4. 错误码速查表

> 来源: ERROR_CODES_SOT.md v2.2

| 错误码 | HTTP | 含义 | 使用场景 |
|--------|------|------|----------|
| AUTH_400 | 400 | 认证失败 | 用户名或密码错误 |
| AUTH_401 | 401 | 未认证 | Token 缺失或过期 |
| AUTH_403 | 403 | 无权限 | 角色不允许此操作 |
| STATE_400 | 400 | 状态转换非法 | 不符合状态机定义 |
| STATE_402 | 400 | 终态非法回退 | 尝试修改已确认数据 |
| BIZ_001 | 400 | 无效的操作 | 违反业务规则 |
| BIZ_002 | 404 | 资源不存在 | 根据 ID 查询未找到 |
| BIZ_100 | 400 | 金额非法 | 金额 ≤ 0 |
| BIZ_101 | 400 | 余额不足 | 转账/消耗超出余额 |
| BIZ_402 | 400 | 红冲缺少原因 | 红冲操作未提供 reason |
| VAL_001 | 400 | 参数校验失败 | 必填字段缺失 |
| PERM-001 | 403 | 权限不足 | 无权执行此操作 |
| RES-001 | 404 | 资源未找到 | 查询无结果 |

---

## 5. 权限矩阵

> 来源: MASTER.md v4.9 §2.4

| 操作 | ceo | project_owner | finance | pitcher | account_manager | admin |
|------|-----|---------------|---------|---------|-----------------|-------|
| 创建用户 | ✓ | - | - | - | - | ✓ |
| 创建项目 | ✓ | - | - | - | - | ✓ |
| 管理项目成员 | ✓ | ✓ | - | - | - | ✓ |
| 创建渠道 | - | - | - | - | ✓ | ✓ |
| 审批渠道 | - | ✓ | - | - | - | ✓ |
| 创建账户 | - | - | - | - | ✓ | ✓ |
| 分配账户 | - | - | - | - | ✓ | ✓ |
| 提交日报 | - | - | - | ✓ | - | - |
| 审核日报 | - | ✓ | - | - | - | ✓ |
| 创建充值 | - | - | - | ✓ | ✓ | - |
| 审批充值 | - | - | ✓ | - | - | ✓ |
| 查看利润 | ✓ | - | ✓ | - | - | ✓ |
| 红冲操作 | - | - | - | - | - | ✓ |

---

## 6. 模块依赖图

```
M1 认证 ──► M2 用户 ──► M3 项目 ──► M4 渠道
                │              │           │
                │              │           ▼
                │              └──────► M5 账户
                │                          │
                │                          ▼
                │                      M6 日报
                │                          │
                └──────────► M7 充值 ◄─────┘
                                 │
                                 ▼
                             M8 账本
                              │   │
                              ▼   ▼
                        M9 对账   M10 利润
```

**关键路径**: M1 → M2 → M3 → M5 → M6 → M8 → M10

---

## 7. 任务卡编号规则

| 模块 | 前缀 | 示例 |
|------|------|------|
| M1 认证 | TASK-AUTH | TASK-AUTH-001 |
| M2 用户 | TASK-USER | TASK-USER-001 |
| M3 项目 | TASK-PROJ | TASK-PROJ-001 |
| M4 渠道 | TASK-CHAN | TASK-CHAN-001 |
| M5 账户 | TASK-ACCT | TASK-ACCT-001 |
| M6 日报 | TASK-RPT | TASK-RPT-001 |
| M7 充值 | TASK-FIN | TASK-FIN-001 |
| M8 账本 | TASK-LEDGER | TASK-LEDGER-001 |
| M9 对账 | TASK-RECON | TASK-RECON-001 |
| M10 利润 | TASK-PROFIT | TASK-PROFIT-001 |
| M11 周报 | TASK-WEEKLY | TASK-WEEKLY-001 |

---

## 8. 常用命令

```bash
# 环境检查
python --version          # 预期: 3.11+
node -v                   # 预期: 20+

# 运行测试
pytest backend/tests/ -v                    # 运行所有测试
pytest backend/tests/test_users_api.py -v   # 运行单个文件

# 代码检查
ruff check backend/                         # lint 检查
ruff format backend/                        # 自动格式化

# 数据库迁移
alembic revision --autogenerate -m "描述"   # 生成迁移
alembic upgrade head                        # 执行迁移

# Git 操作
git status
git add .
git commit -m "类型(模块): 描述"
git push
```

---

## 9. 财务模块铁律

| 铁律 | 约束 | 检查方法 |
|------|------|----------|
| 金额必用 Decimal | 禁止 Float | `grep -r "float\|Float" backend/` |
| 核心数据禁删 | 账本只能红冲 | `grep -r "\.delete\(\)" backend/` |
| 终态不可回退 | completed 禁止修改 | 审查状态机代码 |
| 双写必须事务 | 双账本同时写 | 审查事务边界 |
| 操作必须审计 | 记录操作人 | 检查 created_by |

---

## 10. Phase 边界

### Phase 1 (照亮阶段)
- 原则: 记录事实、展示状态、提示异常，**不强制阻断**
- 模块: M1-M8, M10, M11 (部分)
- 日报: 3 状态简化版

### Phase 2 (自动化阶段)
- 原则: 引入约束、强制审批、考核关联
- 模块: M6 完整版, M9 对账
- 日报: 8 状态完整版
