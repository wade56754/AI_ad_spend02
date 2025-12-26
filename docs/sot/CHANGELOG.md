# SoT 变更记录

> 本文件记录 `docs/sot/` 下所有规格文档的变更历史。
> 格式遵循 [Keep a Changelog](https://keepachangelog.com/)。

---

## [Unreleased]

### 待定
- 无

---

## [v2.0.3] - 2025-12-27

### 新增
- INDEX.md: 模块→规格映射索引
- CHANGELOG.md: 本文件

### 变更
- MASTER.md: 从 docs/1.overview/ 移动到 docs/sot/
- 所有SoT文件: 从 docs/sot/ 移动到 docs/sot/

### 文档结构
```
docs/sot/
├── MASTER.md           # 规格总纲
├── INDEX.md            # 模块映射 (新增)
├── CHANGELOG.md        # 变更记录 (新增)
├── STATE_MACHINE.md    # 状态机
├── DATA_SCHEMA.md      # 数据模型
├── API_SOT.md          # API规格
├── BUSINESS_RULES.md   # 业务规则
├── ERROR_CODES_SOT.md  # 错误码
└── AUTH_SPEC.md        # 认证规格
```

---

## [v2.0.2] - 2025-12-27

### 变更
- 解决 Q-001: 阶梯定价边界规则（左闭右开）
- R-REV-001 扩展: 红冲范围增加"平台消耗"
- R-RECON-002 修正: 公式含期初基准

### 新增
- AdAccount.opening_balance: 期初余额字段
- AdAccount.opening_balance_date: 期初余额日期
- BalanceSnapshot.correction_reason: 更正原因

### 修复
- 供应链对账公式缺少期初基准的问题

---

## [v2.0.1] - 2025-12-26

### 变更
- 术语统一为"可用资金"（替代"可用余额""剩余资金"等）
- 日报状态机简化为6状态

### 修复
- 成本确认职责明确（户管T+1确认）

---

## [v2.0.0] - 2025-12-26

### 重大变更
- PRD与SoT合并为统一规格文档
- 篇幅精简80%
- 统一术语表

### 结构
```
Part A: 事实表（FACTS）
Part B: 规则表（RULES）
Part C: 验收表（ACCEPTANCE）
Part D: 待定表（TBD）
```

---

## [v1.2] - 2025-12-26

### 新增
- D001-D005 业务决策整合到FACTS_TABLE/RULE_TABLE/OPEN_QUESTIONS结构

---

## [v1.1] - 2025-12-26

### 修复
- Q-011: 手续费确认时机
- Q-012: 财务月结复核定义

---

## [v1.0] - 2025-12-26

### 初始版本
- PRD v1.0 发布
- 核心业务流程定义
- 7角色权限定义

---

## 变更类型说明

- **新增**: 新功能、新规则、新字段
- **变更**: 现有功能的修改
- **弃用**: 即将移除的功能
- **移除**: 已删除的功能
- **修复**: Bug修复
- **安全**: 安全相关更新

---

## 版本号规则

- **主版本号**: 不兼容的架构变更
- **次版本号**: 向后兼容的功能新增
- **修订号**: 向后兼容的问题修复

---

## 如何更新

1. 每次修改SoT文档时，同步更新本CHANGELOG
2. 在 `[Unreleased]` 区域记录变更
3. 发布时移动到对应版本号下
4. PR标题格式: `docs(sot): [变更类型] 简述`

示例:
```
docs(sot): [新增] INDEX.md 模块映射
docs(sot): [修复] R-RECON-002 公式缺少期初基准
```
