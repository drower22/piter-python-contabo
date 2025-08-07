// @file: src/shared/components/ui/DateRangePicker.tsx
// @description: A reusable date range picker component.

import * as React from 'react';
import { DateRange as RDRDateRange } from 'react-date-range';
import type { Range, RangeKeyDict } from 'react-date-range';
import 'react-date-range/dist/styles.css';
import 'react-date-range/dist/theme/default.css';
import { pt } from 'date-fns/locale';
import { cn } from '../../../lib/utils';
import './date-range-custom.css';
import { Button } from './button';

// Adapter para compatibilizar a tipagem
export interface DateRange {
  from?: Date;
  to?: Date;
}


interface DateRangePickerProps {
  dateRange: DateRange | undefined;
  setDateRange: (dateRange: DateRange | undefined) => void;
  className?: string;
  onClose?: () => void;
}

export function DateRangePicker({ dateRange, setDateRange, className, onClose }: DateRangePickerProps) {
  // Estado interno para seleção temporária
  const [pendingRange, setPendingRange] = React.useState<Range>({
    startDate: dateRange?.from || undefined,
    endDate: dateRange?.to || undefined,
    key: 'selection',
  });

  React.useEffect(() => {
    setPendingRange({
      startDate: dateRange?.from || undefined,
      endDate: dateRange?.to || undefined,
      key: 'selection',
    });
  }, [dateRange]);

  function handleChange(ranges: RangeKeyDict) {
    setPendingRange(ranges.selection);
  }

  const isValid = !!pendingRange.startDate && !!pendingRange.endDate;

  function handleConfirm() {
    if (pendingRange.startDate && pendingRange.endDate) {
      setDateRange({ from: pendingRange.startDate, to: pendingRange.endDate });
      onClose?.();
    }
  }

  function handleCancel() {
    onClose?.();
  }

  return (
    <div className={cn('flex flex-col items-center gap-4', className)}>
      <RDRDateRange
        ranges={[pendingRange]}
        onChange={handleChange}
        showMonthAndYearPickers={true}
        months={2}
        direction="horizontal"
        locale={pt}
        showDateDisplay={false}
        weekdayDisplayFormat="EEEEE"
        rangeColors={["#4B1F6F"]}
        color="#4B1F6F"
        editableDateInputs={false}
        className="rounded-2xl shadow-xl border-none"
        maxDate={new Date()}
      />
      <div className="flex w-full justify-end gap-2 p-4">
        <Button onClick={handleCancel} variant="outline">
          Cancelar
        </Button>
        <Button onClick={handleConfirm} disabled={!isValid}>
          Confirmar
        </Button>
      </div>
    </div>
  );
}

