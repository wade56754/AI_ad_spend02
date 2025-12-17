/**
 * 示例测试：登录表单
 *
 * 演示如何测试表单组件，包括：
 * - 表单渲染
 * - 用户输入
 * - 表单验证
 * - API 调用
 * - 错误处理
 */

import { render, screen, waitFor } from '../../tests/test-utils'
import { userEvent } from '../../tests/test-utils'
import {
  setupFetchMock,
  resetFetchMock,
  mockFetchSuccess,
  mockFetchError,
  mockApiSuccess,
  mockAuthenticatedState,
} from '../../tests/mocks'

// 示例登录表单组件
interface LoginFormProps {
  onSuccess?: (data: any) => void
  onError?: (error: Error) => void
}

function LoginForm({ onSuccess, onError }: LoginFormProps) {
  const [email, setEmail] = React.useState('')
  const [password, setPassword] = React.useState('')
  const [error, setError] = React.useState('')
  const [isLoading, setIsLoading] = React.useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    // 客户端验证
    if (!email || !password) {
      setError('邮箱和密码不能为空')
      setIsLoading(false)
      return
    }

    if (!/\S+@\S+\.\S+/.test(email)) {
      setError('邮箱格式不正确')
      setIsLoading(false)
      return
    }

    try {
      // API 调用
      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })

      const data = await response.json()

      if (!response.ok) {
        throw new Error(data.error?.message || '登录失败')
      }

      onSuccess?.(data.data)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '登录失败'
      setError(errorMessage)
      onError?.(err as Error)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} aria-label="登录表单">
      <div>
        <label htmlFor="email">邮箱</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="请输入邮箱"
          disabled={isLoading}
        />
      </div>

      <div>
        <label htmlFor="password">密码</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="请输入密码"
          disabled={isLoading}
        />
      </div>

      {error && (
        <div role="alert" className="error-message">
          {error}
        </div>
      )}

      <button type="submit" disabled={isLoading}>
        {isLoading ? '登录中...' : '登录'}
      </button>
    </form>
  )
}

// Mock React
import React from 'react'

describe('LoginForm Component', () => {
  beforeEach(() => {
    setupFetchMock()
  })

  afterEach(() => {
    resetFetchMock()
    jest.clearAllMocks()
  })

  describe('表单渲染', () => {
    it('should render all form fields', () => {
      render(<LoginForm />)

      expect(screen.getByLabelText(/邮箱/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/密码/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /登录/i })).toBeInTheDocument()
    })

    it('should have correct input placeholders', () => {
      render(<LoginForm />)

      expect(screen.getByPlaceholderText(/请输入邮箱/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/请输入密码/i)).toBeInTheDocument()
    })
  })

  describe('用户输入', () => {
    it('should update email field on user input', async () => {
      const user = userEvent.setup()
      render(<LoginForm />)

      const emailInput = screen.getByLabelText(/邮箱/i)
      await user.type(emailInput, 'test@example.com')

      expect(emailInput).toHaveValue('test@example.com')
    })

    it('should update password field on user input', async () => {
      const user = userEvent.setup()
      render(<LoginForm />)

      const passwordInput = screen.getByLabelText(/密码/i)
      await user.type(passwordInput, 'password123')

      expect(passwordInput).toHaveValue('password123')
    })

    it('should hide password input', () => {
      render(<LoginForm />)

      const passwordInput = screen.getByLabelText(/密码/i)
      expect(passwordInput).toHaveAttribute('type', 'password')
    })
  })

  describe('表单验证', () => {
    it('should show error when email is empty', async () => {
      const user = userEvent.setup()
      render(<LoginForm />)

      const passwordInput = screen.getByLabelText(/密码/i)
      await user.type(passwordInput, 'password123')

      const submitButton = screen.getByRole('button', { name: /登录/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/邮箱和密码不能为空/i)
      })
    })

    it('should show error when password is empty', async () => {
      const user = userEvent.setup()
      render(<LoginForm />)

      const emailInput = screen.getByLabelText(/邮箱/i)
      await user.type(emailInput, 'test@example.com')

      const submitButton = screen.getByRole('button', { name: /登录/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/邮箱和密码不能为空/i)
      })
    })

    it('should show error for invalid email format', async () => {
      const user = userEvent.setup()
      render(<LoginForm />)

      const emailInput = screen.getByLabelText(/邮箱/i)
      const passwordInput = screen.getByLabelText(/密码/i)

      await user.type(emailInput, 'invalid-email')
      await user.type(passwordInput, 'password123')

      const submitButton = screen.getByRole('button', { name: /登录/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/邮箱格式不正确/i)
      })
    })
  })

  describe('API 调用', () => {
    it('should call login API with correct credentials', async () => {
      const user = userEvent.setup()
      const mockResponse = mockApiSuccess({
        access_token: 'mock-token',
        user: { id: '1', email: 'test@example.com' },
      })

      mockFetchSuccess(mockResponse.data)

      render(<LoginForm />)

      const emailInput = screen.getByLabelText(/邮箱/i)
      const passwordInput = screen.getByLabelText(/密码/i)

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')

      const submitButton = screen.getByRole('button', { name: /登录/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          'http://localhost:8000/api/v1/auth/login',
          expect.objectContaining({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              email: 'test@example.com',
              password: 'password123',
            }),
          })
        )
      })
    })

    it('should call onSuccess callback on successful login', async () => {
      const user = userEvent.setup()
      const handleSuccess = jest.fn()
      const mockData = {
        access_token: 'mock-token',
        user: { id: '1', email: 'test@example.com' },
      }

      mockFetchSuccess(mockData)

      render(<LoginForm onSuccess={handleSuccess} />)

      const emailInput = screen.getByLabelText(/邮箱/i)
      const passwordInput = screen.getByLabelText(/密码/i)

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')

      const submitButton = screen.getByRole('button', { name: /登录/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(handleSuccess).toHaveBeenCalledWith(mockData)
      })
    })
  })

  describe('错误处理', () => {
    it('should show error message on API failure', async () => {
      const user = userEvent.setup()

      mockFetchError('AUTH-001', '邮箱或密码错误', 401)

      render(<LoginForm />)

      const emailInput = screen.getByLabelText(/邮箱/i)
      const passwordInput = screen.getByLabelText(/密码/i)

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'wrongpassword')

      const submitButton = screen.getByRole('button', { name: /登录/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/邮箱或密码错误/i)
      })
    })

    it('should call onError callback on login failure', async () => {
      const user = userEvent.setup()
      const handleError = jest.fn()

      mockFetchError('AUTH-001', '登录失败', 401)

      render(<LoginForm onError={handleError} />)

      const emailInput = screen.getByLabelText(/邮箱/i)
      const passwordInput = screen.getByLabelText(/密码/i)

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')

      const submitButton = screen.getByRole('button', { name: /登录/i })
      await user.click(submitButton)

      await waitFor(() => {
        expect(handleError).toHaveBeenCalled()
      })
    })
  })

  describe('加载状态', () => {
    it('should show loading state during API call', async () => {
      const user = userEvent.setup()

      // Mock slow API response
      ;(global.fetch as jest.Mock).mockImplementation(
        () =>
          new Promise((resolve) => {
            setTimeout(() => {
              resolve({
                ok: true,
                json: async () => mockApiSuccess({ token: 'test' }),
              })
            }, 100)
          })
      )

      render(<LoginForm />)

      const emailInput = screen.getByLabelText(/邮箱/i)
      const passwordInput = screen.getByLabelText(/密码/i)

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')

      const submitButton = screen.getByRole('button', { name: /登录/i })
      await user.click(submitButton)

      // Check loading state
      expect(screen.getByRole('button', { name: /登录中/i })).toBeDisabled()

      // Wait for loading to finish
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /登录/i })).not.toBeDisabled()
      })
    })

    it('should disable inputs during loading', async () => {
      const user = userEvent.setup()

      ;(global.fetch as jest.Mock).mockImplementation(
        () =>
          new Promise((resolve) => {
            setTimeout(() => {
              resolve({
                ok: true,
                json: async () => mockApiSuccess({ token: 'test' }),
              })
            }, 100)
          })
      )

      render(<LoginForm />)

      const emailInput = screen.getByLabelText(/邮箱/i)
      const passwordInput = screen.getByLabelText(/密码/i)

      await user.type(emailInput, 'test@example.com')
      await user.type(passwordInput, 'password123')

      const submitButton = screen.getByRole('button', { name: /登录/i })
      await user.click(submitButton)

      expect(emailInput).toBeDisabled()
      expect(passwordInput).toBeDisabled()
    })
  })
})
