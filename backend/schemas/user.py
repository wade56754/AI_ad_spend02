"""
用户管理 Schema 定义 (重构版)

SoT References:
- API_SOT.md v9.3 §5 Users API
- DATA_SCHEMA.md v5.6 §3.1.1 users 表
- MASTER.md v4.6 §2.4 (6角色模型)
- BUSINESS_RULES.md BR-USER-001, BR-USER-002
- ERROR_CODES_SOT.md v2.1 (错误码)

依赖代码块:
- pagination: PaginationMeta
- response-envelope: 标准响应格式

Version: 2.2
Author: Claude Code

v2.2 更新 (2025-12):
- 移除 supervisor 角色 (PRD v5.1 废弃，职责合并到 project_owner)
- 更新 SoT 引用到 MASTER.md v4.6

v2.1 更新 (2025-12):
- 新增 team_id 字段：投手直接归属团队
- 新增 team_name 响应字段：便于前端展示
"""
from datetime import datetime
from typing import Optional, List, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator

# 角色枚举 - 严格对应 MASTER.md v4.6 §2.4 (6角色模型)
# PRD v5.1: supervisor 已废弃，职责合并到 project_owner
RoleType = Literal[
    "ceo",             # 老板 - 资金安全、公司盈亏、最终决策
    "project_owner",   # 项目负责人 - 项目盈亏、资金使用效率、日报审核
    "finance",         # 财务 - 资金出入准确、数据真实、对账
    "pitcher",         # 投手 - CPL 达标、日报准确、执行投放
    "account_manager", # 户管 - 账户分配、账户状态监控
    "admin"            # 管理员 - 系统配置（不参与业务）
]

# 合法角色列表 (MASTER.md v4.6 §2.4) - 6角色模型
# 注意: supervisor 已废弃 (PRD v5.1)，请勿添加
VALID_ROLES = ["ceo", "project_owner", "finance", "pitcher", "account_manager", "admin"]


class UserBase(BaseModel):
    """用户基础字段"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    role: RoleType = Field(..., description="用户角色")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    team_id: Optional[UUID] = Field(None, description="所属团队ID (v2.1)")
    is_active: bool = Field(default=True, description="账号是否激活")

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """验证角色是否合法 - BR-USER-003"""
        if v not in VALID_ROLES:
            raise ValueError(f"无效的角色: {v}，合法角色: {VALID_ROLES}")
        return v


class UserCreate(UserBase):
    """
    创建用户请求 Schema

    POST /api/v1/users
    权限: admin
    """
    model_config = ConfigDict(from_attributes=True)

    password: str = Field(..., min_length=8, max_length=128, description="用户密码")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError("密码长度不能少于8位")
        return v


class UserUpdate(BaseModel):
    """
    更新用户请求 Schema

    PUT /api/v1/users/{user_id}
    权限: admin
    """
    model_config = ConfigDict(from_attributes=True)

    username: Optional[str] = Field(None, min_length=2, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    role: Optional[RoleType] = Field(None, description="用户角色")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    team_id: Optional[UUID] = Field(None, description="所属团队ID (v2.1)")
    is_active: Optional[bool] = Field(None, description="账号是否激活")
    password: Optional[str] = Field(None, min_length=8, max_length=128, description="新密码")

    @field_validator('role')
    @classmethod
    def validate_role(cls, v: Optional[str]) -> Optional[str]:
        """验证角色是否合法"""
        if v is not None and v not in VALID_ROLES:
            raise ValueError(f"无效的角色: {v}，合法角色: {VALID_ROLES}")
        return v


class UserResponse(BaseModel):
    """
    用户响应 Schema

    对应 API_SOT.md §5.3 Response Schema
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, description="真实姓名")
    role: str = Field(..., description="角色")
    department: Optional[str] = Field(None, description="部门")
    team_id: Optional[UUID] = Field(None, description="所属团队ID (v2.1)")
    team_name: Optional[str] = Field(None, description="所属团队名称 (v2.1)")
    is_active: bool = Field(..., description="账号是否激活")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")


class UserListResponse(BaseModel):
    """用户列表项响应 - 精简版"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    full_name: Optional[str] = None
    email: str
    role: str
    department: Optional[str] = None
    team_id: Optional[UUID] = None  # v2.1
    team_name: Optional[str] = None  # v2.1
    is_active: bool
    created_at: datetime


class UserListQueryParams(BaseModel):
    """
    用户列表查询参数

    GET /api/v1/users?page=1&page_size=20&role=media_buyer&is_active=true&team_id=xxx
    """
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")
    role: Optional[RoleType] = Field(None, description="角色过滤")
    team_id: Optional[UUID] = Field(None, description="团队过滤 (v2.1)")
    is_active: Optional[bool] = Field(None, description="账号状态过滤")
    search: Optional[str] = Field(None, max_length=100, description="搜索用户名或姓名")


class PaginationMeta(BaseModel):
    """分页元数据"""
    page: int
    page_size: int
    total: int
    total_pages: int
    has_next: bool
    has_prev: bool


class UserListPaginatedResponse(BaseModel):
    """用户列表分页响应"""
    items: List[UserListResponse]
    meta: dict  # 包含 pagination
