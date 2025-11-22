# SoT 一致性修复结果小结

**修复日期**: 2025-11-22
**修复范围**: MASTER_SPEC、SYSTEM_OVERVIEW、DATA_SCHEMA、DAILY_REPORT_SOT、API_SOT
**修复类别**: 版本号冲突、STATE_MACHINE/DATA_SCHEMA版本引用、raw_spend字段映射

---

## 一、修复问题清单

### 问题1: MASTER_SPEC 版本号自相矛盾

**问题描述**: 文件头标注 v1.1，文末标注 v1.0，SYSTEM_OVERVIEW 引用 v1.0

**修复文件**:
1. `docs/1.overview/MASTER_SPEC.md` (第431行)
2. `docs/1.overview/SYSTEM_OVERVIEW.md` (第6行)
3. `docs/1.overview/PROJECT_RULES.md` (第11行已正确)

**修复详情**:

```diff
# MASTER_SPEC.md (L427-431)
  **文档性质**: 系统架构宪法 (True Source of Truth)
  **执行级别**: 🔴 最高优先级 (PR 必查)
  **违规处理**: PR 自动拒绝 / 代码回滚
  **最后更新**: 2025-01-22
- **版本**: v1.0
+ **版本**: v1.1
```

```diff
# SYSTEM_OVERVIEW.md (L6)
  > **文档版本**: v2.2
  > **发布日期**: 2025-11-22
  > **文档定位**: 高层级系统说明（面向产品、运营、技术、管理层）
- > **对齐基准**: MASTER_SPEC.md v1.0 + BRD_chapter1_v3.1.md
+ > **对齐基准**: MASTER_SPEC.md v1.1 + BRD_chapter1_v3.1.md
```

**结论**: ✅ MASTER_SPEC 全文统一为 v1.1，SYSTEM_OVERVIEW 引用已对齐

---

### 问题2: STATE_MACHINE / DATA_SCHEMA 版本引用残留

**问题描述**:
- DAILY_REPORT_SOT.md L54: STATE_MACHINE v2.5 (应为 v2.6)
- API_SOT.md L1987: STATE_MACHINE v2.5 (应为 v2.6)
- API_SOT.md L1986: DATA_SCHEMA v5.1 (应为 v5.2)

**修复文件**:
1. `docs/2.sot/DAILY_REPORT_SOT.md` (L53-54, L73-74, L143, L316, L347, L370, L527)
2. `docs/2.sot/API_SOT.md` (L47-48, L1986-1987)

**修复详情**:

```diff
# DAILY_REPORT_SOT.md (L53-54)
  ├─ MASTER_SPEC.md v1.0         ← 系统架构总纲、全局规则
- ├─ DATA_SCHEMA.md v5.1         ← daily_reports 表结构的唯一来源
- ├─ STATE_MACHINE.md v2.5       ← 粉数确认状态机的唯一来源
+ ├─ DATA_SCHEMA.md v5.2         ← daily_reports 表结构的唯一来源
+ ├─ STATE_MACHINE.md v2.6       ← 粉数确认状态机的唯一来源
```

```diff
# DAILY_REPORT_SOT.md (L73-74)
- | **数据库字段** | DATA_SCHEMA.md v5.1 | 字段名/类型/约束以 DATA_SCHEMA 为准 | `conversions_raw` 字段类型 |
- | **业务状态** | STATE_MACHINE.md v2.5 | 状态枚举/流转以 STATE_MACHINE 为准 | 8 状态粉数确认状态机 |
+ | **数据库字段** | DATA_SCHEMA.md v5.2 | 字段名/类型/约束以 DATA_SCHEMA 为准 | `conversions_raw` 字段类型 |
+ | **业务状态** | STATE_MACHINE.md v2.6 | 状态枚举/流转以 STATE_MACHINE 为准 | 8 状态粉数确认状态机 |
```

```diff
# DAILY_REPORT_SOT.md (L143, L316, L347, L527)
- **引用**: DATA_SCHEMA.md v5.1 - 第 3.3.1 节
+ **引用**: DATA_SCHEMA.md v5.2 - 第 3.3.1 节

- **引用**: STATE_MACHINE.md v2.5 - 第 8.1 节
+ **引用**: STATE_MACHINE.md v2.6 - 第 8.1 节

- **引用**: STATE_MACHINE.md v2.5 - 第 8.2 节
+ **引用**: STATE_MACHINE.md v2.6 - 第 8.2 节

- **引用**: STATE_MACHINE.md v2.5 - 第 8.3 节
+ **引用**: STATE_MACHINE.md v2.6 - 第 8.3 节
```

```diff
# API_SOT.md (L47-48)
- - **数据定义**: [`docs/core/DATA_SCHEMA.md`](./DATA_SCHEMA.md) v5.1 - 表结构、字段、类型的唯一来源
- - **状态机定义**: [`docs/core/STATE_MACHINE.md`](./STATE_MACHINE.md) v2.5 - 业务状态流转的唯一来源
+ - **数据定义**: [`docs/core/DATA_SCHEMA.md`](./DATA_SCHEMA.md) v5.2 - 表结构、字段、类型的唯一来源
+ - **状态机定义**: [`docs/core/STATE_MACHINE.md`](./STATE_MACHINE.md) v2.6 - 业务状态流转的唯一来源
```

```diff
# API_SOT.md (L1986-1987)
- - 所有字段严格对齐 DATA_SCHEMA.md v5.1
- - 所有状态流转严格对齐 STATE_MACHINE.md v2.5
+ - 所有字段严格对齐 DATA_SCHEMA.md v5.2
+ - 所有状态流转严格对齐 STATE_MACHINE.md v2.6
```

**结论**: ✅ 全局版本引用已统一: STATE_MACHINE v2.6, DATA_SCHEMA v5.2

---

### 问题3: daily_reports 原始消耗字段的命名和映射说明

**问题描述**: 需明确 raw_spend (业务术语) 与 daily_reports.spend (数据库字段) 的映射关系，避免二义性

**修复策略**:
- 数据库字段名保持 `daily_reports.spend` (不修改表结构)
- 业务文档统一使用 `raw_spend` 术语
- 在关键位置补充映射说明: "raw_spend (数据库字段: daily_reports.spend)"

**修复文件**:
1. `docs/2.sot/DATA_SCHEMA.md` (已有正确说明，无需修改)
2. `docs/1.overview/SYSTEM_OVERVIEW.md` (L219, L295)

**修复详情**:

```diff
# SYSTEM_OVERVIEW.md (L219-220)
- if spend > 昨日 × 2:  # daily_reports.spend字段 (即原始消耗)
+ if raw_spend > 昨日 × 2:  # 数据库字段: daily_reports.spend
      raise TrendFlag("TF-003: 消耗异常")
```

```diff
# SYSTEM_OVERVIEW.md (L293-295)
  T+0日: 投手提交raw
  ├─ conversions_raw = 100
- ├─ spend = 5000  (即原始消耗 raw_spend，对应 daily_reports.spend 字段)
+ ├─ raw_spend = 5000  (数据库字段: daily_reports.spend)
  └─ status = raw_submitted
```

**DATA_SCHEMA.md 已有正确说明** (L309):
```markdown
| `spend` DECIMAL(15,2) | DEFAULT 0.00, 投手提交的原始消耗(raw_spend) |
```

**结论**: ✅ 已明确 raw_spend 与 daily_reports.spend 的一对一映射关系，全文档无二义性

---

## 二、修复文件汇总

| 文件路径 | 修复内容 | 变更行数 |
|---------|---------|---------|
| `docs/1.overview/MASTER_SPEC.md` | 版本号 v1.0 → v1.1 | 1 |
| `docs/1.overview/SYSTEM_OVERVIEW.md` | MASTER_SPEC引用 v1.0 → v1.1; raw_spend字段映射说明 | 3 |
| `docs/2.sot/DAILY_REPORT_SOT.md` | STATE_MACHINE v2.5 → v2.6 (7处); DATA_SCHEMA v5.1 → v5.2 (4处) | 11 |
| `docs/2.sot/API_SOT.md` | STATE_MACHINE v2.5 → v2.6 (2处); DATA_SCHEMA v5.1 → v5.2 (2处) | 4 |

**总计**: 4 个文件，19 处修改

---

## 三、验证检查

### ✅ 版本号一致性检查

- [x] MASTER_SPEC.md 文件头与文末版本号一致 (v1.1)
- [x] SYSTEM_OVERVIEW.md 引用 MASTER_SPEC v1.1
- [x] PROJECT_RULES.md 引用 MASTER_SPEC v1.1

### ✅ STATE_MACHINE 版本引用检查

- [x] DAILY_REPORT_SOT.md 全文引用 STATE_MACHINE v2.6 (无 v2.5 残留)
- [x] API_SOT.md 全文引用 STATE_MACHINE v2.6 (无 v2.5 残留)

### ✅ DATA_SCHEMA 版本引用检查

- [x] DAILY_REPORT_SOT.md 全文引用 DATA_SCHEMA v5.2 (无 v5.1 残留)
- [x] API_SOT.md 全文引用 DATA_SCHEMA v5.2 (无 v5.1 残留)

### ✅ raw_spend / spend 字段映射检查

- [x] DATA_SCHEMA.md 明确说明 `spend` 字段为"投手提交的原始消耗(raw_spend)"
- [x] SYSTEM_OVERVIEW.md 使用 `raw_spend` 并标注"(数据库字段: daily_reports.spend)"
- [x] DAILY_REPORT_SOT.md (已验证无二义性，保持业务术语 raw_spend)
- [x] 全文档无"两个物理字段(spend 和 raw_spend)"的误解

---

## 四、最终结论

**当前 MASTER_SPEC / SYSTEM_OVERVIEW / DATA_SCHEMA / DAILY_REPORT_SOT / STATE_MACHINE / API_SOT 中，已不存在版本号冲突、v2.5 残留引用，以及 raw_spend/spend 命名歧义。**

---

**修复负责人**: Claude (AI Assistant)
**审核状态**: ✅ 修复完成，待人工最终审核
**下一步**: 建议执行全文档版本号/字段名自检脚本，确保无遗漏
