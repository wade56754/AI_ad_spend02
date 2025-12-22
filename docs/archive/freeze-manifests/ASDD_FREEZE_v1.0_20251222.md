# ASDD Freeze v1.0 - AI 广告代投系统文档体系冻结声明

> **冻结日期**: 2025-11-25
> **冻结范围**: ASDD 7 核心文档
> **status**: frozen
> **基准**: SoT Freeze v1.0
> **owner**: wade
> **last_reviewed**: 2025-11-27

---

## 冻结文档清单

| 文档 | 版本 | 路径 | 状态 |
|-----|------|------|------|
| MASTER.md | v3.4 | docs/1.overview/MASTER.md | Frozen |
| PROJECT.md | v1.2 | docs/1.overview/PROJECT.md | Frozen |
| ARCHITECTURE.md | v1.0 | docs/1.overview/ARCHITECTURE.md | Frozen |
| DOMAIN.md | v1.0 | docs/1.overview/DOMAIN.md | Frozen |
| PATTERNS.md | v1.0 | docs/1.overview/PATTERNS.md | Frozen |
| TESTING.md | v1.0 | docs/1.overview/TESTING.md | Frozen |
| DEPLOYMENT.md | v1.0 | docs/1.overview/DEPLOYMENT.md | Frozen |

---

## 文档引用关系图

```
                         ┌─────────────┐
                         │  MASTER.md  │  ← 最高仲裁（宪法）
                         │   (v3.4)    │
                         └──────┬──────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          ▼                     ▼                     ▼
    ┌───────────┐        ┌─────────────┐        ┌────────────┐
    │PROJECT.md │        │ARCHITECTURE │        │  DOMAIN.md │
    │  (v1.2)   │        │   (v1.0)    │        │   (v1.0)   │
    └─────┬─────┘        └──────┬──────┘        └──────┬─────┘
          │                     │                       │
          │              ┌──────┴──────┐       ┌────────┴────────┐
          │              ▼             ▼       ▼                 ▼
          │        ┌──────────┐  ┌──────────┐┌──────────┐┌──────────────┐
          │        │PATTERNS  │  │TESTING   ││STATE_    ││ DATA_SCHEMA  │
          │        │  .md     │  │  .md     ││MACHINE.md││    .md       │
          │        │ (v1.0)   │  │ (v1.0)   ││(v2.6) ✅ ││ (v5.2) ✅    │
          │        └──────────┘  └──────────┘└──────────┘└──────────────┘
          │              │             │
          │              └──────┬──────┘
          │                     │
          └─────────────────────┼─────────────────────┐
                                ▼                     │
                         ┌─────────────┐             │
                         │DEPLOYMENT.md│◀────────────┘
                         │   (v1.0)    │
                         └─────────────┘
```

---

## Freeze 保护规则

### 1. 禁止直接修改

| 禁止操作 | 原因 |
|---------|------|
| 修改 MASTER.md 不可变量 | 架构宪法，需 RFC 流程 |
| 修改状态枚举定义 | 必须先更新 STATE_MACHINE.md |
| 重复定义业务规则 | 必须引用上游 SoT |
| 在 ASDD 文档中写规则正文 | SoT 为唯一规则源 |

### 2. 变更流程

```
发现需要修改
    │
    ▼
提交 RFC（说明原因、影响范围）
    │
    ▼
架构师审批
    │
    ▼
更新对应 SoT 文档
    │
    ▼
同步更新 ASDD 文档引用
    │
    ▼
更新 Freeze 版本号
```

### 3. 版本演进规则

| 变更类型 | 版本变化 | 示例 |
|---------|---------|------|
| 修复引用错误 | Patch (+0.0.1) | v1.0 → v1.0.1 |
| 新增章节/内容 | Minor (+0.1.0) | v1.0 → v1.1 |
| 架构重构 | Major (+1.0.0) | v1.0 → v2.0 |

---

## 文档统计

| 指标 | 数值 |
|-----|------|
| ASDD 核心文档 | 7 个 |
| 总行数 | ~3,500 行 |
| 反模式定义 | 37 个 |
| 必测清单项 | 13 个 |
| INV 不可变量 | 4 个 |
| BI 业务不可变量 | 5 个 |

---

## Dev-Ready 评分

| 领域 | 评分 | 说明 |
|-----|------|------|
| Backend | 95/100 | 状态机、账本规则完备 |
| Frontend | 92/100 | API 契约、错误码完备 |
| Testing | 98/100 | 必测清单、覆盖率目标明确 |
| Ops | 90/100 | 回滚锚点、CI/CD 流程完备 |

---

## 相关文档

- [MASTER.md](MASTER.md) - 系统架构宪法
- [PROJECT.md](PROJECT.md) - 业务定义与边界
- [ARCHITECTURE.md](ARCHITECTURE.md) - 技术架构约束
- [DOMAIN.md](DOMAIN.md) - 领域索引导航
- [PATTERNS.md](PATTERNS.md) - 反模式清单
- [TESTING.md](TESTING.md) - 测试规范
- [DEPLOYMENT.md](DEPLOYMENT.md) - 部署规范

---

**Freeze 版本**: ASDD_Freeze_v1.0
**冻结日期**: 2025-11-25
**维护者**: 系统架构师
**下次审查**: 根据业务需求
