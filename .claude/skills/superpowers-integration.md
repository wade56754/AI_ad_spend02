# Superpowers 集成指南

> 基于 [obra/superpowers](https://github.com/obra/superpowers) v4.0.3
> 为本项目 AI 编码助手提供增强技能
> 与 AI Code Factory + SuperClaude 深度整合

## 架构概览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      统一开发编排器 (Unified Dev Orchestrator)                │
│                    superpowers-factory-bridge/SKILL.md                       │
│                                                                              │
│    命令: /udev full | /udev brainstorm | /udev plan | /udev tdd | /udev impl │
└────────────────────────────────────┬────────────────────────────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         │                           │                           │
         ▼                           ▼                           ▼
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│    SUPERPOWERS      │   │   AI CODE FACTORY   │   │  SUPERCLAUDE        │
│    (方法论)          │   │    (领域知识)        │   │   ENHANCER          │
├─────────────────────┤   ├─────────────────────┤   ├─────────────────────┤
│ • brainstorming     │   │ • ai-ad-be-gen      │   │ • /sc:analyze       │
│ • writing-plans     │   │ • ai-ad-fe-gen      │   │ • /sc:troubleshoot  │
│ • test-driven-dev   │   │ • ai-ad-test-gen    │   │ • /sc:research      │
│ • subagent-dev      │   │ • flow-orchestrator │   │ • /sc:improve       │
│ • executing-plans   │   │ • spec-governor     │   │                     │
│ • systematic-debug  │   │                     │   │ Pre/Post Hooks      │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SoT 合规层 (Compliance Layer)                      │
│ MASTER.md v4.9 → DATA_SCHEMA.md v5.10 → STATE_MACHINE.md v2.9               │
│ → BUSINESS_RULES.md v5.1 → API_SOT.md → ERROR_CODES_SOT.md                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 技能库位置

| 位置 | 内容 |
|------|------|
| `.superpowers/skills/` | Superpowers 原生技能 |
| `.claude/skills/superpowers-factory-bridge/` | **统一编排器 (NEW)** |
| `.superpowers/skills/sot-aware-planning/` | SoT 感知计划扩展 |
| `.superpowers/skills/tdd-with-factory/` | TDD + 工厂整合 |

## 统一命令接口 (/udev)

| 命令 | 描述 | 阶段 |
|------|------|------|
| `/udev full <task>` | 完整开发周期 | BRAINSTORM → PLAN → EXECUTE → FINISH |
| `/udev brainstorm <topic>` | 设计+SoT上下文 | Phase 1 |
| `/udev plan <task>` | SoT感知计划 | Phase 2 |
| `/udev tdd <feature>` | TDD+工厂测试 | RED → GREEN → REFACTOR |
| `/udev impl <task>` | 子代理+工厂生成 | Phase 3 |
| `/udev debug <issue>` | 系统化调试 | Debugging |
| `/udev finish` | 完成分支 | Phase 4 |

### 完整开发工作流

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  BRAINSTORM  │───▶│     PLAN     │───▶│   EXECUTE    │───▶│    FINISH    │
│  + SoT 上下文 │    │  + SoT 引用   │    │  + TDD       │    │  + 最终审查   │
└──────────────┘    └──────────────┘    │  + Factory   │    └──────────────┘
       │                   │            └──────────────┘           │
       ▼                   ▼                   │                   ▼
   design.md           plan.md             代码+测试             PR/Merge
```

## 核心工作流

### 1. 头脑风暴 (Brainstorming)
在编写代码前激活，通过问题细化想法，探索替代方案。

**触发**: 用户说 "创建X" 或 "实现Y" 时
**技能文件**: `.superpowers/skills/brainstorming/SKILL.md`
**整合命令**: `/udev brainstorm <topic>`

### 2. 测试驱动开发 (TDD)
**核心原则**: 先写测试，看它失败，再写最小代码使其通过。

```
RED (写失败测试)    → /gen test → 验证 FAIL
         ↓
GREEN (最小实现)   → /gen be|fe → 验证 PASS → /sot-check
         ↓
REFACTOR (重构)   → /sc:improve → /sot-check → commit
```

**铁律**: 没有失败的测试，就不能写生产代码
**技能文件**: `.superpowers/skills/test-driven-development/SKILL.md`
**扩展文件**: `.superpowers/skills/tdd-with-factory/SKILL.md`
**整合命令**: `/udev tdd <feature>`

### 3. 编写计划 (Writing Plans)
将工作分解为小任务，自动注入 SoT 引用。

**技能文件**: `.superpowers/skills/writing-plans/SKILL.md`
**扩展文件**: `.superpowers/skills/sot-aware-planning/SKILL.md`
**整合命令**: `/udev plan <task>`

### 4. 执行计划 (Executing Plans)
批量执行计划，带有检查点和审查。

**技能文件**: `.superpowers/skills/executing-plans/SKILL.md`

### 5. 系统化调试 (Systematic Debugging)
4 阶段根因分析流程。

**技能文件**: `.superpowers/skills/systematic-debugging/SKILL.md`
**整合命令**: `/udev debug <issue>`

### 6. 子代理驱动开发 (Subagent-Driven Development)
快速迭代，带两阶段审查（规格合规性 + 代码质量）。

**技能文件**: `.superpowers/skills/subagent-driven-development/SKILL.md`
**整合命令**: `/udev impl <task>`

## 与 AI Code Factory 的整合

### 三层协同

| 层级 | 提供者 | 职责 |
|------|--------|------|
| **方法论** | Superpowers | TDD 纪律、计划结构、调试流程 |
| **领域知识** | AI Code Factory | SoT 规范、业务规则、代码生成 |
| **质量增强** | SuperClaude | 前置分析、后置审查、代码优化 |

### SoT 合规检查点

| 阶段 | 检查点 | 工具 | 阻断? |
|------|--------|------|-------|
| Brainstorm | SoT 依赖识别 | Manual | 否 |
| Plan | 任务 SoT 引用注入 | sot-aware-planning | 否 |
| TDD RED | 测试 SoT 注解 | ai-ad-test-gen | 是 |
| TDD GREEN | 代码 SoT 注解 | ai-ad-be/fe-gen | 是 |
| Execute | 状态/角色/错误码白名单 | /sot-check | 是 |
| Spec Review | SoT 合规检查 | sot-spec-reviewer | 是 |
| Quality | 代码质量+模式 | /sc:analyze | 条件 |
| Final | 防幻觉验证 | CONFIRM phase | 是 |

### 模块检测规则

根据任务描述中的关键词，自动注入相关 SoT 章节:

| 关键词 | 模块 | 注入的 SoT 章节 |
|--------|------|----------------|
| 日报, 投放, CPL, 投手 | pitcher | STATE_MACHINE#daily_report, BR-RPT-* |
| 充值, 流水, 账本, 资金 | finance | LEDGER_SOT, BR-FIN-*, STATE_MACHINE#topup |
| 账户, 开户, 授权 | ad_account | BR-ACCT-*, STATE_MACHINE#ad_account |
| 项目, 成员, 盈亏 | project | BR-PROJ-*, DATA_SCHEMA#projects |
| 对账, 差异, 调整 | reconciliation | BR-RECON-*, STATE_MACHINE#reconciliation |
| 用户, 角色, 权限 | auth | BR-AUTH-*, AUTH_SPEC.md |
| 利润, 毛利, 成本 | profit | BR-PROFIT-*, DATA_SCHEMA#receivable |

## 快速命令对照表

| 命令 | 描述 | Superpowers | AI Factory | SuperClaude |
|------|------|-------------|------------|-------------|
| `/udev full <task>` | 完整开发周期 | brainstorm → plan → execute | /sot-check → /gen | /sc:analyze |
| `/udev brainstorm` | 设计讨论 | brainstorming | /sot-context | /sc:research |
| `/udev plan` | SoT感知计划 | writing-plans | /sot-check | - |
| `/udev tdd` | TDD+工厂 | test-driven-development | /gen test | /sc:analyze |
| `/udev impl` | 子代理实现 | subagent-driven-dev | /gen be, /gen fe | /sc:analyze |
| `/udev debug` | 系统化调试 | systematic-debugging | /dev-flow fix | /sc:troubleshoot |
| `/udev finish` | 完成分支 | finishing-a-development-branch | /sot-check | /sc:analyze |

## TDD 铁律

```
╔════════════════════════════════════════════════════════════════════╗
║                              TDD 铁律                               ║
║                                                                     ║
║     没有失败的测试，就不能写生产代码                                  ║
║     NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST                ║
║                                                                     ║
║     违规处理: 先写代码再写测试 → 删除代码 → 重新开始                 ║
╚════════════════════════════════════════════════════════════════════╝
```

## 参考链接
- [Superpowers GitHub](https://github.com/obra/superpowers) (v4.0.3)
- [统一编排器](./.claude/skills/superpowers-factory-bridge/SKILL.md)
- [TDD 工厂整合](./.superpowers/skills/tdd-with-factory/SKILL.md)
- [SoT 感知计划](./.superpowers/skills/sot-aware-planning/SKILL.md)
