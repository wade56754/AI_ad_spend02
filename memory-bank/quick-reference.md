# 速查参考表

> **版本**: v1.0
> **更新日期**: 2025-12-27
> **用途**: 开发时快速查阅，避免 AI 幻觉

---

## 1. SoT 文档版本对齐表

> 每次开发前必须确认版本一致

| 文档 | 版本 | 路径 | 用途 |
|------|------|------|------|
| MASTER.md | v4.6 | docs/sot/MASTER.md | 架构宪法、角色定义 |
| STATE_MACHINE.md | v2.7 | docs/sot/STATE_MACHINE.md | 状态机定义 |
| DATA_SCHEMA.md | v5.6 | docs/sot/DATA_SCHEMA.md | 数据库表结构 |
| BUSINESS_RULES.md | v4.7 | docs/sot/BUSINESS_RULES.md | 业务规则 |
| ERROR_CODES.md | v2.3 | docs/sot/ERROR_CODES_SOT.md | 错误码定义 |
| AUTH_SPEC.md | v2.2 | docs/sot/AUTH_SPEC.md | 认证授权 |
| LEDGER_SOT.md | v1.2 | docs/sot/LEDGER_SOT.md | 账本规则 |
| API_SOT.md | v9.4 | docs/sot/API_SOT.md | API 规范 |

---

## 2. 角色白名单 (6 角色)

> 来源: MASTER.md v4.6 §2.4

| 角色ID | 中文名 | 核心职责 |
|--------|--------|----------|
| `ceo` | 老板 | 资金安全、公司盈亏、最终决策 |
| `project_owner` | 项目负责人 | 项目盈亏、日报审核、确认有效粉 |
| `finance` | 财务 | 资金出入准确、数据真实、对账 |
| `pitcher` | 投手 | CPL 达标、日报准确、执行投放 |
| `account_manager` | 户管 | 账户分配、账户状态监控 |
| `admin` | 管理员 | 系统配置（不参与业务） |

**禁止使用的角色**:
- `supervisor` (已合并到 project_owner)
- `data_operator` (已移除)
- `media_buyer` (技术层角色，业务层用 pitcher)

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

> 来源: ERROR_CODES.md v2.3

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

> 来源: MASTER.md v4.6 §2.4

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
