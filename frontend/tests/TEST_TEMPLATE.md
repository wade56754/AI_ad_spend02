# 测试模板指南

本文档提供标准的测试模板和最佳实践。

## 📋 目录

1. [组件测试模板](#组件测试模板)
2. [页面测试模板](#页面测试模板)
3. [Hook 测试模板](#hook-测试模板)
4. [API 测试模板](#api-测试模板)
5. [测试最佳实践](#测试最佳实践)

---

## 组件测试模板

### 基础组件测试

```typescript
import { render, screen } from '@/tests/test-utils'
import { ComponentName } from './ComponentName'

describe('ComponentName', () => {
  it('should render correctly', () => {
    render(<ComponentName />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('should handle user interaction', async () => {
    const handleClick = jest.fn()
    const { user } = render(<ComponentName onClick={handleClick} />)

    await user.click(screen.getByRole('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('should display correct props', () => {
    const props = { title: 'Test Title', description: 'Test Description' }
    render(<ComponentName {...props} />)

    expect(screen.getByText(props.title)).toBeInTheDocument()
    expect(screen.getByText(props.description)).toBeInTheDocument()
  })
})
```

### 带状态的组件测试

```typescript
import { render, screen, waitFor } from '@/tests/test-utils'
import { StatefulComponent } from './StatefulComponent'

describe('StatefulComponent', () => {
  it('should update state on interaction', async () => {
    const { user } = render(<StatefulComponent />)

    const input = screen.getByRole('textbox')
    await user.type(input, 'test input')

    await waitFor(() => {
      expect(input).toHaveValue('test input')
    })
  })
})
```

---

## 页面测试模板

### Next.js App Router 页面测试

```typescript
import { render, screen } from '@/tests/test-utils'
import { mockAuthenticatedState, mockFetchSuccess } from '@/tests/mocks'
import Page from './page'

// Mock Next.js navigation
const mockPush = jest.fn()
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => '/test',
  useSearchParams: () => new URLSearchParams(),
}))

describe('Page Component', () => {
  beforeEach(() => {
    // 设置认证状态
    mockAuthenticatedState()

    // Mock API 响应
    mockFetchSuccess({ data: 'test' })
  })

  it('should render page content', () => {
    render(<Page />)
    expect(screen.getByRole('heading')).toBeInTheDocument()
  })

  it('should redirect when not authenticated', () => {
    // Mock 未登录状态
    localStorage.clear()

    render(<Page />)

    // 验证重定向
    expect(mockPush).toHaveBeenCalledWith('/login')
  })
})
```

---

## Hook 测试模板

### 自定义 Hook 测试

```typescript
import { renderHook, waitFor } from '@testing-library/react'
import { createTestQueryClient } from '@/tests/test-utils'
import { mockFetchSuccess } from '@/tests/mocks'
import { useCustomHook } from './useCustomHook'
import { QueryClientProvider } from '@tanstack/react-query'

describe('useCustomHook', () => {
  it('should fetch data successfully', async () => {
    const queryClient = createTestQueryClient()

    mockFetchSuccess({ id: 1, name: 'Test' })

    const { result } = renderHook(() => useCustomHook(), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      ),
    })

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true)
    })

    expect(result.current.data).toEqual({ id: 1, name: 'Test' })
  })

  it('should handle error state', async () => {
    const queryClient = createTestQueryClient()

    mockFetchError('ERR-001', 'Test error')

    const { result } = renderHook(() => useCustomHook(), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      ),
    })

    await waitFor(() => {
      expect(result.current.isError).toBe(true)
    })
  })
})
```

---

## API 测试模板

### API 服务函数测试

```typescript
import { mockFetchSuccess, mockFetchError, setupFetchMock, resetFetchMock } from '@/tests/mocks'
import { apiService } from './apiService'

describe('API Service', () => {
  beforeEach(() => {
    setupFetchMock()
  })

  afterEach(() => {
    resetFetchMock()
  })

  it('should fetch data successfully', async () => {
    const mockData = { id: 1, name: 'Test' }
    mockFetchSuccess(mockData)

    const result = await apiService.getData()

    expect(result).toEqual(mockData)
    expect(global.fetch).toHaveBeenCalledTimes(1)
  })

  it('should handle API error', async () => {
    mockFetchError('API-001', 'API Error')

    await expect(apiService.getData()).rejects.toThrow('API Error')
  })

  it('should send correct request parameters', async () => {
    mockFetchSuccess({ success: true })

    await apiService.postData({ name: 'Test' })

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/endpoint'),
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ name: 'Test' }),
      })
    )
  })
})
```

---

## 测试最佳实践

### 1. 测试命名规范

```typescript
// ✅ 好的命名
it('should render login form with email and password fields', () => {})
it('should show error message when validation fails', () => {})
it('should call onSubmit with form data when form is valid', () => {})

// ❌ 不好的命名
it('test 1', () => {})
it('renders', () => {})
it('works', () => {})
```

### 2. AAA 模式（Arrange, Act, Assert）

```typescript
it('should update counter on button click', async () => {
  // Arrange - 准备测试数据和状态
  const { user } = render(<Counter initialValue={0} />)
  const button = screen.getByRole('button', { name: /increment/i })

  // Act - 执行操作
  await user.click(button)

  // Assert - 验证结果
  expect(screen.getByText('Count: 1')).toBeInTheDocument()
})
```

### 3. 使用 screen 查询

```typescript
// ✅ 推荐：使用语义化查询
const button = screen.getByRole('button', { name: /submit/i })
const heading = screen.getByRole('heading', { name: /dashboard/i })
const input = screen.getByLabelText(/email/i)

// ❌ 避免：使用 testId（除非必要）
const element = screen.getByTestId('submit-button')
```

### 4. 异步测试

```typescript
// ✅ 使用 waitFor
await waitFor(() => {
  expect(screen.getByText('Loaded')).toBeInTheDocument()
})

// ✅ 使用 findBy（自动等待）
const element = await screen.findByText('Loaded')

// ❌ 避免：不等待异步操作
expect(screen.getByText('Loaded')).toBeInTheDocument() // 可能失败
```

### 5. Mock 管理

```typescript
describe('Component', () => {
  beforeEach(() => {
    // 每个测试前设置 mock
    setupFetchMock()
    mockAuthenticatedState()
  })

  afterEach(() => {
    // 每个测试后清理 mock
    resetFetchMock()
    jest.clearAllMocks()
    localStorage.clear()
  })

  it('test case', () => {
    // 测试逻辑
  })
})
```

### 6. 测试覆盖建议

每个组件/页面应该测试：
- ✅ 基本渲染（快照或关键元素）
- ✅ 用户交互（点击、输入等）
- ✅ 边界情况（空数据、错误状态）
- ✅ 权限控制（不同角色的行为）
- ✅ 加载状态
- ✅ 错误处理

---

## 常用查询优先级

按优先级从高到低：

1. **getByRole** - 最推荐，符合无障碍标准
   ```typescript
   screen.getByRole('button', { name: /submit/i })
   ```

2. **getByLabelText** - 表单元素
   ```typescript
   screen.getByLabelText(/email/i)
   ```

3. **getByPlaceholderText** - 占位符
   ```typescript
   screen.getByPlaceholderText(/enter email/i)
   ```

4. **getByText** - 文本内容
   ```typescript
   screen.getByText(/welcome/i)
   ```

5. **getByTestId** - 最后选择
   ```typescript
   screen.getByTestId('custom-element')
   ```

---

## 运行测试

```bash
# 运行所有测试
npm test

# 监听模式
npm run test:watch

# 生成覆盖率报告
npm run test:coverage

# 运行特定测试文件
npm test -- path/to/test.spec.tsx
```
