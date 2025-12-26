# C1 充值审批 - 后端模块规格书

> **版本**: v1.0
> **更新日期**: 2025-12-23
> **SoT 基准**: DATA_SCHEMA.md v5.3, STATE_MACHINE.md v2.7, API_SOT.md v9.3
> **参考指南**: docs/3.dev-guides/BACKEND_MODULE_SPEC_GUIDE.md

---

## 目录

- [§1 模块概述](#1-模块概述)
- [§2 数据模型](#2-数据模型)
- [§3 API 设计](#3-api-设计)
- [§4 权限控制](#4-权限控制)
- [§5 业务逻辑](#5-业务逻辑)
- [§6 前后端接口契约](#6-前后端接口契约)
- [§7 测试要点](#7-测试要点)
- [§8 性能要求](#8-性能要求)
- [§9 安全规范](#9-安全规范)

---

## §1 模块概述

### 1.1 业务目标

本模块实现广告账户充值申请的完整审批流程。投手或户管提交充值申请，经数据员审核和财务审批后，完成打款并更新账户余额。系统通过责任追溯机制确保"谁对钱负责"的问题得到解答。

### 1.2 涉及角色

| 角色 | 系统角色名 | 本模块权限 |
|------|------------|------------|
| 老板 | ceo | 查看所有充值申请（只读） |
| 项目负责人 | project_owner | 查看项目内充值申请（只读） |
| 财务 | finance | **核心操作者**: 财务审批、标记打款、上传凭证 |
| 主管 | supervisor | 查看下属充值申请（只读） |
| 投手 | pitcher (media_buyer) | 创建充值申请、取消自己的申请 |
| 户管 | account_manager | 创建充值申请 |
| 运营 | data_operator | **核心操作者**: 数据审核 |
| 管理员 | admin | 所有操作 |

### 1.3 模块边界

**本模块负责：**
- 充值申请的 CRUD 操作
- 7 状态机流转: draft → pending_review → finance_approve → paid → completed
- 数据员审核 (pending_review → finance_approve/rejected)
- 财务审批 (finance_approve → paid/rejected)
- 打款确认 (paid → completed)
- 审批日志记录

**本模块不负责：**
- 账户余额的直接修改（由 LEDGER_SOT.md 账本模块负责）
- 广告消耗扣款（由日报模块负责）
- 账户冻结/解冻（由账户管理模块负责）

### 1.4 SoT 引用清单 (AI 防幻觉)

| SoT 文档 | 版本 | 引用章节 | 用途 |
|---------|------|---------|------|
| DATA_SCHEMA.md | v5.3 | §4.1 topup_requests | 表结构、字段定义 |
| STATE_MACHINE.md | v2.7 | §9 充值 7 状态机 | 状态流转规则 |
| BUSINESS_RULES.md | v4.1 | BR-TOP-001~005 | 充值业务规则 |
| ERROR_CODES_SOT.md | v2.1 | BIZ_*, STATE_* | 业务错误码 |
| API_SOT.md | v9.3 | §7 Topups | API 端点规范 |
| AUTH_SPEC.md | v2.0 | §3 权限矩阵 | 角色权限 |
| LEDGER_SOT.md | v1.2 | §2 充值记账 | 账本规则 |
| MASTER.md | v4.4 | §2.4 七角色, §3.1 责任追溯 | Phase 边界、责任模型 |

---

## §2 数据模型

### 2.1 表结构定义

**来源**: DATA_SCHEMA.md v5.3 §4.1, `backend/models/workflow/topup_request.py`

```sql
CREATE TABLE topup_requests (
  -- 主键
  id              BIGSERIAL PRIMARY KEY,

  -- 外键
  ad_account_id   BIGINT NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
  requested_by    UUID REFERENCES users(id) ON DELETE SET NULL,
  reviewed_by     UUID REFERENCES users(id) ON DELETE SET NULL,
  approved_by     UUID REFERENCES users(id) ON DELETE SET NULL,

  -- 业务字段
  amount          DECIMAL(15,2) NOT NULL,         -- 申请金额
  status          VARCHAR(20) NOT NULL DEFAULT 'draft',
  request_notes   TEXT,                           -- 申请备注
  reject_reason   TEXT,                           -- 拒绝原因

  -- 时间字段
  requested_at    TIMESTAMPTZ,                    -- 申请时间
  reviewed_at     TIMESTAMPTZ,                    -- 数据审核时间
  approved_at     TIMESTAMPTZ,                    -- 财务审批时间
  paid_at         TIMESTAMPTZ,                    -- 打款时间
  completed_at    TIMESTAMPTZ,                    -- 完成时间

  -- 并发控制
  version         INTEGER NOT NULL DEFAULT 1,     -- 乐观锁版本号

  -- 审计字段
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- 约束
  CONSTRAINT chk_topup_requests_status CHECK (
    status IN ('draft', 'pending_review', 'finance_approve', 'paid', 'completed', 'rejected', 'cancelled')
  ),
  CONSTRAINT chk_topup_requests_amount CHECK (amount > 0)
);

-- 索引
CREATE INDEX idx_topup_requests_ad_account_id ON topup_requests(ad_account_id);
CREATE INDEX idx_topup_requests_status ON topup_requests(status);
CREATE INDEX idx_topup_requests_requested_by ON topup_requests(requested_by);
CREATE INDEX idx_topup_requests_created_at ON topup_requests(created_at);
```

### 2.2 字段说明

| 字段 | 类型 | 必填 | 说明 | 验证规则 |
|------|------|------|------|----------|
| id | BIGSERIAL | 自动 | 主键 | 系统生成 |
| ad_account_id | BIGINT | ✅ | 广告账户ID | 必须存在且激活 |
| amount | DECIMAL(15,2) | ✅ | 申请金额 | > 0, ≤ 100,000 (单笔上限) |
| status | VARCHAR(20) | 自动 | 7 状态机状态 | 见状态机定义 |
| requested_by | UUID | ✅ | 申请人ID | 当前登录用户 |
| reviewed_by | UUID | ❌ | 数据审核人ID | 审核时写入 |
| approved_by | UUID | ❌ | 财务审批人ID | 审批时写入 |
| request_notes | TEXT | ✅ | 申请原因 | 1-1000 字符 |
| reject_reason | TEXT | ❌ | 拒绝原因 | 拒绝时必填 |

### 2.3 关联表

#### 2.3.1 充值交易表

```sql
CREATE TABLE topup_transactions (
  id              BIGSERIAL PRIMARY KEY,
  request_id      BIGINT NOT NULL REFERENCES topup_requests(id) ON DELETE CASCADE,
  transaction_no  VARCHAR(50) NOT NULL,           -- 交易流水号
  amount          DECIMAL(15,2) NOT NULL,         -- 交易金额
  currency        VARCHAR(10) NOT NULL DEFAULT 'CNY',
  payment_method  VARCHAR(20),                    -- 支付方式
  payment_account VARCHAR(100),                   -- 打款账户
  transaction_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  receipt_file    VARCHAR(500),                   -- 凭证文件URL
  notes           TEXT,
  created_by      UUID REFERENCES users(id),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

#### 2.3.2 审批日志表

```sql
CREATE TABLE topup_approval_logs (
  id              BIGSERIAL PRIMARY KEY,
  request_id      BIGINT NOT NULL REFERENCES topup_requests(id) ON DELETE CASCADE,
  action          VARCHAR(50) NOT NULL,           -- 操作类型
  actor_id        UUID NOT NULL REFERENCES users(id),
  actor_role      VARCHAR(20) NOT NULL,           -- 操作者角色
  previous_status VARCHAR(20),                    -- 变更前状态
  new_status      VARCHAR(20),                    -- 变更后状态
  notes           TEXT,                           -- 操作说明
  ip_address      VARCHAR(50),                    -- 客户端IP
  user_agent      TEXT,                           -- 客户端信息
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 2.4 关联关系

```
topup_requests
    ├──→ ad_accounts (ad_account_id → id) 多对一
    │       └── 一个充值申请属于一个广告账户
    │
    ├──→ users (requested_by → id) 多对一
    │       └── 申请人（投手/户管）
    │
    ├──→ users (reviewed_by → id) 多对一
    │       └── 数据审核人（运营）
    │
    ├──→ users (approved_by → id) 多对一
    │       └── 财务审批人
    │
    ├──→ topup_transactions (id ← request_id) 一对多
    │       └── 交易记录
    │
    └──→ topup_approval_logs (id ← request_id) 一对多
            └── 审批日志
```

---

## §3 API 设计

### 3.1 端点清单

**来源**: API_SOT.md v9.3 §7, `backend/routers/topup.py`

| 方法 | 端点 | 描述 | 权限 |
|------|------|------|------|
| GET | /api/v1/topups | 列表查询 | 登录用户 |
| GET | /api/v1/topups/:id | 详情查询 | 数据所有者/上级 |
| POST | /api/v1/topups | 创建充值申请 | media_buyer, account_manager |
| PUT | /api/v1/topups/:id/review | 数据员审核 | data_operator |
| PUT | /api/v1/topups/:id/approve | 财务审批 | finance |
| PUT | /api/v1/topups/:id/pay | 标记已打款 | finance |
| POST | /api/v1/topups/:id/receipt | 上传打款凭证 | finance |
| POST | /api/v1/topups/:id/complete | 标记完成 | finance, admin |
| DELETE | /api/v1/topups/:id | 取消申请 | 申请人本人 (draft状态) |
| GET | /api/v1/topups/stats | 状态统计 | 登录用户 |
| GET | /api/v1/topups/statistics | 详细统计 | admin, finance, data_operator |
| GET | /api/v1/topups/dashboard | 仪表板数据 | 登录用户 |
| GET | /api/v1/topups/export | 导出记录 | admin, finance |

### 3.2 请求/响应格式

#### 3.2.1 创建充值申请

**POST /api/v1/topups**

```typescript
// 请求
interface TopupRequestCreate {
  ad_account_id: number;        // 广告账户ID
  requested_amount: number;     // 申请金额, > 0, ≤ 100,000
  currency?: string;            // 货币类型，默认 USD
  urgency_level?: 'low' | 'normal' | 'high' | 'urgent';  // 紧急程度
  reason: string;               // 充值原因, 1-1000 字符
  notes?: string;               // 补充说明
  expected_date?: string;       // 期望到账日期, YYYY-MM-DD
}

// 响应 201
interface TopupRequestResponse {
  data: {
    id: number;
    request_no: string;
    ad_account_id: number;
    ad_account_name: string;
    project_id: number;
    project_name: string;
    requested_amount: number;
    actual_amount: number | null;
    currency: string;
    urgency_level: string;
    status: 'draft';            // 创建后默认状态
    requested_by: number;
    requested_by_name: string;
    created_at: string;
    // ... 其他字段
  };
  message: string;
}
```

#### 3.2.2 数据员审核

**PUT /api/v1/topups/{request_id}/review**

状态转换: `pending_review → finance_approve` 或 `pending_review → rejected`

```typescript
// 请求
interface TopupDataReviewRequest {
  action: 'approve' | 'reject';  // 审核动作
  notes?: string;                // 审核说明, 最大 1000 字符
}

// 响应 200
interface DataReviewResponse {
  data: TopupRequestResponse;
  message: "审核完成";
}
```

#### 3.2.3 财务审批

**PUT /api/v1/topups/{request_id}/approve**

状态转换: `finance_approve → paid` 或 `finance_approve → rejected`

```typescript
// 请求
interface TopupFinanceApprovalRequest {
  action: 'approve' | 'reject';  // 审批动作
  actual_amount?: number;        // 实际打款金额 (approve 时必填)
  payment_method?: 'bank_transfer' | 'alipay' | 'wechat' | 'paypal' | 'credit_card' | 'other';
  notes?: string;                // 审批说明
}

// 响应 200
interface FinanceApproveResponse {
  data: TopupRequestResponse;
  message: "财务审批完成";
}
```

#### 3.2.4 标记已打款

**PUT /api/v1/topups/{request_id}/pay**

状态转换: `paid → completed` (如果自动完成)

```typescript
// 请求
interface TopupMarkPaidRequest {
  transaction_id?: string;       // 交易流水号
  notes?: string;                // 备注
}

// 响应 200
interface MarkPaidResponse {
  data: TopupRequestResponse;
  message: "已标记为打款";
}
```

### 3.3 错误码定义

**来源**: ERROR_CODES_SOT.md v2.1

| 错误码 | HTTP 状态 | 场景 |
|--------|-----------|------|
| VALIDATION_001 | 400 | 必填字段缺失 |
| VALIDATION_002 | 400 | 字段格式无效 |
| AUTH_401 | 401 | 未登录 |
| AUTH_500 | 403 | 无权限 |
| BIZ_002 | 404 | 充值申请不存在 |
| BIZ_201 | 400 | 单笔充值金额超限 (> 100,000) |
| BIZ_202 | 400 | 账户余额超限 (> 500,000) |
| BIZ_203 | 400 | 每日申请次数超限 (> 3次) |
| STATE_400 | 400 | 无效的状态转换 |
| STATE_401 | 400 | 当前状态不允许该操作 |

### 3.4 分页/筛选规范

```typescript
interface TopupListQueryParams {
  // 分页
  page?: number;              // 页码，默认 1
  page_size?: number;         // 每页数量，默认 20，最大 100

  // 筛选
  status?: string;            // 状态筛选
  urgency?: string;           // 紧急程度
  ad_account_id?: number;     // 广告账户ID
  project_id?: number;        // 项目ID
  start_date?: string;        // 开始日期
  end_date?: string;          // 结束日期
  request_no?: string;        // 申请编号
}
```

---

## §4 权限控制

### 4.1 角色权限矩阵 (7 角色)

**来源**: AUTH_SPEC.md v2.0, MASTER.md v4.4 §2.4

| 操作 | ceo | project_owner | finance | supervisor | pitcher | account_manager | admin |
|------|-----|---------------|---------|------------|---------|-----------------|-------|
| 查看所有 | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 查看项目内 | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 查看自己 | N/A | N/A | ✅ | ✅ | ✅ | ✅ | ✅ |
| 创建申请 | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| 取消申请(draft) | ❌ | ❌ | ❌ | ❌ | ✅(自己) | ✅(自己) | ✅ |
| 数据审核 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 财务审批 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 标记打款 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 标记完成 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 导出 | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |

**说明**:
- `data_operator` 角色专门负责数据审核
- `finance` 角色负责财务审批、打款、完成
- 申请人只能取消自己的 draft 状态申请

### 4.2 数据权限规则

```python
# backend/models/workflow/topup_request.py

def can_be_edited_by(self, user_id: UUID, user_role: UserRole) -> bool:
    """检查用户是否可以编辑此充值申请"""
    # 管理员可以编辑所有申请
    if user_role == UserRole.ADMIN:
        return True

    # 投手只能编辑自己提交的草稿
    if user_role == UserRole.MEDIA_BUYER:
        if self.requested_by != user_id:
            return False
        return self.status == TopupRequestStatus.DRAFT.value

    return False

def can_be_reviewed_by(self, user_id: UUID, user_role: UserRole) -> bool:
    """检查用户是否可以审核此申请（数据员）"""
    if user_role not in [UserRole.ADMIN, UserRole.DATA_OPERATOR]:
        return False
    return self.status == TopupRequestStatus.PENDING_REVIEW.value

def can_be_approved_by(self, user_id: UUID, user_role: UserRole) -> bool:
    """检查用户是否可以批准此申请（财务）"""
    if user_role not in [UserRole.ADMIN, UserRole.FINANCE]:
        return False
    return self.status == TopupRequestStatus.FINANCE_APPROVE.value
```

### 4.3 责任追溯 (MASTER.md §3.1)

```yaml
充值申请责任链:
  申请人 (requested_by):
    - 记录: 谁提交的申请
    - 时间: requested_at
    - 责任: 对申请金额的合理性负责

  数据审核人 (reviewed_by):
    - 记录: 谁审核的
    - 时间: reviewed_at
    - 责任: 对申请数据的准确性负责

  财务审批人 (approved_by):
    - 记录: 谁批准的
    - 时间: approved_at
    - 责任: 对打款决策负责

审批日志:
  - 每次状态变更都记录到 topup_approval_logs
  - 包含: 操作人、角色、时间、IP、前后状态
```

---

## §5 业务逻辑

### 5.1 状态机定义

**来源**: STATE_MACHINE.md v2.7 §9 充值 7 状态机

```
┌─────────┐     submit      ┌───────────────┐
│  draft  │ ───────────────→│ pending_review│
└────┬────┘                 └───────┬───────┘
     │                              │
     │ cancel                       ├──── review_approve ───→ ┌─────────────────┐
     ↓                              │                         │ finance_approve │
┌───────────┐                       │                         └────────┬────────┘
│ cancelled │ (终态)                │                                  │
└───────────┘                       │                    ┌─────────────┼─────────────┐
                                    │                    │             │             │
                                    │            approve │     reject  │     reject  │
                                    │                    ↓             │             │
                                    │             ┌──────────┐         │             │
                                    │             │   paid   │         │             │
                                    │             └────┬─────┘         │             │
                                    │                  │               │             │
                                    │           complete               │             │
                                    │                  ↓               │             │
                                    │           ┌───────────┐          │             │
                                    │           │ completed │ (终态)   │             │
                                    │           └───────────┘          │             │
                                    │                                  │             │
                                    └──────────────────────────────────┴─────────────┘
                                                       │
                                                       ↓
                                                ┌───────────┐
                                                │ rejected  │ (终态)
                                                └───────────┘
```

### 5.2 状态转换表

| 当前状态 | 目标状态 | API 端点 | 触发条件 | 操作者 |
|----------|----------|----------|----------|--------|
| draft | pending_review | (自动提交) | 创建时自动 | pitcher/account_manager |
| draft | cancelled | DELETE | 取消申请 | 申请人本人 |
| pending_review | finance_approve | PUT /review | 数据员通过 | data_operator |
| pending_review | rejected | PUT /review | 数据员拒绝 | data_operator |
| finance_approve | paid | PUT /approve | 财务通过 | finance |
| finance_approve | rejected | PUT /approve | 财务拒绝 | finance |
| paid | completed | PUT /pay 或 POST /complete | 打款完成 | finance |

### 5.3 业务规则

**来源**: `backend/services/topup_service.py`

```python
class TopupService:
    # 业务规则常量
    MAX_SINGLE_AMOUNT = Decimal("100000")   # 单笔充值上限 10 万
    MAX_ACCOUNT_BALANCE = Decimal("500000") # 账户余额上限 50 万
    MAX_DAILY_REQUESTS = 3                   # 每日最大申请次数

    def create_request(self, request_data, current_user) -> TopupRequest:
        # 1. 验证广告账户权限
        ad_account = self._validate_ad_account_access(
            request_data.ad_account_id, current_user
        )

        # 2. 验证申请金额 (BIZ_201)
        if request_data.requested_amount > self.MAX_SINGLE_AMOUNT:
            raise BusinessLogicError("单笔充值金额不能超过10万", error_code="BIZ_201")

        # 3. 检查账户余额上限 (BIZ_202)
        self._check_account_balance_limit(
            request_data.ad_account_id,
            request_data.requested_amount
        )

        # 4. 检查申请频次限制 (BIZ_203)
        self._check_daily_request_limit(
            request_data.ad_account_id,
            current_user.id
        )

        # 5. 创建充值申请
        topup_request = TopupRequest(
            ad_account_id=request_data.ad_account_id,
            amount=request_data.requested_amount,
            status=TopupStatus.PENDING_REVIEW.value,  # 直接进入待审核
            request_notes=request_data.reason,
            requested_by=current_user.id,
            requested_at=datetime.now()
        )

        # 6. 记录审批日志
        self._create_approval_log(...)

        return topup_request
```

### 5.4 业务约束 + Phase 1 规则

```yaml
约束规则:
  金额约束:
    - 单笔充值上限: 100,000
    - 账户余额上限: 500,000
    - 申请金额必须 > 0
    - 金额使用 Decimal(15,2)

  频次约束:
    - 同一账户每日最多申请 3 次

  状态约束:
    - 只能按状态机定义的路径转换
    - 终态 (completed/rejected/cancelled) 不可回退
    - 只有 draft 状态可以取消
    - 只有申请人本人可以取消

  审批约束:
    - 数据审核必须由 data_operator 执行
    - 财务审批必须由 finance 执行
    - 每次审批必须记录审批日志

Phase 1 规则 (照亮阶段):
  ❌ 禁止: 自动拒绝超额申请、自动冻结账户
  ✅ 允许: 提示超限警告、记录异常、高亮显示

  异常处理:
    - 金额超限: 警告提示，但允许创建
    - 频次超限: 警告提示，但允许创建
    - 人工复核: 数据员/财务可以拒绝
```

---

## §6 前后端接口契约

### 6.1 字段映射

| 后端字段 (snake_case) | 前端字段 (camelCase) | 说明 |
|----------------------|---------------------|------|
| ad_account_id | adAccountId | 广告账户ID |
| requested_amount | requestedAmount | 申请金额 |
| actual_amount | actualAmount | 实际金额 |
| requested_by | requestedBy | 申请人ID |
| requested_by_name | requestedByName | 申请人姓名 |
| reviewed_by | reviewedBy | 审核人ID |
| approved_by | approvedBy | 审批人ID |
| request_notes | requestNotes | 申请备注 |
| reject_reason | rejectReason | 拒绝原因 |
| urgency_level | urgencyLevel | 紧急程度 |
| created_at | createdAt | 创建时间 |

### 6.2 枚举值对照

```typescript
// 充值申请状态 (7 状态机)
type TopupRequestStatus =
  | 'draft'           // 草稿
  | 'pending_review'  // 待数据审核
  | 'finance_approve' // 待财务审批
  | 'paid'            // 已打款
  | 'completed'       // 已完成 (终态)
  | 'rejected'        // 已拒绝 (终态)
  | 'cancelled';      // 已取消 (终态)

// 状态中文映射
const STATUS_LABELS: Record<TopupRequestStatus, string> = {
  draft: '草稿',
  pending_review: '待审核',
  finance_approve: '待审批',
  paid: '已打款',
  completed: '已完成',
  rejected: '已拒绝',
  cancelled: '已取消',
};

// 紧急程度
type UrgencyLevel = 'low' | 'normal' | 'high' | 'urgent';

// 支付方式
type PaymentMethod = 'bank_transfer' | 'alipay' | 'wechat' | 'paypal' | 'credit_card' | 'other';
```

### 6.3 时区/格式约定

```yaml
时间格式:
  日期: YYYY-MM-DD (不含时区)
  时间戳: ISO 8601 (含时区)

时区处理:
  存储: UTC (TIMESTAMPTZ)
  传输: UTC
  显示: 前端转换为本地时区

数字格式:
  金额: Decimal 类型，保留2位小数
  最大值: 100,000 (单笔), 500,000 (余额)
```

---

## §7 测试要点

### 7.1 单元测试

```python
# backend/tests/test_topup_service.py

class TestCreateTopupRequest:
    """创建充值申请测试"""

    def test_create_success(self, db, pitcher_user, ad_account):
        """投手可以创建充值申请"""
        request = TopupRequestCreate(
            ad_account_id=ad_account.id,
            requested_amount=Decimal("5000.00"),
            reason="账户余额不足"
        )
        topup = service.create_request(request, pitcher_user)
        assert topup.status == "pending_review"
        assert topup.amount == Decimal("5000.00")

    def test_reject_over_limit(self, db, pitcher_user, ad_account):
        """单笔金额超限应拒绝"""
        request = TopupRequestCreate(
            ad_account_id=ad_account.id,
            requested_amount=Decimal("150000.00"),  # 超过 10 万
            reason="大额充值"
        )
        with pytest.raises(BusinessLogicError) as exc:
            service.create_request(request, pitcher_user)
        assert "BIZ_201" in str(exc.value)

    def test_reject_daily_limit(self, db, pitcher_user, ad_account):
        """每日申请次数超限应拒绝"""
        # 先创建 3 个申请
        for _ in range(3):
            service.create_request(...)

        # 第 4 个应该失败
        with pytest.raises(BusinessLogicError) as exc:
            service.create_request(...)
        assert "BIZ_203" in str(exc.value)


class TestStateTransitions:
    """状态转换测试"""

    def test_pending_review_to_finance_approve(self, request):
        """pending_review → finance_approve 允许"""
        request.status = 'pending_review'
        assert request.can_transition_to(TopupRequestStatus.FINANCE_APPROVE)

    def test_completed_is_terminal(self, completed_request):
        """completed 是终态"""
        assert not completed_request.can_transition_to(TopupRequestStatus.PAID)

    def test_only_requester_can_cancel(self, request, other_user):
        """只有申请人可以取消"""
        with pytest.raises(ValueError):
            request.cancel(other_user.id)
```

### 7.2 集成测试

```python
# backend/tests/test_topup_api.py

class TestTopupAPI:
    """充值 API 集成测试"""

    async def test_pitcher_can_create(self, client, pitcher_token):
        """投手可以创建充值申请"""
        response = await client.post(
            "/api/v1/topups",
            headers={"Authorization": f"Bearer {pitcher_token}"},
            json={
                "ad_account_id": 1,
                "requested_amount": 5000,
                "reason": "账户余额不足"
            }
        )
        assert response.status_code == 201
        assert response.json()["data"]["status"] == "pending_review"

    async def test_data_operator_can_review(self, client, data_operator_token):
        """运营可以审核"""
        response = await client.put(
            "/api/v1/topups/1/review",
            headers={"Authorization": f"Bearer {data_operator_token}"},
            json={"action": "approve", "notes": "审核通过"}
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "finance_approve"

    async def test_finance_can_approve(self, client, finance_token):
        """财务可以审批"""
        response = await client.put(
            "/api/v1/topups/1/approve",
            headers={"Authorization": f"Bearer {finance_token}"},
            json={
                "action": "approve",
                "actual_amount": 5000,
                "payment_method": "bank_transfer"
            }
        )
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "paid"

    async def test_pitcher_cannot_approve(self, client, pitcher_token):
        """投手不能审批"""
        response = await client.put(
            "/api/v1/topups/1/approve",
            headers={"Authorization": f"Bearer {pitcher_token}"},
            json={"action": "approve", "actual_amount": 5000}
        )
        assert response.status_code == 403
```

### 7.3 权限测试矩阵

```python
@pytest.mark.parametrize("role,action,expected", [
    # [角色, 操作, 预期状态码]
    ("ceo", "list_all", 200),
    ("ceo", "create", 403),
    ("pitcher", "create", 201),
    ("pitcher", "cancel_own_draft", 200),
    ("pitcher", "review", 403),
    ("pitcher", "approve", 403),
    ("data_operator", "review", 200),
    ("data_operator", "approve", 403),
    ("finance", "review", 403),
    ("finance", "approve", 200),
    ("finance", "mark_paid", 200),
    ("admin", "all_operations", 200),
])
async def test_role_permissions(client, role, action, expected):
    """角色权限矩阵测试"""
    response = await execute_action(client, role, action)
    assert response.status_code == expected
```

---

## §8 性能要求

### 8.1 响应时间要求

| API | 目标 | 最大容忍 |
|-----|------|----------|
| 列表查询 | < 200ms | < 500ms |
| 详情查询 | < 100ms | < 300ms |
| 创建申请 | < 300ms | < 1s |
| 审核/审批 | < 300ms | < 1s |
| 统计查询 | < 500ms | < 2s |

### 8.2 索引要求

必须为以下查询场景建立索引：
- 按账户查询: `idx_topup_requests_ad_account_id`
- 按状态筛选: `idx_topup_requests_status`
- 按申请人查询: `idx_topup_requests_requested_by`
- 按时间排序: `idx_topup_requests_created_at`

### 8.3 并发控制

```yaml
乐观锁:
  - 使用 version 字段实现乐观锁
  - 每次更新时 version + 1
  - 并发冲突时返回 409 Conflict

事务隔离:
  - 审批操作使用 SERIALIZABLE 隔离级别
  - 防止重复审批
```

---

## §9 安全规范

### 9.1 认证授权

- 所有 API 需要 JWT Token
- 使用 `require_role([...])` 校验角色权限
- 数据权限通过 RLS 和 Service 层双重检查

### 9.2 输入验证

- [x] 使用 Pydantic v2 验证所有输入
- [x] 金额字段使用 Decimal，限制范围 (0, 100000]
- [x] 字符串字段有最大长度限制
- [x] 使用 ORM 参数化查询，禁止拼接 SQL
- [x] 期望日期不能早于明天

### 9.3 审计日志

必须记录以下操作：

| 操作类型 | 记录内容 |
|----------|----------|
| 创建申请 | 申请人、账户、金额、时间 |
| 数据审核 | 审核人、动作、时间、说明 |
| 财务审批 | 审批人、动作、实际金额、时间 |
| 标记打款 | 操作人、交易号、时间 |
| 取消申请 | 操作人、时间 |
| 状态变更 | old_status → new_status、操作人、IP |

---

## 附录: AI 代码工厂禁止行为清单

### A.1 禁止行为

| 禁止行为 | 正确做法 | 检查方式 |
|---------|---------|---------|
| 自定义状态值 | 使用 7 状态机 | 枚举对比 |
| 自动拒绝超额 | Phase 1 只警告 | 逻辑审查 |
| 跳过审批日志 | 每次状态变更记录 | 代码审查 |
| 直接修改余额 | 通过 Ledger 记账 | 代码审查 |
| 跳过权限检查 | require_role() + can_* 方法 | 代码审查 |
| 终态回退 | completed/rejected/cancelled 不可改 | 状态机测试 |

### A.2 SoT 追溯验证 Checklist

生成代码后必须验证：
- [ ] 所有状态值来自 STATE_MACHINE.md v2.7 §9 (7 状态)
- [ ] 所有错误码来自 ERROR_CODES_SOT.md v2.1
- [ ] 所有角色来自 MASTER.md v4.4 §2.4 (7 个)
- [ ] 金额字段使用 Decimal(15,2) 类型
- [ ] 时间字段使用 TIMESTAMPTZ + UTC
- [ ] 每次状态变更记录审批日志
- [ ] 责任追溯字段完整 (requested_by, reviewed_by, approved_by)

---

## 源码位置

| 层 | 文件路径 |
|----|---------|
| Model | `backend/models/workflow/topup_request.py` |
| Model | `backend/models/topup_fixed.py` (Transaction, ApprovalLog) |
| Schema | `backend/schemas/topup.py` |
| Service | `backend/services/topup_service.py` |
| Router | `backend/routers/topup.py` |
| Test | `backend/tests/test_topup_service.py` |
| Test | `backend/tests/test_topup_permissions.py` |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-23 | 初始版本，基于现有代码创建后端规格书 |

---

**维护者**: AI 广告代投系统开发团队
**参考文档**:
- `docs/3.dev-guides/BACKEND_MODULE_SPEC_GUIDE.md`
- `docs/10.module-specs/B1-topup-approval.md` (前端规格书)
- `docs/sot/STATE_MACHINE.md` v2.6 §9
- `docs/sot/DATA_SCHEMA.md` v5.2 §4.1
