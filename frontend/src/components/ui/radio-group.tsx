'use client';

import * as React from 'react';
import { Circle } from 'lucide-react';

import { cn } from '@/lib/utils';

interface RadioGroupContextValue {
  value?: string;
  onValueChange?: (value: string) => void;
  name?: string;
}

const RadioGroupContext = React.createContext<RadioGroupContextValue>({});

interface RadioGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  name?: string;
  disabled?: boolean;
}

const RadioGroup = React.forwardRef<HTMLDivElement, RadioGroupProps>(
  ({ className, value, defaultValue, onValueChange, name, children, ...props }, ref) => {
    const [internalValue, setInternalValue] = React.useState(defaultValue);
    const currentValue = value ?? internalValue;

    const handleValueChange = React.useCallback(
      (newValue: string) => {
        if (value === undefined) {
          setInternalValue(newValue);
        }
        onValueChange?.(newValue);
      },
      [value, onValueChange]
    );

    return (
      <RadioGroupContext.Provider
        value={{ value: currentValue, onValueChange: handleValueChange, name }}
      >
        <div
          ref={ref}
          role="radiogroup"
          className={cn('grid gap-2', className)}
          {...props}
        >
          {children}
        </div>
      </RadioGroupContext.Provider>
    );
  }
);
RadioGroup.displayName = 'RadioGroup';

interface RadioGroupItemProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  value: string;
}

const RadioGroupItem = React.forwardRef<HTMLInputElement, RadioGroupItemProps>(
  ({ className, value, children, ...props }, ref) => {
    const context = React.useContext(RadioGroupContext);
    const isChecked = context.value === value;

    return (
      <label className="flex items-center gap-2 cursor-pointer">
        <span
          className={cn(
            'aspect-square h-4 w-4 rounded-full border border-primary text-primary ring-offset-background focus-within:ring-2 focus-within:ring-ring focus-within:ring-offset-2',
            props.disabled && 'cursor-not-allowed opacity-50',
            className
          )}
        >
          <input
            ref={ref}
            type="radio"
            className="sr-only"
            value={value}
            checked={isChecked}
            name={context.name}
            onChange={() => context.onValueChange?.(value)}
            {...props}
          />
          {isChecked && (
            <span className="flex items-center justify-center h-full">
              <Circle className="h-2.5 w-2.5 fill-current text-current" />
            </span>
          )}
        </span>
        {children}
      </label>
    );
  }
);
RadioGroupItem.displayName = 'RadioGroupItem';

export { RadioGroup, RadioGroupItem };
