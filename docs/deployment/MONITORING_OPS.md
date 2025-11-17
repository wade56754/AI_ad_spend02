# 监控运维文档

> **文档目的**: 为AI广告代投系统提供全面的监控、运维和故障处理指南
> **目标读者**: DevOps工程师、运维团队、系统管理员
> **更新日期**: 2025-11-11
> **版本**: v1.0

---

## 📋 目录

1. [监控架构概览](#1-监控架构概览)
2. [应用监控](#2-应用监控)
3. [基础设施监控](#3-基础设施监控)
4. [业务指标监控](#4-业务指标监控)
5. [日志管理](#5-日志管理)
6. [告警系统](#6-告警系统)
7. [故障处理](#7-故障处理)
8. [性能优化](#8-性能优化)
9. [容量规划](#9-容量规划)
10. [运维自动化](#10-运维自动化)

---

## 1. 监控架构概览

> 状态说明：本文所涉 Prometheus/Grafana/Loki/Alertmanager 能力，部分为“规划能力”。当前版本按需启用基础监控与告警，完整方案落地以 `docs/core/AI_AD_SYSTEM_MAIN_DOCUMENT.md` 为准。

### 1.1 监控体系架构

```
┌─────────────────────────────────────────────────────────────┐
│                      数据收集层                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ 应用指标     │ │ 基础设施指标 │ │ 业务指标     │           │
│  │ Prometheus  │ │ Node Exporter│ │ 自定义指标   │           │
│  │ OpenTelemetry│ │ cAdvisor     │ │ 自定义Exporter│         │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      数据存储层                               │
│  ┌─────────────┐              ┌─────────────┐               │
│  │ Prometheus  │              │   Loki       │               │
│  │  时序数据库   │              │  日志存储    │               │
│  └─────────────┘              └─────────────┘               │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      可视化层                                 │
│  ┌─────────────┐              ┌─────────────┐               │
│  │  Grafana    │              │ AlertManager│               │
│  │  数据可视化  │              │  告警管理    │               │
│  └─────────────┘              └─────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 监控指标分类

| 指标类型 | 监控内容 | 工具 | 告警级别 |
|----------|----------|------|----------|
| **应用监控** | 响应时间、错误率、吞吐量 | Prometheus + Grafana | P0 |
| **基础设施监控** | CPU、内存、磁盘、网络 | Node Exporter | P1 |
| **数据库监控** | 连接数、查询性能、锁等待 | pg_exporter | P0 |
| **业务监控** | 用户活跃度、转化率、收入 | 自定义指标 | P0 |
| **安全监控** | 登录失败、异常访问、攻击 | 自定义指标 | P0 |
| **日志监控** | 错误日志、异常堆栈 | Loki + Grafana | P1 |

---

## 2. 应用监控

### 2.1 应用指标配置

```python
# backend/app/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Request, Response
import time
import logging

# 应用指标
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

ACTIVE_USERS = Gauge(
    'active_users_total',
    'Number of active users'
)

DATABASE_CONNECTIONS = Gauge(
    'database_connections_active',
    'Active database connections'
)

BUSINESS_METRICS = {
    'projects_created_total': Counter(
        'projects_created_total',
        'Total number of projects created',
        ['user_role', 'client_type']
    ),
    'daily_reports_submitted': Counter(
        'daily_reports_submitted_total',
        'Total number of daily reports submitted'
    ),
    'recharge_requests_total': Counter(
        'recharge_requests_total',
        'Total number of recharge requests',
        ['status', 'amount_range']
    )
}

# 监控中间件
async def monitoring_middleware(request: Request, call_next):
    start_time = time.time()

    # 处理请求
    response = await call_next(request)

    # 记录请求指标
    method = request.method
    endpoint = request.url.path
    status_code = str(response.status_code)
    duration = time.time() - start_time

    REQUEST_COUNT.labels(method, endpoint, status_code).inc()
    REQUEST_DURATION.labels(method, endpoint).observe(duration)

    return response

# 业务指标更新
class BusinessMetrics:
    @staticmethod
    def record_project_created(user_role: str, client_type: str):
        """记录项目创建"""
        BUSINESS_METRICS['projects_created_total'].labels(
            user_role=user_role,
            client_type=client_type
        ).inc()

    @staticmethod
    def record_daily_report_submitted():
        """记录日报提交"""
        BUSINESS_METRICS['daily_reports_submitted'].inc()

    @staticmethod
    def record_recharge_request(status: str, amount: float):
        """记录充值请求"""
        # 确定金额范围
        if amount < 1000:
            amount_range = 'small'
        elif amount < 10000:
            amount_range = 'medium'
        else:
            amount_range = 'large'

        BUSINESS_METRICS['recharge_requests_total'].labels(
            status=status,
            amount_range=amount_range
        ).inc()

# 健康检查和指标端点
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI()

@app.get("/metrics")
async def metrics():
    """Prometheus指标端点"""
    return PlainTextResponse(generate_latest())

@app.get("/health")
async def health_check():
    """健康检查端点"""
    # 检查数据库连接
    db_status = await check_database_health()

    # 检查Redis连接
    redis_status = await check_redis_health()

    # 检查外部API连接
    external_api_status = await check_external_api_health()

    overall_status = "healthy" if all([
        db_status, redis_status, external_api_status
    ]) else "unhealthy"

    return {
        "status": overall_status,
        "services": {
            "database": "healthy" if db_status else "unhealthy",
            "redis": "healthy" if redis_status else "unhealthy",
            "external_api": "healthy" if external_api_status else "unhealthy"
        },
        "timestamp": time.time()
    }

async def check_database_health():
    """检查数据库健康状态"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception as e:
        logging.error(f"Database health check failed: {e}")
        return False

async def check_redis_health():
    """检查Redis健康状态"""
    try:
        await redis_client.ping()
        return True
    except Exception as e:
        logging.error(f"Redis health check failed: {e}")
        return False

async def check_external_api_health():
    """检查外部API健康状态"""
    try:
        response = requests.get("https://graph.facebook.com/v18.0/", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logging.error(f"External API health check failed: {e}")
        return False
```

### 2.2 自定义业务指标

```python
# backend/app/monitoring/business_metrics.py
from prometheus_client import Counter, Histogram, Gauge, info
from datetime import datetime, timedelta
import asyncio

# 业务指标
USER_METRICS = {
    'login_attempts': Counter('user_login_attempts_total', 'Total login attempts', ['status']),
    'user_registrations': Counter('user_registrations_total', 'Total user registrations', ['role']),
    'active_sessions': Gauge('user_active_sessions', 'Number of active user sessions'),
}

FINANCIAL_METRICS = {
    'total_spend': Counter('ad_spend_total', 'Total ad spend', ['project_id', 'date']),
    'recharge_amount': Counter('recharge_amount_total', 'Total recharge amount', ['status']),
    'conversion_value': Counter('conversion_value_total', 'Total conversion value', ['project_id']),
}

PERFORMANCE_METRICS = {
    'report_processing_time': Histogram(
        'report_processing_duration_seconds',
        'Time to process daily reports',
        buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0]
    ),
    'data_sync_duration': Histogram(
        'data_sync_duration_seconds',
        'Time to sync data with external APIs',
        buckets=[5.0, 15.0, 30.0, 60.0, 300.0, 600.0]
    )
}

class BusinessMonitor:
    def __init__(self, db_session, redis_client):
        self.db = db_session
        self.redis = redis_client

    async def collect_daily_metrics(self):
        """收集每日业务指标"""
        today = datetime.now().date()

        # 收集用户活跃度
        await self._collect_user_activity(today)

        # 收集财务指标
        await self._collect_financial_metrics(today)

        # 收集项目状态
        await self._collect_project_metrics(today)

    async def _collect_user_activity(self, date):
        """收集用户活跃度指标"""
        try:
            # 今日登录用户数
            login_count = await self.redis.get(f"daily_logins:{date}") or 0

            # 活跃用户数
            active_users = self.db.query(User).filter(
                User.last_login >= date
            ).count()

            # 更新指标
            USER_METRICS['active_sessions'].set(active_users)

            logging.info(f"User activity metrics collected for {date}: "
                        f"logins={login_count}, active_users={active_users}")

        except Exception as e:
            logging.error(f"Failed to collect user activity metrics: {e}")

    async def _collect_financial_metrics(self, date):
        """收集财务指标"""
        try:
            # 今日消耗
            today_spend = self.db.query(func.sum(DailyReport.spend)).filter(
                DailyReport.report_date == date
            ).scalar() or 0

            # 今日充值
            today_recharge = self.db.query(func.sum(RechargeRequest.amount)).filter(
                RechargeRequest.created_at >= date,
                RechargeRequest.status == 'approved'
            ).scalar() or 0

            # 更新指标
            FINANCIAL_METRICS['total_spend'].labels(project_id='all', date=str(date)).inc(today_spend)
            FINANCIAL_METRICS['recharge_amount'].labels(status='approved').inc(today_recharge)

            logging.info(f"Financial metrics collected for {date}: "
                        f"spend={today_spend}, recharge={today_recharge}")

        except Exception as e:
            logging.error(f"Failed to collect financial metrics: {e}")

    async def _collect_project_metrics(self, date):
        """收集项目指标"""
        try:
            # 项目总数
            total_projects = self.db.query(Project).count()

            # 活跃项目数
            active_projects = self.db.query(Project).filter(
                Project.status == 'active'
            ).count()

            # 今日新增项目
            new_projects_today = self.db.query(Project).filter(
                Project.created_at >= date
            ).count()

            logging.info(f"Project metrics collected for {date}: "
                        f"total={total_projects}, active={active_projects}, "
                        f"new_today={new_projects_today}")

        except Exception as e:
            logging.error(f"Failed to collect project metrics: {e}")

# 定时任务：每小时收集一次指标
async def schedule_metrics_collection():
    """调度指标收集"""
    monitor = BusinessMonitor(db_session, redis_client)

    while True:
        try:
            await monitor.collect_daily_metrics()
            await asyncio.sleep(3600)  # 每小时执行一次
        except Exception as e:
            logging.error(f"Error in metrics collection: {e}")
            await asyncio.sleep(300)  # 出错时5分钟后重试
```

---

## 3. 基础设施监控

### 3.1 服务器监控配置

```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

scrape_configs:
  # 应用服务监控
  - job_name: 'ai-ad-spend-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
    scrape_timeout: 10s

  - job_name: 'ai-ad-spend-frontend'
    static_configs:
      - targets: ['frontend:3000']
    metrics_path: '/api/metrics'
    scrape_interval: 30s

  # Node Exporter - 系统指标
  - job_name: 'node-exporter'
    static_configs:
      - targets:
        - 'node-exporter:9100'
    scrape_interval: 10s

  # cAdvisor - 容器指标
  - job_name: 'cadvisor'
    static_configs:
      - targets:
        - 'cadvisor:8080'
    scrape_interval: 15s

  # PostgreSQL Exporter
  - job_name: 'postgres-exporter'
    static_configs:
      - targets:
        - 'postgres-exporter:9187'
    scrape_interval: 15s

  # Redis Exporter
  - job_name: 'redis-exporter'
    static_configs:
      - targets:
        - 'redis-exporter:9121'
    scrape_interval: 15s

  # Nginx Exporter
  - job_name: 'nginx-exporter'
    static_configs:
      - targets:
        - 'nginx-exporter:9113'
    scrape_interval: 15s
```

### 3.2 Docker Compose监控配置

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/alert_rules.yml:/etc/prometheus/alert_rules.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=30d'
      - '--web.enable-lifecycle'
    networks:
      - monitoring

  # Grafana
  grafana:
    image: grafana/grafana:latest
    restart: unless-stopped
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
    networks:
      - monitoring

  # AlertManager
  alertmanager:
    image: prom/alertmanager:latest
    restart: unless-stopped
    ports:
      - "9093:9093"
    volumes:
      - ./monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager
    networks:
      - monitoring

  # Node Exporter
  node-exporter:
    image: prom/node-exporter:latest
    restart: unless-stopped
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    networks:
      - monitoring

  # cAdvisor
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:rw
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    privileged: true
    devices:
      - /dev/kmsg
    networks:
      - monitoring

  # PostgreSQL Exporter
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter:latest
    restart: unless-stopped
    ports:
      - "9187:9187"
    environment:
      - DATA_SOURCE_NAME=postgresql://postgres:password@postgres:5432/ai_ad_spend_prod?sslmode=disable
    networks:
      - monitoring

  # Redis Exporter
  redis-exporter:
    image: oliver006/redis_exporter:latest
    restart: unless-stopped
    ports:
      - "9121:9121"
    environment:
      - REDIS_ADDR=redis://redis:6379
      - REDIS_PASSWORD=password
    networks:
      - monitoring

  # Loki (日志聚合)
  loki:
    image: grafana/loki:latest
    restart: unless-stopped
    ports:
      - "3100:3100"
    volumes:
      - ./monitoring/loki.yml:/etc/loki/local-config.yaml
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - monitoring

  # Promtail (日志收集)
  promtail:
    image: grafana/promtail:latest
    restart: unless-stopped
    volumes:
      - ./monitoring/promtail.yml:/etc/promtail/config.yml
      - /var/log:/var/log:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    command: -config.file=/etc/promtail/config.yml
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:
  alertmanager_data:
  loki_data:

networks:
  monitoring:
    driver: bridge
```

---

## 4. 业务指标监控

### 4.1 Grafana仪表盘配置

```json
{
  "dashboard": {
    "id": null,
    "title": "AI广告代投系统 - 业务监控",
    "tags": ["ai-ad-spend", "business"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "项目概览",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(ai_ad_spend_projects_total)",
            "legendFormat": "总项目数"
          },
          {
            "expr": "sum(ai_ad_spend_active_projects_total)",
            "legendFormat": "活跃项目数"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {"mode": "palette-classic"},
            "custom": {"displayMode": "list", "orientation": "horizontal"},
            "mappings": [],
            "thresholds": {
              "steps": [
                {"color": "green", "value": null},
                {"color": "red", "value": 80}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "用户活跃度",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(user_login_attempts_total{status=\"success\"}[5m])",
            "legendFormat": "成功登录"
          },
          {
            "expr": "rate(user_login_attempts_total{status=\"failed\"}[5m])",
            "legendFormat": "失败登录"
          },
          {
            "expr": "user_active_sessions",
            "legendFormat": "活跃会话"
          }
        ]
      },
      {
        "id": 3,
        "title": "财务指标",
        "type": "graph",
        "targets": [
          {
            "expr": "increase(ad_spend_total[1h])",
            "legendFormat": "每小时消耗"
          },
          {
            "expr": "increase(recharge_amount_total{status=\"approved\"}[1h])",
            "legendFormat": "每小时充值"
          },
          {
            "expr": "increase(conversion_value_total[1h])",
            "legendFormat": "每小时转化价值"
          }
        ]
      },
      {
        "id": 4,
        "title": "API性能",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th百分位响应时间"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th百分位响应时间"
          }
        ]
      },
      {
        "id": 5,
        "title": "错误率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status_code=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
            "legendFormat": "5xx错误率"
          },
          {
            "expr": "rate(http_requests_total{status_code=~\"4..\"}[5m]) / rate(http_requests_total[5m])",
            "legendFormat": "4xx错误率"
          }
        ]
      }
    ],
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "refresh": "5s"
  }
}
```

### 4.2 自定义业务指标收集器

```python
# backend/app/monitoring/business_collector.py
from prometheus_client import Gauge, Counter, CollectorRegistry, generate_latest
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import func

class BusinessMetricsCollector:
    def __init__(self, db_session):
        self.db = db_session
        self.registry = CollectorRegistry()
        self._setup_metrics()

    def _setup_metrics(self):
        """设置业务指标"""
        # 项目相关指标
        self.project_metrics = {
            'total_projects': Gauge(
                'business_total_projects',
                'Total number of projects',
                registry=self.registry
            ),
            'active_projects': Gauge(
                'business_active_projects',
                'Number of active projects',
                registry=self.registry
            ),
            'projects_by_status': Gauge(
                'business_projects_by_status',
                'Projects by status',
                ['status'],
                registry=self.registry
            )
        }

        # 财务相关指标
        self.financial_metrics = {
            'daily_spend': Gauge(
                'business_daily_spend',
                'Total ad spend for the day',
                ['date'],
                registry=self.registry
            ),
            'monthly_budget_utilization': Gauge(
                'business_monthly_budget_utilization',
                'Monthly budget utilization percentage',
                ['project_id'],
                registry=self.registry
            ),
            'recharge_pending_amount': Gauge(
                'business_recharge_pending_amount',
                'Total pending recharge amount',
                registry=self.registry
            )
        }

        # 用户相关指标
        self.user_metrics = {
            'total_users': Gauge(
                'business_total_users',
                'Total number of users',
                ['role'],
                registry=self.registry
            ),
            'daily_active_users': Gauge(
                'business_daily_active_users',
                'Daily active users',
                registry=self.registry
            )
        }

    async def collect_all_metrics(self):
        """收集所有业务指标"""
        try:
            await self._collect_project_metrics()
            await self._collect_financial_metrics()
            await self._collect_user_metrics()

            logging.info("Business metrics collected successfully")

        except Exception as e:
            logging.error(f"Failed to collect business metrics: {e}")

    async def _collect_project_metrics(self):
        """收集项目指标"""
        # 总项目数
        total_projects = self.db.query(Project).count()
        self.project_metrics['total_projects'].set(total_projects)

        # 活跃项目数
        active_projects = self.db.query(Project).filter(
            Project.status == 'active'
        ).count()
        self.project_metrics['active_projects'].set(active_projects)

        # 按状态分类的项目数
        status_counts = self.db.query(
            Project.status,
            func.count(Project.id)
        ).group_by(Project.status).all()

        for status, count in status_counts:
            self.project_metrics['projects_by_status'].labels(status=status).set(count)

    async def _collect_financial_metrics(self):
        """收集财务指标"""
        today = datetime.now().date()

        # 今日消耗
        today_spend = self.db.query(func.sum(DailyReport.spend)).filter(
            DailyReport.report_date == today
        ).scalar() or 0

        self.financial_metrics['daily_spend'].labels(date=str(today)).set(today_spend)

        # 月度预算利用率
        current_month_start = today.replace(day=1)
        project_budgets = self.db.query(
            Project.id,
            Project.budget,
            func.sum(DailyReport.spend).label('current_spend')
        ).outerjoin(
            DailyReport,
            Project.id == DailyReport.project_id
        ).filter(
            DailyReport.report_date >= current_month_start
        ).group_by(Project.id, Project.budget).all()

        for project_id, budget, current_spend in project_budgets:
            utilization = (current_spend or 0) / budget if budget > 0 else 0
            self.financial_metrics['monthly_budget_utilization'].labels(
                project_id=str(project_id)
            ).set(utilization)

        # 待处理充值金额
        pending_amount = self.db.query(func.sum(RechargeRequest.amount)).filter(
            RechargeRequest.status == 'pending'
        ).scalar() or 0

        self.financial_metrics['recharge_pending_amount'].set(pending_amount)

    async def _collect_user_metrics(self):
        """收集用户指标"""
        # 按角色统计用户数
        role_counts = self.db.query(
            User.role,
            func.count(User.id)
        ).group_by(User.role).all()

        for role, count in role_counts:
            self.user_metrics['total_users'].labels(role=role).set(count)

        # 今日活跃用户
        today = datetime.now().date()
        active_users = self.db.query(User).filter(
            User.last_login >= today
        ).count()

        self.user_metrics['daily_active_users'].set(active_users)

    def get_metrics_output(self):
        """获取指标输出"""
        return generate_latest(self.registry)

# FastAPI路由集成
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter()

@router.get("/business-metrics")
async def business_metrics():
    """业务指标端点"""
    collector = BusinessMetricsCollector(db_session)
    await collector.collect_all_metrics()
    return PlainTextResponse(collector.get_metrics_output())
```

---

## 5. 日志管理

### 5.1 日志配置

```python
# backend/app/logging_config.py
import logging
import logging.config
import json
import sys
from datetime import datetime
from pathlib import Path

# 日志配置
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "detailed": {
            "()": "python.logging.Formatter",
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        "json": {
            "()": "pythonlogging_json.JsonFormatter",
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "detailed",
            "stream": sys.stdout
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filename": "/var/log/ai-ad-spend/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8"
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "json",
            "filename": "/var/log/ai-ad-spend/error.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8"
        },
        "security_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "json",
            "filename": "/var/log/ai-ad-spend/security.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8"
        }
    },
    "loggers": {
        "": {
            "level": "INFO",
            "handlers": ["console", "file", "error_file"]
        },
        "app.security": {
            "level": "INFO",
            "handlers": ["security_file"],
            "propagate": False
        },
        "app.database": {
            "level": "WARNING",
            "handlers": ["file"],
            "propagate": True
        },
        "uvicorn": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False
        }
    }
}

# 结构化日志记录器
class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def info(self, message: str, **kwargs):
        """记录信息日志"""
        extra_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "ai-ad-spend",
            **kwargs
        }
        self.logger.info(message, extra={"extra_data": extra_data})

    def error(self, message: str, error: Exception = None, **kwargs):
        """记录错误日志"""
        extra_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "ai-ad-spend",
            "error_type": type(error).__name__ if error else None,
            "error_message": str(error) if error else None,
            **kwargs
        }
        self.logger.error(message, extra={"extra_data": extra_data})

    def security(self, event: str, **kwargs):
        """记录安全事件日志"""
        extra_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "ai-ad-spend",
            "event_type": "security",
            "security_event": event,
            **kwargs
        }
        self.logger.info(f"SECURITY: {event}", extra={"extra_data": extra_data})

    def audit(self, action: str, user_id: str = None, resource: str = None, **kwargs):
        """记录审计日志"""
        extra_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "service": "ai-ad-spend",
            "event_type": "audit",
            "action": action,
            "user_id": user_id,
            "resource": resource,
            **kwargs
        }
        self.logger.info(f"AUDIT: {action}", extra={"extra_data": extra_data})

# 使用示例
logger = StructuredLogger("app.main")

logger.info("API请求处理",
           method="POST",
           endpoint="/api/projects",
           user_id="user-123",
           request_id="req-456")

logger.error("数据库连接失败",
            error=Exception("Connection timeout"),
            retry_count=3)

logger.security("登录失败",
               user_id="user-123",
               ip_address="192.168.1.100",
               reason="密码错误")

logger.audit("项目创建",
             user_id="user-123",
             resource="project-456",
             project_name="新项目")
```

### 5.2 Loki日志聚合配置

```yaml
# monitoring/loki.yml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 1h
  max_chunk_age: 1h
  chunk_target_size: 1048576
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
```

### 5.3 Promtail日志收集配置

```yaml
# monitoring/promtail.yml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: containers
    static_configs:
      - targets:
          - localhost
        labels:
          job: containerlogs
          __path__: /var/lib/docker/containers/*/*log

    pipeline_stages:
      - json:
          expressions:
            output: log
            stream: stream
            attrs:
      - json:
          expressions:
            tag:
          source: attrs
      - regex:
          expression: (?P<container_name>(?:[^|]*))\|
          source: tag
      - timestamp:
          format: RFC3339Nano
          source: time
      - labels:
          stream:
          container_name:
      - output:
          source: output

  - job_name: system_logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: varlogs
          __path__: /var/log/*log

    pipeline_stages:
      - regex:
          expression: (?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+)\s+(?P<level>\w+)\s+(?P<message>.*)
      - timestamp:
          format: Jan 02 15:04:05
          source: timestamp
      - labels:
          level:
      - output:
          source: message
```

---

## 6. 告警系统

### 6.1 告警规则配置

```yaml
# monitoring/alert_rules.yml
groups:
  - name: application.rules
    rules:
      # 应用错误率告警
      - alert: HighErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
          service: ai-ad-spend
        annotations:
          summary: "应用错误率过高"
          description: "5分钟内5xx错误率超过5%，当前值: {{ $value | humanizePercentage }}"

      - alert: CriticalErrorRate
        expr: rate(http_requests_total{status_code=~"5.."}[5m]) > 0.15
        for: 1m
        labels:
          severity: critical
          service: ai-ad-spend
        annotations:
          summary: "应用错误率严重"
          description: "5分钟内5xx错误率超过15%，当前值: {{ $value | humanizePercentage }}"

      # 响应时间告警
      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 3m
        labels:
          severity: warning
          service: ai-ad-spend
        annotations:
          summary: "应用响应时间过长"
          description: "95%请求响应时间超过2秒，当前值: {{ $value }}s"

      - alert: CriticalResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5
        for: 1m
        labels:
          severity: critical
          service: ai-ad-spend
        annotations:
          summary: "应用响应时间严重超标"
          description: "95%请求响应时间超过5秒，当前值: {{ $value }}s"

      # 数据库告警
      - alert: DatabaseDown
        expr: up{job="postgres-exporter"} == 0
        for: 1m
        labels:
          severity: critical
          service: database
        annotations:
          summary: "数据库服务宕机"
          description: "PostgreSQL数据库无法访问"

      - alert: HighDatabaseConnections
        expr: pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
          service: database
        annotations:
          summary: "数据库连接数过高"
          description: "当前活跃连接数: {{ $value }}"

      - alert: DatabaseSlowQueries
        expr: rate(pg_stat_statements_mean_time_seconds[5m]) > 1
        for: 5m
        labels:
          severity: warning
          service: database
        annotations:
          summary: "数据库慢查询"
          description: "平均查询时间超过1秒: {{ $value }}s"

      # Redis告警
      - alert: RedisDown
        expr: up{job="redis-exporter"} == 0
        for: 1m
        labels:
          severity: critical
          service: cache
        annotations:
          summary: "Redis服务宕机"
          description: "Redis缓存服务无法访问"

      - alert: RedisMemoryHigh
        expr: redis_memory_used_bytes / redis_memory_max_bytes > 0.9
        for: 5m
        labels:
          severity: warning
          service: cache
        annotations:
          summary: "Redis内存使用率过高"
          description: "Redis内存使用率: {{ $value | humanizePercentage }}"

  - name: business.rules
    rules:
      # 业务指标告警
      - alert: NoNewProjects
        expr: increase(business_projects_created_total[24h]) == 0
        for: 12h
        labels:
          severity: warning
          service: business
        annotations:
          summary: "24小时内无新项目创建"
          description: "系统可能存在业务异常"

      - alert: HighFailedLogins
        expr: rate(user_login_attempts_total{status="failed"}[5m]) > 5
        for: 2m
        labels:
          severity: warning
          service: security
        annotations:
          summary: "高频登录失败"
          description: "5分钟内登录失败率过高: {{ $value }}次/秒"

      - alert: PendingRechargeHigh
        expr: business_recharge_pending_amount > 50000
        for: 30m
        labels:
          severity: warning
          service: business
        annotations:
          summary: "待处理充值金额过高"
          description: "当前待处理充值金额: ¥{{ $value }}"

  - name: infrastructure.rules
    rules:
      # 系统资源告警
      - alert: HighCPUUsage
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
          service: infrastructure
        annotations:
          summary: "CPU使用率过高"
          description: "实例 {{ $labels.instance }} CPU使用率: {{ $value }}%"

      - alert: HighMemoryUsage
        expr: (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100 > 85
        for: 5m
        labels:
          severity: warning
          service: infrastructure
        annotations:
          summary: "内存使用率过高"
          description: "实例 {{ $labels.instance }} 内存使用率: {{ $value }}%"

      - alert: DiskSpaceLow
        expr: (1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100 > 90
        for: 5m
        labels:
          severity: critical
          service: infrastructure
        annotations:
          summary: "磁盘空间不足"
          description: "实例 {{ $labels.instance }} 磁盘 {{ $labels.mountpoint }} 使用率: {{ $value }}%"

      - alert: DiskSpaceWarning
        expr: (1 - (node_filesystem_avail_bytes / node_filesystem_size_bytes)) * 100 > 80
        for: 10m
        labels:
          severity: warning
          service: infrastructure
        annotations:
          summary: "磁盘空间预警"
          description: "实例 {{ $labels.instance }} 磁盘 {{ $labels.mountpoint }} 使用率: {{ $value }}%"
```

### 6.2 AlertManager配置

```yaml
# monitoring/alertmanager.yml
global:
  smtp_smarthost: 'smtp.company.com:587'
  smtp_from: 'alerts@company.com'
  smtp_auth_username: 'alerts@company.com'
  smtp_auth_password: 'smtp-password'

templates:
  - '/etc/alertmanager/templates/*.tmpl'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'
  routes:
    # 严重告警立即通知
    - match:
        severity: critical
      receiver: 'critical-alerts'
      group_wait: 0s
      repeat_interval: 5m

    # 安全告警特殊处理
    - match:
        service: security
      receiver: 'security-alerts'
      group_wait: 0s
      repeat_interval: 30m

    # 业务告警
    - match:
        service: business
      receiver: 'business-alerts'
      repeat_interval: 2h

receivers:
  # 默认接收者
  - name: 'default'
    email_configs:
      - to: 'ops@company.com'
        subject: '[{{ .Status | toUpper }}] {{ .GroupLabels.alertname }}'
        body: |
          {{ range .Alerts }}
          告警: {{ .Annotations.summary }}
          描述: {{ .Annotations.description }}
          标签: {{ range .Labels.SortedPairs }}{{ .Name }}={{ .Value }} {{ end }}
          时间: {{ .StartsAt }}
          {{ end }}

  # 严重告警
  - name: 'critical-alerts'
    email_configs:
      - to: 'critical-alerts@company.com'
        subject: '[CRITICAL] {{ .GroupLabels.alertname }}'
        body: |
          紧急告警通知！
          {{ range .Alerts }}
          告警: {{ .Annotations.summary }}
          描述: {{ .Annotations.description }}
          时间: {{ .StartsAt }}
          立即处理！
          {{ end }}
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#critical-alerts'
        title: '🚨 Critical Alert'
        text: |
          {{ range .Alerts }}
          {{ .Annotations.summary }}
          {{ .Annotations.description }}
          {{ end }}

  # 安全告警
  - name: 'security-alerts'
    email_configs:
      - to: 'security-team@company.com'
        subject: '[SECURITY] {{ .GroupLabels.alertname }}'
    webhook_configs:
      - url: 'http://security-alert-handler:8080/webhook'

  # 业务告警
  - name: 'business-alerts'
    email_configs:
      - to: 'business-team@company.com'
        subject: '[BUSINESS] {{ .GroupLabels.alertname }}'

# 告警抑制规则
inhibit_rules:
  # 如果主机宕机，抑制该主机的所有其他告警
  - source_match:
      alertname: 'InstanceDown'
    target_match_re:
      alertname: '(CPU|Memory|Disk)High'
    equal: ['instance']

  # 如果数据库宕机，抑制数据库相关的其他告警
  - source_match:
      alertname: 'DatabaseDown'
    target_match:
      service: 'database'
    equal: ['job']
```

### 6.3 自定义告警通知

```python
# backend/app/monitoring/alerts.py
import asyncio
import aiohttp
import logging
from typing import Dict, List, Any
from datetime import datetime

class AlertManager:
    def __init__(self):
        self.webhook_urls = {
            'slack': os.getenv('SLACK_WEBHOOK_URL'),
            'dingtalk': os.getenv('DINGTALK_WEBHOOK_URL'),
            'email': os.getenv('ALERT_EMAIL_URL')
        }

    async def send_alert(self, alert_data: Dict[str, Any], channels: List[str] = None):
        """发送告警通知"""
        channels = channels or ['slack']

        for channel in channels:
            try:
                if channel == 'slack':
                    await self._send_slack_alert(alert_data)
                elif channel == 'dingtalk':
                    await self._send_dingtalk_alert(alert_data)
                elif channel == 'email':
                    await self._send_email_alert(alert_data)

            except Exception as e:
                logging.error(f"Failed to send {channel} alert: {e}")

    async def _send_slack_alert(self, alert_data: Dict[str, Any]):
        """发送Slack告警"""
        webhook_url = self.webhook_urls.get('slack')
        if not webhook_url:
            return

        color = {
            'critical': 'danger',
            'warning': 'warning',
            'info': 'good'
        }.get(alert_data.get('severity', 'info'), 'warning')

        payload = {
            "attachments": [{
                "color": color,
                "title": f"🚨 {alert_data.get('title', 'Alert')}",
                "fields": [
                    {"title": "严重程度", "value": alert_data.get('severity', 'Unknown'), "short": True},
                    {"title": "服务", "value": alert_data.get('service', 'Unknown'), "short": True},
                    {"title": "描述", "value": alert_data.get('description', 'No description'), "short": False},
                ],
                "footer": "AI广告代投系统",
                "ts": int(datetime.now().timestamp())
            }]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Slack API error: {response.status}")

    async def _send_dingtalk_alert(self, alert_data: Dict[str, Any]):
        """发送钉钉告警"""
        webhook_url = self.webhook_urls.get('dingtalk')
        if not webhook_url:
            return

        emoji = {
            'critical': '🔥',
            'warning': '⚠️',
            'info': 'ℹ️'
        }.get(alert_data.get('severity', 'info'), '⚠️')

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"{emoji} 系统告警",
                "text": f"""
## {alert_data.get('title', 'Alert')}

**严重程度**: {alert_data.get('severity', 'Unknown')}
**服务**: {alert_data.get('service', 'Unknown')}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**描述**:
{alert_data.get('description', 'No description')}

---

*AI广告代投系统监控*
                """
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status != 200:
                    raise Exception(f"DingTalk API error: {response.status}")

    async def _send_email_alert(self, alert_data: Dict[str, Any]):
        """发送邮件告警"""
        # 这里可以集成邮件服务API
        logging.info(f"Email alert sent: {alert_data}")

# 业务告警触发器
class BusinessAlertTrigger:
    def __init__(self, alert_manager: AlertManager):
        self.alert_manager = alert_manager

    async def check_and_trigger_alerts(self):
        """检查并触发业务告警"""
        while True:
            try:
                await self._check_business_rules()
                await asyncio.sleep(300)  # 每5分钟检查一次
            except Exception as e:
                logging.error(f"Error in business alert check: {e}")
                await asyncio.sleep(60)

    async def _check_business_rules(self):
        """检查业务规则"""
        # 检查是否有长时间无新项目
        await self._check_no_new_projects()

        # 检查充值申请积压
        await self._check_pending_recharges()

        # 检查异常登录行为
        await self._check_suspicious_logins()

    async def _check_no_new_projects(self):
        """检查是否有长时间无新项目"""
        # 这里应该查询数据库或指标
        has_new_projects = await self._query_new_projects_last_24h()

        if not has_new_projects:
            await self.alert_manager.send_alert({
                'title': '业务预警：24小时内无新项目',
                'description': '系统已经24小时没有新的项目创建，请检查业务是否正常',
                'severity': 'warning',
                'service': 'business'
            })

    async def _check_pending_recharges(self):
        """检查充值申请积压"""
        pending_amount = await self._query_pending_recharge_amount()

        if pending_amount > 50000:  # 超过5万元
            await self.alert_manager.send_alert({
                'title': '充值申请积压',
                'description': f'待处理充值金额达到 ¥{pending_amount:,.2f}，请及时处理',
                'severity': 'warning',
                'service': 'business'
            })

    async def _check_suspicious_logins(self):
        """检查异常登录行为"""
        failed_login_count = await self._query_failed_login_count_last_5min()

        if failed_login_count > 50:  # 5分钟内失败登录超过50次
            await self.alert_manager.send_alert({
                'title': '异常登录行为',
                'description': f'5分钟内失败登录次数达到 {failed_login_count} 次，可能存在攻击行为',
                'severity': 'critical',
                'service': 'security'
            })
```

---

## 7. 故障处理

### 7.1 故障响应流程

```python
# backend/app/monitoring/incident_manager.py
import asyncio
import logging
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class IncidentSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class IncidentStatus(Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    IDENTIFIED = "identified"
    MONITORING = "monitoring"
    RESOLVED = "resolved"

class Incident:
    def __init__(self,
                 id: str,
                 title: str,
                 description: str,
                 severity: IncidentSeverity,
                 service: str):
        self.id = id
        self.title = title
        self.description = description
        self.severity = severity
        self.service = service
        self.status = IncidentStatus.OPEN
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.assigned_to = None
        self.resolution = None
        self.tags = []

class IncidentManager:
    def __init__(self):
        self.active_incidents: Dict[str, Incident] = {}
        self.alert_manager = AlertManager()

    async def create_incident(self,
                           title: str,
                           description: str,
                           severity: IncidentSeverity,
                           service: str,
                           alert_data: Dict = None) -> Incident:
        """创建故障事件"""
        incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        incident = Incident(
            id=incident_id,
            title=title,
            description=description,
            severity=severity,
            service=service
        )

        if alert_data:
            incident.tags.extend(alert_data.get('tags', []))

        self.active_incidents[incident_id] = incident

        # 发送告警通知
        await self._send_incident_alert(incident)

        # 记录到日志
        logging.info(f"Incident created: {incident_id} - {title}")

        return incident

    async def update_incident_status(self,
                                   incident_id: str,
                                   status: IncidentStatus,
                                   update_message: str = None,
                                   assigned_to: str = None):
        """更新故障状态"""
        if incident_id not in self.active_incidents:
            logging.error(f"Incident {incident_id} not found")
            return

        incident = self.active_incidents[incident_id]
        old_status = incident.status
        incident.status = status
        incident.updated_at = datetime.utcnow()

        if assigned_to:
            incident.assigned_to = assigned_to

        # 发送状态更新通知
        await self._send_status_update(incident, old_status, update_message)

        logging.info(f"Incident {incident_id} status updated: {old_status.value} -> {status.value}")

    async def resolve_incident(self,
                             incident_id: str,
                             resolution: str):
        """解决故障事件"""
        if incident_id not in self.active_incidents:
            logging.error(f"Incident {incident_id} not found")
            return

        incident = self.active_incidents[incident_id]
        incident.status = IncidentStatus.RESOLVED
        incident.resolution = resolution
        incident.updated_at = datetime.utcnow()

        # 发送解决通知
        await self._send_resolution_alert(incident)

        # 将事件移到历史记录（在实际实现中应该持久化）
        del self.active_incidents[incident_id]

        logging.info(f"Incident {incident_id} resolved: {resolution}")

    async def _send_incident_alert(self, incident: Incident):
        """发送故障告警"""
        severity_mapping = {
            IncidentSeverity.LOW: 'info',
            IncidentSeverity.MEDIUM: 'warning',
            IncidentSeverity.HIGH: 'warning',
            IncidentSeverity.CRITICAL: 'critical'
        }

        alert_data = {
            'title': f'🚨 故障事件: {incident.title}',
            'description': f"""
**故障ID**: {incident.id}
**服务**: {incident.service}
**严重程度**: {incident.severity.value}
**创建时间**: {incident.created_at.strftime('%Y-%m-%d %H:%M:%S')}

**描述**:
{incident.description}

**影响范围**:
待评估

**当前状态**:
正在调查中...
            """,
            'severity': severity_mapping[incident.severity],
            'service': incident.service,
            'tags': ['incident', incident.service] + incident.tags
        }

        await self.alert_manager.send_alert(alert_data, ['slack', 'email'])

    async def _send_status_update(self, incident: Incident, old_status: IncidentStatus, message: str = None):
        """发送状态更新"""
        if old_status == incident.status:
            return

        alert_data = {
            'title': f'📋 故障状态更新: {incident.id}',
            'description': f"""
**故障**: {incident.title}
**状态变更**: {old_status.value} -> {incident.status.value}
**更新时间**: {incident.updated_at.strftime('%Y-%m-%d %H:%M:%S')}
"""
        }

        if message:
            alert_data['description'] += f"\n**备注**: {message}"

        if incident.assigned_to:
            alert_data['description'] += f"\n**负责人**: {incident.assigned_to}"

        await self.alert_manager.send_alert(alert_data, ['slack'])

    async def _send_resolution_alert(self, incident: Incident):
        """发送故障解决通知"""
        alert_data = {
            'title': f'✅ 故障已解决: {incident.id}',
            'description': f"""
**故障**: {incident.title}
**解决时间**: {incident.updated_at.strftime('%Y-%m-%d %H:%M:%S')}
**持续时间**: {incident.updated_at - incident.created_at}

**解决方案**:
{incident.resolution}
            """,
            'severity': 'info',
            'service': incident.service,
            'tags': ['resolved', incident.service]
        }

        await self.alert_manager.send_alert(alert_data, ['slack', 'email'])

    def get_active_incidents(self) -> List[Incident]:
        """获取活跃故障列表"""
        return list(self.active_incidents.values())

    def get_incident_summary(self) -> Dict[str, int]:
        """获取故障摘要统计"""
        incidents = self.get_active_incidents()

        summary = {
            'total': len(incidents),
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }

        for incident in incidents:
            summary[incident.severity.value] += 1

        return summary

# 故障响应自动化
class IncidentResponseAutomation:
    def __init__(self, incident_manager: IncidentManager):
        self.incident_manager = incident_manager

    async def auto_escalate_incidents(self):
        """自动升级故障"""
        while True:
            try:
                await self._check_escalation_rules()
                await asyncio.sleep(300)  # 每5分钟检查一次
            except Exception as e:
                logging.error(f"Error in incident escalation: {e}")
                await asyncio.sleep(60)

    async def _check_escalation_rules(self):
        """检查升级规则"""
        incidents = self.incident_manager.get_active_incidents()

        for incident in incidents:
            # 规则1: 严重故障30分钟未处理，自动升级
            if (incident.severity == IncidentSeverity.CRITICAL and
                incident.status == IncidentStatus.OPEN and
                datetime.utcnow() - incident.created_at > timedelta(minutes=30)):

                await self.incident_manager.update_incident_status(
                    incident.id,
                    IncidentStatus.INVESTIGATING,
                    "自动升级：严重故障超过30分钟未处理"
                )

                # 发送升级通知
                await self._send_escalation_notification(incident)

            # 规则2: 故障超过2小时未解决，发送提醒
            if (datetime.utcnow() - incident.created_at > timedelta(hours=2) and
                incident.status not in [IncidentStatus.RESOLVED, IncidentStatus.MONITORING]):

                await self._send_reminder_notification(incident)

    async def _send_escalation_notification(self, incident: Incident):
        """发送升级通知"""
        alert_data = {
            'title': f'🔥 故障自动升级: {incident.id}',
            'description': f"""
故障 {incident.title} 已超过30分钟未处理，已自动升级。

**故障ID**: {incident.id}
**严重程度**: {incident.severity.value}
**创建时间**: {incident.created_at.strftime('%Y-%m-%d %H:%M:%S')}

请立即处理此故障！
            """,
            'severity': 'critical',
            'service': incident.service
        }

        await self.incident_manager.alert_manager.send_alert(alert_data, ['slack', 'email'])

    async def _send_reminder_notification(self, incident: Incident):
        """发送提醒通知"""
        duration = datetime.utcnow() - incident.created_at

        alert_data = {
            'title': f'⏰ 故障处理提醒: {incident.id}',
            'description': f"""
故障 {incident.title} 已持续 {duration}。

**故障ID**: {incident.id}
**当前状态**: {incident.status.value}
**负责人**: {incident.assigned_to or '未分配'}

请及时跟进处理进度。
            """,
            'severity': 'warning',
            'service': incident.service
        }

        await self.incident_manager.alert_manager.send_alert(alert_data, ['slack'])
```

### 7.2 故障处理手册

```markdown
# 故障处理手册 (Playbook)

## 1. 应用服务故障

### 1.1 服务无响应
**症状**: API返回502/503错误，健康检查失败

**排查步骤**:
1. 检查应用服务状态
   ```bash
   docker-compose ps
   docker-compose logs backend
   ```

2. 检查服务资源使用
   ```bash
   docker stats
   ```

3. 检查应用日志
   ```bash
   docker-compose logs --tail=100 backend
   ```

4. 检查端口占用
   ```bash
   netstat -tlnp | grep :8000
   ```

**解决措施**:
- 重启应用服务: `docker-compose restart backend`
- 扩容服务: `docker-compose up -d --scale backend=3`
- 如果持续失败，回滚到上一个版本

### 1.2 数据库连接故障
**症状**: 数据库相关错误，连接超时

**排查步骤**:
1. 检查数据库服务状态
   ```bash
   docker-compose ps postgres
   docker-compose logs postgres
   ```

2. 检查数据库连接数
   ```sql
   SELECT count(*) FROM pg_stat_activity;
   ```

3. 检查数据库资源使用
   ```bash
   docker exec -it postgres psql -U postgres -c "SELECT * FROM pg_stat_activity;"
   ```

**解决措施**:
- 重启数据库服务: `docker-compose restart postgres`
- 清理空闲连接: `SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle';`
- 扩容数据库资源

### 1.3 Redis缓存故障
**症状**: 缓存相关功能异常，认证失败

**排查步骤**:
1. 检查Redis服务状态
   ```bash
   docker-compose ps redis
   docker-compose logs redis
   ```

2. 测试Redis连接
   ```bash
   docker exec -it redis redis-cli ping
   ```

3. 检查Redis内存使用
   ```bash
   docker exec -it redis redis-cli info memory
   ```

**解决措施**:
- 重启Redis服务: `docker-compose restart redis`
- 清理Redis缓存: `docker exec -it redis redis-cli FLUSHALL`
- 扩容Redis内存

## 2. 业务逻辑故障

### 2.1 数据不一致
**症状**: 前后端数据显示不一致

**排查步骤**:
1. 检查数据库数据完整性
   ```sql
   SELECT COUNT(*) FROM projects;
   SELECT COUNT(*) FROM ad_accounts;
   SELECT project_id, COUNT(*) FROM ad_accounts GROUP BY project_id;
   ```

2. 检查外键约束
   ```sql
   SELECT conname, conrelid::regclass, confrelid::regclass
   FROM pg_constraint
   WHERE contype = 'f';
   ```

3. 检查触发器状态
   ```sql
   SELECT tgname, tgrelid::regclass, tgenabled
   FROM pg_trigger;
   ```

**解决措施**:
- 运行数据一致性检查脚本
- 修复损坏的数据
- 重新初始化相关表

### 2.2 性能下降
**症状**: 响应时间明显增加

**排查步骤**:
1. 检查慢查询日志
   ```sql
   SELECT query, mean_time, calls
   FROM pg_stat_statements
   ORDER BY mean_time DESC
   LIMIT 10;
   ```

2. 检查索引使用情况
   ```sql
   SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
   FROM pg_stat_user_indexes
   ORDER BY idx_scan DESC;
   ```

3. 检查表大小和行数
   ```sql
   SELECT
       schemaname,
       tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
       n_tup_ins as inserts,
       n_tup_upd as updates,
       n_tup_del as deletes
   FROM pg_stat_user_tables
   ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
   ```

**解决措施**:
- 优化慢查询
- 添加或重建索引
- 清理或归档历史数据
- 扩容数据库资源

## 3. 安全相关故障

### 3.1 大量登录失败
**症状**: 用户无法正常登录，安全告警

**排查步骤**:
1. 检查登录失败日志
   ```bash
   grep "login failed" /var/log/ai-ad-spend/app.log | tail -50
   ```

2. 检查异常IP
   ```bash
   grep "login failed" /var/log/ai-ad-spend/app.log | \
   grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+\.[0-9]\+' | \
   sort | uniq -c | sort -nr | head -10
   ```

3. 检查用户账户状态
   ```sql
   SELECT username, last_login, failed_login_attempts
   FROM users
   WHERE failed_login_attempts > 5;
   ```

**解决措施**:
- 启动速率限制
- 封禁异常IP地址
- 锁定受攻击的账户
- 发送安全告警

### 3.2 数据泄露风险
**症状**: 敏感数据意外暴露

**排查步骤**:
1. 检查访问日志
   ```bash
   grep -E "(password|token|secret)" /var/log/nginx/access.log
   ```

2. 检查API响应
   ```bash
   curl -s "http://localhost:8000/api/users" | jq .
   ```

3. 检查权限配置
   ```sql
   SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
   FROM pg_policies;
   ```

**解决措施**:
- 立即修复数据暴露点
- 更新权限配置
- 撤销可疑的访问令牌
- 进行安全审计

## 4. 运维操作流程

### 4.1 紧急响应流程
1. **接收告警** (0-5分钟)
   - 确认告警信息
   - 创建故障事件
   - 通知相关人员

2. **初步诊断** (5-15分钟)
   - 检查服务状态
   - 分析日志和指标
   - 确定影响范围

3. **紧急处理** (15-30分钟)
   - 实施临时解决方案
   - 恢复关键服务
   - 缓解故障影响

4. **深入分析** (30-60分钟)
   - 找出根本原因
   - 制定长期解决方案
   - 更新监控告警

5. **恢复验证** (60分钟+)
   - 验证服务完全恢复
   - 监控系统稳定性
   - 通知相关方故障解决

### 4.2 变更管理流程
1. **变更申请**
   - 填写变更申请单
   - 进行风险评估
   - 获得必要审批

2. **变更准备**
   - 制定详细实施计划
   - 准备回滚方案
   - 安排变更窗口

3. **变更实施**
   - 按计划执行变更
   - 实时监控系统状态
   - 记录实施过程

4. **变更验证**
   - 验证功能正常
   - 检查性能指标
   - 确认无副作用

5. **变更关闭**
   - 更新系统文档
   - 总结变更经验
   - 关闭变更请求
```

---

## 📞 运维支持

### 运维团队联系
- **运维负责人**: ops@company.com
- **值班工程师**: oncall@company.com
- **紧急故障热线**: +86-xxx-xxxx-xxxx

### 监控面板
- **应用监控**: https://grafana.yourdomain.com
- **基础设施监控**: https://prometheus.yourdomain.com
- **日志查询**: https://loki.yourdomain.com
- **告警管理**: https://alertmanager.yourdomain.com

### 运维工具
- **服务部署**: https://deploy.yourdomain.com
- **配置管理**: https://config.yourdomain.com
- **故障跟踪**: https://incidents.yourdomain.com
- **知识库**: https://kb.yourdomain.com

---

**文档版本**: v1.0
**最后更新**: 2025-11-11
**下次审查**: 监控架构更新时
**维护责任人**: 运维团队负责人