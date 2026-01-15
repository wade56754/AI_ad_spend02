# Claude Code Hooks - AI 广告代投系统

> **版本**: v2.0
> **更新日期**: 2025-12-24
> **基于**: ENABLE_SUPERVISOR_V2.md 规范

本目录包含 Claude Code Hooks，确保开发遵循 SoT 裁判链和 Phase 1 约束。

---

## 目录结构

```
.claude/hooks/
├── inject_timestamp.py   ← SessionStart: 时间戳注入
├── session_start.py      ← SessionStart: SoT 裁判链
├── load_context.py       ← SessionStart: 文档上下文
├── pre_tool_use.py       ← PreToolUse: 合规检查
├── post_tool_use.py      ← PostToolUse: 变更记录
├── stop.py               ← Stop: 会话报告
├── README.md             ← 本文档
└── lib/                  ← 支持库
    ├── __init__.py
    ├── config.py
    ├── compliance_checker.py
    ├── progress_tracker.py
    ├── risk_detector.py
    └── report_generator.py
```

---

## Hook 触发流程

```
会话开始
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ SessionStart (3 hooks)                                  │
│  1. inject_timestamp  → 注入北京时间上下文              │
│  2. session_start     → 加载 SoT 裁判链                 │
│  3. load_context      → 加载 SoT 文档上下文             │
└─────────────────────────────────────────────────────────┘
    │
    ▼
正常对话交互...
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ PreToolUse (执行前检查)                                 │
│  • Write|Edit|MultiEdit → 检查代码合规性                │
│  • Bash                 → 检查命令安全性                │
└─────────────────────────────────────────────────────────┘
    │
    ▼ (通过检查)
┌─────────────────────────────────────────────────────────┐
│ PostToolUse (执行后记录)                                │
│  • Write|Edit|MultiEdit|Bash → 记录变更                 │
└─────────────────────────────────────────────────────────┘
    │
    ▼
会话结束
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ Stop (会话结束)                                         │
│  • 生成会话报告                                         │
│  • 保存日报数据                                         │
│  • 发送桌面通知                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Hooks 详细说明

### 1. inject_timestamp.py

**触发**: SessionStart (第一个)
**超时**: 5000ms

**功能**:
- 注入北京时间 (UTC+8) 上下文
- 显示日期、星期、时段
- 判断工作日/周末/假日
- 内置 2025 年中国假日表

**输出示例**:
```
┌─────────────────────────────────────────────────────────┐
│  北京时间 (UTC+8)
│  2025年12月24日 周三 晚上 20:12
│  工作日 | 冬季
└─────────────────────────────────────────────────────────┘
```

---

### 2. session_start.py

**触发**: SessionStart (第二个)
**超时**: 5000ms

**功能**:
- 显示 SoT 文档优先级 (10 个核心文档)
- 提醒 Phase 1 约束
- 列出 7 个合法角色
- 展示 AI 防幻觉原则 (AH-01 ~ AH-05)

---

### 3. load_context.py

**触发**: SessionStart (第三个)
**超时**: 10000ms

**功能**:
- 加载 4 个核心 SoT 文档摘要
- 显示裁判链优先级规则

---

### 4. pre_tool_use.py

**触发**: PreToolUse
**超时**: 10000ms
**Matcher**: `Write|Edit|MultiEdit` 或 `Bash`

**检查项目**:

| 检查类型 | 触发工具 | 检查内容 |
|---------|---------|---------|
| Phase 2 功能 | Write/Edit | auto_reject, auto_suspend 等 |
| Balance 修改 | Write/Edit | 禁止 .balance = 直接修改 |
| 旧状态名 | Write/Edit | 禁止 draft, submitted 等 |
| 危险命令 | Bash | 禁止删除 SoT、SQL 修改 balance |

**输入** (stdin):
```json
{"tool_name": "Write", "tool_input": {"file_path": "x.py", "content": "..."}}
```

**输出**:
```json
{"decision": "approve", "reason": null}
{"decision": "reject", "reason": "禁止直接修改 balance"}
```

---

### 5. post_tool_use.py

**触发**: PostToolUse
**超时**: 5000ms
**Matcher**: `Write|Edit|MultiEdit|Bash`

**功能**:
- 记录文件修改到会话数据
- 检测关联模块 (A1-Dashboard, B1-日报 等)
- 更新任务进度
- 自动格式化代码 (black/prettier)

---

### 6. stop.py

**触发**: Stop
**超时**: 30000ms

**功能**:
- 生成会话摘要 (文件数、工具调用、模块)
- 保存会话历史 (最近 100 条)
- 更新日报数据
- 发送桌面通知

---

## 配置 (settings.local.json)

```json
{
  "hooks": {
    "SessionStart": [{
      "hooks": [
        {"type": "command", "command": "python .claude/hooks/inject_timestamp.py", "timeout": 5000},
        {"type": "command", "command": "python .claude/hooks/session_start.py", "timeout": 5000},
        {"type": "command", "command": "python .claude/hooks/load_context.py", "timeout": 10000}
      ]
    }],
    "PreToolUse": [
      {"matcher": "Write|Edit|MultiEdit", "hooks": [{"type": "command", "command": "python .claude/hooks/pre_tool_use.py", "timeout": 10000}]},
      {"matcher": "Bash", "hooks": [{"type": "command", "command": "python .claude/hooks/pre_tool_use.py", "timeout": 10000}]}
    ],
    "PostToolUse": [
      {"matcher": "Write|Edit|MultiEdit|Bash", "hooks": [{"type": "command", "command": "python .claude/hooks/post_tool_use.py", "timeout": 5000}]}
    ],
    "Stop": [{
      "hooks": [{"type": "command", "command": "python .claude/hooks/stop.py", "timeout": 30000}]
    }]
  }
}
```

---

## 手动测试

```bash
# SessionStart hooks
python .claude/hooks/inject_timestamp.py
python .claude/hooks/session_start.py
python .claude/hooks/load_context.py

# PreToolUse - 合规
echo '{"tool_name":"Write","tool_input":{"file_path":"t.py","content":"x=1"}}' | python .claude/hooks/pre_tool_use.py

# PreToolUse - 违规
echo '{"tool_name":"Write","tool_input":{"file_path":"t.py","content":"a.balance-=1"}}' | python .claude/hooks/pre_tool_use.py

# PostToolUse
echo '{"tool_name":"Write","tool_input":{"file_path":"t.py"},"success":true}' | python .claude/hooks/post_tool_use.py

# Stop
echo '{"session_id":"test","start_time":"2025-12-24T20:00:00"}' | python .claude/hooks/stop.py
```

---

## 开发规范

### 禁止 (Phase 1)
- 自动拒绝/暂停/冻结
- 自动惩罚机制
- 强制审批流程
- 直接修改 balance

### 允许 (Phase 1)
- 记录事实、展示状态
- 高亮警告、数据统计

### 业务层角色 (6 个，PRD v5.1)
| 角色 | 英文 | 职责 | 技术层映射 |
|------|------|------|-----------|
| 老板 | ceo | 资金安全、最终决策 | admin |
| 项目负责人 | project_owner | 日报审核、项目盈亏 | is_project_owner=true |
| 财务 | finance | 资金出入、对账 | finance |
| 投手 | pitcher | CPL 达标、日报准确 | media_buyer |
| 户管 | account_manager | 账户分配 | account_manager |
| 管理员 | admin | 系统配置 | admin |

> **注**: supervisor 和 data_operator 已废弃 (PRD v5.1)

### AI 防幻觉原则
- AH-01: 禁止假设数据一致
- AH-02: 禁止自动做管理裁决
- AH-03: 禁止引入未定义概念
- AH-04: 遵循 Phase 1 软性原则
- AH-05: 遇歧义停止并询问

---

## 数据文件

| 文件 | 说明 |
|------|------|
| .claude/data/session_data.json | 当前会话数据 |
| .claude/data/session_history.json | 会话历史 |
| .claude/data/daily_reports.json | 日报数据 |
| .claude/logs/*.log | 日志文件 |

---

## 相关文档

- docs/sot/MASTER.md v4.4
- docs/sot/STATE_MACHINE.md v2.6
- docs/sot/API_SOT.md v9.0

---

**维护**: AI 广告代投系统开发团队
