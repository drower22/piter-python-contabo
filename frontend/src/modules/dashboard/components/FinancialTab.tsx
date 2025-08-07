import type { WeeklyFinancials } from '../types';
import { FinancialKpiCards } from '../financial/components/FinancialKpiCards';
import { FinancialDetails } from '../financial/components/FinancialDetails';
import { ReconciliationCard } from '../financial/components/ReconciliationCard';
import { WeekSelector } from './WeekSelector';

interface FinancialTabProps {
  financialData: WeeklyFinancials;
  selectedWeekIndex: number;
  onWeekChange: (index: number) => void;
}

export function FinancialTab({ financialData, selectedWeekIndex, onWeekChange }: FinancialTabProps) {
  return (
    <div className="p-6 space-y-6 font-inter animate-fade-in">
      {/* Seletor de Semana */}
      <div className="space-y-2">
        <h4 className="font-sora text-sm font-semibold text-gray-700">Selecionar Semana</h4>
        <WeekSelector 
          selectedWeekIndex={selectedWeekIndex}
          onWeekChange={onWeekChange}
          className="w-[280px]"
        />
      </div>

      <FinancialKpiCards financialData={financialData} />
      <FinancialDetails financialData={financialData} />
      <ReconciliationCard financialData={financialData} />
    </div>
  );
}
