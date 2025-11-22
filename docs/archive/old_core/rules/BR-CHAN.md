# BR-CHAN：渠道管理业务规则

**版本**: v2.0
**最后更新**: 2025-01-20
**负责模块**: 渠道管理 (channels)

---

## 规则总览

| 规则编号 | 规则名称 | 优先级 | 涉及角色 |
|---------|---------|--------|---------|
| BR-CHAN-001 | 渠道创建与唯一性约束 | P0 | admin, account_manager |

---

## BR-CHAN-001：渠道创建与唯一性约束

### 业务场景

管理员或客户经理创建新的广告投放渠道（如 Meta、Google Ads、TikTok 等），每个渠道必须具有**全局唯一**的渠道代码（`channel_code`），用于后续账户绑定和数据关联。

### 详细约束

#### 1.1 权限约束

- **Rule**: 仅 `admin` 和 `account_manager` 角色可以创建渠道
- **Error Code**: `AUTH_500` (PERMISSION_DENIED)
- **Schema Reference**: `DATA_SCHEMA.md → channels.created_by → users.id`

```python
# backend/routers/channels.py
@router.post("", response_model=ChannelResponse)
async def create_channel(
    payload: CreateChannelRequest,
    user=Depends(get_current_user),
    service: ChannelService = Depends()
):
    # 角色验证
    user_role = user.get("role")
    if user_role not in ["admin", "account_manager"]:
        raise AuthorizationException(
            code=AuthErrorCodes.PERMISSION_DENIED.code,  # AUTH_500
            message="仅管理员和客户经理可以创建渠道"
        )

    channel = service.create_channel(payload, user_id=user.get("user", {}).id)
    return envelope_response(data=channel)
```

#### 1.2 唯一性约束

- **Rule**: `channel_code` 必须全局唯一（不区分大小写）
- **Database Constraint**: `UNIQUE INDEX ON LOWER(channel_code)`
- **Error Code**: `BIZ_203` (DUPLICATE_ENTRY)
- **Schema**: `DATA_SCHEMA.md → channels.channel_code (VARCHAR(50) UNIQUE NOT NULL)`

```sql
-- 数据库约束（已在 DATA_SCHEMA.md 中定义）
CREATE TABLE channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel_code VARCHAR(50) UNIQUE NOT NULL,
    channel_name VARCHAR(100) NOT NULL,
    channel_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 唯一索引（不区分大小写）
CREATE UNIQUE INDEX idx_channels_code_lower ON channels (LOWER(channel_code));
```

```python
# backend/services/channel_service.py
from sqlalchemy.exc import IntegrityError

def create_channel(self, payload: CreateChannelRequest, user_id: UUID):
    # 预先检查重复
    existing = self.db.query(Channel).filter(
        func.lower(Channel.channel_code) == payload.channel_code.lower()
    ).first()

    if existing:
        raise BusinessRuleException(
            code=BusinessErrorCodes.DUPLICATE_ENTRY.code,  # BIZ_203
            message=f"渠道代码 '{payload.channel_code}' 已存在"
        )

    # 创建渠道
    channel = Channel(
        channel_code=payload.channel_code.upper(),  # 统一转大写存储
        channel_name=payload.channel_name,
        channel_type=payload.channel_type,
        status="active",  # 默认状态
        created_by=user_id
    )

    try:
        self.db.add(channel)
        self.db.flush()
    except IntegrityError as e:
        raise BusinessRuleException(
            code=BusinessErrorCodes.DUPLICATE_ENTRY.code,
            message=f"渠道代码重复或外键冲突: {str(e)}"
        )

    # 审计日志
    audit_log(
        operation="CREATE_CHANNEL",
        resource_type="channel",
        resource_id=channel.id,
        user_id=user_id,
        details={"channel_code": channel.channel_code, "channel_name": channel.channel_name}
    )

    return channel
```

#### 1.3 必填字段约束

- **channel_code**: 渠道代码（VARCHAR(50)，建议格式：`META`, `GOOGLE_ADS`, `TIKTOK`）
- **channel_name**: 渠道名称（VARCHAR(100)，如 "Meta 广告平台"）
- **channel_type**: 渠道类型（枚举值：`social_media`, `search_engine`, `e_commerce`, `other`）
- **Error Code**: `BIZ_200` (INVALID_INPUT)

```python
# backend/schemas/channel.py
from pydantic import BaseModel, Field, validator

class CreateChannelRequest(BaseModel):
    channel_code: str = Field(..., min_length=2, max_length=50, description="渠道代码")
    channel_name: str = Field(..., min_length=2, max_length=100, description="渠道名称")
    channel_type: str = Field(..., description="渠道类型")

    @validator("channel_type")
    def validate_channel_type(cls, v):
        ALLOWED_TYPES = ["social_media", "search_engine", "e_commerce", "other"]
        if v not in ALLOWED_TYPES:
            raise ValueError(f"channel_type 必须是以下之一: {ALLOWED_TYPES}")
        return v

    @validator("channel_code")
    def validate_channel_code(cls, v):
        # 仅允许字母、数字、下划线
        if not re.match(r'^[A-Z0-9_]+$', v.upper()):
            raise ValueError("channel_code 仅允许大写字母、数字和下划线")
        return v.upper()
```

#### 1.4 状态初始化

- **初始状态**: `active`（启用）
- **可选状态**: `active`, `inactive`, `archived`
- **State Machine Reference**: `STATE_MACHINE.md → channel`

```
active ↔ inactive → archived
```

```python
def update_channel_status(self, channel_id: UUID, target_status: str, user_id: UUID):
    channel = self.get_channel_by_id(channel_id)

    # 状态流转验证
    ensure_transition_allowed(
        resource_type="channel",
        current_status=channel.status,
        target_status=target_status
    )

    channel.status = target_status

    audit_log(
        operation="UPDATE_CHANNEL_STATUS",
        resource_type="channel",
        resource_id=channel_id,
        user_id=user_id,
        details={"from": channel.status, "to": target_status}
    )
```

#### 1.5 删除保护

- **Rule**: 若渠道下存在关联的广告账户（`ad_accounts.channel_id`），禁止删除
- **Error Code**: `BIZ_202` (INVALID_OPERATION)
- **Schema**: `DATA_SCHEMA.md → ad_accounts.channel_id REFERENCES channels(id) ON DELETE RESTRICT`

```python
def delete_channel(self, channel_id: UUID, user_id: UUID):
    channel = self.get_channel_by_id(channel_id)

    # 检查是否有关联的广告账户
    linked_accounts = self.db.query(AdAccount).filter(
        AdAccount.channel_id == channel_id
    ).count()

    if linked_accounts > 0:
        raise BusinessRuleException(
            code=BusinessErrorCodes.INVALID_OPERATION.code,  # BIZ_202
            message=f"渠道下还有 {linked_accounts} 个广告账户，无法删除"
        )

    # 软删除（更新状态为 archived）
    channel.status = "archived"

    audit_log(
        operation="DELETE_CHANNEL",
        resource_type="channel",
        resource_id=channel_id,
        user_id=user_id,
        details={"channel_code": channel.channel_code}
    )
```

### 错误码映射

| 场景 | 错误码 | HTTP状态码 |
|-----|--------|-----------|
| 非管理员/客户经理创建 | AUTH_500 | 403 |
| 渠道代码重复 | BIZ_203 | 409 |
| 必填字段缺失 | BIZ_200 | 400 |
| 渠道类型无效 | BIZ_200 | 400 |
| 有关联账户时删除 | BIZ_202 | 400 |
| 状态流转非法 | STATE_301 | 400 |

### Test Intent

```gherkin
Given 用户角色为 "admin"
When 创建渠道，channel_code="META", channel_name="Meta广告平台", channel_type="social_media"
Then 渠道创建成功，channel_code="META"，status="active"

Given 用户角色为 "media_buyer"
When 尝试创建渠道
Then 返回 403，错误码 AUTH_500

Given 已存在渠道 channel_code="GOOGLE_ADS"
When 创建新渠道 channel_code="google_ads"（小写）
Then 返回 409，错误码 BIZ_203（不区分大小写冲突）

Given 渠道 channel_id="xxx" 下有 3 个广告账户
When 删除该渠道
Then 返回 400，错误码 BIZ_202，message 包含 "还有 3 个广告账户"

Given 渠道 channel_id="xxx"，status="active"
When 更新 status="inactive"
Then 状态更新成功，audit_log 记录状态流转

Given 创建渠道时 channel_type="invalid_type"
When 提交请求
Then 返回 400，错误码 BIZ_200，message 包含 "channel_type 必须是以下之一"
```

---

## 参考文档

- **数据模型**: `DATA_SCHEMA.md → channels, ad_accounts`
- **状态机**: `STATE_MACHINE.md → channel`
- **错误码**: `ERROR_CODES.md → AUTH_500, BIZ_200, BIZ_202, BIZ_203, STATE_301`
- **核心开发手册**: `AI_AD_SYSTEM_MASTER_SPEC_v2.2.md → 第3章 渠道与账户管理`
