/**
 * 充值管理模块类型定义
 */

// 充值状态枚举
export type RechargeStatus =
  | 'pending'      // 待审核
  | 'processing'   // 充值中
  | 'completed'    // 已完成
  | 'rejected'     // 已驳回
  | 'cancelled';   // 已取消

// 支付方式枚举
export type PaymentMethod =
  | 'alipay'        // 支付宝
  | 'wechat'        // 微信支付
  | 'bank_transfer' // 银行转账
  | 'credit_card';  // 信用卡

// 优先级枚举
export type Priority =
  | 'low'      // 低
  | 'normal'   // 中
  | 'high'     // 高
  | 'urgent';  // 紧急

// 平台枚举
export type Platform =
  | 'facebook'
  | 'google'
  | 'tiktok'
  | 'instagram';

// 币种枚举
export type Currency = 'USD' | 'CNY' | 'EUR' | 'GBP';

// 充值记录基础接口
export interface RechargeRecord {
  id: number;
  request_code: string;           // 充值单号
  account_name: string;           // 关联广告账户名称
  account_id: string;             // 广告账户ID
  platform: Platform;            // 平台
  amount: number;                 // 充值金额
  currency: Currency;             // 币种
  payment_method: PaymentMethod;  // 支付方式
  status: RechargeStatus;         // 状态
  requested_by: string;           // 申请人
  requested_at: string;           // 申请时间
  approved_by?: string;           // 审批人
  approved_at?: string;           // 审批时间
  completed_at?: string;          // 完成时间
  payment_reference?: string;     // 支付参考号
  notes?: string;                 // 备注
  rejection_reason?: string;      // 驳回原因
  priority: Priority;             // 优先级
  project_name?: string;          // 项目名称
  exchange_rate?: number;         // 汇率
  actual_amount?: number;         // 实际到账金额
  fee?: number;                   // 手续费
}

// KPI统计数据接口
export interface RechargeStats {
  total_requests: number;         // 总申请数
  pending_requests: number;       // 待审核申请数
  completed_requests: number;     // 已完成申请数
  total_amount: number;           // 累计充值金额
  pending_amount: number;         // 待充值金额
  monthly_amount?: number;        // 本月充值金额
  average_processing_time?: number; // 平均处理时间(小时)
}

// 筛选条件接口
export interface RechargeFilters {
  search_term: string;            // 搜索关键词
  status: RechargeStatus | 'all'; // 状态筛选
  platform: Platform | 'all';    // 平台筛选
  priority: Priority | 'all';     // 优先级筛选
  date_range: {
    start?: string;
    end?: string;
  };
  payment_method: PaymentMethod | 'all'; // 支付方式筛选
}

// 操作记录时间线接口
export interface RechargeTimeline {
  id: number;
  recharge_id: number;
  action: 'created' | 'approved' | 'rejected' | 'processing' | 'completed' | 'cancelled';
  actor: string;
  actor_role: string;
  timestamp: string;
  notes?: string;
  metadata?: Record<string, any>;
}

// 批量操作接口
export interface BatchOperation {
  action: 'approve' | 'reject' | 'export';
  selected_ids: number[];
  notes?: string;
}

// 收款账户信息接口
export interface PaymentAccount {
  id: number;
  platform: Platform;
  account_name: string;
  account_number: string;
  bank_name?: string;
  currency: Currency;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// 充值记录详情接口（包含关联信息）
export interface RechargeRecordDetail extends RechargeRecord {
  timeline: RechargeTimeline[];     // 操作时间线
  payment_account?: PaymentAccount; // 收款账户信息
  attachments?: {                   // 附件信息
    id: number;
    name: string;
    url: string;
    type: 'image' | 'pdf' | 'excel';
  }[];
}

// 表格列配置接口
export interface TableColumn {
  key: string;
  title: string;
  dataIndex: keyof RechargeRecord;
  width?: string;
  align?: 'left' | 'center' | 'right';
  render?: (value: any, record: RechargeRecord) => React.ReactNode;
}

// 分页信息接口
export interface Pagination {
  current: number;
  pageSize: number;
  total: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
}

// 列表响应接口
export interface RechargeListResponse {
  data: RechargeRecord[];
  pagination: Pagination;
  stats: RechargeStats;
}

// KPI卡片配置接口
export interface KPICardConfig {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: {
    value: number;
    type: 'up' | 'down' | 'neutral';
  };
  color?: 'primary' | 'success' | 'warning' | 'destructive' | 'info';
  icon?: React.ComponentType<any>;
}