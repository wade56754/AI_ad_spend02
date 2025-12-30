# AI 编程助手快速入门

> **5 分钟上手指南**

---

## 1. 最常用命令

```bash
# 生成后端代码
/gen be 创建日报提交接口

# 生成前端代码
/gen fe 日报列表页面

# 代码审查
/review backend/services/daily_report_service.py

# 查看帮助
/help
```

---

## 2. 模块判断（必读）

开始任何任务前，先确定模块归属:

| 你的任务涉及... | 归属模块 | 主要文件 |
|----------------|----------|----------|
| 日报、投放、CPL | `pitcher` | `daily_reports.py` |
| 充值、流水、账本 | `finance` | `ledger_service.py` |
| 广告账户、开户 | `ad_account` | `ad_accounts.py` |
| 项目、成员权限 | `project` | `projects.py` |

---

## 3. SoT 白名单（必记）

### 状态 (8 个)
```
draft → pending_review → trend_pending → trend_ok
     → real_pending → real_filled → final_pending → final_confirmed
```

### 角色 (6 个)
```
ceo, admin, project_owner, finance, pitcher, account_manager
```

### 错误码前缀 (16 个)
```
AUTH_, BIZ_, FIN_, LEDGER_, STATE_, VALIDATION_,
DB_, SYS_, API_, PERM_, RES_, DATA_, RECON_, REPORT_, RPT_, IMPORT_
```

---

## 4. 防幻觉检查清单

生成代码前，确保:

- [ ] 状态值在 8 状态白名单中
- [ ] 角色值在 6 角色白名单中
- [ ] 错误码使用 16 前缀之一
- [ ] 无自动阻断代码（不用 `reject()`, `suspend()`, `freeze()`）
- [ ] Phase 1 原则：只提示、不阻断

---

## 5. 典型工作流

```
1. 确定模块归属
   └─ 不确定? 问 Claude 或查上表

2. 生成代码
   └─ /gen be <任务描述>

3. 检查生成结果
   └─ /review <文件路径>

4. 运行测试
   └─ pytest backend/tests/

5. 提交代码
   └─ git add && git commit
```

---

## 6. 遇到问题?

| 问题 | 解决方案 |
|------|----------|
| 状态值不确定 | 查看 `docs/sot/STATE_MACHINE.md` |
| 角色权限不清 | 查看 `docs/sot/AUTH_SPEC.md` |
| API 格式不对 | 查看 `docs/sot/API_SOT.md` |
| 错误码不存在 | 查看 `docs/sot/ERROR_CODES_SOT.md` |

或直接运行 `/help` 获取帮助。

---

## 7. 进阶阅读

- 完整规则: `.claude/PROJECT_RULES.md`
- SoT 文档: `docs/sot/MASTER.md`
- 技能索引: `.claude/skills/INDEX.md`
