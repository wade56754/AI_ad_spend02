# 安全配置文档

> **文档目的**: 为AI广告代投系统提供全面的安全配置和最佳实践指南
> **目标读者**: 安全工程师、开发团队、系统管理员
> **更新日期**: 2025-11-11
> **版本**: v1.0

---

## 📋 目录

1. [安全架构概览](#1-安全架构概览)
2. [身份认证和授权](#2-身份认证和授权)
3. [数据传输安全](#3-数据传输安全)
4. [数据存储安全](#4-数据存储安全)
5. [API安全防护](#5-api安全防护)
6. [Web应用安全](#6-web应用安全)
7. [RLS行级安全策略](#7-rls行级安全策略)
8. [安全监控和审计](#8-安全监控和审计)
9. [漏洞管理](#9-漏洞管理)
10. [安全测试](#10-安全测试)

---

## 1. 安全架构概览

### 1.1 安全防护体系

```
┌─────────────────────────────────────────────────────────────┐
│                       安全防护层                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  WAF防护    │ │  DDoS防护   │ │  速率限制    │           │
│  │  Cloudflare │ │  AWS Shield │ │  Rate Limit │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                       网络传输层                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  HTTPS/TLS  │ │  HSTS强制   │ │  安全头配置  │           │
│  │  1.3协议    │ │  安全传输   │ │  CSP策略    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                       应用安全层                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  身份认证   │ │  权限控制   │ │  输入验证    │           │
│  │  JWT+OAuth  │ │  RBAC模型   │ │  参数验证    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                       数据安全层                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  数据加密   │ │  访问控制   │ │  审计日志    │           │
│  │  AES-256    │ │  RLS策略    │ │  操作记录    │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 安全原则

1. **纵深防御**: 多层安全防护，单点突破不会导致系统崩溃
2. **最小权限**: 用户和服务只获得必要的最小权限
3. **零信任**: 不信任任何内部或外部请求，都需要验证
4. **默认安全**: 所有配置默认为安全模式
5. **透明可控**: 安全策略可审计、可监控、可配置

---

## 2. 身份认证和授权

### 2.1 JWT 认证配置

#### JWT Token 结构
```typescript
// 后端 JWT 配置
const jwtConfig = {
  secret: process.env.JWT_SECRET, // 32字节以上随机密钥
  algorithm: 'HS256',
  accessTokenExpire: '15m',
  refreshTokenExpire: '7d',
  issuer: 'ai-ad-spend',
  audience: 'ai-ad-spend-users',
}

// Token 生成
interface JWTPayload {
  sub: string        // 用户ID
  email: string      // 用户邮箱
  role: string       // 用户角色
  permissions: string[] // 用户权限
  iat: number        // 签发时间
  exp: number        // 过期时间
  iss: string        // 签发者
  aud: string        // 受众
}

// 中间件验证
export const verifyJWT = async (token: string): Promise<JWTPayload> => {
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET!) as JWTPayload

    // 检查token是否在黑名单中
    const isBlacklisted = await redis.get(`blacklist:${token}`)
    if (isBlacklisted) {
      throw new Error('Token已失效')
    }

    return decoded
  } catch (error) {
    throw new AuthenticationError('无效的认证令牌')
  }
}
```

#### Token 刷新机制
```python
# backend/app/auth/token_refresh.py
from fastapi import APIRouter, HTTPException, Depends
from jose import JWTError, jwt
import redis

router = APIRouter()

@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    try:
        # 验证refresh token
        payload = jwt.decode(
            refresh_token,
            REFRESH_SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="无效的refresh token")

        # 检查用户是否存在且活跃
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="用户不存在或已被禁用")

        # 生成新的access token
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )

        # 将旧的access token加入黑名单
        old_token = await redis.get(f"token:{user_id}")
        if old_token:
            await redis.setex(f"blacklist:{old_token}", 3600, "revoked")

        # 存储新的access token
        await redis.setex(f"token:{user_id}", 900, access_token)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 900
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="无效的refresh token")

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    # 将当前token加入黑名单
    await redis.setex(f"blacklist:{token}", 3600, "revoked")

    # 清除用户token缓存
    await redis.delete(f"token:{current_user.id}")

    return {"message": "退出登录成功"}
```

### 2.2 OAuth 集成

#### Supabase Auth 配置
```typescript
// lib/auth/supabase.ts
import { createClientComponentClient } from '@supabase/auth-helpers-nextjs'
import { Database } from '@/types/database'

export const supabase = createClientComponentClient<Database>()

// 登录函数
export const signInWithEmail = async (email: string, password: string) => {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })

  if (error) throw error

  // 获取用户权限
  const { data: permissions } = await supabase
    .from('user_permissions')
    .select(`
      permission_id,
      permissions (
        name,
        description
      )
    `)
    .eq('user_id', data.user?.id)

  return {
    user: data.user,
    session: data.session,
    permissions: permissions?.map(p => p.permissions) || []
  }
}

// 注册函数
export const signUpWithEmail = async (
  email: string,
  password: string,
  metadata: Record<string, any>
) => {
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: metadata
    }
  })

  if (error) throw error
  return data
}
```

### 2.3 多因素认证 (MFA)

```python
# backend/app/auth/mfa.py
import pyotp
import qrcode
from io import BytesIO
import base64

class MFAService:
    def __init__(self):
        self.app_name = "AI广告代投系统"

    def generate_secret(self) -> str:
        """生成MFA密钥"""
        return pyotp.random_base32()

    def generate_qr_code(self, user_email: str, secret: str) -> str:
        """生成QR码"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name=self.app_name
        )

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')

        return base64.b64encode(buffer.getvalue()).decode()

    def verify_token(self, secret: str, token: str) -> bool:
        """验证MFA令牌"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)

    def generate_backup_codes(self) -> list[str]:
        """生成备用代码"""
        import secrets
        return [secrets.token_hex(4).upper() for _ in range(10)]

# API端点
@router.post("/mfa/setup")
async def setup_mfa(
    current_user: User = Depends(get_current_user)
):
    """设置MFA"""
    mfa_service = MFAService()
    secret = mfa_service.generate_secret()
    qr_code = mfa_service.generate_qr_code(current_user.email, secret)
    backup_codes = mfa_service.generate_backup_codes()

    # 临时存储密钥（需要在验证后永久保存）
    await redis.setex(f"mfa_setup:{current_user.id}", 600, secret)

    return {
        "qr_code": qr_code,
        "secret": secret,
        "backup_codes": backup_codes
    }

@router.post("/mfa/verify")
async def verify_mfa_setup(
    token: str,
    current_user: User = Depends(get_current_user)
):
    """验证MFA设置"""
    secret = await redis.get(f"mfa_setup:{current_user.id}")
    if not secret:
        raise HTTPException(status_code=400, detail="MFA设置已过期")

    mfa_service = MFAService()
    if not mfa_service.verify_token(secret, token):
        raise HTTPException(status_code=400, detail="无效的MFA令牌")

    # 永久保存MFA密钥
    current_user.mfa_secret = secret
    current_user.mfa_enabled = True
    db.commit()

    # 清除临时密钥
    await redis.delete(f"mfa_setup:{current_user.id}")

    return {"message": "MFA设置成功"}
```

---

## 3. 数据传输安全

### 3.1 HTTPS 配置

#### Nginx SSL 配置
```nginx
# nginx/conf.d/ssl.conf
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL 证书配置
    ssl_certificate /etc/ssl/certs/yourdomain.com.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.com.key;

    # SSL 协议配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;

    # 加密套件配置
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384;
    ssl_ciphers 'TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384';

    # SSL 会话配置
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    ssl_session_tickets off;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # HSTS (HTTP Strict Transport Security)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

    # 其他安全头
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

    # CSP (Content Security Policy)
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; frame-ancestors 'none';" always;
}
```

#### 前端 HTTPS 配置
```typescript
// next.config.js
const nextConfig = {
  // 强制 HTTPS
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'Strict-Transport-Security',
            value: 'max-age=31536000; includeSubDomains; preload',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
    ]
  },
}

module.exports = nextConfig
```

### 3.2 API 传输安全

#### 请求签名验证
```python
# backend/app/security/signature.py
import hmac
import hashlib
import time
from fastapi import Request, HTTPException

class SignatureValidator:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key.encode()

    def generate_signature(self, timestamp: str, nonce: str, body: str) -> str:
        """生成请求签名"""
        message = f"{timestamp}{nonce}{body}".encode()
        return hmac.new(
            self.secret_key,
            message,
            hashlib.sha256
        ).hexdigest()

    def verify_signature(
        self,
        request: Request,
        signature: str,
        timestamp: str,
        nonce: str
    ) -> bool:
        """验证请求签名"""
        try:
            # 检查时间戳（防止重放攻击）
            request_time = int(timestamp)
            current_time = int(time.time())
            if abs(current_time - request_time) > 300:  # 5分钟有效期
                return False

            # 检查nonce（防止重复请求）
            if redis.exists(f"nonce:{nonce}"):
                return False

            # 读取请求体
            body = await request.body()
            body_str = body.decode()

            # 生成预期签名
            expected_signature = self.generate_signature(timestamp, nonce, body_str)

            # 验证签名
            if not hmac.compare_digest(signature, expected_signature):
                return False

            # 标记nonce已使用
            redis.setex(f"nonce:{nonce}", 300, "used")

            return True

        except Exception:
            return False

# 中间件使用
signature_validator = SignatureValidator(secret_key=env.SIGNATURE_SECRET)

async def verify_request_signature(request: Request):
    signature = request.headers.get("X-Signature")
    timestamp = request.headers.get("X-Timestamp")
    nonce = request.headers.get("X-Nonce")

    if not all([signature, timestamp, nonce]):
        raise HTTPException(status_code=401, detail="缺少签名信息")

    if not signature_validator.verify_signature(request, signature, timestamp, nonce):
        raise HTTPException(status_code=401, detail="签名验证失败")
```

### 3.3 WebSocket 安全

```python
# backend/app/websocket/security.py
from fastapi import WebSocket, HTTPException
import jwt
import json

class WebSocketAuth:
    @staticmethod
    async def authenticate(websocket: WebSocket):
        """WebSocket连接认证"""
        try:
            # 获取认证token
            token = await websocket.receive_text()

            # 验证token格式
            if token.startswith("Bearer "):
                token = token[7:]

            # 验证JWT
            payload = jwt.decode(
                token,
                env.JWT_SECRET,
                algorithms=[env.JWT_ALGORITHM]
            )

            # 检查用户状态
            user = db.query(User).filter(User.id == payload["sub"]).first()
            if not user or not user.is_active:
                await websocket.close(code=1008, reason="用户认证失败")
                return None

            return user

        except Exception:
            await websocket.close(code=1008, reason="认证失败")
            return None

    @staticmethod
    async def authorize(user: User, resource: str, action: str):
        """WebSocket权限检查"""
        if not has_permission(user, f"{resource}:{action}"):
            raise HTTPException(status_code=403, detail="权限不足")

# WebSocket路由使用
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    # 认证
    user = await WebSocketAuth.authenticate(websocket)
    if not user:
        return

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message = json.loads(data)

            # 验证消息格式和权限
            resource = message.get("resource")
            action = message.get("action")

            if resource and action:
                await WebSocketAuth.authorize(user, resource, action)

            # 处理消息
            await handle_message(websocket, user, message)

    except Exception as e:
        await websocket.close(code=1011, reason=str(e))
```

---

## 4. 数据存储安全

### 4.1 数据库加密

#### 敏感字段加密
```python
# backend/app/security/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class DataEncryption:
    def __init__(self, master_key: str):
        self.key = self._derive_key(master_key)
        self.cipher = Fernet(self.key)

    def _derive_key(self, master_key: str) -> bytes:
        """从主密钥派生加密密钥"""
        salt = b'ai_ad_spend_salt'  # 在生产环境中使用随机盐
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(master_key.encode()))

    def encrypt(self, data: str) -> str:
        """加密数据"""
        if not data:
            return data
        encrypted_data = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted_data).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """解密数据"""
        if not encrypted_data:
            return encrypted_data
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception:
            raise ValueError("解密失败")

# 数据库模型中的加密字段使用
class User(Base):
    __tablename__ = "users"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String)  # 加密存储

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._encryption = DataEncryption(env.ENCRYPTION_MASTER_KEY)

    @property
    def phone_decrypted(self) -> str:
        """获取解密的手机号"""
        return self._encryption.decrypt(self.phone) if self.phone else ""

    @phone.setter
    def phone_encrypted(self, value: str):
        """设置加密的手机号"""
        self.phone = self._encryption.encrypt(value) if value else None

# 自动加密装饰器
def encrypt_sensitive_fields(fields: list[str]):
    """自动加密敏感字段的装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            encryption = DataEncryption(env.ENCRYPTION_MASTER_KEY)

            # 加密输入参数中的敏感字段
            for field in fields:
                if field in kwargs:
                    kwargs[field] = encryption.encrypt(str(kwargs[field]))

            result = func(*args, **kwargs)

            # 解密结果中的敏感字段
            if isinstance(result, dict):
                for field in fields:
                    if field in result:
                        result[field] = encryption.decrypt(result[field])

            return result
        return wrapper
    return decorator
```

### 4.2 数据库连接安全

```python
# backend/app/database/security.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool
import ssl

# 安全的数据库连接配置
def create_secure_database_url() -> str:
    """创建安全的数据库连接URL"""
    base_url = env.DATABASE_URL

    # 添加SSL参数
    ssl_params = {
        "sslmode": "require",
        "sslcert": "/etc/ssl/certs/client-cert.pem",
        "sslkey": "/etc/ssl/private/client-key.pem",
        "sslrootcert": "/etc/ssl/certs/ca-cert.pem",
    }

    # 构建安全连接字符串
    from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

    parsed = urlparse(base_url)
    query = parse_qs(parsed.query)

    # 添加SSL参数
    for key, value in ssl_params.items():
        query[key] = [value]

    secure_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        urlencode(query, doseq=True),
        parsed.fragment
    ))

    return secure_url

# 创建数据库引擎
engine = create_engine(
    create_secure_database_url(),
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={
        "sslcontext": ssl.create_default_context(
            cafile="/etc/ssl/certs/ca-cert.pem",
            certfile="/etc/ssl/certs/client-cert.pem",
            keyfile="/etc/ssl/private/client-key.pem"
        ),
        "options": "-c statement_timeout=30000"
    }
)
```

---

## 5. API安全防护

### 5.1 速率限制

```python
# backend/app/security/rate_limit.py
import redis
import time
from fastapi import Request, HTTPException
from typing import Optional

class RateLimiter:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def is_allowed(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, Optional[int]]:
        """
        检查是否允许请求
        :param key: 限制键（通常是IP或用户ID）
        :param limit: 请求次数限制
        :param window: 时间窗口（秒）
        :return: (是否允许, 剩余请求次数)
        """
        current_time = int(time.time())
        window_start = current_time - window

        # 清理过期记录
        self.redis.zremrangebyscore(key, 0, window_start)

        # 获取当前窗口内的请求次数
        current_requests = self.redis.zcard(key)

        if current_requests >= limit:
            # 获取最早的请求时间，计算重置时间
            earliest_request = self.redis.zrange(key, 0, 0, withscores=True)
            reset_time = int(earliest_request[0][1]) + window if earliest_request else current_time + window
            return False, reset_time

        # 记录当前请求
        self.redis.zadd(key, {str(current_time): current_time})
        self.redis.expire(key, window)

        remaining = limit - current_requests - 1
        return True, remaining

# 不同级别的速率限制
RATE_LIMITS = {
    "global": {"limit": 100, "window": 60},      # 全局限制
    "auth": {"limit": 5, "window": 300},         # 认证相关
    "upload": {"limit": 10, "window": 3600},     # 文件上传
    "api": {"limit": 1000, "window": 3600},      # API调用
}

# 速率限制中间件
async def rate_limit_middleware(
    request: Request,
    call_next,
    redis_client: redis.Redis = Depends(get_redis)
):
    # 获取客户端IP
    client_ip = request.client.host
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    # 确定限制类型
    path = request.url.path
    if path.startswith("/auth/"):
        limit_type = "auth"
    elif path.startswith("/upload/"):
        limit_type = "upload"
    else:
        limit_type = "api"

    # 应用速率限制
    rate_limiter = RateLimiter(redis_client)
    key = f"rate_limit:{limit_type}:{client_ip}"
    limit_config = RATE_LIMITS[limit_type]

    is_allowed, remaining_or_reset = rate_limiter.is_allowed(
        key,
        limit_config["limit"],
        limit_config["window"]
    )

    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail="请求过于频繁，请稍后再试",
            headers={
                "X-RateLimit-Limit": str(limit_config["limit"]),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(remaining_or_reset),
                "Retry-After": str(limit_config["window"])
            }
        )

    # 添加响应头
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit_config["limit"])
    response.headers["X-RateLimit-Remaining"] = str(remaining_or_reset)

    return response
```

### 5.2 输入验证和过滤

```python
# backend/app/security/validation.py
import re
import html
from typing import Any, Dict, List
from pydantic import validator

class SecurityValidator:
    @staticmethod
    def sanitize_input(input_string: str) -> str:
        """清理输入字符串"""
        if not input_string:
            return ""

        # HTML转义
        sanitized = html.escape(input_string)

        # 移除潜在的危险字符
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\n', '\r', '\t']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')

        return sanitized.strip()

    @staticmethod
    def validate_email(email: str) -> bool:
        """验证邮箱格式"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """验证手机号格式"""
        pattern = r'^1[3-9]\d{9}$'
        return re.match(pattern, phone) is not None

    @staticmethod
    def validate_password(password: str) -> tuple[bool, List[str]]:
        """验证密码强度"""
        errors = []

        if len(password) < 8:
            errors.append("密码长度至少8位")

        if not re.search(r'[a-z]', password):
            errors.append("密码必须包含小写字母")

        if not re.search(r'[A-Z]', password):
            errors.append("密码必须包含大写字母")

        if not re.search(r'\d', password):
            errors.append("密码必须包含数字")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("密码必须包含特殊字符")

        return len(errors) == 0, errors

# Pydantic模型中的安全验证
class UserCreate(BaseModel):
    email: str
    password: str
    phone: Optional[str] = None
    name: str

    @validator('email')
    def validate_email(cls, v):
        if not SecurityValidator.validate_email(v):
            raise ValueError('邮箱格式不正确')
        return v.lower()

    @validator('phone')
    def validate_phone(cls, v):
        if v and not SecurityValidator.validate_phone(v):
            raise ValueError('手机号格式不正确')
        return v

    @validator('password')
    def validate_password(cls, v):
        is_valid, errors = SecurityValidator.validate_password(v)
        if not is_valid:
            raise ValueError('密码不符合要求: ' + ', '.join(errors))
        return v

    @validator('name')
    def sanitize_name(cls, v):
        return SecurityValidator.sanitize_input(v)
```

### 5.3 SQL注入防护

```python
# backend/app/security/sql_injection.py
from sqlalchemy import text
from sqlalchemy.orm import Session
import re

class SQLInjectionProtection:
    @staticmethod
    def detect_sql_injection(input_string: str) -> bool:
        """检测SQL注入攻击"""
        # 常见的SQL注入模式
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+\'\w+\'\s*=\s*\'\w+\')",
            r"(\b(OR|AND)\s+\w+\s*=\s*\w+)",
            r"(--|#|\/\*|\*\/)",
            r"(;\s*(DROP|DELETE|UPDATE|INSERT)\b)",
            r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT|ONLOAD|ONERROR)\b)",
        ]

        for pattern in sql_patterns:
            if re.search(pattern, input_string, re.IGNORECASE):
                return True

        return False

    @staticmethod
    def validate_query_parameters(params: Dict[str, Any]) -> bool:
        """验证查询参数"""
        for key, value in params.items():
            if isinstance(value, str):
                if SQLInjectionProtection.detect_sql_injection(value):
                    raise SecurityError(f"检测到SQL注入攻击: {key}={value}")
        return True

# 安全的数据库查询函数
def safe_execute_query(
    db: Session,
    query: str,
    params: Dict[str, Any] = None
):
    """安全执行数据库查询"""
    try:
        # 验证查询参数
        if params:
            SQLInjectionProtection.validate_query_parameters(params)

        # 使用参数化查询
        result = db.execute(text(query), params or {})
        return result

    except Exception as e:
        # 记录安全事件
        log_security_event("sql_injection_attempt", {
            "query": query,
            "params": params,
            "error": str(e)
        })
        raise

# 安全的动态查询构建
class SafeQueryBuilder:
    def __init__(self, model_class):
        self.model_class = model_class
        self.query = None
        self.filters = []

    def add_filter(self, field_name: str, operator: str, value: Any):
        """添加安全的过滤条件"""
        # 验证字段名是否存在
        if not hasattr(self.model_class, field_name):
            raise ValueError(f"字段 '{field_name}' 不存在")

        # 验证操作符
        allowed_operators = ['=', '!=', '>', '<', '>=', '<=', 'like', 'ilike', 'in']
        if operator not in allowed_operators:
            raise ValueError(f"不支持的操作符 '{operator}'")

        # 验证值
        if isinstance(value, str):
            if SQLInjectionProtection.detect_sql_injection(value):
                raise SecurityError(f"检测到SQL注入攻击: {value}")

        self.filters.append((field_name, operator, value))
        return self

    def build_query(self, db: Session):
        """构建安全的查询"""
        query = db.query(self.model_class)

        for field_name, operator, value in self.filters:
            field = getattr(self.model_class, field_name)

            if operator == '=':
                query = query.filter(field == value)
            elif operator == '!=':
                query = query.filter(field != value)
            elif operator == '>':
                query = query.filter(field > value)
            elif operator == '<':
                query = query.filter(field < value)
            elif operator == '>=':
                query = query.filter(field >= value)
            elif operator == '<=':
                query = query.filter(field <= value)
            elif operator == 'like':
                query = query.filter(field.like(f"%{value}%"))
            elif operator == 'ilike':
                query = query.filter(field.ilike(f"%{value}%"))
            elif operator == 'in':
                query = query.filter(field.in_(value))

        return query
```

---

## 6. Web应用安全

### 6.1 XSS防护

```python
# backend/app/security/xss.py
import html
import re
from markupsafe import Markup, escape
from typing import Any

class XSSProtection:
    @staticmethod
    def sanitize_html(input_string: str) -> str:
        """清理HTML输入，防止XSS攻击"""
        if not input_string:
            return ""

        # HTML转义
        sanitized = html.escape(input_string)

        # 移除危险的事件处理器和属性
        dangerous_patterns = [
            r'on\w+\s*=',           # 事件处理器
            r'javascript:',         # JavaScript协议
            r'vbscript:',           # VBScript协议
            r'data:',               # Data协议
            r'<script[^>]*>',       # Script标签
            r'</script>',           # Script结束标签
            r'<iframe[^>]*>',       # iframe标签
            r'<object[^>]*>',       # object标签
            r'<embed[^>]*>',        # embed标签
            r'<form[^>]*>',         # form标签
            r'<input[^>]*>',        # input标签
            r'expression\s*\(',     # CSS表达式
        ]

        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)

        return sanitized

    @staticmethod
    def sanitize_json(data: Any) -> Any:
        """清理JSON数据"""
        if isinstance(data, str):
            return XSSProtection.sanitize_html(data)
        elif isinstance(data, dict):
            return {key: XSSProtection.sanitize_json(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [XSSProtection.sanitize_json(item) for item in data]
        else:
            return data

# FastAPI响应中间件
from fastapi import Response
from fastapi.responses import JSONResponse

async def xss_protection_middleware(request: Request, call_next):
    response = await call_next(request)

    # 添加XSS保护头
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["X-Content-Type-Options"] = "nosniff"

    # 如果是JSON响应，清理内容
    if (
        isinstance(response, JSONResponse) and
        hasattr(response, 'body') and
        response.body
    ):
        try:
            import json
            data = json.loads(response.body.decode())
            sanitized_data = XSSProtection.sanitize_json(data)
            response.body = json.dumps(sanitized_data).encode()
        except:
            pass

    return response
```

### 6.2 CSRF防护

```python
# backend/app/security/csrf.py
import secrets
import hashlib
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

class CSRFProtection:
    def __init__(self):
        self.token_length = 32
        self.header_name = "X-CSRF-Token"
        self.cookie_name = "csrf_token"

    def generate_token(self) -> str:
        """生成CSRF令牌"""
        return secrets.token_urlsafe(self.token_length)

    def verify_token(self, request: Request, token: str) -> bool:
        """验证CSRF令牌"""
        # 从Cookie中获取存储的令牌
        stored_token = request.cookies.get(self.cookie_name)

        if not stored_token:
            return False

        # 使用安全的比较方法防止时序攻击
        return secrets.compare_digest(stored_token, token)

    def set_token_cookie(self, response: Response, token: str):
        """设置CSRF令牌Cookie"""
        response.set_cookie(
            key=self.cookie_name,
            value=token,
            max_age=3600,  # 1小时
            secure=True,   # 仅HTTPS
            httponly=True, # 仅HTTP
            samesite='strict'
        )

# CSRF依赖
security = HTTPBearer()
csrf_protection = CSRFProtection()

async def verify_csrf_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """验证CSRF令牌的依赖函数"""

    # 对于安全的方法（GET, HEAD, OPTIONS）不需要CSRF保护
    if request.method in ["GET", "HEAD", "OPTIONS"]:
        return

    # 从请求头获取CSRF令牌
    csrf_token = request.headers.get(csrf_protection.header_name)

    if not csrf_token:
        raise HTTPException(status_code=403, detail="缺少CSRF令牌")

    # 验证令牌
    if not csrf_protection.verify_token(request, csrf_token):
        raise HTTPException(status_code=403, detail="无效的CSRF令牌")

# 前端CSRF集成
# 前端需要在请求头中包含CSRF令牌
const csrfToken = getCookie('csrf_token');
fetch('/api/projects', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-CSRF-Token': csrfToken,
  },
  body: JSON.stringify(projectData),
});
```

---

## 7. RLS行级安全策略

### 7.1 RLS策略配置

```sql
-- 启用RLS
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE recharge_requests ENABLE ROW LEVEL SECURITY;

-- 创建RLS策略

-- 项目访问策略
CREATE POLICY project_access_policy ON projects
    USING (
        -- 管理员全权限
        current_setting('app.current_role') = 'admin'
        OR
        -- 户管可访问所有项目
        current_setting('app.current_role') = 'data_clerk'
        OR
        -- 投手只能访问分配给自己的项目
        EXISTS (
            SELECT 1 FROM ad_accounts aa
            WHERE aa.project_id = projects.id
            AND aa.assigned_user_id = current_setting('app.current_user_id')::uuid
        )
        OR
        -- 项目经理只能访问自己的项目
        manager_id = current_setting('app.current_user_id')::uuid
    );

-- 广告账户访问策略
CREATE POLICY ad_account_access_policy ON ad_accounts
    USING (
        -- 管理员全权限
        current_setting('app.current_role') = 'admin'
        OR
        -- 户管可访问所有账户
        current_setting('app.current_role') = 'data_clerk'
        OR
        -- 投手只能访问分配给自己的账户
        assigned_user_id = current_setting('app.current_user_id')::uuid
    );

-- 日报访问策略
CREATE POLICY daily_report_access_policy ON daily_reports
    USING (
        -- 管理员全权限
        current_setting('app.current_role') = 'admin'
        OR
        -- 户管可访问所有日报
        current_setting('app.current_role') = 'data_clerk'
        OR
        -- 投手只能访问自己的日报
        user_id = current_setting('app.current_user_id')::uuid
        OR
        -- 投手可以访问自己负责账户的日报
        EXISTS (
            SELECT 1 FROM ad_accounts aa
            WHERE aa.id = daily_reports.ad_account_id
            AND aa.assigned_user_id = current_setting('app.current_user_id')::uuid
        )
    );

-- 充值请求访问策略
CREATE POLICY recharge_request_access_policy ON recharge_requests
    USING (
        -- 管理员全权限
        current_setting('app.current_role') = 'admin'
        OR
        -- 户管和财务可访问所有充值请求
        current_setting('app.current_role') IN ('data_clerk', 'finance')
        OR
        -- 投手只能访问自己的充值请求
        requester_id = current_setting('app.current_user_id')::uuid
    );

-- 用户权限策略
CREATE POLICY user_access_policy ON users
    USING (
        -- 管理员可访问所有用户
        current_setting('app.current_role') = 'admin'
        OR
        -- 用户只能访问自己的信息
        id = current_setting('app.current_user_id')::uuid
    );
```

### 7.2 中间件注入用户上下文

```python
# backend/app/middleware/rls.py
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio

class RLSContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 获取用户信息
        user = await get_current_user_optional(request)

        if user:
            # 设置RLS上下文
            request.state.db_session.execute(
                text("SELECT set_config('app.current_user_id', :user_id, true)"),
                {"user_id": str(user.id)}
            )

            request.state.db_session.execute(
                text("SELECT set_config('app.current_role', :role, true)"),
                {"role": user.role}
            )
        else:
            # 清除RLS上下文
            request.state.db_session.execute(
                text("SELECT set_config('app.current_user_id', '', true)")
            )

            request.state.db_session.execute(
                text("SELECT set_config('app.current_role', '', true)")
            )

        response = await call_next(request)
        return response

# 数据库连接函数
def get_db_with_rls():
    """获取带有RLS上下文的数据库会话"""
    db = SessionLocal()
    try:
        # 确保RLS配置正确
        db.execute(text("SET row_security = on"))
        yield db
    finally:
        db.close()
```

---

## 8. 安全监控和审计

### 8.1 安全事件记录

```python
# backend/app/security/audit.py
import json
import asyncio
from datetime import datetime
from enum import Enum

class SecurityEventType(str, Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PERMISSION_CHANGE = "permission_change"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SECURITY_VIOLATION = "security_violation"

class SecurityAuditor:
    def __init__(self, redis_client, db_session):
        self.redis = redis_client
        self.db = db_session

    async def log_security_event(
        self,
        event_type: SecurityEventType,
        user_id: str = None,
        ip_address: str = None,
        user_agent: str = None,
        resource: str = None,
        action: str = None,
        details: dict = None,
        risk_level: str = "low"  # low, medium, high, critical
    ):
        """记录安全事件"""
        event_data = {
            "event_type": event_type,
            "user_id": user_id,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "resource": resource,
            "action": action,
            "details": details or {},
            "risk_level": risk_level,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # 存储到Redis（实时访问）
        await self.redis.lpush(
            "security_events",
            json.dumps(event_data)
        )

        # 设置过期时间（30天）
        await self.redis.expire("security_events", 2592000)

        # 如果是高风险事件，立即写入数据库
        if risk_level in ["high", "critical"]:
            await self._write_to_database(event_data)

        # 触发告警
        if risk_level in ["medium", "high", "critical"]:
            await self._trigger_alert(event_data)

    async def _write_to_database(self, event_data: dict):
        """写入数据库"""
        try:
            audit_log = SecurityLog(
                event_type=event_data["event_type"],
                user_id=event_data.get("user_id"),
                ip_address=event_data.get("ip_address"),
                user_agent=event_data.get("user_agent"),
                resource=event_data.get("resource"),
                action=event_data.get("action"),
                details=event_data["details"],
                risk_level=event_data["risk_level"],
                timestamp=datetime.utcnow()
            )

            self.db.add(audit_log)
            self.db.commit()

        except Exception as e:
            print(f"Failed to write security event to database: {e}")

    async def _trigger_alert(self, event_data: dict):
        """触发安全告警"""
        alert_data = {
            "type": "security_alert",
            "event_type": event_data["event_type"],
            "risk_level": event_data["risk_level"],
            "user_id": event_data.get("user_id"),
            "ip_address": event_data.get("ip_address"),
            "timestamp": event_data["timestamp"],
            "details": event_data["details"]
        }

        # 发送到告警系统
        await self.redis.publish("security_alerts", json.dumps(alert_data))

        # 发送邮件/短信通知（对于高风险事件）
        if event_data["risk_level"] == "critical":
            await self._send_emergency_notification(alert_data)

# 安全监控装饰器
def audit_security_event(
    event_type: SecurityEventType,
    resource: str = None,
    action: str = None,
    risk_level: str = "low"
):
    """安全审计装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 获取请求上下文
            request = kwargs.get('request')
            if not request:
                return await func(*args, **kwargs)

            user = getattr(request.state, 'current_user', None)

            try:
                # 执行原函数
                result = await func(*args, **kwargs)

                # 记录成功事件
                await request.state.security_auditor.log_security_event(
                    event_type=event_type,
                    user_id=user.id if user else None,
                    ip_address=request.client.host,
                    user_agent=request.headers.get("User-Agent"),
                    resource=resource,
                    action=action,
                    risk_level=risk_level,
                    details={"status": "success"}
                )

                return result

            except Exception as e:
                # 记录失败事件
                await request.state.security_auditor.log_security_event(
                    event_type=SecurityEventType.SECURITY_VIOLATION,
                    user_id=user.id if user else None,
                    ip_address=request.client.host,
                    user_agent=request.headers.get("User-Agent"),
                    resource=resource,
                    action=action,
                    risk_level="high",
                    details={
                        "status": "error",
                        "error": str(e),
                        "function": func.__name__
                    }
                )

                raise

        return wrapper
    return decorator
```

### 8.2 异常行为检测

```python
# backend/app/security/anomaly_detection.py
import asyncio
from datetime import datetime, timedelta
from collections import defaultdict, deque
import numpy as np

class AnomalyDetector:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.user_behaviors = defaultdict(lambda: deque(maxlen=100))
        self.ip_behaviors = defaultdict(lambda: deque(maxlen=100))

    async def detect_login_anomalies(self, user_id: str, ip_address: str):
        """检测登录异常"""
        anomalies = []

        # 检查异常登录时间
        recent_logins = await self._get_recent_logins(user_id, hours=24)
        if recent_logins:
            login_times = [login['timestamp'] for login in recent_logins]
            if len(login_times) >= 3:
                # 检查是否在异常时间登录（比如凌晨3-6点）
                current_hour = datetime.now().hour
                if 3 <= current_hour <= 6:
                    normal_hours = [int(dt.hour) for dt in login_times]
                    if current_hour not in normal_hours:
                        anomalies.append({
                            "type": "unusual_login_time",
                            "severity": "medium",
                            "description": "异常登录时间",
                            "current_hour": current_hour,
                            "normal_hours": normal_hours
                        })

        # 检查异常IP地址
        user_ips = await self._get_user_ips(user_id, days=30)
        if ip_address not in user_ips:
            # 检查IP地理位置（需要IP地理位置服务）
            is_suspicious = await self._check_ip_reputation(ip_address)
            anomalies.append({
                "type": "new_ip_address",
                "severity": "high" if is_suspicious else "medium",
                "description": "新IP地址登录",
                "ip_address": ip_address,
                "known_ips": list(user_ips)
            })

        # 检查登录频率异常
        recent_attempts = await self._get_recent_login_attempts(ip_address, minutes=10)
        if len(recent_attempts) > 5:
            anomalies.append({
                "type": "high_frequency_login",
                "severity": "high",
                "description": "高频登录尝试",
                "attempts": len(recent_attempts),
                "time_window": "10 minutes"
            })

        return anomalies

    async def detect_data_access_anomalies(self, user_id: str, resource: str, action: str):
        """检测数据访问异常"""
        anomalies = []

        # 检查异常访问模式
        access_pattern = await self._get_user_access_pattern(user_id, hours=1)

        # 检查访问频率异常
        if len(access_pattern) > 100:  # 1小时内访问超过100次
            anomalies.append({
                "type": "high_frequency_access",
                "severity": "medium",
                "description": "高频数据访问",
                "access_count": len(access_pattern),
                "time_window": "1 hour"
            })

        # 检查异常资源访问
        user_resources = await self._get_user_accessible_resources(user_id, days=7)
        if resource not in user_resources:
            anomalies.append({
                "type": "unusual_resource_access",
                "severity": "high",
                "description": "访问异常资源",
                "resource": resource,
                "usual_resources": list(user_resources)[:10]
            })

        return anomalies

    async def _get_recent_logins(self, user_id: str, hours: int = 24):
        """获取最近登录记录"""
        key = f"user_logins:{user_id}"
        events = await self.redis.lrange(key, 0, -1)

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_logins = []

        for event in events:
            data = json.loads(event)
            event_time = datetime.fromisoformat(data['timestamp'])
            if event_time >= cutoff_time:
                recent_logins.append(data)

        return recent_logins

    async def _check_ip_reputation(self, ip_address: str) -> bool:
        """检查IP声誉"""
        # 这里可以集成第三方IP声誉检查服务
        # 比如VirusTotal, AbuseIPDB等
        suspicious_indicators = [
            "proxy" in ip_address,
            "tor" in ip_address,
            self._is_private_ip(ip_address)
        ]

        return any(suspicious_indicators)

    def _is_private_ip(self, ip_address: str) -> bool:
        """检查是否为私有IP"""
        try:
            import ipaddress
            ip = ipaddress.ip_address(ip_address)
            return ip.is_private
        except:
            return False

# 异常检测中间件
async def anomaly_detection_middleware(request: Request, call_next):
    """异常检测中间件"""
    user = getattr(request.state, 'current_user', None)

    if not user:
        return await call_next(request)

    # 检测异常
    detector = AnomalyDetector(redis_client)

    # 检查登录异常
    if "/auth/login" in str(request.url):
        anomalies = await detector.detect_login_anomalies(
            user.id,
            request.client.host
        )

        if anomalies:
            for anomaly in anomalies:
                await request.state.security_auditor.log_security_event(
                    event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                    user_id=user.id,
                    ip_address=request.client.host,
                    risk_level=anomaly["severity"],
                    details=anomaly
                )

    # 检测数据访问异常
    if request.method in ["GET", "POST", "PUT", "DELETE"]:
        # 解析请求路径和操作
        path_parts = request.url.path.strip("/").split("/")
        if len(path_parts) >= 2:
            resource = path_parts[1]
            action = request.method.lower()

            anomalies = await detector.detect_data_access_anomalies(
                user.id,
                resource,
                action
            )

            if anomalies:
                for anomaly in anomalies:
                    await request.state.security_auditor.log_security_event(
                        event_type=SecurityEventType.SUSPICIOUS_ACTIVITY,
                        user_id=user.id,
                        ip_address=request.client.host,
                        risk_level=anomaly["severity"],
                        details=anomaly
                    )

    return await call_next(request)
```

---

## 9. 漏洞管理

### 9.1 安全漏洞扫描

```bash
#!/bin/bash
# scripts/security_scan.sh

echo "开始安全漏洞扫描..."

# 依赖漏洞扫描
echo "1. 扫描Python依赖漏洞..."
pip-audit

echo "2. 扫描Node.js依赖漏洞..."
npm audit --audit-level=moderate

# Docker安全扫描
echo "3. Docker镜像安全扫描..."
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    aquasec/trivy image ai-ad-spend:latest

# 代码安全扫描
echo "4. 代码安全扫描..."
bandit -r backend/ -f json -o security_report_backend.json
semgrep --config=auto backend/ --json -o security_report_semgrep.json

# 网络安全扫描
echo "5. 网络安全扫描..."
nmap -sV -oN nmap_scan.txt localhost

echo "安全扫描完成，请查看报告文件。"
```

### 9.2 安全补丁管理

```python
# backend/app/security/patch_management.py
import subprocess
import json
import asyncio
from datetime import datetime, timedelta
import requests

class SecurityPatchManager:
    def __init__(self):
        self.patch_window = timedelta(days=7)  # 7天内应用补丁
        self.critical_patch_window = timedelta(days=1)  # 1天内应用关键补丁

    async def check_for_security_updates(self):
        """检查安全更新"""
        vulnerabilities = []

        # 检查Python包安全更新
        python_vulns = await self._check_python_security_updates()
        vulnerabilities.extend(python_vulns)

        # 检查系统安全更新
        system_vulns = await self._check_system_security_updates()
        vulnerabilities.extend(system_vulns)

        # 按严重程度分类
        critical_vulns = [v for v in vulnerabilities if v['severity'] == 'critical']
        high_vulns = [v for v in vulnerabilities if v['severity'] == 'high']

        # 立即处理关键漏洞
        if critical_vulns:
            await self._handle_critical_vulnerabilities(critical_vulns)

        # 调度高优先级漏洞修复
        if high_vulns:
            await self._schedule_vulnerability_fixes(high_vulns)

        return vulnerabilities

    async def _check_python_security_updates(self):
        """检查Python包安全更新"""
        try:
            # 使用pip-audit检查
            result = subprocess.run(
                ['pip-audit', '--format', 'json'],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                audit_data = json.loads(result.stdout)
                vulnerabilities = []

                for vuln in audit_data.get('vulnerabilities', []):
                    vulnerabilities.append({
                        'type': 'python_package',
                        'package': vuln['name'],
                        'version': vuln['installed_version'],
                        'fixed_version': vuln.get('fixed_versions', ['Unknown'])[0],
                        'severity': vuln['severity'],
                        'description': vuln['description'],
                        'cve': vuln.get('cve', '')
                    })

                return vulnerabilities

        except Exception as e:
            print(f"Failed to check Python security updates: {e}")

        return []

    async def _handle_critical_vulnerabilities(self, vulnerabilities):
        """处理关键漏洞"""
        for vuln in vulnerabilities:
            # 立即通知安全团队
            await self._send_security_alert({
                'type': 'critical_vulnerability',
                'package': vuln['package'],
                'severity': vuln['severity'],
                'cve': vuln.get('cve', ''),
                'description': vuln['description'],
                'action_required': 'immediate'
            })

            # 记录安全事件
            await self._log_security_event({
                'event_type': 'critical_vulnerability_detected',
                'details': vuln,
                'timestamp': datetime.utcnow().isoformat()
            })

    async def _send_security_alert(self, alert_data):
        """发送安全告警"""
        # 集成告警系统（Slack, 邮件, 短信等）
        webhook_url = os.getenv('SECURITY_WEBHOOK_URL')

        if webhook_url:
            payload = {
                'text': f'🚨 安全告警: {alert_data["type"]}',
                'attachments': [{
                    'color': 'danger',
                    'fields': [
                        {'title': '包名', 'value': alert_data['package'], 'short': True},
                        {'title': '严重程度', 'value': alert_data['severity'], 'short': True},
                        {'title': 'CVE', 'value': alert_data.get('cve', 'N/A'), 'short': True},
                        {'title': '描述', 'value': alert_data['description'], 'short': False},
                    ]
                }]
            }

            requests.post(webhook_url, json=payload)

# 安全补丁调度任务
async def schedule_security_patch_checks():
    """调度安全补丁检查"""
    while True:
        try:
            patch_manager = SecurityPatchManager()
            vulnerabilities = await patch_manager.check_for_security_updates()

            print(f"Found {len(vulnerabilities)} security vulnerabilities")

        except Exception as e:
            print(f"Error in security patch check: {e}")

        # 每24小时检查一次
        await asyncio.sleep(86400)
```

---

## 10. 安全测试

### 10.1 渗透测试指南

```python
# tests/security/pentest_checklist.py
"""
安全渗透测试检查清单
"""

PENTEST_CHECKLIST = {
    "认证和授权": [
        "弱密码测试",
        "默认凭据测试",
        "会话管理测试",
        "权限绕过测试",
        "多因素认证绕过测试",
        "密码策略测试",
        "账户锁定测试",
        "JWT令牌测试",
        "OAuth流程测试",
    ],

    "输入验证": [
        "SQL注入测试",
        "NoSQL注入测试",
        "XSS攻击测试",
        "CSRF攻击测试",
        "命令注入测试",
        "XML外部实体攻击测试",
        "文件上传漏洞测试",
        "参数污染测试",
        "HTTP参数注入测试",
    ],

    "会话管理": [
        "会话令牌生成测试",
        "会话固定攻击测试",
        "会话劫持测试",
        "会话超时测试",
        "并发会话测试",
        "会话注销测试",
        "跨站请求伪造测试",
    ],

    "加密和敏感数据处理": [
        "敏感数据泄露测试",
        "加密算法强度测试",
        "密钥管理测试",
        "传输加密测试",
        "存储加密测试",
        "随机数生成测试",
        "哈希函数测试",
        "证书验证测试",
    ],

    "业务逻辑": [
        "工作流绕过测试",
        "价格操纵测试",
        "竞态条件测试",
        "逻辑缺陷测试",
        "业务流程绕过测试",
        "权限提升测试",
        "数据完整性测试",
    ],

    "基础设施": [
        "服务器配置测试",
        "网络安全测试",
        "容器安全测试",
        "云服务配置测试",
        "API网关测试",
        "负载均衡器测试",
        "DNS安全测试",
        "DDoS防护测试",
    ]
}

# 自动化安全测试
class SecurityTestCase:
    def __init__(self):
        self.vulnerable_payloads = [
            {"test": "SQL注入", "payloads": ["'", "OR '1'='1", "DROP TABLE", "UNION SELECT"]},
            {"test": "XSS攻击", "payloads": ["<script>alert('XSS')</script>", "<img src=x onerror=alert('XSS')>"]},
            {"test": "命令注入", "payloads": ["; ls", "| whoami", "&& cat /etc/passwd"]},
            {"test": "路径遍历", "payloads": ["../../../etc/passwd", "..\\..\\windows\\system32"]},
        ]

    async def run_security_tests(self, base_url: str):
        """运行自动化安全测试"""
        results = []

        for test_case in self.vulnerable_payloads:
            for payload in test_case["payloads"]:
                result = await self._test_payload(base_url, test_case["test"], payload)
                results.append(result)

        return results

    async def _test_payload(self, base_url: str, test_type: str, payload: str):
        """测试特定payload"""
        import aiohttp
        import asyncio

        try:
            async with aiohttp.ClientSession() as session:
                # 测试不同的端点
                endpoints = [
                    "/api/projects",
                    "/api/users",
                    "/api/auth/login",
                    "/api/search",
                ]

                vulnerabilities = []

                for endpoint in endpoints:
                    # 测试GET参数
                    async with session.get(
                        f"{base_url}{endpoint}",
                        params={"q": payload}
                    ) as response:
                        if await self._check_vulnerability(response, payload):
                            vulnerabilities.append({
                                "method": "GET",
                                "endpoint": endpoint,
                                "parameter": "q",
                                "payload": payload
                            })

                    # 测试POST数据
                    async with session.post(
                        f"{base_url}{endpoint}",
                        json={"data": payload}
                    ) as response:
                        if await self._check_vulnerability(response, payload):
                            vulnerabilities.append({
                                "method": "POST",
                                "endpoint": endpoint,
                                "parameter": "data",
                                "payload": payload
                            })

                return {
                    "test_type": test_type,
                    "payload": payload,
                    "vulnerabilities": vulnerabilities,
                    "status": "vulnerable" if vulnerabilities else "safe"
                }

        except Exception as e:
            return {
                "test_type": test_type,
                "payload": payload,
                "error": str(e),
                "status": "error"
            }

    async def _check_vulnerability(self, response, payload):
        """检查是否存在漏洞"""
        text = await response.text()

        # 检查错误信息泄露
        error_indicators = [
            "syntax error",
            "mysql_fetch",
            "ORA-",
            "Microsoft OLE DB",
            "Warning: mysql",
            "valid PostgreSQL result",
        ]

        for indicator in error_indicators:
            if indicator.lower() in text.lower():
                return True

        # 检查XSS执行
        if "<script>" in payload and "<script>" in text:
            return True

        # 检查系统命令执行
        command_indicators = ["uid=", "gid=", "root:", "bin/"]
        for indicator in command_indicators:
            if indicator in text:
                return True

        return False
```

### 10.2 安全测试自动化

```python
# tests/security/security_tests.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app

class TestSecurity:

    def test_sql_injection_protection(self, client: TestClient):
        """测试SQL注入防护"""
        malicious_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM users --",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ]

        for payload in malicious_payloads:
            response = client.get(
                "/api/projects",
                params={"search": payload}
            )

            # 应该返回400错误或正常响应，但不应该是500错误
            assert response.status_code in [200, 400, 422]

            # 响应中不应该包含数据库错误信息
            assert "error" not in response.text.lower()
            assert "mysql" not in response.text.lower()
            assert "syntax" not in response.text.lower()

    def test_xss_protection(self, client: TestClient):
        """测试XSS防护"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>"
        ]

        for payload in xss_payloads:
            response = client.post(
                "/api/projects",
                json={
                    "name": payload,
                    "description": payload
                }
            )

            if response.status_code == 200:
                # 检查返回的数据是否被正确转义
                response_data = response.json()
                assert "<script>" not in str(response_data)
                assert "javascript:" not in str(response_data)

    def test_rate_limiting(self, client: TestClient):
        """测试速率限制"""
        # 快速发送多个请求
        responses = []
        for i in range(10):
            response = client.post(
                "/api/auth/login",
                json={
                    "email": "test@example.com",
                    "password": "wrongpassword"
                }
            )
            responses.append(response)

        # 检查是否有请求被限制
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "速率限制没有生效"

    def test_authentication_required(self, client: TestClient):
        """测试认证要求"""
        protected_endpoints = [
            "/api/projects",
            "/api/users",
            "/api/reports",
            "/api/recharge-requests"
        ]

        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"{endpoint} 应该需要认证"

    def test_authorization_check(self, client: TestClient):
        """测试权限检查"""
        # 使用普通用户权限尝试访问管理员功能
        client.headers["Authorization"] = "Bearer normal_user_token"

        admin_endpoints = [
            "/api/admin/users",
            "/api/admin/system-config",
            "/api/admin/security-logs"
        ]

        for endpoint in admin_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 403, f"{endpoint} 应该需要管理员权限"

    def test_csrf_protection(self, client: TestClient):
        """测试CSRF防护"""
        # 尝试没有CSRF令牌的POST请求
        response = client.post(
            "/api/projects",
            json={"name": "Test Project"}
        )

        # 应该返回403或包含CSRF令牌要求
        assert response.status_code in [403, 422]

# 集成到CI/CD的安全测试
if __name__ == "__main__":
    # 运行安全测试
    pytest.run(["tests/security/security_tests.py", "-v"])

    # 生成安全报告
    security_scanner = SecurityTestCase()
    results = asyncio.run(security_scanner.run_security_tests("http://localhost:8000"))

    print("安全测试完成")
    for result in results:
        if result["status"] == "vulnerable":
            print(f"发现漏洞: {result['test_type']}")
            for vuln in result["vulnerabilities"]:
                print(f"  - {vuln}")
```

---

## 📞 安全支持

### 安全团队联系
- **安全负责人**: security@company.com
- **安全工程师**: security-engineer@company.com
- **安全事件响应**: security-incident@company.com

### 安全资源
- **安全文档**: https://security.yourdomain.com
- **漏洞报告**: https://vulnerability.yourdomain.com
- **安全策略**: https://policy.yourdomain.com
- **安全培训**: https://training.yourdomain.com

### 应急响应
- **24/7 安全热线**: +86-xxx-xxxx-xxxx
- **安全事件报告**: security-incident@company.com
- **漏洞悬赏计划**: https://bugbounty.yourdomain.com

---

**文档版本**: v1.0
**最后更新**: 2025-11-11
**下次审查**: 安全策略更新时
**维护责任人**: 安全团队负责人