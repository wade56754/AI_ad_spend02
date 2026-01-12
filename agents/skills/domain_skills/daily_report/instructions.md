# 日报管理技能 - 核心指令

> **SoT 引用**: STATE_MACHINE.md v2.8, DATA_SCHEMA.md v5.7

## 日报 8 状态机

```
raw_submitted    # 投手提交原始数据
    ↓
trend_pending    # 趋势风控检测中
    ↓
trend_ok         # 趋势正常
trend_flagged    # 趋势异常 → 需运营复核
    ↓
trend_resolved   # 运营确认正常波动
    ↓
final_pending    # 等待最终确认
    ↓
final_confirmed  # 运营确认最终粉数
    ↓
final_locked     # 计费锁定 (终态)
```

## 核心字段

| 字段 | 类型 | 说明 | SoT |
|------|------|------|-----|
| `spend` | Decimal | 消耗金额 | DATA_SCHEMA.md#daily_reports.spend |
| `conversions` | Integer | 转化数 (粉数) | DATA_SCHEMA.md#daily_reports.conversions |
| `conversions_final` | Integer | 最终粉数 | DATA_SCHEMA.md#daily_reports.conversions_final |
| `status` | String | 状态 | STATE_MACHINE.md#daily_report |

## 关键约束

1. **状态白名单**: 只能使用上述 8 种状态
2. **禁止使用旧状态**: `draft`, `pending`, `approved` 已废弃
3. **Phase 1 约束**: 趋势异常只能提示，不能自动阻断
4. **计费 SoT**: 成本使用 `ad_spend_daily.spend`，**不是** `daily_report.spend`

## 代码模板

### 状态枚举 (Python)

```python
# SoT: STATE_MACHINE.md#daily_report
class DailyReportStatus(str, Enum):
    RAW_SUBMITTED = "raw_submitted"
    TREND_PENDING = "trend_pending"
    TREND_OK = "trend_ok"
    TREND_FLAGGED = "trend_flagged"
    TREND_RESOLVED = "trend_resolved"
    FINAL_PENDING = "final_pending"
    FINAL_CONFIRMED = "final_confirmed"
    FINAL_LOCKED = "final_locked"
```

### 状态徽章 (TypeScript)

```typescript
// SoT: STATE_MACHINE.md#daily_report
const DAILY_REPORT_STATUS_COLORS = {
  raw_submitted: 'blue',
  trend_pending: 'yellow',
  trend_ok: 'green',
  trend_flagged: 'red',
  trend_resolved: 'cyan',
  final_pending: 'orange',
  final_confirmed: 'green',
  final_locked: 'gray',
} as const;
```
