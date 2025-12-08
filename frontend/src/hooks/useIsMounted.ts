/**
 * useIsMounted Hook
 *
 * Returns true after the component has mounted (client-side)
 * Useful for SSR-safe rendering
 */

'use client';

import { useState, useEffect, useDeferredValue } from 'react';

export function useIsMounted(): boolean {
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
  }, []);

  return isMounted;
}

/**
 * useDeferredRender Hook
 *
 * Returns true after the initial render to defer non-critical content
 * Useful for SSR-safe deferred rendering
 */
export function useDeferredRender(delay = 0): boolean {
  const [shouldRender, setShouldRender] = useState(false);

  useEffect(() => {
    if (delay > 0) {
      const timer = setTimeout(() => setShouldRender(true), delay);
      return () => clearTimeout(timer);
    } else {
      setShouldRender(true);
    }
  }, [delay]);

  return shouldRender;
}

export default useIsMounted;
