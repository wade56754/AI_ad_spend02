# Bug 修复索引

> 记录所有 Bug 修复，便于追踪和学习
> 自动生成于 2026-01-14 13:00

---

## 统计概览

| 指标 | 数量 |
|------|------|
| **总计** | 1 |
| **P0 (阻塞)** | 0 |
| **P1 (严重)** | 0 |
| **P2 (一般)** | 1 |
| **P3 (轻微)** | 0 |

---

## 按状态统计

| 状态 | 数量 |
|------|------|
| **待修复** | 0 |
| **修复中** | 0 |
| **已修复** | 1 |
| **已验证** | 0 |
| **已关闭** | 0 |

---

## Bug 列表

### 2026-01

| ID | 日期 | 标题 | 级别 | 状态 | 模块 |
|----|------|------|------|------|------|
| BUG-2026-0114-001 | 2026-01-14 | [FastVerifier Unicode error](./2026-01-14-FastVerifier-Unicode-error.md) | P2 | 已修复 | 代码工厂 |

---

## 快捷操作

```bash
# 记录新 Bug
python -m agents.skills.code_factory.tools.bug_tracker record

# 列出所有 Bug
python -m agents.skills.code_factory.tools.bug_tracker list

# 更新 Bug 状态
python -m agents.skills.code_factory.tools.bug_tracker update BUG-ID --status 已验证
```

---

## 相关文档

- [Bug 修复模板](./template.md)
- [历史修复汇总](../../docs/integration/BUG_FIXES_SUMMARY.md)

---

**最后更新**: 2026-01-14 13:00