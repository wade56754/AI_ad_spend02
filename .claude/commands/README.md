# Claude Commands 索引

> **版本**: v1.0
> **更新日期**: 2025-12-17
> **命令总数**: 7

---

## 命令清单

| 命令 | 文件 | 用途 |
|------|------|------|
| `/agent` | `agent.md` | 代理管理命令 |
| `/doc-agent` | `doc-agent.md` | 文档代理命令 |
| `/orch` | `orch.md` | 编排器命令 |
| `/sot-check` | `sot-check.md` | SoT 检查命令 |
| `/openspec.apply` | `openspec/apply.md` | 应用 OpenSpec 变更 |
| `/openspec.archive` | `openspec/archive.md` | 归档 OpenSpec |
| `/openspec.proposal` | `openspec/proposal.md` | 创建 OpenSpec 提案 |

---

## 命令详情

### 核心命令

#### `/agent`
**文件**: `agent.md`
**用途**: 代理管理和调用
```
/agent [agent-name] [task]
```

#### `/doc-agent`
**文件**: `doc-agent.md`
**用途**: 文档相关代理操作
```
/doc-agent [action] [doc-name]
```

#### `/orch`
**文件**: `orch.md`
**用途**: 编排器控制命令
```
/orch [pipeline] [params]
```

#### `/sot-check`
**文件**: `sot-check.md`
**用途**: SoT 文档一致性检查
```
/sot-check [doc-path]
```

### OpenSpec 命令

#### `/openspec.proposal`
**文件**: `openspec/proposal.md`
**用途**: 创建新的 OpenSpec 变更提案
```
/openspec.proposal [change-id] [description]
```

#### `/openspec.apply`
**文件**: `openspec/apply.md`
**用途**: 应用已批准的 OpenSpec 变更
```
/openspec.apply [change-id]
```

#### `/openspec.archive`
**文件**: `openspec/archive.md`
**用途**: 归档已完成的 OpenSpec 变更
```
/openspec.archive [change-id]
```

---

## 目录结构

```
commands/
├── agent.md           # 代理管理
├── doc-agent.md       # 文档代理
├── orch.md            # 编排器
├── sot-check.md       # SoT 检查
└── openspec/          # OpenSpec 命令组
    ├── apply.md       # 应用变更
    ├── archive.md     # 归档变更
    └── proposal.md    # 创建提案
```

---

## 命令结构规范

每个命令文件应遵循以下结构：

```yaml
---
name: command-name
type: command
usage: "/command-name [args]"
description: |
  命令描述
examples:
  - "/command-name arg1"
  - "/command-name --flag value"
---

命令提示内容...
```

---

## 与 OpenSpec 的集成

OpenSpec 命令组提供完整的规范变更管理流程：

```
/openspec.proposal   创建变更提案
        ↓
  [审批流程]
        ↓
/openspec.apply      应用变更到代码
        ↓
/openspec.archive    归档已完成的变更
```

**变更流程**:
1. 使用 `/openspec.proposal` 创建变更提案
2. 在 `openspec/changes/<change-id>/` 目录编写 spec deltas
3. 获得审批后使用 `/openspec.apply` 应用变更
4. 变更完成后使用 `/openspec.archive` 归档

---

## 相关文件

- 技能索引: `../skills/INDEX.md`
- 代理索引: `../agents/README.md`
- 项目规则: `../PROJECT_RULES.md`
- OpenSpec 指南: `../../openspec/AGENTS.md`
