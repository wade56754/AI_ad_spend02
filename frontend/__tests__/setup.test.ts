/**
 * 测试框架设置验证
 *
 * 这个测试文件用于验证测试框架是否正确配置
 */

describe('Test Framework Setup', () => {
  it('should run basic test', () => {
    expect(true).toBe(true)
  })

  it('should have access to Jest globals', () => {
    expect(jest).toBeDefined()
    expect(describe).toBeDefined()
    expect(it).toBeDefined()
    expect(expect).toBeDefined()
  })

  it('should have correct environment variables', () => {
    expect(process.env.NEXT_PUBLIC_API_URL).toBe('http://localhost:8000')
    expect(process.env.NEXT_PUBLIC_APP_URL).toBe('http://localhost:3000')
  })

  it('should support async tests', async () => {
    const promise = Promise.resolve('success')
    await expect(promise).resolves.toBe('success')
  })

  it('should support mock functions', () => {
    const mockFn = jest.fn()
    mockFn('test')

    expect(mockFn).toHaveBeenCalledTimes(1)
    expect(mockFn).toHaveBeenCalledWith('test')
  })
})

describe('DOM Testing Setup', () => {
  it('should have jest-dom matchers', () => {
    const element = document.createElement('div')
    element.textContent = 'Hello World'

    document.body.appendChild(element)

    expect(element).toBeInTheDocument()
    expect(element).toHaveTextContent('Hello World')

    document.body.removeChild(element)
  })

  it('should have matchMedia mock', () => {
    expect(window.matchMedia).toBeDefined()

    const mediaQuery = window.matchMedia('(min-width: 768px)')
    expect(mediaQuery.matches).toBe(false)
  })

  it('should have IntersectionObserver mock', () => {
    expect(window.IntersectionObserver).toBeDefined()

    const observer = new IntersectionObserver(() => {})
    expect(observer).toBeDefined()
  })
})
