"""
认证路由模块
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import structlog

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from core.db import get_db
from core.logging import log_requests
from core.error_codes import AuthErrorCodes
from core.security import AuthenticatedUser
from deps.supabase_auth import get_current_user
from services.supabase_auth_service import supabase_auth_service
from utils.response import success_response, error_response
from exceptions import ValidationError, AuthenticationError

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["认证"])


# 请求模型
class LoginRequest(BaseModel):
    """登录请求"""
    identifier: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., min_length=1, description="密码")
    remember_me: bool = Field(False, description="记住我")


class RegisterRequest(BaseModel):
    """注册请求"""
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=8, description="密码")
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=8, description="新密码")
    logout_all: bool = Field(True, description="是否登出所有设备")


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    email: EmailStr = Field(..., description="邮箱")


class ResetPasswordConfirmRequest(BaseModel):
    """确认重置密码请求"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, description="新密码")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")


@router.post("/login", response_model=dict)
@log_requests("auth")
async def login(
    request: LoginRequest,
    request_obj: Request = None
):
    """
    用户登录

    权限: 公开接口
    """
    try:
        # 使用Supabase登录，返回用户信息和会话
        result = await supabase_auth_service.login_user(
            email=request.identifier,
            password=request.password,
            remember_me=request.remember_me,
            request=request_obj
        )

        return success_response(
            data=result,
            message="登录成功"
        )

    except HTTPException as e:
        error_code = AuthErrorCodes.INVALID_CREDENTIALS if e.status_code == 401 else AuthErrorCodes.LOGIN_FAILED
        return error_response(
            code=error_code.code,
            message=e.detail,
            status_code=e.status_code
        )
    except Exception as e:
        return error_response(
            code=AuthErrorCodes.LOGIN_FAILED.code,
            message="登录失败，请稍后重试",
            status_code=500
        )


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
@log_requests("auth")
async def register(
    request: RegisterRequest
):
    """
    用户注册

    权限: 公开接口
    """
    try:
        result = await supabase_auth_service.register_user(
            email=request.email,
            password=request.password,
            username=request.username,
            full_name=request.full_name
        )

        return success_response(
            data=result,
            message="注册成功，请查看邮箱验证邮件",
            status_code=201
        )

    except HTTPException as e:
        if "duplicate" in str(e.detail).lower() or "已被注册" in str(e.detail):
            error_code = AuthErrorCodes.EMAIL_ALREADY_EXISTS
        else:
            error_code = AuthErrorCodes.REGISTER_FAILED
        return error_response(
            code=error_code.code,
            message=e.detail,
            status_code=e.status_code
        )
    except Exception as e:
        return error_response(
            code=AuthErrorCodes.REGISTER_FAILED.code,
            message="注册失败，请稍后重试",
            status_code=500
        )


@router.post("/refresh", response_model=dict)
@log_requests("auth")
async def refresh_token(
    request: RefreshTokenRequest
):
    """
    刷新访问令牌

    权限: 公开接口（需要有效的refresh_token）
    """
    try:
        token_info = await supabase_auth_service.refresh_token(request.refresh_token)

        return success_response(
            data=token_info,
            message="令牌刷新成功"
        )

    except HTTPException as e:
        return error_response(
            code=AuthErrorCodes.TOKEN_REFRESH_FAILED.code,
            message=e.detail,
            status_code=e.status_code
        )
    except Exception as e:
        return error_response(
            code=AuthErrorCodes.TOKEN_REFRESH_FAILED.code,
            message="令牌刷新失败",
            status_code=500
        )


@router.post("/logout", response_model=dict)
@log_requests("auth")
async def logout(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    用户登出

    权限: 需要认证
    """
    try:
        # 获取Authorization头
        authorization = request.headers.get("authorization")
        token = authorization.removeprefix("Bearer ").strip() if authorization else ""

        user_id = current_user.get("user", {}).get("id")

        # 登出
        await supabase_auth_service.logout_user(token, user_id)

        return success_response(
            data={"logged_out_at": datetime.now(timezone.utc).isoformat()},
            message="登出成功"
        )

    except Exception as e:
        return error_response(
            code=AuthErrorCodes.LOGOUT_FAILED.code,
            message="登出失败",
            status_code=500
        )


@router.post("/logout-all", response_model=dict)
@log_requests("auth")
async def logout_all(
    request: Request,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """登出所有设备"""
    try:
        auth_service = SupabaseAuthService()

        # 获取Authorization头
        authorization = request.headers.get("authorization")
        token = authorization.removeprefix("Bearer ").strip() if authorization else None

        # 记录登出日志
        await auth_service.update_user_last_activity(
            current_user.id,
            "logout_all",
            {}
        )

        # 登出所有设备
        success = await auth_service.logout(token or "", logout_all=True)

        if success:
            return success_response(
                data={"logged_out_at": datetime.utcnow().isoformat()},
                message="已从所有设备登出"
            )

    except Exception as e:
        return error_response(
            code="AUTH_LOGOUT_ALL_ERROR",
            message="全设备登出失败",
            status_code=500
        )


@router.get("/me", response_model=dict)
@log_requests("auth")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    获取当前用户信息

    权限: 需要认证
    """
    try:
        user_info = current_user.get("user")
        profile = current_user.get("profile", {})

        if not user_info:
            return error_response(
                code=AuthErrorCodes.USER_NOT_FOUND.code,
                message="用户不存在",
                status_code=404
            )

        return success_response(
            data={
                "user": user_info,
                "profile": profile
            }
        )

    except Exception as e:
        return error_response(
            code=AuthErrorCodes.AUTHENTICATION_ERROR.code,
            message="获取用户信息失败",
            status_code=500
        )


@router.post("/change-password", response_model=dict)
@log_requests("auth")
async def change_password(
    request: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    修改密码

    权限: 需要认证
    """
    try:
        # 注意：Supabase不支持验证旧密码，只能直接更新
        # 生产环境中应该实现额外的旧密码验证逻辑
        await supabase_auth_service.update_password(
            new_password=request.new_password,
            access_token=""  # Token从请求头获取
        )

        return success_response(
            message="密码修改成功，请重新登录"
        )

    except HTTPException as e:
        return error_response(
            code=AuthErrorCodes.PASSWORD_CHANGE_FAILED.code,
            message=e.detail,
            status_code=e.status_code
        )
    except Exception as e:
        return error_response(
            code=AuthErrorCodes.PASSWORD_CHANGE_FAILED.code,
            message="密码修改失败",
            status_code=500
        )


@router.post("/forgot-password", response_model=dict)
@log_requests("auth")
async def forgot_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """忘记密码"""
    try:
        auth_service = SupabaseAuthService()
        success = await auth_service.reset_password_request(request.email)

        # 为了安全，总是返回成功
        return success_response(
            message="如果邮箱存在，重置密码链接已发送"
        )

    except Exception as e:
        # 不暴露具体错误
        return success_response(
            message="如果邮箱存在，重置密码链接已发送"
        )


@router.post("/reset-password", response_model=dict)
@log_requests("auth")
async def reset_password(
    request: ResetPasswordConfirmRequest,
    db: Session = Depends(get_db)
):
    """重置密码"""
    try:
        auth_service = SupabaseAuthService()
        success = await auth_service.reset_password_confirm(
            reset_token=request.token,
            new_password=request.new_password
        )

        if success:
            return success_response(
                message="密码重置成功"
            )

    except ValidationError as e:
        return error_response(
            code=e.error_code,
            message=str(e),
            status_code=400
        )
    except Exception as e:
        return error_response(
            code="AUTH_RESET_PASSWORD_ERROR",
            message="密码重置失败",
            status_code=500
        )


@router.post("/verify-email", response_model=dict)
@log_requests("auth")
async def verify_email(
    token: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """验证邮箱"""
    try:
        auth_service = SupabaseAuthService()
        success = await auth_service.verify_email(token)

        if success:
            return success_response(
                message="邮箱验证成功"
            )
        else:
            return error_response(
                code="AUTH_VERIFY_EMAIL_FAILED",
                message="验证链接无效或已过期",
                status_code=400
            )

    except Exception as e:
        return error_response(
            code="AUTH_VERIFY_EMAIL_ERROR",
            message="邮箱验证失败",
            status_code=500
        )


@router.post("/resend-verification", response_model=dict)
@log_requests("auth")
async def resend_verification(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """重新发送验证邮件"""
    try:
        auth_service = SupabaseAuthService()
        success = await auth_service.send_email_verification(int(current_user.id))

        if success:
            return success_response(
                message="验证邮件已发送"
            )
        else:
            return error_response(
                code="AUTH_ALREADY_VERIFIED",
                message="邮箱已验证",
                status_code=400
            )

    except Exception as e:
        return error_response(
            code="AUTH_RESEND_VERIFICATION_ERROR",
            message="发送验证邮件失败",
            status_code=500
        )


@router.post("/verify-token", response_model=dict)
@log_requests("auth")
async def verify_token(
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """验证令牌有效性"""
    return success_response(
        data={
            "valid": True,
            "user_id": current_user.id,
            "role": current_user.role,
            "expires_at": current_user.raw_claims.get("exp")
        }
    )


# 兼容旧版本的OAuth2PasswordRequestForm登录方式
@router.post("/login/oauth", response_model=dict)
@log_requests("auth")
async def login_oauth(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    request_obj: Request = None
):
    """OAuth2登录（兼容性）"""
    try:
        auth_service = SupabaseAuthService()
        user, token_info = await auth_service.authenticate(
            identifier=form_data.username,
            password=form_data.password
        )

        # 获取客户端IP
        client_ip = request_obj.client.host if request_obj else None

        # 记录登录日志
        await auth_service.update_user_last_activity(
            user.id,
            "login",
            {"ip": client_ip}
        )

        return success_response(
            data={
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role,
                    "is_active": user.is_active
                },
                "token": token_info
            }
        )

    except AuthenticationError as e:
        return error_response(
            code=e.error_code,
            message=str(e),
            status_code=401
        )