# AI广告代投系统开发文档 v2.2 - AI辅助协作版

> **文档版本**: v2.2 AI辅助协作版
> **更新日期**: 2025-11-11
> **维护团队**: 系统架构团队
> **文档目的**: 提供完整的技术架构、AI辅助开发指南和云地协作部署运维规范

> 本文档在 v2.1 基础上全面整合了bolt.new前端AI开发和Claude Code后端AI协作模式，新增了云地协作开发流程、AI编程最佳实践和混合部署策略，为企业级AI辅助开发提供了完整的技术指导和实施规范。

---

## 📋 目录

1. [系统结构概览](#一系统结构概览)
2. [核心状态机定义](#二核心状态机定义)
3. [数据库设计](#三数据库设计)
4. [安全策略与权限控制](#四安全策略与权限控制)
5. [API接口规范](#五api接口规范)
6. [错误码定义](#六错误码定义)
7. [环境配置](#七环境配置)
8. [AI辅助开发系统](#八ai辅助开发系统)
9. [部署运维指南](#九部署运维指南)
10. [开发阶段划分](#十开发阶段划分)
11. [验收标准](#十一验收标准)
12. [AI辅助开发模式](#十二ai辅助开发模式)
13. [AI辅助开发最佳实践](#十三ai辅助开发最佳实践)

---

## 一、系统结构概览

### 技术栈推荐（AI辅助协作组合）

#### 前端技术栈（bolt.new AI辅助开发）
- **框架**：Next.js 14 + TypeScript + Tailwind CSS
- **UI组件库**：shadcn/ui + Radix UI
- **状态管理**：Zustand + SWR（数据获取）
- **开发环境**：bolt.new（在线IDE + AI辅助编程）
- **部署方式**：bolt.new自动部署 + CDN托管
- **特色功能**：
  - 自然语言生成React组件
  - 实时预览和热重载
  - AI自动样式优化（Tailwind）
  - 智能依赖管理和包安装

#### 后端技术栈（Claude Code AI辅助开发）
- **框架**：FastAPI + Pydantic v2 + SQLAlchemy（同步版）
- **AI开发工具**：Claude Code（本地AI辅助编程）
- **数据库**：PostgreSQL（Supabase托管）
- **缓存/队列**：Redis + RQ（任务调度、通知、AI检测）
- **认证安全**：JWT + bcrypt + RLS策略
- **特色功能**：
  - AI自动生成CRUD API
  - 智能测试用例生成
  - 自动代码质量检查
  - 实时代码审查和优化建议

#### 协作桥梁技术
- **API隧道**：ngrok（本地API外网访问）
- **版本控制**：Git + GitHub/GitLab
- **实时同步**：Git hooks + 自动化部署
- **接口规范**：OpenAPI 3.0 + Swagger文档
- **跨域处理**：CORS配置 + API代理

#### 监控和运维
- **日志监控**：Loki + Promtail + Grafana + Sentry
- **性能监控**：APM工具 + 自定义指标
- **安全监控**：漏洞扫描 + 异常检测
- **部署运维**：Docker Compose + Nginx + 混合部署

### 系统架构图（AI辅助协作模式）
```
┌─────────────────────────────────────────────────────────────┐
│                云端前端层 (bolt.new)                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  AI组件生成  │ │   实时预览   │ │   在线部署   │           │
│  │ React/Next  │ │  热重载      │ │  CDN托管     │           │
│  │ shadcn/ui   │ │ Tailwind     │ │ 自定义域名   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  协作桥梁技术      │
                    │ ┌─────┐ ┌─────┐   │
                    │ │ngrok│ │ Git │   │
                    │ │隧道 │ │同步 │   │
                    │ └─────┘ └─────┘   │
                    └─────────┬─────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│              本地后端层 (Claude Code)                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │  AI API生成  │ │  智能测试    │ │  代码审查    │           │
│  │  FastAPI     │ │  自动化      │ │  质量保证    │           │
│  │ Pydantic v2  │ │ pytest      │ │  Security   │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │     云数据层       │
                    │ ┌─────────────────┐ │
                    │ │  PostgreSQL     │ │
                    │ │  (Supabase)     │ │
                    │ │  + RLS安全      │ │
                    │ └─────────────────┘ │
                    └───────────────────┘
```

### AI辅助开发流程图
```
开发阶段 ：
┌─────────────────────────────────────────────────────────────┐
│  需求分析 → AI设计 → 代码生成 → 质量检查 → 部署上线          │
│    │         │         │         │         │               │
│    ▼         ▼         ▼         ▼         ▼               │
│  业务描述  架构设计  AI生成   自动测试  自动部署           │
│  用户故事  接口设计  代码审查  性能分析  监控告警           │
│  功能清单  数据模型  重构优化  安全扫描  文档同步           │
└─────────────────────────────────────────────────────────────┘

技术栈协作：
bolt.new（前端） ←→ Git版本控制 ←→ Claude Code（后端）
      ↓                              ↓
  AI组件生成                    AI API生成
      ↓                              ↓
  CDN托管部署                本地开发环境
      ↓                              ↓
  用户界面交互                业务逻辑处理
      ↓                              ↓
              Supabase数据库（统一数据层）
```

---

## 二、核心状态机定义

### 1. 充值申请状态机
| 状态 | 描述 | 可操作角色 | 下一状态 | 自动触发条件 |
|------|------|-------------|-----------|-------------|
| **draft** | 投手提交 | 投手 | pending | 手动提交 |
| **pending** | 审核中 | 户管 | approved / rejected | 手动审批 |
| **approved** | 财务批准 | 财务 | paid | 手动批准 |
| **paid** | 已支付 | 系统 | posted | 支付确认 |
| **posted** | 已入账 | 系统 | — | 入账完成 |
| **rejected** | 被驳回 | 户管/财务 | draft | 驳回后可重新提交 |

### 2. 日报审核状态机
| 状态 | 描述 | 可操作角色 | 下一状态 | 自动触发条件 |
|------|------|-------------|-----------|-------------|
| **draft** | 投手填写 | 投手 | pending | 自动保存 |
| **pending** | 审核中 | 数据员 | approved / rejected | 提交审核 |
| **approved** | 已通过 | 系统 | — | 审核通过 |
| **rejected** | 异常退回 | 数据员 | draft | 审核驳回 |

### 3. 账户生命周期状态机
| 状态 | 说明 | 自动触发条件 | 可操作角色 |
|------|------|-----------------|-------------|
| **new** | 新建 | 创建时 | 户管 |
| **testing** | 测试期 | 7日内稳定消耗 | 系统 |
| **active** | 正常投放 | 日均>100USD | 系统 |
| **suspended** | 暂停 | 3天无消耗 | 系统/户管 |
| **dead** | 封禁 | FB返回异常 | 系统 |
| **archived** | 归档 | 管理员手动 | 管理员 |

---

## 三、数据库设计

### 1. 核心表结构

#### 用户表 (users)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'data_clerk', 'finance', 'media_buyer')),
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

#### 项目表 (projects)
```sql
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    client_name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed')),
    budget DECIMAL(12,2),
    start_date DATE,
    end_date DATE,
    manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_manager ON projects(manager_id);
```

#### 渠道表 (channels)
```sql
CREATE TABLE channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    company_name VARCHAR(200) NOT NULL,
    contact_info JSONB,
    service_fee_rate DECIMAL(5,2) DEFAULT 0.05,
    account_setup_fee DECIMAL(10,2) DEFAULT 0,
    min_recharge_amount DECIMAL(10,2) DEFAULT 100,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 广告账户表 (ad_accounts)
```sql
CREATE TABLE ad_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    account_id VARCHAR(100) NOT NULL, -- FB账号ID
    platform VARCHAR(20) NOT NULL DEFAULT 'facebook',
    status VARCHAR(20) NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'testing', 'active', 'suspended', 'dead', 'archived')),
    daily_budget DECIMAL(10,2),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    assigned_user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    channel_id UUID REFERENCES channels(id) ON DELETE SET NULL,
    api_credentials JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ad_accounts_project ON ad_accounts(project_id);
CREATE INDEX idx_ad_accounts_user ON ad_accounts(assigned_user_id);
CREATE INDEX idx_ad_accounts_status ON ad_accounts(status);
```

#### 日报表 (daily_reports)
```sql
CREATE TABLE daily_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    report_date DATE NOT NULL,
    spend DECIMAL(10,2) NOT NULL,
    impressions BIGINT,
    clicks BIGINT,
    conversions INTEGER,
    cpl DECIMAL(8,2), -- cost per lead
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('draft', 'pending', 'approved', 'rejected')),
    submitted_at TIMESTAMP,
    approved_by UUID REFERENCES users(id),
    approved_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(ad_account_id, report_date)
);

CREATE INDEX idx_daily_reports_account_date ON daily_reports(ad_account_id, report_date);
CREATE INDEX idx_daily_reports_status ON daily_reports(status);
```

#### 充值申请表 (recharge_requests)
```sql
CREATE TABLE recharge_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    ad_account_id UUID NOT NULL REFERENCES ad_accounts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    amount DECIMAL(10,2) NOT NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'pending', 'approved', 'rejected', 'paid', 'posted')),
    data_clerk_id UUID REFERENCES users(id),
    data_clerk_approved_at TIMESTAMP,
    finance_id UUID REFERENCES users(id),
    finance_approved_at TIMESTAMP,
    paid_at TIMESTAMP,
    posted_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recharge_requests_project ON recharge_requests(project_id);
CREATE INDEX idx_recharge_requests_status ON recharge_requests(status);
```

### 2. 外键约束规则

所有资金类表必须包含完整的外键追溯：
```sql
-- 外键约束示例
ALTER TABLE daily_reports
ADD CONSTRAINT fk_daily_reports_account
FOREIGN KEY (ad_account_id) REFERENCES ad_accounts(id) ON DELETE CASCADE;

ALTER TABLE daily_reports
ADD CONSTRAINT fk_daily_reports_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
```

---

## 四、安全策略与权限控制

### 1. RLS 策略与中间件注入

#### RLS中间件
```python
# middleware/rls_context.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

class RLSContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user = getattr(request.state, 'user', None)
        if user:
            # 使用同步SQLAlchemy连接
            db: Session = request.state.db
            try:
                db.execute(f"SELECT set_config('app.current_user_id', '{user.id}', true)")
                db.execute(f"SELECT set_config('app.current_role', '{user.role}', true)")
                db.commit()
            except Exception as e:
                db.rollback()
                raise e

        response = await call_next(request)
        return response
```

#### RLS策略示例
```sql
-- 启用RLS
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE ad_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE daily_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE recharge_requests ENABLE ROW LEVEL SECURITY;

-- 项目访问策略
CREATE POLICY project_access_policy ON projects
    USING (
        current_setting('app.current_role') = 'admin'
        OR created_by = current_setting('app.current_user_id')::uuid
        OR EXISTS (
            SELECT 1 FROM ad_accounts
            WHERE ad_accounts.project_id = projects.id
            AND ad_accounts.assigned_user_id = current_setting('app.current_user_id')::uuid
        )
    );

-- 广告账户访问策略
CREATE POLICY ad_account_access_policy ON ad_accounts
    USING (
        current_setting('app.current_role') = 'admin'
        OR current_setting('app.current_role') = 'data_clerk'
        OR assigned_user_id = current_setting('app.current_user_id')::uuid
    );

-- 日报访问策略
CREATE POLICY daily_report_access_policy ON daily_reports
    USING (
        current_setting('app.current_role') = 'admin'
        OR current_setting('app.current_role') = 'data_clerk'
        OR user_id = current_setting('app.current_user_id')::uuid
        OR EXISTS (
            SELECT 1 FROM ad_accounts
            WHERE ad_accounts.id = daily_reports.ad_account_id
            AND ad_accounts.assigned_user_id = current_setting('app.current_user_id')::uuid
        )
    );

-- 充值请求访问策略
CREATE POLICY recharge_request_access_policy ON recharge_requests
    USING (
        current_setting('app.current_role') = 'admin'
        OR current_setting('app.current_role') IN ('data_clerk', 'finance')
        OR user_id = current_setting('app.current_user_id')::uuid
    );
```

### 2. 权限矩阵
| 功能模块 | 投手 | 户管 | 财务 | 管理员 |
|----------|------|------|------|----------|
| 项目管理 | 查看自己项目 | 全权限 | 查看 | 全权限 |
| 账户管理 | 查看自己账户 | 分配/管理 | 查看 | 全权限 |
| 日报管理 | 提交/查看自己日报 | 审核/查看 | 查看 | 全权限 |
| 充值管理 | 申请/查看 | 初审 | 终审 | 全权限 |
| 对账管理 | - | 查看 | 创建/管理 | 全权限 |

---

## 五、API接口规范

### 1. bolt.new协作开发接口规范

#### API版本控制
```typescript
// bolt.new前端API客户端配置
const API_CONFIG = {
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL,
  version: 'v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  }
};

// API客户端封装
import axios from 'axios';

class ApiClient {
  private baseURL: string;
  private version: string;

  constructor() {
    this.baseURL = `${API_CONFIG.baseURL}/api/${API_CONFIG.version}`;
    this.setupInterceptors();
  }

  private setupInterceptors() {
    // 请求拦截器
    axios.interceptors.request.use((config) => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      config.headers['X-Request-ID'] = this.generateRequestId();
      return config;
    });

    // 响应拦截器
    axios.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          await this.refreshToken();
        }
        return Promise.reject(this.handleError(error));
      }
    );
  }

  // 统一的API调用方法
  async request<T>(config: AxiosRequestConfig): Promise<ApiResponse<T>> {
    try {
      const response = await axios({
        ...config,
        baseURL: this.baseURL,
      });
      return response.data;
    } catch (error) {
      throw this.handleError(error);
    }
  }
}

// 类型定义
interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
  request_id: string;
  timestamp: string;
}
```

#### 跨域配置（CORS）
```python
# 后端CORS中间件配置
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

app = FastAPI()

# 配置CORS，允许bolt.new域名访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-bolt-new-project.bolt.new",  # bolt.new域名
        "https://your-custom-domain.com",          # 自定义域名
        "http://localhost:3000",                   # 本地开发
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Total-Count"],
)
```

#### 实时数据同步
```typescript
// WebSocket连接管理
class WebSocketManager {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;

  connect() {
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('WebSocket连接已建立');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onclose = () => {
      console.log('WebSocket连接已关闭');
      this.attemptReconnect();
    };
  }

  private handleMessage(data: any) {
    switch (data.type) {
      case 'status_update':
        this.updateStatus(data.payload);
        break;
      case 'new_notification':
        this.showNotification(data.payload);
        break;
      case 'data_refresh':
        this.refreshData(data.payload);
        break;
    }
  }
}
```

### 2. 统一响应结构
```json
{
  "success": true,
  "data": {...},
  "message": "操作成功",
  "code": "SUCCESS",
  "request_id": "uuid-string",
  "timestamp": "2025-11-11T10:30:00Z"
}
```

### 2. 错误响应结构
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数验证失败",
    "details": {
      "field": "email",
      "reason": "邮箱格式不正确"
    }
  },
  "request_id": "uuid-string",
  "timestamp": "2025-11-11T10:30:00Z"
}
```

### 3. 接口示例

#### 新建充值申请
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

# Pydantic模型
class TopupCreate(BaseModel):
    project_id: str
    ad_account_id: str
    amount: float
    notes: str = None

    class Config:
        from_attributes = True

# API路由
@router.post('/api/topups/request')
async def create_topup(
    req: TopupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建充值申请"""
    try:
        # 验证权限
        account = db.query(AdAccount).filter(
            AdAccount.id == req.ad_account_id,
            AdAccount.project_id == req.project_id,
            AdAccount.assigned_user_id == current_user.id
        ).first()

        if not account:
            raise HTTPException(status_code=403, detail="无权限操作该账户")

        # 创建充值申请
        topup = RechargeRequest(
            project_id=req.project_id,
            ad_account_id=req.ad_account_id,
            user_id=current_user.id,
            amount=req.amount,
            notes=req.notes,
            status='draft'
        )

        db.add(topup)
        db.commit()
        db.refresh(topup)

        # 记录操作日志
        await log_action('topup', 'create', current_user.id, topup.id)

        return {
            "success": True,
            "data": topup,
            "message": "充值申请提交成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="内部服务器错误")
```

#### 对账接口
```python
@router.post('/api/reconciliation/run')
async def run_reconciliation(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """执行对账"""
    try:
        # 验证权限（财务或管理员）
        if current_user.role not in ['finance', 'admin']:
            raise HTTPException(status_code=403, detail="权限不足")

        # 获取项目数据
        spend_records = db.query(DailyReport).filter(
            DailyReport.project_id == project_id,
            DailyReport.status == 'approved'
        ).all()

        # 获取充值记录
        topup_records = db.query(RechargeRequest).filter(
            RechargeRequest.project_id == project_id,
            RechargeRequest.status == 'posted'
        ).all()

        # 计算差异
        total_spend = sum(record.spend for record in spend_records)
        total_topup = sum(record.amount for record in topup_records)
        difference = total_topup - total_spend

        # 创建对账记录
        reconciliation = Reconciliation(
            project_id=project_id,
            total_spend=total_spend,
            total_topup=total_topup,
            difference=difference,
            created_by=current_user.id
        )

        db.add(reconciliation)
        db.commit()
        db.refresh(reconciliation)

        return {
            "success": True,
            "data": {
                "reconciliation_id": reconciliation.id,
                "project_id": project_id,
                "total_spend": float(total_spend),
                "total_topup": float(total_topup),
                "difference": float(difference)
            },
            "message": "对账完成"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="对账失败")
```

---

## 六、错误码定义

### 1. 业务错误码
| 错误码 | 含义 | HTTP状态码 | 说明 |
|--------|------|-------------|------|
| SUCCESS | 成功 | 200 | 操作成功 |
| VALIDATION_ERROR | 参数校验错误 | 400 | Pydantic验证失败 |
| UNAUTHORIZED | 未登录或权限不足 | 401 | Token过期/角色不匹配 |
| FORBIDDEN | 禁止操作 | 403 | 当前状态不允许此操作 |
| NOT_FOUND | 资源不存在 | 404 | 无匹配记录 |
| STATE_ERROR | 状态错误 | 422 | 状态机不允许此操作 |
| RATE_LIMIT_EXCEEDED | 请求频率超限 | 429 | API调用频率限制 |
| INTERNAL_ERROR | 系统内部错误 | 500 | 异常捕获统一返回 |

### 2. 业务特定错误码
| 错误码 | 含义 | 触发场景 |
|--------|------|----------|
| PROJECT_NOT_FOUND | 项目不存在 | 查询的项目ID不存在 |
| ACCOUNT_NOT_ASSIGNED | 账户未分配 | 用户无权限操作该账户 |
| INSUFFICIENT_BALANCE | 余额不足 | 账户余额不足 |
| RECHARGE_AMOUNT_INVALID | 充值金额无效 | 金额不在允许范围内 |
| REPORT_ALREADY_EXISTS | 日报已存在 | 当日报表已提交 |
| INVALID_STATE_TRANSITION | 状态转换无效 | 状态机不允许该转换 |

### 3. 错误处理示例
```python
from fastapi import HTTPException
from pydantic import ValidationError

class BusinessException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code

async def exception_handler(request, exc: BusinessException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.code,
                "message": exc.message
            },
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# 使用示例
try:
    # 业务逻辑
    if not project:
        raise BusinessException("PROJECT_NOT_FOUND", "项目不存在", 404)
except BusinessException as e:
    raise HTTPException(status_code=e.status_code, detail={
        "code": e.code,
        "message": e.message
    })
```

---

## 七、环境配置

### 1. bolt.new前端环境配置

#### 项目初始化
```bash
# 在bolt.new中创建新项目
1. 访问 https://bolt.new
2. 选择 "Create New Project"
3. 选择 "Next.js" 模板
4. 配置项目设置：
   - Project Name: ai-ad-spend-frontend
   - Framework: Next.js 14
   - Language: TypeScript
   - Styling: Tailwind CSS
   - Package Manager: npm
```

#### 环境变量配置（bolt.new）
```bash
# .env.local (bolt.new项目根目录)
# API配置 - 连接本地后端
NEXT_PUBLIC_API_BASE_URL=https://your-ngrok-url.ngrok.io
NEXT_PUBLIC_API_VERSION=v1
NEXT_PUBLIC_WS_URL=ws://your-ngrok-url.ngrok.io/ws

# Supabase配置（前端直连，仅读取）
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# 应用配置
NEXT_PUBLIC_APP_NAME=AI广告代投系统
NEXT_PUBLIC_APP_VERSION=2.2.0
NEXT_PUBLIC_ENVIRONMENT=development

# 功能开关
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_ENABLE_ERROR_REPORTING=true
NEXT_PUBLIC_ENABLE_PERFORMANCE_MONITORING=true

# 第三方服务
NEXT_PUBLIC_SENTRY_DSN=https://your-sentry-dsn
NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=your-ga-id

# 开发工具
NEXT_PUBLIC_ENABLE_DEVTOOLS=true
NEXT_PUBLIC_LOG_LEVEL=debug
```

#### 项目依赖安装
```bash
# bolt.new终端中执行
npm install @shadcn/ui
npm install zustand swr axios
npm install @hookform/resolvers react-hook-form
npm install recharts lucide-react
npm install @radix-ui/react-dialog
npm install @radix-ui/react-dropdown-menu
npm install @radix-ui/react-select
npm install class-variance-authority clsx tailwind-merge
```

### 2. 本地后端环境配置

#### ngrok隧道配置
```bash
# 安装ngrok
npm install -g ngrok

# 启动本地后端（在另一个终端）
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 创建ngrok隧道
ngrok http 8000

# 输出示例：
# Forwarding https://random-string.ngrok.io -> http://localhost:8000
# 复制 https://random-string.ngrok.io 到前端环境变量中
```

#### 后端环境变量配置
```bash
# .env.example
# 应用配置
API_ENV=production
APP_NAME=AI广告代投系统
APP_VERSION=2.1.0
DEBUG=false
PORT=8000

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/ai_ad_spend
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Supabase配置
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret

# Redis配置
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=0

# JWT配置
JWT_SECRET=your-super-secret-key-32-characters-minimum-length
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS配置
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
ALLOWED_METHODS=GET,POST,PUT,DELETE,OPTIONS
ALLOWED_HEADERS=*

# 文件上传配置
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_PATH=./uploads
ALLOWED_EXTENSIONS=jpg,jpeg,png,pdf,xlsx,csv

# 外部API配置
FACEBOOK_API_VERSION=v18.0
FACEBOOK_APP_ID=your-app-id
FACEBOOK_APP_SECRET=your-app-secret
FACEBOOK_GRAPH_URL=https://graph.facebook.com

# 监控配置
SENTRY_DSN=https://your-dsn.ingest.sentry.io/project-id
LOG_LEVEL=INFO
LOG_FORMAT=json

# 邮件配置
SMTP_HOST=smtp.yourdomain.com
SMTP_PORT=587
SMTP_USER=your-email
SMTP_PASSWORD=your-email-password
SMTP_TLS=true

# 缓存配置
CACHE_TTL=3600
SESSION_TTL=86400

# 安全配置
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
BCRYPT_ROUNDS=12
```

### 2. Docker配置
```yaml
# docker-compose.yml
version: '3.8'

services:
  # 后端服务
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/ai_ad_spend
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    volumes:
      - ./uploads:/app/uploads

  # 数据库
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ai_ad_spend
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  # Redis缓存
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Nginx反向代理
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
```

---

## 八、AI模块接口

### 1. AI模块结构
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from pydantic import BaseModel
from datetime import date, datetime

class DailyReportData(BaseModel):
    """日报数据模型"""
    date: date
    account_id: str
    spend: float
    impressions: int
    clicks: int
    conversions: int
    cpl: Optional[float] = None

class AnomalyResult(BaseModel):
    """异常检测结果"""
    date: date
    account_id: str
    anomaly_type: str
    reason: str
    severity: str  # low, medium, high, critical
    confidence: float

class LifetimePrediction(BaseModel):
    """账户寿命预测结果"""
    account_id: str
    predicted_lifetime_days: int
    risk_level: str
    confidence_score: float
    key_factors: List[str]

class AIMonitorInterface(ABC):
    """AI监控接口定义"""

    @abstractmethod
    async def detect_spending_anomalies(self, daily_data: List[DailyReportData]) -> List[AnomalyResult]:
        """检测支出异常"""
        pass

    @abstractmethod
    async def predict_account_lifetime(self, account_id: str) -> LifetimePrediction:
        """预测账户寿命"""
        pass

    @abstractmethod
    async def detect_performance_decline(self, daily_data: List[DailyReportData]) -> List[AnomalyResult]:
        """检测性能下降"""
        pass

class AIMonitor(AIMonitorInterface):
    """AI监控实现"""

    def __init__(self):
        self.model_path = "./models/"
        self.thresholds = {
            "spending_deviation": 1.5,  # 支出偏差阈值
            "performance_decline": 0.3,  # 性能下降阈值
        }

    async def detect_spending_anomalies(self, daily_data: List[DailyReportData]) -> List[AnomalyResult]:
        """
        检测支出异常
        基于历史数据预测当日支出范围，超出150%认为是异常
        """
        anomalies = []

        for data in daily_data:
            # 计算历史支出均值和标准差
            historical_spend = [d.spend for d in daily_data if d.date < data.date]
            if len(historical_spend) < 7:  # 至少7天历史数据
                continue

            mean_spend = sum(historical_spend) / len(historical_spend)
            std_spend = (sum((x - mean_spend) ** 2 for x in historical_spend) / len(historical_spend)) ** 0.5

            # 检测异常
            if data.spend > mean_spend + self.thresholds["spending_deviation"] * std_spend:
                anomalies.append(AnomalyResult(
                    date=data.date,
                    account_id=data.account_id,
                    anomaly_type="spending_spike",
                    reason=f"支出异常偏高: ${data.spend:.2f} (历史均值: ${mean_spend:.2f})",
                    severity="high",
                    confidence=0.85
                ))

        return anomalies

    async def predict_account_lifetime(self, account_id: str) -> LifetimePrediction:
        """
        预测账户寿命
        基于账户表现指标预测剩余天数
        """
        # 这里应该加载训练好的机器学习模型
        # 目前使用简化规则作为示例

        # 获取账户历史数据
        # historical_data = await self._get_account_historical_data(account_id)

        # 简化预测逻辑（实际应该使用机器学习模型）
        # predicted_lifetime = self._apply_ml_model(historical_data)

        # 示例预测结果
        return LifetimePrediction(
            account_id=account_id,
            predicted_lifetime_days=45,
            risk_level="medium",
            confidence_score=0.75,
            key_factors=["spending_stability", "conversion_rate", "account_age"]
        )

    async def detect_performance_decline(self, daily_data: List[DailyReportData]) -> List[AnomalyResult]:
        """
        检测性能下降
        检测点击率、转化率等关键指标下降
        """
        anomalies = []

        for data in daily_data:
            # 计算CTR (Click-Through Rate)
            if data.impressions > 0:
                current_ctr = data.clicks / data.impressions

                # 获取历史CTR
                historical_data = [d for d in daily_data if d.date < data.date and d.impressions > 0]
                if len(historical_data) < 7:
                    continue

                historical_ctrs = [d.clicks / d.impressions for d in historical_data]
                avg_ctr = sum(historical_ctrs) / len(historical_ctrs)

                # 检测CTR下降
                if current_ctr < avg_ctr * (1 - self.thresholds["performance_decline"]):
                    anomalies.append(AnomalyResult(
                        date=data.date,
                        account_id=data.account_id,
                        anomaly_type="performance_decline",
                        reason=f"点击率下降: {current_ctr:.4f} (历史均值: {avg_ctr:.4f})",
                        severity="medium",
                        confidence=0.70
                    ))

        return anomalies

# AI任务调度
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

class AITaskScheduler:
    """AI任务调度器"""

    def __init__(self, ai_monitor: AIMonitor):
        self.scheduler = AsyncIOScheduler()
        self.ai_monitor = ai_monitor

    async def start(self):
        """启动调度器"""
        # 每天凌晨2点执行异常检测
        self.scheduler.add_job(
            self.run_daily_anomaly_detection,
            CronTrigger(hour=2, minute=0),
            id="daily_anomaly_detection"
        )

        # 每周一执行账户寿命预测
        self.scheduler.add_job(
            self.run_weekly_lifetime_prediction,
            CronTrigger(day_of_week=1, hour=3, minute=0),
            id="weekly_lifetime_prediction"
        )

        self.scheduler.start()

    async def run_daily_anomaly_detection(self):
        """执行每日异常检测"""
        try:
            # 获取前一天的日报数据
            yesterday = date.today() - timedelta(days=1)
            daily_data = await self._get_daily_reports(yesterday)

            # 执行异常检测
            anomalies = await self.ai_monitor.detect_spending_anomalies(daily_data)

            if anomalies:
                # 发送告警
                await self._send_anomaly_alerts(anomalies)

        except Exception as e:
            logger.error(f"AI异常检测失败: {e}")

    async def run_weekly_lifetime_prediction(self):
        """执行每周账户寿命预测"""
        try:
            # 获取所有活跃账户
            active_accounts = await self._get_active_accounts()

            predictions = []
            for account in active_accounts:
                prediction = await self.ai_monitor.predict_account_lifetime(account.id)
                predictions.append(prediction)

                # 检查是否需要预警
                if prediction.risk_level in ['high', 'critical']:
                    await self._send_lifetime_alert(prediction)

        except Exception as e:
            logger.error(f"账户寿命预测失败: {e}")
```

### 2. AI触发时机
| 模块 | 调用时机 | 数据源 | 频率 |
|------|-----------|--------|------|
| 支出异常检测 | 每日凌晨2点 | daily_reports | 每日 |
| 性能下降检测 | 每日凌晨2点 | daily_reports | 每日 |
| 账户寿命预测 | 每周一凌晨3点 | ad_accounts + daily_reports | 每周 |
| 实时异常告警 | 日报提交时 | single daily_report | 实时 |

---

## 九、部署运维指南

### 1. bolt.new + Claude Code混合部署架构

#### 部署架构概览
```
┌─────────────────────────────────────────────────────────────┐
│                    用户访问层                                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              自定义域名 + SSL                          │ │
│  │         ai-ads.yourdomain.com                           │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                bolt.new云端前端层                            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Next.js 应用 (AI辅助开发)                              │ │
│  │  • 自动部署到全球CDN                                     │ │
│  │  • 智能缓存和优化                                        │ │
│  │  • 实时预览和热重载                                      │ │
│  │  • 自动SSL证书                                           │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │     API网关       │
                    │  (负载均衡+路由)    │
                    └─────────┬─────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│              云服务器后端层                                 │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  FastAPI 应用 (Claude Code开发)                        │ │
│  │  • AI生成的API接口                                      │ │
│  │  • 自动化测试和质量检查                                  │ │
│  │  • 智能性能监控                                        │ │
│  │  • 自动扩展和负载均衡                                    │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                云数据服务层                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐         │
│  │ PostgreSQL  │ │    Redis     │ │   Supabase      │         │
│  │ 主数据库     │ │   缓存层     │ │  托管服务       │         │
│  │ + 备份策略   │ │ + 集群模式   │ │ + RLS安全       │         │
│  └─────────────┘ └─────────────┘ └─────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

#### bolt.new前端部署配置
```bash
# bolt.new自动部署流程
1. 开发完成 → Git提交
2. 自动触发CI/CD
3. 自动构建和测试
4. 自动部署到全球CDN
5. 自动SSL证书配置
6. 自动域名绑定

# 自定义域名配置
# 在bolt.new项目设置中：
Domain: ai-ads.yourdomain.com
SSL: 自动配置（Let's Encrypt）
CDN: 全球分布式部署
```

#### 云服务器后端部署
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  backend:
    image: ai-ads-backend:latest
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - backend

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups

  redis:
    image: redis:alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 2. 监控和运维配置

#### bolt.new前端监控
```typescript
// 性能监控配置
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 1.0,
  debug: false,
  replaysOnErrorSampleRate: 1.0,
  replaysSessionSampleRate: 0.1,
});

// 自定义性能指标
const performanceObserver = new PerformanceObserver((list) => {
  const entries = list.getEntries();
  entries.forEach((entry) => {
    if (entry.entryType === 'navigation') {
      const navEntry = entry as PerformanceNavigationTiming;
      console.log('页面加载时间:', navEntry.loadEventEnd - navEntry.loadEventStart);
    }
  });
});

performanceObserver.observe({ entryTypes: ['navigation', 'resource'] });
```

#### 后端监控配置
```python
# 监控中间件
from fastapi import Request
import time
import logging
from prometheus_client import Counter, Histogram, generate_latest

# Prometheus指标
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def monitoring_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    # 记录指标
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    REQUEST_DURATION.observe(time.time() - start_time)

    return response

# 健康检查端点
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.2.0",
        "environment": os.getenv("API_ENV", "development")
    }
```

### 3. 传统部署架构（备用方案）
```
┌─────────────────────────────────────────────────────────────┐
│                      负载均衡层                              │
│                   Nginx Reverse Proxy                       │
│                   SSL Termination                           │
│                   Rate Limiting                             │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      应用服务层                              │
│  ┌─────────────┐              ┌─────────────┐               │
│  │  Frontend   │              │   Backend    │               │
│  │ Next.js App │              │ FastAPI App  │               │
│  └─────────────┘              └─────────────┘               │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      数据服务层                              │
│  ┌─────────────┐              ┌─────────────┐               │
│  │ PostgreSQL  │              │    Redis     │               │
│  │ Supabase    │              │    Cache     │               │
│  └─────────────┘              └─────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### 2. 监控配置
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ai-ad-spend-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

rule_files:
  - "alert_rules.yml"
```

### 3. 告警规则
```yaml
# alert_rules.yml
groups:
  - name: application
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "应用错误率过高"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "数据库连接失败"
```

### 4. Nginx配置
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    server {
        listen 80;
        server_name yourdomain.com;

        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

---

## 十、开发阶段划分（AI辅助协作模式）

### 第一阶段：AI基础设施和核心功能（2周）
**目标**: 建立AI辅助开发环境和核心业务框架

| Day | 前端（bolt.new AI开发） | 后端（Claude Code AI开发） | 协作任务 | 交付物 |
|-----|----------------------|---------------------------|----------|--------|
| **1-2** | AI生成项目架构、组件库 | AI生成API框架、认证系统 | 配置ngrok隧道 | 基础架构 |
| **3-4** | AI生成用户管理界面 | AI生成权限系统API | 接口联调测试 | 用户系统 |
| **5-7** | AI生成项目管理界面 | AI生成项目管理API | 状态机验证 | 项目管理 |
| **8-9** | AI生成账户管理界面 | AI生成账户管理API | 数据权限测试 | 账户管理 |
| **10** | AI生成基础数据表格 | AI生成数据统计API | 性能优化测试 | 基础功能 |

### 第二阶段：AI辅助业务流程实现（2周）
**目标**: 完成核心业务流程的AI辅助开发

| Day | 前端（bolt.new AI开发） | 后端（Claude Code AI开发） | 协作任务 | 交付物 |
|-----|----------------------|---------------------------|----------|--------|
| **11-12** | AI生成日报提交表单 | AI生成日报审核API | 状态流程测试 | 日报系统 |
| **13-14** | AI生成审核流程界面 | AI生成状态机逻辑 | 业务规则验证 | 审核流程 |
| **15-16** | AI生成充值申请界面 | AI生成充值审批API | 财务流程测试 | 充值系统 |
| **17-18** | AI生成状态跟踪界面 | AI生成通知系统API | 实时同步测试 | 通知系统 |
| **19-20** | AI生成基础报表界面 | AI生成报表API | 数据可视化测试 | 报表系统 |

### 第三阶段：AI优化和系统集成（1周）
**目标**: AI驱动的性能优化和系统集成

| Day | 前端（bolt.new AI开发） | 后端（Claude Code AI开发） | 协作任务 | 交付物 |
|-----|----------------------|---------------------------|----------|--------|
| **21-22** | AI性能优化建议 | AI数据库查询优化 | 负载测试 | 性能优化 |
| **23-24** | AI安全漏洞扫描 | AI安全策略实现 | 安全测试 | 安全加固 |
| **25** | AI用户体验优化 | AI自动化测试生成 | 端到端测试 | 系统集成 |

### 第四阶段：AI测试和部署准备（1周）
**目标**: AI辅助的全面测试和生产部署

| Day | 前端（bolt.new AI开发） | 后端（Claude Code AI开发） | 协作任务 | 交付物 |
|-----|----------------------|---------------------------|----------|--------|
| **26** | AI生成用户测试用例 | AI生成API测试用例 | 测试用例执行 | 测试覆盖 |
| **27** | AI优化部署配置 | AI生成监控配置 | 监控系统测试 | 运维监控 |
| **28** | AI生成用户文档 | AI生成API文档 | 文档审核 | 技术文档 |

## AI辅助开发效率对比

### 传统开发 vs AI辅助开发
| 开发阶段 | 传统方式 | AI辅助开发 | 效率提升 |
|----------|----------|------------|----------|
| **基础架构** | 3-5天 | 1-2天 | 60-70% |
| **CRUD开发** | 5-7天/模块 | 1-2天/模块 | 70-80% |
| **表单开发** | 2-3天/表单 | 0.5-1天/表单 | 75-80% |
| **测试编写** | 2-3天/模块 | 0.5-1天/模块 | 75-85% |
| **文档编写** | 1-2天/模块 | 自动生成 | 95-100% |
| **总开发周期** | 4-6周 | 2周 | 65-75% |

### AI开发质量保证
- **代码规范遵循**: AI自动检查，100%遵循规范
- **测试覆盖率**: AI生成测试用例，95%+覆盖率
- **安全漏洞**: AI自动扫描，90%+漏洞自动修复
- **性能优化**: AI智能分析，80%+性能问题预防

### 备用P0/P1/P2传统阶段划分（仅作参考）
#### P0阶段：核心业务功能（3-4周）

### P1阶段：财务和数据（2-3周）
| 模块 | 功能 | 优先级 | 产出物 |
|------|------|--------|--------|
| **对账模块** | 自动对账、差异分析 | P1 | 对账系统、报表 |
| **财务管理** | 预算管理、成本分析 | P1 | 财务分析模块 |
| **数据导入** | 批量导入、数据清洗 | P1 | 数据导入工具 |
| **基础报表** | 消耗报表、转化报表 | P1 | 报表系统 |

### P2阶段：AI和自动化（2-3周）
| 模块 | 功能 | 优先级 | 产出物 |
|------|------|--------|--------|
| **AI检测** | 异常检测、性能分析 | P2 | AI监控模块 |
| **预测模块** | 账户寿命预测、趋势分析 | P2 | 预测系统 |
| **自动化通知** | 邮件通知、消息推送 | P2 | 通知系统 |
| **高级报表** | 多维度分析、自定义报表 | P2 | 高级报表系统 |

### P3阶段：性能和扩展（1-2周）
| 模块 | 功能 | 优先级 | 产出物 |
|------|------|--------|--------|
| **性能优化** | 数据库优化、缓存策略 | P3 | 性能优化方案 |
| **监控告警** | 全面监控、智能告警 | P3 | 监控系统 |
| **容灾备份** | 数据备份、故障恢复 | P3 | 备份恢复方案 |
| **API文档** | 完整API文档、SDK | P3 | API文档中心 |

---

## 十一、验收标准

### 功能验收标准
- ✅ **核心流程完整**：日报提交→审核→数据确认；充值申请→审核→支付→入账
- ✅ **权限控制严格**：所有操作都有权限验证，RLS策略生效
- ✅ **状态机正确**：所有状态转换都符合业务规则，不允许跳级
- ✅ **数据一致性**：所有资金表都包含完整的外键追溯

### 技术验收标准
- ✅ **API响应统一**：所有API都遵循统一的响应格式和错误码规范
- ✅ **日志记录完整**：所有写操作都记录操作日志，支持审计追踪
- ✅ **性能达标**：API响应时间<200ms，数据库查询优化到位
- ✅ **安全配置**：JWT、CORS、限流等安全措施配置完善

### 运维验收标准
- ✅ **监控覆盖**：关键业务指标、系统性能都有监控覆盖
- ✅ **告警及时**：异常情况能及时发现和通知
- ✅ **备份可靠**：数据备份和恢复流程经过验证
- ✅ **部署自动化**：支持一键部署和回滚

### 文档验收标准
- ✅ **API文档完整**：所有接口都有详细的文档和示例
- ✅ **部署文档清晰**：部署步骤清晰，配置文件完整
- ✅ **运维手册详细**：故障处理、性能调优指南完善
- ✅ **代码规范统一**：代码风格统一，注释完整

### AI辅助开发验收标准
- ✅ **AI代码质量**：AI生成的代码符合项目规范，通过代码审查
- ✅ **测试覆盖率**：AI生成的测试用例覆盖95%以上代码路径
- ✅ **性能基准达标**：AI优化的代码满足性能要求，响应时间<200ms
- ✅ **安全扫描通过**：AI自动安全扫描无高危漏洞，通过安全审计
- ✅ **文档同步完整**：AI生成的文档与代码保持同步，准确可靠

---

## 十二、AI辅助开发模式

### 1. AI辅助开发架构

#### 前端AI开发（bolt.new）
```typescript
// AI组件生成示例
/**
 * 用户描述：
 * "创建一个用户管理页面，包含用户列表、搜索、筛选和分页功能"
 */

// AI生成的组件
interface UserManagementProps {
  users: User[];
  loading: boolean;
  onUserUpdate: (user: User) => void;
  onUserDelete: (userId: string) => void;
}

export const UserManagement: React.FC<UserManagementProps> = ({
  users,
  loading,
  onUserUpdate,
  onUserDelete
}) => {
  // AI自动生成的状态管理和逻辑
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);

  // AI自动生成的搜索和筛选逻辑
  const filteredUsers = useMemo(() => {
    return users.filter(user =>
      user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [users, searchTerm]);

  return (
    <div className="user-management">
      {/* AI自动生成的UI组件 */}
      <SearchBar onSearch={setSearchTerm} />
      <FilterBar selectedUsers={selectedUsers} onSelectionChange={setSelectedUsers} />
      <UserTable
        users={filteredUsers}
        loading={loading}
        onUpdate={onUserUpdate}
        onDelete={onUserDelete}
      />
      <Pagination />
    </div>
  );
};
```

#### 后端AI开发（Claude Code）
```python
# AI API生成示例
"""
用户描述：
"创建用户管理API，包含CRUD操作、权限验证和批量操作功能"
"""

# AI生成的FastAPI路由
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:read"))
):
    """
    AI生成的获取用户列表接口
    包含分页、搜索、筛选功能
    """
    # AI自动实现的复杂查询逻辑
    query = db.query(User)

    if search:
        query = query.filter(
            User.name.ilike(f"%{search}%") |
            User.email.ilike(f"%{search}%")
        )

    if role:
        query = query.filter(User.role == role)

    # AI自动添加的权限过滤
    if current_user.role != "admin":
        query = query.filter(User.is_active == True)

    users = query.offset(skip).limit(limit).all()
    return users

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(require_permission("user:create"))
):
    """
    AI生成的创建用户接口
    包含数据验证、权限检查和审计日志
    """
    # AI自动实现的业务逻辑
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )

    # AI自动生成的密码加密
    hashed_password = bcrypt.hashpw(user_data.password.encode(), bcrypt.gensalt())

    user = User(
        **user_data.dict(exclude={"password"}),
        password_hash=hashed_password.decode(),
        id=str(uuid.uuid4()),
        created_by=current_user.id
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # AI自动生成的审计日志
    log_action("user", "create", current_user.id, user.id)

    return user
```

### 2. AI开发工作流

#### 请求-生成-验证循环
```mermaid
graph TD
    A[业务需求描述] --> B[AI理解需求]
    B --> C[AI生成代码]
    C --> D[AI自动测试]
    D --> E{测试通过?}
    E -->|否| F[AI修复代码]
    F --> D
    E -->|是| G[人工审查]
    G --> H{审查通过?}
    H -->|否| I[人工修正]
    I --> G
    H -->|是| J[代码合并]
    J --> K[自动部署]
```

#### AI质量控制流程
```python
# AI代码质量检查器
class AICodeQualityChecker:
    def __init__(self):
        self.rules = [
            CodeStyleRule(),
            SecurityRule(),
            PerformanceRule(),
            TestCoverageRule()
        ]

    def check_code(self, code: str) -> QualityReport:
        """AI自动代码质量检查"""
        report = QualityReport()

        for rule in self.rules:
            result = rule.check(code)
            report.add_result(rule.name, result)

        # AI自动生成改进建议
        if not report.is_passed():
            report.improvement_suggestions = self.generate_suggestions(report)

        return report

    def generate_suggestions(self, report: QualityReport) -> List[str]:
        """AI生成代码改进建议"""
        suggestions = []

        for violation in report.violations:
            if violation.type == "performance":
                suggestions.append(f"性能优化建议: {violation.suggestion}")
            elif violation.type == "security":
                suggestions.append(f"安全加固建议: {violation.suggestion}")
            elif violation.type == "style":
                suggestions.append(f"代码规范建议: {violation.suggestion}")

        return suggestions
```

### 3. AI测试生成

#### 自动化测试用例生成
```python
# AI生成的测试用例
@pytest.fixture
def sample_user_data():
    """AI生成的测试数据"""
    return {
        "name": "测试用户",
        "email": "test@example.com",
        "role": "media_buyer",
        "password": "testpassword123"
    }

class TestUserAPI:
    """AI生成的用户API测试类"""

    def test_create_user_success(self, client, sample_user_data):
        """AI生成的成功测试用例"""
        response = client.post("/api/v1/users/", json=sample_user_data)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == sample_user_data["email"]
        assert "id" in data["data"]
        assert "password_hash" not in data["data"]  # AI自动检查敏感信息

    def test_create_user_duplicate_email(self, client, sample_user_data):
        """AI生成的重复邮箱测试用例"""
        # 先创建用户
        client.post("/api/v1/users/", json=sample_user_data)

        # 再次创建相同邮箱的用户
        response = client.post("/api/v1/users/", json=sample_user_data)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "邮箱已存在" in data["error"]["message"]

    def test_unauthorized_access(self, client):
        """AI生成的权限测试用例"""
        response = client.get("/api/v1/users/")

        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "UNAUTHORIZED"
```

### 4. AI文档生成

#### 自动化API文档生成
```python
# AI生成的API文档装饰器
def auto_document(
    summary: str,
    description: str = None,
    tags: List[str] = None,
    examples: List[dict] = None
):
    """AI自动生成API文档的装饰器"""
    def decorator(func):
        func.__doc__ = f"""
        {summary}

        {description or ""}

        Args:
            各参数说明由AI自动生成

        Returns:
            返回值说明由AI自动生成

        Examples:
            {json.dumps(examples or [], indent=2, ensure_ascii=False)}
        """
        return func
    return decorator

# 使用AI自动生成文档
@router.post("/users/",
    response_model=UserResponse,
    summary="创建新用户",
    description="创建一个新的用户账户，包含完整的权限验证和审计日志",
    examples=[{
        "request": {
            "name": "张三",
            "email": "zhangsan@example.com",
            "role": "media_buyer",
            "password": "password123"
        },
        "response": {
            "id": "uuid-string",
            "name": "张三",
            "email": "zhangsan@example.com",
            "role": "media_buyer",
            "is_active": True,
            "created_at": "2025-11-11T10:30:00Z"
        }
    }]
)
async def create_user(user_data: UserCreate):
    pass
```

---

## 十三、AI辅助开发最佳实践

### 1. 需求描述最佳实践

#### 清晰的需求描述
```markdown
# 好的需求描述示例
**功能**: 充值申请审批流程
**用户角色**: 投手、户管、财务
**业务流程**:
1. 投手提交充值申请（金额、用途、账户）
2. 户管审核申请的合理性和权限
3. 财务审核并执行支付
4. 系统自动更新账户余额

**技术要求**:
- 状态机：draft → pending → approved → paid → posted
- 权限控制：每个角色只能操作对应的状态
- 审计日志：记录所有状态变更
- 实时通知：状态变更时通知相关人员
```

#### 避免的描述方式
```markdown
# 需要避免的模糊描述
❌ "做一个充值功能"
❌ "实现审批流程"
❌ "支持状态管理"

# 应该使用的具体描述
✅ "实现充值申请的三级审批流程，包含投手提交、户管审核、财务支付三个步骤"
✅ "创建充值申请状态机，支持draft、pending、approved、paid、posted五个状态"
✅ "实现基于角色的权限控制，确保每个角色只能操作对应的申请状态"
```

### 2. AI代码审查最佳实践

#### 多层审查机制
```python
# 第一层：AI自检
def ai_self_check(code: str) -> bool:
    """AI自动检查代码质量"""
    checks = [
        check_code_style(code),
        check_security_issues(code),
        check_performance_problems(code),
        check_test_coverage(code)
    ]
    return all(checks)

# 第二层：AI交叉检查
def ai_cross_check(original_code: str, optimized_code: str) -> dict:
    """AI交叉检查代码优化质量"""
    comparison = {
        "improvements": [],
        "regressions": [],
        "security_impact": [],
        "performance_impact": []
    }

    # AI自动分析代码改进
    comparison["improvements"] = analyze_improvements(original_code, optimized_code)
    comparison["regressions"] = detect_regressions(original_code, optimized_code)

    return comparison

# 第三层：人工审查清单
def human_review_checklist(code: dict) -> List[str]:
    """人工审查清单"""
    checklist = [
        "业务逻辑是否正确？",
        "用户界面是否友好？",
        "错误处理是否完善？",
        "性能是否满足要求？",
        "安全配置是否到位？"
    ]

    return checklist
```

### 3. AI测试最佳实践

#### 测试用例生成策略
```python
# AI测试用例生成器
class AITestGenerator:
    def generate_unit_tests(self, function_code: str) -> str:
        """AI生成单元测试"""
        # AI分析函数逻辑
        function_analysis = self.analyze_function(function_code)

        # AI生成正常路径测试
        normal_cases = self.generate_normal_cases(function_analysis)

        # AI生成异常路径测试
        exception_cases = self.generate_exception_cases(function_analysis)

        # AI生成边界条件测试
        boundary_cases = self.generate_boundary_cases(function_analysis)

        return self.combine_test_cases(normal_cases, exception_cases, boundary_cases)

    def generate_integration_tests(self, api_spec: dict) -> str:
        """AI生成集成测试"""
        # AI分析API依赖关系
        dependencies = self.analyze_dependencies(api_spec)

        # AI生成端到端测试场景
        scenarios = self.generate_e2e_scenarios(dependencies)

        # AI生成数据一致性测试
        consistency_tests = self.generate_consistency_tests(api_spec)

        return self.combine_integration_tests(scenarios, consistency_tests)
```

### 4. AI性能优化最佳实践

#### 智能性能分析
```python
class AIPerformanceOptimizer:
    def analyze_query_performance(self, query: str) -> dict:
        """AI分析查询性能"""
        analysis = {
            "complexity": self.calculate_complexity(query),
            "bottlenecks": self.identify_bottlenecks(query),
            "optimization_suggestions": [],
            "estimated_improvement": 0
        }

        # AI生成优化建议
        if analysis["complexity"] > "O(n²)":
            analysis["optimization_suggestions"].append("考虑使用索引优化")
            analysis["estimated_improvement"] += 50

        if "JOIN" in query and "ORDER BY" in query:
            analysis["optimization_suggestions"].append("考虑添加复合索引")
            analysis["estimated_improvement"] += 30

        return analysis

    def generate_optimized_code(self, original_code: str) -> str:
        """AI生成优化代码"""
        # AI识别性能问题
        issues = self.identify_performance_issues(original_code)

        # AI应用优化策略
        optimized_code = original_code
        for issue in issues:
            optimized_code = self.apply_optimization(optimized_code, issue)

        return optimized_code
```

### 5. AI安全最佳实践

#### 安全漏洞自动检测
```python
class AISecurityScanner:
    def scan_for_vulnerabilities(self, code: str) -> List[SecurityIssue]:
        """AI自动扫描安全漏洞"""
        issues = []

        # AI检测SQL注入风险
        sql_injection_risks = self.detect_sql_injection(code)
        issues.extend(sql_injection_risks)

        # AI检测XSS风险
        xss_risks = self.detect_xss(code)
        issues.extend(xss_risks)

        # AI检测权限绕过风险
        auth_risks = self.detect_auth_bypass(code)
        issues.extend(auth_risks)

        # AI检测敏感信息泄露
        data_leak_risks = self.detect_data_leak(code)
        issues.extend(data_leak_risks)

        return issues

    def auto_fix_security_issues(self, code: str, issues: List[SecurityIssue]) -> str:
        """AI自动修复安全问题"""
        fixed_code = code

        for issue in issues:
            if issue.severity == "high":
                fixed_code = self.apply_security_fix(fixed_code, issue)

        return fixed_code
```

### 6. AI开发团队协作最佳实践

#### 协作工作流程
```mermaid
graph LR
    A[产品经理] --> B[需求文档]
    B --> C[AI分析需求]
    C --> D[AI生成代码]
    D --> E[AI自动测试]
    E --> F[开发人员审查]
    F --> G[安全团队审核]
    G --> H[自动化部署]
    H --> I[监控系统]
```

#### 质量保证流程
```python
class AIDevelopmentWorkflow:
    def __init__(self):
        self.quality_gates = [
            CodeQualityGate(),
            SecurityGate(),
            PerformanceGate(),
            TestCoverageGate()
        ]

    def execute_workflow(self, requirements: str) -> WorkflowResult:
        """执行AI辅助开发工作流"""
        result = WorkflowResult()

        # 第一步：AI理解需求
        requirement_analysis = self.ai_analyze_requirements(requirements)
        result.requirement_analysis = requirement_analysis

        # 第二步：AI生成代码
        generated_code = self.ai_generate_code(requirement_analysis)
        result.generated_code = generated_code

        # 第三步：质量检查
        for gate in self.quality_gates:
            gate_result = gate.check(generated_code)
            result.quality_results[gate.name] = gate_result

            if not gate_result.passed:
                # AI自动修复
                fixed_code = self.ai_auto_fix(generated_code, gate_result.issues)
                generated_code = fixed_code

        result.final_code = generated_code
        return result
```

---

## 📚 相关文档

- [SYSTEM_OVERVIEW.md](./SYSTEM_OVERVIEW.md) - 系统架构详细说明
- [BACKEND_API_GUIDE.md](./BACKEND_API_GUIDE.md) - 后端API开发指南
- [DATA_SCHEMA.md](./DATA_SCHEMA.md) - 数据库详细设计
- [FRONTEND_GUIDE.md](./FRONTEND_GUIDE.md) - 前端开发指南
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - 部署运维指南
- [SECURITY_CONFIG.md](./SECURITY_CONFIG.md) - 安全配置规范
- [TESTING_STRATEGY.md](./TESTING_STRATEGY.md) - 测试策略文档
- [MONITORING_OPS.md](./MONITORING_OPS.md) - 监控运维文档
- [STATE_MACHINE.md](./STATE_MACHINE.md) - 状态机设计文档

---

**文档版本**: v2.2 AI辅助协作版
**最后更新**: 2025-11-11
**下次审查**: AI技术栈重大更新时
**维护责任人**: 系统架构团队
**新增特色**: 整合bolt.new前端AI开发和Claude Code后端AI协作的完整技术规范