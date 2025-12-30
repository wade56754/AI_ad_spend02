---
description: "工作流编排: 端到端开发流程自动化"
argument-hint: "<be-dev|fe-dev|fullstack|hotfix|release>"
---

# 工作流编排 Skill

## 使用方式

```bash
/flow be-dev 实现日报批量提交功能      # 后端开发流程
/flow fe-dev 日报列表页面重构          # 前端开发流程
/flow fullstack 新增取消日报功能       # 全栈开发流程
/flow hotfix 修复状态流转错误          # 热修复流程
/flow release v1.2.0                   # 发版流程
```

---

## 工作流类型

### 1. be-dev - 后端开发流程

```
┌─────────────────────────────────────────────────────────┐
│                    后端开发流程                          │
├─────────────────────────────────────────────────────────┤
│  Step 1: 需求分析                                       │
│  ├─ 确定模块归属 (pitcher/finance/ad_account/project)   │
│  ├─ 识别 SoT 依赖                                       │
│  └─ 列出影响范围                                        │
│                                                         │
│  Step 2: 代码生成                                       │
│  ├─ /gen be <task>                                      │
│  ├─ 生成 Schema → Service → Router                     │
│  └─ 自动添加 SoT 注释                                   │
│                                                         │
│  Step 3: 代码审查                                       │
│  ├─ /review <files> --sot                              │
│  ├─ 验证状态/角色/错误码                                │
│  └─ 检查 Phase 1 合规                                   │
│                                                         │
│  Step 4: 测试验证                                       │
│  ├─ /gen test <task>                                   │
│  ├─ pytest backend/tests/                              │
│  └─ 确保覆盖率 > 60%                                   │
│                                                         │
│  Step 5: 文档更新                                       │
│  ├─ /doc api                                           │
│  └─ 更新 README (如需要)                               │
└─────────────────────────────────────────────────────────┘
```

**自动执行**:
```bash
# Step 1
echo "📋 分析任务: $TASK"
# 自动判断模块

# Step 2
/gen be $TASK

# Step 3
/review backend/services/*.py --sot

# Step 4
/gen test $TASK
pytest backend/tests/ -v

# Step 5
/doc api
```

---

### 2. fe-dev - 前端开发流程

```
┌─────────────────────────────────────────────────────────┐
│                    前端开发流程                          │
├─────────────────────────────────────────────────────────┤
│  Step 1: 需求分析                                       │
│  ├─ 确定功能模块                                        │
│  ├─ 检查 API 依赖                                       │
│  └─ 设计组件结构                                        │
│                                                         │
│  Step 2: 代码生成                                       │
│  ├─ /gen fe <task>                                     │
│  ├─ 生成 Types → API → Components                      │
│  └─ 遵循 React 最佳实践                                 │
│                                                         │
│  Step 3: 类型检查                                       │
│  ├─ npm run type-check                                 │
│  ├─ npm run lint                                       │
│  └─ 修复类型错误                                        │
│                                                         │
│  Step 4: 本地验证                                       │
│  ├─ npm run dev                                        │
│  ├─ 手动测试功能                                        │
│  └─ 检查响应式布局                                      │
│                                                         │
│  Step 5: 提交代码                                       │
│  ├─ git add && git commit                              │
│  └─ 创建 PR                                            │
└─────────────────────────────────────────────────────────┘
```

---

### 3. fullstack - 全栈开发流程

```
┌─────────────────────────────────────────────────────────┐
│                    全栈开发流程                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Phase 1: 后端实现 (be-dev)                             │
│  ├─ API 设计                                           │
│  ├─ 代码生成                                           │
│  └─ 测试验证                                           │
│                                                         │
│  Phase 2: 前端实现 (fe-dev)                             │
│  ├─ API 集成                                           │
│  ├─ UI 组件                                            │
│  └─ 状态管理                                           │
│                                                         │
│  Phase 3: 集成测试                                      │
│  ├─ E2E 测试                                           │
│  ├─ API 联调                                           │
│  └─ 性能验证                                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**执行顺序**:
```bash
# Phase 1: 后端
/flow be-dev $TASK

# Phase 2: 前端
/flow fe-dev $TASK

# Phase 3: 集成
pytest tests/e2e/ -v
```

---

### 4. hotfix - 热修复流程

```
┌─────────────────────────────────────────────────────────┐
│                    热修复流程                            │
├─────────────────────────────────────────────────────────┤
│  ⚡ 快速修复生产问题                                     │
│                                                         │
│  Step 1: 创建修复分支                                   │
│  └─ git checkout -b hotfix/issue-xxx                   │
│                                                         │
│  Step 2: 定位问题                                       │
│  ├─ 分析错误日志                                        │
│  └─ 复现问题                                           │
│                                                         │
│  Step 3: 修复代码                                       │
│  ├─ 最小化修改                                         │
│  └─ 添加回归测试                                        │
│                                                         │
│  Step 4: 验证修复                                       │
│  ├─ /review <files> --sot                              │
│  ├─ pytest 相关测试                                    │
│  └─ 本地验证                                           │
│                                                         │
│  Step 5: 快速发布                                       │
│  ├─ 创建 PR                                            │
│  ├─ 紧急审批                                           │
│  └─ 合并部署                                           │
└─────────────────────────────────────────────────────────┘
```

**约束**:
- 修改范围最小化
- 必须包含测试
- 跳过非必要检查

---

### 5. release - 发版流程

```
┌─────────────────────────────────────────────────────────┐
│                    发版流程                              │
├─────────────────────────────────────────────────────────┤
│  Step 1: 版本检查                                       │
│  ├─ 确认所有 PR 已合并                                  │
│  ├─ 检查测试通过率                                      │
│  └─ 验证 SoT 版本一致                                   │
│                                                         │
│  Step 2: 生成变更日志                                   │
│  └─ /doc changelog                                     │
│                                                         │
│  Step 3: 更新版本号                                     │
│  ├─ package.json                                       │
│  ├─ pyproject.toml                                     │
│  └─ VERSION 文件                                       │
│                                                         │
│  Step 4: 创建 Release                                   │
│  ├─ git tag vX.Y.Z                                     │
│  ├─ git push --tags                                    │
│  └─ GitHub Release                                     │
│                                                         │
│  Step 5: 部署验证                                       │
│  ├─ 部署到 staging                                     │
│  ├─ 冒烟测试                                           │
│  └─ 部署到 production                                  │
└─────────────────────────────────────────────────────────┘
```

---

## 流程状态追踪

每个流程执行时会创建状态文件:

```
.claude/data/flow_state.json
{
  "flow_id": "be-dev-20251230-001",
  "type": "be-dev",
  "task": "实现日报批量提交",
  "status": "in_progress",
  "current_step": 3,
  "steps": [
    {"name": "需求分析", "status": "completed"},
    {"name": "代码生成", "status": "completed"},
    {"name": "代码审查", "status": "in_progress"},
    {"name": "测试验证", "status": "pending"},
    {"name": "文档更新", "status": "pending"}
  ],
  "started_at": "2025-12-30T10:00:00Z"
}
```

**恢复中断的流程**:
```bash
/flow resume    # 继续上次中断的流程
/flow status    # 查看当前流程状态
/flow abort     # 放弃当前流程
```

---

## 输出示例

```
🚀 启动工作流: be-dev

📋 任务: 实现日报批量提交功能
📂 模块: pitcher
📄 SoT 依赖: STATE_MACHINE.md, API_SOT.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1/5: 需求分析 ✅
  - 模块: pitcher
  - 影响文件: 3 个
  - SoT 引用: 2 个

Step 2/5: 代码生成 ✅
  - 生成: backend/schemas/daily_report.py
  - 生成: backend/services/daily_report_service.py
  - 修改: backend/routers/daily_reports.py

Step 3/5: 代码审查 🔄 进行中...
  - 检查 SoT 合规...
  - 检查 Phase 1 原则...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏱️ 已用时: 5 分钟
📊 进度: 40%
```
