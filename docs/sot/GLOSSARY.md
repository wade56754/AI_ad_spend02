# 术语汇总 (Glossary)

> **版本**: v1.1
> **最后更新**: 2026-01-02
> **来源**: MASTER.md v4.9, DATA_SCHEMA.md v5.11

---

## 角色术语 (6 角色)

| 术语 | 英文 | 定义 | 核心职责 |
|------|------|------|---------|
| **老板** | ceo | 公司最高决策者 | 资金安全、公司盈亏、最终决策 |
| **项目负责人** | project_owner | 项目盈亏责任人 | 项目盈亏、日报审核、资金使用效率 |
| **财务** | finance | 财务管理人员 | 资金出入准确、数据真实、对账 |
| **投手** | pitcher | 广告投放执行者 | CPL 达标、日报准确、执行投放 |
| **户管** | account_manager | 广告账户管理员 | 账户分配、账户状态监控 |
| **管理员** | admin | 系统管理员 | 系统配置（不参与业务） |

### 废弃角色

| 术语 | 英文 | 废弃原因 | 替代方案 |
|------|------|---------|---------|
| ~~主管~~ | supervisor | MASTER v4.6+ 废弃（PRD v5.1 仍包含但架构以 MASTER 为准） | 合并到 project_owner |
| ~~数据运营~~ | data_operator | 不在宪法中 | 不使用 |
| ~~媒体买手~~ | media_buyer | 技术层术语 | 业务层用 pitcher |

---

## 财务术语

### 资金相关

| 术语 | 英文 | 定义 | 计算公式 |
|------|------|------|---------|
| **可用资金** | available_funds | 账户当前可用于投放的资金 | `opening_balance + Σtopup - Σad_spend` |
| **期初余额** | opening_balance | 系统启用时的初始余额 | 首次录入值 |
| **充值金额** | topup_amount | 单次充值金额 | - |
| **平台消耗** | ad_spend | 广告平台实际消耗（不含手续费） | 平台数据 |
| **平台余额** | platform_balance | 平台后台显示的余额 | 需对账 |

### 弃用术语

| 弃用 | 统一为 | ADR |
|------|--------|-----|
| ~~可用余额~~ | 可用资金 | ADR-003 |
| ~~剩余资金~~ | 可用资金 | ADR-003 |
| ~~remaining_funds~~ | available_funds | ADR-003 |
| ~~available_balance~~ | available_funds | ADR-003 |

### 费用相关

| 术语 | 英文 | 定义 |
|------|------|------|
| **服务费** | service_fee | 代投服务收取的费用 |
| **手续费** | platform_fee | 平台收取的手续费 |
| **实际消耗** | real_spend | 广告平台实际扣费金额 |
| **充值手续费** | topup_fee | 充值时产生的手续费 |

### 收入与利润

| 术语 | 英文 | 定义 | 计算公式 |
|------|------|------|---------|
| **收入** | revenue | 服务收入 | 按模式计算 |
| **成本** | cost | 总成本 | `real_spend + fee` |
| **毛利** | gross_profit | 毛利润 | `revenue - cost` |
| **CPL** | cost_per_lead | 单个线索成本 | `ad_spend / conversions_final` |

### 收入模式

| 模式 | 英文 | 公式 |
|------|------|------|
| **按粉计费** | per_lead | `revenue = conversions_final × unit_price` |
| **费率计费** | fee_rate | `revenue = ad_spend × service_fee_rate` |

---

## 日报状态 (8 状态)

| 状态 | 英文 | 定义 | 可转换至 |
|------|------|------|---------|
| **原始提交** | raw_submitted | 投手提交原始粉数 | trend_pending |
| **趋势待检** | trend_pending | 等待趋势风控检查 | trend_ok, trend_flagged |
| **趋势正常** | trend_ok | 趋势检查通过 | final_pending |
| **趋势异常** | trend_flagged | 趋势异常，需人工复核 | trend_resolved |
| **异常已解决** | trend_resolved | 运营确认异常已解决 | final_pending |
| **最终待确认** | final_pending | 等待最终粉数确认 | final_confirmed |
| **最终已确认** | final_confirmed | 最终粉数已确认 | final_locked |
| **已锁定** | final_locked | 已进入计费，锁定（终态） | - |

> 来源: STATE_MACHINE.md v2.9 SM-1

---

## 账户状态

| 状态 | 英文 | 定义 |
|------|------|------|
| **正常** | active | 账户可正常使用 |
| **暂停** | suspended | 账户暂停使用 |
| **封禁** | banned | 账户被平台封禁 |

---

## 充值状态

| 状态 | 英文 | 定义 |
|------|------|------|
| **待处理** | pending | 充值待处理 |
| **已完成** | completed | 充值已完成 |
| **已取消** | cancelled | 充值已取消 |

> 来源: STATE_MACHINE.md v2.9 SM-2

---

## 对账状态

| 状态 | 英文 | 定义 |
|------|------|------|
| **待对账** | pending | 等待对账 |
| **已匹配** | matched | 数据匹配 |
| **有差异** | discrepancy | 数据有差异 |
| **已调整** | adjusted | 差异已调整 |
| **已确认** | confirmed | 对账已确认 |

> 来源: STATE_MACHINE.md v2.9 SM-3

---

## 技术术语

### SoT 相关

| 术语 | 英文 | 定义 |
|------|------|------|
| **真相源** | Source of Truth (SoT) | 权威数据/规范来源 |
| **裁判链** | Arbitration Chain | SoT 优先级顺序 |
| **不变量** | Invariant | 绝对不能违反的约束 |
| **防幻觉** | Anti-Hallucination | 防止 AI 生成错误内容的机制 |

### Phase 阶段

| 术语 | 英文 | 定义 |
|------|------|------|
| **Phase 1** | Illuminate Phase | 照亮阶段：只提示、不阻断 |
| **Phase 2** | Enforce Phase | 强制阶段：规则强制执行 |

> 来源: ADR-002

---

## 缩写对照

| 缩写 | 全称 | 中文 |
|------|------|------|
| CPL | Cost Per Lead | 单粉成本 |
| ROAS | Return On Ad Spend | 广告支出回报率 |
| SoT | Source of Truth | 真相源 |
| ADR | Architecture Decision Record | 架构决策记录 |
| BR | Business Rule | 业务规则 |
| SM | State Machine | 状态机 |

---

## 相关文档

- [MASTER.md](./MASTER.md) - 系统宪法
- [DATA_SCHEMA.md](./DATA_SCHEMA.md) - 数据模型
- [STATE_MACHINE.md](./STATE_MACHINE.md) - 状态机规范
- [ADR-003](../adr/003-可用资金术语统一.md) - 术语统一决策

---

**维护周期**: 每次新增/变更术语后更新
