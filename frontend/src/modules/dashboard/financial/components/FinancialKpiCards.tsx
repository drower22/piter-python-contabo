import { cn } from '@/lib/utils';
import type { WeeklyFinancials } from '../../types';

// Helper para formatar valores monetários
const formatCurrency = (value: number) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);

interface FinancialKpiCardsProps {
  financialData: WeeklyFinancials;
}

export function FinancialKpiCards({ financialData }: FinancialKpiCardsProps) {
  const { online, direct, reconciliation } = financialData;
  const totalGross = online.gross + direct.total;

  const kpiStyle = "p-4 bg-white rounded-xl shadow-sm border flex flex-col items-center justify-center min-h-[90px]";

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">

      {/* Card Repasse iFood */}
      <div className={kpiStyle}>
        <p className="text-sm text-gray-500 mb-1">Repasse iFood</p>
        <p className="text-xl md:text-2xl font-semibold font-sora text-brand-purple-600">{formatCurrency(online.net)}</p>
      </div>

      {/* Card Vendas na Loja */}
      <div className={kpiStyle}>
        <p className="text-sm text-gray-500 mb-1">Vendas na Loja</p>
        <p className="text-xl md:text-2xl font-semibold font-sora text-brand-purple-600">{formatCurrency(direct.total)}</p>
      </div>

      {/* Card Total Bruto */}
      <div className={kpiStyle}>
        <p className="text-sm text-gray-500 mb-1">Total Bruto</p>
        <p className="text-xl md:text-2xl font-semibold font-sora text-brand-purple-600">{formatCurrency(totalGross)}</p>
      </div>

      {/* Card Conciliação */}
      <div className={cn(
        kpiStyle,
        reconciliation.status === 'pending' ? 'bg-yellow-50 border-yellow-200' : 'bg-green-50 border-green-200'
      )}>
        <p className="text-sm text-gray-600 mb-1">Conciliação</p>
        {reconciliation.status === 'pending' ? 
          <p className="text-xl md:text-2xl font-semibold font-sora text-yellow-800">{reconciliation.pendingItems} pendências</p> : 
          <p className="text-xl md:text-2xl font-semibold font-sora text-green-800">Conciliado</p> 
        }
      </div>
    </div>
  );
}