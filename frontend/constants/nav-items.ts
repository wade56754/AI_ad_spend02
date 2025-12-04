import type { NavItem } from '@/types/nav.types';
import {
  LayoutDashboard,
  Users,
  FileText,
  DollarSign,
  CheckSquare,
  BookOpen,
  Settings,
} from 'lucide-react';

export const navItems: NavItem[] = [
  {
    title: '概览',
    url: '/dashboard',
    icon: LayoutDashboard,
    shortcut: ['d', 'd'],
  },
  {
    title: '项目管理',
    url: '/dashboard/projects',
    icon: LayoutDashboard,
  },
  {
    title: '渠道账户',
    url: '/dashboard/ad-accounts',
    icon: Users,
  },
  {
    title: '日报管理',
    url: '/dashboard/daily-reports',
    icon: FileText,
  },
  {
    title: '充值管理',
    url: '/dashboard/topup',
    icon: DollarSign,
  },
  {
    title: '对账管理',
    url: '/dashboard/reconciliation',
    icon: CheckSquare,
  },
  {
    title: '账本查询',
    url: '/dashboard/ledger',
    icon: BookOpen,
  },
  {
    title: '系统设置',
    url: '/dashboard/settings',
    icon: Settings,
  },
];

