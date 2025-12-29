# E2E 测试

基于 Playwright + TypeScript 的端到端测试。

## 目录结构

```
__tests__/
├── e2e/                    # E2E 测试用例
│   ├── a1-dashboard/       # A1 驾驶舱
│   ├── a2-fund-overview/   # A2 资金总览
│   ├── a3-project-pnl/     # A3 项目盈亏
│   ├── b1-topup-approval/  # B1 充值审批 (7 状态机)
│   ├── b2-daily-report-review/ # B2 日报审核 (8 状态机)
│   ├── b3-weekly-brief/    # B3 周简报
│   ├── c1-project-mgmt/    # C1 项目管理 (5 状态机)
│   ├── c2-pitcher-mgmt/    # C2 投手管理
│   ├── c3-spend-detail/    # C3 消耗明细
│   └── d1-monthly-settlement/ # D1 月度结算 (4 状态机)
├── fixtures/               # 测试数据
│   ├── test-accounts.ts    # 测试账号 (7 角色)
│   └── mock-data.ts        # Mock 数据
├── utils/                  # 测试工具
│   ├── auth.ts             # 认证辅助
│   └── assertions.ts       # 断言辅助
└── checkpoints/            # 检查点 YAML
```

## 运行测试

### 开发环境

```bash
# 1. 安装依赖
npm install

# 2. 启动前端开发服务器 (新终端)
cd frontend && npm run dev

# 3. 运行测试
npx playwright test

# 带 UI 运行
npx playwright test --ui

# 运行单个模块
npx playwright test a1-dashboard
```

### CI 环境

```bash
# 自动启动 dev server
CI=true npx playwright test
```

## 测试覆盖

| 模块 | 测试数 | 状态机 | 特性 |
|------|--------|--------|------|
| A1 驾驶舱 | ~30 | - | 权限/数据/Phase1 |
| A2 资金总览 | ~25 | - | 负余额高亮 |
| A3 项目盈亏 | ~22 | - | 亏损高亮 |
| B1 充值审批 | ~24 | 7 状态 | 状态机 + 非法转换 |
| B2 日报审核 | ~28 | 8 状态 | 状态机 + 非法转换 |
| B3 周简报 | ~18 | - | CPL 预警 |
| C1 项目管理 | ~30 | 5 状态 | 状态机 + 表单 |
| C2 投手管理 | ~20 | - | 绩效异常 |
| C3 消耗明细 | ~25 | - | 高消耗预警 |
| D1 月度结算 | ~26 | 4 状态 | 状态机 + 生成 |

**总计: 269 测试用例**

## 5 类测试

1. **权限测试 (CP-XX-001)**: 7 角色访问控制
2. **页面渲染 (CP-XX-002)**: UI 元素可见性
3. **数据状态 (CP-XX-003)**: 加载/空/错误/成功
4. **功能操作 (CP-XX-004)**: 用户交互
5. **Phase 1 规则 (CP-XX-005)**: 高亮但不阻断

## data-testid 规范

前端组件需要添加 `data-testid` 属性:

```tsx
// 表格
<Table data-testid="project-table">

// 按钮
<Button data-testid="create-project-btn">

// 表单输入
<Input data-testid="input-name">

// 行
<TableRow data-testid={`row-${item.id}`}>

// 操作按钮
<Button data-testid={`edit-btn-${item.id}`}>
```
