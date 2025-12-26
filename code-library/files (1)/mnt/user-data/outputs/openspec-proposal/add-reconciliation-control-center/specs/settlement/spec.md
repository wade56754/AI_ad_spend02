# Spec Delta: Settlement Rules Capability

**Change-ID**: `add-reconciliation-control-center`
**Capability**: `settlement`
**Affected SoT**: DATA_SCHEMA.md, BUSINESS_RULES.md, ERROR_CODES_SOT.md

---

## ADDED Requirements

### Requirement: Settlement Type Support

系统 SHALL 支持三种结算类型：fixed、tiered、markup。

#### Scenario: Project with fixed settlement
- **GIVEN** 项目 settlement_type = 'fixed'
- **AND** 项目 unit_price = 50.00
- **WHEN** 日报 conversions_final = 100
- **THEN** 计算收入 = 100 × 50.00 = 5000.00

#### Scenario: Project with tiered settlement (incremental)
- **GIVEN** 项目 settlement_type = 'tiered'
- **AND** 结算规则配置为 incremental 模式:
  ```json
  {
    "tiers": [
      {"min": 0, "max": 1000, "price": 50},
      {"min": 1001, "max": 5000, "price": 45},
      {"min": 5001, "max": null, "price": 40}
    ],
    "calculation_basis": "incremental"
  }
  ```
- **WHEN** 日报 conversions_final = 3000
- **THEN** 计算收入 = 1000×50 + 2000×45 = 50000 + 90000 = 140000

#### Scenario: Project with tiered settlement (cumulative)
- **GIVEN** 项目 settlement_type = 'tiered'
- **AND** 结算规则配置为 cumulative 模式:
  ```json
  {
    "tiers": [
      {"min": 0, "max": 1000, "price": 50},
      {"min": 1001, "max": 5000, "price": 45},
      {"min": 5001, "max": null, "price": 40}
    ],
    "calculation_basis": "cumulative"
  }
  ```
- **WHEN** 日报 conversions_final = 3000
- **THEN** 计算收入 = 3000 × 45 = 135000（按达到的阶梯价格）

#### Scenario: Project with markup settlement (percentage)
- **GIVEN** 项目 settlement_type = 'markup'
- **AND** 结算规则配置:
  ```json
  {
    "base_cost_field": "real_spend",
    "markup_type": "percentage",
    "markup_value": 15
  }
  ```
- **WHEN** 日报 real_spend = 10000.00
- **THEN** 计算收入 = 10000 × (1 + 15%) = 11500.00

#### Scenario: Project with markup settlement (fixed)
- **GIVEN** 项目 settlement_type = 'markup'
- **AND** 结算规则配置:
  ```json
  {
    "base_cost_field": "real_spend",
    "markup_type": "fixed",
    "markup_value": 500
  }
  ```
- **WHEN** 日报 real_spend = 10000.00
- **THEN** 计算收入 = 10000 + 500 = 10500.00

---

### Requirement: Settlement Rule Management

系统 SHALL 支持结算规则的创建和管理。

#### Scenario: Create tiered rule
- **GIVEN** 用户角色为 finance 或 admin
- **WHEN** 用户创建 tiered 类型结算规则
- **AND** 阶梯配置连续无缝隙
- **THEN** 系统创建结算规则
- **AND** 记录 effective_from 生效日期

#### Scenario: Invalid tiered config rejected
- **GIVEN** 用户创建 tiered 结算规则
- **WHEN** 阶梯配置存在缝隙（如 max=1000 后 min=1002）
- **THEN** 系统返回 HTTP 400
- **AND** 错误码 SET-001

#### Scenario: Apply rule to project
- **GIVEN** 存在有效的结算规则
- **AND** 项目 settlement_type = 'tiered' 或 'markup'
- **WHEN** 用户关联结算规则到项目
- **THEN** 项目 settlement_rules_id 更新
- **AND** 后续收入计算使用新规则

#### Scenario: Missing rule for non-fixed project
- **GIVEN** 项目 settlement_type = 'tiered'
- **AND** 项目 settlement_rules_id = NULL
- **WHEN** 系统尝试计算收入
- **THEN** 返回 HTTP 400
- **AND** 错误码 SET-004

#### Scenario: Rule effective period conflict
- **GIVEN** 项目已关联生效期为 [2025-01-01, 2025-06-30] 的规则
- **WHEN** 用户尝试关联生效期为 [2025-03-01, 2025-12-31] 的规则
- **THEN** 系统返回 HTTP 400
- **AND** 错误码 SET-003

---

### Requirement: Revenue Calculation API

系统 SHALL 提供统一的收入计算接口。

#### Scenario: Calculate project revenue
- **GIVEN** 项目存在有效的结算配置
- **AND** 指定日期范围内存在已锁定的日报
- **WHEN** 用户调用收入计算 API
- **THEN** 系统返回：
  - total_conversions: 总粉数
  - total_revenue: 总收入
  - breakdown: 按日期的明细

#### Scenario: Calculate with multiple rules in period
- **GIVEN** 计算期间跨越多个结算规则生效期
- **WHEN** 用户调用收入计算 API
- **THEN** 系统按各规则生效期分段计算
- **AND** 返回分段明细

---

## MODIFIED Requirements

### Requirement: Project Extended Fields

修改现有 projects 表，新增结算类型相关字段。

#### Scenario: Project default settlement type
- **GIVEN** 创建新项目
- **WHEN** 未指定 settlement_type
- **THEN** 默认值为 'fixed'
- **AND** 使用 unit_price 字段计算收入

#### Scenario: Change settlement type
- **GIVEN** 项目 settlement_type = 'fixed'
- **AND** 用户角色为 finance 或 admin
- **WHEN** 用户修改 settlement_type 为 'tiered'
- **AND** 关联有效的结算规则
- **THEN** 项目结算类型更新
- **AND** 后续新日报使用新规则计算

#### Scenario: Settlement type validation
- **GIVEN** 项目 settlement_type 字段
- **WHEN** 尝试设置为无效值（如 'custom'）
- **THEN** 系统返回 HTTP 400
- **AND** 错误码 SET-002

---

## Tiered Config Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["tiers", "calculation_basis"],
  "properties": {
    "tiers": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["min", "max", "price"],
        "properties": {
          "min": { "type": "integer", "minimum": 0 },
          "max": { "type": ["integer", "null"], "minimum": 1 },
          "price": { "type": "number", "minimum": 0 }
        }
      }
    },
    "calculation_basis": {
      "type": "string",
      "enum": ["cumulative", "incremental"]
    }
  }
}
```

## Markup Config Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["base_cost_field", "markup_type", "markup_value"],
  "properties": {
    "base_cost_field": {
      "type": "string",
      "enum": ["real_spend", "raw_spend"]
    },
    "markup_type": {
      "type": "string",
      "enum": ["percentage", "fixed"]
    },
    "markup_value": {
      "type": "number",
      "minimum": 0
    }
  }
}
```

---

## Error Codes Reference

| 错误码 | HTTP | 场景 |
|--------|------|------|
| SET-001 | 400 | 阶梯配置无效（不连续） |
| SET-002 | 400 | 结算类型不支持 |
| SET-003 | 400 | 生效期冲突 |
| SET-004 | 400 | 结算规则缺失 |

---

**END OF SPEC**
