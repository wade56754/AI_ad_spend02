/**
 * API Mock Helpers
 *
 * 提供 API 请求的 mock 工具函数
 */

/**
 * Mock fetch 响应
 */
export function mockFetchResponse(data: any, status = 200) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: async () => data,
    text: async () => JSON.stringify(data),
    headers: new Headers({
      'content-type': 'application/json',
    }),
  } as Response)
}

/**
 * Mock 成功的 API 响应（符合 API_SOT.md v9.0 Envelope 格式）
 */
export function mockApiSuccess<T>(data: T) {
  return {
    success: true,
    data,
    message: 'Success',
  }
}

/**
 * Mock 失败的 API 响应（符合 ERROR_CODES_SOT.md v2.1）
 */
export function mockApiError(code: string, message: string, details?: any) {
  return {
    success: false,
    error: {
      code,
      message,
      details,
    },
  }
}

/**
 * Mock 分页响应
 */
export function mockPaginatedResponse<T>(
  items: T[],
  page = 1,
  pageSize = 20,
  total?: number
) {
  const actualTotal = total ?? items.length
  return mockApiSuccess({
    items,
    pagination: {
      page,
      page_size: pageSize,
      total: actualTotal,
      total_pages: Math.ceil(actualTotal / pageSize),
    },
  })
}

/**
 * 设置全局 fetch mock
 */
export function setupFetchMock() {
  global.fetch = jest.fn()
}

/**
 * 重置 fetch mock
 */
export function resetFetchMock() {
  if (global.fetch && typeof (global.fetch as any).mockReset === 'function') {
    ;(global.fetch as jest.Mock).mockReset()
  }
}

/**
 * Mock fetch 返回成功响应
 */
export function mockFetchSuccess<T>(data: T) {
  ;(global.fetch as jest.Mock).mockResolvedValueOnce(
    mockFetchResponse(mockApiSuccess(data), 200)
  )
}

/**
 * Mock fetch 返回错误响应
 */
export function mockFetchError(code: string, message: string, status = 400) {
  ;(global.fetch as jest.Mock).mockResolvedValueOnce(
    mockFetchResponse(mockApiError(code, message), status)
  )
}

/**
 * Mock 401 未授权错误
 */
export function mockUnauthorizedError() {
  mockFetchError('AUTH-001', 'Unauthorized', 401)
}

/**
 * Mock 403 权限不足错误
 */
export function mockForbiddenError() {
  mockFetchError('AUTH-002', 'Forbidden', 403)
}

/**
 * Mock 网络错误
 */
export function mockNetworkError() {
  ;(global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'))
}
