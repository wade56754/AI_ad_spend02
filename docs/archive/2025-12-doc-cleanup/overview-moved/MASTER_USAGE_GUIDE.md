# MASTER.md 使用指南

> **注意**: 本指南已整合至 MASTER.md v4.4 附录
> **日期**: 2025-11-25
> **状态**: supplementary
> **说明**: 本指南为辅助文档，用于说明如何正确使用 MASTER.md 与 SoT 层文件。
> **owner**: wade
> **last_reviewed**: 2025-11-27

---

> **文档版本**: v1.0
> **创建日期**: 2025-11-25
> **适用范围**: AI 工具（Cursor、Claude Code、GitHub Copilot）和开发者

---

## 快速开始

### 在 Cursor 中使用 MASTER.md

**1. 引用 MASTER.md**
```
@file:docs/1.overview/MASTER.md
```

**2. 询问系统架构问题**
```
@file:docs/1.overview/MASTER.md 系统的双账本架构是什么？
```

**3. 引用 SoT 文档**
```
@file:docs/2.sot/STATE_MACHINE.md 状态机的流转规则是什么？
```

---

## AI 使用最佳实践

### 场景 1: 实现新功能

**步骤 1: 读取 MASTER.md**
```
@file:docs/1.overview/MASTER.md
请告诉我这个系统的核心不可变量是什么？
```

**步骤 2: 查询相关 SoT 文档**
```
@codebase docs/2.sot/
我需要实现日报功能，应该参考哪些 SoT 文档？
```

**步骤 3: 确认实现约束**
```
@file:docs/1.overview/MASTER.md
实现日报功能时，需要遵守哪些禁止事项？
```

**步骤 4: 生成代码**
```
根据 MASTER.md 的规则，实现一个符合以下要求的日报创建功能：
- 遵循三数据流分离（INV-002）
- 遵循状态机流转（INV-003）
- 使用 Result 模式处理错误
- 禁止魔法数字
```

### 场景 2: 修改现有代码

**步骤 1: 检查是否违反不可变量**
```
@file:docs/1.overview/MASTER.md
我想修改账本余额计算逻辑，这会违反哪些不可变量？
```

**步骤 2: 查询相关 SoT 文档**
```
@file:docs/2.sot/LEDGER_SOT.md
账本余额的计算公式是什么？
```

**步骤 3: 确认修改方案**
```
根据 MASTER.md 的 INV-001，账本余额必须通过 SUM(ledger_entries.amount) 计算。
我的修改方案是否符合这个要求？
```

### 场景 3: 解决文档冲突

**步骤 1: 查询裁判链**
```
@file:docs/1.overview/MASTER.md
当 STATE_MACHINE.md 和 DATA_SCHEMA.md 对同一概念有不同定义时，应该以哪个为准？
```

**步骤 2: 应用裁判链规则**
根据 MASTER.md 第三章的裁判链：
- STATE_MACHINE.md 优先级高于 DATA_SCHEMA.md
- 以 STATE_MACHINE.md 的定义为准

---

## 常见问题

### Q1: 如何快速了解系统架构？

**A**: 按以下顺序阅读：
1. `docs/1.overview/MASTER.md` - 系统哲学和不可变量
2. `docs/2.sot/STATE_MACHINE.md` - 状态机规则
3. `docs/2.sot/DATA_SCHEMA.md` - 数据模型
4. `docs/2.sot/LEDGER_SOT.md` - 账本规则

### Q2: 实现功能时应该先读哪个文档？

**A**: 始终先读 `docs/1.overview/MASTER.md`，然后根据功能类型：
- **状态相关**: `docs/2.sot/STATE_MACHINE.md`
- **数据相关**: `docs/2.sot/DATA_SCHEMA.md`
- **账本相关**: `docs/2.sot/LEDGER_SOT.md`
- **权限相关**: `docs/2.sot/AUTH_SPEC.md`
- **API 相关**: `docs/2.sot/API_SOT.md`

### Q3: 发现文档冲突怎么办？

**A**: 
1. 查询 MASTER.md 第三章的裁判链
2. 高优先级文档覆盖低优先级文档
3. 无法解决时，停止生成代码并询问用户

### Q4: 如何确保代码符合系统规范？

**A**: 使用以下检查清单：
- [ ] 是否违反了 INV-001 至 INV-004 的任何禁止条款？
- [ ] 是否使用了 SoT 未定义的字段、状态、角色？
- [ ] 是否遵循了 TypeScript strict mode？
- [ ] 是否使用了 Result 模式处理错误？
- [ ] 是否避免了魔法数字？
- [ ] 是否包含了单元测试（覆盖率 80%+）？

---

## 代码生成示例

### 示例 1: 创建日报（符合规范）

```typescript
// ✅ 正确示例：遵循 MASTER.md 规则

import { Result } from '@/common/result';
import { DailyReportState } from '@/constants/states'; // 来自 STATE_MACHINE.md

// 常量定义（禁止魔法数字）
const MIN_CONVERSIONS = 0; // 最小粉数（来自业务规则）

interface CreateDailyReportParams {
  projectId: string;
  conversionsRaw: number;
  rawSpend: number;
}

/**
 * 创建日报
 * 遵循 MASTER.md INV-002: 三数据流分离
 * 遵循 MASTER.md INV-003: 状态机强制流转
 */
export async function createDailyReport(
  params: CreateDailyReportParams
): Promise<Result<DailyReport, DailyReportError>> {
  // 使用 Result 模式（禁止 throw Error）
  if (params.conversionsRaw < MIN_CONVERSIONS) {
    return Result.err({
      code: 'INVALID_CONVERSIONS',
      message: '粉数不能为负数',
    });
  }

  // 状态初始化为 raw_submitted（来自 STATE_MACHINE.md）
  const dailyReport = await db.dailyReport.create({
    data: {
      projectId: params.projectId,
      conversionsRaw: params.conversionsRaw,
      rawSpend: params.rawSpend,
      state: DailyReportState.RAW_SUBMITTED, // 来自 SoT，不是硬编码
    },
  });

  return Result.ok(dailyReport);
}
```

### 示例 2: 计算账本余额（符合规范）

```typescript
// ✅ 正确示例：遵循 MASTER.md INV-001

/**
 * 计算项目账本余额
 * 遵循 MASTER.md INV-001: 余额 = SUM(ledger_entries.amount)
 * 禁止直接 UPDATE projects.balance
 */
export async function calculateProjectBalance(
  projectId: string
): Promise<Result<number, BalanceError>> {
  // 从 ledger_entries 计算（唯一正确方式）
  const entries = await db.ledgerEntry.findMany({
    where: {
      projectId,
      category: 'PROJECT', // 来自 LEDGER_SOT.md
    },
  });

  // 使用 SUM 计算（禁止 UPDATE）
  const balance = entries.reduce((sum, entry) => sum + entry.amount, 0);

  return Result.ok(balance);
}
```

### 示例 3: 错误示例（违反规范）

```typescript
// ❌ 错误示例：违反 MASTER.md 规则

// 1. 使用魔法数字
if (user.age > 18) { ... } // ❌ 应该定义常量

// 2. 直接 UPDATE 余额
await db.project.update({
  where: { id: projectId },
  data: { balance: newBalance }, // ❌ 违反 INV-001
});

// 3. 使用 throw Error
if (invalid) {
  throw new Error('Invalid'); // ❌ 应该使用 Result 模式
}

// 4. 硬编码状态
state: 'final_locked' // ❌ 应该引用 STATE_MACHINE.md 的枚举

// 5. 混合账本
await db.ledgerEntry.create({
  category: 'PROJECT',
  type: 'COST', // ❌ 违反 INV-001：PROJECT 账本不能记录 COST
});
```

---

## 验证清单

在提交代码前，使用以下清单验证：

### 架构合规性
- [ ] 未违反 INV-001（双账本独立核算）
- [ ] 未违反 INV-002（三数据流分离）
- [ ] 未违反 INV-003（状态机强制流转）
- [ ] 未违反 INV-004（职责分离）

### 代码质量
- [ ] TypeScript strict mode 启用
- [ ] 无 `any` 类型
- [ ] 无魔法数字
- [ ] 使用 Result 模式处理错误
- [ ] 测试覆盖率 80%+

### 文档一致性
- [ ] 所有字段来自 DATA_SCHEMA.md
- [ ] 所有状态来自 STATE_MACHINE.md
- [ ] 所有错误码来自 ERROR_CODES_SOT.md
- [ ] 所有 API 定义来自 API_SOT.md

---

## 参考资源

- **MASTER.md**: `docs/1.overview/MASTER.md`
- **MASTER_SPEC.md**: `docs/1.overview/MASTER_SPEC.md`
- **SoT 文档**: `docs/2.sot/`
- **开发指南**: `docs/3.dev-guides/`

---

**最后更新**: 2025-11-25  
**维护者**: 系统架构师









