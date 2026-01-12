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

from backend.core.supabase_client import supabase_client
from backend.core.db import get_db
from backend.core.config import get_settings

settings = get_settings()


class SupabaseAuthService:
    """Supabase认证服务"""

    def __init__(self):
        self._provider = supabase_client

    @property
    def client(self):
        return self._provider.supabase

    @property
    def admin_client(self):
        return self._provider.get_admin_client()

    async def register_user(
        self,
        email: str,
        password: str,
        username: Optional[str] = None,
        full_name: Optional[str] = None,
        role: str = "pitcher",
        account_manager_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        auto_confirm: bool = False,
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
                "account_manager_id": account_manager_id,
            }

            if metadata:
                user_metadata.update(metadata)

            # 通过Supabase注册
            response = self.admin_client.auth.admin.create_user(
                {
                    "email": email,
                    "password": password,
                    "email_confirm": auto_confirm,
                    "user_metadata": user_metadata,
                }
            )

            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="注册失败"
                )

            # 记录注册日志
            await self._record_login(
                response.user.id, "registration", "success", email=email
            )

            return {
                "user_id": response.user.id,
                "email": response.user.email,
                "role": role,
                "auto_confirm": auto_confirm,
                "message": "注册成功" + ("，请查收验证邮件" if not auto_confirm else ""),
            }

        except Exception as e:
            if "duplicate" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="该邮箱已被注册"
                )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def login_user(
        self,
        email: str,
        password: str,
        remember_me: bool = False,
        request: Optional[Request] = None,
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
        import logging

        logger = logging.getLogger(__name__)

        try:
            logger.info(f"[LOGIN] Starting login for: {email}")

            # 通过Supabase登录
            response = self.client.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            if not response.user or not response.session:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="登录失败"
                )

            logger.info(
                f"[LOGIN] Supabase auth successful for user: {response.user.id}"
            )

            # 获取用户资料（可选，失败不阻塞登录）
            profile = None
            try:
                profile = await self._get_user_profile(response.user.id)
                logger.info(f"[LOGIN] Profile lookup result: {profile is not None}")
            except Exception as profile_error:
                logger.warning(
                    f"[LOGIN] Profile lookup failed (non-blocking): {profile_error}"
                )
                profile = None

            # 如果没有 profile，从 user_metadata 构建默认 profile
            if not profile:
                logger.info(f"[LOGIN] Building default profile from user_metadata")
                user_metadata = response.user.user_metadata or {}
                profile = {
                    "id": response.user.id,
                    "username": user_metadata.get("username", email.split("@")[0]),
                    "full_name": user_metadata.get("full_name", ""),
                    "role": user_metadata.get("role", "pitcher"),
                    "is_active": True,
                }

            # 检查账户是否激活
            if not profile.get("is_active", True):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="账户已被禁用"
                )

            # 记录登录历史（失败不阻塞）
            try:
                await self._record_login(
                    response.user.id,
                    "password",
                    "success",
                    ip_address=self._get_client_ip(request),
                    user_agent=request.headers.get("user-agent") if request else None,
                )
            except Exception as record_error:
                logger.warning(
                    f"[LOGIN] Failed to record login (non-blocking): {record_error}"
                )

            # 创建会话记录（失败不阻塞）
            try:
                await self._create_session(
                    response.user.id,
                    response.session.access_token,
                    device_info=self._extract_device_info(request) if request else None,
                    expires_at=response.session.expires_at,
                )
            except Exception as session_error:
                logger.warning(
                    f"[LOGIN] Failed to create session (non-blocking): {session_error}"
                )

            logger.info(f"[LOGIN] Login successful for: {email}")

            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "email_confirmed_at": response.user.email_confirmed_at,
                    "phone": response.user.phone,
                    "phone_confirmed_at": response.user.phone_confirmed_at,
                    "profile": profile,
                },
                "session": {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                    "expires_at": response.session.expires_at,
                    "expires_in": response.session.expires_in,
                },
            }

        except HTTPException:
            # 重新抛出 HTTPException，不做处理
            raise
        except Exception as e:
            logger.error(
                f"[LOGIN] Login failed with exception: {type(e).__name__}: {e}"
            )

            # 记录失败登录（不阻塞）
            try:
                await self._record_login_by_email(
                    email,
                    "password",
                    "failed",
                    ip_address=self._get_client_ip(request),
                    user_agent=request.headers.get("user-agent") if request else None,
                )
            except Exception:
                pass

            if "Invalid login credentials" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="邮箱或密码错误"
                )

            # 返回通用登录失败，不暴露内部错误
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="登录失败，请稍后重试"
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
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="刷新失败"
                )

            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_at": response.session.expires_at,
                "expires_in": response.session.expires_in,
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="令牌已过期或无效"
            )

    async def reset_password(self, email: str) -> None:
        """
        发送密码重置邮件

        Args:
            email: 邮箱地址
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            # 获取前端URL
            frontend_url = settings.frontend_url
            redirect_url = f"{frontend_url}/reset-password"

            logger.info(f"Sending password reset email to: {email}")
            logger.info(f"Redirect URL: {redirect_url}")

            response = self.client.auth.reset_password_email(
                email, options={"redirect_to": redirect_url}
            )

            logger.info(f"Supabase response: {response}")
            logger.debug(f"Password reset email sent to {email}, response: {response}")

        except Exception as e:
            # 记录详细错误但不暴露给用户
            logger.error(f"Password reset email error: {type(e).__name__}: {e}", exc_info=True)

    async def update_password(self, new_password: str, access_token: str) -> None:
        """
        更新密码

        Args:
            new_password: 新密码
            access_token: 访问令牌
        """
        try:
            response = self.client.auth.update_user({"password": new_password})

            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="密码更新失败"
                )

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    async def reset_password_confirm(
        self, reset_token: str, new_password: str, refresh_token: Optional[str] = None
    ) -> bool:
        """
        使用重置令牌确认密码重置

        Args:
            reset_token: 重置令牌（来自邮件链接中的 access_token）
            new_password: 新密码
            refresh_token: 刷新令牌（可选，用于 Supabase recovery flow）

        Returns:
            是否成功
        """
        import logging

        logger = logging.getLogger(__name__)

        try:
            logger.info(
                f"Attempting password reset with token length: {len(reset_token)}"
            )
            logger.info(f"Refresh token provided: {refresh_token is not None}")

            # 使用 recovery token 设置会话
            # Supabase recovery flow 需要 access_token 和 refresh_token
            if refresh_token:
                response = self.client.auth.set_session(reset_token, refresh_token)
            else:
                # 如果没有 refresh_token，尝试只用 access_token
                response = self.client.auth.set_session(reset_token, "")

            if not response or not response.user:
                logger.error("Failed to set session with recovery token")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="无效或已过期的重置令牌"
                )

            logger.info(f"Session set successfully for user: {response.user.id}")

            # 使用会话更新密码
            update_response = self.client.auth.update_user({"password": new_password})

            if not update_response.user:
                logger.error("Failed to update password")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="密码更新失败"
                )

            logger.info("Password updated successfully")
            return True

        except HTTPException:
            raise
        except Exception as e:
            import logging

            logging.error(f"Password reset confirm error: {type(e).__name__}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"密码重置失败: {str(e)}"
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

            return {"user": response.user, "profile": profile}

        except Exception:
            return None

    async def verify_email(self, token: str) -> None:
        """
        验证邮箱

        Args:
            token: 验证令牌
        """
        try:
            response = self.client.auth.verify_otp({"token": token, "type": "email"})

            if not response.user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱验证失败"
                )

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

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
                    email, options={"data": user.user_metadata}
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
            response = (
                self.admin_client.table("user_sessions")
                .select("*")
                .eq("user_id", user_id)
                .eq("is_active", True)
                .execute()
            )

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
            self.admin_client.table("user_sessions").update({"is_active": False}).eq(
                "id", session_id
            ).eq("user_id", user_id).execute()

        except Exception:
            pass

    # 私有方法

    async def _get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户资料"""
        try:
            response = (
                self.admin_client.table("user_profiles")
                .select("*")
                .eq("id", user_id)
                .single()
                .execute()
            )

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
        user_agent: Optional[str] = None,
    ) -> None:
        """记录登录历史"""
        try:
            self.admin_client.table("user_login_history").insert(
                {
                    "user_id": user_id,
                    "email": email,
                    "login_type": login_type,
                    "status": status,
                    "login_time": datetime.now(timezone.utc).isoformat(),
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                }
            ).execute()
        except Exception:
            pass  # 忽略记录错误

    async def _record_login_by_email(
        self,
        email: str,
        login_type: str,
        status: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
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
                    user_agent=user_agent,
                )
        except Exception:
            pass

    async def _update_login_logout(self, user_id: str) -> None:
        """更新登出时间"""
        try:
            self.admin_client.table("user_login_history").update(
                {"logout_time": datetime.now(timezone.utc).isoformat()}
            ).eq("user_id", user_id).is_("logout_time", "null").execute()
        except Exception:
            pass

    async def _create_session(
        self,
        user_id: str,
        session_token: str,
        device_info: Optional[Dict[str, Any]] = None,
        expires_at: Optional[str] = None,
    ) -> None:
        """创建会话记录"""
        try:
            self.admin_client.table("user_sessions").insert(
                {
                    "user_id": user_id,
                    "session_token": session_token,
                    "device_info": device_info,
                    "is_active": True,
                    "expires_at": expires_at,
                }
            ).execute()
        except Exception:
            pass

    async def _invalidate_sessions(self, user_id: str) -> None:
        """使用户的所有会话失效"""
        try:
            self.admin_client.table("user_sessions").update({"is_active": False}).eq(
                "user_id", user_id
            ).execute()
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

        device_info = {"user_agent": user_agent, "ip": self._get_client_ip(request)}

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
