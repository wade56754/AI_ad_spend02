"""
Supabase客户端配置
Version: 1.0
Author: Claude协作开发
"""

import os
from typing import Optional, Dict, Any
from supabase import create_client, Client

from core.config import get_settings

settings = get_settings()


class SupabaseClient:
    """Supabase客户端管理器"""

    def __init__(self):
        self._supabase: Optional[Client] = None
        self._admin_client: Optional[Client] = None
        self._url = settings.SUPABASE_URL
        self._key = settings.SUPABASE_ANON_KEY
        self._service_key = settings.SUPABASE_SERVICE_ROLE_KEY

    @property
    def supabase(self) -> Client:
        """获取普通客户端"""
        if not self._supabase:
            self._supabase = create_client(self._url, self._key)
        return self._supabase

    def get_admin_client(self) -> Client:
        """获取管理员权限的客户端"""
        if not self._admin_client:
            self._admin_client = create_client(self._url, self._service_key)
        return self._admin_client

    def get_client(self, use_admin: bool = False) -> Client:
        """根据需要获取客户端"""
        return self.get_admin_client() if use_admin else self.supabase

    async def verify_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        """验证JWT令牌"""
        try:
            response = self.supabase.auth.get_user(token)
            return response.user if response.user else None
        except Exception:
            return None

    async def refresh_session(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """刷新会话"""
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            return response.session if response.session else None
        except Exception:
            return None


# 全局单例
supabase_client = SupabaseClient()