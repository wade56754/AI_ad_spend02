# 常见问题解答 (FAQ)

> **版本**: v1.0
> **最后更新**: 2025-12-30
> **维护者**: 架构组

---

## 目录

1. [SoT 相关](#sot-相关)
2. [角色相关](#角色相关)
3. [状态机相关](#状态机相关)
4. [Skills/Commands 相关](#skillscommands-相关)
5. [开发流程相关](#开发流程相关)
6. [防幻觉相关](#防幻觉相关)

---

## SoT 相关

### Q1: 什么是 SoT？

**A**: SoT (Source of Truth) 是"真相源"，指项目中权威的数据和规范来源。所有开发必须基于 SoT 文档，禁止凭想象实现功能。

主要 SoT 文档：
- `MASTER.md` - 系统宪法
- `DATA_SCHEMA.md` - 数据模型
- `STATE_MACHINE.md` - 状态机规范
- `BUSINESS_RULES.md` - 业务规则

### Q2: SoT 裁判链是什么？

**A**: 当多个 SoT 文档有冲突时，按以下优先级裁决：

```
MASTER.md > DATA_SCHEMA.md > STATE_MACHINE.md > BUSINESS_RULES.md > API_SOT.md
```

高优先级文档的规则覆盖低优先级文档。

### Q3: 如何引用 SoT？

**A**: 在代码和文档中引用 SoT 时，必须包含版本号：

```python
# 正确
# SoT: MASTER.md v4.6 §2.4

# 错误
# SoT: MASTER.md §2.4
```

### Q4: 发现 SoT 缺失怎么办？

**A**: 按照 AH-03 原则处理：
1. 立即停止当前操作
2. 记录缺失内容
3. 询问用户/业务确认
4. 获得确认后继续

**禁止**凭想象补充规范。

---

## 角色相关

### Q5: 系统有哪些角色？

**A**: 系统定义 6 个角色（MASTER.md v4.6 §2.4）：

| 角色 | 英文 | 核心职责 |
|------|------|---------|
| 老板 | ceo | 资金安全、公司盈亏、最终决策 |
| 项目负责人 | project_owner | 项目盈亏、日报审核 |
| 财务 | finance | 资金出入准确、对账 |
| 投手 | pitcher | CPL 达标、日报准确 |
| 户管 | account_manager | 账户分配、状态监控 |
| 管理员 | admin | 系统配置 |

### Q6: supervisor 角色去哪了？

**A**: `supervisor` 角色已在 PRD v5.1 中废弃，其职责合并到 `project_owner`。

如果在代码中看到 `supervisor`，应替换为 `project_owner`。

### Q7: media_buyer 和 pitcher 有什么区别？

**A**:
- `media_buyer` 是技术层术语（数据库/API）
- `pitcher` 是业务层术语（用户界面/文档）

在业务文档和用户界面中应使用 `pitcher`。

---

## 状态机相关

### Q8: 日报有哪些状态？

**A**: 日报有 8 个状态（STATE_MACHINE.md v2.8 SM-1）：

```
raw_submitted → trend_pending → trend_ok → final_pending → final_confirmed → final_locked
                            ↘ trend_flagged → trend_resolved ↗
```

### Q9: final_locked 状态可以修改吗？

**A**: 不可以。`final_locked` 是终态，数据已进入计费，只能通过**红冲**操作进行调整（需要 ref_id 和 reason）。

### Q10: Phase 1 和 Phase 2 有什么区别？

**A**:
- **Phase 1（照亮阶段）**: 只提示、不阻断，记录问题但允许继续
- **Phase 2（强制阶段）**: 规则强制执行，违规会阻断操作

当前系统处于 **Phase 1**。

---

## Skills/Commands 相关

### Q11: 如何查看所有可用命令？

**A**: 查看 `.claude/CAPABILITIES.md` 或运行：

```
/help
```

常用命令：
- `/gen be <task>` - 生成后端代码
- `/gen fe <task>` - 生成前端代码
- `/review <file>` - 代码审查
- `/sot-check <file>` - SoT 合规检查

### Q12: Skill 和 Agent 有什么区别？

**A**:

| 维度 | Skills | Agents |
|------|--------|--------|
| 执行方式 | 单次调用 | 持续循环 |
| 状态管理 | 无状态 | 有状态 |
| 适用场景 | 明确任务 | 复杂任务 |

### Q13: 如何添加新的 Skill？

**A**:
1. 在 `.claude/skills/` 下创建目录
2. 添加 `SKILL.md` 文件（含 YAML Frontmatter）
3. 更新 `.claude/skills/INDEX.md`
4. 更新 `.claude/CAPABILITIES.md`

---

## 开发流程相关

### Q14: 开发前必须做什么？

**A**: 按 CLAUDE.md 要求：

1. 读 `memory-bank/architecture.md` 了解项目结构
2. 读 `memory-bank/prd.md` 了解需求
3. 查 `docs/sot/MASTER.md` 确认规则
4. 查对应的 `BR-*.md` 获取详细业务规则

### Q15: 功能完成后必须做什么？

**A**:
1. 更新 `memory-bank/progress.md` 记录完成状态
2. 更新 `memory-bank/architecture.md`（如有新文件）
3. Git 提交

### Q16: Memory Bank 是什么？

**A**: Memory Bank 是项目记忆库，包含：

| 文件 | 用途 |
|------|------|
| progress.md | 进度记录 |
| architecture.md | 架构说明 |
| implementation-plan.md | 实施计划 |
| prd.md | 需求/PRD |

每次对话开始时自动读取，确保上下文连续。

---

## 防幻觉相关

### Q17: 什么是防幻觉原则？

**A**: 防幻觉原则（AH-01~05）是防止 AI 生成错误内容的机制：

| 原则 | 规则 |
|------|------|
| AH-01 | 禁止假设数据一致，缺失标记"待确认" |
| AH-02 | 禁止自动管理裁决（拒绝/暂停/冻结） |
| AH-03 | 禁止引入 SoT 未定义概念 |
| AH-04 | Phase 1 只提示不阻断 |
| AH-05 | 遇到歧义必须停止询问 |

### Q18: 什么是"不变量"？

**A**: 不变量是绝对不能违反的约束（CLAUDE.md）：

1. 预收款≠收入：履约完成前是负债
2. 平台消耗不含手续费：广告费和手续费分开核算
3. 可用资金公式：`opening_balance + Σtopup - Σad_spend`
4. 锁定后不可改：只能红冲
5. 数据域隔离：投手只看自己账户

### Q19: 遇到不确定的需求怎么办？

**A**: 按 AH-05 原则：
1. 立即停止
2. 列出歧义点
3. 询问用户确认
4. 获得确认后继续

**禁止**猜测或自行决定。

---

## 其他问题

### Q20: 如何获取更多帮助？

**A**:
- 查看 `CLAUDE.md` - 项目入口
- 查看 `docs/sot/INDEX.md` - SoT 快速导航
- 查看 `.claude/CAPABILITIES.md` - 能力清单
- 使用 `/help` 命令

### Q21: 如何报告问题？

**A**:
1. 在 `memory-bank/progress.md` 的"阻塞项"部分记录
2. 创建 GitHub Issue（如适用）
3. 联系相关负责人

---

## 相关文档

- [CLAUDE.md](../CLAUDE.md) - 项目入口
- [docs/sot/INDEX.md](../docs/sot/INDEX.md) - SoT 快速导航
- [CAPABILITIES.md](./CAPABILITIES.md) - 能力清单
- [INTEGRATION_MAP.md](./INTEGRATION_MAP.md) - 集成关系图

---

**维护周期**: 收到新问题时更新
