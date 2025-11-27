---
version: v1.0
status: ready_for_production
layer: infrastructure
owner: wade
last_reviewed: 2025-11-27
baseline: MASTER.md v3.4, SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0
---

# Observability Guide

## 1. Purpose

定义可观测性指南，涵盖监控（Monitoring）、日志（Logging）、追踪（Tracing）三大支柱，确保系统健康监控和故障快速诊断。

## 2. Observability Three Pillars

```
┌─────────────────────────────────────────────────────────┐
│                  Observability                          │
├─────────────────────────────────────────────────────────┤
│  1. Metrics   │  2. Logs      │  3. Traces             │
│  (What)       │  (Why)        │  (Where + How long)    │
├───────────────┼───────────────┼────────────────────────┤
│  - CPU usage  │  - Error logs │  - Request trace ID    │
│  - Memory     │  - API calls  │  - Span duration       │
│  - Latency    │  - User actions│ - Service dependencies│
│  - Error rate │  - SQL queries│  - Bottleneck analysis │
└───────────────┴───────────────┴────────────────────────┘
```

---

## 3. Current Implementation

### 3.1 Metrics (Basic)

**Railway Dashboard**:
- CPU usage (%)
- Memory usage (MB)
- Network I/O (MB/s)
- HTTP request count
- HTTP response times (p50, p95, p99)

**Vercel Dashboard**:
- Page load times
- Function execution times
- Bandwidth usage
- Request count

**Supabase Dashboard**:
- Database connections
- Query performance (slow query log)
- Table sizes
- RLS policy violations

### 3.2 Logs (Current)

**Backend Logging** (Python `logging` module):

```python
# backend/app/logging_config.py
import logging
import sys

def setup_logging(log_level: str = "INFO"):
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='{"time":"%(asctime)s", "level":"%(levelname)s", "logger":"%(name)s", "message":"%(message)s"}',
        stream=sys.stdout
    )

# Usage
logger = logging.getLogger(__name__)
logger.info("Daily report created", extra={"report_id": 123, "user_id": 456})
logger.error("Database connection failed", extra={"error": str(e)})
```

**Frontend Logging** (Console + Error Tracking):

```typescript
// frontend/lib/logger.ts
export const logger = {
  info: (message: string, meta?: Record<string, any>) => {
    console.log(JSON.stringify({ level: 'info', message, ...meta, timestamp: new Date().toISOString() }));
  },
  error: (message: string, error?: Error, meta?: Record<string, any>) => {
    console.error(JSON.stringify({ level: 'error', message, error: error?.message, stack: error?.stack, ...meta, timestamp: new Date().toISOString() }));
  },
};

// Usage
logger.info('User logged in', { userId: 123 });
logger.error('API call failed', error, { endpoint: '/api/v1/topups' });
```

**Log Levels**:
- **DEBUG**: Detailed debugging information (local development only)
- **INFO**: General informational messages (normal operation)
- **WARNING**: Warning messages (recoverable errors)
- **ERROR**: Error messages (failed operations, need attention)
- **CRITICAL**: Critical errors (system failure, immediate action required)

**Current Log Storage**:
- **Railway Logs**: Backend logs (searchable in Railway dashboard, 7-day retention)
- **Vercel Logs**: Frontend logs (searchable in Vercel dashboard, 7-day retention)
- **Supabase Logs**: Database logs (query logs, error logs, 7-day retention)

### 3.3 Tracing (None - Planned)

**Current Status**: No distributed tracing implemented

**Planned Implementation** (2026-Q1):
- **OpenTelemetry** for instrumentation
- **Jaeger** for trace visualization
- **Trace Context Propagation** (X-Trace-ID header across services)

---

## 4. Future Roadmap: Prometheus + Grafana (Metrics)

### 4.1 Prometheus Setup (Planned 2026-Q1)

**Architecture**:
```
Backend (FastAPI) → Prometheus Exporter → Prometheus Server → Grafana Dashboard
                                               ↓
                                          AlertManager → Slack/PagerDuty
```

**Metrics to Track**:

| Metric | Type | Description | Alert Threshold |
|--------|------|-------------|-----------------|
| `http_requests_total` | Counter | Total HTTP requests | N/A |
| `http_request_duration_seconds` | Histogram | Request latency | p99 > 2s |
| `http_requests_errors_total` | Counter | HTTP 5xx errors | Error rate > 5% |
| `database_connections_active` | Gauge | Active DB connections | > 80 connections |
| `daily_reports_created_total` | Counter | Daily reports created | N/A |
| `ledger_entries_created_total` | Counter | Ledger entries created | N/A |

**Backend Instrumentation** (Prometheus client):

```python
# backend/app/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI

app = FastAPI()

# Metrics
http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
http_request_duration_seconds = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])
database_connections_active = Gauge('database_connections_active', 'Active database connections')

# Middleware to track metrics
@app.middleware("http")
async def metrics_middleware(request, call_next):
    with http_request_duration_seconds.labels(method=request.method, endpoint=request.url.path).time():
        response = await call_next(request)
        http_requests_total.labels(method=request.method, endpoint=request.url.path, status=response.status_code).inc()
    return response

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

### 4.2 Grafana Dashboard (Planned 2026-Q1)

**Dashboards to Create**:
1. **Application Health Dashboard**:
   - Request rate (requests/second)
   - Error rate (5xx errors %)
   - Latency (p50, p95, p99)
   - Active users (current sessions)

2. **Business Metrics Dashboard**:
   - Daily reports created (count)
   - Topups created (count, total amount)
   - Ledger entries created (count)
   - Reconciliation status (matched %, mismatched %)

3. **Infrastructure Dashboard**:
   - CPU usage (%)
   - Memory usage (%)
   - Disk I/O (MB/s)
   - Network I/O (MB/s)

---

## 5. Future Roadmap: ELK Stack (Logs)

### 5.1 ELK Stack Setup (Planned 2026-Q2)

**Architecture**:
```
Backend (FastAPI) → Logstash → Elasticsearch ← Kibana Dashboard
Frontend (Next.js) →
```

**Components**:
- **Elasticsearch**: Distributed search and analytics engine (stores logs)
- **Logstash**: Log aggregation and transformation pipeline
- **Kibana**: Log visualization and search UI

**Benefits**:
- Centralized log storage (across Railway, Vercel, Supabase)
- Full-text search on logs
- Log correlation by trace ID
- Long-term log retention (30+ days)

**Log Format** (JSON structured logging):

```json
{
  "timestamp": "2025-11-27T10:30:00Z",
  "level": "INFO",
  "logger": "app.routers.daily_reports",
  "message": "Daily report created successfully",
  "trace_id": "abc123",
  "user_id": 456,
  "report_id": 789,
  "environment": "production"
}
```

### 5.2 Kibana Dashboard (Planned 2026-Q2)

**Dashboards to Create**:
1. **Error Log Dashboard**:
   - Error count by endpoint
   - Error stack traces
   - Error trends over time

2. **API Call Dashboard**:
   - Top 10 slowest endpoints
   - API call distribution by user
   - Failed API calls

3. **User Activity Dashboard**:
   - User login events
   - User actions (create topup, submit report, etc.)
   - User session duration

---

## 6. Future Roadmap: OpenTelemetry + Jaeger (Tracing)

### 6.1 OpenTelemetry Instrumentation (Planned 2026-Q2)

**Architecture**:
```
Frontend (Next.js) → API Gateway → Backend (FastAPI) → Database (PostgreSQL)
      |                    |                |                    |
  [Trace Span]        [Trace Span]     [Trace Span]       [Trace Span]
      └────────────────────┴────────────────┴────────────────────┘
                            ↓
                    OpenTelemetry Collector
                            ↓
                       Jaeger Backend
                            ↓
                     Jaeger UI (Trace Visualization)
```

**Trace Example**:

```
Trace ID: abc123
│
├─ Frontend: Page Load (500ms)
│  ├─ API Call: GET /api/v1/daily-reports (300ms)
│  │  ├─ Backend: Query daily_reports table (200ms)
│  │  │  └─ Database: SELECT * FROM daily_reports (180ms)
│  │  └─ Backend: Serialize response (20ms)
│  └─ Frontend: Render components (100ms)
```

**Benefits**:
- Identify bottlenecks (which service is slow?)
- Trace request flow across multiple services
- Debug performance issues (why is this API slow?)

### 6.2 Jaeger Dashboard (Planned 2026-Q2)

**Features**:
- Trace search by trace ID, service, operation
- Trace timeline visualization
- Service dependency graph
- Latency distribution histograms

---

## 7. Health Checks

### 7.1 Backend Health Endpoint

**Endpoint**: `GET /health`

**Implementation**:

```python
# backend/app/routers/health.py
from fastapi import APIRouter, status
from app.database import engine

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    # Check database connection
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        database_status = "connected"
    except Exception as e:
        database_status = f"error: {str(e)}"

    return {
        "status": "healthy" if database_status == "connected" else "unhealthy",
        "database": database_status,
        "version": "1.2.3",  # App version
        "uptime": get_uptime_seconds(),
    }
```

**Health Check Criteria**:
- ✅ HTTP 200 response
- ✅ Database connection successful (`database: "connected"`)
- ✅ Response time < 500ms

**Monitoring**:
- Railway health checks (automatic, every 30s)
- External monitoring (UptimeRobot, Pingdom) - checks every 5 minutes

### 7.2 Frontend Health Check

**Endpoint**: `GET /api/health` (Next.js API route)

**Implementation**:

```typescript
// frontend/app/api/health/route.ts
export async function GET() {
  // Check backend API connection
  try {
    const response = await fetch(process.env.NEXT_PUBLIC_API_URL + '/health', { cache: 'no-store' });
    const data = await response.json();

    return Response.json({
      status: data.status === 'healthy' ? 'healthy' : 'degraded',
      backend: data.status,
      version: '1.0.0',
    });
  } catch (error) {
    return Response.json({
      status: 'unhealthy',
      backend: 'unreachable',
      error: error.message,
    }, { status: 503 });
  }
}
```

---

## 8. Alerting (Planned 2026-Q1)

### 8.1 Alert Rules

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| **High Error Rate** | 5xx error rate > 5% (5-min window) | Critical | Page on-call engineer via PagerDuty |
| **High Latency** | p99 latency > 2s (5-min window) | Warning | Slack notification to #alerts channel |
| **Database Connection Failure** | Health check fails (database unreachable) | Critical | Page on-call engineer + Slack alert |
| **Disk Space Low** | Disk usage > 85% | Warning | Slack notification to #infra channel |
| **Memory Usage High** | Memory usage > 90% (10-min window) | Warning | Slack notification to #infra channel |

### 8.2 Alert Channels

| Channel | Use Case | Configuration |
|---------|---------|---------------|
| **PagerDuty** | Critical alerts (page on-call engineer) | Integrate with Prometheus AlertManager |
| **Slack** | Warning alerts (notify team) | Webhook integration (`https://hooks.slack.com/...`) |
| **Email** | Low-priority alerts (daily digest) | SMTP configuration |

### 8.3 On-Call Rotation

**Schedule**:
- **Primary On-Call**: Rotates weekly (Monday 9am → next Monday 9am)
- **Secondary On-Call**: Backup (escalation after 15 minutes)

**Escalation Policy**:
1. Alert triggered → Page primary on-call (PagerDuty)
2. If no response within 15 minutes → Page secondary on-call
3. If no response within 30 minutes → Page engineering manager

---

## 9. Traceability

### 9.1 References to Dev-Guides Layer

| Dev-Guide Document | Observability Implementation |
|--------------------|------------------------------|
| [TROUBLESHOOTING.md](../3.dev-guides/TROUBLESHOOTING.md) | Logs and metrics used for debugging (error patterns, slow queries) |
| [DEPLOYMENT_GUIDE.md](../3.dev-guides/DEPLOYMENT_GUIDE.md) | Health checks verify deployment success |

### 9.2 References to SoT Layer

| SoT Document | Observability Metrics |
|--------------|----------------------|
| [STATE_MACHINE.md](../2.sot/STATE_MACHINE.md) v2.6 | Track daily report state transitions (metrics: reports in each state) |
| [API_SOT.md](../2.sot/API_SOT.md) v9.0 | Monitor API endpoint latency and error rates |
| [ERROR_CODES_SOT.md](../2.sot/ERROR_CODES_SOT.md) v2.1 | Aggregate error logs by error code (e.g., AUTH-003, VAL-001) |

---

## 10. Summary

### 10.1 Current Implementation (2025-11-27)

| Pillar | Status | Tools |
|--------|--------|-------|
| **Metrics** | Basic | Railway Dashboard, Vercel Dashboard, Supabase Dashboard |
| **Logs** | Basic (JSON structured) | Railway Logs, Vercel Logs, Python `logging` module |
| **Tracing** | None | N/A |
| **Alerting** | Manual (dashboard monitoring) | N/A |

### 10.2 Planned Implementation (2026-Q1)

| Pillar | Status | Tools |
|--------|--------|-------|
| **Metrics** | Advanced | Prometheus + Grafana |
| **Logs** | Centralized | ELK Stack (Elasticsearch, Logstash, Kibana) |
| **Tracing** | Distributed | OpenTelemetry + Jaeger |
| **Alerting** | Automated | PagerDuty + Slack integration |

---

**Document Version**: v1.0
**Last Updated**: 2025-11-27
**Baseline**: MASTER.md v3.4, SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0
