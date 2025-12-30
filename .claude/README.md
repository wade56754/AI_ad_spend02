# Claude Code 项目配置说明

> **版本**: v2.0 | **更新日期**: 2025-12-30

---

## 🚀 快速开始

**新手必读**: [QUICK_START.md](./QUICK_START.md) - 5 分钟上手指南

---

## 📋 核心命令 (6 个)

| 命令 | 说明 | 示例 |
|------|------|------|
| `/gen` | 代码生成 | `/gen be 创建日报接口` |
| `/review` | 代码审查 | `/review backend/services/*.py --sot` |
| `/doc` | 文档生成 | `/doc api` |
| `/spec` | 规范管理 | `/spec proposal add-status` |
| `/flow` | 工作流 | `/flow be-dev 新功能` |
| `/help` | 帮助 | `/help` |

**完整命令索引**: [commands/INDEX.md](./commands/INDEX.md)

---

## 📚 SoT 文档体系

### 裁判链优先级

```
1. MASTER.md v4.6      → 系统全局规则
2. DATA_SCHEMA.md v5.6 → 数据库结构
3. STATE_MACHINE.md v2.8 → 状态机定义
4. BUSINESS_RULES.md v4.7 → 业务规则
5. API_SOT.md v9.4     → API 契约
6. ERROR_CODES_SOT.md v2.2 → 错误码
```

### 白名单速查

**8 状态**:
```
draft, pending_review, trend_pending, trend_ok,
real_pending, real_filled, final_pending, final_confirmed
```

**6 角色**:
```
ceo, admin, project_owner, finance, pitcher, account_manager
```

**错误码前缀** (16 个):
```
AUTH_, BIZ_, FIN_, LEDGER_, STATE_, VALIDATION_,
DB_, SYS_, API_, PERM_, RES_, DATA_, RECON_, REPORT_, RPT_, IMPORT_
```

---

## 🛡️ 防幻觉原则 (BLOCKING)

| 原则 | 规则 |
|------|------|
| AH-01 | 禁止假设数据一致，遇到缺失标记"待确认" |
| AH-02 | 禁止自动做管理裁决，不生成拒绝/暂停代码 |
| AH-03 | 禁止引入 SoT 未定义概念 |
| AH-04 | 必须遵循 Phase 1 软性原则（只提示不阻断） |
| AH-05 | 遇到歧义必须停止并询问 |

---

## 📂 目录结构

```
.claude/
├── QUICK_START.md       # 🚀 快速入门（新手必读）
├── README.md            # 本文件
├── PROJECT_RULES.md     # 完整项目规则
├── commands/            # 命令定义
│   ├── INDEX.md         # 命令索引
│   ├── gen-v2.md        # 代码生成
│   ├── review-v2.md     # 代码审查
│   ├── doc-v2.md        # 文档生成
│   ├── spec.md          # 规范管理
│   ├── flow.md          # 工作流
│   └── help.md          # 帮助系统
├── skills/              # 技能库（内部实现）
│   └── INDEX.md         # 技能索引
└── data/                # 运行时数据
```

---

## 🔗 相关文档

| 文档 | 说明 |
|------|------|
| [CLAUDE.md](../CLAUDE.md) | 根目录项目指令 |
| [docs/sot/MASTER.md](../docs/sot/MASTER.md) | SoT 总纲 |
| [memory-bank/](../memory-bank/) | 项目记忆库 |

---

## ⚡ 常用操作

```bash
# 生成后端代码
/gen be 创建日报接口

# 审查代码
/review backend/services/daily_report_service.py --sot

# 查看帮助
/help
```

---

**最后更新**: 2025-12-30 | **版本**: v2.0
