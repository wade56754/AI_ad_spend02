# AI_ad_spend02 文档架构

> **版本**: v2.0
> **日期**: 2025-11-25
> **基准**: ASDD Freeze v1.0 + SoT Freeze v1.0
> **状态**: Frozen

---

## 1. 文档体系概览

本系统采用 **ASDD (AI Spec-Driven Development)** + **SoT (Source of Truth)** 双层文档架构。

### 1.1 文档分层

```
docs/
├── README.md                              # 文档中心索引
├── DOCUMENTATION_ARCHITECTURE.md          # 本文档 - 架构说明

├── 1.overview/                            # ASDD 7 核心文档
│   ├── MASTER.md                         # 系统架构宪法 v3.4
│   ├── PROJECT.md                        # 业务定义 v1.2
│   ├── ARCHITECTURE.md                   # 技术架构 v1.0
│   ├── DOMAIN.md                         # 领域索引 v1.0
│   ├── PATTERNS.md                       # 反模式清单 v1.0
│   ├── TESTING.md                        # 测试规范 v1.0
│   ├── DEPLOYMENT.md                     # 部署规范 v1.0
│   └── ASDD_FREEZE_v1.0.md              # ASDD 冻结声明
│
├── 2.sot/                                 # SoT 真相来源文档
│   ├── STATE_MACHINE.md                  # 状态机 v2.6
│   ├── DATA_SCHEMA.md                    # 数据架构 v5.2
│   ├── BUSINESS_RULES.md                 # 业务规则 v3.1
│   ├── API_SOT.md                        # API 规范 v2.2
│   ├── ERROR_CODES_SOT.md                # 错误码 v2.1
│   ├── AUTH_SPEC.md                      # 认证授权 v2.0
│   ├── LEDGER_SOT.md                     # 账本规则 v1.1
│   ├── DAILY_REPORT_SOT.md               # 日报规则 v1.0
│   ├── TRANSFER_SOT.md                   # 划拨规则 v1.0
│   ├── RECONCILIATION_SOT.md             # 对账规则 v1.0
│   └── RLS_POLICIES_SOT.md               # RLS 策略 v1.0
│
├── 3.dev-guides/                          # 开发指南
│   ├── API_DEVELOPMENT_FLOW.md           # API 开发流程
│   ├── API_RULEBOOK.md                   # API 规则手册
│   ├── BACKEND_SETUP.md                  # 后端搭建
│   ├── BACKEND_DEV_GUIDE.md              # 后端开发指南
│   ├── FRONTEND_SETUP.md                 # 前端搭建
│   ├── FRONTEND_RULES.md                 # 前端规范
│   ├── TESTING_GUIDE.md                  # 测试指南
│   └── DEVELOPMENT_STANDARDS.md          # 开发标准
│
├── 4.ui-ux/                               # UI/UX 文档 (待建)
│   └── README.md
│
├── 5.ops/                                 # 运维文档 (待建)
│   └── README.md
│
└── archive/                               # 历史归档
    ├── asdd_migration/                   # ASDD 迁移说明
    ├── core_archive/                     # 旧核心文档
    ├── old_core/                         # 旧 SoT 文档
    └── [其他历史版本]
```

---

## 2. 文档优先级仲裁链

### 2.1 ASDD + SoT 双层仲裁

```
ASDD Layer (架构层)
    MASTER.md v3.4                    <- 最高仲裁权
        |
        +-- PROJECT.md v1.2           <- 业务边界
        +-- ARCHITECTURE.md v1.0      <- 技术约束
        +-- DOMAIN.md v1.0            <- 领域索引
        +-- PATTERNS.md v1.0          <- 反模式约束
        +-- TESTING.md v1.0           <- 测试约束
        +-- DEPLOYMENT.md v1.0        <- 部署约束

SoT Layer (规范层)
    STATE_MACHINE.md v2.6             <- 状态定义 (最高 SoT)
        |
        +-- DATA_SCHEMA.md v5.2       <- 数据结构
        +-- BUSINESS_RULES.md v3.1    <- 业务规则
            |
            +-- API_SOT.md v2.2       <- API 定义
            +-- ERROR_CODES_SOT.md v2.1
            +-- AUTH_SPEC.md v2.0
                |
                +-- LEDGER_SOT.md v1.1
                +-- DAILY_REPORT_SOT.md v1.0
                +-- TRANSFER_SOT.md v1.0
                +-- RECONCILIATION_SOT.md v1.0
                +-- RLS_POLICIES_SOT.md v1.0
```

### 2.2 冲突仲裁规则

| 冲突场景 | 仲裁文档 | 处理方式 |
|---------|---------|---------|
| 架构原则冲突 | MASTER.md | 修改所有下游文档 |
| 状态定义冲突 | STATE_MACHINE.md | 修改 API/业务文档 |
| 数据结构冲突 | DATA_SCHEMA.md | 修改 API/业务文档 |
| 业务规则冲突 | BUSINESS_RULES.md | 修改模块 SoT |
| API 定义冲突 | API_SOT.md | 修改开发指南 |

---

## 3. 文档状态管理

### 3.1 状态定义

| 状态 | 说明 | 允许操作 |
|-----|------|---------|
| **Draft** | 草稿中 | 任意修改 |
| **Review** | 评审中 | 根据反馈修改 |
| **Active** | 生效中 | 按流程修改 |
| **Frozen** | 已冻结 | 仅 RFC 流程 |
| **Deprecated** | 已废弃 | 不允许修改 |
| **Archived** | 已归档 | 不允许修改 |

### 3.2 当前文档状态

| 文档 | 版本 | 状态 |
|-----|------|------|
| MASTER.md | v3.4 | Frozen |
| PROJECT.md | v1.2 | Frozen |
| ARCHITECTURE.md | v1.0 | Frozen |
| DOMAIN.md | v1.0 | Frozen |
| PATTERNS.md | v1.0 | Frozen |
| TESTING.md | v1.0 | Frozen |
| DEPLOYMENT.md | v1.0 | Frozen |
| STATE_MACHINE.md | v2.6 | Frozen |
| DATA_SCHEMA.md | v5.2 | Frozen |
| BUSINESS_RULES.md | v3.1 | Frozen |
| API_SOT.md | v2.2 | Frozen |
| ERROR_CODES_SOT.md | v2.1 | Frozen |
| AUTH_SPEC.md | v2.0 | Frozen |
| LEDGER_SOT.md | v1.1 | Frozen |
| 其他 SoT 文档 | v1.0 | Frozen |
| 开发指南 | - | Active |

---

## 4. Freeze 保护规则

### 4.1 禁止操作

| 禁止操作 | 原因 |
|---------|------|
| 修改 MASTER.md 不可变量 (INV-*) | 架构宪法 |
| 修改状态枚举定义 | 必须先更新 STATE_MACHINE.md |
| 重复定义业务规则 | 必须引用上游 SoT |
| 在下游文档定义规则正文 | SoT 为唯一规则源 |

### 4.2 变更流程 (RFC)

```
发现需要修改
    |
    v
提交 RFC (说明原因、影响范围)
    |
    v
架构师审批
    |
    v
更新对应 SoT 文档
    |
    v
同步更新下游文档引用
    |
    v
更新 Freeze 版本号
```

---

## 5. 文档统计

| 指标 | 数值 |
|-----|------|
| ASDD 核心文档 | 7 个 |
| SoT 规范文档 | 11 个 |
| 开发指南 | 9 个 |
| 反模式定义 | 37 个 |
| 必测清单项 | 13 个 |
| INV 不可变量 | 4 个 |
| BI 业务不可变量 | 5 个 |
| 归档文档 | 100+ 个 |

---

## 6. 相关文档

- [README.md](README.md) - 文档中心索引
- [MASTER.md](1.overview/MASTER.md) - 系统架构宪法
- [ASDD_FREEZE_v1.0.md](1.overview/ASDD_FREEZE_v1.0.md) - ASDD 冻结声明

---

**文档版本**: v2.0
**最后更新**: 2025-11-25
**基准**: ASDD_Freeze_v1.0 + SoT_Freeze_v1.0
**维护者**: 系统架构师
