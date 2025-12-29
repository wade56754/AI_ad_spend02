# AI 开发工作流 v2.0

> **版本**: v2.0
> **基准文档**: docs/guides/AI_PROGRAMMING_SOP.md v1.0
> **适用场景**: 每个功能开发任务
> **关键依赖**: CLAUDE.md + memory-bank + AI 代码工厂

---

## 0. 工作流总览

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        每次新对话的完整工作流                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                    Step 0: 自动加载 (Claude 自动执行)                 │  │
│   │                                                                     │  │
│   │   CLAUDE.md (自动注入)                                              │  │
│   │   ├── SoT 版本: MASTER.md v4.6 | DATA_SCHEMA.md v5.6 | ...         │  │
│   │   ├── 6 角色白名单 (无 supervisor)                                  │  │
│   │   ├── Phase 1 约束 (只提示不阻断)                                   │  │
│   │   ├── 5 个不变量                                                    │  │
│   │   └── AI 防幻觉原则 (AH-01 ~ AH-05)                                 │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                     ↓                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                    Step 1: 读取 memory-bank                          │  │
│   │                                                                     │  │
│   │   用户提示词:                                                       │  │
│   │   "阅读 /memory-bank 所有文档，                                     │  │
│   │    阅读 progress.md 了解之前进度，                                  │  │
│   │    然后继续实施计划第 3 步"                                         │  │
│   │                                                                     │  │
│   │   AI 读取:                                                          │  │
│   │   ├── game-design-document.md  → 理解需求                           │  │
│   │   ├── tech-stack.md           → 知道技术栈                          │  │
│   │   ├── architecture.md         → 知道每个文件的作用                  │  │
│   │   ├── implementation-plan.md  → 知道第 N 步要做什么                 │  │
│   │   ├── progress.md             → 知道第 1~N-1 步已完成               │  │
│   │   ├── dev-workflow.md         → 知道开发流程                        │  │
│   │   └── quick-reference.md      → 速查角色/状态/错误码                │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                     ↓                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                    Step 2: 确认任务卡                                 │  │
│   │                                                                     │  │
│   │   从 implementation-plan.md 获取当前任务:                           │  │
│   │   ├── 任务卡 ID: TASK-RPT-001                                       │  │
│   │   ├── 描述: 日报创建 API                                            │  │
│   │   ├── 依赖: M5 账户模块 (已完成)                                    │  │
│   │   └── 验收标准: 见任务卡                                            │  │
│   │                                                                     │  │
│   │   查阅 SoT 文档:                                                    │  │
│   │   ├── docs/sot/BUSINESS_RULES.md → BR-RPT-*                         │  │
│   │   ├── docs/sot/STATE_MACHINE.md → 日报状态机                        │  │
│   │   └── docs/sot/DATA_SCHEMA.md → daily_reports 表                    │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                     ↓                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                    Step 3: 调用 AI 代码工厂                          │  │
│   │                                                                     │  │
│   │   使用方式 (Claude Code):                                           │  │
│   │   「                                                                │  │
│   │   使用 ai-ad-code-factory，                                         │  │
│   │   requirement = "添加日报创建 API"，                                │  │
│   │   module = "pitcher"                                                │  │
│   │   」                                                                │  │
│   │                                                                     │  │
│   │   6 阶段流水线:                                                     │  │
│   │   ┌────────┐  ┌────────┐  ┌───────┐  ┌──────────┐  ┌────────┐  ┌─────────┐  │
│   │   │ SEARCH │→│ SELECT │→│ ADAPT │→│ ASSEMBLE │→│ VERIFY │→│ CONFIRM │  │
│   │   └────────┘  └────────┘  └───────┘  └──────────┘  └────────┘  └─────────┘  │
│   │      搜索       选型       适配        组装         验证       防幻觉确认  │
│   │                                                                     │  │
│   │   输出:                                                             │  │
│   │   ├── 可用代码文件 (标注 SoT 来源)                                  │  │
│   │   ├── 集成指南                                                      │  │
│   │   └── 来源追溯报告                                                  │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                     ↓                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                    Step 4: 验证与测试                                 │  │
│   │                                                                     │  │
│   │   质量门禁:                                                         │  │
│   │   ├── ruff check backend/          → Lint 通过                      │  │
│   │   ├── pytest tests/xxx -v          → 测试通过                       │  │
│   │   ├── grep -r "supervisor" backend/ → 无结果 (6角色检查)            │  │
│   │   └── SoT 来源标注检查              → 所有代码有标注                │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                     ↓                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                    Step 5: 更新 memory-bank + 提交                   │  │
│   │                                                                     │  │
│   │   更新 progress.md:                                                 │  │
│   │   ├── 标记 TASK-RPT-001 为 ✅ 完成                                  │  │
│   │   └── 记录完成日期和备注                                            │  │
│   │                                                                     │  │
│   │   更新 architecture.md (如有新文件):                                │  │
│   │   └── 添加新文件的说明                                              │  │
│   │                                                                     │  │
│   │   Git 提交:                                                         │  │
│   │   git add .                                                         │  │
│   │   git commit -m "feat(daily-reports): 添加日报创建 API              │  │
│   │                                                                     │  │
│   │   - 实现 POST /daily-reports 端点                                   │  │
│   │   - 关联规则: BR-RPT-001                                            │  │
│   │   - 测试覆盖: 85%                                                   │  │
│   │                                                                     │  │
│   │   Co-Authored-By: Claude <noreply@anthropic.com>"                   │  │
│   │                                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                     ↓                                       │
│                        新建聊天 → 执行第 N+1 步                             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. CLAUDE.md 自动加载

> Claude Code 启动时自动读取 CLAUDE.md，注入以下约束

### 自动注入的约束

| 约束类型 | 内容 | 来源 |
|----------|------|------|
| SoT 版本 | MASTER.md v4.6, DATA_SCHEMA.md v5.6, ... | CLAUDE.md |
| 角色白名单 | 6 个角色，无 supervisor | MASTER.md v4.6 §2.4 |
| Phase 1 原则 | 只提示、不阻断、不自动问责 | CLAUDE.md |
| 不变量 | 5 个绝对不能违反的规则 | CLAUDE.md |
| 防幻觉原则 | AH-01 ~ AH-05 | MASTER.md v4.6 §7 |

### CLAUDE.md 关键内容

```markdown
## 强制规则 (MANDATORY)

### 写任何代码前必须
1. **完整阅读** `memory-bank/architecture.md` - 了解项目结构
2. **完整阅读** `memory-bank/game-design-document.md` - 了解需求
3. **查阅对应 SoT** - 不允许凭想象实现任何功能

### 每完成一个功能后必须
1. **更新** `memory-bank/progress.md` - 记录完成状态
2. **更新** `memory-bank/architecture.md` - 如有新文件/模块
```

---

## 2. memory-bank 文档用途

| 文档 | 用途 | 每次必读? |
|------|------|-----------|
| `game-design-document.md` | 需求/PRD - 做什么 | ✅ |
| `tech-stack.md` | 技术栈 - 用什么 | 首次 |
| `architecture.md` | 架构说明 - 每个文件干什么 | ✅ |
| `implementation-plan.md` | 实施计划 - 怎么做 | ✅ |
| `progress.md` | 进度记录 - 做到哪了 | ✅ |
| `dev-workflow.md` | 开发工作流 | 首次 |
| `quick-reference.md` | 速查表 | 按需 |

### 标准提示词模板

```
阅读 /memory-bank 所有文档，
阅读 progress.md 了解之前进度，
然后继续实施计划第 N 步
```

---

## 3. AI 代码工厂集成

### 调用方式

```
「
使用 ai-ad-code-factory，
requirement = "{{需求描述}}"，
module = "pitcher" | "finance" | "ad_account" | "project"
」
```

### 6 阶段流水线

| 阶段 | 名称 | Skill | 输出 |
|------|------|-------|------|
| 1 | SEARCH | ai-ad-code-searcher | 候选代码列表 |
| 2 | SELECT | ai-ad-code-selector | 最佳参考 + 适配方案 |
| 3 | ADAPT | ai-ad-code-adapter | 适配后的代码 |
| 4 | ASSEMBLE | ai-ad-code-assembler | 完整功能模块 |
| 5 | VERIFY | ai-ad-code-verifier | 验证报告 |
| 6 | CONFIRM | (内置) | 来源追溯报告 |

### 代码块优先原则

> 生成代码前先查询代码块注册表

| 规则 | 描述 |
|------|------|
| CB-001 | 生成代码前，必须先查询代码块注册表 |
| CB-002 | 如果存在匹配的代码块，必须使用 |
| CB-003 | 代码块只能扩展，不能修改核心逻辑 |
| CB-004 | 使用代码块时必须标注 `# CodeBlock: {block_id}` |

### 代码来源标注规范

```python
# SoT: STATE_MACHINE.md#daily_report
class ReportStatus(str, Enum):
    RAW_SUBMITTED = "raw_submitted"
    TREND_OK = "trend_ok"
    FINAL_CONFIRMED = "final_confirmed"

# SoT: DATA_SCHEMA.md#daily_reports.amount
amount: Decimal = Field(..., description="消耗金额")

# SoT: BUSINESS_RULES.md#BR-RPT-001
def validate_report_date(self, date: date) -> bool:
    ...
```

---

## 4. 单次开发循环 (35-75 分钟)

```
Step 1        Step 2        Step 3        Step 4        Step 5
─────────     ─────────     ─────────     ─────────     ─────────
拆任务        写提示词       AI 生成       跑测试        提交代码
   │             │             │             │             │
   ▼             ▼             ▼             ▼             ▼
┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐      ┌─────┐
│任务卡│ ──► │提示词│ ──► │代码  │ ──► │测试  │ ──► │PR   │
└─────┘      └─────┘      └─────┘      └─────┘      └─────┘
```

| Step | 时间预算 | 超时说明 |
|------|----------|----------|
| Step 1 拆任务 | 5-10 分钟 | 任务太大，需要再拆 |
| Step 2 写提示词 | 5-10 分钟 | 用模板，不要从零写 |
| Step 3 AI 生成 | 10-30 分钟 | AI 不理解，优化提示词 |
| Step 4 跑测试 | 10-20 分钟 | 失败次数 >3，回到 Step 1 |
| Step 5 提交代码 | 5 分钟 | 固定流程 |

---

## 5. 质量门禁

### 5 秒扫描检查 (拿到代码后立即执行)

```bash
# 角色检查
grep -r "supervisor" backend/      # 必须无结果
grep -r "media_buyer" backend/     # 必须无结果 (用 pitcher)

# 状态检查
# 确认状态值在 STATE_MACHINE.md 中

# 错误码检查
# 确认错误码在 ERROR_CODES.md 中
```

### 任务卡完成标准

| 检查项 | 必须 |
|--------|------|
| 代码通过 `ruff check` | ✅ |
| 单元测试覆盖率 > 80% | ✅ |
| 无 supervisor 角色 | ✅ |
| 状态值在 STATE_MACHINE.md 中 | ✅ |
| 错误码在 ERROR_CODES.md 中 | ✅ |
| API 响应格式符合 API_SOT.md | ✅ |
| 所有代码有 SoT 来源标注 | ✅ |

---

## 6. 每日检查清单

### 开始前 (5 分钟)
```markdown
□ git pull 拉取最新代码
□ 确认今天要做的任务 (查看 progress.md)
□ 打开相关 SoT 文档
```

### 让 AI 写代码前 (2 分钟)
```markdown
□ 提示词包含 SoT 版本对齐表?
□ 提示词说明 "6 角色，无 supervisor"?
□ 提示词引用了具体的 SoT 章节?
□ 指定了 module 参数?
```

### 拿到 AI 代码后 (1 分钟)
```markdown
□ 5 秒扫描: 搜索 supervisor (必须无)
□ 5 秒扫描: 状态值在枚举内
□ 5 秒扫描: 错误码在 ERROR_CODES.md 内
□ 5 秒扫描: 代码有 SoT 来源标注
```

### 提交前 (3 分钟)
```markdown
□ ruff check 通过?
□ pytest 通过?
□ 提交信息格式正确?
□ progress.md 已更新?
```

### 结束前 (5 分钟)
```markdown
□ git status 确认无未提交文件
□ 更新 progress.md
□ 记录明天要做什么
```

---

## 7. 常见错误速查

| 错误 | 症状 | 解决方案 |
|------|------|----------|
| P0-1 角色搞错 | supervisor 出现 | 提示词第一句: "6 角色，无 supervisor" |
| P0-2 状态值自创 | 状态机流转失败 | 提示词中复制 STATE_MACHINE.md 定义 |
| P0-3 金额用 Float | 精度丢失 | 明确要求 Decimal(15,2) |
| P1-1 错误码自创 | 前端无法处理 | 提示词中附上错误码清单 |
| P1-2 字段名不一致 | API 返回空 | 对照 DATA_SCHEMA.md |
| P2-1 上下文丢失 | AI 忘记约定 | 每次给完整上下文 |
| P2-2 代码无来源标注 | 无法追溯 | 使用 `# SoT: DOC#SECTION` 格式 |

---

## 8. 相关文档

| 文档 | 路径 | 用途 |
|------|------|------|
| CLAUDE.md | 项目根目录 | Claude 自动加载的约束 |
| AI 代码工厂 | .claude/skills/ai-ad-code-factory/skill.md | 6 阶段流水线 |
| 代码块注册表 | .claude/skills/ai-ad-code-factory/knowledge/code-blocks-registry.md | 16 个代码块 |
| 防幻觉规则 | .claude/skills/ai-ad-code-factory/knowledge/anti-hallucination-rules.md | AH-01 ~ AH-05 |
| 任务卡 | docs/guides/TASK_CARDS_v2.md | 57 个任务卡 |
| AI SOP | docs/guides/AI_PROGRAMMING_SOP.md | AI 编程规范 |
