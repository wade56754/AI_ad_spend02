---
description: "代码生成: 后端/前端/测试代码一键生成"
argument-hint: "<be|fe|test> <task-description>"
---

# 代码生成 Skill

## 使用方式

```bash
/gen be 创建日报提交接口
/gen fe 日报列表页面组件
/gen test 日报状态流转测试
```

## 执行流程

### Step 1: 解析任务

从用户输入提取:
- **type**: `be` (后端) | `fe` (前端) | `test` (测试)
- **task**: 任务描述

### Step 2: 自动判断模块

根据关键词自动推断模块归属:

| 关键词 | 模块 | 可写路径 |
|--------|------|----------|
| 日报、投放、CPL、投手 | pitcher | `routers/daily_reports.py`, `services/daily_report_service.py` |
| 充值、流水、账本、财务 | finance | `routers/finance.py`, `services/ledger_service.py` |
| 账户、开户、授权 | ad_account | `routers/ad_accounts.py`, `services/ad_account_service.py` |
| 项目、成员、权限 | project | `routers/projects.py`, `services/project_service.py` |

**如果无法判断 → 询问用户**

### Step 3: 防幻觉检查 (BLOCKING)

生成前必须验证:

```
□ 状态值在白名单中?
  ✓ draft, pending_review, trend_pending, trend_ok,
    real_pending, real_filled, final_pending, final_confirmed

□ 角色值在白名单中?
  ✓ ceo, admin, project_owner, finance, pitcher, account_manager

□ 错误码前缀在白名单中?
  ✓ AUTH_, BIZ_, FIN_, LEDGER_, STATE_, VALIDATION_,
    DB_, SYS_, API_, PERM_, RES_, DATA_, RECON_, REPORT_, RPT_, IMPORT_

□ 无自动阻断代码?
  ✗ 禁止: raise HTTPException(403), suspend(), freeze(), reject()
  ✓ 允许: 记录日志, 返回警告标记, 高亮显示
```

**任一检查失败 → STOP → 询问用户**

### Step 4: 生成代码

**后端 (be)**:
```
生成顺序: Schema → Service → Router
文件位置:
  - backend/schemas/{module}.py
  - backend/services/{module}_service.py
  - backend/routers/{module}.py

禁止修改:
  - backend/models/**
  - migrations/**
```

**前端 (fe)**:
```
生成顺序: Types → API → Component → 设计审查
文件位置:
  - frontend/src/features/{module}/types/
  - frontend/src/features/{module}/services/
  - frontend/src/features/{module}/components/

设计审查 (调用 frontend-design skill):
  - 设计系统一致性 (颜色/间距/字体)
  - 组件复用性验证 (使用 DataTable, StatusBadge 等)
  - 响应式布局检查 (断点策略)
  - 可访问性检查 (a11y)
```

**测试 (test)**:
```
文件位置:
  - backend/tests/test_{module}.py
  - backend/tests/services/test_{module}_service.py
```

### Step 5: 自动验证

生成后执行:
```bash
# 后端
ruff check backend/
mypy backend/ --ignore-missing-imports

# 前端
npm run lint --prefix frontend
npm run type-check --prefix frontend
```

**验证失败 → 自动修复（最多 3 次）**

### Step 5.5: 前端设计审查 (仅 fe 类型)

**当 type = fe 时，调用 frontend-design skill 进行设计审查**:

```
设计审查清单:

□ 设计系统一致性
  - 颜色使用正确的 CSS 变量 (--primary, --destructive 等)
  - 间距使用 Tailwind 标准值 (space-4, gap-6 等)
  - 字体层级正确 (text-2xl/bold, text-lg/medium 等)

□ 组件复用性
  - 表格使用 DataTable 组件
  - 状态显示使用 StatusBadge 组件
  - 表单使用 Form + FormField 模式
  - 弹窗使用 Dialog/AlertDialog

□ 响应式设计
  - 使用 grid-cols-1 md:grid-cols-2 lg:grid-cols-4 模式
  - 移动端适配考虑

□ 可访问性 (a11y)
  - 按钮有 aria-label
  - 表单元素有关联 label
  - 颜色对比度达标

□ 禁止模式检查
  ✗ 内联样式 style={{}}
  ✗ 硬编码颜色 bg-[#xxx]
  ✗ 手写 <table> 标签
  ✗ 魔法数字 w-[347px]
```

**审查不通过 → 自动修复 → 重新审查**

### Step 6: 更新进度文档 (MANDATORY)

**验证通过后必须执行**:

1. 读取 `memory-bank/progress.md`
2. 更新对应任务卡状态: `⏳ todo` → `✅ done`
3. 更新模块进度百分比
4. 更新总体完成率
5. 在「最近完成的任务」表格添加记录

```markdown
## 8. 最近完成的任务

| 日期 | 任务卡 | 描述 | 生成文件 |
|------|--------|------|----------|
| {TODAY} | {TASK_ID} | {DESCRIPTION} | {FILE_LIST} |
```

**此步骤不可跳过** - 确保进度追踪的准确性

## 输出格式

**后端生成输出**:
```
✅ 代码生成完成

📁 生成文件:
  - backend/schemas/daily_report.py (新增)
  - backend/services/daily_report_service.py (修改)
  - backend/routers/daily_reports.py (修改)

📋 SoT 引用:
  - STATE_MACHINE.md v2.8: draft → pending_review
  - API_SOT.md v9.4: POST /api/v1/daily-reports

📊 进度更新:
  - 任务卡: TASK-XXX-001 → ✅ done
  - 模块进度: XX% (N/M)
  - 总体进度: XX% (N/M)

⚠️ 注意事项:
  - 需要运行 pytest 验证
```

**前端生成输出 (包含设计审查)**:
```
✅ 代码生成完成

📁 生成文件:
  - frontend/src/features/daily-reports/types/index.ts (新增)
  - frontend/src/features/daily-reports/components/DailyReportList.tsx (新增)

📋 SoT 引用:
  - STATE_MACHINE.md v2.8: raw_submitted, trend_ok, final_confirmed
  - API_SOT.md v9.4: GET /api/v1/daily-reports

🎨 设计审查结果:
  ✅ 设计系统一致性: 通过
  ✅ 组件复用性: 使用 DataTable, StatusBadge
  ✅ 响应式设计: md:grid-cols-2 lg:grid-cols-4
  ✅ 可访问性: aria-label 已添加
  ⚠️ 修复项: 1 个硬编码颜色已替换为 CSS 变量

📊 进度更新:
  - 任务卡: TASK-XXX-001 → ✅ done
  - 模块进度: XX% (N/M)
```

## 约束

- 所有状态/角色/错误码必须来自 SoT 白名单
- 禁止生成自动阻断逻辑（Phase 1 原则）
- 每个生成的函数必须包含 SoT 引用注释
