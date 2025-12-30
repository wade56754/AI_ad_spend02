---
description: "帮助: 显示所有可用命令和使用示例"
argument-hint: "[command-name]"
---

# 帮助系统

## 使用方式

```bash
/help           # 显示所有命令
/help gen       # 显示 gen 命令详情
/help sot       # 显示 SoT 相关信息
```

## 命令速查表

### 代码生成
| 命令 | 说明 | 示例 |
|------|------|------|
| `/gen be <task>` | 生成后端代码 | `/gen be 创建日报接口` |
| `/gen fe <task>` | 生成前端代码 | `/gen fe 日报列表页` |
| `/gen test <task>` | 生成测试代码 | `/gen test 日报流转测试` |

### 代码审查
| 命令 | 说明 | 示例 |
|------|------|------|
| `/review <file>` | 审查代码质量 | `/review backend/services/daily_report_service.py` |
| `/sot-check <file>` | 检查 SoT 合规 | `/sot-check backend/routers/daily_reports.py` |

### 文档操作
| 命令 | 说明 | 示例 |
|------|------|------|
| `/doc <type>` | 生成文档 | `/doc api` |

### 工作流
| 命令 | 说明 | 示例 |
|------|------|------|
| `/flow <type>` | 执行工作流 | `/flow be-dev` |
| `/restart` | 重启开发服务 | `/restart` |

## 模块判断指南

```
问: 我的任务属于哪个模块?

┌─────────────────────────────────────────┐
│ 涉及日报、投放、CPL、投手?              │
│   → pitcher 模块                        │
├─────────────────────────────────────────┤
│ 涉及充值、流水、账本、对账?              │
│   → finance 模块                        │
├─────────────────────────────────────────┤
│ 涉及广告账户、开户、授权?                │
│   → ad_account 模块                     │
├─────────────────────────────────────────┤
│ 涉及项目、成员、权限分配?                │
│   → project 模块                        │
└─────────────────────────────────────────┘
```

## SoT 白名单速查

### 8 个状态
```
draft, pending_review, trend_pending, trend_ok,
real_pending, real_filled, final_pending, final_confirmed
```

### 6 个角色
```
ceo, admin, project_owner, finance, pitcher, account_manager
```

### 错误码前缀
```
AUTH_, BIZ_, FIN_, LEDGER_, STATE_, VALIDATION_,
DB_, SYS_, API_, PERM_, RES_, DATA_, RECON_, REPORT_, RPT_, IMPORT_
```

## 常见问题

**Q: 生成的代码报错怎么办?**
A: 运行 `/review <file>` 检查问题，或查看 lint 输出

**Q: 不确定状态值对不对?**
A: 查看上方 SoT 白名单，或运行 `/sot-check <file>`

**Q: 如何查看完整文档?**
A: 阅读 `.claude/QUICK_START.md` 或 `docs/sot/MASTER.md`
