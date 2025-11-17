# API 开发流程规范

> **文档版本**: v7.0
> **文档类型**: 项目强制规范（SoT）
> **适用范围**: 所有后端API开发
> **规范级别**: 🔴 强制执行
> **AI工具兼容**: Claude Code / Cursor / GitHub Copilot

---

## ⚠️ 核心约束与真相源

### 唯一真相源（强制依赖）
- **数据定义**: [`docs/core/DATA_SCHEMA.md`](./DATA_SCHEMA.md) - 表结构、字段、类型的唯一来源
- **系统规范**: [`docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md`](./AI_AD_SYSTEM_MAIN_DOCUMENT.md) - 角色、权限、业务流程的唯一来源
- **状态机定义**: [`docs/core/STATE_MACHINE.md`](./STATE_MACHINE.md) - 业务状态流转的唯一来源
- **模块规划**: `docs/modules/{{MODULE_NAME}}/API_GUIDE.md` - 具体模块的API设计文档

### 五个不可违背的规则
1. **数据库字段禁止自创** - 所有字段必须在 DATA_SCHEMA.md 中定义
2. **角色限定为5个** - `admin`/`finance`/`data_operator`/`account_manager`/`media_buyer`
3. **响应必须使用 Envelope** - 使用 `success_response`/`error_response`
4. **前端必须通过 apiFetch** - 禁止直接 fetch 或其他 HTTP 库
5. **开发顺序强制执行** - Schema → Service → Router → Test → Exception Handler

---

## 🤖 AI 工具开发指导

### Claude Code / Cursor 推荐 Prompt 模板

#### 创建新API时的标准Prompt
```markdown
基于以下规范创建 {{模块名}} 模块的 {{功能}} API：

1. 数据定义参考：docs/core/DATA_SCHEMA.md 中的 {{表名}} 表
2. 状态机定义：docs/core/STATE_MACHINE.md 中的 {{状态机名称}}
3. 权限要求：{{角色列表}} 可以执行此操作

具体需求：
- 功能描述：{{功能描述}}
- 输入参数：{{参数列表}}
- 业务规则：{{业务规则}}
- 状态转换：{{from_status}} → {{to_status}}

请按照以下顺序生成代码：
1. Schema定义（backend/schemas/{{module}}.py）
2. Service实现（backend/services/{{module}}_service.py）
3. Router接口（backend/routers/{{module}}.py）
4. 异常处理器（backend/core/exception_handlers.py 中添加）
5. 测试用例（backend/tests/test_{{module}}_api.py）

注意事项：
- 严格使用 DATA_SCHEMA.md 中的字段名
- 使用项目定义的5个角色
- 金额用 Decimal，时间用 datetime
- 响应使用 success_response/error_response
- 状态转换必须符合 STATE_MACHINE.md 定义
```

#### 修复Bug时的标准Prompt
```markdown
修复 {{模块名}} 模块的 {{问题描述}}：

错误信息：
{{错误日志或堆栈}}

相关文件：
- 模型定义：backend/models/{{model}}.py
- 服务实现：backend/services/{{service}}.py
- 路由定义：backend/routers/{{router}}.py

请检查：
1. 字段名是否与 DATA_SCHEMA.md 一致
2. 角色是否使用标准5个角色之一
3. 状态转换是否符合 STATE_MACHINE.md
4. 是否正确处理了异常

修复要求：
- 保持现有API接口不变
- 添加适当的错误处理
- 更新相关测试用例
```

### AI工具配置文件示例

#### .cursorrules (Cursor配置)
```yaml
project_rules:
  - file: docs/core/API_DEVELOPMENT_FLOW.md
    enforce: always
  - file: docs/core/DATA_SCHEMA.md
    reference: database_fields
  - file: docs/core/STATE_MACHINE.md
    reference: state_transitions

code_generation:
  - always_use: "success_response, error_response"
  - never_use: "direct return dict"
  - decimal_for: "all money fields"
  - roles: ["admin", "finance", "data_operator", "account_manager", "media_buyer"]
```

#### .claude/project-rules.md (Claude Code配置)
```markdown
# 项目规则

## 必须遵循的文档
- API开发流程：docs/core/API_DEVELOPMENT_FLOW.md
- 数据库定义：docs/core/DATA_SCHEMA.md
- 状态机定义：docs/core/STATE_MACHINE.md

## 代码生成规则
1. 所有API响应使用 Envelope 格式
2. 金额字段使用 Decimal 类型
3. 前端调用使用 apiFetch
4. 角色限定为5个标准角色
5. 状态转换严格遵循状态机定义
```

---

## 📋 开发步骤（强制流程）

### Step 1: 确认需求与文档（10分钟）

#### 必须查阅的文档
```bash
# 1. 查看表结构定义
grep -A 50 "{{table_name}}" docs/core/DATA_SCHEMA.md

# 2. 查看状态机定义
grep -A 30 "{{state_machine_name}}" docs/core/STATE_MACHINE.md

# 3. 查看权限矩阵
grep -A 20 "权限矩阵" docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md

# 4. 查看模块API规划（如果存在）
cat docs/modules/{{module_name}}/API_GUIDE.md
```

#### 实际示例：充值模块
```bash
# 查看充值申请表结构
grep -A 50 "topup_requests" docs/core/DATA_SCHEMA.md

# 查看充值状态机
grep -A 30 "充值申请状态机" docs/core/STATE_MACHINE.md
# 输出：draft → pending → approved/rejected/cancelled

# 查看充值权限
grep -A 20 "充值管理" docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md
# 输出：创建(media_buyer,finance,admin) 审批(finance)
```

### Step 2: Schema 层实现（15分钟）

#### 标准实现（引用STATE_MACHINE.md）
```python
# backend/schemas/topup.py
from pydantic import BaseModel, Field, ConfigDict, field_validator
from decimal import Decimal
from typing import Optional, Literal
from datetime import datetime

# 状态定义来自 STATE_MACHINE.md - 充值申请状态机
TOPUP_STATUS = Literal["draft", "pending", "approved", "rejected", "cancelled"]

class TopupRequestCreate(BaseModel):
    """创建充值申请 - 基于 DATA_SCHEMA.md topup_requests表"""
    model_config = ConfigDict(from_attributes=True)

    # 字段严格对应 DATA_SCHEMA.md 定义
    project_id: int = Field(..., description="项目ID - 外键projects.id")
    ad_account_id: int = Field(..., description="广告账户ID - 外键ad_accounts.id")
    requested_amount: Decimal = Field(
        ...,
        ge=100,  # 业务规则：最小100元
        le=1000000,  # 业务规则：单笔上限100万
        description="申请金额 - DECIMAL(15,2)"
    )
    reason: str = Field(..., min_length=10, max_length=500)

class TopupStatusTransition(BaseModel):
    """状态转换 - 基于 STATE_MACHINE.md 充值申请状态机"""
    from_status: TOPUP_STATUS
    to_status: TOPUP_STATUS

    @field_validator('to_status')
    def validate_transition(cls, v, values):
        """验证状态转换合法性 - 参考 STATE_MACHINE.md"""
        transitions = {
            "draft": ["pending", "cancelled"],
            "pending": ["approved", "rejected"],
            "approved": [],  # 终态
            "rejected": [],  # 终态
            "cancelled": []  # 终态
        }
        from_status = values.get('from_status')
        if from_status and v not in transitions.get(from_status, []):
            raise ValueError(f"非法状态转换: {from_status} → {v}")
        return v
```

### Step 3: Service 层实现（30分钟）

#### 包含状态机验证的Service
```python
# backend/services/topup_service.py
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.topup import TopupRequest
from backend.schemas.topup import TopupRequestCreate, TopupStatusTransition
from backend.core.exceptions import BusinessError, PermissionError, StateTransitionError
from backend.core.error_codes import ErrorCode

class TopupService:
    """充值服务 - 实现 STATE_MACHINE.md 定义的充值申请状态机"""

    # 状态转换规则（来自 STATE_MACHINE.md）
    STATE_TRANSITIONS = {
        "draft": {
            "pending": "submit_request",  # 提交申请
            "cancelled": "cancel_draft"    # 取消草稿
        },
        "pending": {
            "approved": "approve_request",  # 审批通过
            "rejected": "reject_request"    # 审批拒绝
        },
        "approved": {},  # 终态，不可转换
        "rejected": {},  # 终态，不可转换
        "cancelled": {} # 终态，不可转换
    }

    # 状态转换权限（来自 AI_AD_SYSTEM_MAIN_DOCUMENT.md）
    TRANSITION_PERMISSIONS = {
        "submit_request": ["media_buyer", "admin"],  # 提交权限
        "approve_request": ["finance"],              # 审批权限
        "reject_request": ["finance"],               # 拒绝权限
        "cancel_draft": ["media_buyer", "admin"]     # 取消权限
    }

    def __init__(self, db: Session):
        self.db = db

    def validate_state_transition(
        self,
        from_status: str,
        to_status: str,
        user_role: str
    ) -> str:
        """
        验证状态转换合法性
        返回转换方法名称
        """
        # 检查转换路径是否存在
        transitions = self.STATE_TRANSITIONS.get(from_status, {})
        if to_status not in transitions:
            raise StateTransitionError(
                f"状态转换非法: {from_status} → {to_status}，"
                f"请参考 STATE_MACHINE.md 充值申请状态机"
            )

        # 获取转换方法
        method_name = transitions[to_status]

        # 检查权限
        allowed_roles = self.TRANSITION_PERMISSIONS.get(method_name, [])
        if user_role not in allowed_roles:
            raise PermissionError(
                code=ErrorCode.AUTH_002,
                message=f"角色 {user_role} 无权执行 {from_status} → {to_status} 转换"
            )

        return method_name

    def create_request(
        self,
        data: TopupRequestCreate,
        current_user_id: int,
        current_user_role: str
    ) -> TopupRequest:
        """创建充值申请（初始状态：draft）"""

        # 权限检查（基于 AI_AD_SYSTEM_MAIN_DOCUMENT.md）
        if current_user_role not in ['admin', 'finance', 'media_buyer']:
            raise PermissionError(
                code=ErrorCode.AUTH_002,
                message="无权限创建充值申请"
            )

        # 创建申请，初始状态为 draft（STATE_MACHINE.md 定义）
        topup = TopupRequest(
            **data.model_dump(),
            status='draft',  # 初始状态
            created_by=current_user_id,
            created_at=datetime.utcnow()
        )

        self.db.add(topup)
        self.db.commit()
        self.db.refresh(topup)

        return topup

    def transition_status(
        self,
        request_id: int,
        to_status: str,
        current_user_id: int,
        current_user_role: str,
        **kwargs
    ) -> TopupRequest:
        """
        通用状态转换方法
        基于 STATE_MACHINE.md 定义的状态机执行转换
        """
        topup = self.db.query(TopupRequest).filter_by(id=request_id).first()

        if not topup:
            raise BusinessError(ErrorCode.BIZ_002, "充值申请不存在")

        # 验证状态转换
        method_name = self.validate_state_transition(
            topup.status,
            to_status,
            current_user_role
        )

        # 执行具体的转换方法
        transition_method = getattr(self, f"_{method_name}")
        return transition_method(topup, current_user_id, **kwargs)

    def _submit_request(self, topup: TopupRequest, user_id: int, **kwargs):
        """提交申请: draft → pending"""
        topup.status = 'pending'
        topup.submitted_at = datetime.utcnow()
        topup.submitted_by = user_id

        self.db.commit()
        self.db.refresh(topup)
        return topup

    def _approve_request(self, topup: TopupRequest, user_id: int, **kwargs):
        """审批通过: pending → approved"""
        actual_amount = kwargs.get('actual_amount')
        if not actual_amount:
            raise BusinessError(ErrorCode.BIZ_001, "请提供实际充值金额")

        topup.status = 'approved'
        topup.actual_amount = actual_amount
        topup.approved_by = user_id
        topup.approved_at = datetime.utcnow()

        # TODO: 触发实际充值流程

        self.db.commit()
        self.db.refresh(topup)
        return topup

    def _reject_request(self, topup: TopupRequest, user_id: int, **kwargs):
        """审批拒绝: pending → rejected"""
        rejection_reason = kwargs.get('rejection_reason')
        if not rejection_reason:
            raise BusinessError(ErrorCode.BIZ_001, "请提供拒绝原因")

        topup.status = 'rejected'
        topup.rejection_reason = rejection_reason
        topup.rejected_by = user_id
        topup.rejected_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(topup)
        return topup
```

### Step 4: Router 层实现（20分钟）

```python
# backend/routers/topups.py
from fastapi import APIRouter, Depends, Query, Body, Request
from typing import Dict, Any
from backend.core.dependencies import get_db, get_current_user, require_role
from backend.core.response import success_response, error_response
from backend.services.topup_service import TopupService
from backend.schemas.topup import TopupRequestCreate, TopupRequestResponse
from backend.models.users import User
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/topup-requests", tags=["充值管理"])

@router.post("", summary="创建充值申请")
async def create_topup_request(
    request: TopupRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建充值申请（初始状态为draft）"""
    service = TopupService(db)
    result = service.create_request(
        data=request,
        current_user_id=current_user.id,
        current_user_role=current_user.role
    )

    return success_response(
        data=TopupRequestResponse.model_validate(result),
        message="充值申请已创建"
    )

@router.post("/{request_id}/transition", summary="状态转换")
async def transition_status(
    request: Request,
    request_id: int,
    body: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    通用状态转换接口
    基于 STATE_MACHINE.md 定义的状态机规则
    """
    to_status = body.pop('to_status')

    service = TopupService(db)
    result = service.transition_status(
        request_id=request_id,
        to_status=to_status,
        current_user_id=current_user.id,
        current_user_role=current_user.role,
        **body  # 传递其他参数
    )

    return success_response(
        data=TopupRequestResponse.model_validate(result),
        message=f"状态已转换为 {to_status}"
    )
```

### Step 5: 全局异常处理器（10分钟）

```python
# backend/core/exception_handlers.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from backend.core.exceptions import (
    BusinessError,
    PermissionError,
    StateTransitionError,
    ValidationError
)
from backend.core.response import error_response
from backend.core.config import settings
import traceback
import logging

logger = logging.getLogger(__name__)

async def business_exception_handler(request: Request, exc: BusinessError):
    """业务异常处理器"""
    logger.warning(f"Business error: {exc.message}", extra={
        "path": request.url.path,
        "method": request.method,
        "error_code": exc.code
    })

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response(
            code=exc.code,
            message=exc.message,
            details=exc.details
        )
    )

async def permission_exception_handler(request: Request, exc: PermissionError):
    """权限异常处理器"""
    logger.warning(f"Permission denied: {exc.message}", extra={
        "path": request.url.path,
        "method": request.method,
        "user_id": request.state.user_id if hasattr(request.state, 'user_id') else None
    })

    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=error_response(
            code=exc.code,
            message=exc.message
        )
    )

async def state_transition_exception_handler(request: Request, exc: StateTransitionError):
    """状态转换异常处理器"""
    logger.error(f"State transition error: {exc.message}", extra={
        "path": request.url.path,
        "method": request.method,
        "transition": exc.transition_info
    })

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_response(
            code="BIZ_003",
            message=exc.message,
            details={
                "transition": exc.transition_info,
                "help": "请查阅 STATE_MACHINE.md 了解合法的状态转换"
            }
        )
    )

async def validation_exception_handler(request: Request, exc: ValidationError):
    """参数验证异常处理器"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response(
            code="VALIDATION_001",
            message="参数验证失败",
            details=exc.errors()
        )
    )

async def generic_exception_handler(request: Request, exc: Exception):
    """通用异常处理器（兜底）"""
    logger.error(f"Unhandled exception: {str(exc)}", extra={
        "path": request.url.path,
        "method": request.method,
        "traceback": traceback.format_exc()
    })

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response(
            code="SYS_001",
            message="系统内部错误",
            details={"error": str(exc)} if settings.DEBUG else None
        )
    )

def register_exception_handlers(app):
    """注册所有异常处理器到FastAPI应用"""
    app.add_exception_handler(BusinessError, business_exception_handler)
    app.add_exception_handler(PermissionError, permission_exception_handler)
    app.add_exception_handler(StateTransitionError, state_transition_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
```

#### 在main.py中注册
```python
# backend/main.py
from fastapi import FastAPI
from backend.core.exception_handlers import register_exception_handlers

app = FastAPI(title="AI广告代投系统")

# 注册全局异常处理器
register_exception_handlers(app)
```

### Step 6: 测试编写（30分钟）

```python
# backend/tests/test_topup_api.py
import pytest
from httpx import AsyncClient
from decimal import Decimal

class TestTopupAPI:
    """充值申请API测试 - 覆盖STATE_MACHINE.md定义的所有状态转换"""

    @pytest.fixture
    def valid_topup_data(self):
        """有效的充值申请数据"""
        return {
            "project_id": 1,
            "ad_account_id": 1,
            "requested_amount": "10000.00",
            "reason": "Facebook广告账户余额不足，需要补充推广预算"
        }

    async def test_state_machine_workflow(
        self,
        client: AsyncClient,
        media_buyer_token: str,
        finance_token: str,
        valid_topup_data: dict
    ):
        """✅ 测试完整状态机流程: draft → pending → approved"""
        # 1. 创建草稿 (初始状态: draft)
        response = await client.post(
            "/api/v1/topup-requests",
            json=valid_topup_data,
            headers={"Authorization": f"Bearer {media_buyer_token}"}
        )
        assert response.status_code == 200
        draft = response.json()["data"]
        assert draft["status"] == "draft"

        # 2. 提交申请 (draft → pending)
        response = await client.post(
            f"/api/v1/topup-requests/{draft['id']}/transition",
            json={"to_status": "pending"},
            headers={"Authorization": f"Bearer {media_buyer_token}"}
        )
        assert response.status_code == 200
        pending = response.json()["data"]
        assert pending["status"] == "pending"

        # 3. 审批通过 (pending → approved)
        response = await client.post(
            f"/api/v1/topup-requests/{draft['id']}/transition",
            json={
                "to_status": "approved",
                "actual_amount": "9500.00"
            },
            headers={"Authorization": f"Bearer {finance_token}"}
        )
        assert response.status_code == 200
        approved = response.json()["data"]
        assert approved["status"] == "approved"
        assert approved["actual_amount"] == "9500.00"

    async def test_invalid_state_transition(
        self,
        client: AsyncClient,
        finance_token: str,
        approved_topup_id: int
    ):
        """✅ 测试非法状态转换 (违反STATE_MACHINE.md)"""
        # 尝试从approved转回pending（非法）
        response = await client.post(
            f"/api/v1/topup-requests/{approved_topup_id}/transition",
            json={"to_status": "pending"},
            headers={"Authorization": f"Bearer {finance_token}"}
        )
        assert response.status_code == 400
        error = response.json()["error"]
        assert error["code"] == "BIZ_003"
        assert "STATE_MACHINE.md" in error["details"]["help"]

    async def test_permission_on_state_transition(
        self,
        client: AsyncClient,
        media_buyer_token: str,
        pending_topup_id: int
    ):
        """✅ 测试状态转换权限 (基于AI_AD_SYSTEM_MAIN_DOCUMENT.md)"""
        # media_buyer尝试审批（无权限）
        response = await client.post(
            f"/api/v1/topup-requests/{pending_topup_id}/transition",
            json={
                "to_status": "approved",
                "actual_amount": "5000.00"
            },
            headers={"Authorization": f"Bearer {media_buyer_token}"}
        )
        assert response.status_code == 403
        error = response.json()["error"]
        assert error["code"] == "AUTH_002"
```

---

## 🔴 强制检查清单（每次提交前必须完成）

### 代码检查
```markdown
## 数据一致性
[ ] 表名与 DATA_SCHEMA.md 完全一致
[ ] 字段名与 DATA_SCHEMA.md 完全一致
[ ] 数据类型正确（Decimal for money, datetime for time）

## 状态机合规
[ ] 初始状态来自 STATE_MACHINE.md
[ ] 状态转换路径符合 STATE_MACHINE.md
[ ] 终态不可再转换

## 权限控制
[ ] 使用标准5个角色
[ ] 权限矩阵与 AI_AD_SYSTEM_MAIN_DOCUMENT.md 一致
[ ] Service层有权限验证

## 异常处理
[ ] 业务异常使用 BusinessError
[ ] 权限异常使用 PermissionError
[ ] 状态异常使用 StateTransitionError
[ ] 已注册全局异常处理器

## API规范
[ ] 使用 success_response/error_response
[ ] 包含完整的 Envelope 字段
[ ] 错误码来自 core.error_codes
[ ] 分页响应包含 meta.pagination

## 测试覆盖
[ ] 正常流程测试
[ ] 状态转换测试
[ ] 权限验证测试
[ ] 异常处理测试
[ ] 边界条件测试
```

### 提交前命令
```bash
# 1. 格式检查
black backend/
isort backend/

# 2. 类型检查
mypy backend/

# 3. 运行测试
pytest backend/tests/ -v

# 4. 检查覆盖率
pytest --cov=backend --cov-report=html

# 5. 安全检查
bandit -r backend/
```

---

## 🚫 常见违规及AI纠正指导

### 违规类型与纠正

| 违规类型 | 错误示例 | 正确示例 | AI纠正Prompt |
|---------|---------|---------|-------------|
| **字段自创** | `topup_amount` | `requested_amount` | "请使用 DATA_SCHEMA.md 中 topup_requests 表的准确字段名" |
| **角色错误** | `manager` | `account_manager` | "角色必须是: admin/finance/data_operator/account_manager/media_buyer" |
| **状态自创** | `processing` | `pending` | "请参考 STATE_MACHINE.md 中的充值申请状态机" |
| **直接返回** | `return {"data": ...}` | `return success_response(...)` | "使用 backend.core.response 的 success_response/error_response" |
| **Float金额** | `amount: float` | `amount: Decimal` | "所有金额字段必须使用 Decimal 类型" |

### AI工具调试技巧

#### 当AI生成错误代码时
```markdown
你生成的代码有以下问题：
1. 字段名 {{field}} 不存在，请查看 DATA_SCHEMA.md 的 {{table}} 表
2. 状态 {{status}} 不合法，请查看 STATE_MACHINE.md 的 {{state_machine}} 定义
3. 角色 {{role}} 不存在，标准角色只有5个

请重新生成，严格遵循：
- docs/core/DATA_SCHEMA.md
- docs/core/STATE_MACHINE.md
- docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md
```

---

## 📚 真实模块文档引用

### 充值模块完整示例
- 表定义: `DATA_SCHEMA.md#topup_requests`
- 状态机: `STATE_MACHINE.md#充值申请状态机`
- 权限矩阵: `AI_AD_SYSTEM_MAIN_DOCUMENT.md#充值管理权限`
- API设计: `docs/modules/topup/API_GUIDE.md`

### 日报模块完整示例
- 表定义: `DATA_SCHEMA.md#daily_reports`
- 状态机: `STATE_MACHINE.md#日报状态机`
- 权限矩阵: `AI_AD_SYSTEM_MAIN_DOCUMENT.md#日报管理权限`
- API设计: `docs/modules/daily_report/API_GUIDE.md`

### 项目模块完整示例
- 表定义: `DATA_SCHEMA.md#projects`
- 状态机: `STATE_MACHINE.md#项目状态机`
- 权限矩阵: `AI_AD_SYSTEM_MAIN_DOCUMENT.md#项目管理权限`
- API设计: `docs/modules/project/API_GUIDE.md`

---

## 🔧 快速参考卡片

### 核心常量定义
```python
# 5个标准角色
VALID_ROLES = ["admin", "finance", "data_operator", "account_manager", "media_buyer"]

# 6个核心表
CORE_TABLES = ["users", "projects", "ad_accounts", "daily_reports", "topup_requests", "reconciliations"]

# 错误码前缀
ERROR_PREFIXES = {
    "AUTH_": "认证授权（401/403）",
    "BIZ_": "业务逻辑（400/404）",
    "SYS_": "系统错误（500）",
    "VALIDATION_": "参数验证（422）"
}
```

### 状态机快查（STATE_MACHINE.md摘要）
```yaml
充值申请: draft → pending → approved/rejected/cancelled
日报: draft → submitted → approved/rejected
项目: draft → active → paused → completed → archived
账户: pending → active → disabled → banned
对账: processing → completed → confirmed → disputed
```

### 权限矩阵快查（AI_AD_SYSTEM_MAIN_DOCUMENT.md摘要）
```yaml
admin: 全部权限
finance: 财务审批、对账、报表
data_operator: 日报审核、数据管理
account_manager: 项目管理、账户分配
media_buyer: 日报提交、充值申请
```

---

## 📊 统一响应格式（Envelope）

### 成功响应
```json
{
  "success": true,
  "data": {
    "id": 1,
    "status": "pending",
    "requested_amount": "10000.00"
  },
  "message": "操作成功",
  "code": "SUCCESS",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-17T10:00:00Z"
}
```

### 错误响应
```json
{
  "success": false,
  "error": {
    "code": "BIZ_003",
    "message": "状态转换非法",
    "details": {
      "from": "approved",
      "to": "pending",
      "help": "请查阅 STATE_MACHINE.md 了解合法的状态转换"
    }
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2025-11-17T10:00:00Z"
}
```

### 分页响应
```json
{
  "success": true,
  "data": {
    "items": [...],
    "meta": {
      "pagination": {
        "page": 1,
        "page_size": 20,
        "total": 100,
        "total_pages": 5,
        "has_next": true,
        "has_prev": false
      }
    }
  },
  "message": "查询成功",
  "code": "SUCCESS"
}
```

---

## 🔗 相关文档链接

### 核心规范（强制阅读）
1. **[DATA_SCHEMA.md](./DATA_SCHEMA.md)** - 数据库定义
2. **[STATE_MACHINE.md](./STATE_MACHINE.md)** - 状态机定义
3. **[AI_AD_SYSTEM_MAIN_DOCUMENT.md](./AI_AD_SYSTEM_MAIN_DOCUMENT.md)** - 系统总规范

### 模块设计（按需阅读）
- `docs/modules/topup/` - 充值模块
- `docs/modules/daily_report/` - 日报模块
- `docs/modules/project/` - 项目模块
- `docs/modules/reconciliation/` - 对账模块

### 开发工具
- `scripts/check_compliance.py` - 合规性检查脚本
- `scripts/generate_api.py` - API代码生成器
- `.github/workflows/api_check.yml` - CI检查配置

---

**文档性质**: 项目强制规范
**执行级别**: 🔴 必须严格遵守
**违规处理**: PR自动拒绝 / 代码回滚
**最后更新**: 2025-11-17
**版本**: v7.0

**v7.0 更新说明**:
- 新增 AI 工具专用 Prompt 模板
- 新增全局异常处理器示例
- 强化 STATE_MACHINE.md 引用
- 添加真实模块文档路径
- 优化 AI 纠错指导