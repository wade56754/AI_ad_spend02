# 开发流程真相源 (DEV_FLOW_SOT)

> **版本**: v1.1
> **状态**: active
> **层级**: SoT (Layer 2)
> **Owner**: wade
> **创建日期**: 2025-12-07
> **更新日期**: 2025-12-07
> **Baseline**: AI_CODE_FACTORY_DEV_GUIDE_v2.4, SoT Freeze v2.6

---

## 1. 文档定位

本文档定义 AI 代码工厂的 **标准开发流程 (Development Flows)**，是所有自动化代码生成、审查、测试的流程真相源。

### 1.1 与其他 SoT 的关系

```
┌─────────────────────────────────────────────────────────────────┐
│                    SoT 层级关系                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STATE_MACHINE.md ─┬─→ 状态流转规则                              │
│  DATA_SCHEMA.md ───┼─→ 字段定义                                  │
│  BUSINESS_RULES.md ┼─→ 业务规则                                  │
│  API_SOT.md ───────┼─→ API 契约                                  │
│  ERROR_CODES_SOT.md┴─→ 错误码                                    │
│                    │                                             │
│                    ▼                                             │
│  DEV_FLOW_SOT.md ────→ 开发流程规范 (本文档)                     │
│                    │                                             │
│                    ▼                                             │
│  .claude/skills/** ──→ Skill 实现                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 核心原则

| 原则 | 说明 |
|------|------|
| **SoT 优先** | 任何流程的第一步必须是 SoT 对齐检查 |
| **命令驱动** | 所有流程通过 `/sot-check`、`/gen`、`/review`、`/doc` 组合实现 |
| **可追溯** | 每个流程产出必须可追溯到 SoT 规则 |
| **人工确认** | 代码提交前必须人工确认 |

---

## 2. 命令体系

### 2.1 核心命令

| 命令 | 职责 | 触发的 Skill |
|------|------|-------------|
| `/sot-check <file>` | SoT 合规检查 | ai-ad-spec-governor |
| `/gen be <task>` | 后端代码生成 | ai-ad-be-gen |
| `/gen fe <task>` | 前端代码生成 | ai-ad-fe-gen |
| `/gen test <task>` | 测试代码生成 | ai-ad-test-gen |
| `/review <file>` | 代码审查 | ai-master-architect |
| `/doc [dir]` | 文档审计 | ai-doc-system-auditor |

### 2.2 命令执行约束

```
┌─────────────────────────────────────────────────────────────────┐
│                    命令执行约束                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. 命令由用户在 Claude Code 中手动触发                          │
│  2. 命令不支持管道串联 (&&)，必须逐条执行                        │
│  3. 每个命令执行后需确认结果再执行下一步                         │
│  4. 遇到 P0 问题必须先修复再继续                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 标准开发流程 (7 大 Flow)

### 3.1 Flow 总览

| Flow ID | 名称 | 适用场景 | 复杂度 | 命令 |
|---------|------|----------|--------|------|
| BE_DEV_FLOW | 后端开发流程 | 新增后端模块/功能 | 高 | `/dev-flow be` |
| FE_DEV_FLOW | 前端开发流程 | 新增页面/组件 | 中 | `/dev-flow fe` |
| API_FIX_FLOW | 接口修复流程 | 单接口 Bug 修复 | 低 | `/dev-flow fix` |
| TEST_HARDEN_FLOW | 测试加固流程 | 测试补齐/回归 | 中 | `/dev-flow test` |
| DOC_FREEZE_FLOW | 文档冻结流程 | 文档治理/冻结报告 | 低 | `/dev-flow doc` |
| REFACTOR_FLOW | 代码重构流程 | 不改业务的重构 | 中 | `/dev-flow refactor` |
| FULL_FLOW | 完整功能开发 | 端到端功能交付 | 高 | `/dev-flow full` |

### 3.2 Flow 选择决策树

```
                    ┌─────────────────┐
                    │   任务类型？     │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │ 新功能？  │      │ Bug修复？ │      │ 文档？   │
    └────┬─────┘      └────┬─────┘      └────┬─────┘
         │                 │                 │
    ┌────┴────┐           │                 ▼
    │         │           │          DOC_FREEZE_FLOW
    ▼         ▼           │
 后端？    前端？         │
    │         │           │
    ▼         ▼           ▼
BE_DEV    FE_DEV    ┌──────────┐
_FLOW     _FLOW     │ 涉及测试？│
                    └────┬─────┘
                         │
                    ┌────┴────┐
                    │         │
                    ▼         ▼
              API_FIX    TEST_HARDEN
              _FLOW      _FLOW
```

---

## 4. BE_DEV_FLOW (后端开发流程)

### 4.1 适用场景

- 新增后端模块 (如: topup_service, reconciliation_service)
- 新增 API 端点 (如: POST /api/v1/reports/export)
- 新增业务逻辑 (如: 状态机流转、账本分录)

### 4.2 流程步骤

```
┌─────────────────────────────────────────────────────────────────┐
│                    BE_DEV_FLOW (6 步)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: SoT 对齐                                                │
│  ────────────────                                                │
│  命令: /sot-check docs/2.sot/                                    │
│  目的: 确认相关 SoT 规则，识别状态机/字段/业务规则               │
│  产出: SoT 规则清单 + 依赖关系                                   │
│                                                                  │
│  Step 2: Schema 层生成                                           │
│  ────────────────────                                            │
│  命令: /gen be "生成 {module} 的 Pydantic Schema"                │
│  目的: 生成请求/响应模型、枚举定义                               │
│  产出: backend/schemas/{module}.py                               │
│                                                                  │
│  Step 3: Service 层生成                                          │
│  ────────────────────                                            │
│  命令: /gen be "实现 {module} 的业务逻辑"                        │
│  目的: 实现核心业务函数，含状态机验证、账本操作                  │
│  产出: backend/services/{module}_service.py                      │
│                                                                  │
│  Step 4: Router 层生成                                           │
│  ────────────────────                                            │
│  命令: /gen be "创建 {module} 的 API 端点"                       │
│  目的: 定义 FastAPI 路由，注入依赖，异常处理                     │
│  产出: backend/routers/{module}.py                               │
│                                                                  │
│  Step 5: 测试生成                                                │
│  ────────────────                                                │
│  命令: /gen test "为 {module} 生成状态机和 API 测试"             │
│  目的: 生成 Service 层测试 + API 层测试                          │
│  产出: backend/tests/services/test_{module}_service.py           │
│         backend/tests/api/test_{module}_api.py                   │
│                                                                  │
│  Step 6: 代码审查                                                │
│  ────────────────                                                │
│  命令: /review backend/services/{module}_service.py              │
│  目的: SoT 合规检查 + 代码质量审查                               │
│  产出: 审查报告 (P0/P1/P2 问题清单)                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Prompt 模板

```yaml
# Step 1: SoT 对齐
prompt: |
  检查 {module} 相关的 SoT 规则：
  - STATE_MACHINE.md: 查找 {entity} 的状态定义
  - DATA_SCHEMA.md: 查找 {entity} 的字段定义
  - BUSINESS_RULES.md: 查找 BR-{prefix}-* 规则
  - API_SOT.md: 查找相关 API 契约

# Step 2: Schema 生成
prompt: |
  为 {module} 生成 Pydantic Schema：
  - 状态枚举必须对齐 STATE_MACHINE.md
  - 字段命名必须对齐 DATA_SCHEMA.md
  - 包含请求模型、响应模型、分页结构

# Step 3: Service 生成
prompt: |
  实现 {module} 的 Service 层：
  - 业务函数签名符合 API_SOT.md
  - 状态流转验证符合 STATE_MACHINE.md
  - 错误码使用 ERROR_CODES_SOT.md 定义
  - 账本操作符合 LEDGER_SOT.md（如适用）

# Step 4: Router 生成
prompt: |
  创建 {module} 的 FastAPI Router：
  - 端点路径符合 API_SOT.md
  - 权限检查符合 AUTH_SPEC.md
  - 异常映射到正确的 HTTP 状态码

# Step 5: 测试生成
prompt: |
  为 {module} 生成测试用例：
  - 状态机测试: 覆盖所有合法流转 + 非法流转
  - API 测试: 正向路径 + 权限校验 + 错误场景
  - 账本测试: 分录正确性（如适用）

# Step 6: 代码审查
prompt: |
  审查 {module} 代码：
  - P0: 状态枚举一致性、错误码合规、权限检查
  - P1: 字段命名、API 契约、类型注解
  - P2: 代码风格、复杂度
```

### 4.4 本地测试命令

```bash
# 运行模块测试
pytest backend/tests/services/test_{module}_service.py -v
pytest backend/tests/api/test_{module}_api.py -v

# 类型检查
mypy backend/services/{module}_service.py

# 代码风格
ruff check backend/services/{module}_service.py
black --check backend/services/{module}_service.py
```

### 4.5 Freeze 报告模板

```markdown
# {Module} 模块实现报告

## 1. 概述
- 模块: {module}
- 实现日期: YYYY-MM-DD
- 开发者: xxx

## 2. SoT 对齐
- STATE_MACHINE.md v2.6: 状态 {states}
- DATA_SCHEMA.md v5.2: 字段 {fields}
- BUSINESS_RULES.md v3.2: 规则 {rules}

## 3. 变更清单
| 文件 | 变更类型 | 说明 |
|------|----------|------|
| backend/schemas/{module}.py | 新增 | ... |
| backend/services/{module}_service.py | 新增 | ... |
| backend/routers/{module}.py | 新增 | ... |

## 4. 测试覆盖
- 状态机测试: X 个用例，覆盖 Y 个状态
- API 测试: X 个用例
- 通过率: 100%

## 5. 审查结果
- P0: 0
- P1: 0
- P2: N (已记录)
```

---

## 5. FE_DEV_FLOW (前端开发流程)

### 5.1 适用场景

- 新增页面 (如: 日报列表页、充值审批页)
- 新增组件 (如: 状态徽章、数据表格)
- 新增 Hook (如: useReportList, useTopupApproval)

### 5.2 流程步骤

```
┌─────────────────────────────────────────────────────────────────┐
│                    FE_DEV_FLOW (5 步)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: SoT 对齐                                                │
│  ────────────────                                                │
│  命令: /sot-check docs/2.sot/API_SOT.md                          │
│  目的: 确认 API 契约、状态枚举、字段定义                         │
│  产出: API 端点清单 + 数据结构                                   │
│                                                                  │
│  Step 2: API Client 生成                                         │
│  ────────────────────                                            │
│  命令: /gen fe "生成 {module} 的 API Client"                     │
│  目的: 生成类型安全的 API 调用封装                               │
│  产出: frontend/src/lib/api/{module}.ts                          │
│                                                                  │
│  Step 3: 组件/页面生成                                           │
│  ────────────────────                                            │
│  命令: /gen fe "创建 {page/component} 页面/组件"                 │
│  目的: 生成 React 组件，含状态管理、数据获取                     │
│  产出: frontend/src/modules/{module}/                            │
│                                                                  │
│  Step 4: 测试生成                                                │
│  ────────────────                                                │
│  命令: /gen test "为 {component} 生成前端测试"                   │
│  目的: 生成组件测试 + Hook 测试                                  │
│  产出: frontend/tests/{module}/                                  │
│                                                                  │
│  Step 5: 代码审查                                                │
│  ────────────────                                                │
│  命令: /review frontend/src/modules/{module}/                    │
│  目的: 类型检查 + API 契约验证                                   │
│  产出: 审查报告                                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 本地测试命令

```bash
# TypeScript 编译
cd frontend && npm run type-check

# ESLint 检查
npm run lint

# 组件测试
npm run test -- --testPathPattern={module}

# 构建验证
npm run build
```

---

## 6. API_FIX_FLOW (接口修复流程)

### 6.1 适用场景

- 单个 API 返回数据错误
- API 状态码不正确
- API 权限检查缺失
- API 参数验证不足

### 6.2 流程步骤

```
┌─────────────────────────────────────────────────────────────────┐
│                    API_FIX_FLOW (4 步)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: 问题定位                                                │
│  ────────────────                                                │
│  命令: /sot-check backend/routers/{file}.py                      │
│  目的: 对比 API_SOT.md，识别偏差点                               │
│  产出: 问题清单 + SoT 规则引用                                   │
│                                                                  │
│  Step 2: 修复生成                                                │
│  ────────────────                                                │
│  命令: /gen be "修复 {api_endpoint} 的 {问题描述}"               │
│  目的: 生成修复代码                                              │
│  产出: 修改后的 Router/Service 代码                              │
│                                                                  │
│  Step 3: 回归测试                                                │
│  ────────────────                                                │
│  命令: /gen test "为 {api_endpoint} 生成回归测试"                │
│  目的: 确保修复不引入新问题                                      │
│  产出: 回归测试用例                                              │
│                                                                  │
│  Step 4: 验证审查                                                │
│  ────────────────                                                │
│  命令: /review backend/routers/{file}.py                         │
│  目的: 确认修复符合 SoT                                          │
│  产出: 审查报告                                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.3 本地测试命令

```bash
# 运行相关测试
pytest backend/tests/api/test_{module}_api.py::{test_case} -v

# 快速验证
pytest backend/tests/ -k "{keyword}" --tb=short
```

---

## 7. TEST_HARDEN_FLOW (测试加固流程)

### 7.1 适用场景

- 状态机测试覆盖不足
- 账本测试缺失
- 边界条件测试不全
- 回归测试补充

### 7.2 流程步骤

```
┌─────────────────────────────────────────────────────────────────┐
│                    TEST_HARDEN_FLOW (4 步)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: 覆盖分析                                                │
│  ────────────────                                                │
│  命令: /sot-check backend/tests/                                 │
│  目的: 分析当前测试覆盖，识别缺口                                │
│  产出: 测试缺口清单                                              │
│                                                                  │
│  Step 2: 状态机测试                                              │
│  ────────────────                                                │
│  命令: /gen test "补齐 {entity} 状态机测试"                      │
│  目的: 覆盖所有状态流转路径                                      │
│  产出: 状态机测试用例                                            │
│                                                                  │
│  Step 3: 边界测试                                                │
│  ────────────────                                                │
│  命令: /gen test "补齐 {module} 边界条件测试"                    │
│  目的: 覆盖异常输入、权限边界、并发场景                          │
│  产出: 边界测试用例                                              │
│                                                                  │
│  Step 4: 覆盖验证                                                │
│  ────────────────                                                │
│  命令: /review backend/tests/                                    │
│  目的: 确认测试质量和覆盖率                                      │
│  产出: 测试审查报告                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.3 本地测试命令

```bash
# 运行全量测试
pytest backend/tests/ -v

# 覆盖率报告
pytest backend/tests/ --cov=backend --cov-report=html

# 状态机专项测试
pytest backend/tests/ -k "state" -v
```

---

## 8. DOC_FREEZE_FLOW (文档冻结流程)

### 8.1 适用场景

- 模块开发完成后的文档冻结
- SoT 文档审计
- 版本发布前的文档治理

### 8.2 流程步骤

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOC_FREEZE_FLOW (3 步)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: 文档审计                                                │
│  ────────────────                                                │
│  命令: /doc docs/                                                │
│  目的: 扫描文档体系，识别 P0/P1/P2 问题                          │
│  产出: 文档审计报告                                              │
│                                                                  │
│  Step 2: SoT 一致性检查                                          │
│  ────────────────────                                            │
│  命令: /sot-check docs/2.sot/                                    │
│  目的: 验证 SoT 文档间的交叉引用一致性                           │
│  产出: SoT 一致性报告                                            │
│                                                                  │
│  Step 3: Freeze 报告生成                                         │
│  ────────────────────                                            │
│  命令: /doc --freeze {module}                                    │
│  目的: 生成冻结报告，标记文档版本                                │
│  产出: docs/reports/{module}_FREEZE_REPORT.md                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 8.3 Freeze 报告模板

```markdown
# {Module} 冻结报告

## 元信息
- 冻结日期: YYYY-MM-DD
- 冻结版本: vX.Y
- 审核人: xxx

## 文档清单
| 文档 | 版本 | 状态 |
|------|------|------|
| STATE_MACHINE.md | v2.6 | frozen |
| DATA_SCHEMA.md | v5.2 | frozen |

## 审计结果
- P0: 0
- P1: 0
- P2: N (已记录)

## 冻结声明
本模块文档已冻结，任何修改需走 RFC 流程。
```

---

## 9. REFACTOR_FLOW (代码重构流程)

### 9.1 适用场景

- 代码结构优化 (如: 拆分大函数、提取公共模块)
- 代码去重复 (如: 合并重复逻辑、抽取公共组件)
- 性能调优 (如: 查询优化、缓存引入)
- 技术债偿还 (如: 升级依赖、替换废弃 API)

### 9.2 约束条件 (CRITICAL)

```
┌─────────────────────────────────────────────────────────────────┐
│                    REFACTOR_FLOW 强制约束                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  🔴 不得改变业务行为                                             │
│  ────────────────────                                            │
│  - 输入/输出契约必须保持不变                                    │
│  - 状态机流转逻辑不得修改                                       │
│  - API 端点签名不得改变                                         │
│  - 错误码返回值不得改变                                         │
│                                                                  │
│  🔴 不得修改 SoT 定义                                           │
│  ────────────────────                                            │
│  - 若发现 SoT 有问题，应先走 SoT 变更流程 (RFC)                 │
│  - 禁止在重构中"顺便"调整 SoT                                   │
│                                                                  │
│  ✅ 允许的改动                                                   │
│  ────────────────                                                │
│  - 内部实现逻辑重组                                             │
│  - 代码结构调整 (拆分/合并文件)                                 │
│  - 变量/函数重命名 (保持 API 兼容)                              │
│  - 性能优化 (保持功能等价)                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.3 入口条件

| 条件 | 说明 |
|------|------|
| 测试覆盖 | 目标模块测试覆盖率 ≥ 80% |
| CI 通过 | 当前 main 分支 CI 绿色 |
| SoT 稳定 | 相关 SoT 文档处于 frozen 状态 |
| 无阻断问题 | 无 P0 级 Bug 待修复 |

### 9.4 退出条件

| 条件 | 说明 |
|------|------|
| 测试全绿 | 所有现有测试通过 (不新增测试) |
| 行为等价 | API 响应与重构前完全一致 |
| SoT 合规 | `/sot-check` 无新增 P0/P1 |
| 审查通过 | `/review` 通过 |

### 9.5 流程步骤

```
┌─────────────────────────────────────────────────────────────────┐
│                    REFACTOR_FLOW (5 步)                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: 快照基线                                                │
│  ────────────────                                                │
│  命令: pytest backend/tests/ --tb=short (保存通过用例清单)      │
│  目的: 建立行为基线，用于验证重构后等价性                       │
│  产出: 测试快照 + API 响应样本                                   │
│                                                                  │
│  Step 2: SoT 对齐检查                                            │
│  ────────────────────                                            │
│  命令: /sot-check {target_files}                                 │
│  目的: 确认当前代码已符合 SoT，识别技术债                       │
│  产出: SoT 合规报告 + 技术债清单                                 │
│                                                                  │
│  Step 3: 代码分析                                                │
│  ────────────────                                                │
│  命令: /review {target_files}                                    │
│  目的: 识别可重构点 (复杂度、重复、性能瓶颈)                    │
│  产出: 重构建议清单                                              │
│                                                                  │
│  Step 4: 重构实施                                                │
│  ────────────────                                                │
│  命令: /gen be "重构 {module} 的 {重构目标}"                    │
│  目的: 执行重构，保持行为等价                                   │
│  产出: 重构后的代码                                              │
│                                                                  │
│  Step 5: 等价验证                                                │
│  ────────────────                                                │
│  命令: /sot-check {target_files} + pytest (对比快照)            │
│  目的: 确认重构后行为与基线一致                                 │
│  产出: 等价性验证报告                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.6 本地验证命令

```bash
# Step 1: 建立基线
pytest backend/tests/ -v > refactor_baseline.txt

# Step 4: 重构后回归
pytest backend/tests/ -v > refactor_after.txt

# Step 5: 对比验证
diff refactor_baseline.txt refactor_after.txt
```

---

## 10. FULL_FLOW (完整功能开发流程)

### 10.1 定义

FULL_FLOW 是标准 Flow 的组合模式，用于端到端的完整功能开发。

### 10.2 组合序列

```
┌─────────────────────────────────────────────────────────────────┐
│                    FULL_FLOW 组合序列                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Phase 1: 后端开发                                               │
│  ────────────────                                                │
│  执行: BE_DEV_FLOW (完整 6 步)                                  │
│  产出: Schema + Service + Router + 后端测试                     │
│                                                                  │
│  Phase 2: 前端开发                                               │
│  ────────────────                                                │
│  执行: FE_DEV_FLOW (完整 5 步)                                  │
│  产出: API Client + 页面/组件 + 前端测试                        │
│                                                                  │
│  Phase 3: 测试加固                                               │
│  ────────────────                                                │
│  执行: TEST_HARDEN_FLOW (完整 4 步)                             │
│  产出: 状态机测试 + 边界测试 + 覆盖率报告                       │
│                                                                  │
│  Phase 4: 文档冻结                                               │
│  ────────────────                                                │
│  执行: DOC_FREEZE_FLOW (完整 3 步)                              │
│  产出: 文档审计报告 + Freeze 报告                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.3 流程图

```
BE_DEV_FLOW → FE_DEV_FLOW → TEST_HARDEN_FLOW → DOC_FREEZE_FLOW
    │              │               │                  │
    ▼              ▼               ▼                  ▼
 后端代码       前端代码        测试覆盖          文档冻结
```

### 10.4 适用场景

- 新模块开发 (如: 充值模块、对账模块)
- 大型功能需求 (涉及前后端联调)
- MVP 功能交付

### 10.5 其他常用组合

| 组合名称 | 序列 | 适用场景 |
|----------|------|----------|
| 后端专项 | BE_DEV_FLOW | 仅后端改动 |
| 前端专项 | FE_DEV_FLOW | 仅前端改动 |
| 快速修复 | API_FIX_FLOW → TEST_HARDEN_FLOW | 单接口 Bug |
| 文档治理 | DOC_FREEZE_FLOW | 文档审计/冻结 |
| 代码重构 | REFACTOR_FLOW | 不改业务的重构 |

---

## 11. 命令映射表

### 11.1 `/dev-flow` 命令映射

| 命令 | 触发的 Flow | 说明 |
|------|-------------|------|
| `/dev-flow be <task>` | BE_DEV_FLOW | 后端功能开发 |
| `/dev-flow fe <task>` | FE_DEV_FLOW | 前端功能开发 |
| `/dev-flow fix <task>` | API_FIX_FLOW | 接口 Bug 修复 |
| `/dev-flow test <task>` | TEST_HARDEN_FLOW | 测试加固 |
| `/dev-flow doc [dir]` | DOC_FREEZE_FLOW | 文档审计/冻结 |
| `/dev-flow full <task>` | FULL_FLOW | 完整功能开发 |
| `/dev-flow refactor <task>` | REFACTOR_FLOW | 代码重构 |

### 11.2 Flow 与核心命令映射

| Flow | Step 1 | Step 2 | Step 3 | Step 4 | Step 5 | Step 6 |
|------|--------|--------|--------|--------|--------|--------|
| BE_DEV_FLOW | /sot-check | /gen be | /gen be | /gen be | /gen test | /review |
| FE_DEV_FLOW | /sot-check | /gen fe | /gen fe | /gen test | /review | - |
| API_FIX_FLOW | /sot-check | /gen be | /gen test | /review | - | - |
| TEST_HARDEN_FLOW | /sot-check | /gen test | /gen test | /review | - | - |
| DOC_FREEZE_FLOW | /doc | /sot-check | /doc --freeze | - | - | - |
| REFACTOR_FLOW | pytest | /sot-check | /review | /gen be | /sot-check | - |

---

## 12. 历史命名对照表

> ⚠️ 以下命名已废弃，请使用新命名。

| 旧命名 | 新命名 | 说明 |
|--------|--------|------|
| `/dev-flow feature` | `/dev-flow be` 或 `/dev-flow full` | 按范围选择 |
| `/dev-flow bugfix` | `/dev-flow fix` | 统一简写 |
| `/dev-flow docs` | `/dev-flow doc` | 统一简写 |
| `be_only` | `/dev-flow be` | Legacy Agent 命名 |
| `be_then_test` | `/dev-flow be` (已包含测试) | Legacy Agent 命名 |
| `full_pipeline` | `/dev-flow full` | Legacy Agent 命名 |

---

## 13. 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.1 | 2025-12-07 | 新增 REFACTOR_FLOW、FULL_FLOW；新增命令映射表、历史命名对照表 |
| v1.0 | 2025-12-07 | 初始版本，定义 5 大开发流程 |
