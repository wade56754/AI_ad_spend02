import type { LucideIcon } from 'lucide-react';

export interface NavItem {
  title: string;
  url: string;
  icon: LucideIcon;
  isActive?: boolean;
  shortcut?: string[];
  items?: NavItem[];
  badge?: number;
}

export interface NavGroup {
  label: string;
  items: NavItem[];
}

