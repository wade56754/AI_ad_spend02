# AI 代码工厂最佳实践指南

> **版本**: v1.0
> **最后更新**: 2026-01-02
> **基准**: MASTER.md v4.9, .codefactory.yaml v5.0.0

---

## 核心工作法: 读 → 查 → 写 → 检

```
1. 读 Memory Bank    → 了解当前进度和架构
2. 查 SoT 文档       → 确认规则和约束
3. 写 代码           → 使用正确的流程和命令
4. 检 合规性         → /sot-check + /review
```

---

## 一、开发流程选择

| 场景 | 推荐流程 | 复杂度 |
|------|---------|--------|
| 新增后端 API | `/flow be` | L2-L3 |
| 新增前端页面 | `/flow fe` | L2-L3 |
| Bug 修复 | `/flow fix` | L1-L2 |
| 完整功能（前后端） | `/flow full` | L3-L4 |
| 代码重构 | `/flow refactor` | L3-L4 |
| 文档生成 | `/flow doc` | L1 |
| 测试补充 | `/flow test` | L2 |

### 选择原则

- **不确定选什么** → 用 `/flow full`（最完整验证链）
- **简单修复** → 用 `/flow fix`（避免过度工程）
- **L4 任务** → 拆分成多个 L2/L3

---

## 二、SoT 合规检查

### 裁判链优先级

```
1. MASTER.md v4.9       最高权威
2. STATE_MACHINE.md     状态规范
3. DATA_SCHEMA.md       数据模型
4. BUSINESS_RULES.md    业务规则
5. API_SOT.md           接口规范
```

### 查阅时机

| 涉及内容 | 必查文档 |
|---------|---------|
| 角色权限 | MASTER.md §2 + BR-AUTH.md |
| 状态流转 | STATE_MACHINE.md |
| 数据字段 | DATA_SCHEMA.md |
| API 端点 | API_SOT.md |
| 业务公式 | BR-PROFIT.md / BR-FIN.md |

### 冲突处理

高优先级 SoT > 低优先级 SoT > PRD

---

## 三、Phase 1 约束（关键）

### 禁止的模式

```typescript
// ❌ 自动阻断
if (anomaly) throw new Error("操作被阻断");

// ❌ 自动拒绝
if (!valid) return { status: 'rejected' };

// ❌ 强制审批
if (!approved) blockOperation();
```

### 正确的模式

```typescript
// ✅ 只提示
if (anomaly) {
  toast.warning("检测到异常，请复核");
  logEvent("anomaly_detected");
}

// ✅ 只高亮
<StatusBadge variant="warning">待确认</StatusBadge>

// ✅ 只记录
await createAuditLog({ action, user, data });
```

---

## 四、角色权限实现

### 6 角色白名单

```typescript
const VALID_ROLES = [
  'ceo',            // 老板
  'project_owner',  // 项目负责人
  'finance',        // 财务
  'pitcher',        // 投手
  'account_manager', // 户管
  'admin'           // 管理员
] as const;
```

### 禁止使用的角色

| 废弃角色 | 替代方案 |
|---------|---------|
| ~~supervisor~~ | `project_owner` |
| ~~media_buyer~~ | `pitcher` |
| ~~data_operator~~ | 不在宪法中，不使用 |

---

## 五、代码质量自检

### 生成前检查

- [ ] 确认任务复杂度等级 (L1-L4)
- [ ] 确认涉及的 SoT 文档
- [ ] 确认 Phase 1 约束适用

### 生成后检查

- [ ] 交互页面第一行是否为 `'use client'`
- [ ] 是否使用了 6 角色白名单
- [ ] 是否使用了正确的日报状态 (3 状态)
- [ ] 是否使用 `DataTable` 而非手写 `<table>`
- [ ] 是否使用 `apiGet/apiPost` 而非 `fetch`
- [ ] 是否有完整的错误处理和 toast

---

## 六、防幻觉原则

| 原则 | 触发条件 | 正确做法 |
|------|---------|---------|
| **AH-01** | 字段可能为空 | 用 `?.` 或 `?? 默认值` |
| **AH-02** | 需要自动裁决 | 改为"待人工确认" |
| **AH-03** | SoT 中无定义 | **停止** → 询问 |
| **AH-04** | 需要阻断逻辑 | 改为提示+记录 |
| **AH-05** | 需求有歧义 | 列出选项 → 询问 |

---

## 七、常见反模式

```typescript
// ❌ 直接 fetch
fetch('/api/reports')
// ✅ 使用封装
apiGet('/api/v1/reports')

// ❌ 手写表格
<table><tbody>...</tbody></table>
// ✅ 使用组件
<DataTable columns={columns} data={data} />

// ❌ 硬编码状态
if (status === 'pending')
// ✅ 使用枚举
if (status === DailyReportStatus.RAW_SUBMITTED)

// ❌ 自定义错误码
throw new Error('Invalid input')
// ✅ 使用标准错误码
throw new AppError('VAL-001', 'Invalid input')
```

---

## 八、命令使用速查

| 命令 | 用途 | 典型场景 |
|------|------|---------|
| `/gen be:api` | 生成后端 API | 新增端点 |
| `/gen fe:page` | 生成前端页面 | 新增页面 |
| `/sot-check` | 合规检查 | 每次改动后 |
| `/review` | 代码审查 | 提交前 |
| `/auto-fix` | 自动修复 | 简单问题 |
| `/test-gen` | 生成测试 | 功能稳定后 |

---

## 九、开发流程详解

### `/flow full` 完整流程

```
Phase 1: 分析
  ├── 读取 SoT 文档
  ├── 理解业务规则
  └── 确认 Phase 1 约束

Phase 2: 后端生成
  ├── 模型定义 (DATA_SCHEMA.md)
  ├── API 端点 (API_SOT.md)
  ├── 业务逻辑 (BR-*.md)
  └── 单元测试

Phase 3: 前端生成
  ├── 页面组件
  ├── API 对接
  ├── 表单验证
  └── 响应式布局

Phase 4: 验证
  ├── /sot-check 合规检查
  ├── /review 代码审查
  └── 集成测试
```

### `/flow fix` 修复流程

```
Phase 1: 定位
  ├── 复现问题
  ├── 定位根因
  └── 确认影响范围

Phase 2: 修复
  ├── 最小改动原则
  ├── 保持向后兼容
  └── 添加回归测试

Phase 3: 验证
  ├── 问题已解决
  ├── 无新问题引入
  └── /sot-check 通过
```

---

## 十、总结：优先级排序

1️⃣ **SoT 优先** - 任何编码前先查 SoT
2️⃣ **Phase 1 约束** - 只提示不阻断
3️⃣ **6 角色白名单** - 禁止废弃角色
4️⃣ **正确选择流程** - 匹配任务复杂度
5️⃣ **防幻觉检查** - 缺失/歧义即停止
6️⃣ **代码质量自检** - 使用 /sot-check + /review

---

## 相关文档

- [CLAUDE.md](../../CLAUDE.md) - 项目指令
- [dev-flow.md](../../.claude/commands/dev-flow.md) - 开发流程详解
- [INDEX.md](../../.claude/commands/INDEX.md) - 命令索引
- [TASK_COMPLEXITY.md](./TASK_COMPLEXITY.md) - 任务复杂度分级
- [AI_PROGRAMMING_BEST_PRACTICES_v3.1.md](./AI_PROGRAMMING_BEST_PRACTICES_v3.1.md) - AI 编程规范

---

## 变更历史

### v1.0 (2026-01-02)

- 初始版本
- 整合 7 维度最佳实践分析
- 基于 .codefactory.yaml v5.0.0 和 MASTER.md v4.9
