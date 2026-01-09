import { createBrowserClient } from '@supabase/ssr';

// Supabase 客户端配置
// 用于前端浏览器环境的 Supabase 客户端

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    'Supabase 环境变量未配置。请在 .env.local 中设置:\n' +
    '- NEXT_PUBLIC_SUPABASE_URL\n' +
    '- NEXT_PUBLIC_SUPABASE_ANON_KEY'
  );
}

// 创建浏览器端 Supabase 客户端 (单例模式)
export const supabase = createBrowserClient(
  supabaseUrl || '',
  supabaseAnonKey || ''
);

// 导出类型
export type { User, Session } from '@supabase/supabase-js';
