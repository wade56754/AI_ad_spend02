# 发布记录：v2.0.3

> **发布日期**: 2025-12-27
> **发布人**: @xxx
> **环境**: production

---

## 版本信息

| 项目 | 值 |
|------|---|
| 版本号 | v2.0.3 |
| Git Tag | v2.0.3 |
| 回滚点 | pre-release-20251227-143022 |
| 数据库版本 | alembic revision `abc123def` |

---

## 变更摘要

### 新功能
- 账户期初余额录入功能
- 供应链对账优化（含期初基准）

### Bug修复
- 修复日报状态机缺少confirmed状态的问题

### 文档更新
- SoT更新至v2.0.2，解决Q-001阶梯定价边界

---

## 关联变更

| 类型 | 链接 |
|------|------|
| PR | #123, #124, #125 |
| Issue | #100, #101 |
| SoT版本 | v2.0.2 |
| CHANGELOG | [docs/sot/CHANGELOG.md](../sot/CHANGELOG.md) |

---

## 迁移信息

### 数据库迁移
```bash
# 迁移命令
alembic upgrade abc123def

# 回滚命令
alembic downgrade -1
```

### 迁移脚本
| 脚本 | 说明 | 可回滚 |
|------|------|:------:|
| 001_add_opening_balance.py | 新增期初余额字段 | ✅ |
| 002_update_recon_formula.py | 更新对账公式 | ✅ |

### 数据迁移
- 无数据迁移

---

## 验收证据

### 自动化测试
| 测试类型 | 结果 | 报告链接 |
|---------|:----:|---------|
| 单元测试 | ✅ | [pytest-report.html](./artifacts/pytest-report.html) |
| 覆盖率 | 78% | [coverage.html](./artifacts/coverage/index.html) |
| Lint | ✅ | CI日志 |
| 验收测试 | ✅ | [acceptance.html](./artifacts/acceptance.html) |

### 手动验收
| 验收项 | 结果 | 验收人 |
|--------|:----:|-------|
| 账户期初余额录入 | ✅ | @户管测试 |
| 供应链对账显示正确 | ✅ | @财务测试 |
| 权限隔离正确 | ✅ | @QA |

---

## 审批确认

| 角色 | 确认人 | 确认时间 | 确认方式 |
|------|--------|---------|---------|
| Tech Lead | @yyy | 2025-12-27 14:00 | PR Approval |
| CEO | @zzz | 2025-12-27 14:30 | PR Label: ceo-approved |

---

## 回滚方案

### 触发条件
- 线上出现P0级别bug
- 财务数据计算错误
- 用户无法登录

### 回滚步骤
```bash
# 1. 切换到回滚点
git checkout pre-release-20251227-143022

# 2. 数据库回滚
alembic downgrade -1

# 3. 重新部署
./scripts/deploy.sh

# 4. 验证
curl https://api.example.com/health
```

### 回滚负责人
- 主责：@xxx
- 备份：@yyy

---

## 发布后监控

### 关键指标（发布后24小时）
| 指标 | 基线 | 发布后 | 状态 |
|------|------|--------|:----:|
| API响应时间p99 | 200ms | - | ⏳ |
| 错误率 | 0.1% | - | ⏳ |
| 日报提交成功率 | 99.5% | - | ⏳ |

### 监控链接
- [Grafana Dashboard](https://grafana.example.com/d/xxx)
- [Sentry Errors](https://sentry.example.com/xxx)

---

## 备注

（发布过程中的特殊情况记录）
