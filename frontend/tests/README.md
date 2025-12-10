# 前端测试框架文档

本文档说明如何使用项目的测试框架。

## 📋 目录

- [快速开始](#快速开始)
- [测试框架组成](#测试框架组成)
- [运行测试](#运行测试)
- [编写测试](#编写测试)
- [Mock 工具](#mock-工具)
- [最佳实践](#最佳实践)

---

## 快速开始

### 1. 运行所有测试

```bash
npm test
```

### 2. 监听模式（开发时推荐）

```bash
npm run test:watch
```

### 3. 生成覆盖率报告

```bash
npm run test:coverage
```

### 4. 运行特定测试文件

```bash
npm test -- path/to/test.spec.tsx
```

### 5. CI 模式运行

```bash
npm run test:ci
```

---

## 测试框架组成

### 核心技术栈

| 工具 | 版本 | 用途 |
|------|------|------|
| **Jest** | ^29.7.0 | 测试运行器 |
| **React Testing Library** | ^16.0.1 | React 组件测试 |
| **@testing-library/jest-dom** | ^6.5.0 | DOM 断言扩展 |
| **@testing-library/user-event** | ^14.5.2 | 用户交互模拟 |

### 目录结构

```
frontend/
├── tests/                          # 测试工具和配置
│   ├── setup.ts                    # Jest 全局设置
│   ├── test-utils.tsx              # 测试工具函数
│   ├── mocks/                      # Mock 工具
│   │   ├── api.ts                  # API mock 工具
│   │   ├── auth.ts                 # 认证 mock 工具
│   │   └── index.ts                # 统一导出
│   ├── TEST_TEMPLATE.md            # 测试模板
│   └── README.md                   # 本文档
│
├── __tests__/                      # 测试文件
│   ├── setup.test.ts               # 框架验证测试
│   └── example/                    # 示例测试
│       ├── Button.test.tsx         # Button 组件示例
│       └── LoginForm.test.tsx      # 登录表单示例
│
└── jest.config.js                  # Jest 配置
```

---

## 运行测试

### 命令说明

```bash
# 运行所有测试
npm test

# 监听模式（文件变更时自动运行）
npm run test:watch

# 生成覆盖率报告（生成到 coverage/ 目录）
npm run test:coverage

# CI 模式（无 watch，生成覆盖率）
npm run test:ci

# 运行特定文件
npm test -- Button.test.tsx

# 运行匹配模式的测试
npm test -- --testNamePattern="should render"

# 更新快照
npm test -- -u
```

### 环境变量

测试环境自动设置以下环境变量：

```typescript
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
process.env.NEXT_PUBLIC_APP_URL = 'http://localhost:3000'
```

---

## 编写测试

### 基础测试结构

```typescript
import { render, screen } from '@/tests/test-utils'

describe('ComponentName', () => {
  it('should render correctly', () => {
    render(<ComponentName />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

### 使用 TanStack Query

```typescript
import { renderWithProviders } from '@/tests/test-utils'
import { mockFetchSuccess } from '@/tests/mocks'

describe('ComponentWithQuery', () => {
  it('should fetch and display data', async () => {
    mockFetchSuccess({ name: 'Test' })

    const { findByText } = renderWithProviders(<ComponentWithQuery />)

    expect(await findByText('Test')).toBeInTheDocument()
  })
})
```

### 用户交互测试

```typescript
import { render, screen } from '@/tests/test-utils'
import { userEvent } from '@/tests/test-utils'

describe('InteractiveComponent', () => {
  it('should handle click event', async () => {
    const user = userEvent.setup()

    render(<Button>Click Me</Button>)

    await user.click(screen.getByRole('button'))

    expect(screen.getByText('Clicked')).toBeInTheDocument()
  })
})
```

---

## Mock 工具

### API Mock

```typescript
import {
  setupFetchMock,
  resetFetchMock,
  mockFetchSuccess,
  mockFetchError,
  mockPaginatedResponse,
} from '@/tests/mocks'

describe('API Test', () => {
  beforeEach(() => {
    setupFetchMock()
  })

  afterEach(() => {
    resetFetchMock()
  })

  it('should handle API success', async () => {
    mockFetchSuccess({ id: 1, name: 'Test' })
    // ... test code
  })

  it('should handle API error', async () => {
    mockFetchError('API-001', 'Error message')
    // ... test code
  })

  it('should handle paginated data', async () => {
    const items = [{ id: 1 }, { id: 2 }]
    mockPaginatedResponse(items, 1, 20)
    // ... test code
  })
})
```

### 认证 Mock

```typescript
import {
  mockAuthenticatedState,
  mockUnauthenticatedState,
  mockAuthenticatedStateWithRole,
  mockUsers,
} from '@/tests/mocks'

describe('Auth Test', () => {
  it('should render for authenticated user', () => {
    mockAuthenticatedState()
    // ... test code
  })

  it('should redirect for unauthenticated user', () => {
    mockUnauthenticatedState()
    // ... test code
  })

  it('should handle admin role', () => {
    mockAuthenticatedStateWithRole('admin')
    // ... test code
  })
})
```

### Next.js Router Mock

```typescript
// Router 已在 setup.ts 中全局 mock
import { useRouter } from 'next/navigation'

const mockPush = jest.fn()

// 如需自定义 router 行为
jest.mocked(useRouter).mockReturnValue({
  push: mockPush,
  // ... other router methods
} as any)
```

---

## 最佳实践

### ✅ 推荐做法

1. **使用语义化查询**
   ```typescript
   // ✅ 好
   screen.getByRole('button', { name: /submit/i })

   // ❌ 避免
   screen.getByTestId('submit-button')
   ```

2. **等待异步操作**
   ```typescript
   // ✅ 好
   await waitFor(() => {
     expect(screen.getByText('Loaded')).toBeInTheDocument()
   })

   // ✅ 更好（自动等待）
   expect(await screen.findByText('Loaded')).toBeInTheDocument()
   ```

3. **清理 Mock**
   ```typescript
   afterEach(() => {
     jest.clearAllMocks()
     resetFetchMock()
     localStorage.clear()
   })
   ```

4. **测试用户行为而非实现**
   ```typescript
   // ✅ 好 - 测试行为
   await user.click(screen.getByRole('button'))
   expect(screen.getByText('Success')).toBeInTheDocument()

   // ❌ 避免 - 测试实现
   expect(component.state.count).toBe(1)
   ```

### ❌ 避免的做法

1. 不要测试第三方库的实现
2. 不要过度使用 `data-testid`
3. 不要直接访问组件内部状态
4. 不要忘记清理副作用（定时器、监听器等）

---

## 常见问题

### Q: 测试运行很慢怎么办？

A: 使用 `--maxWorkers=50%` 限制并发数：
```bash
npm test -- --maxWorkers=50%
```

### Q: 如何调试失败的测试？

A: 使用 `screen.debug()` 查看 DOM：
```typescript
it('test', () => {
  render(<Component />)
  screen.debug() // 打印当前 DOM
})
```

### Q: 如何跳过某个测试？

A: 使用 `it.skip()` 或 `describe.skip()`：
```typescript
it.skip('not ready yet', () => {
  // ...
})
```

### Q: 如何只运行某个测试？

A: 使用 `it.only()` 或 `describe.only()`：
```typescript
it.only('focus on this test', () => {
  // ...
})
```

---

## 参考资源

- [Jest 官方文档](https://jestjs.io/)
- [React Testing Library 文档](https://testing-library.com/react)
- [Testing Library 查询优先级](https://testing-library.com/docs/queries/about/#priority)
- [测试模板](./TEST_TEMPLATE.md)

---

## 获取帮助

如遇到问题：
1. 查看 [TEST_TEMPLATE.md](./TEST_TEMPLATE.md) 中的示例
2. 查看 `__tests__/example/` 目录中的示例测试
3. 运行 `npm test -- __tests__/setup.test.ts` 验证框架配置
