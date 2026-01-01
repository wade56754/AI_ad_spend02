# 命令索引

> **版本**: v3.1
> **更新日期**: 2026-01-02
> **命令总数**: 11 个命令 (6 核心 + 5 辅助)

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

## 辅助命令 (v3.1 新增)

| 命令 | 说明 | 使用示例 |
|------|------|----------|
| `/test-gen` | 测试自动生成 | `/test-gen backend/services/daily_report.py` |
| `/auto-fix` | 自动修复 | `/auto-fix backend/routers/*.py --sot` |
| `/security-scan` | 安全扫描 | `/security-scan --backend` |
| `/perf-analyze` | 性能分析 | `/perf-analyze --api /api/v1/daily-reports` |
| `/migration` | 数据库迁移 | `/migration generate add_status_field` |

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

### /test-gen - 测试自动生成

```bash
/test-gen <file>              # 为指定文件生成测试
/test-gen <file> --unit       # 仅单元测试
/test-gen <file> --integration # 集成测试
/test-gen <module>            # 为整个模块生成测试
```

**文件**: [test-gen.md](./test-gen.md)

---

### /auto-fix - 自动修复

```bash
/auto-fix <file>              # 自动修复指定文件
/auto-fix <dir>               # 自动修复目录下所有文件
/auto-fix <file> --dry-run    # 仅预览，不实际修改
/auto-fix <file> --sot        # 仅修复 SoT 相关问题
```

**文件**: [auto-fix.md](./auto-fix.md)

---

### /security-scan - 安全扫描

```bash
/security-scan                    # 扫描整个项目
/security-scan --backend          # 仅后端
/security-scan --frontend         # 仅前端
/security-scan --deps             # 仅依赖检查
/security-scan --severity high    # 仅高危漏洞
```

**文件**: [security-scan.md](./security-scan.md)

---

### /perf-analyze - 性能分析

```bash
/perf-analyze                     # 分析整个项目
/perf-analyze --backend           # 仅后端
/perf-analyze --frontend          # 仅前端
/perf-analyze --db                # 仅数据库查询
/perf-analyze --api <endpoint>    # 分析特定 API
```

**文件**: [perf-analyze.md](./perf-analyze.md)

---

### /migration - 数据库迁移

```bash
/migration generate <name>        # 生成迁移脚本
/migration validate               # 验证迁移安全性
/migration apply                  # 应用迁移
/migration rollback               # 回滚上一次迁移
/migration history                # 查看迁移历史
```

**文件**: [migration.md](./migration.md)

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
│                   命令速查表 v3.1                        │
├─────────────────────────────────────────────────────────┤
│  代码生成                                               │
│    /gen be <task>     后端代码                          │
│    /gen fe <task>     前端代码                          │
│    /test-gen <file>   自动生成测试                      │
├─────────────────────────────────────────────────────────┤
│  质量检查                                               │
│    /review <file>     代码审查                          │
│    /auto-fix <file>   自动修复                          │
│    /security-scan     安全扫描                          │
│    /perf-analyze      性能分析                          │
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
│  数据库                                                 │
│    /migration generate 生成迁移                         │
│    /migration apply    应用迁移                         │
│    /migration rollback 回滚迁移                         │
├─────────────────────────────────────────────────────────┤
│  工作流                                                 │
│    /flow be-dev       后端开发                          │
│    /flow fullstack    全栈开发                          │
├─────────────────────────────────────────────────────────┤
│  帮助                                                   │
│    /help              查看帮助                          │
└─────────────────────────────────────────────────────────┘
```
