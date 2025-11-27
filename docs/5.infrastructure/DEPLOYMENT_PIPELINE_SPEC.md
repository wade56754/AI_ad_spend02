---
version: v1.0
status: ready_for_production
layer: infrastructure
owner: wade
last_reviewed: 2025-11-27
baseline: MASTER.md v3.4, SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0
---

# Deployment Pipeline Specification

## 1. Purpose

定义持续部署（CD）流程规范，确保代码从CI验证通过后能够安全、可靠、零停机地部署到生产环境。

## 2. Deployment Targets

| Environment | Backend | Frontend | Database | Purpose |
|------------|---------|----------|----------|---------|
| **Development** | Docker Compose (local) | Next.js dev server (localhost:3000) | Supabase Local | Local development |
| **Staging** | Railway Preview Deploy | Vercel Preview Deploy | Supabase Staging Project | Integration testing |
| **Production** | Railway Production | Vercel Production | Supabase Production Project | Live system |

---

## 3. Backend Deployment Flow (Railway)

### 3.1 Deployment Steps

```
Git Push → GitHub Actions CI ✅ → Build Docker Image → Push to GHCR
                                           ↓
                                  Railway Webhook Trigger
                                           ↓
                                  Railway Pull Image from GHCR
                                           ↓
                                  Run Database Migrations (Alembic)
                                           ↓
                                  Deploy New Container (Rolling Update)
                                           ↓
                                  Health Check (GET /health)
                                           ↓
                                  ✅ Success / ❌ Rollback
```

### 3.2 Database Migration Strategy

**Alembic Migration Execution**:

```bash
# Railway deployment script
#!/bin/bash
set -e

# Step 1: Run database migrations
alembic upgrade head

# Step 2: Start FastAPI application
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Zero-Downtime Migration Principles**:
1. **Backward Compatible Migrations**: New schema must support old code
2. **Two-Phase Deployment**:
   - Phase 1: Deploy schema changes (add columns, not drop)
   - Phase 2: Deploy code changes (use new columns)
   - Phase 3: Drop old columns (after verification)

**Example** (Add `conversions_final_v2` column):
```python
# Migration 1: Add new column (nullable)
def upgrade():
    op.add_column('daily_reports', sa.Column('conversions_final_v2', sa.Integer(), nullable=True))

# Deploy code to use conversions_final_v2

# Migration 2: Backfill data + make column non-nullable
def upgrade():
    op.execute("UPDATE daily_reports SET conversions_final_v2 = conversions_final WHERE conversions_final_v2 IS NULL")
    op.alter_column('daily_reports', 'conversions_final_v2', nullable=False)

# Migration 3: Drop old column (after verification)
def upgrade():
    op.drop_column('daily_reports', 'conversions_final')
```

### 3.3 Health Checks

**Endpoint**: `GET /health`

**Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.2.3",
  "uptime": 3600
}
```

**Health Check Criteria**:
- ✅ HTTP 200 response
- ✅ Database connection successful
- ✅ Response time < 500ms

**Failure Handling**:
- ❌ Health check fails → Railway keeps old container running
- ❌ Retry 3 times (30s interval) → Rollback to previous deployment

---

## 4. Frontend Deployment Flow (Vercel)

### 4.1 Deployment Steps

```
Git Push → GitHub Actions CI ✅ → Vercel Webhook Trigger
                                           ↓
                                  Vercel Build (next build)
                                           ↓
                                  Generate Static Pages
                                           ↓
                                  Deploy to CDN
                                           ↓
                                  Invalidate Old CDN Cache
                                           ↓
                                  ✅ Success (Deployment URL)
```

### 4.2 Environment Variable Injection

**Vercel Environment Variables**:
- `NEXT_PUBLIC_API_URL` - Backend API URL (e.g., `https://api.ai-ad-spend.com`)
- `NEXT_PUBLIC_SUPABASE_URL` - Supabase project URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` - Supabase anonymous key (public)

**Injection Method**:
```bash
# Vercel CLI deployment (manual)
vercel --prod \
  -e NEXT_PUBLIC_API_URL=https://api.ai-ad-spend.com \
  -e NEXT_PUBLIC_SUPABASE_URL=https://<project>.supabase.co \
  -e NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key>

# Vercel Dashboard (automatic)
# Set environment variables in Vercel Dashboard → Settings → Environment Variables
```

### 4.3 CDN Cache Invalidation

**Vercel Automatic Invalidation**:
- Every deployment invalidates old CDN cache
- New deployment gets unique URL (e.g., `https://<deployment-id>.vercel.app`)
- Production domain (`https://ai-ad-spend.com`) points to latest deployment

**Manual Invalidation** (if needed):
```bash
# Purge CDN cache via Vercel API
curl -X POST "https://api.vercel.com/v1/projects/<project-id>/purge" \
  -H "Authorization: Bearer <vercel-token>"
```

---

## 5. Deployment Strategies

### 5.1 Rolling Update (Default)

**Railway Backend**:
- Deploy new container alongside old container
- Gradually shift traffic from old → new (10% → 50% → 100%)
- Old container terminates after health checks pass

**Advantage**: Zero downtime
**Disadvantage**: Brief period with mixed versions

### 5.2 Blue-Green Deployment (Planned)

**Concept**:
- **Blue**: Current production environment
- **Green**: New deployment environment
- Switch traffic from Blue → Green instantly
- Keep Blue as rollback target

**Implementation** (Railway + Vercel):
```bash
# Deploy to Green environment
railway up --environment green

# Switch traffic (update DNS or load balancer)
railway promote green --to production

# Verify Green environment
curl https://api.ai-ad-spend.com/health

# Rollback if issues (switch back to Blue)
railway promote blue --to production
```

### 5.3 Canary Deployment (Future)

**Concept**:
- Deploy to 5% of users first
- Monitor error rates and latency
- Gradually increase to 100% if no issues

**Implementation** (requires advanced routing):
- Use Railway's traffic splitting feature (planned)
- Monitor metrics: error rate, p99 latency, user feedback

---

## 6. Rollback Procedures

### 6.1 Railway Backend Rollback

**Method 1: Railway Dashboard**
1. Navigate to Railway Dashboard → Deployments
2. Click on previous successful deployment
3. Click "Redeploy" button
4. Health checks run → old version restored

**Method 2: Railway CLI**
```bash
# List recent deployments
railway logs --deployment <deployment-id>

# Rollback to specific deployment
railway rollback <deployment-id>
```

**Rollback Time**: < 2 minutes

### 6.2 Vercel Frontend Rollback

**Method 1: Vercel Dashboard**
1. Navigate to Vercel Dashboard → Deployments
2. Click on previous successful deployment
3. Click "Promote to Production" button
4. CDN cache invalidated → old version restored

**Method 2: Vercel CLI**
```bash
# List recent deployments
vercel ls

# Rollback to specific deployment
vercel alias set <deployment-url> ai-ad-spend.com
```

**Rollback Time**: < 1 minute (instant CDN switch)

### 6.3 Database Migration Rollback

**Alembic Downgrade**:
```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision-id>
```

**Caution**:
- ⚠️ Database rollback may cause data loss (if new columns dropped)
- ⚠️ Always backup database before migration
- ✅ Test rollback procedure in staging environment first

**Best Practice**: Design migrations as **forward-only** (avoid downgrades)

---

## 7. Deployment Checklist

### 7.1 Pre-Deployment Checklist

- [ ] CI pipeline passed (all quality gates ✅)
- [ ] Database migrations tested in staging environment
- [ ] Environment variables updated in Railway/Vercel (if needed)
- [ ] Rollback plan documented
- [ ] Monitoring dashboards ready (Railway logs, Vercel logs)
- [ ] Stakeholders notified (if major release)

### 7.2 Post-Deployment Checklist

- [ ] Health checks passing (`GET /health` returns 200)
- [ ] Smoke tests passed (login, create topup, view daily reports)
- [ ] Error rate normal (< 1% 5xx errors)
- [ ] Performance metrics normal (p99 latency < 2s)
- [ ] No user-reported issues (check support channels)

---

## 8. Deployment Frequency

| Environment | Frequency | Trigger |
|------------|-----------|---------|
| **Development** | On every commit to `develop` | Automatic (Vercel/Railway preview) |
| **Staging** | On every PR to `main` | Automatic (Vercel/Railway preview) |
| **Production** | On merge to `main` | Automatic (after CI passes) |

**Target**: Daily production deployments (continuous delivery)

---

## 9. Traceability

### 9.1 References to Dev-Guides Layer

| Dev-Guide Document | Deployment Implementation |
|--------------------|--------------------------|
| [DEPLOYMENT_GUIDE.md](../3.dev-guides/DEPLOYMENT_GUIDE.md) | Detailed manual deployment steps (this document automates them) |
| [TESTING_STRATEGY.md](../3.dev-guides/TESTING_STRATEGY.md) | Integration tests run before deployment |

### 9.2 References to SoT Layer

| SoT Document | Deployment Validation |
|--------------|----------------------|
| [DATA_SCHEMA.md](../2.sot/DATA_SCHEMA.md) v5.2 | Database migrations align with schema definitions |
| [API_SOT.md](../2.sot/API_SOT.md) v9.0 | Health check endpoint defined in API_SOT |

---

## 10. Future Enhancements

### 10.1 Planned Improvements (2026-Q1)

- [ ] Implement blue-green deployment (Railway + Vercel)
- [ ] Add canary deployment (5% → 50% → 100%)
- [ ] Automate smoke tests post-deployment (Playwright E2E tests)
- [ ] Add deployment approval workflow (manual approval for production)

### 10.2 Long-Term Goals (2026-H2)

- [ ] Implement feature flags (LaunchDarkly or custom)
- [ ] Add A/B testing infrastructure (split traffic by feature)
- [ ] Implement progressive delivery (gradual rollout by user segment)

---

**Document Version**: v1.0
**Last Updated**: 2025-11-27
**Baseline**: MASTER.md v3.4, SoT Freeze v2.6, Dev-Guides Freeze vFinal, Architecture Freeze v1.0
