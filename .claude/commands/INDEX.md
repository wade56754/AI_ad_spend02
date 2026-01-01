# 命令索引

> **版本**: v3.0
> **更新日期**: 2026-01-02
> **命令总数**: 6 个核心命令

---

## 核心命令 (v3.0)

| 命令 | 说明 | 使用示例 |
|------|------|----------|
| `/gen` | 代码生成 | `/gen be 创建日报接口` |
| `/review` | 代码审查 + SoT 检查 | `/review backend/services/*.py` |
| `/doc` | 文档生成 | `/doc api` |
| `/openspec:proposal` | 规范变更提案 | `/openspec:proposal add-status` |
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

**文件**: [gen.md](./gen.md)

---

### /review - 代码审查

```bash
/review <file>           # 完整审查
/review <file> --sot     # 仅 SoT 合规检查
/review <file> --fix     # 审查并自动修复
```

**文件**: [review.md](./review.md)

---

### /doc - 文档生成

```bash
/doc api             # API 文档
/doc readme <path>   # 模块 README
/doc changelog       # 变更日志
/doc sot <module>    # SoT 规范文档
```

**文件**: [doc.md](./doc.md)

---

### /openspec:* - 规范管理

```bash
/openspec:proposal <name>   # 创建变更提案
/openspec:apply <name>      # 应用变更
/openspec:archive <name>    # 归档变更
```

**文件**: [openspec/](./openspec/)

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

### 从 v2.x 迁移到 v3.0

| 旧命令 | 新命令 |
|--------|--------|
| `/gen-v2 be <task>` | `/gen be <task>` |
| `/review-v2 <file>` | `/review <file>` |
| `/doc-v2 api` | `/doc api` |
| `/spec proposal` | `/openspec:proposal` |
| `/spec validate` | (已移除，集成到 proposal) |
| `/spec apply` | `/openspec:apply` |
| `/spec archive` | `/openspec:archive` |
| `/openspec-proposal` | `/openspec:proposal` |
| `/openspec-apply` | `/openspec:apply` |
| `/openspec-archive` | `/openspec:archive` |

---

## 快速参考卡

```
┌─────────────────────────────────────────────────────────┐
│                   命令速查表 v3.0                        │
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
│    /openspec:proposal 创建提案                          │
│    /openspec:apply    应用变更                          │
│    /openspec:archive  归档变更                          │
├─────────────────────────────────────────────────────────┤
│  工作流                                                 │
│    /flow be-dev       后端开发                          │
│    /flow fullstack    全栈开发                          │
├─────────────────────────────────────────────────────────┤
│  帮助                                                   │
│    /help              查看帮助                          │
└─────────────────────────────────────────────────────────┘
```
