# BR-FIN: 财务与充值业务规则

> **文档版本**: v1.0
> **最后更新**: 2025-11-20
> **所属模块**: 财务管理 (Finance & Topup)
> **引用文档**:
> - `DATA_SCHEMA.md` - 数据结构定义
> - `ERROR_CODES.md` - 错误码定义
> - `STATE_MACHINE.md` - 充值状态机
> - `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` - 核心开发手册

---

## 规则概览

| 规则编号 | 规则名称 | 优先级 | 状态 |
|---------|---------|--------|------|
| BR-FIN-001 | 充值申请创建权限 | P0 | ✅ Active |
| BR-FIN-002 | 财务审批职责分离 | P0 | ✅ Active |
| BR-FIN-003 | 金额字段合规性 | P0 | ✅ Active |
| BR-FIN-005 | 双写一致性保障 | P0 | ✅ Active |

---

## BR-FIN-001: 充值申请创建权限

### 业务场景

投手 (Media Buyer) 或客户经理 (Account Manager) 在广告账户余额不足时，需要向系统提交充值申请。系统必须验证用户权限、项目有效性和金额合规性。

### 规则定义

#### 1.1 角色权限约束

**允许创建充值申请的角色**:
- `media_buyer` - 投手可为自己负责的广告账户所属项目申请充值
- `account_manager` - 客户经理可为自己管理的项目申请充值

**禁止创建充值申请的角色**:
- ❌ `data_operator` - 数据操作员仅负责审核，不能发起申请
- ❌ `finance` - 财务人员仅负责审批，不能发起申请
- ✅ `admin` - 管理员可以代替任何角色发起申请（紧急情况）

#### 1.2 字段约束

**引用**: `DATA_SCHEMA.md` 3.4.1 - `topup_requests` 表

| 字段 | 类型 | 约束 | 说明 |
|-----|------|------|------|
| `amount` | DECIMAL(15,2) | **NOT NULL, > 0** | 申请金额必须大于0，最多保留2位小数 |
| `project_id` | BIGINT | **NOT NULL, FK → projects.id** | 必须引用有效的项目ID |
| `applicant_id` | UUID | **NOT NULL, FK → users.id** | 申请人ID，从当前用户获取 |
| `currency` | VARCHAR(10) | DEFAULT 'CNY' | 币种，当前仅支持人民币 |
| `urgency_level` | VARCHAR(20) | CHECK IN ('low', 'normal', 'high', 'urgent') | 紧急程度 |
| `status` | VARCHAR(20) | DEFAULT 'draft' | 初始状态必须为 `draft` |

#### 1.3 业务逻辑校验

**前置条件**:
1. 用户角色必须为 `media_buyer` 或 `account_manager` (admin例外)
2. 关联的项目 (`project_id`) 必须存在且状态不为 `archived`
3. 用户必须有权限访问该项目:
   - 投手: 该项目下有分配给自己的广告账户
   - 客户经理: 该项目的 `account_manager_id` 为当前用户
4. 充值金额 `amount` 必须大于 0 且小于等于 10,000,000.00 (业务限额)

**Service层实现示例**:
```python
# backend/services/topup_service.py
class TopupService:
    def create_request(self, payload: TopupCreate, user: Dict) -> TopupRequest:
        # 1. 角色权限校验
        user_role = user.get("profile", {}).get("role")
        if user_role not in ["admin", "media_buyer", "account_manager"]:
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,  # AUTH_500
                message="仅投手、客户经理和管理员可以创建充值申请"
            )

        # 2. 验证项目存在性
        project = self.db.query(Project).filter(Project.id == payload.project_id).first()
        if not project:
            raise ResourceNotFoundException(
                code=BusinessErrorCodes.RESOURCE_NOT_FOUND.code,  # BIZ_100
                message=f"项目 {payload.project_id} 不存在"
            )

        # 3. 验证项目状态
        if project.status == "archived":
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,  # BIZ_001
                message="已归档的项目无法申请充值"
            )

        # 4. 验证用户项目权限
        if user_role == "media_buyer":
            # 投手: 检查是否有分配到该项目的广告账户
            has_account = self.db.query(AdAccount).filter(
                AdAccount.project_id == payload.project_id,
                AdAccount.assigned_to == user.get("user", {}).id
            ).first()
            if not has_account:
                raise AuthorizationException(
                    code=AuthErrorCodes.PERMISSION_DENIED.code,  # AUTH_500
                    message="您没有权限为该项目申请充值"
                )

        elif user_role == "account_manager":
            # 客户经理: 检查是否是项目管理者
            if project.account_manager_id != user.get("user", {}).id:
                raise AuthorizationException(
                    code=AuthErrorCodes.PERMISSION_DENIED.code,  # AUTH_500
                    message="您不是该项目的客户经理,无权申请充值"
                )

        # 5. 金额合规性校验
        if payload.amount <= 0:
            raise ValidationException(
                code=BusinessErrorCodes.INVALID_INPUT.code,  # BIZ_002
                message="充值金额必须大于0"
            )

        if payload.amount > Decimal("10000000.00"):
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_INPUT.code,  # BIZ_002
                message="单次充值金额不得超过1000万元"
            )

        # 6. 创建充值申请
        request = TopupRequest(
            project_id=payload.project_id,
            applicant_id=user.get("user", {}).id,
            amount=payload.amount,
            currency="CNY",
            urgency_level=payload.urgency_level or "normal",
            status="draft",
            request_no=self._generate_request_no(),  # 生成唯一流水号
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        self.db.add(request)
        self.db.commit()

        return request
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|------------|
| 角色权限不足 | `AUTH_500` | 403 | "仅投手、客户经理和管理员可以创建充值申请" |
| 项目不存在 | `BIZ_100` | 404 | "项目 12345 不存在" |
| 项目已归档 | `BIZ_001` | 400 | "已归档的项目无法申请充值" |
| 无项目访问权限 | `AUTH_500` | 403 | "您没有权限为该项目申请充值" |
| 金额无效 | `BIZ_002` | 400 | "充值金额必须大于0" |
| 金额超限 | `BIZ_002` | 400 | "单次充值金额不得超过1000万元" |

**引用**: `ERROR_CODES.md` - 认证错误码 (AUTH_*), 业务错误码 (BIZ_*)

### 测试用例 (Test Intent)

**TC-FIN-001-01: 投手正常创建充值申请**
- **Given**: 用户角色为 `media_buyer`, 有分配到项目 #101 的广告账户
- **When**: 提交充值申请 `{project_id: 101, amount: 5000.00}`
- **Then**:
  - 创建成功, 返回 HTTP 201
  - `topup_requests` 表新增记录
  - `applicant_id` 为当前用户ID
  - `status` 为 `draft`

**TC-FIN-001-02: 客户经理为管理项目申请充值**
- **Given**: 用户角色为 `account_manager`, 是项目 #102 的 `account_manager_id`
- **When**: 提交充值申请 `{project_id: 102, amount: 10000.00}`
- **Then**: 创建成功, 返回 HTTP 201

**TC-FIN-001-03: 投手尝试为无权限项目申请充值**
- **Given**: 用户角色为 `media_buyer`, 没有分配到项目 #103 的账户
- **When**: 提交充值申请 `{project_id: 103, amount: 3000.00}`
- **Then**: 返回 HTTP 403, 错误码 `AUTH_500`

**TC-FIN-001-04: 数据操作员尝试创建充值申请**
- **Given**: 用户角色为 `data_operator`
- **When**: 提交充值申请 `{project_id: 101, amount: 2000.00}`
- **Then**: 返回 HTTP 403, 错误码 `AUTH_500`

**TC-FIN-001-05: 充值金额为0**
- **Given**: 用户角色为 `media_buyer`
- **When**: 提交充值申请 `{project_id: 101, amount: 0.00}`
- **Then**: 返回 HTTP 400, 错误码 `BIZ_002`, 消息 "充值金额必须大于0"

**TC-FIN-001-06: 充值金额超限**
- **Given**: 用户角色为 `account_manager`
- **When**: 提交充值申请 `{project_id: 102, amount: 20000000.00}`
- **Then**: 返回 HTTP 400, 错误码 `BIZ_002`, 消息 "单次充值金额不得超过1000万元"

**TC-FIN-001-07: 项目已归档**
- **Given**: 项目 #104 状态为 `archived`
- **When**: 客户经理提交充值申请 `{project_id: 104, amount: 5000.00}`
- **Then**: 返回 HTTP 400, 错误码 `BIZ_001`

---

## BR-FIN-002: 财务审批职责分离

### 业务场景

充值申请的审批流程需要实现职责分离 (Separation of Duties, SOD)，防止申请人自我审批导致的财务风险。系统必须强制执行多级审批流程，并确保每一步由不同角色的不同人员操作。

### 规则定义

#### 2.1 状态机流转规则

**引用**: `STATE_MACHINE.md` - 充值状态机 (Topup Request Lifecycle)

**完整流程**:
```
draft → pending_review → finance_approve → paid → completed
  ↓           ↓                ↓
cancelled  rejected         rejected
              ↓
            draft (重新提交)
```

**角色权限矩阵**:

| 状态流转 | 触发操作 | 允许角色 | 禁止条件 |
|---------|---------|---------|---------|
| `draft → pending_review` | 提交审核 | `media_buyer`, `account_manager` (申请人) | 申请人不能是自己的审批人 |
| `pending_review → finance_approve` | 数据复核通过 | `data_operator` | 复核人 ≠ 申请人 |
| `pending_review → rejected` | 数据复核拒绝 | `data_operator` | - |
| `finance_approve → paid` | 财务打款 | `finance` | 财务审批人 ≠ 申请人 ≠ 复核人 |
| `finance_approve → rejected` | 财务拒绝 | `finance` | - |
| `paid → completed` | 确认到账 | `finance` | - |
| `rejected → draft` | 重新修改 | 原申请人 | - |
| `draft/pending_review → cancelled` | 取消申请 | 原申请人, `admin` | 已支付后不可取消 |

#### 2.2 职责分离约束

**强制规则**:
1. **申请人 ≠ 复核人**: `topup_requests.applicant_id` ≠ 复核操作的 `operator_id`
2. **申请人 ≠ 审批人**: `topup_requests.applicant_id` ≠ 财务审批的 `approved_by`
3. **复核人 ≠ 审批人**: 数据复核的 `operator_id` ≠ 财务审批的 `approved_by`

**审批日志记录** (引用 `DATA_SCHEMA.md` 3.4.3):
```sql
CREATE TABLE topup_approval_logs (
    id BIGSERIAL PRIMARY KEY,
    topup_request_id BIGINT NOT NULL REFERENCES topup_requests(id),
    action VARCHAR(50) NOT NULL,  -- 'submit', 'data_review_approve', 'data_review_reject', 'finance_approve', 'finance_reject', 'cancel'
    from_status VARCHAR(20) NOT NULL,
    to_status VARCHAR(20) NOT NULL,
    operator_id UUID NOT NULL REFERENCES users(id),  -- 操作人ID
    comments TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 2.3 Service层实现示例

```python
# backend/services/topup_service.py
class TopupService:
    def submit_for_review(self, request_id: int, user: Dict) -> TopupRequest:
        """提交充值申请审核 (draft → pending_review)"""
        request = self._get_request_or_404(request_id)

        # 状态流转校验
        ensure_transition_allowed(request.status, "pending_review")

        # 仅申请人可提交
        if request.applicant_id != user.get("user", {}).id:
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="仅申请人可以提交审核"
            )

        with self.db.begin():
            request.status = "pending_review"
            request.submitted_at = datetime.now(timezone.utc)
            request.updated_at = datetime.now(timezone.utc)

            # 记录审批日志
            self._create_approval_log(
                request_id=request.id,
                action="submit",
                from_status="draft",
                to_status="pending_review",
                operator_id=user.get("user", {}).id,
                comments="提交审核"
            )

        return request

    def approve_by_data_operator(self, request_id: int, user: Dict) -> TopupRequest:
        """数据复核通过 (pending_review → finance_approve)"""
        request = self._get_request_or_404(request_id)

        # 角色权限校验
        if user.get("profile", {}).get("role") not in ["admin", "data_operator"]:
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="仅数据操作员可以执行数据复核"
            )

        # 状态流转校验
        ensure_transition_allowed(request.status, "finance_approve")

        # 职责分离检查: 复核人 ≠ 申请人
        if request.applicant_id == user.get("user", {}).id:
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,  # BIZ_001
                message="申请人不能审批自己的充值申请 (职责分离)"
            )

        with self.db.begin():
            request.status = "finance_approve"
            request.data_reviewed_by = user.get("user", {}).id
            request.data_reviewed_at = datetime.now(timezone.utc)
            request.updated_at = datetime.now(timezone.utc)

            self._create_approval_log(
                request_id=request.id,
                action="data_review_approve",
                from_status="pending_review",
                to_status="finance_approve",
                operator_id=user.get("user", {}).id,
                comments="数据复核通过"
            )

        return request

    def approve_by_finance(self, request_id: int, user: Dict, payment_voucher: str) -> TopupRequest:
        """财务审批并打款 (finance_approve → paid)"""
        request = self._get_request_or_404(request_id)

        # 角色权限校验
        if user.get("profile", {}).get("role") not in ["admin", "finance"]:
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="仅财务人员可以执行财务审批"
            )

        # 状态流转校验
        ensure_transition_allowed(request.status, "paid")

        # 职责分离检查: 财务审批人 ≠ 申请人
        if request.applicant_id == user.get("user", {}).id:
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,
                message="申请人不能审批自己的充值申请 (职责分离)"
            )

        # 职责分离检查: 财务审批人 ≠ 数据复核人
        if request.data_reviewed_by == user.get("user", {}).id:
            raise BusinessRuleException(
                code=BusinessErrorCodes.INVALID_OPERATION.code,
                message="数据复核人不能同时进行财务审批 (职责分离)"
            )

        with self.db.begin():
            request.status = "paid"
            request.approved_by = user.get("user", {}).id
            request.approved_at = datetime.now(timezone.utc)
            request.payment_voucher_url = payment_voucher  # 支付凭证
            request.updated_at = datetime.now(timezone.utc)

            self._create_approval_log(
                request_id=request.id,
                action="finance_approve",
                from_status="finance_approve",
                to_status="paid",
                operator_id=user.get("user", {}).id,
                comments="财务审批通过并完成打款"
            )

        return request
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|------------|
| 申请人自我审批 | `BIZ_001` | 400 | "申请人不能审批自己的充值申请 (职责分离)" |
| 复核人同时审批 | `BIZ_001` | 400 | "数据复核人不能同时进行财务审批 (职责分离)" |
| 非法状态流转 | `STATE_400` | 400 | "非法状态流转: pending_review → completed" |
| 角色权限不足 | `AUTH_500` | 403 | "仅财务人员可以执行财务审批" |

### 测试用例 (Test Intent)

**TC-FIN-002-01: 正常三级审批流程**
- **Given**:
  - 投手 Alice (user_id=U1) 创建充值申请 R1
  - 数据操作员 Bob (user_id=U2)
  - 财务人员 Carol (user_id=U3)
- **When**:
  1. Alice 提交审核 (draft → pending_review)
  2. Bob 数据复核通过 (pending_review → finance_approve)
  3. Carol 财务审批打款 (finance_approve → paid)
  4. Carol 确认到账 (paid → completed)
- **Then**:
  - 每一步状态流转成功
  - `topup_approval_logs` 记录4条操作日志
  - 最终状态为 `completed`

**TC-FIN-002-02: 申请人尝试自我复核**
- **Given**: 投手 Alice (user_id=U1) 创建充值申请 R2, 状态为 `pending_review`
- **When**: Alice 尝试作为数据操作员复核自己的申请
- **Then**: 返回 HTTP 400, 错误码 `BIZ_001`, 消息 "申请人不能审批自己的充值申请"

**TC-FIN-002-03: 复核人尝试自我财务审批**
- **Given**:
  - 充值申请 R3 状态为 `finance_approve`
  - 数据复核人为 Bob (user_id=U2)
- **When**: Bob 尝试作为财务人员审批 R3
- **Then**: 返回 HTTP 400, 错误码 `BIZ_001`, 消息 "数据复核人不能同时进行财务审批"

**TC-FIN-002-04: 管理员绕过职责分离 (紧急情况)**
- **Given**: 管理员 Admin (user_id=U0, role=admin)
- **When**: Admin 创建申请 R4 并自行完成全部审批流程
- **Then**:
  - 允许通过 (admin 拥有紧急处理权限)
  - 审计日志记录 operator_id 均为 U0
  - 触发安全告警 (可选)

---

## BR-FIN-003: 金额字段合规性

### 业务场景

财务系统对金额字段的精度和类型有严格要求，必须确保数据库层、应用层、前端展示层的一致性，避免浮点数精度问题导致的财务数据不准确。

### 规则定义

#### 3.1 数据库层约束

**引用**: `DATA_SCHEMA.md` 3.4.1 - `topup_requests` 表

**强制类型**: `DECIMAL(15,2)`
- 整数部分: 最多 13 位 (支持千万级金额)
- 小数部分: 固定 2 位 (精确到分)

**禁止类型**: `FLOAT`, `DOUBLE`, `REAL` (浮点数存在精度损失)

**示例**:
```sql
-- ✅ 正确
CREATE TABLE topup_requests (
    amount DECIMAL(15,2) NOT NULL CHECK (amount > 0)
);

-- ❌ 错误
CREATE TABLE topup_requests (
    amount FLOAT NOT NULL  -- 禁止使用浮点数
);
```

#### 3.2 应用层约束

**Python (Backend)**:
```python
from decimal import Decimal
from pydantic import BaseModel, Field

class TopupCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, max_digits=15, decimal_places=2)

    class Config:
        json_encoders = {
            Decimal: lambda v: str(v)  # 序列化为字符串,避免精度损失
        }

# ✅ 正确
amount = Decimal("5000.00")

# ❌ 错误
amount = 5000.0  # float类型
amount = Decimal(5000.0)  # 从float构造,可能有精度问题
```

**TypeScript (Frontend)**:
```typescript
// ✅ 正确: 使用字符串传输金额
interface TopupCreateRequest {
  amount: string;  // "5000.00"
  project_id: number;
}

// 前端展示时转换
const displayAmount = parseFloat(amount).toFixed(2);

// ❌ 错误
interface TopupCreateRequest {
  amount: number;  // JavaScript number 有精度问题
}
```

#### 3.3 金额锁定规则

**规则**: 充值申请进入 `pending_review` 状态后，金额字段锁定，仅管理员可修改。

**实现**:
```python
class TopupService:
    def update_amount(self, request_id: int, new_amount: Decimal, user: Dict) -> TopupRequest:
        request = self._get_request_or_404(request_id)

        # 状态检查: 只有 draft 状态可以修改金额
        if request.status != "draft":
            # 仅 admin 可以修改已提交申请的金额
            if user.get("profile", {}).get("role") != "admin":
                raise BusinessRuleException(
                    code=BusinessErrorCodes.STATUS_TRANSITION_NOT_ALLOWED.code,  # STATE_400
                    message=f"充值申请状态为 {request.status},金额已锁定,仅管理员可修改"
                )

        # 金额合规性校验
        if new_amount <= 0 or new_amount > Decimal("10000000.00"):
            raise ValidationException(
                code=BusinessErrorCodes.INVALID_INPUT.code,
                message="充值金额必须在 0.01 ~ 10,000,000.00 之间"
            )

        # 记录修改历史 (审计)
        old_amount = request.amount
        request.amount = new_amount
        request.updated_at = datetime.now(timezone.utc)
        request.updated_by = user.get("user", {}).id

        self._create_audit_log(
            action="UPDATE_AMOUNT",
            entity_id=str(request.id),
            user=user,
            payload_before={"amount": str(old_amount)},
            payload_after={"amount": str(new_amount)}
        )

        self.db.commit()
        return request
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|------------|
| 非 draft 状态修改金额 | `STATE_400` | 400 | "充值申请状态为 pending_review,金额已锁定" |
| 金额类型错误 | `BIZ_002` | 400 | "金额必须为 DECIMAL(15,2) 类型" |
| 金额超限 | `BIZ_002` | 400 | "充值金额必须在 0.01 ~ 10,000,000.00 之间" |

### 测试用例 (Test Intent)

**TC-FIN-003-01: draft 状态修改金额**
- **Given**: 充值申请 R1 状态为 `draft`, 金额为 `5000.00`
- **When**: 申请人修改金额为 `8000.00`
- **Then**: 修改成功, `amount` 更新为 `8000.00`

**TC-FIN-003-02: pending_review 状态修改金额 (非管理员)**
- **Given**: 充值申请 R2 状态为 `pending_review`, 申请人为 Alice
- **When**: Alice 尝试修改金额为 `6000.00`
- **Then**: 返回 HTTP 400, 错误码 `STATE_400`

**TC-FIN-003-03: 管理员强制修改已提交申请的金额**
- **Given**: 充值申请 R3 状态为 `finance_approve`, 管理员为 Admin
- **When**: Admin 修改金额为 `7000.00`
- **Then**:
  - 修改成功
  - 审计日志记录修改操作
  - 触发安全告警 (可选)

**TC-FIN-003-04: 金额精度测试**
- **Given**: 用户创建充值申请
- **When**: 提交金额 `5000.123` (小数点后3位)
- **Then**:
  - 后端拒绝请求, 返回 HTTP 400
  - 错误消息 "金额必须保留2位小数"

**TC-FIN-003-05: 浮点数精度问题防范**
- **Given**: 前端发送金额 `0.1 + 0.2` (JavaScript浮点数)
- **When**: 后端接收到 `0.30000000000000004`
- **Then**:
  - 后端使用 `Decimal` 类型处理
  - 数据库存储为 `0.30`
  - 审计日志记录原始输入

---

## BR-FIN-005: 双写一致性保障

### 业务场景

充值申请状态变更为 `completed` (到账确认) 时，必须同步更新资金总账 (`ledger_entries`)，确保充值金额记录到项目账本中。系统必须保证这两个操作的原子性，避免数据不一致。

### 规则定义

#### 5.1 事务一致性约束

**核心规则**: 以下操作必须在同一数据库事务中完成:
1. 更新 `topup_requests.status = 'completed'`
2. 插入 `ledger_entries` 记录 (`entry_type = 'topup_in'`)

**引用**: `DATA_SCHEMA.md` 3.4.4 - `ledger_entries` 表

```sql
CREATE TABLE ledger_entries (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL REFERENCES projects(id),
    entry_type VARCHAR(20) NOT NULL,  -- 'topup_in', 'spend_out', 'refund_in', 'adjustment'
    amount DECIMAL(15,2) NOT NULL,
    balance_after DECIMAL(15,2) NOT NULL,  -- 余额快照
    related_id BIGINT,  -- 关联业务ID (topup_request_id, daily_report_id等)
    occurred_at TIMESTAMPTZ NOT NULL,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### 5.2 Service层实现示例

```python
# backend/services/topup_service.py
class TopupService:
    def confirm_completed(self, request_id: int, user: Dict) -> TopupRequest:
        """确认充值到账 (paid → completed)"""
        request = self._get_request_or_404(request_id)

        # 角色权限校验
        if user.get("profile", {}).get("role") not in ["admin", "finance"]:
            raise AuthorizationException(
                code=AuthErrorCodes.PERMISSION_DENIED.code,
                message="仅财务人员可以确认到账"
            )

        # 状态流转校验
        ensure_transition_allowed(request.status, "completed")

        # ===== 开启事务 =====
        with self.db.begin():
            # 1. 更新充值申请状态
            request.status = "completed"
            request.completed_at = datetime.now(timezone.utc)
            request.updated_at = datetime.now(timezone.utc)

            # 2. 查询项目当前余额
            latest_entry = self.db.query(LedgerEntry).filter(
                LedgerEntry.project_id == request.project_id
            ).order_by(LedgerEntry.occurred_at.desc()).first()

            current_balance = latest_entry.balance_after if latest_entry else Decimal("0.00")
            new_balance = current_balance + request.amount

            # 3. 写入资金总账
            ledger_entry = LedgerEntry(
                project_id=request.project_id,
                entry_type="topup_in",
                amount=request.amount,
                balance_after=new_balance,
                related_id=request.id,  # 关联充值申请ID
                occurred_at=datetime.now(timezone.utc),
                notes=f"充值到账: {request.request_no}",
                created_at=datetime.now(timezone.utc)
            )
            self.db.add(ledger_entry)

            # 4. 记录审批日志
            self._create_approval_log(
                request_id=request.id,
                action="confirm_completed",
                from_status="paid",
                to_status="completed",
                operator_id=user.get("user", {}).id,
                comments="确认充值到账"
            )

            # 5. 提交事务 (commit 由 context manager 自动处理)

        return request
```

#### 5.3 失败回滚机制

**场景**: 如果事务中任一步骤失败 (如数据库约束违反、网络中断等)，整个事务回滚，保证数据一致性。

**示例**:
```python
try:
    with self.db.begin():
        # 步骤1: 更新 topup_requests
        request.status = "completed"

        # 步骤2: 插入 ledger_entries
        ledger_entry = LedgerEntry(...)
        self.db.add(ledger_entry)

        # 如果这里抛出异常,整个事务回滚
        self.db.flush()  # 触发数据库约束检查

except IntegrityError as e:
    # 事务已自动回滚
    logger.error(f"双写一致性失败: {e}")
    raise SystemException(
        code=SystemErrorCodes.TRANSACTION_FAILED.code,  # SYS_001
        message="充值确认失败,事务已回滚"
    )
```

#### 5.4 幂等性保障

**问题**: 网络重试可能导致重复调用 `confirm_completed` 接口。

**解决方案**: 在事务开始前检查状态:
```python
def confirm_completed(self, request_id: int, user: Dict) -> TopupRequest:
    request = self._get_request_or_404(request_id)

    # 幂等性检查
    if request.status == "completed":
        logger.warning(f"充值申请 {request_id} 已确认,跳过重复操作")
        return request  # 直接返回,不重复写入

    # 继续正常流程...
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 | 错误消息示例 |
|-----|--------|-----------|------------|
| 事务失败 | `SYS_001` | 500 | "充值确认失败,事务已回滚" |
| 数据库约束违反 | `DB_001` | 500 | "数据库完整性约束违反" |
| 重复确认 | - | 200 | (幂等返回,无错误) |

### 测试用例 (Test Intent)

**TC-FIN-005-01: 正常双写流程**
- **Given**: 充值申请 R1 状态为 `paid`, 金额为 `5000.00`, 项目 #101 当前余额 `10000.00`
- **When**: 财务人员确认到账
- **Then**:
  - `topup_requests.status` 更新为 `completed`
  - `ledger_entries` 新增记录: `entry_type='topup_in', amount=5000.00, balance_after=15000.00`
  - 两条记录在同一事务中提交

**TC-FIN-005-02: 事务中断回滚**
- **Given**: 充值申请 R2 状态为 `paid`
- **When**: 确认到账时,插入 `ledger_entries` 失败 (如外键约束违反)
- **Then**:
  - `topup_requests.status` 未更新 (仍为 `paid`)
  - `ledger_entries` 无新记录
  - 返回 HTTP 500, 错误码 `SYS_001`

**TC-FIN-005-03: 幂等性测试**
- **Given**: 充值申请 R3 状态已为 `completed`
- **When**: 客户端重试调用 `confirm_completed`
- **Then**:
  - 返回 HTTP 200
  - `ledger_entries` 无重复记录
  - 日志记录 "充值申请 R3 已确认,跳过重复操作"

**TC-FIN-005-04: 并发冲突测试**
- **Given**: 两个财务人员 Carol1, Carol2 同时确认同一充值申请 R4
- **When**: 并发调用 `confirm_completed`
- **Then**:
  - 其中一个请求成功,另一个因状态检查失败而拒绝
  - `ledger_entries` 仅写入一次
  - 使用数据库行锁 (`SELECT FOR UPDATE`) 防止并发

---

## 附录

### A. 相关文档

- `DATA_SCHEMA.md` - 数据结构定义
- `ERROR_CODES.md` - 错误码清单
- `STATE_MACHINE.md` - 充值状态机
- `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md` - 核心开发手册

### B. 变更历史

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2025-11-20 | 初始版本,包含 BR-FIN-001~005 | 系统架构团队 |

---

**END OF DOCUMENT**
