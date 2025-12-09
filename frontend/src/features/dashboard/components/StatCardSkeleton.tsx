/**
 * StatCardSkeleton Component
 *
 * Loading skeleton for dashboard components
 * Based on UI_DESIGN_SYSTEM.md v2.0 Section 9.1
 *
 * Uses shadcn Skeleton and Card components
 */

'use client';

import React from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export function StatCardSkeleton() {
  return (
    <Card className="rounded-xl border shadow-sm">
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <Skeleton className="w-12 h-12 rounded-lg" />
          <Skeleton className="w-16 h-5 rounded" />
        </div>
        <Skeleton className="w-24 h-8 rounded mb-2" />
        <Skeleton className="w-16 h-4 rounded" />
      </CardContent>
    </Card>
  );
}

export function TrendChartSkeleton() {
  return (
    <Card className="rounded-xl border shadow-sm">
      <CardHeader className="pb-4">
        <Skeleton className="w-32 h-6 rounded mb-2" />
        <Skeleton className="w-48 h-4 rounded" />
      </CardHeader>
      <CardContent className="px-4 pb-4">
        <Skeleton className="h-48 w-full rounded" />
      </CardContent>
    </Card>
  );
}

export function CardSkeleton() {
  return (
    <Card className="rounded-xl border shadow-sm">
      <CardContent className="p-6">
        <Skeleton className="w-24 h-6 rounded mb-4" />
        <div className="space-y-3">
          <Skeleton className="h-12 w-full rounded" />
          <Skeleton className="h-12 w-full rounded" />
          <Skeleton className="h-12 w-full rounded" />
        </div>
      </CardContent>
    </Card>
  );
}

export default StatCardSkeleton;
