# AI广告代投系统开发文档 v2.1 执行版

> 本文档在 v2.0 基础上补充了接口示例、状态机表、RLS注入代码、错误码定义与环境变量样例，使其具备直接执行与开发落地能力。

---

## 一、系统结构概览

### 技术栈推荐（固定组合）
- **前端**：Next.js 14 + TypeScript + Tailwind（推荐 shadcn/ui）
- **后端**：FastAPI + Pydantic v2 + SQLAlchemy（同步版）
- **数据库**：PostgreSQL（Supabase 托管）
- **缓存/队列**：Redis + RQ（任务调度、通知、AI检测）
- **日志监控**：Loki + Promtail + Grafana + Sentry
- **部署**：Docker Compose + Nginx 反向代理

---

## 二、核心状态机定义

### 1. 充值申请
| 状态 | 描述 | 可操作角色 | 下一状态 |
|------|------|-------------|------------|
| draft | 投手提交 | 投手 | pending |
| pending | 审核中 | 户管 | approved / rejected |
| approved | 财务批准 | 财务 | paid |
| paid | 已支付 | 系统 | posted |
| posted | 已入账 | 系统 | — |
| rejected | 被驳回 | 户管/财务 | draft |

### 2. 日报审核
| 状态 | 描述 | 可操作角色 | 下一状态 |
|------|------|-------------|------------|
| draft | 投手填写 | 投手 | pending |
| pending | 审核中 | 数据员 | approved / rejected |
| approved | 已通过 | 系统 | — |
| rejected | 异常退回 | 数据员 | draft |

### 3. 账户生命周期
| 状态 | 说明 | 自动触发条件 |
|------|------|----------------|
| new | 新建 | 创建时 |
| testing | 测试期 | 7日内稳定消耗 |
| active | 正常投放 | 日均>100USD |
| suspended | 暂停 | 3天无消耗 |
| dead | 封禁 | FB返回异常 |
| archived | 归档 | 管理员手动 |

---

## 三、数据库与安全策略

### 1. 外键约束与规则
所有资金类表（`topups`, `ad_spend_daily`, `reconciliations`）必须包含：
```
project_id NOT NULL
ad_account_id NOT NULL
user_id NOT NULL
```
并设置：
- 明细表：`ON DELETE CASCADE`
- 主表：`ON DELETE SET NULL`

### 2. RLS 策略与中间件注入
```python
# middleware/rls_context.py
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class RLSContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        user = getattr(request.state, 'user', None)
        if user:
            conn = request.state.db
            await conn.execute(f"SELECT set_config('app.current_user_id', '{user.id}', true)")
            await conn.execute(f"SELECT set_config('app.current_role', '{user.role}', true)")
        response = await call_next(request)
        return response
```
Supabase 端策略示例：
```sql
CREATE POLICY rls_project_access ON projects
  FOR SELECT USING (current_setting('app.current_role') = 'admin'
     OR created_by = current_setting('app.current_user_id'));
```

---

## 四、接口示例

### 1. 新建充值申请
```python
@router.post('/api/topups/request')
def create_topup(req: TopupCreate, user: User = Depends(get_user)):
    with Session(engine) as session, session.begin():
        topup = Topup(**req.dict(), user_id=user.id, status='pending')
        session.add(topup)
        log_action('topup', 'create', user.id, topup.id)
    return {"success": True, "data": topup, "message": "Recharge request submitted."}
```

### 2. 对账接口
```python
@router.post('/api/reconciliation/run')
def run_reconciliation(project_id: UUID):
    with Session(engine) as session:
        spend = session.query(AdSpendDaily).filter_by(project_id=project_id).all()
        topups = session.query(Topup).filter_by(project_id=project_id, status='posted').all()
        diff = sum([s.amount for s in spend]) - sum([t.amount for t in topups])
        rec = Reconciliation(project_id=project_id, diff=diff)
        session.add(rec)
        session.commit()
    return {"success": True, "data": {"project_id": project_id, "difference": diff}}
```

---

## 五、错误码定义

| 错误码 | 含义 | HTTP状态码 | 说明 |
|--------|------|-------------|------|
| 4001 | 参数校验错误 | 400 | Pydantic验证失败 |
| 4010 | 未登录或权限不足 | 401 | Token过期/角色不匹配 |
| 4031 | 禁止操作 | 403 | 当前状态不允许此操作 |
| 4040 | 资源不存在 | 404 | 无匹配记录 |
| 5001 | 系统内部错误 | 500 | 异常捕获统一返回 |

示例：
```python
try:
    ...
except ValidationError as e:
    raise HTTPException(status_code=400, detail={"code":4001,"message":str(e)})
```

---

## 六、环境变量样例

```bash
# .env.example
API_ENV=production
PORT=8080

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=service-role-key
SUPABASE_PUBLIC_KEY=anon-key

# Redis
REDIS_URL=redis://redis:6379

# JWT
JWT_SECRET=supersecretkey
JWT_EXPIRE=3600

# Sentry
SENTRY_DSN=https://xxx.ingest.sentry.io/xxx
```

---

## 七、AI 模块接口定义

### 1. 模块结构
```python
class AIMonitor:
    def detect_anomaly(self, daily_data: list) -> list:
        # 返回异常日报记录
        return [{"date": "2025-11-10", "reason": "spend deviation >150%"}]

    def predict_account_lifetime(self, account_id: str) -> dict:
        return {"days_remaining": 12, "risk_level": "medium"}
```

### 2. 触发时机
| 模块 | 调用时机 | 数据源 |
|------|-----------|--------|
| 异常检测 | 每日报表审核后 | ad_spend_daily |
| 寿命预测 | 每晚定时任务 | ad_accounts |

---

## 八、统一返回结构
```json
{
  "success": true,
  "data": {...},
  "message": "ok",
  "request_id": "a3f98d7"
}
```
错误返回：
```json
{
  "success": false,
  "error": {"code": 4010, "message": "Unauthorized"},
  "request_id": "a3f98d7"
}
```

---

## 九、开发阶段划分
| 阶段 | 内容 | 输出 |
|------|------|------|
| P0 | 项目、渠道、账户、日报、充值 | 可用后台系统 |
| P1 | 财务模块、对账、日志 | 数据准确可核对 |
| P2 | 报表、通知、AI模块 | 自动化监控上线 |

---

## 十、验收标准
- ✅ 核心流程（日报、充值、对账）端到端可跑通
- ✅ 所有写操作均记录日志
- ✅ 所有API具备统一响应与错误码
- ✅ RLS策略在Supabase中验证生效
- ✅ 监控指标在Grafana可视化

---

**版本号**：v2.1 执行版  
**更新日期**：2025-11-11  
**维护人**：系统架构负责人

