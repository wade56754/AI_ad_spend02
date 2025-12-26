---
name: AI_AD_CODE_FIXER_FLOW
version: v1.2.0
status: release-candidate
layer: 6.agent-layer
owner: wade
last_reviewed: 2025-12-07
profile: backend-code-fix
baseline: AI_CODE_FACTORY_DEV_GUIDE_v2.3, MASTER.md v4.4

description: >
  本文档定义 AI_ad_spend02 项目中 backend 代码修复（code-fix）、
  自动测试（test-runner）、自动 patch、多轮回归（loop）
  的完整执行规范。所有执行必须在 Context7（backend-code-fix profile）
  环境下进行，并通过 use context7 自动加载约束、SoT 版本和路径限制。

dependencies:
  sot_versions:
    state_machine: v2.6
    data_schema: v5.2
    ledger_sot: v1.1
  required_skills:
    - ai-ad-doc-orchestrator
    - ai-ad-agents-test-runner
    - ai-doc-system-auditor
---

# AI_AD_CODE_FIXER_FLOW（Backend 代码修复流程规范）

本流程是 AI_ad_spend02 后端代码治理体系的一部分，用于确保：

- 与 SoT（Single Source of Truth）一致  
- 自动化修复生产代码  
- 自动运行 pytest 并多轮迭代  
- 每次 patch 受 Context7 MCP 保护（只改允许范围）  
- 修复结果可 Freeze 到版本库  

---

# 0. 执行前置条件：必须 use context7

使用本 agent-flow 之前，需在 Claude 中执行：

use context7


执行结果会自动加载：

- SoT 版本（v2.6 / v5.2 / v1.1）
- allowed_skills
- allowed_write_paths（backend/models、services、routers、core、utils）
- forbidden_write_paths（docs、tests、migrations、frontend）
- output_style、auto_format  
- constraints（Minimal Diff、禁止发明字段）

本流程 **完全依赖 Context7 MCP**。  
执行前不需要 `<CONTEXT7 preset="..."/>`，也不可替代。

---

# 1. 流程目的（Purpose）

AI_AD_CODE_FIXER_FLOW 旨在用 **AI+自动化** 方式，  
对 backend 代码进行：

- 错误修复（service, model, router, core）  
- SoT 对齐（字段、状态机、关系）  
- 自动补丁生成  
- pytest 自动化回归  
- 全局一致性验证  
- Freeze 冻结

最终目标：  

> 让 backend 模块达到：无 P0、无 P1、pytest 全部通过、可 Freeze。

---

# 2. 问题分级（Severity Rules）

必须与 `ai-doc-system-auditor` 的 P0/P1/P2 级别保持一致。

## **P0 – 阻塞问题（必须立即修复）**
- 运行期异常：ImportError, AttributeError, TypeError  
- SQLAlchemy 关系错误：NoForeignKeysError  
- 状态值使用旧枚举导致测试无法运行  
- 缺字段导致模型初始化失败  
- 业务逻辑错误使服务不可用  

## **P1 – 高危问题（应在本轮修复）**
- 违反 SoT：状态机、字段、外键关系不一致  
- service 层违背 SoT 状态流转  
- 与 DATA_SCHEMA 不一致的字段命名  
- 非终态可回退等逻辑错误  

## **P2 – 优化问题（可进入 backlog）**
- 断言偏差、错误消息不对齐  
- 模糊边界情况  
- 性能问题、重复计算  
- 日志格式不规范

---

# 3. 安全约束（Constraints）

## 3.1 写入限制（来自 Context7）

仅允许修改：



backend/models/**
backend/services/**
backend/routers/**
backend/core/**
backend/utils/**


禁止修改（只读）：



backend/tests/**
docs/**
frontend/**
migrations/**
alembic/**
scripts/**
.github/**


**测试文件禁止任何自动修改**（关键规则）  
防止 AI 通过“skip test”欺骗测试通过。

---

## 3.2 Minimal Diff Rule（最小差异补丁规则）

所有修复必须满足：

- 不允许重构非目标代码  
- 不允许重写整个文件  
- 只能修改必要行  
- 所有 Patch 必须可读、可解释、可回滚  

---

## 3.3 SoT 对齐规则

- 不允许发明不存在的字段  
- 不允许发明不存在的状态  
- 使用 ENUM 只能来自：STATE_MACHINE v2.6  
- Model 字段必须来自：DATA_SCHEMA v5.2  
- Ledger 操作必须来自：LEDGER_SOT v1.1

---

## 3.4 禁止自动 DDL / Migration

- 禁止生成 Alembic 迁移  
- 禁止修改数据库结构  
- 如果模型字段更改影响迁移，必须另开 Migration Flow

---

# 4. 流程阶段（Phase-by-Phase Definition）

## **Phase 0 — 初始化**

人类决定：

- 修复范围（模块：daily_reports / topups / reconciliation / ledger）  
- pytest 目标  
- 是否允许 auto_write（建议 true）  
- 必须先执行：`use context7`

---

## **Phase 1 — 错误收集 & 分类**

由 test-runner 运行：

```bash
python -m pytest backend/tests -q


收集：

passed / failed / skipped / errors

关键错误的堆栈

按文件分类的 P0/P1/P2

由 Agent 输出：

问题汇总

与 SoT 的偏差

需要修改的文件

Phase 2 — 修复计划（Repair Plan）

Agent 给出表格计划：

Severity	File	Line	Issue	Fix

必须覆盖：

根因分析

受影响模块

风险评估

是否需要人工审批

人类在这一阶段可以“否决危险方案”。

Phase 3 — 执行修复（Patch Execution）

由 orchestrator 执行：

加载 Context7

检查 allowed_write_paths

自动生成 patch

auto_write=True 写回代码

仅修改必要文件。

Patch 输出格式：

### backend/services/topup_service.py
- old
+ new

Phase 4 — 多轮回归（Loop）

再次运行 pytest：

python -m pytest backend/tests -q


Agent 分析：

P0 是否消失

P1 是否减少

是否产生新的问题

若仍有 P0 → 回到 Phase 2
最多允许 3~4 轮，否则需要人工介入。

Phase 5 — Freeze 准备（Freeze Ready）

满足以下条件：

与目标模块相关的所有测试：passed

P0 清零

P1 清零

Patch 差异最小化

完全遵守 SoT 版本

由 Agent 生成：

Freeze Summary

修复文件清单

SoT 对齐报告

由人类执行：

更新 FREEZE_MANIFEST

打 Git Tag

合并到 main 分支

5. Skill & Agent 协作结构

本流程依赖 3 个主要 skill：

ai-ad-doc-orchestrator

自动生成 patch

限制写入范围

遵守 Minimal Diff

加载 Context7

ai-ad-agents-test-runner

运行 pytest

输出结构化报告

区分 P0/P1/P2

ai-doc-system-auditor

检查 SoT 对齐

审计字段、枚举、状态、Ledger 行为

6. Claude 提示语模板（支持 MCP use context7）

注意：不再使用 <CONTEXT7 ...>
必须先输入 use context7，Claude 自动加载上下文。

使用说明

第 1 步（你输入）：

use context7


第 2 步（Claude 返回 “context loaded”）

第 3 步（你输入修复命令）：

<REQUEST>
  执行 AI_AD_CODE_FIXER_FLOW v1.2.0。

  模块范围：
    - topups
    - daily_reports

  pytest 输出：
    （粘贴统计）

  关键错误堆栈：
    （粘贴 P0 错误）

  要求：
    - 遵守 Context7（backend-code-fix profile）
    - 只修改 allowed_write_paths
    - 禁止修改 backend/tests/**
    - 使用 Minimal-Diff 原则

  请按本流程执行：
    1. classify problems
    2. generate repair_plan
    3. auto patch (auto_write=true)
    4. tell me next pytest commands
</REQUEST>

7. Freeze 条件（上线判定标准）

pytest：无 failed、无 errors

P0：0

P1：0

SoT 对齐：100%

Patch 差异最小

Context7 约束全部遵守

FREEZE_MANIFEST 已更新版本号

Git 上存在 freeze tag

满足以上条件后，本流程进入：

status: frozen
version: v1.2.1

8. 附录 A：示例 Execution Flow（Mermaid）
flowchart TD
    A[use context7] --> B[Phase 1: pytest 收集错误]
    B --> C[Phase 2: 修复计划]
    C --> D[Phase 3: patch 修复]
    D --> E[Phase 4: pytest 重新运行]
    E -->|P0 存在| C
    E -->|全部通过| F[Phase 5: Freeze]

9. 附录 B：Allowed / Forbidden 路径

Allowed：

backend/models/**

backend/services/**

backend/routers/**

backend/core/**

backend/utils/**

Forbidden：

backend/tests/**

docs/**

frontend/**

migrations/**

alembic/**

scripts/**

.github/**

.vscode/**

10. 附录 C：Minimal-Diff 示例
- return ad_account.assigned_user_id
+ return ad_account.assigned_to


不能这样（❌）：

- 全文件删除重写
+ 新文件覆盖

11. 附录 D：修复计划表样例
Severity	File	Issue	Plan
P0	topup_service.py:708	assigned_user_id 不存在	替换成 assigned_to，并添加 alias
P1	reconciliation.py	total_platform_spend 缺字段	添加 property alias，保持 SoT 一致