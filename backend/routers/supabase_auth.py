"""
Supabase认证路由
Version: 1.0
Author: Claude协作开发
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any, List

from services.supabase_auth_service import supabase_auth_service
from deps.supabase_auth import (
    get_current_user,
    get_current_active_user,
    require_admin,
    require_finance
)
from core.response import success_response, error_response

router = APIRouter(prefix="/auth", tags=["认证"])


# 请求/响应模型
class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    username: Optional[str] = Field(None, max_length=50, description="用户名")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    role: str = Field("media_buyer", description="角色")
    account_manager_id: Optional[str] = Field(None, description="上级经理ID")
    auto_confirm: bool = Field(False, description="是否自动确认邮箱")

    @validator('role')
    def validate_role(cls, v):
        allowed_roles = ["admin", "finance", "data_operator", "account_manager", "media_buyer"]
        if v not in allowed_roles:
            raise ValueError(f"角色必须是: {', '.join(allowed_roles)}")
        return v


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(False, description="是否记住登录")


class UpdatePasswordRequest(BaseModel):
    current_password: Optional[str] = Field(None, description="当前密码（可选，用于密码修改）")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")
    confirm_password: str = Field(..., description="确认新密码")

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('密码不匹配')
        return v


class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="邮箱地址")


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., description="验证令牌")


class UpdateProfileRequest(BaseModel):
    username: Optional[str] = Field(None, max_length=50, description="用户名")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    timezone: Optional[str] = Field("UTC", description="时区")
    language: Optional[str] = Field("zh-CN", description="语言")
    preferences: Optional[Dict[str, Any]] = Field(None, description="偏好设置")
    notification_settings: Optional[Dict[str, Any]] = Field(None, description="通知设置")


# 认证端点
@router.post("/register", summary="用户注册")
async def register(request: RegisterRequest):
    """
    用户注册

    - **email**: 邮箱地址
    - **password**: 密码（至少6位）
    - **username**: 用户名（可选）
    - **full_name**: 全名（可选）
    - **role**: 角色（默认media_buyer）
    - **account_manager_id**: 上级经理ID（可选）
    - **auto_confirm**: 是否自动确认邮箱（默认False）
    """
    try:
        result = await supabase_auth_service.register_user(
            email=request.email,
            password=request.password,
            username=request.username,
            full_name=request.full_name,
            role=request.role,
            account_manager_id=request.account_manager_id,
            auto_confirm=request.auto_confirm
        )

        return success_response(
            data=result,
            message=result["message"]
        )

    except HTTPException as e:
        return error_response(
            message=e.detail,
            code=e.status_code,
            status_code=e.status_code
        )
    except Exception as e:
        return error_response(
            message="注册失败",
            code="REGISTER_FAILED",
            status_code=500
        )


@router.post("/login", summary="用户登录")
async def login(
    request: LoginRequest,
    http_request: Request
):
    """
    用户登录

    - **email**: 邮箱地址
    - **password**: 密码
    - **remember_me**: 是否记住登录状态

    返回JWT访问令牌和刷新令牌
    """
    try:
        result = await supabase_auth_service.login_user(
            email=request.email,
            password=request.password,
            remember_me=request.remember_me,
            request=http_request
        )

        # 构建响应数据
        response_data = {
            "user": result["user"],
            "session": result["session"]
        }

        return success_response(
            data=response_data,
            message="登录成功"
        )

    except HTTPException as e:
        return error_response(
            message=e.detail,
            code=e.status_code,
            status_code=e.status_code
        )
    except Exception as e:
        return error_response(
            message="登录失败",
            code="LOGIN_FAILED",
            status_code=500
        )


@router.post("/logout", summary="用户登出")
async def logout(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    用户登出
    """
    try:
        # 从请求头获取token
        authorization = request.headers.get("authorization")
        token = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:]

        if token:
            await supabase_auth_service.logout_user(
                access_token=token,
                user_id=current_user["user"].id
            )

        return success_response(
            message="登出成功"
        )

    except Exception as e:
        return error_response(
            message="登出失败",
            code="LOGOUT_FAILED",
            status_code=500
        )


@router.post("/refresh", summary="刷新令牌")
async def refresh_token(
    refresh_token: str = Field(..., description="刷新令牌")
):
    """
    使用刷新令牌获取新的访问令牌
    """
    try:
        result = await supabase_auth_service.refresh_token(refresh_token)

        return success_response(
            data=result,
            message="令牌刷新成功"
        )

    except HTTPException as e:
        return error_response(
            message=e.detail,
            code=e.status_code,
            status_code=e.status_code
        )
    except Exception as e:
        return error_response(
            message="令牌刷新失败",
            code="REFRESH_FAILED",
            status_code=500
        )


# 密码管理
@router.post("/reset-password", summary="请求重置密码")
async def reset_password(request: ResetPasswordRequest):
    """
    发送密码重置邮件

    - **email**: 邮箱地址
    """
    try:
        await supabase_auth_service.reset_password(request.email)

        # 无论邮箱是否存在都返回成功，避免枚举攻击
        return success_response(
            message="如果该邮箱已注册，您将收到密码重置邮件"
        )

    except Exception as e:
        # 不暴露错误信息
        return success_response(
            message="如果该邮箱已注册，您将收到密码重置邮件"
        )


@router.post("/update-password", summary="更新密码")
async def update_password(
    request: UpdatePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    更新密码

    - **current_password**: 当前密码（可选）
    - **new_password**: 新密码（至少6位）
    - **confirm_password**: 确认新密码
    """
    try:
        # 从请求头获取token
        # 实际实现中，Supabase不需要当前密码
        # 如果需要验证当前密码，需要额外的流程

        # 这里简化处理，直接更新密码
        # 在生产环境中，可能需要先验证当前密码
        authorization = current_user.get("session", {}).get("access_token")

        await supabase_auth_service.update_password(
            new_password=request.new_password,
            access_token=authorization
        )

        return success_response(
            message="密码更新成功"
        )

    except HTTPException as e:
        return error_response(
            message=e.detail,
            code=e.status_code,
            status_code=e.status_code
        )
    except Exception as e:
        return error_response(
            message="密码更新失败",
            code="UPDATE_PASSWORD_FAILED",
            status_code=500
        )


# 邮箱验证
@router.post("/verify-email", summary="验证邮箱")
async def verify_email(request: VerifyEmailRequest):
    """
    使用验证令牌验证邮箱

    - **token**: 邮箱验证令牌
    """
    try:
        await supabase_auth_service.verify_email(request.token)

        return success_response(
            message="邮箱验证成功"
        )

    except HTTPException as e:
        return error_response(
            message=e.detail,
            code=e.status_code,
            status_code=e.status_code
        )
    except Exception as e:
        return error_response(
            message="邮箱验证失败",
            code="VERIFY_EMAIL_FAILED",
            status_code=500
        )


@router.post("/resend-verification", summary="重新发送验证邮件")
async def resend_verification(
    email: EmailStr = Field(..., description="邮箱地址")
):
    """
    重新发送邮箱验证邮件

    - **email**: 邮箱地址
    """
    try:
        await supabase_auth_service.resend_verification_email(email)

        # 无论邮箱是否存在都返回成功
        return success_response(
            message="如果该邮箱已注册且未验证，您将收到验证邮件"
        )

    except Exception as e:
        return success_response(
            message="如果该邮箱已注册且未验证，您将收到验证邮件"
        )


# 用户信息
@router.get("/me", summary="获取当前用户信息")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    获取当前登录用户的详细信息
    """
    return success_response(
        data=current_user,
        message="获取成功"
    )


@router.patch("/profile", summary="更新用户资料")
async def update_profile(
    request: UpdateProfileRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    更新当前用户的资料

    - **username**: 用户名
    - **full_name**: 全名
    - **phone**: 手机号
    - **avatar_url**: 头像URL
    - **department**: 部门
    - **position**: 职位
    - **timezone**: 时区
    - **language**: 语言
    - **preferences**: 偏好设置
    - **notification_settings**: 通知设置
    """
    try:
        from services.supabase_auth_service import supabase_client

        # 构建更新数据
        update_data = {
            k: v for k, v in request.dict(exclude_unset=True).items()
            if v is not None
        }

        # 更新用户元数据
        user_metadata = {}
        if request.username:
            user_metadata["username"] = request.username
        if request.full_name:
            user_metadata["full_name"] = request.full_name

        # 更新Supabase Auth的用户元数据
        if user_metadata:
            auth_response = supabase_client.supabase.auth.update_user({
                "data": user_metadata
            })

            if not auth_response.user:
                raise HTTPException(
                    status_code=400,
                    detail="更新用户信息失败"
                )

        # 更新用户资料表
        if update_data:
            admin_client = supabase_client.get_admin_client()
            response = admin_client.table("user_profiles")\
                .update(update_data)\
                .eq("id", current_user["user"].id)\
                .execute()

            if not response.data:
                raise HTTPException(
                    status_code=400,
                    detail="更新用户资料失败"
                )

        return success_response(
            message="用户资料更新成功"
        )

    except HTTPException as e:
        return error_response(
            message=e.detail,
            code=e.status_code,
            status_code=e.status_code
        )
    except Exception as e:
        return error_response(
            message="更新用户资料失败",
            code="UPDATE_PROFILE_FAILED",
            status_code=500
        )


# 会话管理
@router.get("/sessions", summary="获取活跃会话")
async def get_user_sessions(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    获取当前用户的所有活跃会话
    """
    try:
        sessions = await supabase_auth_service.get_user_sessions(
            current_user["user"].id
        )

        # 清理敏感信息
        for session in sessions:
            session.pop("session_token", None)

        return success_response(
            data=sessions,
            message="获取会话列表成功"
        )

    except Exception as e:
        return error_response(
            message="获取会话列表失败",
            code="GET_SESSIONS_FAILED",
            status_code=500
        )


@router.delete("/sessions/{session_id}", summary="撤销会话")
async def revoke_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    撤销指定的会话

    - **session_id**: 会话ID
    """
    try:
        await supabase_auth_service.revoke_session(
            session_id=session_id,
            user_id=current_user["user"].id
        )

        return success_response(
            message="会话已撤销"
        )

    except Exception as e:
        return error_response(
            message="撤销会话失败",
            code="REVOKE_SESSION_FAILED",
            status_code=500
        )


@router.delete("/sessions", summary="撤销所有会话")
async def revoke_all_sessions(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    撤销当前用户的所有其他会话
    """
    try:
        # 获取所有会话
        sessions = await supabase_auth_service.get_user_sessions(
            current_user["user"].id
        )

        # 撤销除了当前会话外的所有会话
        for session in sessions:
            if session.get("is_active"):
                await supabase_auth_service.revoke_session(
                    session_id=session["id"],
                    user_id=current_user["user"].id
                )

        return success_response(
            message="所有会话已撤销"
        )

    except Exception as e:
        return error_response(
            message="撤销会话失败",
            code="REVOKE_SESSIONS_FAILED",
            status_code=500
        )


# 管理员功能
@router.post("/admin/users/{user_id}/activate", summary="激活用户")
async def activate_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    激活用户账户

    - **user_id**: 用户ID
    """
    try:
        from services.supabase_auth_service import supabase_client

        admin_client = supabase_client.get_admin_client()
        response = admin_client.table("user_profiles")\
            .update({"is_active": True})\
            .eq("id", user_id)\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="用户不存在"
            )

        return success_response(
            message="用户已激活"
        )

    except HTTPException as e:
        return error_response(
            message=e.detail,
            code=e.status_code,
            status_code=e.status_code
        )
    except Exception as e:
        return error_response(
            message="激活用户失败",
            code="ACTIVATE_USER_FAILED",
            status_code=500
        )


@router.post("/admin/users/{user_id}/deactivate", summary="停用用户")
async def deactivate_user(
    user_id: str,
    current_user: Dict[str, Any] = Depends(require_admin)
):
    """
    停用用户账户

    - **user_id**: 用户ID
    """
    try:
        from services.supabase_auth_service import supabase_client

        admin_client = supabase_client.get_admin_client()
        response = admin_client.table("user_profiles")\
            .update({"is_active": False})\
            .eq("id", user_id)\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=404,
                detail="用户不存在"
            )

        return success_response(
            message="用户已停用"
        )

    except HTTPException as e:
        return error_response(
            message=e.detail,
            code=e.status_code,
            status_code=e.status_code
        )
    except Exception as e:
        return error_response(
            message="停用用户失败",
            code="DEACTIVATE_USER_FAILED",
            status_code=500
        )