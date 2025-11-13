"""
Supabase认证服务
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any, List
from fastapi import HTTPException, status, Request
from supabase import Client
from sqlalchemy.orm import Session

from core.supabase_client import supabase_client
from core.db import get_db


class SupabaseAuthService:
    """Supabase认证服务"""

    def __init__(self):
        self.client = supabase_client.supabase
        self.admin_client = supabase_client.get_admin_client()

    async def register_user(
        self,
        email: str,
        password: str,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        role: str = "media_buyer",
        account_manager_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_confirm: bool = False
    ) -> Dict[str, Any]:
        """
        用户注册

        Args:
            email: 邮箱地址
            password: 密码
            username: 用户名
            full_name: 全名
            role: 角色
            account_manager_id: 账户经理ID
            metadata: 额外的元数据
            auto_confirm: 是否自动确认邮箱

        Returns:
            注册结果
        """
        try:
            # 构建用户元数据
            user_metadata = {
                "username": username,
                "full_name": full_name or email.split("@")[0],
                "role": role,
                "account_manager_id": account_manager_id
            }

            if metadata:
                user_metadata.update(metadata)

            # 通过Supabase注册
            response = self.admin_client.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": auto_confirm,
                "user_metadata": user_metadata
            })

            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="注册失败"
                )

            # 记录注册日志
            await self._record_login(
                response.user.id,
                "registration",
                "success",
                email=email
            )

            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "role": role,
                "auto_confirm": auto_confirm,
                "message": "注册成功" + ("，请查收验证邮件" if not auto_confirm else "")
            }

        except Exception as e:
            if "duplicate" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该邮箱已被注册"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def login_user(
        self,
        email: str,
        password: str,
        remember_me: bool = False,
        request: Optional[Request] = None
    ) -> Dict[str, Any]:
        """
        用户登录

        Args:
            email: 邮箱地址
            password: 密码
            remember_me: 是否记住登录
            request: FastAPI请求对象

        Returns:
            登录结果
        """
        try:
            # 通过Supabase登录
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            if not response.user or not response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="登录失败"
                )

            # 获取用户资料
            profile = await self._get_user_profile(response.user.id)

            if not profile:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户资料不存在"
                )

            # 检查账户是否激活
            if not profile.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="账户已被禁用"
                )

            # 记录登录历史
            await self._record_login(
                response.user.id,
                "password",
                "success",
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent") if request else None
            )

            # 创建会话记录
            await self._create_session(
                response.user.id,
                response.session.access_token,
                device_info=self._extract_device_info(request) if request else None,
                expires_at=response.session.expires_at
            )

            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "email_confirmed_at": response.user.email_confirmed_at,
                    "phone": response.user.phone,
                    "phone_confirmed_at": response.user.phone_confirmed_at,
                    "profile": profile
                },
                "session": {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_at": response.session.expires_at,
                    "expires_in": response.session.expires_in
                }
            }

        except Exception as e:
            # 记录失败登录
            await self._record_login_by_email(
                email,
                "password",
                "failed",
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent") if request else None
            )

            if "Invalid login credentials" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="邮箱或密码错误"
                )

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e)
            )

    async def logout_user(self, access_token: str, user_id: str) -> None:
        """
        用户登出

        Args:
            access_token: 访问令牌
            user_id: 用户ID
        """
        try:
            # 通过Supabase登出
            self.client.auth.sign_out(access_token)

            # 更新登录历史
            await self._update_login_logout(user_id)

            # 使会话失效
            await self._invalidate_sessions(user_id)

        except Exception as e:
            # 即使登出失败也不抛出错误
            pass

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        刷新令牌

        Args:
            refresh_token: 刷新令牌

        Returns:
            新的会话信息
        """
        try:
            response = self.client.auth.refresh_session(refresh_token)

            if not response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="刷新失败"
                )

            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_at": response.session.expires_at,
                "expires_in": response.session.expires_in
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已过期或无效"
            )

    async def reset_password(self, email: str) -> None:
        """
        发送密码重置邮件

        Args:
            email: 邮箱地址
        """
        try:
            self.client.auth.reset_password_for_email(
                email,
                options={
                    "redirect_to": f"{settings.FRONTEND_URL}/reset-password"
                }
            )

        except Exception as e:
            # 不暴露邮箱是否存在的信息
            pass

    async def update_password(
        self,
        new_password: str,
        access_token: str
    ) -> None:
        """
        更新密码

        Args:
            new_password: 新密码
            access_token: 访问令牌
        """
        try:
            response = self.client.auth.update_user({
                "password": new_password
            })

            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="密码更新失败"
                )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        验证JWT令牌

        Args:
            token: JWT令牌

        Returns:
            用户信息和资料
        """
        try:
            response = self.client.auth.get_user(token)

            if not response.user:
                return None

            # 获取用户资料
            profile = await self._get_user_profile(response.user.id)

            return {
                "user": response.user,
                "profile": profile
            }

        except Exception:
            return None

    async def verify_email(self, token: str) -> None:
        """
        验证邮箱

        Args:
            token: 验证令牌
        """
        try:
            response = self.client.auth.verify_otp({
                "token": token,
                "type": "email"
            })

            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱验证失败"
                )

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    async def resend_verification_email(self, email: str) -> None:
        """
        重新发送验证邮件

        Args:
            email: 邮箱地址
        """
        try:
            # 使用管理员接口获取用户并重新发送验证邮件
            users = self.admin_client.auth.admin.list_users()
            user = next((u for u in users.users if u.email == email), None)

            if user and not user.email_confirmed_at:
                self.admin_client.auth.admin.invite_user_by_email(
                    email,
                    options={
                        "data": user.user_metadata
                    }
                )

        except Exception:
            # 不暴露用户是否存在的信息
            pass

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户的活跃会话

        Args:
            user_id: 用户ID

        Returns:
            会话列表
        """
        try:
            response = self.admin_client.table("user_sessions")\
                .select("*")\
                .eq("user_id", user_id)\
                .eq("is_active", True)\
                .execute()

            return response.data or []

        except Exception:
            return []

    async def revoke_session(self, session_id: str, user_id: str) -> None:
        """
        撤销指定会话

        Args:
            session_id: 会话ID
            user_id: 用户ID
        """
        try:
            self.admin_client.table("user_sessions")\
                .update({"is_active": False})\
                .eq("id", session_id)\
                .eq("user_id", user_id)\
                .execute()

        except Exception:
            pass

    # 私有方法

    async def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户资料"""
        try:
            response = self.admin_client.table("user_profiles")\
                .select("*")\
                .eq("id", user_id)\
                .single()\
                .execute()

            return response.data if response.data else None

        except Exception:
            return None

    async def _record_login(
        self,
        user_id: str,
        login_type: str,
        status: str,
        email: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """记录登录历史"""
        try:
            self.admin_client.table("user_login_history")\
                .insert({
                    "user_id": user_id,
                    "email": email,
                    "login_type": login_type,
                    "status": status,
                    "login_time": datetime.now(timezone.utc).isoformat(),
                    "ip_address": ip_address,
                    "user_agent": user_agent
                })\
                .execute()
        except Exception:
            pass  # 忽略记录错误

    async def _record_login_by_email(
        self,
        email: str,
        login_type: str,
        status: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """通过邮箱记录登录尝试"""
        try:
            # 先通过邮箱查找用户
            users = self.admin_client.auth.admin.list_users()
            user = next((u for u in users.users if u.email == email), None)

            if user:
                await self._record_login(
                    user.id,
                    login_type,
                    status,
                    email=email,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
        except Exception:
            pass

    async def _update_login_logout(self, user_id: str) -> None:
        """更新登出时间"""
        try:
            self.admin_client.table("user_login_history")\
                .update({
                    "logout_time": datetime.now(timezone.utc).isoformat()
                })\
                .eq("user_id", user_id)\
                .is_("logout_time", "null")\
                .execute()
        except Exception:
            pass

    async def _create_session(
        self,
        user_id: str,
        session_token: str,
        device_info: Optional[Dict[str, Any]] = None,
        expires_at: Optional[str] = None
    ) -> None:
        """创建会话记录"""
        try:
            self.admin_client.table("user_sessions")\
                .insert({
                    "user_id": user_id,
                    "session_token": session_token,
                    "device_info": device_info,
                    "is_active": True,
                    "expires_at": expires_at
                })\
                .execute()
        except Exception:
            pass

    async def _invalidate_sessions(self, user_id: str) -> None:
        """使用户的所有会话失效"""
        try:
            self.admin_client.table("user_sessions")\
                .update({"is_active": False})\
                .eq("user_id", user_id)\
                .execute()
        except Exception:
            pass

    def _get_client_ip(self, request: Optional[Request]) -> Optional[str]:
        """获取客户端IP地址"""
        if not request:
            return None

        # 尝试从各种头部获取真实IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else None

    def _extract_device_info(self, request: Request) -> Dict[str, Any]:
        """提取设备信息"""
        user_agent = request.headers.get("user-agent", "")

        device_info = {
            "user_agent": user_agent,
            "ip": self._get_client_ip(request)
        }

        # 简单的设备检测
        if "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
            device_info["device_type"] = "mobile"
        elif "Tablet" in user_agent or "iPad" in user_agent:
            device_info["device_type"] = "tablet"
        else:
            device_info["device_type"] = "desktop"

        # 浏览器检测
        if "Chrome" in user_agent:
            device_info["browser"] = "Chrome"
        elif "Firefox" in user_agent:
            device_info["browser"] = "Firefox"
        elif "Safari" in user_agent:
            device_info["browser"] = "Safari"
        elif "Edge" in user_agent:
            device_info["browser"] = "Edge"
        else:
            device_info["browser"] = "Other"

        return device_info


# 全局服务实例
supabase_auth_service = SupabaseAuthService()