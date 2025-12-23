"""
认证路由模块
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import structlog

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from backend.core.db import get_db
from backend.core.logging import log_requests
from backend.core.error_codes import AuthErrorCodes, SystemErrorCodes, ValidationErrorCodes, BusinessErrorCodes
# AuthenticatedUser 已被 Dict[str, Any] 替代，改用本地 JWT 认证
from backend.deps.local_auth import get_current_user  # 使用本地认证
from backend.services.local_auth_service import LocalAuthService  # 使用本地认证服务
from backend.core.response import success_response, error_response
from backend.exceptions import ValidationError, AuthenticationError

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
    token: str = Field(..., description="重置令牌 (access_token)")
    new_password: str = Field(..., min_length=8, description="新密码")
    refresh_token: Optional[str] = Field(None, description="刷新令牌 (用于 Supabase recovery flow)")


class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str = Field(..., description="刷新令牌")


@router.post("/login", response_model=dict)
@log_requests("auth")
async def login(
    request: LoginRequest,
    request_obj: Request = None,
    db: Session = Depends(get_db)
):
    """
    用户登录

    权限: 公开接口
    """
    try:
        # 使用本地 JWT 认证服务
        auth_service = LocalAuthService(db)
        result = await auth_service.login_user(
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
        error_msg = e.detail if isinstance(e.detail, str) else e.detail.get("message", "登录失败")
        return error_response(
            code=error_code.code,
            message=error_msg,
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        return error_response(
            code=AuthErrorCodes.LOGIN_FAILED.code,
            message="登录失败，请稍后重试",
            status_code=500
        )


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
@log_requests("auth")
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    用户注册

    权限: 公开接口
    """
    try:
        logger.info(f"[REGISTER_DEBUG] Starting registration for: {request.email}")
        # 使用本地 JWT 认证服务
        auth_service = LocalAuthService(db)
        logger.info(f"[REGISTER_DEBUG] LocalAuthService created")
        result = await auth_service.register_user(
            email=request.email,
            password=request.password,
            username=request.username,
            full_name=request.full_name
        )
        logger.info(f"[REGISTER_DEBUG] Registration successful: {result.get('user', {}).get('id')}")

        return success_response(
            data=result,
            message="注册成功",
            status_code=201
        )

    except HTTPException as e:
        logger.error(f"[REGISTER_DEBUG] HTTPException: {e.detail}")
        error_msg = e.detail if isinstance(e.detail, str) else e.detail.get("message", "注册失败")
        if "duplicate" in str(error_msg).lower() or "已被注册" in str(error_msg) or "已被使用" in str(error_msg):
            error_code = AuthErrorCodes.EMAIL_ALREADY_EXISTS
        else:
            error_code = AuthErrorCodes.REGISTER_FAILED
        return error_response(
            code=error_code.code,
            message=error_msg,
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"[REGISTER_DEBUG] General Exception: {type(e).__name__}: {e}")
        import traceback
        logger.error(f"[REGISTER_DEBUG] Traceback: {traceback.format_exc()}")
        return error_response(
            code=AuthErrorCodes.REGISTER_FAILED.code,
            message=str(e),  # Return actual error for debugging
            status_code=500
        )


@router.post("/refresh", response_model=dict)
@log_requests("auth")
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    刷新访问令牌

    权限: 公开接口（需要有效的refresh_token）
    """
    try:
        auth_service = LocalAuthService(db)
        token_info = await auth_service.refresh_token(request.refresh_token)

        return success_response(
            data=token_info,
            message="令牌刷新成功"
        )

    except HTTPException as e:
        return error_response(
            code=AuthErrorCodes.TOKEN_REFRESH_FAILED.code,
            message=e.detail if isinstance(e.detail, str) else e.detail.get("message", "令牌刷新失败"),
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"Refresh token error: {e}")
        return error_response(
            code=AuthErrorCodes.TOKEN_REFRESH_FAILED.code,
            message="令牌刷新失败",
            status_code=500
        )


@router.post("/logout", response_model=dict)
@log_requests("auth")
async def logout(
    request: Request,
    db: Session = Depends(get_db),
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
        auth_service = LocalAuthService(db)
        await auth_service.logout_user(token, user_id)

        return success_response(
            data={"logged_out_at": datetime.now(timezone.utc).isoformat()},
            message="登出成功"
        )

    except Exception as e:
        logger.error(f"Logout error: {e}")
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
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """登出所有设备"""
    try:
        # 获取Authorization头
        authorization = request.headers.get("authorization")
        token = authorization.removeprefix("Bearer ").strip() if authorization else ""

        user_id = current_user.get("user", {}).get("id")

        # 登出当前会话并使所有会话失效
        auth_service = LocalAuthService(db)
        await auth_service.logout_user(token, user_id)

        return success_response(
            data={"logged_out_at": datetime.now(timezone.utc).isoformat()},
            message="已从所有设备登出"
        )

    except Exception as e:
        logger.error(f"Logout all error: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="全设备登出失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code
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
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="获取用户信息失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code
        )


@router.post("/change-password", response_model=dict)
@log_requests("auth")
async def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    修改密码

    权限: 需要认证
    """
    try:
        user_id = current_user.get("user", {}).get("id")
        if not user_id:
            return error_response(
                code=AuthErrorCodes.USER_NOT_FOUND.code,
                message="用户不存在",
                status_code=404
            )

        auth_service = LocalAuthService(db)
        await auth_service.change_password(
            user_id=user_id,
            old_password=request.old_password,
            new_password=request.new_password
        )

        return success_response(
            message="密码修改成功，请重新登录"
        )

    except HTTPException as e:
        return error_response(
            code=AuthErrorCodes.PASSWORD_CHANGE_FAILED.code,
            message=e.detail if isinstance(e.detail, str) else e.detail.get("message", "密码修改失败"),
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"Change password error: {e}")
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
        auth_service = LocalAuthService(db)
        await auth_service.reset_password(request.email)

        # 为了安全，总是返回成功
        return success_response(
            message="如果邮箱存在，重置密码链接已发送"
        )

    except Exception as e:
        logger.error(f"Forgot password error: {e}")
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
        auth_service = LocalAuthService(db)
        success = await auth_service.reset_password_confirm(
            reset_token=request.token,
            new_password=request.new_password,
            refresh_token=request.refresh_token
        )

        if success:
            return success_response(
                message="密码重置成功"
            )

    except HTTPException as e:
        return error_response(
            code=ValidationErrorCodes.INVALID_INPUT.code,
            message=e.detail if isinstance(e.detail, str) else e.detail.get("message", "密码重置失败"),
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"Reset password error: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="密码重置失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code
        )


@router.post("/verify-email", response_model=dict)
@log_requests("auth")
async def verify_email(
    token: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """验证邮箱"""
    try:
        auth_service = LocalAuthService(db)
        success = await auth_service.verify_email(token)

        if success:
            return success_response(
                message="邮箱验证成功"
            )
        else:
            return error_response(
                code=AuthErrorCodes.TOKEN_INVALID.code,
                message="验证链接无效或已过期",
                status_code=400
            )

    except Exception as e:
        logger.error(f"Verify email error: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="邮箱验证失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code
        )


@router.post("/resend-verification", response_model=dict)
@log_requests("auth")
async def resend_verification(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """重新发送验证邮件"""
    try:
        user_email = current_user.get("user", {}).get("email")
        if not user_email:
            return error_response(
                code=AuthErrorCodes.USER_NOT_FOUND.code,
                message="用户不存在",
                status_code=404
            )

        auth_service = LocalAuthService(db)
        success = await auth_service.resend_verification_email(user_email)

        if success:
            return success_response(
                message="验证邮件已发送"
            )
        else:
            return error_response(
                code=BusinessErrorCodes.OPERATION_FAILED.code,
                message="邮箱已验证",
                status_code=400
            )

    except Exception as e:
        logger.error(f"Resend verification error: {e}")
        return error_response(
            code=SystemErrorCodes.INTERNAL_ERROR.code,
            message="发送验证邮件失败",
            status_code=SystemErrorCodes.INTERNAL_ERROR.status_code
        )


@router.post("/verify-token", response_model=dict)
@log_requests("auth")
async def verify_token(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """验证令牌有效性"""
    user_info = current_user.get("user", {})
    raw_claims = current_user.get("raw_claims", {})
    return success_response(
        data={
            "valid": True,
            "user_id": user_info.get("id"),
            "role": user_info.get("role"),
            "expires_at": raw_claims.get("exp")
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
        auth_service = LocalAuthService(db)
        result = await auth_service.login_user(
            email=form_data.username,
            password=form_data.password,
            request=request_obj
        )

        return success_response(
            data=result,
            message="登录成功"
        )

    except HTTPException as e:
        return error_response(
            code=AuthErrorCodes.INVALID_CREDENTIALS.code,
            message=e.detail if isinstance(e.detail, str) else e.detail.get("message", "登录失败"),
            status_code=e.status_code
        )
    except Exception as e:
        logger.error(f"OAuth login error: {e}")
        return error_response(
            code=AuthErrorCodes.LOGIN_FAILED.code,
            message="登录失败，请稍后重试",
            status_code=500
        )