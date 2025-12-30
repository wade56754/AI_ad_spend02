# 命令索引

> **版本**: v2.0
> **更新日期**: 2025-12-30
> **命令总数**: 6 个核心命令

---

## 核心命令 (v2.0)

| 命令 | 说明 | 使用示例 |
|------|------|----------|
| `/gen` | 代码生成 | `/gen be 创建日报接口` |
| `/review` | 代码审查 + SoT 检查 | `/review backend/services/*.py` |
| `/doc` | 文档生成 | `/doc api` |
| `/spec` | 规范管理 | `/spec proposal add-status` |
| `/flow` | 工作流编排 | `/flow be-dev 新功能` |
| `/help` | 快速帮助 | `/help gen` |

---

## 命令详情

### /gen - 代码生成

```bash
/gen be <task>      # 后端代码 (Schema → Service → Router)
/gen fe <task>      # 前端代码 (Types → API → Components)
/gen test <task>    # 测试代码 (pytest 用例)
```

**文件**: [gen-v2.md](./gen-v2.md)

---

### /review - 代码审查

```bash
/review <file>           # 完整审查
/review <file> --sot     # 仅 SoT 合规检查
/review <file> --fix     # 审查并自动修复
```

**文件**: [review-v2.md](./review-v2.md)

---

### /doc - 文档生成

```bash
/doc api             # API 文档
/doc readme <path>   # 模块 README
/doc changelog       # 变更日志
/doc sot <module>    # SoT 规范文档
```

**文件**: [doc-v2.md](./doc-v2.md)

---

### /spec - 规范管理

```bash
/spec proposal <name>   # 创建变更提案
/spec validate <name>   # 验证提案
/spec apply <name>      # 应用变更
/spec archive <name>    # 归档变更
```

**文件**: [spec.md](./spec.md)

---

### /flow - 工作流编排

```bash
/flow be-dev <task>      # 后端开发流程
/flow fe-dev <task>      # 前端开发流程
/flow fullstack <task>   # 全栈开发流程
/flow hotfix <task>      # 热修复流程
/flow release <version>  # 发版流程
```

**文件**: [flow.md](./flow.md)

---

### /help - 快速帮助

```bash
/help              # 显示所有命令
/help <command>    # 显示命令详情
/help sot          # 显示 SoT 白名单
```

**文件**: [help.md](./help.md)

---

## 迁移说明

### 从 v1.x 迁移到 v2.0

| 旧命令 | 新命令 |
|--------|--------|
| `/gen be <task>` | `/gen be <task>` (不变) |
| `/gen fe <task>` | `/gen fe <task>` (不变) |
| `/sot-check <file>` | `/review <file> --sot` |
| `/openspec-proposal` | `/spec proposal` |
| `/openspec-validate` | `/spec validate` |
| `/openspec-apply` | `/spec apply` |
| `/openspec-archive` | `/spec archive` |
| `/dev-flow be` | `/flow be-dev` |
| `/restart` | `/flow restart` (待实现) |
| `/pc <prompt>` | 已移除 (集成到 /gen) |

### 旧版命令 (仍可用，但建议迁移)

旧版命令文件保留在 `.claude/commands/` 目录，但建议使用新版 `-v2` 命令。

---

## 快速参考卡

```
┌─────────────────────────────────────────────────────────┐
│                   命令速查表                             │
├─────────────────────────────────────────────────────────┤
│  代码生成                                               │
│    /gen be <task>     后端代码                          │
│    /gen fe <task>     前端代码                          │
│    /gen test <task>   测试代码                          │
├─────────────────────────────────────────────────────────┤
│  质量检查                                               │
│    /review <file>     代码审查                          │
│    /review --sot      SoT 合规                          │
├─────────────────────────────────────────────────────────┤
│  文档操作                                               │
│    /doc api           API 文档                          │
│    /doc changelog     变更日志                          │
├─────────────────────────────────────────────────────────┤
│  规范管理                                               │
│    /spec proposal     创建提案                          │
│    /spec apply        应用变更                          │
├─────────────────────────────────────────────────────────┤
│  工作流                                                 │
│    /flow be-dev       后端开发                          │
│    /flow fullstack    全栈开发                          │
├─────────────────────────────────────────────────────────┤
│  帮助                                                   │
│    /help              查看帮助                          │
└─────────────────────────────────────────────────────────┘
```
