# AI 驱动开发文档参考项目

> **版本**: v1.0
> **日期**: 2025-12-17
> **用途**: 整合 AI 驱动开发的最佳实践和开源参考项目

---

## 1. 核心理念

### 1.1 Spec-Driven Development (规范驱动开发)

传统开发: `代码先行 → 文档补充`
规范驱动: `规范先行 → 代码生成 → 规范验证`

**核心原则**:
- 规范是"可执行的合同"，而非文档摆设
- AI Agent 使用规范作为"唯一真相来源 (SoT)"
- 分离"稳定的意图"与"灵活的实现"

---

## 2. 重点参考项目

### 2.1 GitHub Spec-Kit ⭐⭐⭐⭐⭐

> **最推荐** - GitHub 官方的规范驱动开发工具包

| 属性 | 值 |
|------|-----|
| **GitHub** | [github/spec-kit](https://github.com/github/spec-kit) |
| **License** | MIT |
| **语言** | Python |
| **兼容 AI** | Claude Code, GitHub Copilot, Gemini CLI, Cursor, Windsurf |

**四阶段工作流**:
```
Constitution → Specification → Planning → Tasks → Implementation
(宪法)         (规范)          (规划)     (任务)   (实现)
```

**核心命令**:
```bash
# 安装
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# 初始化项目
specify init <project-name> --ai claude

# 工作流命令
/speckit.constitution   # 定义项目原则
/speckit.specify        # 描述需求 (关注 "what"，非 "how")
/speckit.plan           # 技术架构文档
/speckit.tasks          # 生成可执行任务
/speckit.implement      # 执行所有任务
```

**与本项目 ASDD 的对比**:

| 维度 | Spec-Kit | 本项目 ASDD |
|------|----------|-------------|
| 层级 | 4 阶段 | 6 层架构 |
| 规范格式 | Markdown + 命令 | SoT 文档 + 状态机 |
| 重点 | 0-to-1 开发 | 全生命周期 |
| 验证 | Checklist | SoT Guard |

**借鉴点**:
- ✅ Constitution (宪法) 概念 → 类似我们的 MASTER.md
- ✅ 命令化工作流 (可集成到 SuperClaude Skill)
- ✅ 多 AI Agent 支持架构

---

### 2.2 ReadmeAI ⭐⭐⭐⭐

> AI 驱动的 README 生成器

| 属性 | 值 |
|------|-----|
| **GitHub** | [eli64s/readme-ai](https://github.com/eli64s/readme-ai) |
| **Stars** | 2,800+ |
| **License** | MIT |
| **语言** | Python |

**核心能力**:
- 自动分析代码库结构
- 提取依赖和技术栈
- 生成完整 README (介绍、功能、安装、使用)
- 支持多种 LLM (OpenAI, Anthropic, Gemini, Ollama)

**工作流程**:
```
代码库 → 依赖提取 → 结构分析 → LLM 生成 → README 输出
```

**安装使用**:
```bash
pip install -U readmeai

readmeai --repository https://github.com/user/project \
  --badge-style flat-square \
  --header-style modern
```

**借鉴点**:
- ✅ 代码库分析管道 (可用于 CodeSearcherSkill)
- ✅ 多 LLM Provider 支持架构
- ✅ 自动文档生成模式

---

### 2.3 Cursor Rules & Prompts ⭐⭐⭐⭐

> AI 编码助手规则系统

| 属性 | 值 |
|------|-----|
| **GitHub** | [thehimel/cursor-rules-and-prompts](https://github.com/thehimel/cursor-rules-and-prompts) |
| **Stars** | 100+ |
| **License** | MIT |

**核心理念**:
```
"让 AI 自动遵循你的编码规范，而非每次重复说明"
```

**规则结构**:
```yaml
---
alwaysApply: true
description: "代码风格规则"
author: "team"
---

# 规则内容 (Markdown)
## Code Style
- 使用绝对导入
- 组件采用 PascalCase

## Organization
- 按功能模块组织
- 共享组件放在 shared/
```

**六大分类**:
1. **Code Style** - 导入、组件、样式模式
2. **Organization** - 文件结构、功能布局
3. **Documentation** - 文档标准、注释规范
4. **Infrastructure** - 路由、配置
5. **Constraints** - 反模式、最佳实践
6. **Dependencies** - 库选择、组件使用

**借鉴点**:
- ✅ 规则分类体系 (可整合到 PROJECT_RULES.md)
- ✅ YAML frontmatter 格式
- ✅ 多项目同步机制

---

### 2.4 AI-Doc-Gen ⭐⭐⭐⭐

> 多 Agent 代码文档生成系统

| 属性 | 值 |
|------|-----|
| **GitHub** | [divar-ir/ai-doc-gen](https://github.com/divar-ir/ai-doc-gen) |
| **Stars** | 670+ |
| **License** | MIT |

**特点**:
- 多 Agent 协作分析代码库
- GitLab 集成
- 自动生成综合文档

**借鉴点**:
- ✅ 多 Agent 文档生成架构
- ✅ 代码库分析策略

---

### 2.5 AI DevOps Intent Solutions ⭐⭐⭐

> 企业级文档生成方案

| 属性 | 值 |
|------|-----|
| **GitHub** | [jeremylongshore/ai-devops-intent-solutions](https://github.com/jeremylongshore/ai-devops-intent-solutions) |
| **Stars** | 22 |

**特点**:
- 通过 Claude Code CLI 和 Cursor IDE 生成企业文档
- PRD、架构、任务、风险管理一体化
- 5 分钟生成完整项目文档

**借鉴点**:
- ✅ 企业级文档模板
- ✅ 快速文档生成流程

---

## 3. AI 驱动开发工作流对比

| 项目 | 核心流程 | 适用场景 |
|------|----------|---------|
| **Spec-Kit** | Constitution → Spec → Plan → Tasks → Implement | Greenfield 项目 |
| **本项目 ASDD** | MASTER → SoT → API → Code → Test → Deploy | 全生命周期管理 |
| **Cursor Rules** | Rules → AI Generation → Validation | 日常编码规范 |
| **ReadmeAI** | Repo Analysis → LLM → Documentation | 文档自动化 |

---

## 4. 推荐整合方案

### 4.1 文档层级整合

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AI 驱动开发文档体系                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Level 1: 宪法层 (Constitution)                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  MASTER.md                                                   │   │
│  │  • 业务边界和不变量                                          │   │
│  │  • 永久禁止行为                                              │   │
│  │  • 核心原则                                                  │   │
│  │                                                             │   │
│  │  参考: Spec-Kit Constitution                                │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  Level 2: 规范层 (Specification)                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  SoT 文档集                                                  │   │
│  │  • STATE_MACHINE.md - 状态机定义                             │   │
│  │  • DATA_SCHEMA.md - 数据模式                                 │   │
│  │  • BUSINESS_RULES.md - 业务规则                              │   │
│  │  • API_SOT.md - API 规范                                     │   │
│  │  • ERROR_CODES_SOT.md - 错误码                               │   │
│  │                                                             │   │
│  │  参考: Spec-Kit Specification                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  Level 3: 规则层 (Rules)                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  PROJECT_RULES.md / CLAUDE.md                               │   │
│  │  • 编码规范                                                  │   │
│  │  • 反模式库                                                  │   │
│  │  • AI 行为约束                                               │   │
│  │                                                             │   │
│  │  参考: Cursor Rules & Prompts                               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              ↓                                      │
│  Level 4: 代码资料库 (Code Library)                                 │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  code-library/                                               │   │
│  │  • inventory/ - 功能清单                                     │   │
│  │  • references/ - GitHub 参考                                 │   │
│  │  • templates/ - 适配模板                                     │   │
│  │                                                             │   │
│  │  参考: 本项目 Phase 1 成果                                   │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 工作流整合

**现有 ASDD 工作流**:
```
需求 → SoT 文档 → 代码生成 → SoT Guard 验证 → 测试 → 部署
```

**整合 Spec-Kit 后**:
```
Constitution (MASTER.md)
    ↓
Specification (SoT 文档)
    ↓
Planning (架构设计)
    ↓
Tasks (任务分解)
    ↓
Implementation (代码工厂)
    ├── Search (CodeSearcherSkill)
    ├── Select (CodeSelectorSkill)
    ├── Adapt (CodeAdapterSkill)
    ├── Assemble (CodeAssemblerSkill)
    └── Verify (CodeVerifierSkill + SoT Guard)
```

---

## 5. 行动建议

### 5.1 短期 (Phase 1)

1. **引入 Spec-Kit 命令体系**
   - 在 SuperClaude 中添加 `/speckit.*` 类似命令
   - 整合到现有 ai-ad-doc-orchestrator

2. **整合 Cursor Rules 格式**
   - 将 PROJECT_RULES.md 改造为结构化规则
   - 添加 YAML frontmatter 元数据

3. **完善 CLAUDE.md**
   - 参考 Cursor Rules 的分类体系
   - 添加更多编码规范细节

### 5.2 中期 (Phase 2)

1. **引入 ReadmeAI 代码分析能力**
   - 用于 CodeSearcherSkill 的代码库分析
   - 自动生成功能清单

2. **构建多 Agent 文档生成**
   - 参考 AI-Doc-Gen 的多 Agent 架构
   - 与现有 DocAgent 整合

### 5.3 长期 (Phase 3)

1. **完整 Spec-Kit 工作流**
   - 实现 Constitution → Implementation 全流程
   - 与 CI/CD 集成

---

## 6. 参考链接汇总

### 规范驱动开发
- [GitHub Spec-Kit](https://github.com/github/spec-kit) - GitHub 官方规范驱动工具包
- [Spec-Driven Development Blog](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/) - GitHub 博客介绍

### AI 文档生成
- [ReadmeAI](https://github.com/eli64s/readme-ai) - README 自动生成
- [AI-Doc-Gen](https://github.com/divar-ir/ai-doc-gen) - 多 Agent 文档生成
- [AI DevOps Intent Solutions](https://github.com/jeremylongshore/ai-devops-intent-solutions) - 企业文档方案

### AI 编码规则
- [Cursor Rules & Prompts](https://github.com/thehimel/cursor-rules-and-prompts) - AI 编码规则集
- [AI-Driven Development Topic](https://github.com/topics/ai-driven-development) - GitHub 主题页

### AI Agent 框架
- [MetaGPT](https://github.com/geekan/MetaGPT) - 多 Agent 软件开发
- [OpenHands](https://github.com/All-Hands-AI/OpenHands) - 自主开发 Agent
- [Aider](https://github.com/paul-gauthier/aider) - AI 配对编程

---

**文档结束**
