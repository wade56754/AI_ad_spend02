# Skills 索引

> **版本**: v1.0
> **更新日期**: 2025-12-17
> **技能总数**: 19

---

## 按类别分类

### 代码工厂 (Code Factory)

| 技能 | 版本 | 状态 | 说明 |
|------|------|------|------|
| [ai-ad-code-factory](./ai-ad-code-factory/SKILL.md) | 2.0 | ready | 主编排器 - 搜索→选型→适配→组装→验证 |
| [ai-ad-code-searcher](./ai-ad-code-searcher/SKILL.md) | 1.0 | ready | 代码搜索引擎 |
| [ai-ad-code-selector](./ai-ad-code-selector/SKILL.md) | 1.0 | ready | 代码选型器 |
| [ai-ad-code-adapter](./ai-ad-code-adapter/SKILL.md) | 1.0 | ready | 代码适配器 |
| [ai-ad-code-assembler](./ai-ad-code-assembler/SKILL.md) | 1.0 | ready | 代码组装器 |
| [ai-ad-code-verifier](./ai-ad-code-verifier/SKILL.md) | 1.0 | ready | 代码验证器 |

### 文档处理 (Documentation)

| 技能 | 版本 | 状态 | 说明 |
|------|------|------|------|
| [ai-ad-doc-orchestrator](./ai-ad-doc-orchestrator/SKILL.md) | 5.3 | ready | 文档编排器 - ASDD 文档生成工作流 |
| [ai-ad-doc-architect](./ai-ad-doc-architect/SKILL.md) | 2.2 | ready | 文档架构师 - 文档规划与设计 |
| [ai-ad-doc-fixer](./ai-ad-doc-fixer/SKILL.md) | 3.1 | ready | 文档修复器 - 审查与修订 |
| [ai-project-doc-writer](./ai-project-doc-writer/SKILL.md) | 3.1 | ready | 文档编写者 - 大纲与正文生成 |
| [ai-ad-sot-doc-pipeline](./ai-ad-sot-doc-pipeline/SKILL.md) | 3.1 | ready | SoT 文档管道执行器 |
| [ai-doc-system-auditor](./ai-doc-system-auditor/SKILL.md) | 1.5 | ready | 文档系统审计员 |

### 规范驱动 (Spec-Driven)

| 技能 | 版本 | 状态 | 说明 |
|------|------|------|------|
| [ai-ad-spec-kit](./ai-ad-spec-kit/SKILL.md) | 1.0 | ready | Spec-Kit 规范工具包 (5阶段工作流) |
| [ai-ad-spec-governor](./ai-ad-spec-governor/SKILL.md) | 1.2 | ready | 规范治理总调度器 |

### 架构与工程 (Architecture)

| 技能 | 版本 | 状态 | 说明 |
|------|------|------|------|
| [ai-master-architect](./ai-master-architect/SKILL.md) | 4.1 | ready | 系统架构裁判官 - 宪法级校验 |
| [prompt-engineer-skill](./prompt-engineer-skill/SKILL.md) | 2.1 | ready | 提示词工程 - Claude 最佳实践 |

### 测试自动化 (Testing)

| 技能 | 版本 | 状态 | 说明 |
|------|------|------|------|
| [ai-ad-agents-test-orchestrator](./ai-ad-agents-test-orchestrator/SKILL.md) | 2.2 | ready | Agent 测试编排器 |
| [ai-ad-agents-test-runner](./ai-ad-agents-test-runner/SKILL.md) | 1.0 | ready | Agent 测试运行器 |
| [ai-ad-api-automation-test](./ai-ad-api-automation-test/SKILL.md) | 1.3 | beta | API 自动化测试 |

---

## 按字母排序

- [ai-ad-agents-test-orchestrator](./ai-ad-agents-test-orchestrator/SKILL.md) - Agent 测试编排器
- [ai-ad-agents-test-runner](./ai-ad-agents-test-runner/SKILL.md) - Agent 测试运行器
- [ai-ad-api-automation-test](./ai-ad-api-automation-test/SKILL.md) - API 自动化测试
- [ai-ad-code-adapter](./ai-ad-code-adapter/SKILL.md) - 代码适配器
- [ai-ad-code-assembler](./ai-ad-code-assembler/SKILL.md) - 代码组装器
- [ai-ad-code-factory](./ai-ad-code-factory/SKILL.md) - 代码工厂主编排器
- [ai-ad-code-searcher](./ai-ad-code-searcher/SKILL.md) - 代码搜索引擎
- [ai-ad-code-selector](./ai-ad-code-selector/SKILL.md) - 代码选型器
- [ai-ad-code-verifier](./ai-ad-code-verifier/SKILL.md) - 代码验证器
- [ai-ad-doc-architect](./ai-ad-doc-architect/SKILL.md) - 文档架构师
- [ai-ad-doc-fixer](./ai-ad-doc-fixer/SKILL.md) - 文档修复器
- [ai-ad-doc-orchestrator](./ai-ad-doc-orchestrator/SKILL.md) - 文档编排器
- [ai-ad-sot-doc-pipeline](./ai-ad-sot-doc-pipeline/SKILL.md) - SoT 文档管道
- [ai-ad-spec-governor](./ai-ad-spec-governor/SKILL.md) - 规范治理调度器
- [ai-ad-spec-kit](./ai-ad-spec-kit/SKILL.md) - Spec-Kit 规范工具包
- [ai-doc-system-auditor](./ai-doc-system-auditor/SKILL.md) - 文档系统审计员
- [ai-master-architect](./ai-master-architect/SKILL.md) - 架构裁判官
- [ai-project-doc-writer](./ai-project-doc-writer/SKILL.md) - 文档编写者
- [prompt-engineer-skill](./prompt-engineer-skill/SKILL.md) - 提示词工程

---

## 统计信息

| 类别 | 数量 | 状态 |
|------|------|------|
| 代码工厂 | 6 | ready |
| 文档处理 | 6 | ready |
| 规范驱动 | 2 | ready |
| 架构与工程 | 2 | ready |
| 测试自动化 | 3 | 2 ready, 1 beta |
| **总计** | **19** | **18 ready, 1 beta** |

---

## 依赖关系

```
ai-ad-doc-orchestrator (文档编排器)
├── ai-project-doc-writer    # 大纲+正文生成
├── ai-ad-doc-fixer          # 审查+修订
└── ai-master-architect      # 宪法级校验

ai-ad-code-factory (代码工厂)
├── ai-ad-code-searcher      # 搜索
├── ai-ad-code-selector      # 选型
├── ai-ad-code-adapter       # 适配
├── ai-ad-code-assembler     # 组装
└── ai-ad-code-verifier      # 验证

ai-ad-spec-kit (规范工具包)
└── 独立技能，无子依赖
```

---

## 相关文件

- 项目规则: `../.claude/PROJECT_RULES.md`
- 代理索引: `../agents/README.md`
- 命令索引: `../commands/README.md`
