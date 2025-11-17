/**
 * 黄金规则13：必须延迟渲染动态内容
 *
 * 这个Hook确保服务器和客户端的首次渲染（水合）100%一致
 * 任何依赖客户端环境的UI渲染必须被延迟到水合之后执行
 */

import { useState, useEffect } from 'react';

/**
 * 安全的客户端环境检测Hook
 * 遵循SSR最佳实践，防止水合失败
 */
export const useIsMounted = () => {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    // 确保只在客户端执行
    setIsMounted(true);
  }, []);

  return isMounted;
};

/**
 * 安全的延迟渲染Hook
 * 用于包装任何依赖客户端环境的内容
 */
export const useDeferredRender = (delay: number = 0) => {
  const [shouldRender, setShouldRender] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setShouldRender(true);
    }, delay);

    return () => clearTimeout(timer);
  }, [delay]);

  return shouldRender;
};

/**
 * 安全的localStorage Hook
 * 防止SSR时访问localStorage导致的错误
 */
export const useLocalStorage = <T>(key: string, initialValue: T) => {
  const [storedValue, setStoredValue] = useState<T>(initialValue);
  const isMounted = useIsMounted();

  useEffect(() => {
    if (!isMounted) return;

    try {
      const item = window.localStorage.getItem(key);
      if (item) {
        setStoredValue(JSON.parse(item));
      }
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
    }
  }, [key, isMounted]);

  const setValue = (value: T | ((val: T) => T)) => {
    if (!isMounted) return;

    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.warn(`Error setting localStorage key "${key}":`, error);
    }
  };

  return [storedValue, setValue] as const;
};

/**
 * 安全的窗口大小Hook
 * 防止SSR时访问window对象导致的错误
 */
export const useWindowSize = () => {
  const [windowSize, setWindowSize] = useState({
    width: 0,
    height: 0,
  });
  const isMounted = useIsMounted();

  useEffect(() => {
    if (!isMounted) return;

    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [isMounted]);

  return windowSize;
};

/**
 * 安全的主题Hook
 * 防止SSR时主题切换导致的闪烁
 */
export const useThemeSafe = () => {
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const isMounted = useIsMounted();

  useEffect(() => {
    if (!isMounted) return;

    // 从localStorage读取保存的主题
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark';
    if (savedTheme) {
      setTheme(savedTheme);
    } else {
      // 检查系统主题偏好
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setTheme(prefersDark ? 'dark' : 'light');
    }
  }, [isMounted]);

  useEffect(() => {
    if (!isMounted) return;

    // 应用主题到DOM
    document.documentElement.setAttribute('data-theme', theme);

    // 保存到localStorage
    localStorage.setItem('theme', theme);
  }, [theme, isMounted]);

  const toggleTheme = () => {
    setTheme(prev => prev === 'dark' ? 'light' : 'dark');
  };

  return { theme, toggleTheme, isMounted };
};

/**
 * 安全的动态数据Hook
 * 用于任何需要异步获取的数据
 */
export const useAsyncData = <T>(
  asyncFn: () => Promise<T>,
  deps: React.DependencyList = []
) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const isMounted = useIsMounted();

  useEffect(() => {
    if (!isMounted) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await asyncFn();
        if (isMounted) {
          setData(result);
        }
      } catch (err) {
        if (isMounted) {
          setError(err as Error);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchData();
  }, deps);

  return { data, loading, error, isMounted };
};