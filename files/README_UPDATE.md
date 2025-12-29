# README.md 更新章节

> 此文件包含需要添加/更新到 README.md 的内容
> 请将以下内容合并到现有 README.md 中

---

## 📂 项目结构（更新版）

```
AI_ad_spend02/
├── README.md                    # 本文件
├── CLAUDE.md                    # AI编程记忆（极简）
├── justfile                     # 跨平台命令入口
│
├── docs/
│   ├── sot/                     # 📌 SoT唯一真相源
│   │   ├── MASTER.md            # 规格总纲（最高优先级）
│   │   ├── INDEX.md             # 模块→规格映射（开发必查）
│   │   ├── CHANGELOG.md         # 变更记录
│   │   ├── STATE_MACHINE.md     # 状态机定义
│   │   ├── DATA_SCHEMA.md       # 数据模型
│   │   ├── LEDGER_SOT.md        # 账本规格
│   │   ├── API_SOT.md           # API规格
│   │   └── ...
│   │
│   ├── adr/                     # 架构决策记录
│   ├── releases/                # 发布归档
│   ├── runbooks/                # 运维手册
│   ├── 1.overview/              # 项目概述
│   ├── 3.dev-guides/            # 开发指南
│   └── 4.architecture/          # 架构视图
│
├── .ai-rules/                   # AI编程规则
│   ├── engineering.md           # 工程规范
│   └── quality-gates.md         # 质量门禁
│
├── backend/                     # 后端服务
├── frontend/                    # 前端应用
├── scripts/                     # 工具脚本
└── tests/                       # 测试代码
```

---

## 🚀 快速开始

### 使用 justfile（推荐）

```bash
# 查看所有可用命令
just --list

# 启动开发环境
just dev

# 运行测试
just test

# CI门禁检查
just ci-check
```

### 不使用 just

```bash
# 后端
cd backend && uvicorn main:app --reload --port 8000

# 前端
cd frontend && npm run dev

# 测试
cd backend && pytest
```

---

## 📖 文档导航

### 开发前必读

| 文档 | 位置 | 用途 |
|------|------|------|
| **INDEX.md** | `docs/sot/INDEX.md` | 找到对应模块的SoT章节 |
| **MASTER.md** | `docs/sot/MASTER.md` | 规格总纲 |
| **engineering.md** | `.ai-rules/engineering.md` | 工程规范 |

### SoT裁判链

```
MASTER.md → STATE_MACHINE.md → DATA_SCHEMA.md → LEDGER_SOT.md 
→ BUSINESS_RULES.md → API_SOT.md → ERROR_CODES_SOT.md → AUTH_SPEC.md
```

遇到冲突时，按此优先级以前者为准。

---

## 🔧 开发规范

### 开发前检查清单

```markdown
[ ] 查 docs/sot/INDEX.md 找到对应规格章节
[ ] 确认状态机是否符合
[ ] 确认公式是否正确
[ ] 确认权限是否符合数据域
```

### 开发后检查清单

```markdown
[ ] 权限：投手只能操作自己账户
[ ] 权限：项目负责人只能操作自己项目
[ ] 状态机：状态流转符合SM-1/SM-2/SM-3
[ ] 金额：可用资金公式正确（含opening_balance）
[ ] 金额：平台消耗不含手续费
[ ] 锁定：locked状态数据不可修改
[ ] 红冲：有ref_id和reason
[ ] Phase 1：只提示不阻断
```

---

## 📋 PR门禁

每个PR必须通过：

| 门禁 | 命令 | 要求 |
|------|------|------|
| 单元测试 | `pytest -q --cov` | 通过且覆盖率≥70% |
| 代码检查 | `ruff check . && ruff format --check .` | 无错误 |
| 类型检查 | `mypy backend/` | 无错误 |
| 迁移检查 | `python scripts/check_migration.py` | 可回滚 |
| 变更记录 | `python scripts/check_changelog.py` | 已更新 |

---

## 🏗️ 架构决策

重要架构决策记录在 `docs/adr/` 目录：

| ADR | 决策 |
|-----|------|
| ADR-001 | 采用7角色模型 |
| ADR-002 | Phase 1只提示不阻断 |
| ADR-003 | 统一术语为"可用资金" |

---

## 📞 联系方式

- 📧 Email: support@ai-ad-spend.com
- 🐛 Issues: [GitHub Issues](https://github.com/wade56754/AI_ad_spend02/issues)

---

**文档版本**: v4.1.0 (2025-12-27 结构重组后)
