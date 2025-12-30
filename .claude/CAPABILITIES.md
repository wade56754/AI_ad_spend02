# Claude 能力清单

> **版本**: v1.0
> **最后更新**: 2025-12-30
> **维护者**: 架构组

---

## 能力概览

| 类别 | 数量 | 说明 |
|------|------|------|
| Skills | 23 | 专业技能模块 |
| Agents | 3 | 任务执行代理 |
| Commands | 11 | 斜杠命令 |
| **总计** | **37** | - |

---

## Skills (技能库)

### 代码工厂 (Code Factory) - 6 个

| 技能 | 版本 | 状态 | 职责 |
|------|------|------|------|
| ai-ad-code-factory | 3.4 | ready | 主编排器：搜索→选型→适配→组装→验证 |
| ai-ad-code-searcher | 1.0 | ready | 代码搜索引擎 |
| ai-ad-code-selector | 1.0 | ready | 代码选型器 |
| ai-ad-code-adapter | 1.0 | ready | 代码适配器 |
| ai-ad-code-assembler | 1.0 | ready | 代码组装器 |
| ai-ad-code-verifier | 1.0 | ready | 代码验证器 |

### 代码生成 (Generators) - 3 个

| 技能 | 版本 | 状态 | 职责 |
|------|------|------|------|
| ai-ad-be-gen | 2.0 | ready | 后端代码生成 (FastAPI) |
| ai-ad-fe-gen | 1.0 | ready | 前端代码生成 (React/Next.js) |
| ai-ad-test-gen | 1.0 | ready | 测试代码生成 |

### 文档处理 (Documentation) - 5 个

| 技能 | 版本 | 状态 | 职责 |
|------|------|------|------|
| ai-ad-doc-orchestrator | 5.3 | ready | 文档编排器：ASDD 文档生成工作流 |
| ai-ad-doc-architect | 2.2 | ready | 文档架构师：文档规划与设计 |
| ai-doc-system-auditor | 1.5 | ready | 文档系统审计员 |
| superclaude-enhancer | 1.0 | ready | SuperClaude 增强器 |
| code-cleanup | 1.0 | ready | 代码清理工具 |

### 规范驱动 (Spec-Driven) - 3 个

| 技能 | 版本 | 状态 | 职责 |
|------|------|------|------|
| ai-ad-spec-kit | 1.0 | ready | Spec-Kit 规范工具包 (5 阶段工作流) |
| ai-ad-spec-governor | 1.2 | ready | 规范治理总调度器 |
| ai-ad-flow-orchestrator | 1.0 | ready | 流程编排器 |

### 测试自动化 (Testing) - 3 个

| 技能 | 版本 | 状态 | 职责 |
|------|------|------|------|
| ai-ad-agents-test-orchestrator | 2.2 | ready | Agent 测试编排器 |
| ai-ad-agents-test-runner | 1.0 | ready | Agent 测试运行器 |
| ai-ad-api-automation-test | 1.3 | beta | API 自动化测试 |

### 工具类 (Utils) - 3 个

| 技能 | 版本 | 状态 | 职责 |
|------|------|------|------|
| ai-ad-prompt-structurer | 4.0 | ready | 提示词结构化器 |
| prompt-optimizer | 1.0 | ready | 提示词优化器 |
| ai-code-quality-assistant | 1.0 | ready | 代码质量助手 |

---

## Agents (代理库)

| 代理 | 版本 | 状态 | 职责 | 触发方式 |
|------|------|------|------|---------|
| codex-loop | 1.0 | active | 代码开发循环代理 | Task tool |
| doc-architect | 1.0 | active | 文档架构代理 | Task tool |
| doc-fixer | 1.0 | active | 文档修复代理 | Task tool |

### Agents vs Skills 区别

| 维度 | Skills | Agents |
|------|--------|--------|
| 执行方式 | 单次调用 | 持续循环 |
| 状态管理 | 无状态 | 有状态 |
| 适用场景 | 明确任务 | 复杂任务 |
| 上下文 | 需显式传递 | 自动维护 |

---

## Commands (命令库)

### 代码生成命令

| 命令 | 用途 | 调用 Skill |
|------|------|-----------|
| `/gen be <task>` | 后端代码生成 | ai-ad-be-gen |
| `/gen fe <task>` | 前端代码生成 | ai-ad-fe-gen |
| `/gen test <task>` | 测试代码生成 | ai-ad-test-gen |

### 文档命令

| 命令 | 用途 | 调用 Skill |
|------|------|-----------|
| `/doc <task>` | 文档生成/修复 | ai-ad-doc-orchestrator |

### 审查命令

| 命令 | 用途 | 调用 Skill |
|------|------|-----------|
| `/review <file>` | 代码审查 | ai-master-architect |
| `/sot-check <file>` | SoT 合规检查 | ai-ad-spec-governor |

### 流程命令

| 命令 | 用途 | 调用 Skill |
|------|------|-----------|
| `/dev-flow <type>` | 开发流程编排 | ai-ad-flow-orchestrator |
| `/restart` | 重启开发服务 | - |
| `/pc <prompt>` | 提示词优化 | ai-ad-prompt-structurer |

### OpenSpec 命令

| 命令 | 用途 | 说明 |
|------|------|------|
| `/openspec-proposal` | 创建变更提案 | OpenSpec 工作流 |
| `/openspec-validate` | 验证提案 | OpenSpec 工作流 |
| `/openspec-apply` | 应用变更 | OpenSpec 工作流 |
| `/openspec-archive` | 归档变更 | OpenSpec 工作流 |

---

## 能力依赖图

```
Commands (用户入口)
    │
    ├── /gen be ──────────► ai-ad-be-gen ──────► API_SOT.md
    │                                           DATA_SCHEMA.md
    │
    ├── /gen fe ──────────► ai-ad-fe-gen ──────► 组件库
    │
    ├── /review ──────────► ai-master-architect ► MASTER.md
    │                                             BR-*.md
    │
    ├── /sot-check ───────► ai-ad-spec-governor ► 所有 SoT
    │
    └── /doc ─────────────► ai-ad-doc-orchestrator
                                │
                                ├── ai-ad-doc-architect
                                └── ai-doc-system-auditor
```

---

## 快速使用指南

### 生成后端代码

```
/gen be 创建用户登录 API
```

### 生成前端代码

```
/gen fe 创建登录表单组件
```

### 审查代码

```
/review backend/routers/auth.py
```

### 检查 SoT 合规

```
/sot-check backend/services/finance_service.py
```

### 优化提示词

```
/pc 帮我写一个代码重构的提示词
```

---

## 扩展指南

### 添加新 Skill

1. 在 `.claude/skills/` 下创建目录
2. 添加 `SKILL.md` 文件（含 YAML Frontmatter）
3. 更新 `.claude/skills/INDEX.md`
4. 更新本文件 (CAPABILITIES.md)

### 添加新 Command

1. 在 `.claude/commands/` 下创建 `.md` 文件
2. 更新 `.claude/commands/README.md`
3. 更新本文件 (CAPABILITIES.md)

---

## 相关文档

- [Skills INDEX](./skills/INDEX.md) - 技能详细索引
- [Agents README](./agents/README.md) - 代理使用说明
- [Commands README](./commands/README.md) - 命令使用说明
- [INTEGRATION_MAP](./INTEGRATION_MAP.md) - 集成关系图

---

**维护周期**: 每次新增 Skill/Agent/Command 后更新
