/**
 * API请求封装模块
 * 提供统一的HTTP请求方法和错误处理
 */
import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  InternalAxiosRequestConfig,
} from 'axios'

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message: string
  code: string
  request_id: string
  timestamp: string
}

// 分页响应类型
export interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  pagination: {
    page: number
    size: number
    total: number
    pages: number
    has_next: boolean
    has_prev: boolean
  }
}

// 错误响应类型
export interface ApiError {
  success: false
  error: {
    code: string
    message: string
    details?: any
  }
  request_id: string
  timestamp: string
}

// 配置类型
export interface ApiConfig {
  baseURL?: string
  timeout?: number
  headers?: Record<string, string>
  withCredentials?: boolean
}

// Token管理
class TokenManager {
  private static instance: TokenManager
  private accessToken: string | null = null
  private refreshToken: string | null = null
  private refreshPromise: Promise<string> | null = null

  static getInstance(): TokenManager {
    if (!TokenManager.instance) {
      TokenManager.instance = new TokenManager()
    }
    return TokenManager.instance
  }

  setTokens(accessToken: string, refreshToken: string): void {
    this.accessToken = accessToken
    this.refreshToken = refreshToken

    // 存储到localStorage
    localStorage.setItem('access_token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
  }

  getAccessToken(): string | null {
    if (!this.accessToken) {
      this.accessToken = localStorage.getItem('access_token')
    }
    return this.accessToken
  }

  getRefreshToken(): string | null {
    if (!this.refreshToken) {
      this.refreshToken = localStorage.getItem('refresh_token')
    }
    return this.refreshToken
  }

  clearTokens(): void {
    this.accessToken = null
    this.refreshToken = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  async refreshAccessToken(): Promise<string> {
    // 防止重复刷新
    if (this.refreshPromise) {
      return this.refreshPromise
    }

    const refreshToken = this.getRefreshToken()
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    this.refreshPromise = this.doRefreshToken(refreshToken)

    try {
      const newAccessToken = await this.refreshPromise
      return newAccessToken
    } finally {
      this.refreshPromise = null
    }
  }

  private async doRefreshToken(refreshToken: string): Promise<string> {
    try {
      const response = await axios.post('/api/v1/auth/refresh', {
        refresh_token: refreshToken
      })

      const { access_token, refresh_token } = response.data.data
      this.setTokens(access_token, refresh_token)

      return access_token
    } catch (error) {
      this.clearTokens()
      throw error
    }
  }
}

// 创建API客户端
class ApiClient {
  private instance: AxiosInstance
  private tokenManager: TokenManager

  constructor(config: ApiConfig = {}) {
    this.tokenManager = TokenManager.getInstance()

    // 创建axios实例
    this.instance = axios.create({
      baseURL: config.baseURL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        ...config.headers,
      },
      withCredentials: config.withCredentials || false,
    })

    // 设置请求拦截器
    this.setupRequestInterceptors()

    // 设置响应拦截器
    this.setupResponseInterceptors()
  }

  private setupRequestInterceptors(): void {
    // 请求前拦截器
    this.instance.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        // 添加请求ID
        config.headers = config.headers || {}
        config.headers['X-Request-ID'] = this.generateRequestId()

        // 添加认证token
        const token = this.tokenManager.getAccessToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        // 记录请求日志
        console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
          params: config.params,
          data: config.data,
        })

        return config
      },
      (error) => {
        console.error('[API Request Error]', error)
        return Promise.reject(error)
      }
    )
  }

  private setupResponseInterceptors(): void {
    // 响应拦截器
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => {
        // 记录响应日志
        console.log(`[API Response] ${response.config.method?.toUpperCase()} ${response.config.url}`, {
          status: response.status,
          data: response.data,
        })

        return response
      },
      async (error) => {
        const originalRequest = error.config

        // 记录错误日志
        console.error(`[API Error] ${originalRequest?.method?.toUpperCase()} ${originalRequest?.url}`, {
          status: error.response?.status,
          data: error.response?.data,
          message: error.message,
        })

        // 处理401未授权错误
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            // 刷新token
            const newToken = await this.tokenManager.refreshAccessToken()

            // 更新请求头
            originalRequest.headers.Authorization = `Bearer ${newToken}`

            // 重新发送原始请求
            return this.instance(originalRequest)
          } catch (refreshError) {
            // 刷新失败，清除token并跳转到登录页
            this.tokenManager.clearTokens()
            window.location.href = '/auth/login'
            return Promise.reject(refreshError)
          }
        }

        return Promise.reject(error)
      }
    )
  }

  private generateRequestId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  // GET请求
  async get<T = any>(
    url: string,
    params?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.instance.get(url, { ...config, params })
    return response.data
  }

  // POST请求
  async post<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.instance.post(url, data, config)
    return response.data
  }

  // PUT请求
  async put<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.instance.put(url, data, config)
    return response.data
  }

  // PATCH请求
  async patch<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.instance.patch(url, data, config)
    return response.data
  }

  // DELETE请求
  async delete<T = any>(
    url: string,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const response = await this.instance.delete(url, config)
    return response.data
  }

  // 分页查询
  async getPaginated<T = any>(
    url: string,
    params?: {
      page?: number
      size?: number
      [key: string]: any
    },
    config?: AxiosRequestConfig
  ): Promise<PaginatedResponse<T>> {
    const response = await this.instance.get(url, { ...config, params })
    return response.data
  }

  // 文件上传
  async upload<T = any>(
    url: string,
    file: File,
    onProgress?: (progress: number) => void,
    config?: AxiosRequestConfig
  ): Promise<ApiResponse<T>> {
    const formData = new FormData()
    formData.append('file', file)

    const response = await this.instance.post(url, formData, {
      ...config,
      headers: {
        ...config?.headers,
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onProgress(progress)
        }
      },
    })

    return response.data
  }

  // 文件下载
  async download(
    url: string,
    filename?: string,
    config?: AxiosRequestConfig
  ): Promise<void> {
    const response = await this.instance.get(url, {
      ...config,
      responseType: 'blob',
    })

    // 创建下载链接
    const blob = new Blob([response.data])
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = filename || 'download'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
  }

  // 获取原始axios实例（用于特殊场景）
  getAxiosInstance(): AxiosInstance {
    return this.instance
  }
}

// 创建默认API客户端实例
const apiClient = new ApiClient()

// 导出工厂函数和默认实例
export function createApiClient(config?: ApiConfig): ApiClient {
  return new ApiClient(config)
}

export default apiClient

// 导出便捷方法
export const api = {
  get: <T = any>(url: string, params?: any, config?: AxiosRequestConfig) =>
    apiClient.get<T>(url, params, config),

  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    apiClient.post<T>(url, data, config),

  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    apiClient.put<T>(url, data, config),

  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    apiClient.patch<T>(url, data, config),

  delete: <T = any>(url: string, config?: AxiosRequestConfig) =>
    apiClient.delete<T>(url, config),

  getPaginated: <T = any>(url: string, params?: any, config?: AxiosRequestConfig) =>
    apiClient.getPaginated<T>(url, params, config),

  upload: <T = any>(
    url: string,
    file: File,
    onProgress?: (progress: number) => void,
    config?: AxiosRequestConfig
  ) => apiClient.upload<T>(url, file, onProgress, config),

  download: (url: string, filename?: string, config?: AxiosRequestConfig) =>
    apiClient.download(url, filename, config),
}

// 导出Token管理器
export const tokenManager = TokenManager.getInstance()