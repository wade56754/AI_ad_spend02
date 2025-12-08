/**
 * Theme Hook
 *
 * Wrapper around next-themes for theme management
 */

'use client';

import { useTheme as useNextTheme } from 'next-themes';
import { useIsMounted } from './useIsMounted';

export function useTheme() {
  const { theme, setTheme, systemTheme, resolvedTheme } = useNextTheme();
  const mounted = useIsMounted();

  return {
    theme: theme || 'system',
    setTheme,
    systemTheme,
    resolvedTheme,
    isDark: resolvedTheme === 'dark',
    isLight: resolvedTheme === 'light',
    toggleTheme: () => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark'),
    mounted,
  };
}

export default useTheme;
