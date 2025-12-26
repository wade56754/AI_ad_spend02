# SoT 应用指南：从文档到代码

> **目标**：让 RECONCILIATION_CONTROL_CENTER_SOT.md 真正落地到项目开发中

---

## 一、文档部署

### 1.1 放到项目目录

```bash
# 在项目根目录执行
cp RECONCILIATION_CONTROL_CENTER_SOT.md docs/sot/

# 目录结构
docs/
├── 1.overview/
│   ├── MASTER.md           # 架构宪法
│   └── CORE_MODULES.md     # 核心模块
├── 2.sot/
│   ├── STATE_MACHINE.md    # 状态机
│   ├── DATA_SCHEMA.md      # 数据模型
│   ├── LEDGER_SOT.md       # 账本规则
│   ├── BUSINESS_RULES.md   # 业务规则
│   ├── API_SOT.md          # API 规范
│   ├── ERROR_CODES_SOT.md  # 错误码
│   └── RECONCILIATION_CONTROL_CENTER_SOT.md  # ⭐ 新增
└── 3.dev-guides/
    └── ...
```

### 1.2 更新 SoT 裁判链

在 `MASTER.md` 或 `PROJECT_RULES.md` 中更新裁判链：

```yaml
# .claude/PROJECT_RULES.md 或 MASTER.md

sotChain:
  - "MASTER.md v4.4"
  - "BUSINESS_FLOW_MANAGEMENT.md"
  - "MVP_PHASE_DESIGN.md"
  - "STATE_MACHINE.md v2.7"              # 版本升级
  - "DATA_SCHEMA.md v5.3"                # 版本升级
  - "LEDGER_SOT.md v1.2"                 # 版本升级
  - "RECONCILIATION_CONTROL_CENTER_SOT.md v1.1"  # ⭐ 新增
  - "BUSINESS_RULES.md v4.0"             # 版本升级
  - "API_SOT.md v9.1"                    # 版本升级
  - "ERROR_CODES_SOT.md v2.2"            # 版本升级
  - "AUTH_SPEC.md v2.0"
```

---

## 二、开发流程集成

### 2.1 开发前必查（AI 编码防幻觉）

```
┌─────────────────────────────────────────────────────────────┐
│  开发任务: 实现对账守恒校验 API                              │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 查 SoT 文档                                        │
│  ────────────────────                                       │
│  1. 打开 RECONCILIATION_CONTROL_CENTER_SOT.md               │
│  2. 找到 §2.3 守恒公式                                       │
│  3. 找到 §5.1 BR-REC-001 规则                               │
│  4. 找到 §9.1 REC-* 错误码                                  │
│  5. 找到 §10.2 对账 API 端点                                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 2: 确认没有遗漏                                        │
│  ────────────────────                                       │
│  □ 守恒公式定义清楚了吗？                                    │
│  □ 阈值（¥1/¥100）确认了吗？                                 │
│  □ 错误码格式正确吗？                                        │
│  □ API 路径正确吗？                                          │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  Step 3: 开始写代码                                          │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 代码中引用 SoT

**每个关键函数都要注释引用来源**：

```python
# backend/services/reconciliation_service.py

class ReconciliationService:
    """
    对账服务
    
    SoT 引用:
    - RECONCILIATION_CONTROL_CENTER_SOT.md §2.3 (守恒公式)
    - RECONCILIATION_CONTROL_CENTER_SOT.md §5.1 (BR-REC-001~004)
    """
    
    def validate_conservation(
        self, 
        ad_account_id: UUID, 
        start_date: date, 
        end_date: date
    ) -> ConservationResult:
        """
        验证守恒公式: Σ(充值) - Σ(消耗) = Δ(余额) + Δ(押款)
        
        SoT 引用:
        - RECONCILIATION_CONTROL_CENTER_SOT.md §2.3
        - BR-REC-001: 对账守恒公式校验
        
        阈值 (来自 §2.3):
        - ≤ ¥1.00: 自动通过
        - > ¥1.00 且 ≤ ¥100.00: 黄灯
        - > ¥100.00: 红灯
        """
        # 1. 计算 Σ(充值到账)
        total_topup = self._sum_topup(ad_account_id, start_date, end_date)
        
        # 2. 计算 Σ(实际消耗)
        total_cost = self._sum_cost(ad_account_id, start_date, end_date)
        
        # 3. 计算 Δ(余额)
        delta_balance = self._calc_balance_delta(ad_account_id, start_date, end_date)
        
        # 4. 计算 Δ(押款)
        delta_deposit = self._calc_deposit_delta(ad_account_id, start_date, end_date)
        
        # 5. 守恒校验
        left_side = total_topup - total_cost
        right_side = delta_balance + delta_deposit
        difference = abs(left_side - right_side)
        
        # 6. 阈值判断 (BR-REC-001)
        if difference <= Decimal("1.00"):
            return ConservationResult(status="pass", difference=difference)
        elif difference <= Decimal("100.00"):
            return ConservationResult(status="yellow", difference=difference)
        else:
            return ConservationResult(status="red", difference=difference)
```

### 2.3 PR 检查清单

```markdown
## PR Checklist (对账模块)

### SoT 合规检查
- [ ] 状态枚举来自 RECONCILIATION_CONTROL_CENTER_SOT.md §4.1
- [ ] 错误码来自 RECONCILIATION_CONTROL_CENTER_SOT.md §9
- [ ] API 路径与 RECONCILIATION_CONTROL_CENTER_SOT.md §10 一致
- [ ] 守恒公式与 RECONCILIATION_CONTROL_CENTER_SOT.md §2.3 一致

### 代码规范检查
- [ ] 关键函数有 SoT 引用注释
- [ ] 金额字段使用 Decimal(15,2)
- [ ] 状态流转遵循白名单

### 测试覆盖
- [ ] TC-REC-001~005 守恒公式测试
- [ ] TC-REC-006~011 状态机测试
- [ ] TC-SET-001~007 结算规则测试
```

---

## 三、数据库迁移

### 3.1 创建 Alembic 迁移

```bash
# 生成迁移文件
cd backend
alembic revision --autogenerate -m "add_reconciliation_control_center"
```

### 3.2 迁移脚本内容

```python
# backend/alembic/versions/xxx_add_reconciliation_control_center.py

"""add reconciliation control center

SoT 引用:
- RECONCILIATION_CONTROL_CENTER_SOT.md §3 (数据模型)

Revision ID: xxx
Revises: yyy
Create Date: 2025-12-26
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

def upgrade():
    # §3.3 settlement_rules 表
    op.create_table(
        'settlement_rules',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('rule_type', sa.String(20), nullable=False),
        sa.Column('config', JSONB, nullable=False),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_to', sa.Date()),
        sa.Column('created_by', UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.CheckConstraint("rule_type IN ('tiered', 'markup')"),
    )
    
    # §3.1 balance_snapshots 表
    op.create_table(
        'balance_snapshots',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('ad_account_id', UUID(), sa.ForeignKey('ad_accounts.id'), nullable=False),
        sa.Column('snapshot_date', sa.Date(), nullable=False),
        sa.Column('balance', sa.Numeric(15, 2), nullable=False),
        sa.Column('deposit', sa.Numeric(15, 2), nullable=False, server_default='0'),
        sa.Column('remaining_balance', sa.Numeric(15, 2), nullable=False),
        sa.Column('source', sa.String(20), nullable=False, server_default='manual'),
        sa.Column('created_by', UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('notes', sa.Text()),
        sa.UniqueConstraint('ad_account_id', 'snapshot_date'),
        sa.CheckConstraint("source IN ('manual', 'api', 'import')"),
    )
    
    # §3.2 reconciliation_issues 表
    op.create_table(
        'reconciliation_issues',
        sa.Column('id', UUID(), primary_key=True),
        sa.Column('reconciliation_batch_id', UUID(), sa.ForeignKey('reconciliation_batches.id')),
        sa.Column('ad_account_id', UUID(), sa.ForeignKey('ad_accounts.id')),
        sa.Column('issue_date', sa.Date(), nullable=False),
        sa.Column('issue_type', sa.String(30), nullable=False),
        sa.Column('expected_amount', sa.Numeric(15, 2)),
        sa.Column('actual_amount', sa.Numeric(15, 2)),
        sa.Column('status', sa.String(20), nullable=False, server_default='open'),
        sa.Column('assigned_to', UUID(), sa.ForeignKey('users.id')),
        sa.Column('assigned_at', sa.DateTime(timezone=True)),
        sa.Column('resolution_type', sa.String(30)),
        sa.Column('resolution_note', sa.Text()),
        sa.Column('resolved_at', sa.DateTime(timezone=True)),
        sa.Column('resolved_by', UUID(), sa.ForeignKey('users.id')),
        sa.Column('attachments', JSONB, server_default='[]'),
        sa.Column('sla_deadline', sa.DateTime(timezone=True)),
        sa.Column('sla_breached', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_by', UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # §3.4 projects 表扩展
    op.add_column('projects', sa.Column('settlement_type', sa.String(20), server_default='fixed'))
    op.add_column('projects', sa.Column('settlement_rules_id', UUID(), sa.ForeignKey('settlement_rules.id')))
    
    # §3.5 ad_accounts 表扩展
    op.add_column('ad_accounts', sa.Column('deposit', sa.Numeric(15, 2), server_default='0'))
    op.add_column('ad_accounts', sa.Column('deposit_updated_at', sa.DateTime(timezone=True)))
    
    # 索引
    op.create_index('idx_balance_snapshots_date', 'balance_snapshots', ['snapshot_date'])
    op.create_index('idx_balance_snapshots_account', 'balance_snapshots', ['ad_account_id'])
    op.create_index('idx_rec_issues_status', 'reconciliation_issues', ['status'])
    op.create_index('idx_rec_issues_date', 'reconciliation_issues', ['issue_date'])


def downgrade():
    op.drop_index('idx_rec_issues_date')
    op.drop_index('idx_rec_issues_status')
    op.drop_index('idx_balance_snapshots_account')
    op.drop_index('idx_balance_snapshots_date')
    
    op.drop_column('ad_accounts', 'deposit_updated_at')
    op.drop_column('ad_accounts', 'deposit')
    op.drop_column('projects', 'settlement_rules_id')
    op.drop_column('projects', 'settlement_type')
    
    op.drop_table('reconciliation_issues')
    op.drop_table('balance_snapshots')
    op.drop_table('settlement_rules')
```

---

## 四、后端开发顺序

### 4.1 推荐开发顺序（按依赖）

```
Phase 1: 基础设施 (Day 1-2)
├── 1.1 数据库迁移 (alembic)
├── 1.2 Models 定义
│   ├── balance_snapshot.py
│   ├── reconciliation_issue.py
│   └── settlement_rule.py
└── 1.3 Schemas 定义
    ├── balance_snapshot.py
    ├── reconciliation_issue.py
    └── settlement_rule.py

Phase 2: 核心服务 (Day 3-6)
├── 2.1 SnapshotService
│   ├── create_snapshot()
│   ├── batch_import_snapshots()
│   └── check_snapshot_gaps()
├── 2.2 ReconciliationService
│   ├── validate_conservation()  ← 核心！
│   ├── create_issue()
│   ├── assign_issue()
│   ├── resolve_issue()
│   └── close_issue()
└── 2.3 SettlementService
    ├── calculate_revenue()
    ├── calculate_tiered_revenue()
    └── calculate_markup_revenue()

Phase 3: API 层 (Day 7-8)
├── 3.1 routers/snapshots.py
├── 3.2 routers/reconciliation.py
└── 3.3 routers/settlements.py

Phase 4: 测试 (Day 9-10)
├── 4.1 单元测试 (services)
├── 4.2 API 测试 (routers)
└── 4.3 集成测试 (流程)
```

### 4.2 核心代码结构

```
backend/
├── models/
│   ├── balance_snapshot.py      # SoT §3.1
│   ├── reconciliation_issue.py  # SoT §3.2
│   └── settlement_rule.py       # SoT §3.3
├── schemas/
│   ├── balance_snapshot.py
│   ├── reconciliation_issue.py
│   └── settlement_rule.py
├── services/
│   ├── snapshot_service.py
│   ├── reconciliation_service.py  # SoT §2.3, §5.1
│   └── settlement_service.py      # SoT §6
├── routers/
│   ├── snapshots.py               # SoT §10.1
│   ├── reconciliation.py          # SoT §10.2
│   └── settlements.py             # SoT §10.3
└── tests/
    ├── services/
    │   ├── test_reconciliation_service.py  # SoT §11.1-11.2
    │   └── test_settlement_service.py      # SoT §11.3
    └── routers/
        └── test_reconciliation_api.py
```

---

## 五、前端开发

### 5.1 页面与 SoT 映射

| 页面 | 对应 SoT 章节 | 角色 |
|------|-------------|------|
| 余额快照录入 | §3.1, §15.1.4 | 户管 |
| 对账看板 | §7, §15.2.3 | 财务 |
| 差异单列表 | §4.1, §10.2 | 财务 |
| 差异单处理 | §4.1 状态机 | 财务/户管 |
| 结算规则配置 | §6, §10.3 | 财务 |
| 老板驾驶舱 | §15.2.5 | CEO |

### 5.2 TypeScript 类型定义

```typescript
// frontend/src/modules/reconciliation/types/index.ts

/**
 * 差异单类型
 * SoT 引用: RECONCILIATION_CONTROL_CENTER_SOT.md §3.2
 */
export type IssueType =
  | 'topup_mismatch'      // 充值差异
  | 'spend_mismatch'      // 消耗差异
  | 'deposit_change'      // 押款变化
  | 'balance_anomaly'     // 余额异常
  | 'snapshot_missing'    // 快照缺失
  | 'conservation_failed' // 守恒校验失败
  | 'other';

/**
 * 差异单状态
 * SoT 引用: RECONCILIATION_CONTROL_CENTER_SOT.md §4.1
 */
export type IssueStatus = 
  | 'open'          // 待处理
  | 'assigned'      // 已分配
  | 'investigating' // 调查中
  | 'resolved'      // 已处理
  | 'closed';       // 已关闭

/**
 * 结算类型
 * SoT 引用: RECONCILIATION_CONTROL_CENTER_SOT.md §6.1
 */
export type SettlementType = 'fixed' | 'tiered' | 'markup';

/**
 * 余额快照
 * SoT 引用: RECONCILIATION_CONTROL_CENTER_SOT.md §3.1
 */
export interface BalanceSnapshot {
  id: string;
  adAccountId: string;
  snapshotDate: string;
  balance: number;
  deposit: number;
  remainingBalance: number;
  source: 'manual' | 'api' | 'import';
  createdBy: string;
  createdAt: string;
  notes?: string;
}

/**
 * 差异单
 * SoT 引用: RECONCILIATION_CONTROL_CENTER_SOT.md §3.2
 */
export interface ReconciliationIssue {
  id: string;
  adAccountId: string;
  issueDate: string;
  issueType: IssueType;
  expectedAmount?: number;
  actualAmount?: number;
  differenceAmount?: number;
  status: IssueStatus;
  assignedTo?: string;
  assignedAt?: string;
  resolutionType?: string;
  resolutionNote?: string;
  resolvedAt?: string;
  slaDeadline?: string;
  slaBreached: boolean;
}
```

### 5.3 API Hooks

```typescript
// frontend/src/modules/reconciliation/hooks/useReconciliation.ts

import { useMutation, useQuery } from '@tanstack/react-query';
import { reconciliationApi } from '../services/api';

/**
 * 对账校验 Hook
 * SoT 引用: RECONCILIATION_CONTROL_CENTER_SOT.md §10.2
 */
export function useValidateConservation() {
  return useMutation({
    mutationFn: reconciliationApi.validateConservation,
    onError: (error) => {
      // 错误码来自 SoT §9.1
      if (error.code === 'REC-007') {
        toast.error('对账期间快照缺失，请先补录快照');
      }
    }
  });
}

/**
 * 差异单列表 Hook
 * SoT 引用: RECONCILIATION_CONTROL_CENTER_SOT.md §10.2
 */
export function useReconciliationIssues(filters: IssueFilters) {
  return useQuery({
    queryKey: ['reconciliation-issues', filters],
    queryFn: () => reconciliationApi.getIssues(filters),
  });
}
```

---

## 六、测试验证

### 6.1 守恒公式测试用例

```python
# backend/tests/services/test_reconciliation_service.py

"""
SoT 引用: RECONCILIATION_CONTROL_CENTER_SOT.md §11.1
"""

import pytest
from decimal import Decimal
from backend.services.reconciliation_service import ReconciliationService

class TestConservationValidation:
    """TC-REC-001 ~ TC-REC-005"""
    
    def test_conservation_pass(self, db_session, test_data):
        """
        TC-REC-001: 守恒校验通过
        SoT: §2.3, BR-REC-001
        """
        service = ReconciliationService(db_session)
        
        # 准备数据: 充值100, 消耗60, 余额变化40
        # Σ(充值) - Σ(消耗) = Δ(余额) + Δ(押款)
        # 100 - 60 = 40 + 0 ✓
        
        result = service.validate_conservation(
            ad_account_id=test_data.account_id,
            start_date=date(2025, 12, 1),
            end_date=date(2025, 12, 31)
        )
        
        assert result.status == "pass"
        assert result.difference <= Decimal("1.00")
    
    def test_conservation_fail_red(self, db_session, test_data):
        """
        TC-REC-002: 守恒校验失败 - 红灯
        SoT: §2.3, BR-REC-001
        阈值: > ¥100.00
        """
        service = ReconciliationService(db_session)
        
        # 准备数据: 差异 = 150
        result = service.validate_conservation(
            ad_account_id=test_data.account_id_with_red_diff,
            start_date=date(2025, 12, 1),
            end_date=date(2025, 12, 31)
        )
        
        assert result.status == "red"
        assert result.difference > Decimal("100.00")
    
    def test_conservation_fail_yellow(self, db_session, test_data):
        """
        TC-REC-003: 守恒校验失败 - 黄灯
        SoT: §2.3, BR-REC-001
        阈值: > ¥1.00 且 ≤ ¥100.00
        """
        service = ReconciliationService(db_session)
        
        # 准备数据: 差异 = 50
        result = service.validate_conservation(
            ad_account_id=test_data.account_id_with_yellow_diff,
            start_date=date(2025, 12, 1),
            end_date=date(2025, 12, 31)
        )
        
        assert result.status == "yellow"
        assert Decimal("1.00") < result.difference <= Decimal("100.00")
```

---

## 七、日常工作流

### 7.1 开发新功能

```
1. 接到需求: "实现差异单分配功能"
              │
              ▼
2. 查 SoT:   打开 RECONCILIATION_CONTROL_CENTER_SOT.md
              │
              ├── §4.1 状态机: open → assigned 需要 finance/admin
              ├── §5.1 BR-REC-002: SLA 规则
              ├── §9.1 REC-004: 权限不足错误码
              └── §10.2 API: PUT /api/v1/reconciliation/issues/{id}/assign
              │
              ▼
3. 写代码:   Service → Router → 测试
              │
              ▼
4. 提 PR:    填写 SoT 合规检查清单
              │
              ▼
5. Code Review: 检查是否符合 SoT
```

### 7.2 修 Bug

```
1. Bug: "差异单状态跳过了 assigned 直接到 investigating"
              │
              ▼
2. 查 SoT:   RECONCILIATION_CONTROL_CENTER_SOT.md §4.1
              │
              └── 状态流转白名单: open → [assigned] 唯一
              │
              ▼
3. 定位:     代码违反了 SoT 定义的状态机
              │
              ▼
4. 修复:     添加状态流转校验
```

---

## 八、检查清单

### 开发前
- [ ] 确认需求涉及 SoT 哪些章节
- [ ] 确认数据表结构与 §3 一致
- [ ] 确认状态枚举与 §4 一致
- [ ] 确认业务规则编号与 §5 一致

### 开发中
- [ ] 关键函数添加 SoT 引用注释
- [ ] 错误码使用 §9 定义的 REC-*/SET-*
- [ ] 金额字段使用 Decimal(15,2)

### 提 PR 前
- [ ] 单元测试覆盖 §11 定义的测试用例
- [ ] API 路径与 §10 一致
- [ ] 运行回归测试通过

---

## 九、常见问题

### Q1: SoT 文档和代码冲突怎么办？
**A**: 以 SoT 为准，修改代码。如果确认 SoT 有误，走 OpenSpec 流程修改 SoT。

### Q2: SoT 没有覆盖的场景怎么办？
**A**: 停止开发，创建 OpenSpec 提案，补充 SoT 定义后再继续。

### Q3: 紧急需求来不及更新 SoT 怎么办？
**A**: 先在代码中标注 `TODO: 待补充 SoT`，并在 Sprint 结束前补充。

---

**文档版本**: v1.0
**适用于**: RECONCILIATION_CONTROL_CENTER_SOT.md v1.1
**最后更新**: 2025-12-26
