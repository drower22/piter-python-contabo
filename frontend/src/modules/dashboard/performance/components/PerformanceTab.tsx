import { type DateRange } from '@/shared/components/ui/DateRangePicker';
import { useState } from 'react';
import type { WeeklyFinancials } from '../../types';
import { PerformanceChart } from './PerformanceChart';
import { PerformanceKpis } from './PerformanceKpis';
import { DateRangePicker } from '@/shared/components/ui/DateRangePicker';
import { PeriodDropdown } from '../../components/PeriodDropdown';
import { Dialog, DialogContent } from '@/shared/components/ui/dialog';
import { subDays, startOfDay, endOfDay } from 'date-fns';

interface PerformanceTabProps {
  data: WeeklyFinancials;
  dateRange: DateRange | undefined;
  setDateRange: (dateRange: DateRange | undefined) => void;
}

export function PerformanceTab({ data, dateRange, setDateRange }: PerformanceTabProps) {
  const [period, setPeriod] = useState<string>('7');
  const [customModalOpen, setCustomModalOpen] = useState(false);

  function handlePeriodChange(newPeriod: string) {
    setPeriod(newPeriod);
    if (newPeriod === 'custom') {
      setCustomModalOpen(true);
    } else {
      setCustomModalOpen(false);
      const days = parseInt(newPeriod, 10);
      const today = endOfDay(new Date());
      const from = startOfDay(subDays(today, days - 1));
      setDateRange({ from, to: today });
    }
  }

  function handleCustomDateChange(dr: DateRange | undefined) {
    setDateRange(dr);
    setPeriod('custom');
    setCustomModalOpen(false);
  }

  function handleCancelModal() {
    setCustomModalOpen(false);
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="bg-white rounded-xl shadow-md p-6 space-y-6">
        {/* Filtro de Período */}
        <div className="space-y-2">
          <h4 className="font-sora text-sm font-semibold text-gray-700">Filtrar por período</h4>
          <div className="flex items-center gap-2">
            <PeriodDropdown value={period} onChange={handlePeriodChange} />
            <Dialog open={customModalOpen} onOpenChange={setCustomModalOpen}>
              <DialogContent className="max-w-2xl p-0 bg-transparent border-none shadow-none flex items-center justify-center">
                <div className="bg-white rounded-2xl shadow-xl p-6">
                  <DateRangePicker dateRange={dateRange} setDateRange={handleCustomDateChange} onClose={handleCancelModal} />
                </div>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* KPIs */}
        <div className="mb-20">
          <PerformanceKpis data={data} />
        </div>

        {/* Card do gráfico com título integrado */}
        <div className="bg-white rounded-xl shadow border p-0 overflow-hidden mt-16">
          <div className="flex items-center gap-2 px-6 pt-4 pb-2 border-b border-gray-100 bg-gray-50">
            <svg width="22" height="22" fill="none" viewBox="0 0 24 24" stroke="currentColor" className="text-brand-purple">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 17v2a1 1 0 001 1h14a1 1 0 001-1v-2M7 10v7m4-4v4m4-7v7" />
            </svg>
            <span className="font-sora text-base font-semibold text-brand-purple">
              {period !== 'custom'
                ? `Comparativo dos últimos ${period} dias`
                : 'Comparativo - Período Personalizado'}
            </span>
          </div>
          <div className="px-4 md:px-8 pb-4 pt-2">
            <PerformanceChart dateRange={dateRange} />
          </div>
        </div>
      </div>
    </div>
  );
}
