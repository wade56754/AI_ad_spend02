# /perf-analyze - 性能分析

> **版本**: v1.0
> **优先级**: 中
> **依赖**: py-spy (Python), React DevTools

---

## 用途

分析代码性能问题，包括 N+1 查询、内存泄漏、慢查询、渲染性能等。

---

## 使用方式

```bash
/perf-analyze                     # 分析整个项目
/perf-analyze <file>              # 分析指定文件
/perf-analyze --backend           # 仅后端
/perf-analyze --frontend          # 仅前端
/perf-analyze --db                # 仅数据库查询
/perf-analyze --api <endpoint>    # 分析特定 API
```

---

## 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `<file>` | 目标文件 | `backend/services/*.py` |
| `--backend` | 仅后端分析 | |
| `--frontend` | 仅前端分析 | |
| `--db` | 仅数据库查询 | |
| `--api` | 分析特定 API | `/api/v1/daily-reports` |
| `--profile` | 启用 profiling | |

---

## 分析项目

### 后端性能

| 检查项 | 说明 |
|--------|------|
| N+1 查询 | 循环中的数据库查询 |
| 慢查询 | 缺少索引、全表扫描 |
| 内存泄漏 | 未释放的资源 |
| 同步阻塞 | 阻塞异步代码 |
| 缓存缺失 | 可缓存的重复计算 |

### 前端性能

| 检查项 | 说明 |
|--------|------|
| 不必要渲染 | 缺少 memo/useMemo |
| 大型 bundle | 未拆分的依赖 |
| 图片优化 | 未压缩/未懒加载 |
| 状态管理 | 过度渲染 |
| 内存泄漏 | 未清理的订阅 |

### 数据库性能

| 检查项 | 说明 |
|--------|------|
| 缺少索引 | 频繁查询字段 |
| 过度查询 | 可合并的查询 |
| 大事务 | 长时间锁表 |
| 连接泄漏 | 未释放连接 |

---

## 示例

### 分析 N+1 查询

```bash
/perf-analyze --db
```

输出:
```
🔍 数据库查询分析
=================

扫描文件: 24 个
发现问题: 3 个

┌──────────────────────────────────────────────────────────┐
│ N+1 查询检测                                             │
├──────────┬────────────────────────────────────────────────┤
│ 位置     │ backend/services/daily_report_service.py:67   │
│ 问题     │ 循环中查询 Project 表                         │
│ 影响     │ 100 条记录 = 101 次查询                       │
│ 修复     │ 使用 selectinload 预加载                      │
└──────────┴────────────────────────────────────────────────┘

修复示例:
```python
# 修复前
reports = db.query(DailyReport).all()
for report in reports:
    project = report.project  # N+1!

# 修复后
reports = db.query(DailyReport).options(
    selectinload(DailyReport.project)
).all()
```

### 分析 API 性能

```bash
/perf-analyze --api /api/v1/daily-reports
```

输出:
```
🚀 API 性能分析: /api/v1/daily-reports
======================================

响应时间分析:
  平均: 245ms
  P95:  580ms
  P99:  1.2s

瓶颈分析:
  1. 数据库查询: 180ms (73%)
     - daily_reports 表: 120ms
     - projects JOIN: 60ms
  2. 序列化: 45ms (18%)
  3. 业务逻辑: 20ms (8%)

优化建议:
  🔴 [高优先] 添加 project_id 索引
  🟡 [中优先] 使用 Redis 缓存热点数据
  🟢 [低优先] 启用响应压缩
```

### 分析前端渲染

```bash
/perf-analyze --frontend
```

输出:
```
⚛️ React 性能分析
=================

组件渲染分析:
  DailyReportTable: 12 次/秒 ⚠️ 过度渲染
  StatusBadge: 48 次/秒 ⚠️ 需要 memo
  Header: 1 次/秒 ✅

Bundle 分析:
  总大小: 1.2MB
  最大块: vendors.js (450KB)

优化建议:
  🔴 为 DailyReportTable 添加 React.memo
  🟡 拆分 lodash 按需导入
  🟢 图片使用 next/image
```

---

## 与项目集成

### 性能指标

基于 SoT 定义的性能要求:
- API 响应: < 200ms (P95)
- 页面加载: < 3s (LCP)
- 数据库查询: < 50ms

### 自动化

可集成到 CI/CD:
```yaml
- name: Performance Check
  run: /perf-analyze --ci --threshold 200ms
```

---

## 输出

1. 终端报告
2. `perf-report.json` (可选)
3. 火焰图 (可选)
