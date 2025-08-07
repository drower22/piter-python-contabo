import { useState, useMemo } from 'react';
import { DashboardFilters } from '../components/DashboardFilters';
import { FinancialTab } from '../components/FinancialTab';
import { PerformanceTab } from '../performance/components/PerformanceTab';
import { generateWeeklyData } from '../data/financial.data';
import type { WeeklyFinancials } from '../types';

/**
 * @file DashboardPage.tsx
 * @description A página principal do dashboard, que orquestra a exibição
 * dos filtros e dos painéis de Desempenho e Financeiro.
 */
import type { DateRange } from '@/shared/components/ui/DateRangePicker';

export function DashboardPage() {
  // Estado para controlar qual aba está selecionada: 'performance' ou 'financial'
  const [filterType, setFilterType] = useState<'performance' | 'financial'>('performance');

  // Estado para controlar a semana selecionada. 0 = Esta semana, 1 = Semana passada, etc.
  const [selectedWeekIndex, setSelectedWeekIndex] = useState<number>(0);

  // Estado global para filtro de datas
  const [dateRange, setDateRange] = useState<DateRange | undefined>();

  // Gera e memoriza os dados financeiros para a semana selecionada.
  const financialData: WeeklyFinancials = useMemo(() => generateWeeklyData(selectedWeekIndex), [selectedWeekIndex]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold font-sora text-brand-black-charcoal">Dashboard</h1>
        <p className="text-gray-500 mt-1">Visualize os dados de vendas e repasses da sua loja.</p>
      </header>

      {/* Card principal que unifica tudo */}
      <div className="bg-white rounded-xl shadow-md font-inter">
        <div className="p-6 border-b">
          <DashboardFilters
            filterType={filterType}
            onFilterTypeChange={setFilterType}
          />
        </div>

        {/* Renderização condicional do conteúdo da aba */}
        <main>
          {filterType === 'performance' && (
            <PerformanceTab
              data={financialData}
              dateRange={dateRange}
              setDateRange={setDateRange}
            />
          )}
          {filterType === 'financial' && (
            <FinancialTab
              financialData={financialData}
              selectedWeekIndex={selectedWeekIndex}
              onWeekChange={setSelectedWeekIndex}
            />
          )}
        </main>
      </div>
    </div>
  );
}
