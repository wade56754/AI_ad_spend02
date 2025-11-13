"""
认证路由模块
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from core.database import get_db
from core.security import jwt_manager, token_blacklist, AuthenticatedUser, get_current_user
from models.user import User
from services.auth_service import AuthService
from utils.response import success_response, error_response
from exceptions import ValidationError, AuthenticationError

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
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db),
    request_obj: Request = None
):
    """用户登录"""
    try:
        auth_service = AuthService(db)
        user, token_info = await auth_service.authenticate(
            identifier=request.identifier,
            password=request.password,
            remember_me=request.remember_me
        )

        # 获取客户端IP
        client_ip = request_obj.client.host if request_obj else None

        # 记录登录日志
        await auth_service.update_user_last_activity(
            user.id,
            "login",
            {"ip": client_ip, "remember_me": request.remember_me}
        )

        return success_response(
            data={
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role,
                    "is_active": user.is_active,
                    "email_verified": user.email_verified,
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                    "login_count": user.login_count or 0
                },
                "token": token_info
            },
            message="登录成功"
        )

    except AuthenticationError as e:
        return error_response(
            code=e.error_code,
            message=str(e),
            status_code=401
        )
    except Exception as e:
        return error_response(
            code="AUTH_LOGIN_ERROR",
            message="登录失败，请稍后重试",
            status_code=500
        )


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """用户注册"""
    try:
        auth_service = AuthService(db)
        user = await auth_service.register_user(
            email=request.email,
            password=request.password,
            username=request.username,
            full_name=request.full_name
        )

        return success_response(
            data={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "email_verified": user.email_verified,
                "created_at": user.created_at.isoformat()
            },
            message="注册成功，请查看邮箱验证邮件",
            status_code=201
        )

    except ValidationError as e:
        return error_response(
            code=e.error_code,
            message=str(e),
            status_code=400
        )
    except Exception as e:
        return error_response(
            code="AUTH_REGISTER_ERROR",
            message="注册失败，请稍后重试",
            status_code=500
        )


@router.post("/refresh", response_model=dict)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """刷新访问令牌"""
    try:
        auth_service = AuthService(db)
        token_info = await auth_service.refresh_token(request.refresh_token)

        return success_response(
            data=token_info,
            message="令牌刷新成功"
        )

    except AuthenticationError as e:
        return error_response(
            code=e.error_code,
            message=str(e),
            status_code=401
        )
    except Exception as e:
        return error_response(
            code="AUTH_REFRESH_ERROR",
            message="令牌刷新失败",
            status_code=500
        )


@router.post("/logout", response_model=dict)
async def logout(
    request: Request,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """用户登出"""
    try:
        auth_service = AuthService(db)

        # 获取Authorization头
        authorization = request.headers.get("authorization")
        token = authorization.removeprefix("Bearer ").strip() if authorization else None

        # 记录登出日志
        await auth_service.update_user_last_activity(
            current_user.id,
            "logout",
            {}
        )

        # 登出
        success = await auth_service.logout(token or "")

        if success:
            return success_response(
                data={"logged_out_at": datetime.utcnow().isoformat()},
                message="登出成功"
            )

    except Exception as e:
        return error_response(
            code="AUTH_LOGOUT_ERROR",
            message="登出失败",
            status_code=500
        )


@router.post("/logout-all", response_model=dict)
async def logout_all(
    request: Request,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """登出所有设备"""
    try:
        auth_service = AuthService(db)

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
async def get_current_user_info(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户信息"""
    try:
        auth_service = AuthService(db)
        user = await auth_service.get_user_by_id(int(current_user.id))

        if not user:
            return error_response(
                code="AUTH_USER_NOT_FOUND",
                message="用户不存在",
                status_code=404
            )

        return success_response(
            data={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "is_active": user.is_active,
                "email_verified": user.email_verified,
                "avatar_url": user.avatar_url,
                "phone": user.phone,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                "login_count": user.login_count or 0,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
                "permissions": current_user.permissions
            }
        )

    except Exception as e:
        return error_response(
            code="AUTH_GET_USER_ERROR",
            message="获取用户信息失败",
            status_code=500
        )


@router.post("/change-password", response_model=dict)
async def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """修改密码"""
    try:
        auth_service = AuthService(db)
        success = await auth_service.change_password(
            user_id=int(current_user.id),
            old_password=request.old_password,
            new_password=request.new_password,
            logout_all=request.logout_all
        )

        if success:
            # 记录密码修改日志
            await auth_service.update_user_last_activity(
                current_user.id,
                "change_password",
                {"logout_all": request.logout_all}
            )

            return success_response(
                message="密码修改成功，请重新登录"
            )

    except ValidationError as e:
        return error_response(
            code=e.error_code,
            message=str(e),
            status_code=400
        )
    except Exception as e:
        return error_response(
            code="AUTH_CHANGE_PASSWORD_ERROR",
            message="密码修改失败",
            status_code=500
        )


@router.post("/forgot-password", response_model=dict)
async def forgot_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """忘记密码"""
    try:
        auth_service = AuthService(db)
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
async def reset_password(
    request: ResetPasswordConfirmRequest,
    db: Session = Depends(get_db)
):
    """重置密码"""
    try:
        auth_service = AuthService(db)
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
async def verify_email(
    token: str = Body(..., embed=True),
    db: Session = Depends(get_db)
):
    """验证邮箱"""
    try:
        auth_service = AuthService(db)
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
async def resend_verification(
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user)
):
    """重新发送验证邮件"""
    try:
        auth_service = AuthService(db)
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
async def login_oauth(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    request_obj: Request = None
):
    """OAuth2登录（兼容性）"""
    try:
        auth_service = AuthService(db)
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