# Claude Commands 索引

> **版本**: v3.1
> **更新日期**: 2026-01-02
> **命令总数**: 25

---

## 核心命令

| 命令 | 文件 | 用途 |
|------|------|------|
| `/gen` | `gen.md` | 代码生成 (后端/前端/测试) |
| `/review` | `review.md` | 代码审查 + SoT 检查 |
| `/doc` | `doc.md` | 文档生成 |
| `/flow` | `flow.md` | 工作流编排 |
| `/help` | `help.md` | 快速帮助 |
| `/sot-check` | `sot-check.md` | SoT 合规检查 |

## 质量工具命令 (v3.1 新增)

| 命令 | 文件 | 用途 |
|------|------|------|
| `/test-gen` | `test-gen.md` | 测试自动生成 (pytest/vitest) |
| `/auto-fix` | `auto-fix.md` | 自动修复 (SoT/风格/类型) |
| `/security-scan` | `security-scan.md` | 安全扫描 (OWASP/依赖) |
| `/perf-analyze` | `perf-analyze.md` | 性能分析 (N+1/慢查询/渲染) |
| `/migration` | `migration.md` | 数据库迁移 (Alembic) |

---

## OpenSpec 命令

| 命令 | 文件 | 用途 |
|------|------|------|
| `/openspec:proposal` | `openspec/proposal.md` | 创建变更提案 |
| `/openspec:apply` | `openspec/apply.md` | 应用变更 |
| `/openspec:archive` | `openspec/archive.md` | 归档变更 |

---

## 辅助命令

| 命令 | 文件 | 用途 |
|------|------|------|
| `/ai-help` | `ai-help.md` | AI 编程助手帮助 |
| `/check-code` | `check-code.md` | 快速代码检查 |
| `/clarify` | `clarify.md` | 需求澄清 |
| `/dev-flow` | `dev-flow.md` | 统一开发流程 |
| `/gen-feature` | `gen-feature.md` | 生成功能代码 |
| `/kb-build` | `kb-build.md` | 构建知识库 |
| `/kb-search` | `kb-search.md` | 知识库搜索 |
| `/pc` | `pc.md` | 提示词优化 |
| `/preprompt` | `preprompt.md` | 加载提示词模板 |
| `/project-config` | `project-config.md` | 项目配置 |
| `/restart` | `restart.md` | 重启开发服务 |
| `/sot-context` | `sot-context.md` | 获取 SoT 上下文 |

---

## 目录结构

```
commands/
├── gen.md             # 代码生成
├── review.md          # 代码审查
├── doc.md             # 文档生成
├── flow.md            # 工作流编排
├── help.md            # 快速帮助
├── sot-check.md       # SoT 检查
├── test-gen.md        # 测试自动生成 (v3.1)
├── auto-fix.md        # 自动修复 (v3.1)
├── security-scan.md   # 安全扫描 (v3.1)
├── perf-analyze.md    # 性能分析 (v3.1)
├── migration.md       # 数据库迁移 (v3.1)
├── INDEX.md           # 命令索引
├── README.md          # 本文件
└── openspec/          # OpenSpec 命令组
    ├── proposal.md    # 创建提案
    ├── apply.md       # 应用变更
    └── archive.md     # 归档变更
```

---

## OpenSpec 工作流

```
/openspec:proposal   创建变更提案
        ↓
   [审批流程]
        ↓
/openspec:apply      应用变更到代码
        ↓
/openspec:archive    归档已完成的变更
```

**变更流程**:
1. 使用 `/openspec:proposal` 创建变更提案
2. 在 `openspec/changes/<change-id>/` 目录编写 spec deltas
3. 获得审批后使用 `/openspec:apply` 应用变更
4. 变更完成后使用 `/openspec:archive` 归档

---

## 快速参考

```bash
# 代码生成
/gen be <task>           # 后端代码
/gen fe <task>           # 前端代码
/test-gen <file>         # 自动生成测试

# 代码审查
/review <file>           # 完整审查
/auto-fix <file>         # 自动修复

# 质量检查
/security-scan           # 安全扫描
/perf-analyze            # 性能分析

# 数据库
/migration generate <n>  # 生成迁移
/migration apply         # 应用迁移
/migration rollback      # 回滚迁移

# 文档生成
/doc api                 # API 文档
/doc changelog           # 变更日志

# 规范管理
/openspec:proposal <id>  # 创建提案
/openspec:apply <id>     # 应用变更
/openspec:archive <id>   # 归档变更

# 工作流
/flow be-dev <task>      # 后端开发
/flow fullstack <task>   # 全栈开发
```

---

## 相关文件

- 技能索引: `../skills/INDEX.md`
- 项目规则: `../PROJECT_RULES.md`
- SoT 文档: `../../docs/sot/`
