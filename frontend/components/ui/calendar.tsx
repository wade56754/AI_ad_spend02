'use client';

import { useState } from 'react';
import { ChevronLeftIcon, ChevronRightIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from './button';

export type CalendarMode = 'single' | 'range' | 'multiple';

interface CalendarProps {
  mode?: CalendarMode;
  selected?: Date | Date[];
  defaultSelected?: Date | Date[];
  onSelect?: (date: Date | Date[] | undefined) => void;
  className?: string;
  disabled?: (date: Date) => boolean;
  locale?: string;
  weekStartsOn?: 0 | 1 | 2 | 3 | 4 | 5 | 6;
  showWeekNumbers?: boolean;
  numberOfMonths?: number;
  min?: Date;
  max?: Date;
}

const months = [
  '一月', '二月', '三月', '四月', '五月', '六月',
  '七月', '八月', '九月', '十月', '十一月', '十二月'
];

const weekDays = ['日', '一', '二', '三', '四', '五', '六'];

function Calendar({
  mode = 'single',
  selected,
  defaultSelected,
  onSelect,
  className = '',
  disabled,
  locale = 'zh-CN',
  weekStartsOn = 1,
  showWeekNumbers = false,
  numberOfMonths = 1,
  min,
  max
}: CalendarProps) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState<Date | Date[] | undefined>(defaultSelected);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // Get days in month
  const getDaysInMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  };

  // Get first day of month
  const getFirstDayOfMonth = (date: Date) => {
    return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
  };

  // Format date for comparison
  const formatDateString = (date: Date) => {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  };

  // Check if date is selected
  const isDateSelected = (date: Date) => {
    if (!selectedDate) return false;

    if (Array.isArray(selectedDate)) {
      return selectedDate.some(d => formatDateString(d) === formatDateString(date));
    }

    return formatDateString(selectedDate) === formatDateString(date);
  };

  // Check if date is today
  const isDateToday = (date: Date) => {
    const today = new Date();
    return formatDateString(date) === formatDateString(today);
  };

  // Check if date is disabled
  const isDateDisabled = (date: Date) => {
    if (disabled && disabled(date)) return true;
    if (min && date < min) return true;
    if (max && date > max) return true;
    return false;
  };

  // Handle date selection
  const handleDateSelect = (date: Date) => {
    if (isDateDisabled(date)) return;

    let newSelection: Date | Date[];

    if (mode === 'single') {
      newSelection = date;
    } else if (mode === 'multiple') {
      const currentSelection = Array.isArray(selectedDate) ? selectedDate : [];
      const isSelected = currentSelection.some(d => formatDateString(d) === formatDateString(date));

      if (isSelected) {
        newSelection = currentSelection.filter(d => formatDateString(d) !== formatDateString(date));
      } else {
        newSelection = [...currentSelection, date];
      }
    } else {
      // Range mode
      if (!Array.isArray(selectedDate) || selectedDate.length === 0) {
        newSelection = [date];
      } else if (selectedDate.length === 1) {
        const startDate = selectedDate[0];
        if (date < startDate) {
          newSelection = [date, startDate];
        } else {
          newSelection = [startDate, date];
        }
      } else {
        newSelection = [date];
      }
    }

    setSelectedDate(newSelection);
    onSelect?.(newSelection);
  };

  // Navigate to previous month
  const goToPreviousMonth = () => {
    setCurrentDate(new Date(year, month - 1));
  };

  // Navigate to next month
  const goToNextMonth = () => {
    setCurrentDate(new Date(year, month + 1));
  };

  // Render calendar month
  const renderMonth = (offset = 0) => {
    const monthDate = new Date(year, month + offset);
    const monthYear = monthDate.getFullYear();
    const monthIndex = monthDate.getMonth();

    const daysInMonth = getDaysInMonth(monthDate);
    const firstDay = getFirstDayOfMonth(monthDate);

    // Adjust for week start
    const adjustedFirstDay = firstDay - weekStartsOn;
    const startOffset = adjustedFirstDay < 0 ? adjustedFirstDay + 7 : adjustedFirstDay;

    const days = [];

    // Week numbers
    let weekNumber = 1;

    // Create calendar days
    for (let i = 0; i < startOffset + daysInMonth; i++) {
      const dayNumber = i - startOffset + 1;

      if (i < startOffset) {
        // Empty cells before month starts
        days.push(<div key={`empty-${i}`} className="h-10"></div>);
      } else {
        const date = new Date(monthYear, monthIndex, dayNumber);
        const isSelected = isDateSelected(date);
        const isToday = isDateToday(date);
        const isDisabled = isDateDisabled(date);

        days.push(
          <Button
            key={dayNumber}
            variant={isSelected ? "default" : "ghost"}
            className={cn(
              'h-10 w-10 p-0 font-normal',
              isToday && 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400',
              isSelected && !isToday && 'bg-blue-600 text-white hover:bg-blue-700',
              !isSelected && !isToday && 'hover:bg-gray-100 dark:hover:bg-gray-700',
              isDisabled && 'text-gray-400 dark:text-gray-600 cursor-not-allowed hover:bg-transparent'
            )}
            disabled={isDisabled}
            onClick={() => handleDateSelect(date)}
          >
            {dayNumber}
          </Button>
        );
      }

      // Add week number at the start of each week
      if (showWeekNumbers && i % 7 === 0 && i > 0) {
        weekNumber++;
      }
    }

    return (
      <div key={offset} className="flex-1 min-w-[280px]">
        {/* Month Header */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium text-sm text-gray-900 dark:text-gray-100">
            {months[monthIndex]} {monthYear}
          </h3>
          {offset === 0 && (
            <div className="flex space-x-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={goToPreviousMonth}
                className="h-8 w-8 p-0"
              >
                <ChevronLeftIcon className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={goToNextMonth}
                className="h-8 w-8 p-0"
              >
                <ChevronRightIcon className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>

        {/* Week Days Header */}
        <div className="grid grid-cols-7 gap-1 mb-2">
          {showWeekNumbers && (
            <div className="h-10 flex items-center justify-center text-xs font-medium text-gray-500">
              周
            </div>
          )}
          {weekDays.map((day, index) => {
            const dayIndex = (index + weekStartsOn) % 7;
            return (
              <div
                key={day}
                className="h-10 flex items-center justify-center text-xs font-medium text-gray-500 dark:text-gray-400"
              >
                {weekDays[dayIndex]}
              </div>
            );
          })}
        </div>

        {/* Calendar Days */}
        <div className="grid grid-cols-7 gap-1">
          {showWeekNumbers && (
            <div className="flex flex-col space-y-1">
              {Array.from({ length: Math.ceil((startOffset + daysInMonth) / 7) }, (_, i) => (
                <div
                  key={i}
                  className="h-10 flex items-center justify-center text-xs font-medium text-gray-500"
                >
                  {i + 1}
                </div>
              ))}
            </div>
          )}
          {days}
        </div>
      </div>
    );
  };

  return (
    <div className={cn('p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700', className)}>
      <div className={`grid ${numberOfMonths > 1 ? 'grid-cols-1 md:grid-cols-2' : ''} gap-6`}>
        {Array.from({ length: numberOfMonths }, (_, i) => renderMonth(i))}
      </div>
    </div>
  );
}

export default Calendar;