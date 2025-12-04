AI Spec Driven Development 迁移计划  
AI 广告代投系统 (AI_ad_spend02)  

编制日期: 2025-11-25  
基准版本: SoT Freeze v1.0  
输出类型: 结构映射 + 边界定义（禁止输出任意文档正文内容）

---

## 0. 总体目标与安全前提

- 本计划用于将现有 SoT 文档体系与 **ai-spec-driven-development (ASDD)** 的 7 核心文档结构对齐。
- 目标是：**增加“架构层/领域层/实现层”的分层清晰度，而不改变已有 SoT 语义**。
- **所有 AI 工具在执行本计划时，必须遵守以下前提：**

### 0.1 缺失信息停机机制

- 如在迁移过程中遇到：
  - 文档缺失
  - 概念未定义
  - 规则语义不明
- **禁止 AI 或任何工具“合理补全”**。
- 必须输出：  
  `Missing: <缺失项>`  
  由人工（架构师/业务负责人）补齐后再继续执行。

### 0.2 SoT Freeze 保护

- 现有 SoT 文档（STATE_MACHINE / DATA_SCHEMA / LEDGER_SOT / DAILY_REPORT_SOT / RECONCILIATION_SOT / TRANSFER_SOT 等）处于 **Freeze 状态**。
- 迁移过程中：
  - **禁止为了适配 ASDD 而修改 SoT 正文**。
  - 仅允许在新建的 ASDD 文档中 **引用 SoT**，不允许复制或改写 SoT 内容。

---

## 一、现有体系 vs ASDD 7 核心文档映射

| ASDD 核心文档  | 现有对应                                              | 映射类型   | 迁移建议   |
|----------------|-------------------------------------------------------|------------|------------|
| MASTER.md      | docs/1.overview/MASTER.md v3.3                       | 完全对应   | 保留，无需迁移 |
| PROJECT.md     | MASTER_SPEC.md v1.1 + SYSTEM_OVERVIEW.md v2.2        | 拆分对应   | 提炼业务视角，单独成文 |
| ARCHITECTURE.md| MASTER.md 第2-4章 + DDD_API_ARCHITECTURE.md          | 散落分布   | 重组为独立架构文档 |
| DOMAIN.md      | STATE_MACHINE.md v2.6 + DATA_SCHEMA.md v5.2 + BUSINESS_RULES.md v3.1 | 多文档分担 | 新建“导航索引层” |
| PATTERNS.md    | docs/3.dev-guides/\*.md                              | 无统一入口 | 整合为统一实现模式 |
| TESTING.md     | TESTING_GUIDE.md                                     | 部分对应   | 扩充测试策略 |
| DEPLOYMENT.md  | 无                                                    | 缺失       | 新建，绑定回滚锚点 |

---

## 二、7 核心文档定义与边界

### 2.1 MASTER.md（已存在 ✅）

| 属性       | 定义 |
|------------|------|
| 内容边界   | 系统哲学、不可变量、禁止事项、SoT 裁判链 |
| 不包含     | API 细节、表结构、状态流转规则、测试细节 |
| 目标读者   | AI Agent、新成员、架构审计员 |
| 执行者角色 | 架构师（唯一修改权） |
| AI 提示建议| 「任何实现前必须验证是否违反 MASTER.md 不可变量」 |
| 引用关系   | → 被所有文档引用（最高仲裁源） |
| 现有文件   | docs/1.overview/MASTER.md v3.3 |

---

### 2.2 PROJECT.md（需整合）

| 属性       | 定义 |
|------------|------|
| 内容边界   | 业务愿景、核心问题、成功指标、MVP 范围、功能清单、**明确不做什么**（Out of Scope） |
| 不包含     | 技术实现、API 格式、数据库设计、账务算法 |
| 目标读者   | PM、运营、客户、AI Agent（理解业务上下文） |
| 执行者角色 | PM / 业务架构师 |
| AI 提示建议| 「实现功能前验证是否在 MVP 范围内，且未触及 Out of Scope」 |
| 引用关系   | ← MASTER.md，→ DOMAIN.md |
| 来源映射   | 从 MASTER_SPEC.md §1-2 + SYSTEM_OVERVIEW.md 提取业务视角内容 |

> 额外要求：  
> - 必须明确列出：**本系统不做的事情**，如财务记账外部系统、税务申报、反洗钱等，防止业务范围无限膨胀。

---

### 2.3 ARCHITECTURE.md（需重组）

| 属性       | 定义 |
|------------|------|
| 内容边界   | 分层架构、组件关系、数据流图、部署拓扑、技术选型约束、服务间依赖方向 |
| 不包含     | 具体业务规则、字段定义、API 端点清单 |
| 目标读者   | 后端/前端开发、DevOps、AI Agent |
| 执行者角色 | 技术架构师 |
| AI 提示建议| 「新增模块前必须验证分层归属与依赖方向，不允许反向依赖和跨层调用」 |
| 引用关系   | ← MASTER.md，→ PATTERNS.md，→ DEPLOYMENT.md |
| 来源映射   | 从 MASTER_SPEC.md §2 + MASTER.md §3-4 + DDD_API_ARCHITECTURE.md 提取 |

> 限制：  
> - ARCHITECTURE.md 不允许重新描述业务规则，只能描述 **“如何在技术上承载业务不变量”**。  

---

### 2.4 DOMAIN.md（需创建索引层）

| 属性       | 定义 |
|------------|------|
| 内容边界   | 领域词汇表（索引）、实体边界（索引）、状态机（引用）、业务规则（引用）、账务/日报/对账/迁移的领域分区导航 |
| 不包含     | 状态机详细定义、字段类型、SQL、账务公式、任何业务规则正文 |
| 目标读者   | 业务分析师、后端开发、AI Agent |
| 执行者角色 | 业务架构师 + DBA 联合维护 |
| AI 提示建议| 「任何业务逻辑实现前，必须在 DOMAIN.md 中找到对应实体/规则编号（BR-xxx / SM-xxx / LEDGER-xxx）」 |
| 引用关系   | ← PROJECT.md，→ STATE_MACHINE.md，→ DATA_SCHEMA.md，→ BUSINESS_RULES.md，→ 各 SOT 文档 |
| 来源映射   | 创建导航层，仅引用现有 SoT，不重写 SoT 内容 |

**DOMAIN.md 下级引用结构（导航索引）：**

```text
DOMAIN.md (导航索引)
├── → STATE_MACHINE.md v2.6       (状态流转详细规则)
├── → DATA_SCHEMA.md v5.2         (数据结构详细定义)
├── → BUSINESS_RULES.md v3.1      (业务规则详细清单)
├── → LEDGER_SOT.md v1.1          (账务领域规则)
├── → DAILY_REPORT_SOT.md v1.0    (日报领域规则)
├── → RECONCILIATION_SOT.md v1.0  (对账领域规则)
└── → TRANSFER_SOT.md v1.0        (迁移领域规则)
硬约束：

DOMAIN.md 只允许出现“指向 SoT 的链接/编号/简短说明”，
不允许包含：

任何完整规则句子

任何状态机图

任何字段说明

一旦需要修改领域规则，必须在对应 SoT 修改，而不是在 DOMAIN.md。

2.5 PATTERNS.md（需整合）
属性	定义
内容边界	正向模式（推荐模式）、反模式（禁止模式）、错误处理模式、命名约定、Result 模式、Service 模式、前后端协作约定
不包含	具体业务规则、API 清单、测试用例、任何账务逻辑
目标读者	后端/前端开发、Code Reviewer、AI Agent
执行者角色	Tech Lead
AI 提示建议	「生成或审查代码前，先对照 PATTERNS.md 的反模式清单，任何命中项必须拒绝提交」
引用关系	← ARCHITECTURE.md，→ TESTING.md
来源映射	从 docs/3.dev-guides/ 整合：DEVELOPMENT_STANDARDS.md、API_RULEBOOK.md、FRONTEND_RULES.md、BACKEND_DEV_GUIDE.md

反模式（示例类型，仅在 PATTERNS.md 中详细列出）：

直接 UPDATE ledger_balance 而不是写 ledger entry

在 Service 中绕过状态机直接改数据

在 Controller 中写业务判断

将 raw/real/final 混用在同一个接口输入输出

PATTERNS.md 的定位是：“写代码时不允许做什么 + 应该采用什么模式替代”，
不是“开发教程”。

2.6 TESTING.md（需扩充）
属性	定义
内容边界	测试策略、覆盖率目标、测试分层（unit / integration / e2e）、Mock 规范、CI 集成点、状态边界测试要求
不包含	具体测试用例代码、业务规则正文
目标读者	QA、后端开发、AI Agent
执行者角色	QA Lead
AI 提示建议	「每个 Service 方法必须至少有一个覆盖正常流 + 一个覆盖状态边界/错误流的测试」
引用关系	← PATTERNS.md，→ DEPLOYMENT.md
来源映射	扩充 TESTING_GUIDE.md，尤其是 状态机与账务事件的测试策略。

2.7 DEPLOYMENT.md（缺失 → 必须新建）
属性	定义
内容边界	CI/CD 流程、环境配置规范、发布策略、回滚流程、监控指标、变更审计要求
不包含	业务逻辑、测试用例、架构设计细节
目标读者	DevOps、SRE、AI Agent
执行者角色	DevOps Lead
AI 提示建议	「任何部署脚本/流水线修改前，必须检查：回滚方案是否与账务不可逆性兼容」
引用关系	← ARCHITECTURE.md，← TESTING.md

关键：回滚锚点设计

应用层可回滚：镜像版本/蓝绿发布/金丝雀。

数据库与账务层禁止回滚历史数据：

不允许回滚到旧账本快照覆盖现有账务。

schema 迁移必须向前兼容，不允许通过回滚 schema 修改历史意义。

回滚流程必须做到：

撤回服务版本，但不改变：

ledger entries

状态机终态记录

审计日志

三、迁移执行计划（按优先级）

> **执行状态**: 全部完成 (2025-11-25)

Phase 1：补齐顶层与缺失骨架（高优先级 / 无破坏） ✅ 100%
任务	输出	执行者	状态
保留 MASTER.md v3.4	已升级至 v3.4	架构师	✅ 完成
保留全部 SoT 文档	无变更	架构师/DBA	✅ 完成
创建 DOMAIN.md 导航层	v1.0 (242行)	文档架构师	✅ 完成
创建 DEPLOYMENT.md 骨架	v1.0 (315行)	DevOps Lead	✅ 完成
创建 PROJECT.md 骨架	v1.2 (442行)	业务架构师	✅ 完成
创建 ARCHITECTURE.md 骨架	v1.0 (345行)	技术架构师	✅ 完成

Phase 2：整合开发规范与测试 ✅ 100%
任务	输出	来源	状态
创建 PATTERNS.md	v1.0 (913行, 37反模式)	docs/3.dev-guides/	✅ 完成
扩充 TESTING.md	v1.0 (462行, 13必测项)	TESTING_GUIDE.md	✅ 完成

Phase 3：全局一致性审查 & Freeze ✅ 100%
任务	输出	优先级	状态
审查 7 文档之间引用关系	引用校验报告	P1	✅ 完成
检查是否存在跨层越权/重复定义	无违规	P1	✅ 完成
标记 ASDD 文档 Freeze 版本	ASDD_Freeze_v1.0	P2	✅ 完成

四、文档引用关系图（更新版）

```
                    ┌─────────────┐
                    │  MASTER.md  │  ← 最高仲裁（宪法）
                    │   (v3.4)    │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
    ┌───────────┐   ┌─────────────┐   ┌────────────┐
    │PROJECT.md │   │ARCHITECTURE │   │  DOMAIN.md │
    │  (v1.2)   │   │   (v1.0)    │   │   (v1.0)   │
    └─────┬─────┘   └──────┬──────┘   └──────┬─────┘
          │                │                  │
          │                │         ┌────────┴────────┐
          │                │         ▼                 ▼
          │                │   ┌───────────┐   ┌───────────────┐
          │                │   │STATE_     │   │ DATA_SCHEMA   │
          │                │   │MACHINE.md │   │    .md        │
          │                │   │ (v2.6) ✅ │   │  (v5.2) ✅    │
          │                │   └───────────┘   └───────────────┘
          │                │         │
          │                │         ▼
          │                │   ┌───────────────┐
          │                │   │BUSINESS_RULES │
          │                │   │     .md       │
          │                │   └───────────────┘
          │                │
          │                ▼
          │         ┌─────────────┐
          │         │ PATTERNS.md │
          │         │   (v1.0)    │
          │         └──────┬──────┘
          │                │
          │                ▼
          │         ┌─────────────┐
          └────────▶│ TESTING.md  │
                    │   (v1.0)    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │DEPLOYMENT.md│
                    │   (v1.0)    │
                    └─────────────┘
```
五、禁止事项 (跨层约束清单)
编号	禁止行为	原因
C-001	在 ASDD 文档中重复书写 SoT 规则正文	避免双源冲突，SoT 为唯一规则源
C-002	为适配 ASDD 而修改 SoT 文档内容	破坏 SoT Freeze，影响账务/状态一致性
C-003	在 PATTERNS.md 中定义业务规则（BR-xxx）	业务规则只允许出现在 BUSINESS_RULES / 相关 SOT
C-004	在 DOMAIN.md 中写任何完整业务规则或字段说明	DOMAIN 仅为索引层，防止规则漂移
C-005	创建超过 500 行的单一文档（除 SoT 外）	保持 ASDD 文档精简、易被 AI/人类理解
C-006	在 DEV_GUIDE / API_SOT 中重新解释账务规则	账务语义必须引用 LEDGER_SOT
C-007	在 DEPLOYMENT 中引入“数据库回滚覆盖现有账务”的方案	违反账务不可逆原则
C-008	任何文档中使用“合理推测/经验补全”替代缺失信息	为 AI 幻觉开门

六、CLAUDE / AI 集成建议（AI 操作宪法）
6.1 查询优先级
MASTER.md → 系统哲学 & 不可变量

DOMAIN.md → 领域导航（找到对应 SOT 规则编号）

ARCHITECTURE.md → 分层与依赖约束

PATTERNS.md → 实现模式与反模式

TESTING.md → 测试规范、覆盖要求

DEPLOYMENT.md → 部署/回滚规范

6.2 AI 强制规则（写进 CLAUDE.md / .claude/skills）
实现任何功能前：

必须检查是否违反 MASTER.md 不可变量。

设计业务逻辑前：

必须在 DOMAIN.md 中找到对应实体/规则编号，并跳转到 SoT 阅读原文。

生成代码前：

必须对照 PATTERNS.md 的反模式清单，命中任意一条则拒绝输出实现代码。

编写测试前：

必须对照 TESTING.md 中的状态边界/账务事件测试要求。

修改部署脚本/流水线时：

必须验证是否与 DEPLOYMENT.md 中的回滚锚点与账务不可逆性冲突。

遇到信息缺失或文档冲突时：

只能输出 Missing: 或 Conflict:，禁止自行补全或调和。