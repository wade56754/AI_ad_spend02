"""
Supabase客户端配置
Version: 1.0
Author: Claude协作开发
"""

import os
from typing import Optional, Dict, Any
from supabase import create_client, Client

from backend.core.config import get_settings

settings = get_settings()


class SupabaseClient:
    """Supabase客户端管理器"""

    def __init__(self):
        self._supabase: Optional[Client] = None
        self._admin_client: Optional[Client] = None
        self._url = settings.supabase_url
        self._key = settings.supabase_anon_key
        self._service_key = settings.supabase_service_role_key
        self._fallback_url = settings.supabase_fallback_url
        self._fallback_key = settings.supabase_fallback_anon_key
        self._fallback_service_key = settings.supabase_fallback_service_role_key
        self._current: str = "primary"
        self._last_fail_ts: Optional[float] = None

    @property
    def supabase(self) -> Client:
        if not self._supabase:
            url, key = self._select_url_key()
            self._supabase = create_client(url, key)
        return self._supabase

    def get_admin_client(self) -> Client:
        if not self._admin_client:
            url, key = self._select_url_service_key()
            self._admin_client = create_client(url, key)
        return self._admin_client

    def get_client(self, use_admin: bool = False) -> Client:
        return self.get_admin_client() if use_admin else self.supabase

    def _select_url_key(self) -> tuple[str, str]:
        if self._current == "fallback" and self._fallback_url and self._fallback_key:
            return self._fallback_url, self._fallback_key
        return self._url, self._key

    def _select_url_service_key(self) -> tuple[str, str]:
        if self._current == "fallback" and self._fallback_url and self._fallback_service_key:
            return self._fallback_url, self._fallback_service_key
        return self._url, self._service_key

    def switch_to_fallback(self) -> bool:
        if not (self._fallback_url and self._fallback_key and self._fallback_service_key):
            return False
        self._current = "fallback"
        self._supabase = None
        self._admin_client = None
        return True

    def switch_to_primary(self) -> None:
        self._current = "primary"
        self._supabase = None
        self._admin_client = None

    async def verify_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.supabase.auth.get_user(token)
            return response.user if response.user else None
        except Exception as e:
            if settings.auto_failover and self.switch_to_fallback():
                try:
                    response = self.supabase.auth.get_user(token)
                    return response.user if response.user else None
                except Exception:
                    pass
            return None

    async def refresh_session(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            return response.session if response.session else None
        except Exception:
            if settings.auto_failover and self.switch_to_fallback():
                try:
                    response = self.supabase.auth.refresh_session(refresh_token)
                    return response.session if response.session else None
                except Exception:
                    pass
            return None


# 全局单例
supabase_client = SupabaseClient()