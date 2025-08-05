// @file: src/shared/components/ui/DateRangePicker.tsx
// @description: A reusable date range picker component.

import { useState } from 'react';
import { DayPicker, type DateRange } from 'react-day-picker';
import 'react-day-picker/dist/style.css';
import { ptBR } from 'date-fns/locale';
import { Calendar as CalendarIcon } from 'lucide-react';

interface DateRangePickerProps {
  dateRange: DateRange | undefined;
  setDateRange: (dateRange: DateRange | undefined) => void;
  className?: string;
}

export function DateRangePicker({ dateRange, setDateRange, className }: DateRangePickerProps) {
  const [showDatePicker, setShowDatePicker] = useState(false);

  const formatRange = (range: DateRange | undefined) => {
    if (!range) {
      return 'Selecione um período';
    }
    if (range.from && range.to) {
      return `${range.from.toLocaleDateString('pt-BR')} - ${range.to.toLocaleDateString('pt-BR')}`;
    }
    if (range.from) {
      return `${range.from.toLocaleDateString('pt-BR')} - ...`;
    }
    return 'Selecione um período';
  };

  return (
    <div className={`relative ${className}`}>
      <button
        onClick={() => setShowDatePicker(!showDatePicker)}
        className="w-full md:w-72 flex items-center justify-between text-left bg-gray-100 border border-gray-300 rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-200 transition-colors"
      >
        <span>{formatRange(dateRange)}</span>
        <CalendarIcon className="w-4 h-4 text-gray-500" />
      </button>
      {showDatePicker && (
        <div className="absolute z-10 mt-2 bg-white border rounded-lg shadow-lg animate-fade-in-up">
          <DayPicker
            mode="range"
            selected={dateRange}
            onSelect={(range) => {
              setDateRange(range);
              if (range?.from && range.to) {
                setShowDatePicker(false);
              }
            }}
            locale={ptBR}
            numberOfMonths={2}
          />
        </div>
      )}
    </div>
  );
}
