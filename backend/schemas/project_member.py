"""
项目成员管理 Pydantic Schemas

支持的角色 (MASTER.md v4.4 §2.4):
- owner: 项目负责人 (每项目最多1个)
- member: 普通成员
- viewer: 只读查看者

SoT Reference: MASTER.md v4.4 §2.4, STATE_MACHINE.md v2.6
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict, field_validator


class ProjectMemberRole(str, Enum):
    """项目成员角色枚举"""
    OWNER = "owner"      # 项目负责人
    MEMBER = "member"    # 普通成员
    VIEWER = "viewer"    # 只读查看者


# ==================== 请求 Schemas ====================

class ProjectMemberCreateRequest(BaseModel):
    """创建项目成员请求"""
    model_config = ConfigDict(from_attributes=True)

    project_id: int = Field(..., gt=0, description="项目ID")
    user_id: UUID = Field(..., description="用户ID (UUID)")
    role: ProjectMemberRole = Field(
        default=ProjectMemberRole.MEMBER,
        description="项目内角色: owner/member/viewer"
    )
    permissions: Optional[Dict[str, Any]] = Field(
        None,
        description="扩展权限配置 (JSON)"
    )
    notes: Optional[str] = Field(None, max_length=500, description="备注")

    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        if isinstance(v, str):
            try:
                return ProjectMemberRole(v)
            except ValueError:
                raise ValueError(f"无效角色: {v}. 有效值: owner, member, viewer")
        return v


class ProjectMemberUpdateRequest(BaseModel):
    """更新项目成员请求"""
    model_config = ConfigDict(from_attributes=True)

    role: Optional[ProjectMemberRole] = Field(
        None,
        description="项目内角色: owner/member/viewer"
    )
    permissions: Optional[Dict[str, Any]] = Field(
        None,
        description="扩展权限配置 (JSON)"
    )
    notes: Optional[str] = Field(None, max_length=500, description="备注")


class TransferOwnershipRequest(BaseModel):
    """转移项目负责人请求"""
    model_config = ConfigDict(from_attributes=True)

    new_owner_user_id: UUID = Field(..., description="新负责人用户ID")
    demote_current_to: ProjectMemberRole = Field(
        default=ProjectMemberRole.MEMBER,
        description="当前负责人降级为的角色 (member/viewer)"
    )

    @field_validator('demote_current_to')
    @classmethod
    def validate_demote_role(cls, v):
        if v == ProjectMemberRole.OWNER:
            raise ValueError("不能将当前负责人降级为 owner")
        return v


class BatchAddMembersRequest(BaseModel):
    """批量添加成员请求"""
    model_config = ConfigDict(from_attributes=True)

    members: List['ProjectMemberCreateRequest'] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="成员列表 (最多50个)"
    )


# ==================== 响应 Schemas ====================

class ProjectMemberResponse(BaseModel):
    """项目成员响应"""
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="成员关系ID")
    project_id: int = Field(..., description="项目ID")
    user_id: str = Field(..., description="用户ID (UUID字符串)")
    role: str = Field(..., description="项目内角色")
    permissions: Optional[Dict[str, Any]] = Field(None, description="扩展权限")
    notes: Optional[str] = Field(None, description="备注")
    created_at: datetime = Field(..., description="加入时间")
    updated_at: datetime = Field(..., description="更新时间")

    # 关联用户信息
    user_name: Optional[str] = Field(None, description="用户名")
    user_email: Optional[str] = Field(None, description="用户邮箱")
    user_role: Optional[str] = Field(None, description="用户全局角色")

    # 关联项目信息
    project_name: Optional[str] = Field(None, description="项目名称")


class ProjectMemberDetailResponse(ProjectMemberResponse):
    """项目成员详情响应 (含完整关联信息)"""

    # 额外的用户信息
    user_avatar: Optional[str] = Field(None, description="用户头像URL")
    user_phone: Optional[str] = Field(None, description="用户电话")

    # 额外的项目信息
    project_status: Optional[str] = Field(None, description="项目状态")
    project_client_name: Optional[str] = Field(None, description="项目客户名")

    # 计算字段
    is_owner: bool = Field(False, description="是否为项目负责人")
    can_edit: bool = Field(False, description="是否可编辑项目")


class ProjectMemberListResponse(BaseModel):
    """项目成员列表响应"""
    items: List[ProjectMemberResponse]
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="分页元数据"
    )


class UserProjectsResponse(BaseModel):
    """用户参与的项目列表响应"""
    items: List[ProjectMemberResponse]
    total: int = Field(..., description="总数")


class TransferOwnershipResponse(BaseModel):
    """转移负责人响应"""
    success: bool = Field(..., description="是否成功")
    previous_owner: Optional[ProjectMemberResponse] = Field(
        None,
        description="原负责人信息"
    )
    new_owner: ProjectMemberResponse = Field(..., description="新负责人信息")
    message: str = Field(..., description="操作消息")


class BatchAddMembersResponse(BaseModel):
    """批量添加成员响应"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    members: List[ProjectMemberResponse] = Field(
        default_factory=list,
        description="成功添加的成员"
    )
    errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="失败详情"
    )
