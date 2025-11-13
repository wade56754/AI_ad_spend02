"use client";

import React from 'react';
import { useTheme } from '@/hooks/use-theme';
import { OptimizedButton } from './optimized-button';

/**
 * 主题切换按钮组件
 * 符合可访问性标准，支持键盘导航和屏幕阅读器
 */
export const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme, mounted } = useTheme();

  if (!mounted) {
    // 避免hydration不匹配
    return (
      <div className="w-10 h-10 rounded-lg bg-gray-200 animate-pulse" />
    );
  }

  const isDark = theme === 'dark';

  return (
    <OptimizedButton
      variant="ghost"
      size="sm"
      onClick={toggleTheme}
      icon={
        isDark ? (
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"
            />
          </svg>
        ) : (
          <svg
            className="w-5 h-5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z"
            />
          </svg>
        )
      }
      aria-label={`切换到${isDark ? '浅色' : '深色'}主题`}
      title={`切换到${isDark ? '浅色' : '深色'}主题 (当前: ${isDark ? '深色' : '浅色'}主题)`}
    >
      <span className="sr-only">
        当前主题: {isDark ? '深色' : '浅色'}主题
      </span>
    </OptimizedButton>
  );
};