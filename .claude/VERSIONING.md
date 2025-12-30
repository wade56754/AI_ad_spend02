# 版本管理策略 (Versioning Strategy)

> **版本**: v1.0
> **最后更新**: 2025-12-30
> **维护者**: 架构组

---

## 版本号格式

### 语义化版本 (Semantic Versioning)

```
MAJOR.MINOR.PATCH

MAJOR: 破坏性变更（不兼容的 API 修改）
MINOR: 功能增强（向后兼容的功能新增）
PATCH: 问题修复（向后兼容的问题修正）
```

### 简化版本 (SoT 文档)

```
MAJOR.MINOR

MAJOR: 重大变更（核心概念变化、破坏性修改）
MINOR: 功能增强（新增规则、澄清说明、小幅调整）
```

---

## 版本管理范围

### SoT 文档

| 类别 | 文件 | 版本格式 | 示例 |
|------|------|---------|------|
| 核心文档 | MASTER.md, DATA_SCHEMA.md | MAJOR.MINOR | v4.6 |
| 状态机 | STATE_MACHINE.md | MAJOR.MINOR | v2.8 |
| 业务规则 | BR-*.md | MAJOR.MINOR | v1.0 |
| API 规范 | API_SOT.md | MAJOR.MINOR | v9.4 |

### Skills/Agents/Commands

| 类别 | 版本格式 | 示例 |
|------|---------|------|
| Skills | MAJOR.MINOR | 3.4 |
| Agents | MAJOR.MINOR | 1.0 |
| Commands | 无版本号 | - |

### 项目代码

| 类别 | 版本格式 | 管理方式 |
|------|---------|---------|
| 后端 | MAJOR.MINOR.PATCH | package.json / pyproject.toml |
| 前端 | MAJOR.MINOR.PATCH | package.json |
| 数据库 | Migration 编号 | Alembic / Prisma |

---

## 版本升级规则

### SoT 文档升级

| 变更类型 | 版本变化 | 示例 |
|---------|---------|------|
| 核心概念变化 | MAJOR +1 | v4.6 → v5.0 |
| 角色/状态增减 | MAJOR +1 | v4.6 → v5.0 |
| 规则新增 | MINOR +1 | v4.6 → v4.7 |
| 规则澄清 | MINOR +1 | v4.6 → v4.7 |
| 文档格式调整 | MINOR +1 | v4.6 → v4.7 |
| 错别字修复 | 不升级 | v4.6 |

### Skill 升级

| 变更类型 | 版本变化 | 示例 |
|---------|---------|------|
| 工作流重构 | MAJOR +1 | 2.0 → 3.0 |
| 新增功能 | MINOR +1 | 3.4 → 3.5 |
| Bug 修复 | MINOR +1 | 3.4 → 3.5 |
| 文档更新 | 不升级 | 3.4 |

---

## 版本冻结 (Freeze)

### 什么是版本冻结

版本冻结是将一组 SoT 文档锁定在特定版本，作为开发基准。

### 冻结版本列表

| 冻结版本 | 日期 | 说明 |
|---------|------|------|
| SoT Freeze v1.0 | 2025-11-24 | 首次冻结 |
| SoT Freeze v2.0 | 2025-12-27 | 当前版本 |

### 冻结流程

1. **提案**: 在 CHANGELOG.md 记录冻结计划
2. **审查**: 架构组 + 业务组 Review
3. **批准**: 双签确认
4. **执行**:
   - 更新 VERSION_MANIFEST.md
   - 更新 CLAUDE.md 版本引用
   - 更新 .claude/data/config.yaml
5. **通知**: 通知所有开发者

---

## 版本引用规范

### 在代码中引用

```python
# 正确：包含版本号
# SoT: MASTER.md v4.6 §2.4
# SoT: STATE_MACHINE.md v2.8 SM-1

# 错误：缺少版本号
# SoT: MASTER.md §2.4
```

### 在文档中引用

```markdown
<!-- 正确 -->
> 来源: STATE_MACHINE.md v2.8 SM-1
> 参考: BUSINESS_RULES.md v4.7 BR-FIN-001

<!-- 错误 -->
> 来源: STATE_MACHINE.md SM-1
```

### 在 Skill 中声明

```yaml
---
name: ai-ad-be-gen
version: "2.0"
baseline:
  - MASTER.md v4.6
  - API_SOT.md v9.4
  - DATA_SCHEMA.md v5.6
---
```

---

## 版本同步检查

### 手动检查

```bash
# 检查 CLAUDE.md 中的版本引用
grep -E "v[0-9]+\.[0-9]+" CLAUDE.md

# 检查 Skills 中的 baseline
grep -r "baseline" .claude/skills/*/SKILL.md
```

### 自动检查

使用 `/sot-check` 命令检查版本一致性：

```
/sot-check --versions
```

---

## 版本变更日志

所有版本变更必须记录在：

1. **SoT 文档**: `docs/sot/CHANGELOG.md`
2. **Skills**: 各 SKILL.md 的版本历史部分
3. **项目**: `memory-bank/progress.md`

### 日志格式

```markdown
## [vX.Y] - YYYY-MM-DD

### Added
- 新增内容

### Changed
- 变更内容

### Removed
- 移除内容

### Fixed
- 修复内容
```

---

## 版本回滚

### SoT 文档回滚

1. 从 Git 历史恢复目标版本
2. 更新 VERSION_MANIFEST.md
3. 更新 CHANGELOG.md 记录回滚
4. 通知受影响的 Skills 和代码

### Skill 回滚

1. 从 Git 历史恢复目标版本
2. 更新 INDEX.md 中的版本号
3. 记录回滚原因

---

## 相关文档

- [VERSION_MANIFEST.md](../docs/sot/VERSION_MANIFEST.md) - 版本清单
- [CHANGELOG.md](../docs/sot/CHANGELOG.md) - 变更日志
- [CAPABILITIES.md](./CAPABILITIES.md) - 能力清单

---

**维护周期**: 策略变更时更新
