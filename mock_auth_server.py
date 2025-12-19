"""
模拟认证服务器
用于测试前端注册/登录流程，绕过 Python 3.14 + Supabase 兼容性问题
"""

import json
import uuid
import http.server
import socketserver
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs
import os

# 模拟用户存储
users_db = {}
sessions_db = {}

PORT = 8000

class AuthHandler(http.server.BaseHTTPRequestHandler):

    def _set_headers(self, status_code=200, content_type='application/json'):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def _send_json(self, data, status_code=200):
        self._set_headers(status_code)
        response = json.dumps(data, ensure_ascii=False, default=str)
        self.wfile.write(response.encode('utf-8'))

    def _success_response(self, data=None, message="success"):
        return {
            "success": True,
            "data": data,
            "error": None,
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _error_response(self, code, message, status_code=400):
        return {
            "success": False,
            "data": None,
            "error": {
                "code": code,
                "message": message
            },
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }

    def _read_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length:
            return json.loads(self.rfile.read(content_length).decode('utf-8'))
        return {}

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        path = urlparse(self.path).path

        if path == '/api/v1/auth/me':
            return self._handle_get_me()
        elif path == '/health':
            return self._send_json({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})
        else:
            self._send_json(self._error_response("NOT_FOUND", f"路径 {path} 不存在"), 404)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == '/api/v1/auth/register':
            return self._handle_register()
        elif path == '/api/v1/auth/login':
            return self._handle_login()
        elif path == '/api/v1/auth/logout':
            return self._handle_logout()
        elif path == '/api/v1/auth/refresh':
            return self._handle_refresh()
        else:
            self._send_json(self._error_response("NOT_FOUND", f"路径 {path} 不存在"), 404)

    def _handle_register(self):
        """处理注册请求"""
        try:
            body = self._read_body()
            email = body.get('email', '')
            password = body.get('password', '')
            username = body.get('username', '')
            full_name = body.get('full_name', '')

            # 验证
            if not email or not password or not username:
                self._send_json(self._error_response("VALIDATION_001", "缺少必填字段"), 400)
                return

            if len(password) < 8:
                self._send_json(self._error_response("VALIDATION_001", "密码长度至少8位"), 400)
                return

            # 检查邮箱是否已存在
            if email in users_db:
                self._send_json(self._error_response("AUTH_004", "该邮箱已被注册"), 400)
                return

            # 创建用户
            user_id = str(uuid.uuid4())
            user = {
                "id": user_id,
                "email": email,
                "username": username,
                "full_name": full_name or email.split('@')[0],
                "role": "media_buyer",
                "is_active": True,
                "created_at": datetime.utcnow().isoformat(),
            }
            users_db[email] = {**user, "password": password}

            # 创建会话
            access_token = f"mock_token_{uuid.uuid4().hex}"
            refresh_token = f"mock_refresh_{uuid.uuid4().hex}"
            sessions_db[access_token] = {
                "user_id": user_id,
                "email": email,
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }

            response_data = {
                "user": user,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": 3600,
                "token_type": "Bearer"
            }

            print(f"[REGISTER] 新用户注册: {email} (ID: {user_id})")
            self._send_json(self._success_response(response_data, "注册成功"), 201)

        except Exception as e:
            print(f"[ERROR] 注册失败: {e}")
            self._send_json(self._error_response("AUTH_002", str(e)), 500)

    def _handle_login(self):
        """处理登录请求"""
        try:
            body = self._read_body()
            identifier = body.get('identifier', '')  # 可以是邮箱或用户名
            password = body.get('password', '')

            # 查找用户
            user_data = None
            for email, data in users_db.items():
                if email == identifier or data.get('username') == identifier:
                    user_data = data
                    break

            if not user_data:
                self._send_json(self._error_response("AUTH_001", "用户不存在"), 401)
                return

            if user_data['password'] != password:
                self._send_json(self._error_response("AUTH_001", "密码错误"), 401)
                return

            # 创建会话
            access_token = f"mock_token_{uuid.uuid4().hex}"
            refresh_token = f"mock_refresh_{uuid.uuid4().hex}"
            sessions_db[access_token] = {
                "user_id": user_data['id'],
                "email": user_data['email'],
                "expires_at": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }

            user = {k: v for k, v in user_data.items() if k != 'password'}

            response_data = {
                "user": user,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": 3600,
                "token_type": "Bearer"
            }

            print(f"[LOGIN] 用户登录: {user_data['email']}")
            self._send_json(self._success_response(response_data, "登录成功"))

        except Exception as e:
            print(f"[ERROR] 登录失败: {e}")
            self._send_json(self._error_response("AUTH_001", str(e)), 500)

    def _handle_get_me(self):
        """获取当前用户信息"""
        auth_header = self.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            self._send_json(self._error_response("AUTH_003", "未授权"), 401)
            return

        token = auth_header[7:]
        session = sessions_db.get(token)

        if not session:
            self._send_json(self._error_response("AUTH_003", "无效的令牌"), 401)
            return

        # 查找用户
        user_data = users_db.get(session['email'])
        if not user_data:
            self._send_json(self._error_response("AUTH_005", "用户不存在"), 404)
            return

        user = {k: v for k, v in user_data.items() if k != 'password'}
        self._send_json(self._success_response({"user": user, "profile": user}))

    def _handle_logout(self):
        """处理登出请求"""
        auth_header = self.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            if token in sessions_db:
                del sessions_db[token]
                print(f"[LOGOUT] 用户登出")

        self._send_json(self._success_response({"logged_out_at": datetime.utcnow().isoformat()}, "登出成功"))

    def _handle_refresh(self):
        """刷新令牌"""
        body = self._read_body()
        refresh_token = body.get('refresh_token', '')

        if not refresh_token:
            self._send_json(self._error_response("AUTH_006", "缺少刷新令牌"), 400)
            return

        # 简单模拟：生成新令牌
        new_access_token = f"mock_token_{uuid.uuid4().hex}"
        new_refresh_token = f"mock_refresh_{uuid.uuid4().hex}"

        response_data = {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "expires_in": 3600,
            "token_type": "Bearer"
        }

        self._send_json(self._success_response(response_data, "令牌刷新成功"))

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


def run_server():
    with socketserver.TCPServer(("", PORT), AuthHandler) as httpd:
        print("="*60)
        print(f"  模拟认证服务器已启动")
        print(f"  地址: http://localhost:{PORT}")
        print("="*60)
        print(f"\n可用端点:")
        print(f"  POST /api/v1/auth/register  - 用户注册")
        print(f"  POST /api/v1/auth/login     - 用户登录")
        print(f"  POST /api/v1/auth/logout    - 用户登出")
        print(f"  GET  /api/v1/auth/me        - 获取当前用户")
        print(f"  POST /api/v1/auth/refresh   - 刷新令牌")
        print(f"  GET  /health                - 健康检查")
        print(f"\n按 Ctrl+C 停止服务器\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务器已停止")


if __name__ == "__main__":
    run_server()
