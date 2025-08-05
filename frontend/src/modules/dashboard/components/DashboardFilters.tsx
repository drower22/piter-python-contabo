import { useState } from 'react';
import type { DateRange } from 'react-day-picker';
import { DateRangePicker } from '../../../shared/components/ui/DateRangePicker';

type DashboardFiltersProps = {
  filterType: 'performance' | 'financial';
  onFilterTypeChange: (type: 'performance' | 'financial') => void;
};

export function DashboardFilters({ filterType, onFilterTypeChange }: DashboardFiltersProps) {
  const [dateRange, setDateRange] = useState<DateRange | undefined>();

  return (
    <div className="bg-white p-4 rounded-xl shadow-md space-y-6 font-inter">
      <div className="flex border-b">
        <button
          onClick={() => onFilterTypeChange('performance')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${filterType === 'performance' ? 'border-b-2 border-brand-red text-brand-red font-semibold' : 'text-gray-500 hover:text-gray-700'}`}
        >
          Desempenho
        </button>
        <button
          onClick={() => onFilterTypeChange('financial')}
          className={`px-4 py-2 text-sm font-medium transition-colors ${filterType === 'financial' ? 'border-b-2 border-brand-red text-brand-red font-semibold' : 'text-gray-500 hover:text-gray-700'}`}
        >
          Financeiro
        </button>
      </div>

      {filterType === 'performance' && (
        <div className="space-y-4 animate-fade-in">
          <div>
            <h4 className="font-sora text-sm font-semibold text-gray-700 mb-2">Filtrar por período</h4>
            <DateRangePicker dateRange={dateRange} setDateRange={setDateRange} />
          </div>
        </div>
      )}

      {filterType === 'financial' && (
        <div className="animate-fade-in">
          <p className="text-sm text-gray-500">Filtros financeiros serão implementados aqui.</p>
        </div>
      )}
    </div>
  );
}

