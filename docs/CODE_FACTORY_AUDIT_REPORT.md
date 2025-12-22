# AI 代码工厂合规性审计报告

> **审计标准**: `docs/AI_ANTI_HALLUCINATION_GUARD.md` v1.0
> **审计日期**: 2025-12-22
> **修复完成日期**: 2025-12-22
> **审计范围**: ai-ad-code-factory, ai-ad-be-gen, ai-ad-fe-gen, ai-ad-code-verifier

---

## 1. 审计摘要

| 评级 | 说明 |
|------|------|
| **整体评级** | 🟢 **已修复** - 全部问题已解决 |
| **高危问题** | 5 个 ✅ 已修复 |
| **中危问题** | 4 个 ✅ 已修复 |
| **低危问题** | 3 个 ✅ 已修复 |

### 修复版本汇总

| 文件 | 修复前版本 | 修复后版本 |
|------|-----------|-----------|
| ai-ad-code-factory | v3.0 | v3.2 |
| ai-ad-code-verifier | v2.0 | v2.3 |
| ai-ad-be-gen | v2.2 | v2.3 |
| ai-ad-fe-gen | v2.3 | v2.4 |

---

## 2. 高危问题 (P0 - 必须修复)

### P0-1: 缺少四大模块边界强制检查

**问题描述**:
代码工厂没有强制检查生成的代码属于哪个核心模块（投手/财务/账号/项目），也没有验证写入的表是否在该模块的可写范围内。

**当前代码** (`ai-ad-code-factory/SKILL.md`):
```yaml
scope: "backend" | "frontend" | "fullstack"  # 仅按技术栈划分
```

**违反规则**:
- AI_ANTI_HALLUCINATION_GUARD.md Section 2 "模块边界红线"
- ZT-06: 跨模块写入

**修复方案**:
```yaml
# 新增模块边界配置
module_scope: "pitcher" | "finance" | "ad_account" | "project"

# 在 PromptStructurer 中强制检查
input_contract:
  required:
    module: string  # 必须指定模块
    requirement: string
```

---

### P0-2: 角色列表不一致

**问题描述**:
`ai-ad-code-verifier` 中的合法角色列表与 `AI_ANTI_HALLUCINATION_GUARD.md` 不一致。

**当前代码** (`ai-ad-code-verifier/SKILL.md:395-407`):
```
合法角色 (仅 5 个):
- admin, finance, data_operator, account_manager, media_buyer
```

**正确定义** (`AI_ANTI_HALLUCINATION_GUARD.md`):
```python
USER_ROLE = frozenset(['pitcher', 'account_manager', 'finance', 'supervisor', 'ceo', 'admin'])
```

**差异分析**:
| 当前 | 正确 | 状态 |
|------|------|------|
| admin | admin | ✅ |
| finance | finance | ✅ |
| data_operator | - | ❌ 需删除 |
| account_manager | account_manager | ✅ |
| media_buyer | pitcher | ❌ 名称错误 |
| - | supervisor | ❌ 缺失 |
| - | ceo | ❌ 缺失 |

---

### P0-3: 日报状态机定义不一致

**问题描述**:
验证器中的日报状态与防幻觉护栏文档不一致。

**当前代码** (`ai-ad-code-verifier/SKILL.md:367-382`):
```
合法状态: raw_submitted, trend_pending, trend_ok, trend_flagged,
          trend_resolved, final_pending, final_confirmed, final_locked
```

**正确定义** (`AI_ANTI_HALLUCINATION_GUARD.md`):
```python
REPORT_STATUS = frozenset([
    'DRAFT', 'SUBMITTED', 'PLATFORM_MATCHED',
    'DIFF_FLAGGED', 'CONFIRMED', 'REJECTED', 'REVISED'
])
```

**说明**: 这可能是两套不同的状态机版本，需要确认以哪个为准。

---

### P0-4: 缺少 Ledger 财务规则验证

**问题描述**:
代码验证器没有检查财务模块的核心规则。

**缺失的检查项**:
| 规则 | 当前状态 | 需要添加 |
|------|---------|---------|
| INV-F1: ledger 只能 INSERT | ⚠️ 仅检查 balance 直接修改 | UPDATE/DELETE ledger 检测 |
| INV-F2: CONFIRMED 需 fx_status=LOCKED | ❌ 无 | 状态门禁检查 |
| INV-F3: 一条记录只能冲正一次 | ❌ 无 | 冲正链验证 |
| INV-F4: 期间锁检查 | ❌ 无 | 期间锁前置检查 |
| 金额符号规则 | ❌ 无 | AMOUNT_SIGN_RULES 验证 |

**当前代码仅有** (`ai-ad-code-verifier/SKILL.md:169`):
```
- SOT-008: 直接修改 balance
```

---

### P0-5: BE-Gen/FE-Gen 缺少模块归属判定

**问题描述**:
后端和前端生成器的 THINKING_CHAIN 中没有"模块归属判定"步骤。

**当前代码** (`ai-ad-be-gen/SKILL.md:214-244`):
```xml
<THINKING_CHAIN>
1. SoT 映射
2. 代码规划
3. 代码生成
4. 自检
5. 输出
</THINKING_CHAIN>
```

**缺失步骤**:
```xml
0. 模块归属判定 (新增)
   - 确认任务属于哪个模块 (投手/财务/账号/项目)
   - 验证目标文件在该模块可写范围内
   - 如果跨模块，STOP 并报错
```

---

## 3. 中危问题 (P1 - 应该修复)

### P1-1: Self-Check 清单不完整

**问题描述**:
BE-Gen 和 FE-Gen 的 Self-Check Checklist 缺少管理者一致性自检项。

**当前清单** (`ai-ad-be-gen/SKILL.md:330-339`):
| 检查项 | P0/P1 |
|--------|-------|
| 状态枚举一致性 | P0 |
| 错误码合规 | P0 |
| 字段类型匹配 | P0 |
| 禁区检查 | P0 |
| 权限检查 | P1 |
| 账本规则 | P1 |

**缺失项** (来自 AI_ANTI_HALLUCINATION_GUARD.md Appendix A):
| 检查项 | P0/P1 |
|--------|-------|
| 模块归属确认 | P0 |
| 写入权限在可写范围内 | P0 |
| 金额符号规则 | P0 (财务模块) |
| 跨模块交互检查 | P1 |

---

### P1-2: 缺少可写表白名单

**问题描述**:
BE-Gen 定义了文件边界，但没有定义表级别的写入边界。

**当前代码** (`ai-ad-be-gen/SKILL.md:89-97`):
```yaml
output_boundaries:
  writable:
    - backend/schemas/**
    - backend/services/**
    - backend/routers/**
  forbidden:
    - backend/models/**
    - migrations/**
```

**缺失定义**:
```yaml
# 按模块的可写表边界
module_table_boundaries:
  pitcher:
    writable: [daily_reports, pitchers]
    read_only: [account_ownership_history, ad_accounts, projects]
    forbidden: [ledger, period_locks]
  finance:
    writable: [ledger, period_locks, recon_*]
    read_only: [daily_reports, ad_accounts, agencies]
    forbidden: [pitchers]
  # ...
```

---

### P1-3: 状态值白名单未使用 frozenset

**问题描述**:
验证器中的状态值定义为字符串列表，而非不可变集合。

**当前代码**:
```
合法状态: raw_submitted, trend_pending, ...
```

**推荐做法**:
```python
# 使用 frozenset 确保不可变
REPORT_STATUS = frozenset(['DRAFT', 'SUBMITTED', ...])
```

---

### P1-4: 缺少幻觉抑制最终确认步骤

**问题描述**:
代码生成流程的最后没有"幻觉抑制最终确认"步骤。

**当前流程**:
```
SEARCH → SELECT → ADAPT → ASSEMBLE → VERIFY → 输出
```

**应该添加**:
```
SEARCH → SELECT → ADAPT → ASSEMBLE → VERIFY → 幻觉抑制确认 → 输出
```

---

## 4. 低危问题 (P2 - 可以优化)

### P2-1: 代码来源标注格式不统一

**现状**: 有些用 `# SoT: xxx`，有些用 `# 来源: xxx`

**建议**: 统一为 `# SoT: {DOC}#{SECTION}` 格式

---

### P2-2: 错误码前缀不完整

**当前** (`ai-ad-code-verifier`):
```
VAL, AUTH, BIZ, DB, INT, SYS
```

**推荐补充**:
```
VAL, AUTH, BIZ, DB, INT, SYS, FIN (财务), RPT (日报), ACC (账户)
```

---

### P2-3: 缺少测试覆盖率要求

**现状**: 测试验证是可选的 (`enable_test: false`)

**建议**: 对 P0 功能强制要求测试覆盖

---

## 5. 重构方案

### Phase 1: 紧急修复 (P0)

**任务 1.1: 添加模块边界检查器**
```
文件: .claude/skills/ai-ad-code-factory/module_boundary.py
功能:
- 解析需求，判定目标模块
- 验证写入文件/表是否在可写范围内
- 跨模块写入时抛出 ModuleBoundaryError
```

**任务 1.2: 更新角色/状态白名单**
```
文件: .claude/skills/ai-ad-code-verifier/constants.py
内容:
- USER_ROLE = frozenset(['pitcher', 'account_manager', 'finance', 'supervisor', 'ceo', 'admin'])
- REPORT_STATUS = frozenset(['DRAFT', 'SUBMITTED', 'PLATFORM_MATCHED', 'DIFF_FLAGGED', 'CONFIRMED', 'REJECTED', 'REVISED'])
- LEDGER_STATUS = frozenset(['PENDING', 'APPROVED', 'EXECUTED', 'CONFIRMED', 'REJECTED'])
```

**任务 1.3: 添加 Ledger 财务规则验证**
```
文件: .claude/skills/ai-ad-code-verifier/finance_rules_verifier.py
功能:
- 检测 UPDATE/DELETE ledger 语句
- 验证 CONFIRM 前的 fx_status 检查
- 验证冲正链完整性
- 验证金额符号规则
```

**任务 1.4: 修改 BE-Gen/FE-Gen THINKING_CHAIN**
```
新增 Step 0: 模块归属判定
- 确认任务属于哪个模块
- 验证目标文件在可写范围内
- 如果无法确定，STOP 并询问
```

### Phase 2: 增强检查 (P1)

**任务 2.1: 完善 Self-Check Checklist**
- 添加模块归属确认
- 添加写入权限检查
- 添加金额符号规则检查
- 添加跨模块交互检查

**任务 2.2: 添加表级别边界定义**
- 在 BE-Gen 中添加 module_table_boundaries
- 在 FE-Gen 中添加模块级 API 边界

**任务 2.3: 添加幻觉抑制最终确认**
- 在 VERIFY 后添加确认步骤
- 输出前进行最终自检

### Phase 3: 优化完善 (P2)

**任务 3.1: 统一代码来源标注格式**
**任务 3.2: 完善错误码前缀**
**任务 3.3: 强制关键功能测试覆盖**

---

## 6. 文件修改清单

| 文件 | 修改类型 | 优先级 |
|------|---------|--------|
| `.claude/skills/ai-ad-code-factory/SKILL.md` | 添加模块边界检查 | P0 |
| `.claude/skills/ai-ad-code-verifier/SKILL.md` | 更新角色/状态白名单 | P0 |
| `.claude/skills/ai-ad-code-verifier/SKILL.md` | 添加财务规则验证 | P0 |
| `.claude/skills/ai-ad-be-gen/SKILL.md` | 添加模块归属判定步骤 | P0 |
| `.claude/skills/ai-ad-fe-gen/SKILL.md` | 添加模块归属判定步骤 | P0 |
| `.claude/skills/ai-ad-be-gen/SKILL.md` | 完善 Self-Check | P1 |
| `.claude/skills/ai-ad-fe-gen/SKILL.md` | 完善 Self-Check | P1 |

---

## 7. 验收标准

重构完成后，AI 代码工厂必须满足：

1. **模块边界**: 生成的代码只能写入所属模块的可写表/文件
2. **状态合规**: 生成的状态值必须在白名单内
3. **角色合规**: 生成的角色必须在 6 个合法角色内
4. **财务规则**: 涉及 ledger 的代码必须通过财务规则验证
5. **自检通过**: 所有生成的代码必须通过管理者一致性自检清单

---

## 8. 修复完成记录 (2025-12-22)

### P0 修复 (高危)

| 问题 ID | 问题描述 | 修复措施 | 状态 |
|---------|---------|---------|------|
| P0-1 | 缺少四大模块边界检查 | 添加 `module` 必填参数 + 边界定义 | ✅ |
| P0-2 | 角色列表不一致 | 更新为 6 个角色 frozenset | ✅ |
| P0-3 | 日报状态机不一致 | 统一为 7 状态 frozenset | ✅ |
| P0-4 | 缺少 Ledger 财务规则验证 | 新增 Layer 3.5 + FIN 错误码 | ✅ |
| P0-5 | 缺少模块归属判定 | 添加 Step 0 到 THINKING_CHAIN | ✅ |

### P1 修复 (中危)

| 问题 ID | 问题描述 | 修复措施 | 状态 |
|---------|---------|---------|------|
| P1-1 | Self-Check 清单不完整 | 添加跨模块交互检查 + 幻觉抑制确认 | ✅ |
| P1-2 | 缺少可写表白名单 | 添加 module_table_boundaries | ✅ |
| P1-3 | 状态值未用 frozenset | 已在 P0 中完成 | ✅ |
| P1-4 | 缺少幻觉抑制最终确认 | 添加 Phase 6 CONFIRM + Layer 6 | ✅ |

### P2 修复 (低危)

| 问题 ID | 问题描述 | 修复措施 | 状态 |
|---------|---------|---------|------|
| P2-1 | 来源标注格式不统一 | 统一为 `# SoT: {DOC}#{SECTION}` | ✅ |
| P2-2 | 错误码前缀不完整 | 扩展为 16 个前缀 | ✅ |
| P2-3 | 缺少测试覆盖率要求 | 添加 P0 功能测试要求 | ✅ |

### 关键改进

1. **6 阶段工厂流水线**: SEARCH → SELECT → ADAPT → ASSEMBLE → VERIFY → CONFIRM
2. **8 层验证流水线**: 包含模块边界、财务规则、幻觉抑制等层
3. **16 个错误码前缀**: 通用 6 + 模块专用 10
4. **统一来源标注**: `# SoT: {DOC}#{SECTION}`
5. **P0 功能强制测试**: 状态机、财务、权限必须 100% 覆盖

---

**审计人**: Claude Code
**审计标准**: AI_ANTI_HALLUCINATION_GUARD.md v1.0
**修复确认**: 2025-12-22 全部 12 个问题已修复
