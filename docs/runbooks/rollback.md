# 回滚手册

> **版本**: v1.0
> **最后更新**: 2025-12-27
> **负责人**: DevOps

---

## 1. 回滚触发条件

### 1.1 必须立即回滚

| 情况 | 判断标准 | 响应时间 |
|------|---------|---------|
| P0故障 | 核心功能不可用 | < 5分钟 |
| 数据错误 | 财务数据计算错误 | < 10分钟 |
| 安全漏洞 | 数据泄露风险 | < 5分钟 |

### 1.2 评估后回滚

| 情况 | 判断标准 | 响应时间 |
|------|---------|---------|
| 性能下降 | p99 > 500ms持续10分钟 | < 30分钟 |
| 错误率上升 | 错误率 > 1%持续5分钟 | < 15分钟 |
| 用户投诉 | 多用户反馈同一问题 | < 30分钟 |

---

## 2. 回滚类型

### 2.1 代码回滚（最常用）

```bash
# 找到回滚点
git tag | grep pre-deploy | tail -5

# 回滚到指定版本
git checkout pre-deploy-20251227-143022

# 强制推送（需要权限）
git push -f origin main

# 或者通过revert（更安全）
git revert HEAD~3..HEAD
git push origin main
```

### 2.2 数据库回滚

```bash
# 查看当前版本
cd backend && alembic current

# 回滚一步
alembic downgrade -1

# 回滚到指定版本
alembic downgrade abc123

# 验证回滚
alembic current
```

### 2.3 Kubernetes回滚

```bash
# 查看历史版本
kubectl rollout history deployment/backend

# 回滚到上一版本
kubectl rollout undo deployment/backend

# 回滚到指定版本
kubectl rollout undo deployment/backend --to-revision=3

# 验证回滚
kubectl rollout status deployment/backend
```

### 2.4 Vercel回滚（前端）

```bash
# 通过Vercel CLI
vercel rollback

# 或通过Dashboard
# 1. 打开 https://vercel.com/xxx/ai-ad-frontend
# 2. 找到上一个成功部署
# 3. 点击 "Promote to Production"
```

---

## 3. 回滚流程

### 3.1 紧急回滚流程（P0）

```
发现问题 (0分钟)
    │
    ▼
通知团队 (1分钟)
    │ 飞书群/电话
    ▼
确认回滚 (2分钟)
    │ 主责人确认
    ▼
执行回滚 (5分钟)
    │ 代码+数据库+K8s
    ▼
验证回滚 (8分钟)
    │ 健康检查+功能测试
    ▼
通知恢复 (10分钟)
    │ 飞书群通知
    ▼
事后复盘 (24小时内)
```

### 3.2 标准回滚流程

```bash
#!/bin/bash
# scripts/rollback.sh

echo "=== 开始回滚 ==="

# 1. 记录当前状态
echo "当前Git版本: $(git rev-parse HEAD)"
echo "当前DB版本: $(cd backend && alembic current)"

# 2. 回滚代码
echo "回滚代码..."
git checkout $1  # $1 是回滚目标tag

# 3. 回滚数据库（如果需要）
read -p "是否需要回滚数据库? (y/n) " db_rollback
if [ "$db_rollback" == "y" ]; then
    echo "回滚数据库..."
    cd backend && alembic downgrade -1
fi

# 4. 重新部署
echo "重新部署..."
# docker build ... 或 kubectl rollout undo ...

# 5. 验证
echo "验证回滚..."
curl -s https://api.example.com/health

echo "=== 回滚完成 ==="
```

---

## 4. 回滚后检查清单

### 4.1 必须检查

- [ ] 健康检查通过 `curl /health`
- [ ] 登录功能正常
- [ ] 核心API正常（日报/项目/账户）
- [ ] 数据库连接正常
- [ ] 错误率恢复正常

### 4.2 可选检查

- [ ] 性能指标恢复
- [ ] 监控告警消除
- [ ] 用户反馈确认

---

## 5. 回滚记录模板

```markdown
## 回滚记录: YYYY-MM-DD

### 基本信息
- **触发原因**: [P0故障/性能问题/数据错误]
- **发现时间**: HH:MM
- **回滚开始**: HH:MM
- **回滚完成**: HH:MM
- **影响时长**: XX分钟
- **执行人**: @xxx

### 回滚版本
- **回滚前**: Git abc1234, DB revision xyz789
- **回滚后**: Git def5678, DB revision uvw456

### 影响范围
- 受影响用户: XX人
- 受影响功能: [功能列表]
- 数据影响: [有/无]

### 根因分析
[简述问题原因]

### 后续行动
- [ ] 修复问题
- [ ] 添加测试用例
- [ ] 更新部署检查清单
- [ ] 团队复盘
```

---

## 6. 特殊场景

### 6.1 数据库迁移不可回滚

如果迁移涉及数据删除，无法自动回滚：

1. 检查 `migrations/EXEMPTIONS.md` 是否有说明
2. 使用备份数据恢复
3. 联系DBA手动处理

```bash
# 从备份恢复（示例）
pg_restore -d ai_ad_prod backup_20251227.dump
```

### 6.2 多服务回滚

如果涉及多个服务：

```bash
# 按依赖顺序回滚
kubectl rollout undo deployment/frontend
kubectl rollout undo deployment/backend
kubectl rollout undo deployment/worker
```

### 6.3 灰度回滚

如果使用灰度发布：

```bash
# 将流量全部切回旧版本
kubectl patch virtualservice ai-ad -p '{"spec":{"http":[{"route":[{"destination":{"host":"backend","subset":"stable"},"weight":100}]}]}}'
```

---

## 7. 联系人

| 角色 | 姓名 | 电话 | 飞书 |
|------|------|------|------|
| 值班 | - | - | @oncall |
| 后端 | @xxx | 138xxxx | @xxx |
| 前端 | @yyy | 139xxxx | @yyy |
| DBA | @zzz | 137xxxx | @zzz |
| 老板 | @aaa | 136xxxx | @aaa |

---

## 8. 复盘模板

每次回滚后24小时内完成复盘：

```markdown
## 回滚复盘: YYYY-MM-DD

### 事件时间线
- HH:MM 发现问题
- HH:MM 确认回滚
- HH:MM 执行回滚
- HH:MM 验证恢复

### 5 Whys分析
1. Why: 为什么出现问题？
2. Why: 为什么没有测试发现？
3. Why: 为什么监控没有提前告警？
4. Why: ...
5. Why: ...

### 改进措施
- [ ] 短期：修复bug
- [ ] 中期：增加测试用例
- [ ] 长期：改进部署流程

### 经验教训
[总结]
```
