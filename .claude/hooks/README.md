# Claude Code Hooks - AI 广告代投系统

本目录包含为 AI 广告代投管理系统配置的 Claude Code Hooks，用于确保开发过程中遵循 SoT 裁判链和 Phase 1 约束。

## 📋 Hooks 列表

### 1. SessionStart Hook (`session_start.py`)

**触发时机**: 每次新会话开始时

**功能**:
- 显示 SoT 文档优先级顺序（10 个核心文档）
- 提醒 Phase 1 核心约束（禁止自动阻断/惩罚）
- 列出 7 个合法角色定义
- 展示 AI 防幻觉原则（AH-01 ~ AH-05）

**目的**: 确保 AI 和开发者在开发前了解核心约束和规则。

---

### 2. PreToolUse Hook (`pre_tool_use.py`)

**触发时机**: 使用 `Write` 或 `Edit` 工具前

**检查项目**:

1. **Phase 2 功能检测** (禁止)
   - 关键词: `auto_reject`, `auto_suspend`, `auto_freeze`, `forced_approval` 等
   - 中文关键词: `自动拒绝`, `自动暂停`, `强制审批` 等

2. **外键命名规范**
   - 检查外键字段是否使用 `_id` 后缀
   - 例如: `project_id`, `user_id`, `ad_account_id`

3. **角色定义合规性**
   - 仅允许 7 个角色: `ceo`, `project_owner`, `finance`, `supervisor`, `pitcher`, `account_manager`, `admin`
   - 拒绝任何未定义角色

**行为**: 检测到违规时，**阻止工具执行**并显示详细错误信息。

---

### 3. PostToolUse Hook (`post_tool_use.py`)

**触发时机**: 使用 `Write` 或 `Edit` 工具后

**功能**:
- **Python 文件** (`.py`): 使用 `black` 自动格式化
- **TypeScript 文件** (`.ts`, `.tsx`): 使用 `prettier` 自动格式化

**依赖**:
- Python: 需要安装 `black`
  ```bash
  pip install black
  ```
- TypeScript: 需要安装 `prettier` (或通过 `npx` 使用)
  ```bash
  npm install -g prettier
  ```

**行为**: 格式化失败不会阻止流程，只会显示警告。

---

### 4. Stop Hook (`stop.py`)

**触发时机**: 会话停止时

**功能**:
- 发送桌面通知（Windows/macOS/Linux）
- 显示会话结束信息

**目的**: 提醒用户会话已结束，避免忘记保存工作成果。

---

## 🔧 配置

Hooks 已在 `.claude/settings.local.json` 中配置：

```json
{
  "hooks": {
    "SessionStart": [...],
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Stop": [...]
  }
}
```

## 🚀 使用方法

### 自动触发

这些 hooks 会在相应事件发生时**自动执行**，无需手动调用：

- 启动新会话 → 自动显示 SoT 提醒
- 写入/编辑代码 → 自动检查合规性 + 自动格式化
- 停止会话 → 自动发送桌面通知

### 手动测试

可以手动运行各个 hook 脚本进行测试：

```bash
# 测试 SessionStart Hook
python .claude/hooks/session_start.py

# 测试 PreToolUse Hook (需要设置环境变量)
export TOOL_NAME="Write"
export TOOL_PARAMETERS_JSON='{"file_path": "test.py", "content": "print(123)"}'
python .claude/hooks/pre_tool_use.py

# 测试 PostToolUse Hook (需要真实文件)
export TOOL_NAME="Write"
export TOOL_PARAMETERS_JSON='{"file_path": "test.py"}'
python .claude/hooks/post_tool_use.py

# 测试 Stop Hook
python .claude/hooks/stop.py
```

---

## 📖 开发规范提醒

### ❌ 禁止事项（Phase 1）

- 自动拒绝/暂停/冻结功能
- 自动惩罚机制（扣分、禁用账户）
- 强制审批流程

### ✅ 允许事项（Phase 1）

- 记录事实、展示状态、提示异常
- 高亮警告、数据统计、趋势分析

### 🎯 合法角色（7 个）

| 角色 | 英文 | 职责 |
|------|------|------|
| 老板 | `ceo` | 资金安全、公司盈亏、最终决策 |
| 项目负责人 | `project_owner` | 项目盈亏、资金使用效率 |
| 财务 | `finance` | 资金出入准确、数据真实、对账 |
| 主管 | `supervisor` | 团队产出、投手管理、日常监督 |
| 投手 | `pitcher` | CPL 达标、日报准确、执行投放 |
| 户管 | `account_manager` | 账户分配、账户状态监控 |
| 管理员 | `admin` | 系统配置（不参与业务） |

### 🛡️ AI 防幻觉原则

- **AH-01**: 禁止假设数据一致 - 遇到缺失标记"待确认"
- **AH-02**: 禁止自动做管理裁决 - 不生成自动拒绝/暂停代码
- **AH-03**: 禁止引入 SoT 未定义概念 - 发现缺失→停止→询问
- **AH-04**: 必须遵循 Phase 1 软性原则 - 提示+高亮+记录
- **AH-05**: 遇到歧义必须停止并询问 - 停止→列出歧义→询问

---

## 🔍 故障排查

### Python 编码问题

如果在 Windows 上遇到编码错误，确保：
1. 脚本文件包含 `# -*- coding: utf-8 -*-` 头
2. 脚本中设置了 UTF-8 输出编码
3. 命令行使用 `chcp 65001` 切换到 UTF-8 模式

### 格式化工具未安装

如果看到 "xxx 未安装" 警告：

```bash
# 安装 black (Python)
pip install black

# 安装 prettier (TypeScript)
npm install -g prettier
```

### Hook 未执行

1. 检查 `.claude/settings.local.json` 中的 `hooks` 配置
2. 确保 Python 可执行：`python --version`
3. 查看 Claude Code 控制台输出

---

## 📚 相关文档

- **SoT 裁判链**: `docs/1.overview/MASTER.md` v4.4
- **Phase 设计**: `docs/1.overview/MVP_PHASE_DESIGN.md`
- **状态机**: `docs/2.sot/STATE_MACHINE.md` v2.6
- **API 规范**: `docs/2.sot/API_SOT.md` v9.0
- **错误码**: `docs/2.sot/ERROR_CODES_SOT.md` v2.1

---

## 🆘 支持

如有问题，请：
1. 查看 `.claude/hooks/` 目录下的脚本源码
2. 手动运行脚本测试
3. 检查 Claude Code 日志输出

---

**版本**: v1.0
**更新日期**: 2025-12-22
**维护**: AI 广告代投系统开发团队
