# 部署手册

> **版本**: v1.0
> **最后更新**: 2025-12-27
> **负责人**: DevOps

---

## 1. 部署前检查清单

### 1.1 代码检查
```bash
# 确认在正确分支
git branch --show-current  # 应该是 main 或 release/*

# 确认代码最新
git pull origin main

# 确认测试通过
just ci-check
```

### 1.2 数据库检查
```bash
# 检查是否有未应用的迁移
cd backend && alembic history

# 检查迁移可回滚性
python scripts/check_migration.py
```

### 1.3 环境检查
```bash
# 检查环境变量
cat .env | grep -E "^(DATABASE|SUPABASE|JWT)"

# 检查服务连通性
curl -s https://api.example.com/health
```

---

## 2. 部署流程

### 2.1 标记回滚点
```bash
# 创建部署前标签
git tag pre-deploy-$(date +%Y%m%d-%H%M%S)
git push origin --tags

# 记录当前数据库版本
alembic current > deploy_checkpoint.txt
```

### 2.2 数据库迁移
```bash
# 应用迁移
cd backend
alembic upgrade head

# 验证迁移成功
alembic current
```

### 2.3 部署后端
```bash
# Docker部署
docker build -t ai-ad-backend:$(git rev-parse --short HEAD) .
docker push registry.example.com/ai-ad-backend:$(git rev-parse --short HEAD)

# 或 Kubernetes
kubectl set image deployment/backend backend=registry.example.com/ai-ad-backend:$(git rev-parse --short HEAD)
kubectl rollout status deployment/backend
```

### 2.4 部署前端
```bash
# Vercel部署（自动）
git push origin main

# 或手动
cd frontend
npm run build
vercel --prod
```

### 2.5 验证部署
```bash
# 健康检查
curl -s https://api.example.com/health | jq .

# API测试
curl -s https://api.example.com/api/v1/users/me -H "Authorization: Bearer $TOKEN"

# 前端检查
curl -s https://app.example.com | head -20
```

---

## 3. 部署后监控

### 3.1 关键指标（部署后30分钟内观察）

| 指标 | 正常范围 | 告警阈值 |
|------|---------|---------|
| API响应时间p99 | < 200ms | > 500ms |
| 错误率 | < 0.1% | > 1% |
| CPU使用率 | < 50% | > 80% |
| 内存使用率 | < 60% | > 85% |

### 3.2 监控命令
```bash
# 查看日志
kubectl logs -f deployment/backend --tail=100

# 查看错误
kubectl logs deployment/backend | grep ERROR | tail -20

# 查看指标
curl -s http://localhost:9090/metrics | grep http_request
```

### 3.3 监控链接
- Grafana: https://grafana.example.com/d/xxx
- Sentry: https://sentry.example.com/xxx
- Logs: https://logs.example.com/xxx

---

## 4. 紧急回滚

如果部署后发现问题，立即执行回滚：

```bash
# 1. 回滚代码
git checkout pre-deploy-YYYYMMDD-HHMMSS
git push -f origin main

# 2. 回滚数据库（如果需要）
cd backend
alembic downgrade -1

# 3. 回滚Kubernetes
kubectl rollout undo deployment/backend

# 4. 验证回滚
curl -s https://api.example.com/health
```

详见 [回滚手册](./rollback.md)

---

## 5. 部署记录模板

每次部署后填写：

```markdown
## 部署记录: YYYY-MM-DD

- **版本**: vX.X.X
- **Git Commit**: abc1234
- **部署人**: @xxx
- **开始时间**: HH:MM
- **完成时间**: HH:MM
- **状态**: ✅ 成功 / ❌ 回滚

### 变更内容
- 变更1
- 变更2

### 部署后验证
- [ ] 健康检查通过
- [ ] API测试通过
- [ ] 监控正常

### 问题记录
（如有）
```

---

## 6. 联系人

| 角色 | 姓名 | 联系方式 |
|------|------|---------|
| 主责 | @xxx | 手机/飞书 |
| 备份 | @yyy | 手机/飞书 |
| DBA | @zzz | 手机/飞书 |
