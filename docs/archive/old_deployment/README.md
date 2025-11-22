# 部署指南

## 📌 概述

本目录包含AI广告代投系统的部署文档，涵盖各种部署方案和运维管理。

## 📂 文档结构

```
deployment/
├── README.md              # 部署指南索引（本文件）
├── docker.md             # Docker部署
├── kubernetes.md         # Kubernetes部署
├── monitoring.md         # 监控配置
├── backup.md            # 备份恢复
├── security.md          # 安全配置
└── troubleshooting.md   # 故障排查
```

## 🚀 部署方案

### 开发环境
适用于本地开发和测试

```bash
# 使用docker-compose快速启动
docker-compose -f docker-compose.dev.yml up -d
```

### 测试环境
适用于功能测试和集成测试

```bash
# 使用测试配置部署
docker-compose -f docker-compose.test.yml up -d
```

### 生产环境
适用于正式运行环境

```bash
# 使用Kubernetes部署
kubectl apply -f k8s/
```

## 🐳 Docker部署

### 构建镜像
```bash
# 构建后端镜像
docker build -t ai-ad-spend-backend:latest -f backend/Dockerfile .

# 构建前端镜像
docker build -t ai-ad-spend-frontend:latest -f frontend/Dockerfile .
```

### 运行容器
```bash
# 启动数据库
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15

# 启动Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine

# 启动后端
docker run -d \
  --name backend \
  -e DATABASE_URL=postgresql://... \
  -p 8000:8000 \
  ai-ad-spend-backend:latest

# 启动前端
docker run -d \
  --name frontend \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 \
  -p 3000:3000 \
  ai-ad-spend-frontend:latest
```

## ☸️ Kubernetes部署

### 前置要求
- Kubernetes 1.24+
- kubectl配置完成
- Helm 3+ (可选)

### 部署步骤
```bash
# 创建命名空间
kubectl create namespace ai-ad-spend

# 部署配置
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# 部署数据库
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/redis/

# 部署应用
kubectl apply -f k8s/backend/
kubectl apply -f k8s/frontend/

# 配置Ingress
kubectl apply -f k8s/ingress.yaml
```

### Helm部署
```bash
# 添加Helm仓库
helm repo add ai-ad-spend https://charts.ai-ad-spend.com
helm repo update

# 安装
helm install ai-ad-spend ai-ad-spend/ai-ad-spend \
  --namespace ai-ad-spend \
  --create-namespace \
  --values values.yaml
```

## 📊 监控配置

### Prometheus监控
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'ai-ad-spend-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
```

### Grafana仪表盘
1. 导入仪表盘模板 (ID: 12345)
2. 配置数据源为Prometheus
3. 设置告警规则

### 日志收集
```yaml
# filebeat.yml
filebeat.inputs:
  - type: container
    paths:
      - '/var/lib/docker/containers/*/*.log'
    processors:
      - add_kubernetes_metadata:
          in_cluster: true
```

## 🔧 运维管理

### 健康检查
```bash
# 检查服务状态
curl http://localhost:8000/health
curl http://localhost:3000/api/health

# K8s健康检查
kubectl get pods -n ai-ad-spend
kubectl describe pod <pod-name> -n ai-ad-spend
```

### 扩缩容
```bash
# 手动扩容
kubectl scale deployment backend --replicas=3 -n ai-ad-spend

# 自动扩容
kubectl autoscale deployment backend \
  --min=2 --max=10 --cpu-percent=80 \
  -n ai-ad-spend
```

### 滚动更新
```bash
# 更新镜像
kubectl set image deployment/backend \
  backend=ai-ad-spend-backend:v2.0 \
  -n ai-ad-spend

# 查看更新状态
kubectl rollout status deployment/backend -n ai-ad-spend

# 回滚
kubectl rollout undo deployment/backend -n ai-ad-spend
```

## 💾 备份策略

### 数据库备份
```bash
# 手动备份
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# 定时备份 (crontab)
0 2 * * * /scripts/backup.sh
```

### 文件备份
```bash
# 备份上传文件
tar -czf uploads_$(date +%Y%m%d).tar.gz /app/uploads/

# 备份配置文件
tar -czf configs_$(date +%Y%m%d).tar.gz /app/configs/
```

## 🔒 安全配置

### SSL/TLS配置
```nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
}
```

### 防火墙规则
```bash
# 只允许必要端口
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw enable
```

## 🚨 故障处理

### 常见问题

#### 数据库连接失败
```bash
# 检查数据库状态
docker ps | grep postgres
docker logs postgres

# 检查连接配置
echo $DATABASE_URL
```

#### 服务启动失败
```bash
# 查看日志
docker logs backend
kubectl logs -f pod/backend-xxx -n ai-ad-spend

# 检查配置
docker exec backend env | grep -E "DATABASE|REDIS"
```

#### 性能问题
```bash
# 检查资源使用
docker stats
kubectl top nodes
kubectl top pods -n ai-ad-spend

# 检查慢查询
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
```

## 📈 性能优化

### 数据库优化
- 创建适当的索引
- 配置连接池
- 启用查询缓存
- 定期VACUUM和ANALYZE

### 应用优化
- 启用Gzip压缩
- 配置CDN
- 使用Redis缓存
- 启用HTTP/2

### 容器优化
- 使用多阶段构建
- 最小化镜像大小
- 配置资源限制
- 使用健康检查

## 📝 检查清单

### 部署前检查
- [ ] 环境变量配置完整
- [ ] 数据库迁移已执行
- [ ] SSL证书已配置
- [ ] 备份策略已设置
- [ ] 监控告警已配置

### 部署后验证
- [ ] 所有服务正常启动
- [ ] 健康检查通过
- [ ] 日志正常输出
- [ ] 监控数据正常
- [ ] 功能测试通过

## 📞 支持联系

- **运维团队**: ops@ai-ad-spend.com
- **紧急热线**: +86-xxx-xxxx-xxxx
- **文档更新**: 提交PR到 [GitHub](https://github.com/wade56754/AI_ad_spend02)

---

*最后更新: 2024-11-18*