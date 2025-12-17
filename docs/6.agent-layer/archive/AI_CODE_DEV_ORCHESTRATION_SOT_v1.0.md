# [ARCHIVED] AI 代码开发编排规范 (Code Dev Orchestration SoT)

> **⚠️ 归档声明**
> - **归档日期**: 2025-12-07
> - **归档原因**: 内容已合并至 `AI_CODE_FACTORY_DEV_GUIDE_v2.3.md` §4-7, §11
> - **替代文档**: [../AI_CODE_FACTORY_DEV_GUIDE_v2.3.md](../AI_CODE_FACTORY_DEV_GUIDE_v2.3.md)
> - **保留目的**: 仅供历史参考

---

## 原文档信息

- **原版本**: v1.0
- **原状态**: Active
- **原基准**: MASTER.md v3.5, Agent Layer Freeze v1.0, SoT Freeze v2.6

---

## 内容摘要

本文档原定义了 AI Agent 驱动的代码开发编排流程，包括：

1. **Golden Pipeline 定义** - 经过完整验收的标准化开发流程
2. **开发阶段划分** - 需求→设计→后端→前端→联调→验收
3. **14 项联调检查清单** - API/Auth/Schema/UX/Data/Type/Debug/Perf/SoT
4. **SoT 对齐要求** - 与 STATE_MACHINE/ERROR_CODES/AUTH_SPEC 对齐
5. **Agent 编排流程** - OrchestratorAgent 协调 BE/FE/Test/Doc Agent

以上内容已整合到 `AI_CODE_FACTORY_DEV_GUIDE_v2.3.md` 的以下章节：

| 原章节 | 新位置 |
|-------|--------|
| §2 Golden Pipeline | Dev Guide §3 质量标准与上线门禁 |
| §3 开发阶段划分 | Dev Guide §4-7 开发流程 |
| §4 14项联调检查清单 | Dev Guide §3.2 上线门禁 |
| §5 SoT 对齐要求 | Dev Guide §4.3 SoT 完整性扫描 |
| §6 Agent 编排流程 | Dev Guide §9.3 数据流图, §11 推荐工作流 |

---

## Golden Pipeline 样本库（历史参考）

以下 Golden Pipeline 样本记录保留供历史参考：

| Pipeline ID | 模块 | 状态 | 验收日期 |
|-------------|------|------|----------|
| GOLDEN-BE-TEST-001 | Backend Test Framework | ✅ ready | 2025-11-30 |
| GOLDEN-FE-DASHBOARD-001 | Dashboard Frontend | ✅ ready | 2025-12-06 |
| GOLDEN-DR-001 | Daily Report Full Stack | 🟡 pending | TBD |

---

**如需查看原完整内容，请联系文档管理员。**
