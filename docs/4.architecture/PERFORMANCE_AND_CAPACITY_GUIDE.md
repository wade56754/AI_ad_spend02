---
version: v1.0
status: draft
layer: architecture
owner: wade
last_reviewed: 2025-11-27
baseline: MASTER.md v3.4, SoT Freeze v1.0, Dev-Guides Freeze v2.1
---

# Performance and Capacity Guide (性能与容量规划)

## 1. Overview

### 1.1 Purpose of Performance Guide

性能与容量规划 (Performance and Capacity Guide) 定义系统的性能目标、优化策略和容量预估，确保:

- **Performance SLOs**: 明确的服务级别目标 (Service Level Objectives)
- **Capacity Planning**: 基于业务增长的容量规划
- **Optimization Strategies**: 数据库、缓存、查询优化策略
- **Scalability**: 系统水平和垂直扩展方案

### 1.2 Baseline References

**引用**:
- **DATA_SCHEMA.md v5.2**: 数据库表结构与索引
- **SERVICE_COMPONENT_VIEW.md**: 技术栈与部署架构
- **BOUNDED_CONTEXT_MAP.md**: 核心域识别 (性能关键路径)

## 2. Performance Objectives (性能目标)

### 2.1 Service Level Objectives (SLOs)

**API响应时间目标**:

| API类别 | P50 | P95 | P99 | 说明 |
|---------|-----|-----|-----|------|
| **查询类** (GET) | < 200ms | < 500ms | < 1000ms | 日报列表、项目列表 |
| **提交类** (POST) | < 300ms | < 800ms | < 1500ms | 日报提交、充值申请 |
| **计费类** (事务) | < 500ms | < 1500ms | < 3000ms | final_locked触发计费 |
| **导入类** (批量) | - | - | < 30s | CSV导入 (1000行) |

**前端渲染性能目标**:

| 指标 | 目标 | 说明 |
|------|------|------|
| **FCP** (First Contentful Paint) | < 1.5s | 首次内容绘制 |
| **LCP** (Largest Contentful Paint) | < 2.5s | 最大内容绘制 |
| **TTI** (Time to Interactive) | < 3.5s | 可交互时间 |
| **TBT** (Total Blocking Time) | < 200ms | 总阻塞时间 |

### 2.2 Availability & Reliability

**可用性目标**:
- **SLA**: 99.5% (月度停机时间 < 3.6小时)
- **RTO** (Recovery Time Objective): < 1小时
- **RPO** (Recovery Point Objective): < 15分钟

**错误率目标**:
- **总体错误率**: < 1%
- **5xx错误率**: < 0.1%
- **数据库连接失败率**: < 0.01%

## 3. Database Optimization (数据库优化)

### 3.1 Indexing Strategy (索引策略)

**引用**: DATA_SCHEMA.md v5.2

#### 3.1.1 High-Frequency Query Indexes (高频查询索引)

**users表**:
```sql
-- 已存在索引
CREATE INDEX idx_users_username ON users(username);  -- 登录查询
CREATE INDEX idx_users_role ON users(role);          -- 权限过滤
CREATE INDEX idx_users_email ON users(email);        -- 邮箱查询

-- 建议新增索引
CREATE INDEX idx_users_account_manager_active ON users(account_manager_id, is_active)
  WHERE is_active = true;  -- 投手列表查询 (部分索引)
```

**daily_reports表**:
```sql
-- 已存在索引
CREATE INDEX idx_daily_reports_date ON daily_reports(report_date);
CREATE INDEX idx_daily_reports_account ON daily_reports(ad_account_id);
CREATE INDEX idx_daily_reports_status ON daily_reports(status);
CREATE INDEX idx_daily_reports_created_by ON daily_reports(created_by);

-- 建议新增组合索引
CREATE INDEX idx_daily_reports_account_date_status
  ON daily_reports(ad_account_id, report_date, status);  -- 账户日报列表查询

CREATE INDEX idx_daily_reports_date_status_final
  ON daily_reports(report_date, status)
  WHERE status = 'final_locked';  -- 计费查询 (部分索引)
```

**ledger_entries表**:
```sql
-- 已存在索引
CREATE INDEX idx_ledger_project ON ledger_entries(project_id);
CREATE INDEX idx_ledger_supplier ON ledger_entries(supplier_id);
CREATE INDEX idx_ledger_entry_type ON ledger_entries(entry_type);
CREATE INDEX idx_ledger_type ON ledger_entries(ledger_type);

-- 建议新增组合索引
CREATE INDEX idx_ledger_project_occurred
  ON ledger_entries(project_id, occurred_at)
  WHERE ledger_type = 'PROJECT';  -- 项目账本时间序列查询

CREATE INDEX idx_ledger_supplier_occurred
  ON ledger_entries(supplier_id, occurred_at)
  WHERE ledger_type = 'SUPPLIER';  -- 供应商账本时间序列查询
```

**topup_requests表**:
```sql
-- 已存在索引
CREATE INDEX idx_topup_requests_project ON topup_requests(project_id);
CREATE INDEX idx_topup_requests_status ON topup_requests(status);
CREATE INDEX idx_topup_requests_applicant ON topup_requests(applicant_id);

-- 建议新增组合索引
CREATE INDEX idx_topup_requests_project_status_created
  ON topup_requests(project_id, status, created_at DESC);  -- 项目充值列表
```

#### 3.1.2 Index Maintenance (索引维护)

**定期维护任务**:
```sql
-- 1. 重建索引 (每月)
REINDEX TABLE daily_reports;
REINDEX TABLE ledger_entries;

-- 2. 更新统计信息 (每周)
ANALYZE daily_reports;
ANALYZE ledger_entries;
ANALYZE projects;

-- 3. 清理膨胀 (每季度)
VACUUM ANALYZE daily_reports;
VACUUM ANALYZE ledger_entries;
```

### 3.2 Query Optimization (查询优化)

#### 3.2.1 N+1 Query Problem

**❌ 问题示例**:
```python
# 错误做法: N+1查询
reports = db.query(DailyReport).filter(
    DailyReport.ad_account_id == account_id
).all()

for report in reports:
    # 每次循环都查询一次数据库 (N次查询)
    account = db.query(AdAccount).filter(AdAccount.id == report.ad_account_id).first()
    print(f"{report.report_date}: {account.name}")
```

**✅ 解决方案: Eager Loading**:
```python
# 正确做法: 预加载关联数据 (1次查询)
from sqlalchemy.orm import joinedload

reports = db.query(DailyReport).options(
    joinedload(DailyReport.ad_account),
    joinedload(DailyReport.submitted_by_user)
).filter(
    DailyReport.ad_account_id == account_id
).all()

for report in reports:
    # 数据已预加载，无需额外查询
    print(f"{report.report_date}: {report.ad_account.name}")
```

#### 3.2.2 Pagination Optimization

**❌ 错误做法: OFFSET分页**:
```python
# 性能随页码增加线性下降
def get_daily_reports_offset(page: int, page_size: int = 20):
    offset = (page - 1) * page_size
    return db.query(DailyReport).offset(offset).limit(page_size).all()
```

**✅ 正确做法: Cursor-based分页**:
```python
# 性能稳定，不受页码影响
def get_daily_reports_cursor(
    cursor: Optional[int] = None,
    page_size: int = 20
):
    query = db.query(DailyReport).order_by(DailyReport.id.desc())

    if cursor:
        query = query.filter(DailyReport.id < cursor)

    reports = query.limit(page_size).all()

    return {
        "data": reports,
        "next_cursor": reports[-1].id if reports else None,
        "has_more": len(reports) == page_size
    }
```

#### 3.2.3 Aggregation Optimization

**❌ 错误做法: ORM聚合**:
```python
# 慢: 查询所有记录后在Python中聚合
ledger_entries = db.query(LedgerEntry).filter(
    LedgerEntry.project_id == project_id
).all()

balance = sum(entry.amount for entry in ledger_entries)
```

**✅ 正确做法: 数据库聚合**:
```python
# 快: 在数据库层聚合
from sqlalchemy import func

balance = db.query(
    func.sum(LedgerEntry.amount)
).filter(
    LedgerEntry.project_id == project_id
).scalar() or Decimal("0.00")

# 注意: 实时余额应使用 projects.balance 字段 (LEDGER_SOT.md §2.4)
```

### 3.3 Connection Pooling (连接池配置)

**SQLAlchemy连接池**:
```python
# backend/core/database.py
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,      # 连接前检测可用性
    pool_size=20,            # 连接池大小
    max_overflow=40,         # 最大溢出连接数
    pool_recycle=3600,       # 连接回收时间 (1小时)
    pool_timeout=30,         # 获取连接超时 (30秒)
    echo=False,              # 生产环境关闭SQL日志
    echo_pool=False          # 关闭连接池日志
)
```

**连接池监控**:
```python
# 监控连接池状态
def get_pool_status():
    return {
        "size": engine.pool.size(),
        "checked_in": engine.pool.checkedin(),
        "overflow": engine.pool.overflow(),
        "checked_out": engine.pool.checkedout()
    }
```

## 4. Caching Strategy (缓存策略)

### 4.1 Frontend Caching (TanStack Query)

**引用**: SERVICE_COMPONENT_VIEW.md §2.2.1

#### 4.1.1 Query Caching Configuration

```typescript
// frontend/lib/query-client.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,     // 5分钟内数据视为新鲜
      gcTime: 10 * 60 * 1000,       // 10分钟后清理缓存
      retry: 3,                     // 失败重试3次
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: true,   // 窗口聚焦时重新拉取
      refetchOnReconnect: true,     // 重新连接时重新拉取
    },
    mutations: {
      retry: 1,  // 提交操作仅重试1次
    },
  },
});
```

#### 4.1.2 Query Key Strategy

**查询键设计原则**:
```typescript
// ✅ 推荐: 分层查询键
const dailyReportKeys = {
  all: ['daily-reports'] as const,
  lists: () => [...dailyReportKeys.all, 'list'] as const,
  list: (filters: string) => [...dailyReportKeys.lists(), { filters }] as const,
  details: () => [...dailyReportKeys.all, 'detail'] as const,
  detail: (id: number) => [...dailyReportKeys.details(), id] as const,
};

// 使用示例
function useDailyReport(id: number) {
  return useQuery({
    queryKey: dailyReportKeys.detail(id),
    queryFn: () => fetchDailyReport(id),
  });
}

function useDailyReports(accountId: number, filters: ReportFilters) {
  return useQuery({
    queryKey: dailyReportKeys.list(JSON.stringify({ accountId, ...filters })),
    queryFn: () => fetchDailyReports(accountId, filters),
  });
}
```

#### 4.1.3 Cache Invalidation

```typescript
// 提交日报后失效相关查询
function useSubmitReport() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: submitDailyReport,
    onSuccess: (data) => {
      // 1. 失效日报列表缓存
      queryClient.invalidateQueries({
        queryKey: dailyReportKeys.lists(),
      });

      // 2. 失效账户余额缓存
      queryClient.invalidateQueries({
        queryKey: ['projects', data.project_id, 'balance'],
      });

      // 3. 乐观更新 (可选)
      queryClient.setQueryData(
        dailyReportKeys.detail(data.id),
        data
      );
    },
  });
}
```

### 4.2 Backend Caching (Redis - 规划中)

#### 4.2.1 Cache Hierarchy

**缓存层级**:
```
L1: TanStack Query (前端内存缓存, 5-10分钟)
  ↓
L2: Redis (后端缓存, 1小时)
  ↓
L3: PostgreSQL (数据库)
```

#### 4.2.2 Redis Cache Keys

**命名规范**:
```
{namespace}:{entity}:{id}:{field}

示例:
- project:123:balance
- daily_report:456:detail
- user:uuid-xxx:role
```

**缓存策略**:
```python
# backend/core/cache.py
import redis
import json
from typing import Optional, Any
from functools import wraps

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    db=0,
    decode_responses=True
)

def cache_result(key_prefix: str, ttl: int = 3600):
    """
    结果缓存装饰器

    Args:
        key_prefix: 缓存键前缀
        ttl: 过期时间 (秒)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = f"{key_prefix}:{args}:{kwargs}"

            # 尝试从缓存读取
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # 缓存未命中，执行查询
            result = await func(*args, **kwargs)

            # 写入缓存
            redis_client.setex(cache_key, ttl, json.dumps(result))
            return result

        return wrapper
    return decorator

# 使用示例
@cache_result(key_prefix="project:balance", ttl=300)
async def get_project_balance(project_id: int) -> Decimal:
    """查询项目余额 (缓存5分钟)"""
    project = db.query(Project).filter(Project.id == project_id).first()
    return project.balance if project else Decimal("0.00")
```

#### 4.2.3 Cache Invalidation Strategy

**Write-Through Cache** (写穿缓存):
```python
def update_project_balance(project_id: int, amount: Decimal):
    """更新项目余额 + 缓存失效"""
    with db.begin():
        # 1. 更新数据库
        project = db.query(Project).filter(
            Project.id == project_id
        ).with_for_update().first()
        project.balance += amount
        db.commit()

    # 2. 删除缓存
    redis_client.delete(f"project:balance:{project_id}")
```

**Cache Aside** (旁路缓存):
```python
def get_project_with_cache(project_id: int):
    """读取项目 (旁路缓存)"""
    # 1. 尝试从缓存读取
    cache_key = f"project:detail:{project_id}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)

    # 2. 缓存未命中，查询数据库
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None

    # 3. 写入缓存
    redis_client.setex(cache_key, 3600, json.dumps(project.to_dict()))
    return project
```

## 5. Performance Monitoring (性能监控)

### 5.1 Backend Metrics

**关键指标**:
```python
# backend/core/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# API请求计数
api_requests_total = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

# API响应时间
api_response_time = Histogram(
    'api_response_time_seconds',
    'API response time',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# 数据库连接池
db_pool_connections = Gauge(
    'db_pool_connections',
    'Database connection pool status',
    ['status']  # checked_in, checked_out, overflow
)

# 缓存命中率
cache_hit_rate = Counter(
    'cache_hit_total',
    'Cache hit count',
    ['cache_type', 'result']  # redis/memory, hit/miss
)
```

**中间件集成**:
```python
# backend/middleware/metrics.py
from fastapi import Request
import time

async def metrics_middleware(request: Request, call_next):
    start_time = time.time()

    response = await call_next(request)

    duration = time.time() - start_time

    # 记录指标
    api_requests_total.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()

    api_response_time.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)

    return response
```

### 5.2 Frontend Metrics

**Web Vitals监控**:
```typescript
// frontend/lib/web-vitals.ts
import { onCLS, onFID, onFCP, onLCP, onTTFB } from 'web-vitals';

function sendToAnalytics(metric: Metric) {
  // 发送到分析平台 (如 Google Analytics, Sentry)
  console.log(metric);
}

onCLS(sendToAnalytics);  // Cumulative Layout Shift
onFID(sendToAnalytics);  // First Input Delay
onFCP(sendToAnalytics);  // First Contentful Paint
onLCP(sendToAnalytics);  // Largest Contentful Paint
onTTFB(sendToAnalytics); // Time to First Byte
```

### 5.3 Database Monitoring

**慢查询日志**:
```sql
-- 启用慢查询日志 (PostgreSQL)
ALTER SYSTEM SET log_min_duration_statement = 1000;  -- 记录超过1秒的查询
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';
SELECT pg_reload_conf();
```

**查询性能分析**:
```sql
-- 查看慢查询TOP 10
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- 查看表大小
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 6. Capacity Planning (容量规划)

### 6.1 Data Growth Estimation (数据增长预估)

**业务假设**:
- 投手数量: 50人 (初期) → 200人 (1年后)
- 日报提交频率: 每人每天提交10条 (平均)
- 充值申请频率: 每个项目每月5次
- 项目数量: 20个 (初期) → 100个 (1年后)

**表数据量预估** (1年后):

| 表名 | 行数预估 | 单行大小 | 总大小 | 增长率 |
|------|---------|---------|--------|--------|
| daily_reports | 200人 × 10条/天 × 365天 = 730,000 | 1 KB | ~730 MB | 线性增长 |
| ledger_entries | 730,000 × 2 (REVENUE+COST) = 1,460,000 | 500 B | ~730 MB | 线性增长 |
| topup_requests | 100项目 × 5次/月 × 12月 = 6,000 | 1 KB | ~6 MB | 线性增长 |
| audit_logs | 1,000,000 | 2 KB | ~2 GB | 线性增长 |
| users | 200 | 2 KB | ~400 KB | 稳定 |
| projects | 100 | 1 KB | ~100 KB | 稳定 |
| ad_accounts | 500 | 1 KB | ~500 KB | 稳定 |

**总存储需求**:
- **1年后**: ~4 GB (数据) + ~2 GB (索引) = **6 GB**
- **3年后**: ~18 GB (数据) + ~9 GB (索引) = **27 GB**

### 6.2 Compute Resource Estimation (计算资源预估)

**API Server (FastAPI)**:

| 负载 | QPS | CPU | 内存 | 实例数 |
|------|-----|-----|------|--------|
| 低 (初期) | < 10 | 1 Core | 1 GB | 1 |
| 中 (6个月) | < 50 | 2 Cores | 2 GB | 2 |
| 高 (1年) | < 200 | 4 Cores | 4 GB | 3 |

**PostgreSQL**:

| 负载 | 连接数 | CPU | 内存 | 磁盘 |
|------|--------|-----|------|------|
| 低 (初期) | < 20 | 2 Cores | 4 GB | 50 GB SSD |
| 中 (6个月) | < 50 | 4 Cores | 8 GB | 100 GB SSD |
| 高 (1年) | < 100 | 8 Cores | 16 GB | 200 GB SSD |

**Redis (缓存)**:

| 负载 | 缓存大小 | 内存 |
|------|---------|------|
| 低 (初期) | < 100 MB | 512 MB |
| 中 (6个月) | < 500 MB | 1 GB |
| 高 (1年) | < 2 GB | 4 GB |

### 6.3 Scalability Strategy (扩展策略)

#### 6.3.1 Horizontal Scaling (水平扩展)

**API Server水平扩展**:
```
单实例 → Nginx负载均衡 → 多实例 (3-5个)

优势:
- 无状态设计，易于扩展
- 零停机部署

实施:
1. Docker化API Server
2. 配置Nginx负载均衡
3. 使用Docker Swarm或Kubernetes编排
```

**Database Read Replicas**:
```
PostgreSQL Primary (写) → PostgreSQL Replica 1 (读)
                       → PostgreSQL Replica 2 (读)

读写分离:
- 写操作 (INSERT/UPDATE/DELETE) → Primary
- 读操作 (SELECT) → Replicas (轮询或最少连接)
```

#### 6.3.2 Vertical Scaling (垂直扩展)

**PostgreSQL垂直扩展阈值**:
- CPU使用率 > 70% (持续1小时) → 升级CPU
- 内存使用率 > 80% (持续1小时) → 升级内存
- 磁盘使用率 > 70% → 扩容磁盘

**Supabase升级路径**:
```
Starter ($25/月, 500MB, 2GB带宽)
  ↓
Pro ($25/月, 8GB, 50GB带宽)
  ↓
Team ($599/月, 100GB, 250GB带宽)
  ↓
Enterprise (定制化)
```

## 7. Optimization Checklist (优化检查清单)

### 7.1 Backend Optimization

- [ ] 已添加高频查询索引 (daily_reports, ledger_entries)
- [ ] 已避免N+1查询 (使用joinedload)
- [ ] 已使用Cursor-based分页 (大数据集)
- [ ] 已配置连接池 (pool_size=20, max_overflow=40)
- [ ] 已启用慢查询日志 (log_min_duration_statement=1000)
- [ ] 已实现缓存策略 (TanStack Query + Redis)
- [ ] 已添加API性能监控 (Prometheus Metrics)
- [ ] 已优化Pydantic模型 (避免过度嵌套)

### 7.2 Frontend Optimization

- [ ] 已配置TanStack Query缓存策略 (staleTime=5分钟)
- [ ] 已实现查询键分层 (all/lists/details)
- [ ] 已添加Loading骨架屏 (避免CLS)
- [ ] 已启用代码分割 (Next.js动态导入)
- [ ] 已优化图片加载 (next/image, lazy loading)
- [ ] 已启用Web Vitals监控
- [ ] 已添加Error Boundary (优雅降级)

### 7.3 Database Optimization

- [ ] 已定期REINDEX (每月)
- [ ] 已定期ANALYZE (每周)
- [ ] 已定期VACUUM (每季度)
- [ ] 已启用部分索引 (WHERE子句过滤)
- [ ] 已避免SELECT * (仅查询必要字段)
- [ ] 已使用EXPLAIN ANALYZE分析慢查询
- [ ] 已设置合理的work_mem (提升排序性能)

## 8. Performance Testing (性能测试)

### 8.1 Load Testing (负载测试)

**工具**: Locust

**测试场景**:
```python
# tests/performance/locustfile.py
from locust import HttpUser, task, between

class DailyReportUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # 登录获取Token
        response = self.client.post("/api/v1/auth/login", json={
            "username": "test_buyer",
            "password": "password"
        })
        self.token = response.json()["data"]["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    @task(3)  # 权重3
    def list_daily_reports(self):
        """查询日报列表"""
        self.client.get(
            "/api/v1/daily-reports?account_id=123",
            headers=self.headers
        )

    @task(1)  # 权重1
    def submit_daily_report(self):
        """提交日报"""
        self.client.post(
            "/api/v1/daily-reports",
            headers=self.headers,
            json={
                "report_date": "2025-01-20",
                "ad_account_id": 456,
                "conversions_raw": 100,
                "raw_spend": 4800.00
            }
        )
```

**执行测试**:
```bash
# 模拟100个并发用户，持续5分钟
locust -f tests/performance/locustfile.py --users 100 --spawn-rate 10 --run-time 5m
```

### 8.2 Stress Testing (压力测试)

**目标**: 找到系统崩溃点

**测试步骤**:
1. 从10个并发用户开始
2. 每分钟增加10个用户
3. 持续增加直到错误率 > 5%或响应时间 > 5秒
4. 记录系统崩溃点 (最大QPS、最大并发数)

**预期崩溃点**:
- 单实例API Server: ~200 QPS
- PostgreSQL: ~500 QPS (读操作)
- PostgreSQL: ~100 QPS (写操作)

## 9. Traceability (可追溯性)

### 9.1 References to DATA_SCHEMA.md v5.2

- **§3.3.1 daily_reports表**: 索引设计
- **§3.4.4 ledger_entries表**: 索引设计
- **§4 索引与约束策略**: 索引命名规范

### 9.2 References to SERVICE_COMPONENT_VIEW.md

- **§2.2.2 API Server**: 技术栈与部署架构
- **§2.2.3 Database**: PostgreSQL配置
- **§2.2.5 Cache**: Redis缓存策略

### 9.3 References to BOUNDED_CONTEXT_MAP.md

- **§2.1 核心域**: Financial Ledger + Daily Report (性能关键路径)
- **§6 演进策略**: 微服务拆分规划

---

**文档状态**: ✅ Draft完成，等待审计
**维护责任**: Architecture Team + Backend Team + DevOps Team
**下次审查**: 每季度或性能目标重大调整时
