# AI 代码工厂 - 阶段 2 功能说明

> **版本**: v2.4
> **发布日期**: 2025-12-22
> **基准文档**: MASTER.md v4.4, STATE_MACHINE.md v2.6

## 新增功能概览

阶段 2 为 AI 代码工厂添加了三个核心功能模块，实现 Phase 1/2 边界管理和防幻觉检查。

### 1. Phase 配置系统（PhaseConfig）

**文件**: `agents/skills/code_factory/phase_config.py`

**功能**:
- 管理 Phase 1（照亮不问责）和 Phase 2（问责与约束）两种模式
- 通过环境变量控制 Phase 2 功能开关
- 为代码生成器和验证器提供 Phase 边界检查

**环境变量**:
```bash
# Phase 模式（默认 phase1）
export FACTORY_PHASE="phase1"  # 或 "phase2"

# Phase 2 功能开关（默认全部 false）
export PHASE2_TOPUP_ENFORCEMENT="true"        # 充值强制校验
export PHASE2_DAILY_REPORT_REQUIRED="true"   # 日报强制填报
export PHASE2_WEEKLY_BRIEF_REQUIRED="true"   # 周报强制填报
export PHASE2_SETTLEMENT_LOCK="true"          # 结算期锁定
```

**用法示例**:
```python
from agents.skills.code_factory.phase_config import PhaseConfig

# 从环境变量加载配置
config = PhaseConfig.from_env()

# 检查当前 Phase
if config.is_phase1_enabled():
    print("Phase 1 模式：照亮不问责")
elif config.is_phase2_enabled():
    print("Phase 2 模式：问责与约束")
    print("启用的功能:", config.get_enabled_features())

# 验证代码是否符合 Phase 约束
code = "if balance < 0: raise BusinessError('余额不足')"
valid, msg = config.validate_code_for_phase(code)
if not valid:
    print(f"Phase 1 冲突: {msg}")
```

**Phase 1 vs Phase 2 对比**:

| 维度 | Phase 1（照亮不问责） | Phase 2（问责与约束） |
|-----|---------------------|---------------------|
| 余额不足 | 高亮警告，允许继续 | 阻断投放，强制充值 |
| 日报逾期 | 提示填报，不影响业务 | 自动暂停账户 |
| 异常数据 | 标记需人工复核 | 自动拒绝/冲正 |
| 违规操作 | 记录日志 | 触发考核/罚款 |

---

### 2. SoT 动态加载器（SotLoader）

**文件**: `agents/skills/code_factory/sot_loader.py`

**功能**:
- 从 SoT 文档和代码动态加载角色、状态、字段白名单
- 替代硬编码的 frozenset 定义
- 确保验证器始终使用最新的 SoT 规范

**数据来源优先级**:
1. **优先**: `backend/models/enums.py` - 代码即真理
2. **备选**: SoT 文档（STATE_MACHINE.md, DATA_SCHEMA.md 等）
3. **兜底**: 硬编码白名单

**用法示例**:
```python
from pathlib import Path
from agents.skills.code_factory.sot_loader import SotLoader

# 初始化加载器
loader = SotLoader(project_root=Path("/path/to/project"))

# 验证角色
loader.is_valid_role("admin")  # True
loader.is_valid_role("invalid_role")  # False

# 验证状态
loader.is_valid_status("raw_submitted", "daily_reports")  # True
loader.is_valid_status("DRAFT", "daily_reports")  # False（已废弃）

# 获取所有合法值
print(loader.get_all_roles())
# frozenset({'admin', 'finance', 'data_operator', 'account_manager', 'media_buyer'})

print(loader.get_all_daily_report_states())
# frozenset({'raw_submitted', 'trend_pending', ..., 'final_locked'})

# 验证并获取建议
valid, msg = loader.validate_and_suggest("pitcher", "role")
if not valid:
    print(msg)
    # 输出: 无效角色 'pitcher'。有效角色: admin, account_manager, data_operator, finance, media_buyer
```

**加载的数据**:
- ✅ 5 个技术角色（从 backend/models/enums.py）
- ✅ 8 个日报状态（从 backend/models/enums.py）
- ✅ 充值请求状态（从 backend/models/enums.py）
- ✅ 账本状态（PENDING, CONFIRMED, REVERSED, LOCKED）
- ✅ 错误码前缀（VAL, AUTH, PERM, BUS, DATA, SYS, FIN, SOT）

---

### 3. AH 防幻觉检查器（AntiHallucinationChecker）

**文件**: `agents/skills/verifiers/anti_hallucination_checker.py`

**功能**:
实现 MASTER.md v4.4 §7 的 5 条防幻觉规则（AH-01 到 AH-05）

**检查规则**:

#### AH-01: 禁止假设数据一致
- ❌ 禁止直接修改 `balance` 字段 → 应通过 `ledger_entries`
- ❌ 禁止假设 `unit_price` 一定有值 → 应检查 `None`
- ❌ 禁止使用 `INNER JOIN` 不说明原因 → 应使用 `LEFT JOIN`
- ❌ 禁止设置状态不验证合法性

#### AH-02: 禁止自动管理裁决（Phase 1）
- ❌ 禁止自动拒绝请求（`status = 'rejected'`）
- ❌ 禁止自动暂停账户（`status = 'suspended'`）
- ❌ 禁止自动扣款/罚款

#### AH-03: 禁止引入 SoT 未定义概念
- ✅ 状态值必须在 STATE_MACHINE.md 中定义
- ✅ 角色必须在 5 个技术角色中
- ✅ 错误码前缀必须在 ERROR_CODES_SOT.md 中定义

#### AH-04: 必须遵循 Phase 1 软性原则
- ❌ 避免使用 `raise` 抛出业务异常（除非标注 `# Phase 2 only`）
- ✅ 使用提示/高亮而非错误

#### AH-05: 遇歧义停止并询问
- ❌ 禁止注释中出现"假设"、"推测"、"可能"、"不确定"
- ❌ 禁止 `TODO` / `FIXME` 注释
- ⚠️ 警告 magic number（应定义为常量）

**用法示例**:
```python
from agents.skills.verifiers.anti_hallucination_checker import AntiHallucinationChecker
from agents.skills.code_factory.phase_config import PhaseConfig
from agents.skills.code_factory.sot_loader import SotLoader
from pathlib import Path

# 初始化检查器
phase_config = PhaseConfig.from_env()
sot_loader = SotLoader(project_root=Path("."))
checker = AntiHallucinationChecker(
    phase_config=phase_config,
    sot_loader=sot_loader
)

# 待检查的代码
code = """
def update_balance(user_id: int, amount: float):
    user = User.query.get(user_id)
    user.balance -= amount  # AH-01 违规：直接修改 balance
    if amount > 1000:
        user.status = 'suspended'  # AH-02 违规：自动暂停（Phase 1 禁止）
    db.session.commit()
"""

# 运行所有检查
issues_by_rule = checker.check_all(code)

# 格式化报告
report = checker.format_report(issues_by_rule)
print(report)
```

**输出示例**:
```
============================================================
Anti-Hallucination Check Report
============================================================
Total: 2 Errors, 0 Warnings

[AH-01] - 1 issue(s)
------------------------------------------------------------
  Line 4 [ERROR]: 禁止直接修改 balance 字段
    建议: 应通过 ledger_entries 表记录流水，由触发器/视图自动计算 balance。参考 DATA_SCHEMA.md v5.11 §3.4.4

[AH-02] - 1 issue(s)
------------------------------------------------------------
  Line 6 [ERROR]: Phase 1 禁止自动暂停账户
    建议: 应发送通知，由管理员决定是否暂停

============================================================
```

---

## 集成到代码工厂

### 验证流程集成

在代码验证阶段（VERIFY Phase）添加新的检查层：

```
Layer 3: SpecComplianceVerifier
  └─> 使用 SotLoader 动态加载白名单

Layer 3.1: PhaseComplianceVerifier（新增）
  └─> 使用 PhaseConfig 检查 Phase 1/2 边界

Layer 7: AntiHallucinationChecker（新增）
  └─> 运行 AH-01~05 检查
```

### 环境变量配置示例

**开发环境（默认 Phase 1）**:
```bash
# .env.development
FACTORY_PHASE=phase1
# 所有 Phase 2 开关默认 false
```

**生产环境（启用 Phase 2）**:
```bash
# .env.production
FACTORY_PHASE=phase2
PHASE2_TOPUP_ENFORCEMENT=true
PHASE2_DAILY_REPORT_REQUIRED=true
PHASE2_WEEKLY_BRIEF_REQUIRED=true
PHASE2_SETTLEMENT_LOCK=true
```

---

## 测试验证

### 单元测试

```bash
# 测试 PhaseConfig
pytest agents/skills/code_factory/test_phase_config.py

# 测试 SotLoader
pytest agents/skills/code_factory/test_sot_loader.py

# 测试 AntiHallucinationChecker
pytest agents/skills/verifiers/test_anti_hallucination_checker.py
```

### 功能测试

```bash
# Phase 1 模式测试
export FACTORY_PHASE=phase1
/gen be 创建充值请求接口
# 预期：不生成自动拒绝逻辑

# Phase 2 模式测试
export FACTORY_PHASE=phase2
export PHASE2_TOPUP_ENFORCEMENT=true
/gen be 创建充值请求接口
# 预期：生成余额不足时阻断逻辑
```

---

## 版本历史

### v2.4 (2025-12-22)
- ✅ 新增 Phase 1/2 配置系统
- ✅ 新增 SoT 动态加载器
- ✅ 新增 AH-01~05 防幻觉检查器
- ✅ 更新 verifier 文档 baseline 到 MASTER.md v4.4

### v2.3 (2025-12-20)
- ✅ P0 对齐修复：5 角色 / 8 状态 / 删除无效文档引用

---

## 参考文档

- MASTER.md v4.4 - 宪法文档（§7 防幻觉规则，§8 Phase 定义）
- STATE_MACHINE.md v2.6 - 状态机规范
- DATA_SCHEMA.md v5.2 - 数据模式定义
- DATA_SCHEMA.md v5.11 §3.4.4 - 账本规则
- ERROR_CODES_SOT.md v2.1 - 错误码规范

---

**维护者**: Wade
**最后更新**: 2025-12-22
