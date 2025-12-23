/**
 * Week Picker Component
 *
 * Week selector for weekly briefs
 * SoT: B3-weekly-brief.md §3.1
 */

'use client';

import { useState, useMemo } from 'react';
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Calendar, ChevronLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  format,
  startOfWeek,
  endOfWeek,
  addWeeks,
  subWeeks,
  getISOWeek,
  getYear,
  isSameWeek,
  startOfYear,
  eachWeekOfInterval,
} from 'date-fns';
import { zhCN } from 'date-fns/locale';

interface WeekPickerProps {
  value?: Date;
  onChange?: (weekStart: Date) => void;
  className?: string;
  disabled?: boolean;
}

/**
 * Get ISO week string (e.g., "2025-W51")
 */
export function getWeekString(date: Date): string {
  const week = getISOWeek(date);
  const year = getYear(date);
  return `${year}-W${week.toString().padStart(2, '0')}`;
}

/**
 * Get week label (e.g., "2025年第51周")
 */
export function getWeekLabel(date: Date): string {
  const week = getISOWeek(date);
  const year = getYear(date);
  return `${year}年第${week}周`;
}

/**
 * Get Monday of the week containing the given date
 */
export function getWeekStart(date: Date): Date {
  return startOfWeek(date, { weekStartsOn: 1 });
}

/**
 * Get Sunday of the week containing the given date
 */
export function getWeekEnd(date: Date): Date {
  return endOfWeek(date, { weekStartsOn: 1 });
}

export function WeekPicker({
  value,
  onChange,
  className,
  disabled = false,
}: WeekPickerProps) {
  const [open, setOpen] = useState(false);
  const [displayMonth, setDisplayMonth] = useState(() => value || new Date());

  const selectedWeekStart = useMemo(() => {
    return value ? getWeekStart(value) : getWeekStart(new Date());
  }, [value]);

  const selectedWeekEnd = useMemo(() => {
    return getWeekEnd(selectedWeekStart);
  }, [selectedWeekStart]);

  // Generate weeks for the display month
  const weeksInMonth = useMemo(() => {
    const year = getYear(displayMonth);
    const start = startOfYear(new Date(year, 0, 1));
    const end = new Date(year, 11, 31);
    return eachWeekOfInterval({ start, end }, { weekStartsOn: 1 });
  }, [displayMonth]);

  const handlePrevWeek = () => {
    const newDate = subWeeks(selectedWeekStart, 1);
    onChange?.(getWeekStart(newDate));
  };

  const handleNextWeek = () => {
    const newDate = addWeeks(selectedWeekStart, 1);
    onChange?.(getWeekStart(newDate));
  };

  const handleSelectWeek = (weekStart: Date) => {
    onChange?.(weekStart);
    setOpen(false);
  };

  const handlePrevYear = () => {
    setDisplayMonth(new Date(getYear(displayMonth) - 1, 0, 1));
  };

  const handleNextYear = () => {
    setDisplayMonth(new Date(getYear(displayMonth) + 1, 0, 1));
  };

  const displayText = `${getWeekLabel(selectedWeekStart)} (${format(
    selectedWeekStart,
    'MM/dd',
    { locale: zhCN }
  )} - ${format(selectedWeekEnd, 'MM/dd', { locale: zhCN })})`;

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Button
        variant="outline"
        size="icon"
        onClick={handlePrevWeek}
        disabled={disabled}
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>

      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className={cn(
              'min-w-[260px] justify-start text-left font-normal',
              !value && 'text-muted-foreground'
            )}
            disabled={disabled}
          >
            <Calendar className="mr-2 h-4 w-4" />
            {displayText}
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-auto p-4" align="start">
          <div className="space-y-4">
            {/* Year navigation */}
            <div className="flex items-center justify-between">
              <Button variant="ghost" size="icon" onClick={handlePrevYear}>
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="font-medium">{getYear(displayMonth)}年</span>
              <Button variant="ghost" size="icon" onClick={handleNextYear}>
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>

            {/* Weeks grid */}
            <div className="grid grid-cols-4 gap-2 max-h-[300px] overflow-y-auto">
              {weeksInMonth.map((weekStart) => {
                const isSelected = isSameWeek(weekStart, selectedWeekStart, {
                  weekStartsOn: 1,
                });
                const weekNum = getISOWeek(weekStart);
                const weekEnd = getWeekEnd(weekStart);

                return (
                  <Button
                    key={weekStart.toISOString()}
                    variant={isSelected ? 'default' : 'ghost'}
                    size="sm"
                    className={cn(
                      'h-auto py-2 px-2 flex flex-col items-center',
                      isSelected && 'bg-primary text-primary-foreground'
                    )}
                    onClick={() => handleSelectWeek(weekStart)}
                  >
                    <span className="text-xs font-medium">W{weekNum}</span>
                    <span className="text-[10px] text-muted-foreground">
                      {format(weekStart, 'MM/dd')}
                    </span>
                  </Button>
                );
              })}
            </div>

            {/* Quick select */}
            <div className="flex gap-2 pt-2 border-t">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleSelectWeek(getWeekStart(new Date()))}
              >
                本周
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  handleSelectWeek(getWeekStart(subWeeks(new Date(), 1)))
                }
              >
                上周
              </Button>
            </div>
          </div>
        </PopoverContent>
      </Popover>

      <Button
        variant="outline"
        size="icon"
        onClick={handleNextWeek}
        disabled={disabled}
      >
        <ChevronRight className="h-4 w-4" />
      </Button>
    </div>
  );
}

export default WeekPicker;
