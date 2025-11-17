import { useState, useEffect } from 'react';

export type Theme = 'light' | 'dark';

/**
 * 主题管理Hook
 *
 * 提供主题切换功能，支持：
 * - 深色/浅色主题切换
 * - 本地存储记忆用户偏好
 * - 自动应用主题到DOM
 * - 系统主题检测
 */
export const useTheme = () => {
  const [theme, setTheme] = useState<Theme>('dark');
  const [mounted, setMounted] = useState(false);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  const setThemeExplicitly = (newTheme: Theme) => {
    setTheme(newTheme);
  };

  // 检测系统主题偏好
  const getSystemTheme = (): Theme => {
    if (typeof window === 'undefined') return 'dark';
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  };

  useEffect(() => {
    setMounted(true);

    // 从localStorage恢复主题设置
    const savedTheme = localStorage.getItem('theme') as Theme | null;

    if (savedTheme && ['light', 'dark'].includes(savedTheme)) {
      setTheme(savedTheme);
    } else {
      // 如果没有保存的主题，使用系统主题
      setTheme(getSystemTheme());
    }
  }, []);

  useEffect(() => {
    if (mounted) {
      // 保存主题偏好
      localStorage.setItem('theme', theme);

      // 应用主题到DOM
      document.documentElement.setAttribute('data-theme', theme);

      // 设置meta标签用于移动端状态栏
      const metaThemeColor = document.querySelector('meta[name="theme-color"]');
      if (metaThemeColor) {
        metaThemeColor.setAttribute('content', theme === 'dark' ? '#0f172a' : '#f8fafc');
      }
    }
  }, [theme, mounted]);

  // 监听系统主题变化
  useEffect(() => {
    if (!mounted) return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      // 只有在用户没有手动设置主题时才跟随系统主题
      const savedTheme = localStorage.getItem('theme');
      if (!savedTheme) {
        setTheme(e.matches ? 'dark' : 'light');
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [mounted]);

  return {
    theme,
    toggleTheme,
    setTheme: setThemeExplicitly,
    isDark: theme === 'dark',
    isLight: theme === 'light',
    mounted
  };
};