# 监工系统 (Supervisor System)

> **版本**: v1.0
> **最后更新**: 2025-12-24

监工系统是 AI 广告代投系统的自动化质量保证框架，通过 Claude Code Hooks 机制实时监控开发过程，确保代码符合 SoT（单一真相源）规范。

---

## 目录

- [功能概览](#功能概览)
- [安装说明](#安装说明)
- [配置说明](#配置说明)
- [使用示例](#使用示例)
- [模块详解](#模块详解)
- [常见问题](#常见问题)

---

## 功能概览

| 模块 | 功能 | 触发时机 |
|------|------|----------|
| **配置管理** | SoT 版本、角色、状态机定义 | 启动时加载 |
| **进度追踪** | 11 模块 30 任务进度管理 | 持续更新 |
| **合规检查** | 代码规范、角色验证、状态机检查 | PreToolUse |
| **风险检测** | 阻塞任务、进度落后、合规风险 | 按需检测 |
| **报告生成** | 日报/周报/会话报告 | Stop Hook |

### 核心约束

```
Phase 1（照亮阶段）约束:
  ✅ 允许：记录事实、展示状态、提示异常
  ✅ 允许：高亮警告、数据统计、趋势分析
  ❌ 禁止：自动阻断/拒绝/暂停/冻结功能
  ❌ 禁止：自动惩罚机制
```

---

## 安装说明

### 1. 目录结构

```
.claude/
├── hooks/
│   ├── lib/                    # 公共库
│   │   ├── __init__.py
│   │   ├── config.py           # 配置管理
│   │   ├── progress_tracker.py # 进度追踪
│   │   ├── compliance_checker.py # 合规检查
│   │   ├── risk_detector.py    # 风险检测
│   │   └── report_generator.py # 报告生成
│   ├── pre_tool_use.py         # PreToolUse Hook
│   ├── post_tool_use.py        # PostToolUse Hook
│   └── stop.py                 # Stop Hook
├── data/
│   ├── config.yaml             # 配置文件
│   ├── tasks.yaml              # 任务定义
│   ├── progress.json           # 进度数据（自动生成）
│   └── daily_reports.json      # 日报数据（自动生成）
├── reports/
│   ├── daily/                  # 日报目录
│   └── weekly/                 # 周报目录
├── tests/
│   └── test_supervisor.py      # 集成测试
└── README_SUPERVISOR.md        # 本文档
```

### 2. 依赖安装

```bash
# 确保 Python 3.9+
python --version

# 安装依赖
pip install pyyaml pytest
```

### 3. Hook 配置

在 `.claude/settings.json` 中添加 hooks 配置:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": ["python .claude/hooks/pre_tool_use.py"]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit|Bash",
        "hooks": ["python .claude/hooks/post_tool_use.py"]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": ["python .claude/hooks/stop.py"]
      }
    ]
  }
}
```

### 4. 验证安装

```bash
cd .claude
python -m pytest tests/test_supervisor.py -v
```

---

## 配置说明

### config.yaml 结构

```yaml
# SoT 文档版本
sot_versions:
  MASTER.md: "v4.6"
  API_SOT.md: "v9.4"
  DATA_SCHEMA.md: "v5.6"
  STATE_MACHINE.md: "v2.8"
  BUSINESS_RULES.md: "v4.7"
  ERROR_CODES_SOT.md: "v2.2"
  AUTH_SPEC.md: "v2.1"
  LEDGER_SOT.md: "v1.2"

# 合法角色（6 个）- MASTER.md v4.6 §2.4
# 注意: supervisor 已废弃 (PRD v2.2)，职责合并到 project_owner
valid_roles:
  - ceo
  - project_owner
  - finance
  - pitcher
  - account_manager
  - admin

# 日报 8 状态机
daily_report_states:
  - raw_submitted
  - trend_pending
  - trend_ok
  - trend_flagged
  - trend_resolved
  - final_pending
  - final_confirmed
  - final_locked

# 状态转换规则
state_transitions:
  raw_submitted: [trend_pending]
  trend_pending: [trend_ok, trend_flagged]
  # ...

# 禁止模式（Phase 1 约束）
forbidden_patterns:
  direct_balance_modify: "balance\\s*[-+]=|balance\\s*=\\s*balance"
  auto_block: "auto_(block|reject|freeze|suspend)"
  # ...

# 风险阈值
risk_thresholds:
  blocked_task_count: 3
  delay_days: 7
  progress_lag_percent: 20
```

### 自定义配置

1. **修改 SoT 版本**: 更新 `sot_versions` 部分
2. **调整风险阈值**: 修改 `risk_thresholds`
3. **添加禁止模式**: 在 `forbidden_patterns` 添加新规则

---

## 使用示例

### 1. 配置模块

```python
from lib.config import (
    get_config,
    get_sot_versions,
    is_valid_role,
    is_valid_state_transition
)

# 获取配置
config = get_config()
print(f"配置来源: {config.source}")

# 获取 SoT 版本
versions = get_sot_versions()
print(f"MASTER.md: {versions['MASTER.md']}")

# 验证角色
assert is_valid_role("pitcher") is True
assert is_valid_role("operator") is False  # 旧角色

# 验证状态转换
assert is_valid_state_transition("raw_submitted", "trend_pending") is True
assert is_valid_state_transition("raw_submitted", "final_locked") is False
```

### 2. 进度追踪

```python
from lib.progress_tracker import (
    ProgressTracker,
    TaskStatus,
    get_tracker
)

# 获取追踪器
tracker = get_tracker()

# 更新任务进度
task = tracker.update_task("A1-001", progress=80)
print(f"任务 {task.id}: {task.progress}%")

# 完成任务
task = tracker.complete_task("A1-001")
print(f"状态: {task.status}")

# 获取模块进度
progress = tracker.get_module_progress("A1")
print(f"模块 A1 进度: {progress}%")

# 获取整体进度
overall = tracker.get_overall_progress()
print(f"整体进度: {overall}%")

# 保存进度
tracker.save()
```

### 3. 合规检查

```python
from lib.compliance_checker import (
    ComplianceChecker,
    check_code,
    is_compliant
)

# 创建检查器
checker = ComplianceChecker()

# 检查代码内容
result = checker.check_content("test.py", '''
def process():
    if user.role == "operator":  # 旧角色
        account.balance -= 100   # 直接修改余额
''')

# 查看违规
for v in result.violations:
    print(f"[{v.severity}] {v.type}: {v.message}")

# 便捷函数
violations = check_code('account.balance = 100', "test.py")
print(f"发现 {len(violations)} 个违规")

# 快速检查
if is_compliant('if user.role == "pitcher": pass'):
    print("代码合规")
```

### 4. 风险检测

```python
from lib.risk_detector import (
    RiskDetector,
    RiskType,
    RiskLevel,
    detect_risks
)

# 创建检测器
detector = RiskDetector()

# 运行所有检测
result = detector.detect_all()

# 按级别查看风险
critical = detector.get_risks_by_level(RiskLevel.CRITICAL)
high = detector.get_risks_by_level(RiskLevel.HIGH)

# 按类型查看风险
blocked = detector.get_risks_by_type(RiskType.BLOCKED_TASK)
compliance = detector.get_risks_by_type(RiskType.COMPLIANCE)

# 获取摘要
summary = detector.get_summary()
print(f"总风险: {summary['total']}")
```

### 5. 报告生成

```python
from lib.report_generator import (
    ReportGenerator,
    generate_daily_report
)

# 创建生成器
generator = ReportGenerator()

# 生成日报
daily_content = generator.generate_daily()
filepath = generator.save_report(daily_content, "daily")
print(f"日报已保存: {filepath}")

# 生成周报
weekly_content = generator.generate_weekly()
filepath = generator.save_report(weekly_content, "weekly")
print(f"周报已保存: {filepath}")

# 便捷函数
content = generate_daily_report()
```

---

## 模块详解

### 配置管理 (config.py)

| 函数 | 说明 |
|------|------|
| `get_config()` | 获取配置对象（缓存） |
| `reload_config()` | 重新加载配置 |
| `get_sot_versions()` | 获取 SoT 版本字典 |
| `get_valid_roles()` | 获取有效角色列表 |
| `is_valid_role(role)` | 验证角色是否有效 |
| `is_valid_state(state)` | 验证状态是否有效 |
| `is_valid_state_transition(from, to)` | 验证状态转换是否有效 |

### 进度追踪 (progress_tracker.py)

| 类/函数 | 说明 |
|---------|------|
| `TaskStatus` | 任务状态枚举 (NOT_STARTED, IN_PROGRESS, BLOCKED, COMPLETED) |
| `Task` | 任务数据类 |
| `Module` | 模块数据类 |
| `ProgressTracker` | 进度追踪器类 |
| `get_tracker()` | 获取单例追踪器 |
| `reset_tracker()` | 重置追踪器 |

### 合规检查 (compliance_checker.py)

| 类/函数 | 说明 |
|---------|------|
| `ViolationType` | 违规类型枚举 |
| `Severity` | 严重程度枚举 (ERROR, WARNING, INFO) |
| `Violation` | 违规数据类 |
| `CheckResult` | 检查结果数据类 |
| `ComplianceChecker` | 合规检查器类 |
| `check_code(code, file)` | 检查代码片段 |
| `is_compliant(code)` | 快速合规检查 |

### 风险检测 (risk_detector.py)

| 类/函数 | 说明 |
|---------|------|
| `RiskType` | 风险类型枚举 |
| `RiskLevel` | 风险级别枚举 (LOW, MEDIUM, HIGH, CRITICAL) |
| `Risk` | 风险数据类 |
| `RiskDetector` | 风险检测器类 |
| `detect_risks()` | 运行所有检测 |
| `has_critical_risks()` | 检查是否有严重风险 |

### 报告生成 (report_generator.py)

| 类/函数 | 说明 |
|---------|------|
| `ReportGenerator` | 报告生成器类 |
| `generate_daily_report()` | 生成日报 |
| `generate_weekly_report()` | 生成周报 |

---

## 常见问题

### Q1: 配置文件找不到怎么办？

**A**: 系统会自动使用内置默认配置。检查以下路径是否存在:
- `.claude/data/config.yaml`
- 确保从项目根目录运行

### Q2: 如何添加新的禁止模式？

**A**: 在 `config.yaml` 的 `forbidden_patterns` 部分添加:

```yaml
forbidden_patterns:
  my_new_pattern: >-
    正则表达式
```

### Q3: 如何修改风险阈值？

**A**: 在 `config.yaml` 的 `risk_thresholds` 部分修改:

```yaml
risk_thresholds:
  blocked_task_count: 5   # 阻塞任务数量阈值
  delay_days: 14          # 延迟天数阈值
  progress_lag_percent: 30 # 进度落后百分比
```

### Q4: 日报/周报保存在哪里？

**A**: 默认保存在:
- 日报: `.claude/reports/daily/YYYY-MM-DD.md`
- 周报: `.claude/reports/weekly/YYYY-MM-DD.md`

### Q5: 如何手动运行合规检查？

**A**: 使用便捷函数:

```python
from lib import check_code, is_compliant

# 检查代码
violations = check_code(code_content, "filename.py")

# 快速检查
if not is_compliant(code_content):
    print("代码不合规")
```

### Q6: 如何跳过某些文件的检查？

**A**: 在代码中添加注释:

```python
# supervisor:ignore
account.balance -= 100  # 此行会被忽略
```

### Q7: Windows 上中文显示乱码怎么办？

**A**: 确保终端使用 UTF-8 编码:

```powershell
# PowerShell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001
```

### Q8: 如何查看当前进度？

**A**: 运行以下命令:

```python
from lib import get_tracker, generate_progress_report

tracker = get_tracker()
print(f"整体进度: {tracker.get_overall_progress()}%")

# 或生成完整报告
report = generate_progress_report()
print(report)
```

### Q9: 测试失败怎么排查？

**A**: 运行详细测试:

```bash
cd .claude
python -m pytest tests/test_supervisor.py -v --tb=long
```

### Q10: 如何贡献新功能？

**A**:
1. 在 `lib/` 目录添加新模块
2. 在 `lib/__init__.py` 导出公共接口
3. 在 `tests/test_supervisor.py` 添加测试
4. 更新本文档

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-24 | 初始版本 |

---

*此文档由 AI 广告代投系统监工系统自动维护*
