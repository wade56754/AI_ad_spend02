/**
 * 全局类型定义
 */

// ==================== 基础类型 ====================

export type ID = number | string

export interface BaseEntity {
  id: ID
  created_at: string
  updated_at: string
}

// ==================== 用户相关 ====================

export type UserRole = 'admin' | 'finance' | 'data_operator' | 'account_manager' | 'media_buyer'

export interface User extends BaseEntity {
  email: string
  username: string
  full_name?: string
  role: UserRole
  is_active: boolean
  is_superuser: boolean
  avatar_url?: string
  last_login?: string
}

export interface CreateUserData {
  email: string
  username: string
  password: string
  full_name?: string
  role: UserRole
}

export interface UpdateUserData {
  email?: string
  username?: string
  full_name?: string
  role?: UserRole
  is_active?: boolean
}

// ==================== 项目相关 ====================

export type ProjectStatus = 'active' | 'paused' | 'completed' | 'cancelled'

export interface Project extends BaseEntity {
  name: string
  description?: string
  client_name: string
  client_email?: string
  status: ProjectStatus
  budget?: number
  currency?: string
  start_date?: string
  end_date?: string
  owner_id: number
  account_manager_id?: number
  media_buyers: User[]
  created_by: number
  updated_by: number
}

export interface CreateProjectData {
  name: string
  description?: string
  client_name: string
  client_email?: string
  budget?: number
  currency?: string
  start_date?: string
  end_date?: string
  account_manager_id?: number
  media_buyer_ids?: number[]
}

export interface UpdateProjectData {
  name?: string
  description?: string
  client_name?: string
  client_email?: string
  status?: ProjectStatus
  budget?: number
  currency?: string
  start_date?: string
  end_date?: string
  account_manager_id?: number
  media_buyer_ids?: number[]
}

// ==================== 渠道相关 ====================

export type ChannelStatus = 'active' | 'inactive' | 'suspended'

export interface Channel extends BaseEntity {
  name: string
  platform: string
  account_id: string
  status: ChannelStatus
  daily_budget?: number
  currency?: string
  manager_id?: number
  created_by: number
  updated_by: number
}

export interface CreateChannelData {
  name: string
  platform: string
  account_id: string
  daily_budget?: number
  currency?: string
  manager_id?: number
}

// ==================== 广告账户相关 ====================

export type AdAccountStatus = 'active' | 'inactive' | 'banned' | 'pending' | 'suspended'

export interface AdAccount extends BaseEntity {
  account_id: string
  name: string
  platform: string
  status: AdAccountStatus
  channel_id: number
  project_id?: number
  assigned_to?: number
  daily_budget?: number
  lifetime_budget?: number
  currency?: string
  timezone?: string
  created_by: number
  updated_by: number
}

export interface CreateAdAccountData {
  account_id: string
  name: string
  platform: string
  channel_id: number
  project_id?: number
  assigned_to?: number
  daily_budget?: number
  lifetime_budget?: number
  currency?: string
  timezone?: string
}

// ==================== 日报相关 ====================

export type DailyReportStatus = 'draft' | 'submitted' | 'reviewed' | 'approved' | 'rejected'

export interface DailyReport extends BaseEntity {
  report_date: string
  account_id: number
  submitter_id: number
  reviewer_id?: number
  status: DailyReportStatus
  spend: number
  impressions: number
  clicks: number
  conversions: number
  revenue?: number
  cpm?: number
  cpc?: number
  ctr?: number
  cpa?: number
  roas?: number
  notes?: string
  attachments?: string[]
  submitted_at?: string
  reviewed_at?: string
  rejection_reason?: string
}

export interface CreateDailyReportData {
  report_date: string
  account_id: number
  spend: number
  impressions: number
  clicks: number
  conversions: number
  revenue?: number
  notes?: string
  attachments?: string[]
}

// ==================== 充值相关 ====================

export type TopupStatus = 'draft' | 'pending_review' | 'approved' | 'rejected' | 'paid' | 'confirmed' | 'cancelled'

export interface Topup extends BaseEntity {
  request_id: string
  account_id: number
  requester_id: number
  reviewer_id?: number
  approver_id?: number
  status: TopupStatus
  amount: number
  currency?: string
  payment_method?: string
  payment_reference?: string
  notes?: string
  requested_at?: string
  reviewed_at?: string
  approved_at?: string
  paid_at?: string
  confirmed_at?: string
  rejection_reason?: string
}

export interface CreateTopupData {
  account_id: number
  amount: number
  currency?: string
  payment_method?: string
  notes?: string
}

// ==================== 对账相关 ====================

export type ReconciliationStatus = 'draft' | 'pending' | 'completed' | 'disputed'

export interface Reconciliation extends BaseEntity {
  reconciliation_id: string
  period_start: string
  period_end: string
  account_id: number
  total_spend: number
  total_charges: number
  total_adjustments: number
  final_amount: number
  currency?: string
  status: ReconciliationStatus
  reconciled_by?: number
  notes?: string
  attachments?: string[]
  completed_at?: string
}

// ==================== API请求/响应类型 ====================

export interface PaginationParams {
  page?: number
  size?: number
  sort?: string
  order?: 'asc' | 'desc'
}

export interface PaginationMeta {
  page: number
  size: number
  total: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

export interface ApiResponse<T = any> {
  success: boolean
  data: T
  message: string
  code: string
  request_id: string
  timestamp: string
}

export interface PaginatedResponse<T = any> extends ApiResponse<T[]> {
  pagination: PaginationMeta
}

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

// ==================== 表单类型 ====================

export interface FormErrors {
  [key: string]: string | undefined
}

export interface FormState<T> {
  data: T
  errors: FormErrors
  isSubmitting: boolean
  isDirty: boolean
}

// ==================== UI组件类型 ====================

export interface TableColumn<T = any> {
  key: keyof T
  title: string
  dataIndex?: keyof T
  width?: number | string
  align?: 'left' | 'center' | 'right'
  sorter?: boolean
  filterable?: boolean
  render?: (value: any, record: T, index: number) => React.ReactNode
}

export interface TableProps<T = any> {
  columns: TableColumn<T>[]
  dataSource: T[]
  loading?: boolean
  pagination?: PaginationProps
  rowSelection?: RowSelectionProps<T>
  onRow?: (record: T, index?: number) => React.HTMLAttributes<HTMLElement>
}

export interface PaginationProps {
  current: number
  total: number
  pageSize: number
  showSizeChanger?: boolean
  showQuickJumper?: boolean
  showTotal?: (total: number, range: [number, number]) => string
  onChange: (page: number, pageSize: number) => void
}

export interface RowSelectionProps<T = any> {
  selectedRowKeys?: ID[]
  onChange?: (selectedRowKeys: ID[], selectedRows: T[]) => void
  getCheckboxProps?: (record: T) => { disabled: boolean }
}

// ==================== 路由类型 ====================

export interface RouteConfig {
  path: string
  name: string
  component?: React.ComponentType
  redirect?: string
  meta?: {
    title?: string
    icon?: React.ReactNode
    hidden?: boolean
    requiresAuth?: boolean
    roles?: UserRole[]
    keepAlive?: boolean
  }
  children?: RouteConfig[]
}

// ==================== 通知类型 ====================

export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface Notification {
  id: string
  type: NotificationType
  title: string
  message?: string
  duration?: number
  timestamp: number
}

// ==================== 文件上传类型 ====================

export interface UploadFile {
  uid: string
  name: string
  status: 'uploading' | 'done' | 'error'
  url?: string
  response?: any
  error?: any
  size?: number
  type?: string
}

export interface UploadProps {
  accept?: string
  multiple?: boolean
  maxCount?: number
  maxSize?: number
  action: string
  headers?: Record<string, string>
  beforeUpload?: (file: File) => boolean
  onChange?: (file: UploadFile, fileList: UploadFile[]) => void
}

// ==================== 主题类型 ====================

export type ThemeMode = 'light' | 'dark' | 'auto'

export interface ThemeConfig {
  mode: ThemeMode
  primaryColor: string
  borderRadius: number
  fontSize: number
}