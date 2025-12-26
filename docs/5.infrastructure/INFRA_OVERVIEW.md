---
version: v1.0
status: ready_for_production
layer: infrastructure
owner: wade
last_reviewed: 2025-11-27
baseline: MASTER.md v4.4, SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0
---

# Infrastructure Layer Overview

## 1. Purpose

定义 AI 广告代投系统的基础设施层（Infrastructure Layer）的职责、范围和文档体系。Infrastructure Layer 聚焦于系统的部署、运维、监控和可观测性，确保开发规范（Dev-Guides Layer）能够在生产环境中稳定运行。

## 2. Layer Positioning in ASDD 5-Layer Model

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Overview (MASTER.md, PROJECT.md, ARCHITECTURE.md) │  ← 架构宪法
├─────────────────────────────────────────────────────────────┤
│  Layer 2: SoT (STATE_MACHINE, DATA_SCHEMA, API_SOT, ...)   │  ← 真相来源
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Dev-Guides (API_DEVELOPMENT_FLOW, TESTING, ...)  │  ← 开发规范
├─────────────────────────────────────────────────────────────┤
│  Layer 4: Architecture (DDD patterns, System design, ...)   │  ← 架构设计
├─────────────────────────────────────────────────────────────┤
│  Layer 5: Infrastructure (CI/CD, Deployment, Monitoring)    │  ← 基础设施实现 (THIS LAYER)
└─────────────────────────────────────────────────────────────┘
```

### 2.1 Relationship to Architecture Layer

| Aspect | Architecture Layer | Infrastructure Layer |
|--------|-------------------|---------------------|
| **Focus** | 架构设计（How to design） | 基础设施实现（How to deploy & operate） |
| **Concerns** | DDD patterns, API design, component boundaries | CI/CD pipelines, environment configs, monitoring |
| **Artifacts** | Architecture diagrams, design patterns | Deployment scripts, CI workflows, observability configs |
| **Example** | "Use DDD Aggregate pattern for daily reports" | "Deploy backend to Railway, frontend to Vercel" |

### 2.2 Relationship to Dev-Guides Layer

| Aspect | Dev-Guides Layer | Infrastructure Layer |
|--------|-----------------|---------------------|
| **Focus** | 开发规范（How to code） | 部署运维（How to deploy & monitor） |
| **Concerns** | API development flow, testing strategy, code patterns | Environment setup, deployment pipelines, log aggregation |
| **Artifacts** | Coding guidelines, testing checklist | Dockerfiles, CI/CD configs, monitoring dashboards |
| **Example** | "Follow 6-step API development flow" | "Deploy using GitHub Actions → Railway pipeline" |

**Key Distinction**: Dev-Guides focuses on **developer workflows** (coding, testing), Infrastructure focuses on **operational workflows** (deploying, monitoring).

---

## 3. Infrastructure Documents Inventory

本 Infrastructure Layer 包含以下 5 个核心文档 + 1 个 Freeze Manifest：

| Document | Version | Purpose | Status |
|----------|---------|---------|--------|
| [INFRA_OVERVIEW.md](INFRA_OVERVIEW.md) | v1.0 | Infrastructure层总览，定位与职责 | ready_for_production |
| [CI_PIPELINE_SPEC.md](CI_PIPELINE_SPEC.md) | v1.0 | CI流程规范（GitHub Actions） | ready_for_production |
| [DEPLOYMENT_PIPELINE_SPEC.md](DEPLOYMENT_PIPELINE_SPEC.md) | v1.0 | CD流程规范（部署流水线） | ready_for_production |
| [ENVIRONMENT_VARIABLES_GUIDE.md](ENVIRONMENT_VARIABLES_GUIDE.md) | v1.0 | 环境变量管理规范 | ready_for_production |
| [OBSERVABILITY_GUIDE.md](OBSERVABILITY_GUIDE.md) | v1.0 | 可观测性指南（监控、日志、追踪） | ready_for_production |

**Total**: 5 infrastructure specifications + 1 freeze manifest (optional)

---

## 4. Technology Stack

### 4.1 Containerization

- **Docker**: Container runtime for backend services
- **Docker Compose**: Local development orchestration
- **Dockerfile**: Multi-stage builds for production images

### 4.2 CI/CD Pipeline

- **GitHub Actions**: Primary CI/CD automation platform
- **Workflows**:
  - `.github/workflows/ci-backend.yml` - Backend linting, testing, building
  - `.github/workflows/ci-frontend.yml` - Frontend linting, testing, building
  - `.github/workflows/deploy-production.yml` - Production deployment (planned)

### 4.3 Deployment Platforms

#### Backend Deployment
- **Railway**: Primary backend deployment platform (FastAPI + Supabase Edge Functions alternative)
- **Supabase**: Database (PostgreSQL) + Authentication + Storage
- **Migration**: Alembic (for schema migrations)

#### Frontend Deployment
- **Vercel**: Primary frontend deployment platform (Next.js)
- **CDN**: Vercel CDN for static assets
- **SSR**: Server-side rendering for dynamic pages

### 4.4 Monitoring & Observability

#### Current Implementation
- **Railway Logs**: Backend application logs
- **Vercel Logs**: Frontend application logs
- **Supabase Dashboard**: Database metrics and query performance

#### Planned Implementation
- **Metrics**: Prometheus + Grafana (planned for 2026-Q1)
- **Logging**: ELK Stack (Elasticsearch, Logstash, Kibana) (planned)
- **Tracing**: OpenTelemetry + Jaeger (planned)
- **Alerting**: PagerDuty or Slack integration (planned)

### 4.5 Secrets Management

- **GitHub Secrets**: CI/CD environment variables (DATABASE_URL, API keys)
- **Railway Environment Variables**: Production backend secrets
- **Vercel Environment Variables**: Production frontend secrets
- **Supabase Vault**: Database secrets and service role keys

---

## 5. Infrastructure Principles

### 5.1 Infrastructure as Code (IaC)

**Principle**: All infrastructure configurations must be version-controlled and reproducible.

**Implementation**:
- Dockerfiles for container definitions
- `docker-compose.yml` for local development
- GitHub Actions YAML for CI/CD workflows
- Alembic migrations for database schema changes

**Anti-Pattern**:
- ❌ Manual configuration changes via UI dashboards
- ❌ Hardcoded secrets in code repositories
- ❌ Untracked environment variable changes

### 5.2 Immutable Infrastructure

**Principle**: Infrastructure components should be replaced, not modified in place.

**Implementation**:
- Railway deployments create new instances (previous versions retained for rollback)
- Vercel deployments are immutable (each deploy gets a unique URL)
- Docker images are tagged with commit SHAs (never overwrite tags)

**Rollback Strategy**: Revert to previous deployment (not patch current deployment)

### 5.3 Environment Parity

**Principle**: Development, staging, and production environments should be as similar as possible.

**Implementation**:

| Environment | Database | Backend | Frontend | Purpose |
|------------|----------|---------|----------|---------|
| **Development** | Supabase Local | Docker Compose (local) | Next.js dev server (localhost:3000) | Local development |
| **Staging** | Supabase Staging Project | Railway Preview Deploy | Vercel Preview Deploy | Integration testing |
| **Production** | Supabase Production Project | Railway Production | Vercel Production | Live system |

**Parity Checks**:
- ✅ Same PostgreSQL version across all environments (PostgreSQL 15+)
- ✅ Same Node.js version (Node 20 LTS)
- ✅ Same Python version (Python 3.11+)
- ✅ Same dependency versions (lock files: `package-lock.json`, `requirements.txt`)

### 5.4 Security by Default

**Principle**: Security configurations must be enabled by default, not as an afterthought.

**Implementation**:
- ✅ HTTPS only (HTTP automatically redirects to HTTPS)
- ✅ CORS policies defined in backend (`CORS_ORIGINS` environment variable)
- ✅ RLS (Row-Level Security) enabled for all Supabase tables
- ✅ JWT token expiration enforced (15-minute access tokens, 7-day refresh tokens)
- ✅ Secrets stored in environment variables (never committed to Git)
- ✅ Database migrations reviewed before production deployment

**Security Checklist** (see [DEPLOYMENT_PIPELINE_SPEC.md](DEPLOYMENT_PIPELINE_SPEC.md) for details):
- [ ] All environment variables use secure secret management
- [ ] RLS policies tested for all tables
- [ ] JWT secret rotated quarterly
- [ ] Database connection strings use SSL mode
- [ ] API rate limiting configured (planned)

---

## 6. Infrastructure Document Summaries

### 6.1 CI_PIPELINE_SPEC.md

**Purpose**: 定义持续集成（CI）流程规范，确保代码质量门控。

**Key Sections**:
- GitHub Actions workflow定义（linting, testing, building）
- Quality gates（test coverage ≥ 80%, linting errors = 0, type errors = 0）
- Security scanning（Snyk, Trivy）
- Artifact generation（Docker images, build artifacts）

**Related Dev-Guide**: [TESTING_STRATEGY.md](../3.dev-guides/TESTING_STRATEGY.md)

### 6.2 DEPLOYMENT_PIPELINE_SPEC.md

**Purpose**: 定义持续部署（CD）流程规范，确保零停机部署。

**Key Sections**:
- Backend deployment flow（Railway deployment, database migrations, health checks）
- Frontend deployment flow（Vercel deployment, CDN invalidation）
- Zero-downtime deployment strategies（rolling updates, blue-green deployments）
- Rollback procedures（Railway rollback, Vercel rollback, database migration rollback）

**Related Dev-Guide**: [DEPLOYMENT_GUIDE.md](../3.dev-guides/DEPLOYMENT_GUIDE.md)

### 6.3 ENVIRONMENT_VARIABLES_GUIDE.md

**Purpose**: 定义环境变量管理规范，确保配置安全性和一致性。

**Key Sections**:
- Environment variable naming conventions（`DATABASE_URL`, `NEXT_PUBLIC_*`）
- Secrets management strategy（GitHub Secrets, Railway, Vercel）
- Environment-specific configurations（dev, staging, production）
- Security best practices（never commit `.env` files, rotate secrets quarterly）

**Related Dev-Guide**: [DEPLOYMENT_GUIDE.md](../3.dev-guides/DEPLOYMENT_GUIDE.md)

### 6.4 OBSERVABILITY_GUIDE.md

**Purpose**: 定义可观测性指南，确保系统健康监控和故障诊断。

**Key Sections**:
- Observability三大支柱（Metrics, Logs, Traces）
- Current implementation（Railway logs, Vercel logs, Supabase dashboard）
- Future roadmap（Prometheus + Grafana, ELK Stack, OpenTelemetry）
- Health checks（`GET /health` endpoint, database connection checks）
- Alerting（planned: error rate > 5%, p99 latency > 2s）

**Related Dev-Guide**: [TROUBLESHOOTING.md](../3.dev-guides/TROUBLESHOOTING.md)

---

## 7. Traceability to Other Layers

### 7.1 References to SoT Layer (Layer 2)

Infrastructure configurations must respect SoT definitions:

| SoT Document | Infrastructure Impact | Example |
|--------------|----------------------|---------|
| [DATA_SCHEMA.md](../2.sot/DATA_SCHEMA.md) v5.2 | Database migrations (Alembic) must align with schema definitions | Migration scripts for `daily_reports`, `ledger_entries` tables |
| [STATE_MACHINE.md](../2.sot/STATE_MACHINE.md) v2.6 | Health checks must verify valid state transitions | Alert if daily report stuck in `trend_pending` for > 24h |
| [API_SOT.md](../2.sot/API_SOT.md) v9.0 | API endpoint monitoring and health checks | Monitor `/api/v1/daily-reports` response times |
| [ERROR_CODES_SOT.md](../2.sot/ERROR_CODES_SOT.md) v2.1 | Error log aggregation and alerting | Alert on `AUTH-003` (Invalid Token) spike |

### 7.2 References to Dev-Guides Layer (Layer 3)

Infrastructure enables Dev-Guides workflows:

| Dev-Guide Document | Infrastructure Implementation | Link |
|--------------------|------------------------------|------|
| [API_DEVELOPMENT_FLOW.md](../3.dev-guides/API_DEVELOPMENT_FLOW.md) | CI pipeline runs API tests before deployment | [CI_PIPELINE_SPEC.md](CI_PIPELINE_SPEC.md) |
| [TESTING_STRATEGY.md](../3.dev-guides/TESTING_STRATEGY.md) | CI pipeline enforces coverage thresholds (80%+ unit, 70%+ integration) | [CI_PIPELINE_SPEC.md](CI_PIPELINE_SPEC.md) |
| [DEPLOYMENT_GUIDE.md](../3.dev-guides/DEPLOYMENT_GUIDE.md) | CD pipeline automates deployment steps | [DEPLOYMENT_PIPELINE_SPEC.md](DEPLOYMENT_PIPELINE_SPEC.md) |
| [TROUBLESHOOTING.md](../3.dev-guides/TROUBLESHOOTING.md) | Observability tools provide logs and metrics for debugging | [OBSERVABILITY_GUIDE.md](OBSERVABILITY_GUIDE.md) |

### 7.3 References to Architecture Layer (Layer 4)

Infrastructure realizes architectural designs:

| Architecture Concern | Infrastructure Implementation | Link |
|---------------------|------------------------------|------|
| DDD Aggregate boundaries | Separate microservices in Railway (future) | [DEPLOYMENT_PIPELINE_SPEC.md](DEPLOYMENT_PIPELINE_SPEC.md) |
| API Gateway pattern | Vercel Edge Functions as API gateway (planned) | [DEPLOYMENT_PIPELINE_SPEC.md](DEPLOYMENT_PIPELINE_SPEC.md) |
| Database sharding | Supabase connection pooling and read replicas (planned) | [ENVIRONMENT_VARIABLES_GUIDE.md](ENVIRONMENT_VARIABLES_GUIDE.md) |
| CQRS separation | Separate read/write database connections (future) | [OBSERVABILITY_GUIDE.md](OBSERVABILITY_GUIDE.md) |

---

## 8. Governance and Maintenance

### 8.1 Change Management

**RFC Requirement**: Infrastructure changes affecting production require RFC approval.

**Examples Requiring RFC**:
- ❌ Changing deployment platform (Railway → AWS)
- ❌ Modifying CI quality gates (coverage threshold 80% → 60%)
- ❌ Adding new monitoring tools (Prometheus + Grafana)
- ❌ Changing database migration strategy (Alembic → Prisma Migrate)

**Examples NOT Requiring RFC** (routine maintenance):
- ✅ Updating GitHub Actions versions (e.g., `actions/setup-node@v3` → `v4`)
- ✅ Rotating secrets (quarterly secret rotation)
- ✅ Adjusting log retention periods (30 days → 60 days)
- ✅ Updating health check endpoints (add new endpoint)

### 8.2 Maintenance Schedule

| Frequency | Task | Owner | Document Reference |
|-----------|------|-------|-------------------|
| **Weekly** | Review CI/CD pipeline failures | DevOps | [CI_PIPELINE_SPEC.md](CI_PIPELINE_SPEC.md) |
| **Monthly** | Audit environment variables | DevOps | [ENVIRONMENT_VARIABLES_GUIDE.md](ENVIRONMENT_VARIABLES_GUIDE.md) |
| **Quarterly** | Rotate secrets (JWT, API keys) | Security | [ENVIRONMENT_VARIABLES_GUIDE.md](ENVIRONMENT_VARIABLES_GUIDE.md) |
| **Quarterly** | Review and update monitoring dashboards | DevOps | [OBSERVABILITY_GUIDE.md](OBSERVABILITY_GUIDE.md) |
| **Semi-Annual** | Infrastructure security audit | Security | All infrastructure docs |

### 8.3 Health Score Monitoring

**Infrastructure Health Score** = Weighted average of:
- CI/CD pipeline success rate (40%)
- Deployment success rate (30%)
- System uptime (20%)
- Security compliance (10%)

**Target**: ≥ 95% health score
**Alert Threshold**: < 90% health score triggers investigation

---

## 9. Future Roadmap

### 9.1 Short-Term (2026-Q1)

- [ ] Complete Prometheus + Grafana setup (metrics collection)
- [ ] Implement ELK Stack (centralized logging)
- [ ] Configure PagerDuty alerting (error rate, latency spikes)
- [ ] Add API rate limiting (Redis + FastAPI limiter)

### 9.2 Medium-Term (2026-Q2)

- [ ] Implement OpenTelemetry distributed tracing
- [ ] Add Jaeger for trace visualization
- [ ] Configure blue-green deployment for Railway
- [ ] Implement automated security scanning (OWASP ZAP)

### 9.3 Long-Term (2026-H2)

- [ ] Migrate to Kubernetes (if scale requires)
- [ ] Implement multi-region deployment (CDN + database replicas)
- [ ] Add chaos engineering tests (Chaos Monkey)
- [ ] Implement Infrastructure as Code with Terraform (if needed)

---

## 10. Conclusion

The Infrastructure Layer serves as the operational foundation for the AI 广告代投系统, ensuring that:

1. **Code Quality**: CI pipelines enforce quality gates before deployment
2. **Deployment Reliability**: CD pipelines enable zero-downtime deployments
3. **Security**: Secrets management and environment variable controls prevent leaks
4. **Observability**: Monitoring and logging enable proactive issue detection
5. **Traceability**: Clear links to SoT, Dev-Guides, and Architecture layers

All infrastructure changes must align with this document and the 5 core infrastructure specifications.

---

**Document Version**: v1.0
**Last Updated**: 2025-11-27
**Baseline**: MASTER.md v4.4, SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0
