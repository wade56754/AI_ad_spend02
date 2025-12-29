# AI 防幻觉规则 (Anti-Hallucination Rules)

> **来源**: MASTER.md v4.4 §7
> **版本**: v1.0
> **最后更新**: 2025-12-24
> **级别**: BLOCKING - 所有代码生成必须遵循

---

## 1. 核心原则 (AH-01 ~ AH-05)

| 原则 | 标题 | 规则 | 违反后果 |
|------|------|------|---------|
| **AH-01** | 禁止假设数据一致 | 遇到数据缺失，标记"待确认"，禁止自动填充或假设 | BLOCKING |
| **AH-02** | 禁止自动做管理裁决 | 禁止生成自动拒绝/暂停/终止/冻结代码 | BLOCKING |
| **AH-03** | 禁止引入 SoT 未定义概念 | 发现缺失 → 立即停止 → 询问用户 | BLOCKING |
| **AH-04** | 必须遵循 Phase 1 软性原则 | 仅提示+高亮+记录，不阻断 | WARNING |
| **AH-05** | 遇到歧义必须停止并询问 | 停止 → 列出歧义点 → 询问用户 | BLOCKING |

### 1.1 AH-01: 禁止假设数据一致

```python
# 正确做法
if data.field is None:
    logger.warning("字段缺失，标记为待确认")
    data.field = "待确认"  # 显式标记

# 错误做法 (BLOCKING)
if data.field is None:
    data.field = 0  # 自动假设为 0
```

### 1.2 AH-02: 禁止自动做管理裁决

```python
# 正确做法
if over_budget:
    logger.warning(f"超预算警告: {amount}")
    # 仅记录，不阻断

# 错误做法 (BLOCKING)
if over_budget:
    raise HTTPException(400, "超预算，拒绝操作")  # 自动拒绝
```

### 1.3 AH-03: 禁止引入 SoT 未定义概念

```python
# 正确做法 - 使用 SoT 定义的状态
from backend.models.enums import ReportStatus  # SoT: STATE_MACHINE.md

# 错误做法 (BLOCKING) - 自定义状态
class MyStatus(str, Enum):
    DRAFT = "draft"  # 未定义于 STATE_MACHINE.md
```

### 1.4 AH-04: 必须遵循 Phase 1 软性原则

```python
# 正确做法 - Phase 1: 仅记录和提示
if cpl > target_cpl * 1.3:
    logger.info(f"CPL 异常: {cpl} > {target_cpl * 1.3}")
    report.trend_flag = True
    report.trend_flag_reason = "CPL 超标 30%"
    # 继续执行，不阻断

# 错误做法 (WARNING) - Phase 2 行为
if cpl > target_cpl * 1.3:
    raise HTTPException(400, "CPL 超标，暂停项目")  # 自动阻断
```

### 1.5 AH-05: 遇到歧义必须停止并询问

```
遇到歧义时:
1. 立即停止当前操作
2. 生成歧义报告:
   - 歧义类型: 状态/角色/字段/规则
   - 歧义内容: 具体描述
   - 可能选项: 列出候选
3. 询问用户确认
4. 得到确认后继续
```

---

## 2. SoT 裁判链

```
优先级顺序 (高 → 低):

MASTER.md v4.4
    ↓
DATA_SCHEMA.md v5.2
    ↓
STATE_MACHINE.md v2.6
    ↓
BUSINESS_RULES.md v3.2
    ↓
API_SOT.md v9.0
    ↓
ERROR_CODES_SOT.md v2.1
```

**冲突解决规则**:
- 上层文档优先级高于下层
- 遇到冲突，以上层文档为准
- 无法确定时，停止并询问

---

## 3. 开发前 4 步检查

每次代码生成前，必须执行以下检查:

### Step 1: 边界确认
- [ ] 任务边界是否明确？
- [ ] 模块归属是否确定？(pitcher/finance/ad_account/project)
- [ ] 如有歧义 → 停止 → 询问 (AH-05)

### Step 2: SoT 查询
- [ ] 按裁判链顺序查询相关文档
- [ ] 确认状态值在 STATE_MACHINE.md 中存在
- [ ] 确认角色值在 7 角色白名单中
- [ ] 确认错误码在 ERROR_CODES_SOT.md 中
- [ ] 如发现缺失 → 停止 → 询问 (AH-03)

### Step 3: 现有代码定位
- [ ] 确认目标文件位置
- [ ] 检查是否有可复用代码
- [ ] 避免重复实现

### Step 4: 常量验证
- [ ] 状态值 → STATE_MACHINE.md 白名单
- [ ] 角色值 → 7 角色白名单
- [ ] 错误码 → ERROR_CODES_SOT.md 白名单

---

## 4. 禁止行为清单

| ID | 禁止行为 | 正确做法 | SoT 来源 |
|----|---------|---------|---------|
| F-001 | 自定义错误码 | 使用 ERROR_CODES_SOT.md 中定义的错误码 | ERROR_CODES_SOT.md v2.1 |
| F-002 | 发明新状态 | 使用 STATE_MACHINE.md 中定义的状态 | STATE_MACHINE.md v2.6 |
| F-003 | 直接修改 balance | 通过 ledger_entries 记录余额变更 | LEDGER_SOT.md v1.1 |
| F-004 | 绕过 BFF 直连数据库 | 前端只能通过 API 访问数据 | API_SOT.md v9.0 |
| F-005 | 使用非标准角色 | 仅使用 7 个标准角色 | MASTER.md v4.4 §2.4 |

### 代码反模式检测

```python
# 反模式 1: 硬编码旧状态 (违反 F-002)
class DailyReportStatus(str, Enum):
    DRAFT = "draft"  # 错误: 不在 8 状态机中

# 反模式 2: 直接修改余额 (违反 F-003)
ad_account.balance -= 100  # 错误: 必须通过 ledger

# 反模式 3: 自定义错误码 (违反 F-001)
raise HTTPException(400, "Invalid")  # 错误: 缺少标准错误码

# 反模式 4: 使用旧角色名 (违反 F-005)
if user.role == "media_buyer":  # 错误: 应使用 pitcher
```

---

## 5. 强制开发流程

```
Schema → Service → Router → Test
```

### 5.1 后端代码生成顺序

1. **Schema 层** (`backend/schemas/`)
   - Pydantic 模型定义
   - 字段必须与 DATA_SCHEMA.md 一致
   - 添加 SoT 注释

2. **Service 层** (`backend/services/`)
   - 业务逻辑实现
   - 状态转换必须遵循 STATE_MACHINE.md
   - 错误处理使用 ERROR_CODES_SOT.md

3. **Router 层** (`backend/routers/`)
   - API 端点定义
   - 必须与 API_SOT.md 一致
   - 权限检查使用 7 角色

4. **Test 层** (`backend/tests/`)
   - 单元测试覆盖
   - P0 功能 100% 覆盖
   - 边界测试

---

## 6. 常量定义检查表

### 6.1 日报状态机 (8 状态)

```python
# SoT: STATE_MACHINE.md v2.6 §2
REPORT_STATUS = frozenset([
    'raw_submitted',    # 投手提交原始粉数
    'trend_pending',    # 等待趋势风控检查
    'trend_ok',         # 趋势正常
    'trend_flagged',    # 趋势异常,需人工复核
    'trend_resolved',   # 运营确认异常已解决
    'final_pending',    # 等待最终粉数确认
    'final_confirmed',  # 最终粉数已确认
    'final_locked'      # 已进入计费,锁定(终态)
])
```

### 6.2 用户角色 (6 业务层 + 4 技术层)

```python
# SoT: PRD v2.2 业务层 6 角色
BUSINESS_ROLES = frozenset([
    'ceo',              # 老板 - 资金安全、公司盈亏、最终决策
    'project_owner',    # 项目负责人 - 日报审核、项目盈亏、资金使用效率
    'finance',          # 财务 - 资金出入准确、数据真实、对账
    'pitcher',          # 投手 - CPL 达标、日报准确、执行投放
    'account_manager',  # 户管 - 账户分配、账户状态监控
    'admin'             # 管理员 - 系统配置（不参与业务）
])

# SoT: MASTER.md v4.6 §INV-007 技术层 4 角色
TECHNICAL_ROLES = frozenset(['admin', 'finance', 'account_manager', 'media_buyer'])

# 废弃角色 (PRD v2.2)
DEPRECATED_ROLES = frozenset(['supervisor', 'data_operator'])
```

### 6.3 错误码前缀 (16 前缀)

```python
# SoT: ERROR_CODES_SOT.md v2.1
ERROR_PREFIXES = frozenset([
    # 通用错误 (6 个)
    'VAL',   # 验证错误
    'AUTH',  # 认证/授权错误
    'BIZ',   # 业务逻辑错误
    'DB',    # 数据库错误
    'INT',   # 集成错误
    'SYS',   # 系统错误

    # 模块专用错误 (10 个)
    'FIN',   # 财务错误
    'RPT',   # 日报错误
    'ACC',   # 账户错误
    'PRJ',   # 项目错误
    'PIT',   # 投手错误
    'TOP',   # 充值错误
    'IMP',   # 导入错误
    'EXP',   # 导出错误
    'REC',   # 对账错误
    'SET',   # 结算错误
])
```

---

## 7. Phase 1 行为约束

### 7.1 允许的行为

| 行为 | 说明 | 示例 |
|------|------|------|
| 记录 | 记录事件到日志 | `logger.info("CPL 超标")` |
| 提示 | 返回警告信息 | `warnings: ["CPL 超标 30%"]` |
| 高亮 | 前端显示标记 | `trend_flag: true` |
| 统计 | 数据汇总分析 | `abnormal_count: 5` |

### 7.2 禁止的行为

| 行为 | 说明 | 违反规则 |
|------|------|---------|
| 阻断 | 拒绝请求 | AH-02 |
| 拒绝 | 返回错误 | AH-02 |
| 暂停 | 暂停项目 | AH-02 |
| 冻结 | 冻结账户 | AH-02 |
| 自动拒绝 | 自动驳回 | AH-02 |
| 自动批准 | 自动通过 | AH-02 |

### 7.3 检测模式

```python
# 检查生成的代码是否包含以下模式:
FORBIDDEN_PATTERNS = [
    r'raise\s+HTTPException.*4\d\d',  # HTTP 4xx 错误
    r'raise\s+.*Error.*reject',       # 拒绝错误
    r'\.suspend\(\)',                  # 暂停方法
    r'\.freeze\(\)',                   # 冻结方法
    r'\.disable\(\)',                  # 禁用方法
    r'auto_approve',                   # 自动批准
    r'auto_reject',                    # 自动拒绝
]
```

---

## 8. 开发自检清单

代码生成完成后，必须逐项检查:

### 8.1 来源追溯检查

- [ ] 每个状态值可追溯到 STATE_MACHINE.md
- [ ] 每个角色值可追溯到 7 角色白名单
- [ ] 每个字段值可追溯到 DATA_SCHEMA.md
- [ ] 每个错误码可追溯到 ERROR_CODES_SOT.md
- [ ] 每个 API 调用在项目中存在

### 8.2 SoT 注释检查

- [ ] 所有状态枚举有 `# SoT: STATE_MACHINE.md#xxx` 注释
- [ ] 所有业务规则有 `# SoT: BUSINESS_RULES.md#BR-xxx` 注释
- [ ] 所有 API 端点有 `# SoT: API_SOT.md#xxx` 注释
- [ ] 所有错误码有 `# SoT: ERROR_CODES_SOT.md#xxx` 注释

### 8.3 Phase 1 合规检查

- [ ] 无自动阻断代码
- [ ] 无自动拒绝代码
- [ ] 无自动暂停代码
- [ ] 超标情况仅记录和提示

### 8.4 模块边界检查

- [ ] 确认模块归属 (pitcher/finance/ad_account/project)
- [ ] 写入表在该模块可写范围内
- [ ] 无跨模块写入操作

---

## 9. 歧义处理流程

```
┌─────────────────────────────────────────────────────────────┐
│                    歧义处理流程                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Step 1: 检测到歧义                                          │
│  ├── 状态值不在白名单中                                       │
│  ├── 角色值不在 7 角色中                                      │
│  ├── 字段值不在 DATA_SCHEMA 中                               │
│  ├── 规则编号不在 BUSINESS_RULES 中                          │
│  └── API 端点不在 API_SOT 中                                 │
│                                                             │
│  Step 2: 立即 BLOCKING                                       │
│  └── 停止当前操作，不继续生成代码                              │
│                                                             │
│  Step 3: 生成歧义报告                                         │
│  {                                                          │
│    "type": "STATE_AMBIGUITY",                               │
│    "content": "发现状态 'pending_review' 不在 8 状态机中",     │
│    "options": [                                              │
│      "使用 'trend_pending' (趋势待检查)",                     │
│      "使用 'final_pending' (最终待确认)",                     │
│      "新增状态到 STATE_MACHINE.md"                           │
│    ]                                                         │
│  }                                                          │
│                                                             │
│  Step 4: 等待用户确认                                         │
│  └── 用户选择选项或提供新指示                                  │
│                                                             │
│  Step 5: 继续执行                                             │
│  └── 按用户确认的方案继续                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|---------|
| v1.0 | 2025-12-24 | 初始版本，基于 MASTER.md v4.4 §7 创建 |

---

**维护者**: AI 代码工厂
**关联文档**: MASTER.md v4.4, STATE_MACHINE.md v2.6, DATA_SCHEMA.md v5.2
