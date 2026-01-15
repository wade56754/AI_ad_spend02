# SoT 版本清单

> **版本**: v1.1
> **最后更新**: 2026-01-16
> **维护者**: 架构组

---

## 核心 SoT 文档

| 文件 | 当前版本 | 最后审查 | 负责人 | 状态 |
|------|----------|----------|--------|------|
| MASTER.md | v4.9 | 2026-01-02 | 架构组 | active |
| DATA_SCHEMA.md | v5.11 | 2026-01-10 | 架构组 | active |
| STATE_MACHINE.md | v2.9 | 2026-01-02 | 架构组 | active |
| BUSINESS_RULES.md | v5.2 | 2026-01-12 | 业务组 | active |
| API_SOT.md | v9.7 | 2026-01-02 | 后端组 | frozen |
| AUTH_SPEC.md | v2.2 | 2026-01-02 | 后端组 | active |
| ERROR_CODES_SOT.md | v2.2 | 2025-11-27 | 后端组 | active |

---

## 业务规则子模块

| 文件 | 当前版本 | 规则数 | 负责人 | 状态 |
|------|----------|--------|--------|------|
| BR-AUTH.md | v1.0 | 6 | 业务组 | active |
| BR-USER.md | v1.0 | 5 | 业务组 | active |
| BR-PROJ.md | v1.0 | 8 | 业务组 | active |
| BR-ACCT.md | v1.0 | 6 | 业务组 | active |
| BR-FIN.md | v1.0 | 10 | 财务组 | active |
| BR-RPT.md | v1.0 | 9 | 业务组 | active |
| BR-RECON.md | v1.0 | 7 | 财务组 | active |
| BR-PROFIT.md | v1.0 | 6 | 财务组 | active |
| BR-DATA.md | v1.0 | 5 | 架构组 | active |

---

## 导航文档

| 文件 | 当前版本 | 用途 | 状态 |
|------|----------|------|------|
| INDEX.md | v2.0 | AI 快速导航 | active |
| VERSION_MANIFEST.md | v1.0 | 版本清单 (本文件) | active |
| GLOSSARY.md | v1.0 | 术语汇总 | active |
| CHANGELOG.md | v1.0 | 变更日志 | active |

---

## 版本管理规则

### 版本号格式

```
MAJOR.MINOR

MAJOR: 重大变更（破坏性修改、核心概念变化）
MINOR: 功能增强（新增规则、澄清说明）
```

### 升级流程

1. **提出变更**: 在 CHANGELOG.md 记录变更需求
2. **审查**: 相关负责人 Review
3. **批准**: 架构组 + 业务组双签（核心文档）
4. **更新**: 修改文档并升级版本号
5. **同步**: 更新本文件和 CLAUDE.md 中的版本引用

### 状态定义

| 状态 | 说明 |
|------|------|
| `active` | 当前使用中 |
| `frozen` | 冻结，仅允许 bugfix |
| `deprecated` | 已废弃，计划移除 |

---

## 冻结版本快照

### SoT Freeze v1.0 (2025-11-24)

首次冻结的基准版本：

```
MASTER.md v4.9
DATA_SCHEMA.md v5.11
STATE_MACHINE.md v2.9
BUSINESS_RULES.md v5.2
API_SOT.md v9.7
ERROR_CODES_SOT.md v2.2
AUTH_SPEC.md v2.2
```

### SoT Freeze v2.0 (2025-12-27)

历史冻结版本：

```
MASTER.md v4.9
DATA_SCHEMA.md v5.11
STATE_MACHINE.md v2.9
BUSINESS_RULES.md v5.2
API_SOT.md v9.7
ERROR_CODES_SOT.md v2.2
AUTH_SPEC.md v2.2
```

### SoT Freeze v2.1 (2026-01-16)

当前冻结版本：

```
MASTER.md v4.9
DATA_SCHEMA.md v5.11
STATE_MACHINE.md v2.9
BUSINESS_RULES.md v5.2
API_SOT.md v9.7
ERROR_CODES_SOT.md v2.2
AUTH_SPEC.md v2.2
```

---

## 引用规范

在代码和文档中引用 SoT 时，必须包含版本号：

```python
# 正确
# SoT: MASTER.md v4.9 §2.4

# 错误
# SoT: MASTER.md §2.4
```

```markdown
<!-- 正确 -->
> 来源: STATE_MACHINE.md v2.9 SM-1

<!-- 错误 -->
> 来源: STATE_MACHINE.md SM-1
```

---

## 相关文档

- [INDEX.md](./INDEX.md) - AI 快速导航
- [CHANGELOG.md](./CHANGELOG.md) - SoT 变更历史
- [GLOSSARY.md](./GLOSSARY.md) - 术语汇总
- [../CLAUDE.md](../../CLAUDE.md) - 项目入口

---

**维护周期**: 每次 SoT 文档变更后更新
