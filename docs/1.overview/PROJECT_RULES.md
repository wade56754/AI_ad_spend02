# 项目总规范 (SoT-Architecture)

> **DEPRECATED**: 本文档已废弃，请使用 [PATTERNS.md](PATTERNS.md) v1.0
> **废弃日期**: 2025-11-25
> **取代文档**: PATTERNS.md v1.0 + MASTER.md v3.4 (ASDD Freeze v1.0)

---

> **版本**: v2.0 (DEPRECATED)
> **更新日期**: 2025-11-22
> **文档定位**: ~~项目级 SoT 文档导航与仲裁规则~~

~~本项目遵循以下文件作为系统级总规范：~~

## 核心 SoT 文档（按优先级排序）

1. **MASTER_SPEC.md** (v1.1) — 系统架构宪法，最高优先级
   - 路径: `docs/1.overview/MASTER_SPEC.md`
   - 职责: 架构设计、技术决策、全局约束

2. **STATE_MACHINE.md** (v2.6) — 状态机唯一真相源
   - 路径: `docs/2.sot/STATE_MACHINE.md`
   - 职责: 所有状态枚举、流转规则、终态保护

3. **DATA_SCHEMA.md** (v5.2) — 数据结构唯一真相源
   - 路径: `docs/2.sot/DATA_SCHEMA.md`
   - 职责: 数据库表结构、字段定义、索引约束

4. **BUSINESS_RULES.md** (v3.1) — 业务规则 SoT
   - 路径: `docs/2.sot/BUSINESS_RULES.md`
   - 职责: 业务约束、权限规则、SOD 原则

5. **ERROR_CODES_SOT.md** (v2.1) — 错误码 SoT
   - 路径: `docs/2.sot/ERROR_CODES_SOT.md`
   - 职责: 错误码定义、HTTP 映射、异常处理

6. **AUTH_SPEC.md** (v2.0) — 认证授权规范
   - 路径: `docs/2.sot/AUTH_SPEC.md`
   - 职责: 角色定义、权限控制、RBAC 实现

7. **RLS_POLICIES_SOT.md** (v2.1) — RLS 策略 SoT（规划）
   - 路径: `docs/2.sot/RLS_POLICIES_SOT.md`
   - 职责: 行级安全策略（当前未启用，仅规划）

## 仲裁路径（冲突解决顺序）

```
MASTER_SPEC.md (架构决策)
    ↓
STATE_MACHINE.md (状态规则)
    ↓
DATA_SCHEMA.md (数据结构)
    ↓
BUSINESS_RULES.md (业务约束)
    ↓
ERROR_CODES_SOT.md (错误处理)
```

⚠️ **强制规则**：
- 所有功能开发、接口设计、测试生成都必须以这些文件为真相来源
- 文档冲突时，按上述仲裁路径优先级解决
- 禁止在代码中硬编码状态、角色、错误码等枚举值
- 所有状态字段必须引用 STATE_MACHINE.md v2.6
- 所有数据模型必须引用 DATA_SCHEMA.md v5.2
