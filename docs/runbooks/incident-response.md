# 事件响应手册

> **版本**: v1.0
> **最后更新**: 2025-12-27
> **负责人**: DevOps

---

## 1. 事件分级

| 级别 | 定义 | 响应时间 | 示例 |
|:----:|------|:--------:|------|
| P0 | 核心功能不可用 | < 15分钟 | 系统完全宕机、数据丢失 |
| P1 | 主要功能受损 | < 30分钟 | 登录失败、日报无法提交 |
| P2 | 次要功能异常 | < 2小时 | 报表加载慢、部分页面错误 |
| P3 | 体验问题 | < 24小时 | UI显示异常、非阻塞Bug |

---

## 2. P0 事件响应流程

```
发现问题 (T+0)
    │
    ▼
确认P0级别 (T+2分钟)
    │ 核心功能完全不可用？
    ▼
通知团队 (T+5分钟)
    │ 飞书群/电话/短信
    ▼
组建War Room (T+10分钟)
    │ 拉响应群，指定IC
    ▼
初步诊断 (T+15分钟)
    │ 日志/监控/最近变更
    ▼
决策：回滚 or 修复 (T+20分钟)
    │
    ├─ 回滚 → 见 rollback.md
    │
    └─ 修复 → hotfix流程
         │
         ▼
    验证恢复 (T+30分钟)
         │
         ▼
    通知恢复 (T+35分钟)
         │
         ▼
    事后复盘 (24小时内)
```

---

## 3. 角色与职责

### 3.1 Incident Commander (IC)

- **职责**: 统筹协调，最终决策
- **人选**: 值班工程师 → Tech Lead → CTO
- **权限**: 可决定回滚、可召集任何人

### 3.2 响应团队

| 角色 | 职责 | 联系人 |
|------|------|-------|
| IC | 统筹协调 | 值班表 |
| 后端 | 服务端问题 | @xxx |
| 前端 | 页面问题 | @yyy |
| DBA | 数据库问题 | @zzz |
| 老板 | P0必须通知 | @aaa |

---

## 4. 诊断检查清单

### 4.1 快速检查（5分钟内）

```bash
# 1. 服务健康
curl -s https://api.example.com/health | jq .

# 2. 最近部署
git log --oneline -5

# 3. 错误日志
kubectl logs deployment/backend --tail=50 | grep -i error

# 4. 数据库连接
psql -c "SELECT 1;"

# 5. 外部依赖
curl -s https://api.supabase.co/health
```

### 4.2 深入检查

| 方向 | 检查命令 | 异常表现 |
|------|---------|---------|
| CPU | `kubectl top pods` | > 80% |
| 内存 | `kubectl top pods` | > 85% |
| 磁盘 | `df -h` | > 90% |
| 连接数 | `netstat -an \| wc -l` | > 1000 |
| 慢查询 | `pg_stat_activity` | > 30s |

---

## 5. 常见问题处理

### 5.1 数据库连接耗尽

**症状**: API超时，日志显示 "connection refused"

**处理**:
```bash
# 1. 查看连接数
psql -c "SELECT count(*) FROM pg_stat_activity;"

# 2. 杀死空闲连接
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '5 minutes';"

# 3. 重启应用（释放连接）
kubectl rollout restart deployment/backend
```

### 5.2 内存溢出

**症状**: 服务频繁重启，OOMKilled

**处理**:
```bash
# 1. 查看资源使用
kubectl top pods

# 2. 临时增加内存限制
kubectl patch deployment backend -p '{"spec":{"template":{"spec":{"containers":[{"name":"backend","resources":{"limits":{"memory":"2Gi"}}}]}}}}'

# 3. 排查内存泄漏
# 查看最近代码变更
```

### 5.3 第三方服务故障

**症状**: 部分功能异常，外部API调用失败

**处理**:
1. 确认是第三方问题（检查状态页面）
2. 启用降级策略（如有）
3. 通知用户
4. 监控第三方恢复

---

## 6. 通知模板

### 6.1 事件开始通知

```markdown
🚨 【P0事件】系统异常

**时间**: YYYY-MM-DD HH:MM
**影响**: [影响描述]
**状态**: 处理中
**IC**: @xxx

正在排查，请等待进一步通知。
```

### 6.2 事件恢复通知

```markdown
✅ 【P0恢复】系统已恢复

**时间**: YYYY-MM-DD HH:MM
**影响时长**: XX分钟
**根因**: [简述]
**处理方式**: [回滚/修复]

服务已恢复正常，复盘将在24小时内完成。
```

---

## 7. 复盘模板

事件解决后24小时内完成：

```markdown
# 事件复盘: YYYY-MM-DD P0事件

## 事件概述
- **发生时间**: HH:MM - HH:MM
- **影响时长**: XX分钟
- **影响范围**: [用户数/功能]
- **严重程度**: P0

## 时间线
| 时间 | 事件 | 负责人 |
|------|------|--------|
| HH:MM | 发现问题 | |
| HH:MM | 确认P0 | |
| HH:MM | 开始处理 | |
| HH:MM | 服务恢复 | |

## 根因分析
### 直接原因
[描述]

### 根本原因
[描述]

### 5 Whys
1. Why: ...
2. Why: ...
3. Why: ...
4. Why: ...
5. Why: ...

## 改进措施
| 措施 | 负责人 | 截止日期 | 状态 |
|------|--------|---------|------|
| | | | |

## 经验教训
- ...
```

---

## 8. 值班制度

### 8.1 值班表

| 日期 | 一线值班 | 二线值班 |
|------|---------|---------|
| 周一-周五 | @xxx | @yyy |
| 周六-周日 | @zzz | @aaa |

### 8.2 值班职责

- 监控告警群
- 15分钟内响应P0/P1
- 记录事件处理过程
- 交接班时同步未完成事项

---

## 9. 联系方式

| 角色 | 姓名 | 电话 | 飞书 |
|------|------|------|------|
| 值班群 | - | - | [链接] |
| Tech Lead | @xxx | 138xxxx | @xxx |
| DBA | @yyy | 139xxxx | @yyy |
| 老板 | @zzz | 137xxxx | @zzz |

---

## 10. 参考文档

- [部署手册](./deploy.md)
- [回滚手册](./rollback.md)
- [监控告警配置](../archive/2025-12-structure-cleanup/5.infrastructure/OBSERVABILITY_GUIDE.md)
