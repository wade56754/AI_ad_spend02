# 测试运行指南

> **快速开始指南**：如何运行项目中的各类测试

---

## 📋 目录

- [前置条件](#前置条件)
- [运行单元测试](#运行单元测试)
- [运行 E2E 测试](#运行-e2e-测试)
- [运行性能测试](#运行性能测试)
- [测试脚本说明](#测试脚本说明)
- [常见问题](#常见问题)

---

## 前置条件

### 1. 安装依赖

```bash
cd frontend
pnpm install
```

### 2. 环境要求

- Node.js >= 18.x
- pnpm >= 9.x
- Chrome/Chromium 浏览器（用于 E2E 测试）

### 3. 开发服务器（仅 E2E 测试需要）

E2E 测试需要开发服务器运行在 `http://localhost:3000`：

```bash
cd frontend
pnpm run dev
```

---

## 运行单元测试

### 方式一：使用批处理文件（推荐 - Windows）

双击运行：

```
frontend/run-unit-tests.bat
```

### 方式二：使用 pnpm 命令

```bash
cd frontend

# 运行所有单元测试
pnpm test

# 监听模式（自动重新运行）
pnpm run test:watch

# 生成覆盖率报告
pnpm run test:coverage

# 运行特定测试文件
pnpm test -- DashboardStats.test.tsx

# 更新快照
pnpm test -- -u
```

### 测试输出

成功运行后，你应该看到类似输出：

```
PASS  __tests__/setup.test.ts
PASS  __tests__/example/Button.test.tsx
PASS  __tests__/example/LoginForm.test.tsx
PASS  __tests__/components/DashboardStats.test.tsx
PASS  __tests__/components/DailyReportTable.test.tsx
PASS  __tests__/components/TrendChart.test.tsx

Test Suites: 6 passed, 6 total
Tests:       70 passed, 70 total
Snapshots:   0 total
Time:        10.234 s
```

---

## 运行 E2E 测试

### ⚠️ 重要：先启动开发服务器

在运行 E2E 测试之前，确保开发服务器正在运行：

```bash
# 终端 1 - 启动开发服务器
cd frontend
pnpm run dev
```

### 方式一：使用批处理文件（推荐 - Windows）

**无头模式**（不显示浏览器）:

```
双击运行: frontend/run-e2e-tests.bat
```

**有头模式**（显示浏览器）:

```
双击运行: frontend/run-e2e-headed.bat
```

### 方式二：使用 pnpm 命令

```bash
cd frontend

# 无头模式运行所有 E2E 测试
pnpm run test:e2e

# 显示浏览器窗口
pnpm run test:e2e:headed

# 调试模式（显示浏览器 + 慢放 + DevTools）
pnpm run test:e2e:debug

# 运行特定测试
pnpm run test:e2e -- login.e2e.ts

# 运行特定目录的测试
pnpm run test:e2e -- e2e/tests/auth
```

### E2E 测试输出

成功运行后，你应该看到类似输出：

```
PASS  e2e/tests/auth/login.e2e.ts (25.123 s)
PASS  e2e/tests/auth/signup.e2e.ts (30.456 s)
PASS  e2e/tests/dashboard/dashboard-basic.e2e.ts (20.789 s)
PASS  e2e/tests/daily-reports/daily-reports-basic.e2e.ts (28.234 s)
PASS  e2e/tests/topup/topup-basic.e2e.ts (32.567 s)

Test Suites: 5 passed, 5 total
Tests:       100 passed, 100 total
Time:        137.169 s
```

---

## 运行性能测试

### 前置条件

1. 开发服务器运行在 `http://localhost:3000`
2. 使用已登录的管理员账号

### 运行命令

```bash
cd frontend

# 运行所有性能测试
pnpm run test:performance

# 运行特定性能测试
pnpm run test:performance -- dashboard-performance.e2e.ts
```

### 性能报告

性能测试会生成 Markdown 报告，保存在：

```
frontend/e2e/reports/performance-{pageName}-{timestamp}.md
```

报告包含：

- Core Web Vitals 指标（FCP, LCP, CLS, TTI, TBT）
- 资源加载统计
- 性能评分

---

## 测试脚本说明

### package.json 脚本

| 脚本                        | 说明              | 用途            |
| --------------------------- | ----------------- | --------------- |
| `pnpm test`                 | 运行单元测试      | 日常开发        |
| `pnpm run test:watch`       | 监听模式单元测试  | 开发中实时测试  |
| `pnpm run test:coverage`    | 单元测试 + 覆盖率 | CI/CD、代码审查 |
| `pnpm run test:ci`          | CI 环境单元测试   | GitHub Actions  |
| `pnpm run test:e2e`         | E2E 测试（无头）  | CI/CD           |
| `pnpm run test:e2e:headed`  | E2E 测试（有头）  | 调试、演示      |
| `pnpm run test:e2e:debug`   | E2E 调试模式      | 问题排查        |
| `pnpm run test:performance` | 性能测试          | 性能监控        |
| `pnpm run test:all`         | 所有测试          | 完整验证        |

### 批处理文件

| 文件                 | 说明                  |
| -------------------- | --------------------- |
| `run-unit-tests.bat` | 运行单元测试          |
| `run-e2e-tests.bat`  | 运行 E2E 测试（无头） |
| `run-e2e-headed.bat` | 运行 E2E 测试（有头） |

---

## 常见问题

### Q1: 单元测试报错 "Cannot find module '@/components/...'"

**原因**: 路径别名配置问题

**解决方案**:

1. 检查 `jest.config.js` 中的 `moduleNameMapper`
2. 确保路径别名与 `tsconfig.json` 一致

### Q2: E2E 测试超时

**原因**: 开发服务器未运行或响应慢

**解决方案**:

1. 确保 `pnpm run dev` 正在运行
2. 检查 `http://localhost:3000` 是否可访问
3. 增加测试超时时间（在测试文件中设置）

```typescript
it('test case', async () => {
  // test code
}, 60000); // 60秒超时
```

### Q3: E2E 测试报错 "Protocol error: Target closed"

**原因**: Puppeteer 浏览器意外关闭

**解决方案**:

1. 使用有头模式查看问题：`pnpm run test:e2e:headed`
2. 检查页面是否有 JavaScript 错误
3. 增加等待时间

### Q4: 测试覆盖率太低

**解决方案**:

1. 运行 `pnpm run test:coverage` 查看详细报告
2. 打开 `coverage/lcov-report/index.html` 查看可视化报告
3. 为未覆盖的文件添加测试

### Q5: E2E 测试在 CI 环境失败

**解决方案**:

1. 确保 CI 环境安装了 Chrome/Chromium
2. 使用无头模式：`pnpm run test:e2e`
3. 添加环境变量：`HEADLESS=true`

### Q6: 性能测试指标不稳定

**原因**: 本地环境性能波动

**解决方案**:

1. 关闭其他占用资源的应用
2. 多次运行取平均值
3. 在 CI 环境中运行获得稳定结果

### Q7: 找不到测试文件

**解决方案**:

1. 检查文件命名是否符合规范：
   - 单元测试：`*.test.ts(x)` 或 `*.spec.ts(x)`
   - E2E 测试：`*.e2e.ts`
2. 检查文件位置：
   - 单元测试：`__tests__/` 目录
   - E2E 测试：`e2e/tests/` 目录

### Q8: Mock 不生效

**解决方案**:

1. 确保在测试前调用 `setupFetchMock()`
2. 确保在测试后调用 `resetFetchMock()`
3. 检查 Mock 的 URL 匹配模式

```typescript
beforeEach(() => {
  setupFetchMock();
});

afterEach(() => {
  resetFetchMock();
});
```

---

## 测试最佳实践

### 1. 单元测试

✅ **DO**:

- 测试组件的公共接口和行为
- 使用 `screen.getByRole` 等语义化查询
- 测试用户交互和边缘情况
- 保持测试独立（不依赖其他测试）

❌ **DON'T**:

- 测试实现细节
- 测试第三方库的功能
- 在测试中使用固定延迟（`setTimeout`）
- 依赖测试执行顺序

### 2. E2E 测试

✅ **DO**:

- 使用 Page Object Model
- 等待元素就绪再操作
- 添加有意义的日志输出
- 测试关键业务流程

❌ **DON'T**:

- 直接操作页面元素（应使用 POM）
- 使用 CSS 选择器（优先使用 data-testid）
- 忽略异步操作
- 测试过于细节的交互

### 3. 性能测试

✅ **DO**:

- 在稳定环境中运行
- 记录基准指标
- 监控趋势变化
- 关注 Core Web Vitals

❌ **DON'T**:

- 在开发环境设置严格阈值
- 忽略资源加载统计
- 一次性测试（应多次运行）

---

## 测试文档

- [单元测试文档](tests/README.md)
- [E2E 测试文档](e2e/README.md)
- [测试模板](tests/TEST_TEMPLATE.md)
- [测试实现报告](../docs/testing/TEST_IMPLEMENTATION_REPORT.md)

---

## 获取帮助

如果遇到问题：

1. 查看本文档的"常见问题"部分
2. 查看相关测试文档
3. 使用调试模式运行测试
4. 检查测试日志和截图
5. 联系开发团队

---

**最后更新**: 2025-12-09
**维护者**: AI Development Team
