# 测试运行说明

> **版本**: v1.0
> **日期**: 2025-12-09
> **状态**: ✅ 就绪

---

## 🎯 快速开始

### 验证测试环境

双击运行验证脚本：
```
frontend/verify-test-env.bat
```

该脚本会检查：
- ✅ Node.js 和 npm 版本
- ✅ Jest 和 Puppeteer 安装
- ✅ 配置文件存在性
- ✅ 测试文件列表

### 运行单元测试

**方式 1 - 使用批处理文件**（推荐）:
```
双击运行: frontend/run-unit-tests.bat
```

**方式 2 - 使用命令行**:
```bash
cd frontend
npm test
```

### 运行 E2E 测试

**⚠️ 重要**: 先启动开发服务器！

```bash
# 终端 1 - 启动服务器
cd frontend
npm run dev

# 终端 2 - 运行 E2E 测试
双击运行: frontend/run-e2e-tests.bat
# 或
cd frontend
npm run test:e2e
```

---

## 📊 测试统计

### 已实现的测试

| 类型 | 数量 | 文件数 |
|------|------|--------|
| **组件单元测试** | 70+ 用例 | 6 个文件 |
| **E2E 功能测试** | 100+ 用例 | 5 个文件 |
| **E2E 性能测试** | 10+ 用例 | 1 个文件 |
| **页面对象** | - | 6 个 POM |
| **测试工厂** | - | 5 个工厂 |

### 测试覆盖的模块

✅ **认证模块**
- 登录流程测试（15+ 用例）
- 注册流程测试（15+ 用例）
- 表单验证、错误处理、状态管理

✅ **仪表盘模块**
- 基础功能测试（15+ 用例）
- 性能测试（10+ 用例）
- 统计卡片、图表、导航

✅ **日报管理模块**
- 基础功能测试（18+ 用例）
- 列表、筛选、分页、搜索、导出

✅ **充值管理模块**
- 基础功能测试（32+ 用例）
- 创建、审核、状态管理、权限控制

✅ **组件测试**
- DashboardStats（13+ 用例）
- DailyReportTable（15+ 用例）
- TrendChart（24+ 用例）

---

## 🛠️ 可用的测试脚本

### 批处理文件（Windows）

| 文件 | 功能 | 用途 |
|------|------|------|
| **verify-test-env.bat** | 验证测试环境 | 首次运行前检查 |
| **run-unit-tests.bat** | 运行单元测试 | 日常开发测试 |
| **run-e2e-tests.bat** | 运行 E2E 测试（无头） | 自动化测试 |
| **run-e2e-headed.bat** | 运行 E2E 测试（有头） | 调试、演示 |

### npm 脚本

```bash
# 单元测试
npm test                        # 运行所有单元测试
npm run test:watch              # 监听模式
npm run test:coverage           # 生成覆盖率报告
npm run test:ci                 # CI 环境测试

# E2E 测试
npm run test:e2e                # 无头模式 E2E 测试
npm run test:e2e:headed         # 显示浏览器
npm run test:e2e:debug          # 调试模式（慢放 + DevTools）

# 性能测试
npm run test:performance        # 运行性能测试

# 综合
npm run test:all                # 单元 + E2E 测试
```

---

## 📁 测试文件结构

```
frontend/
├── __tests__/                              # 单元测试
│   ├── setup.test.ts                       # 框架验证
│   ├── example/                            # 示例测试
│   │   ├── Button.test.tsx                 # 按钮组件
│   │   └── LoginForm.test.tsx              # 登录表单
│   └── components/                         # 组件测试
│       ├── DashboardStats.test.tsx         # 统计卡片
│       ├── DailyReportTable.test.tsx       # 日报表格
│       └── TrendChart.test.tsx             # 趋势图表
│
├── e2e/                                    # E2E 测试
│   ├── pages/                              # 页面对象
│   │   ├── BasePage.ts                     # 基础类
│   │   ├── LoginPage.ts                    # 登录页
│   │   ├── SignUpPage.ts                   # 注册页
│   │   ├── DashboardPage.ts                # 仪表盘
│   │   ├── DailyReportsPage.ts             # 日报管理
│   │   └── TopupPage.ts                    # 充值管理
│   │
│   ├── tests/                              # 测试用例
│   │   ├── auth/
│   │   │   ├── login.e2e.ts                # 登录测试
│   │   │   └── signup.e2e.ts               # 注册测试
│   │   ├── dashboard/
│   │   │   └── dashboard-basic.e2e.ts      # 仪表盘测试
│   │   ├── daily-reports/
│   │   │   └── daily-reports-basic.e2e.ts  # 日报测试
│   │   ├── topup/
│   │   │   └── topup-basic.e2e.ts          # 充值测试
│   │   └── performance/
│   │       └── dashboard-performance.e2e.ts # 性能测试
│   │
│   ├── utils/                              # 工具函数
│   │   ├── helpers.ts                      # 测试辅助
│   │   └── performance.ts                  # 性能工具
│   │
│   └── fixtures/                           # 测试资源
│       ├── README.md                       # 资源说明
│       └── .gitkeep                        # Git 追踪
│
├── tests/                                  # 测试工具
│   ├── setup.ts                            # 单元测试设置
│   ├── test-utils.tsx                      # 测试工具
│   ├── mocks/                              # Mock 工具
│   │   ├── api.ts                          # API Mock
│   │   └── auth.ts                         # 认证 Mock
│   ├── factories/                          # 数据工厂
│   │   └── index.ts                        # 所有工厂
│   └── README.md                           # 单元测试文档
│
├── jest.config.js                          # Jest 配置
├── run-unit-tests.bat                      # 单元测试脚本
├── run-e2e-tests.bat                       # E2E 测试脚本
├── run-e2e-headed.bat                      # E2E 有头模式脚本
├── verify-test-env.bat                     # 环境验证脚本
└── TESTING_GUIDE.md                        # 测试指南
```

---

## 🎬 测试运行演示

### 1. 首次运行 - 验证环境

```bash
# 双击运行
verify-test-env.bat

# 预期输出
========================================
Verifying Test Environment
========================================

[1/7] Checking Node.js...
v18.17.0
OK: Node.js installed

[2/7] Checking npm...
9.8.1
OK: npm installed

[3/7] Checking Jest...
29.7.0
OK: Jest installed

[4/7] Checking Puppeteer...
24.32.1
OK: Puppeteer installed

[5/7] Checking test configuration files...
OK: jest.config.js found
OK: e2e/jest.config.js found

[6/7] Checking test setup files...
OK: tests/setup.ts found
OK: tests/test-utils.tsx found

[7/7] Listing test files...

Unit Test Files:
__tests__\setup.test.ts
__tests__\example\Button.test.tsx
__tests__\example\LoginForm.test.tsx
__tests__\components\DashboardStats.test.tsx
__tests__\components\DailyReportTable.test.tsx
__tests__\components\TrendChart.test.tsx

E2E Test Files:
e2e\tests\auth\login.e2e.ts
e2e\tests\auth\signup.e2e.ts
e2e\tests\dashboard\dashboard-basic.e2e.ts
e2e\tests\daily-reports\daily-reports-basic.e2e.ts
e2e\tests\topup\topup-basic.e2e.ts
e2e\tests\performance\dashboard-performance.e2e.ts

========================================
Test Environment Verification Complete!
========================================
```

### 2. 运行单元测试

```bash
# 双击运行
run-unit-tests.bat

# 或使用命令行
cd frontend
npm test

# 预期输出
PASS  __tests__/setup.test.ts
  Jest Test Framework Setup
    ✓ should have Jest globals available (2 ms)
    ✓ should have correct test environment
    ✓ should have DOM testing utilities

PASS  __tests__/example/Button.test.tsx
  Button Component
    Rendering
      ✓ should render with children text (45 ms)
      ✓ should apply primary variant by default (12 ms)
      ✓ should apply correct variant classes (18 ms)
    User Interactions
      ✓ should call onClick handler when clicked (35 ms)
      ✓ should not call onClick when disabled (20 ms)

PASS  __tests__/components/DashboardStats.test.tsx
  DashboardStats Component
    渲染测试
      ✓ 应该渲染所有统计卡片 (52 ms)
      ✓ 应该显示正确的数值 (28 ms)
      ✓ 应该显示正确的标题 (15 ms)
    空数据处理
      ✓ 应该显示占位符 (18 ms)
    ...

Test Suites: 6 passed, 6 total
Tests:       70 passed, 70 total
Snapshots:   0 total
Time:        10.234 s
```

### 3. 运行 E2E 测试

**步骤 1**: 启动开发服务器
```bash
cd frontend
npm run dev

# 等待输出
✓ Ready in 2.5s
○ Local:        http://localhost:3000
```

**步骤 2**: 运行 E2E 测试
```bash
# 双击运行（无头模式）
run-e2e-tests.bat

# 或使用命令行
npm run test:e2e

# 预期输出
PASS  e2e/tests/auth/login.e2e.ts (25.123 s)
  登录流程 E2E 测试
    页面加载
      ✓ 应该成功加载登录页面 (2345 ms)
      ✓ 应该显示登录表单 (1234 ms)
    表单验证
      ✓ 应该显示空邮箱错误 (3456 ms)
      ✓ 应该显示空密码错误 (2789 ms)
      ✓ 应该显示无效邮箱格式错误 (3012 ms)
    登录功能
      ✓ 应该使用有效凭据成功登录 (5678 ms)
      ✓ 应该显示错误凭据错误消息 (4234 ms)
    ...

PASS  e2e/tests/topup/topup-basic.e2e.ts (32.567 s)
  充值管理基础功能测试
    页面加载
      ✓ 应该成功加载充值管理页面 (2456 ms)
    创建充值
      ✓ 点击创建应该打开表单 (3789 ms)
      ✓ 应该能够填写充值信息 (4123 ms)
    审核流程
      ✓ 应该能够打开审核弹窗 (2890 ms)
      ✓ 审核通过应该更新状态 (5432 ms)
    ...

Test Suites: 5 passed, 5 total
Tests:       100 passed, 100 total
Time:        137.169 s (2m 17s)
```

### 4. 运行性能测试

```bash
npm run test:performance

# 预期输出
PASS  e2e/tests/performance/dashboard-performance.e2e.ts (45.678 s)
  仪表盘页面性能测试
    页面加载性能
      ✓ 应该在合理时间内完成首次内容渲染 (FCP) (8234 ms)
        📊 FCP: 1234.56ms
      ✓ 应该在合理时间内完成最大内容渲染 (LCP) (9345 ms)
        📊 LCP: 2100.00ms
      ✓ 应该有较低的累积布局偏移 (CLS) (7890 ms)
        📊 CLS: 0.0456
    资源加载性能
      ✓ 应该限制资源请求数量 (6789 ms)
        📊 总请求数: 45
        📊 总大小: 2.34 MB
    完整性能报告
      ✓ 应该生成完整的性能报告 (10234 ms)

        📊 === 性能测试报告 ===
        FCP: 1234.56ms
        LCP: 2100.00ms
        CLS: 0.0456
        TTI: 3200.00ms
        总请求数: 45
        总大小: 2.34 MB
        报告已保存: e2e/reports/performance-dashboard-full-report-20251209.md
        =========================
```

---

## 🔍 调试失败的测试

### 单元测试调试

1. **运行特定测试**:
   ```bash
   npm test -- DashboardStats.test.tsx
   ```

2. **使用监听模式**:
   ```bash
   npm run test:watch
   ```

3. **查看详细输出**:
   ```bash
   npm test -- --verbose
   ```

4. **更新快照**:
   ```bash
   npm test -- -u
   ```

### E2E 测试调试

1. **使用有头模式**（可以看到浏览器）:
   ```bash
   # 双击运行
   run-e2e-headed.bat

   # 或使用命令
   npm run test:e2e:headed
   ```

2. **使用调试模式**（慢放 + DevTools）:
   ```bash
   npm run test:e2e:debug
   ```

3. **运行特定测试**:
   ```bash
   npm run test:e2e -- login.e2e.ts
   ```

4. **查看截图**（失败时自动保存）:
   ```
   e2e/screenshots/
   ```

---

## 📈 测试报告

### 单元测试覆盖率报告

```bash
npm run test:coverage

# 报告位置
coverage/
├── lcov-report/
│   └── index.html          # 打开查看可视化报告
└── lcov.info              # 原始覆盖率数据
```

### E2E 性能报告

```bash
npm run test:performance

# 报告位置
e2e/reports/
└── performance-{pageName}-{timestamp}.md
```

报告示例：
```markdown
# 性能测试报告 - dashboard

## Core Web Vitals
| 指标 | 值 | 评分 |
|------|-----|------|
| FCP | 1234.56ms | ✅ 优秀 |
| LCP | 2100.00ms | ✅ 优秀 |
| CLS | 0.05 | ✅ 优秀 |
| TTI | 3200.00ms | ✅ 良好 |

## 资源统计
- 总请求数: 45
- 总大小: 2.34 MB
- JS 文件: 12 个 (850 KB)
- CSS 文件: 3 个 (120 KB)
```

---

## ✅ 检查清单

运行测试前，确保：

- [ ] Node.js >= 18.x 已安装
- [ ] 运行 `npm install` 安装依赖
- [ ] 运行 `verify-test-env.bat` 验证环境
- [ ] （E2E 测试）开发服务器在 `http://localhost:3000` 运行
- [ ] （E2E 测试）Chrome/Chromium 浏览器可用

---

## 🚀 CI/CD 集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm ci
      - run: cd frontend && npm run test:ci

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: cd frontend && npm ci
      - run: cd frontend && npm run build
      - run: cd frontend && npm start &
      - run: cd frontend && npm run test:e2e
```

---

## 📚 相关文档

- **[测试运行指南](../../frontend/TESTING_GUIDE.md)** - 详细的测试运行指南
- **[单元测试文档](../../frontend/tests/README.md)** - 单元测试框架和最佳实践
- **[E2E 测试文档](../../frontend/e2e/README.md)** - E2E 测试框架和 Puppeteer 使用
- **[测试实现报告](./TEST_IMPLEMENTATION_REPORT.md)** - 已完成的测试清单
- **[测试模板](../../frontend/tests/TEST_TEMPLATE.md)** - 测试编写模板

---

## 💡 小贴士

### 提高测试速度

1. **并行运行单元测试**:
   ```bash
   npm test -- --maxWorkers=4
   ```

2. **只运行更改的测试**:
   ```bash
   npm test -- --onlyChanged
   ```

3. **跳过慢速测试**:
   ```bash
   npm test -- --testPathIgnorePatterns=e2e
   ```

### 常用组合

```bash
# 开发中：监听模式 + 只运行更改的测试
npm test -- --watch --onlyChanged

# 提交前：覆盖率 + 详细输出
npm run test:coverage -- --verbose

# 调试：单个文件 + 详细输出
npm test -- DashboardStats.test.tsx --verbose
```

---

**最后更新**: 2025-12-09
**维护者**: AI Development Team
**状态**: ✅ 测试环境就绪，可以开始测试！
